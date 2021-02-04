from datetime import *
import telebot
import json
import threading
import time
import logging
import requests
from dotenv import load_dotenv
import os
import pymongo
from pymongo import MongoClient

load_dotenv()
ukr_week = ("понеділок", "вівторок", "середа", "четвер", "п'ятниця")
week = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday')
bot = telebot.TeleBot(os.getenv("TOKEN"))

sub_group_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
sub_group_keyboard.row('Перша підгрупа', 'Друга підгрупа')
days_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
days_keyboard.row("Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця")
cancel_markup = telebot.types.ReplyKeyboardRemove()

cluster = MongoClient(os.getenv("MONGODB_URL"))
db = cluster[os.getenv("MONGODB_NAME")]
first_subgroup_data = db[os.getenv("MONGODB_COLLECTIONF")]
second_subgroup_data = db[os.getenv("MONGODB_COLLECTIONS")]
users_collection = db[os.getenv("MONGODB_COLLECTIONU")]


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"Вітаю {message.from_user.first_name}!\n"
                                      f"Я <b>{bot.get_me().first_name}</b>,"
                                      f" бот який сповіщує студента про початок пари. "
                                      f"\nНапиши /help для перегляду доступних команд.",
                                      parse_mode='html', reply_markup=cancel_markup)


@bot.message_handler(commands=['first_subgroup', 'second_subgroup'])
def sub_group(message):
    user = users_collection.find_one({"_id": message.chat.id}, {"_id": False})

    if user and user.get("subgroup") == message.text[1:]:
        bot.send_message(message.chat.id, 'Ви вже пристуні у даній підгрупі!', reply_markup=cancel_markup)
    else:
        if not user:
            users_collection.insert_one({"_id": message.chat.id, "subgroup": message.text[1:]})
        else:
            users_collection.update_one({"_id": message.chat.id}, {"$set": {"subgroup": message.text[1:]}})

        if message.text[1:] == 'first_subgroup':
            bot.send_message(message.chat.id, 'Ви були додані у першу підгрупу.', reply_markup=cancel_markup)
        else:
            bot.send_message(message.chat.id, 'Ви були додані у другу підгрупу.', reply_markup=cancel_markup)


@bot.message_handler(commands=['first_subgroup_schedule', 'second_subgroup_schedule'])
def show_sub_group_schedule(message):
    show_schedule = ""
    schedule_data = []
    if message.text[1:6] == "first":
        for i in first_subgroup_data.find({}, {"_id": 0, "link": 0}):
            schedule_data.append(i)
    else:
        for i in second_subgroup_data.find({}, {"_id": 0, "link": 0}):
            schedule_data.append(i)

    for day in week:
        show_schedule += f'─────────\n<b>{ukr_week[week.index(day)].upper()}:</b>\n\n'
        for lesson in schedule_data:
            if day in lesson.get("day"):
                show_schedule += f'➜ {lesson.get("time")[:-3]}:\n' \
                                 f'{lesson.get("name")}\n' \
                                 f'Тиждень: {lesson.get("week_count")}\n\n'

    bot.send_message(message.chat.id, show_schedule, parse_mode='html', reply_markup=cancel_markup)


@bot.message_handler(commands=['day_schedule'])
def show_day_schedule(message):
    bot.send_message(message.chat.id, 'Виберіть бажану підгрупу', reply_markup=sub_group_keyboard)
    bot.register_next_step_handler(message, choose_subgroup)


def choose_subgroup(message):
    if message.text in commands_dict:
        return commands_dict[message.text](message)
    elif message.text.lower() not in ('перша підгрупа', 'друга підгрупа'):
        bot.send_message(message.chat.id, 'Обрано некоректну підгрупу!')
        bot.register_next_step_handler(message, choose_subgroup)
    else:
        chosen_subgroup = message.text.lower()
        bot.send_message(message.chat.id, 'Виберіть бажаний день', reply_markup=days_keyboard)
        bot.register_next_step_handler(message, day_schedule, chosen_subgroup)


def day_schedule(message, chosen_subgroup):
    if message.text in commands_dict:
        return commands_dict[message.text](message)
    elif message.text.lower() not in ukr_week:
        bot.send_message(message.chat.id, 'Обрано некоректний день!')
        bot.register_next_step_handler(message, day_schedule, chosen_subgroup)
    else:
        if chosen_subgroup == "перша підгрупа":
            day = week[ukr_week.index(message.text.lower())]
            subgroup_day_data = first_subgroup_data.find({"day": day}, {"_id": 0, "link": 0})
        else:
            day = week[ukr_week.index(message.text.lower())]
            subgroup_day_data = second_subgroup_data.find({"day": day}, {"_id": 0, "link": 0})

        schedule_of_the_day = f'<b>{message.text[0:1].title()+message.text[1:].lower()}</b>:\n\n'
        for lesson in subgroup_day_data:
            schedule_of_the_day += f'➜ {lesson.get("time")[:-3]}:\n' \
                                   f'{lesson.get("name")}\n' \
                                   f'Тиждень: {lesson.get("week_count")}\n\n'

        bot.send_message(message.chat.id, schedule_of_the_day, reply_markup=cancel_markup, parse_mode='html')


@bot.message_handler(commands=['help'])
def show_commands(message):
    bot.send_message(message.chat.id, "/start - Початок роботи"
                                      "\n/first_subgroup - Перша підгрупа"
                                      "\n/second_subgroup - Друга підгрупа"
                                      "\n/first_subgroup_schedule - Розклад першої підгрупи"
                                      "\n/second_subgroup_schedule - Розклад другої підгрупи"
                                      "\n/day_schedule - Розклад на вибраний день вашої підгрупи"
                                      "\n/help - Показати доступні команди"
                                      "\n/leave - Вимкнути сповіщення", reply_markup=cancel_markup)


@bot.message_handler(commands=['leave'])
def leave(message):
    user = users_collection.find_one({"_id": message.chat.id})

    if not user:
        bot.send_message(message.chat.id, 'Вас немає у списку підгруп!', reply_markup=cancel_markup)
    else:
        users_collection.delete_one({"_id": message.chat.id})

        bot.send_message(message.chat.id, 'Ви успішно вимкнули сповіщення. \nЩоб ввімкнути сповіщення'
                                          ' виберіть підгрупу командою /first_subgroup або /second_subgroup',
                         reply_markup=cancel_markup)


def notify():
    first_subgroup_schedule = first_subgroup_data[week[datetime.now().weekday()]]
    second_subgroup_schedule = second_subgroup_data[week[datetime.now().weekday()]]

    while True:
        now = datetime.now()
        forward_time = (now + timedelta(minutes=10)).strftime("%H:%M:%S")
        current_time = now.strftime("%H:%M:%S")

        if current_time == "00:00:00":
            first_subgroup_schedule = first_subgroup_data[week[datetime.now().weekday()]]
            second_subgroup_schedule = second_subgroup_data[week[datetime.now().weekday()]]

        if forward_time in first_subgroup_schedule:
            for i in users["first_subgroup"]:
                try:
                    bot.send_message(i, f'Пара "{first_subgroup_schedule[forward_time]["name"]}" '
                                        f'почнеться через 10 хвилин \nПосилання: '
                                        f'{first_subgroup_schedule[forward_time]["link"]}')
                except telebot.apihelper.ApiTelegramException:
                    users["first_subgroup"].remove(i)

            with open('users.json', 'w') as js:
                json.dump(users, js)

        if forward_time in second_subgroup_schedule:
            for i in users["second_subgroup"]:
                try:
                    bot.send_message(i, f'Пара "{second_subgroup_schedule[forward_time]["name"]}" '
                                        f'почнеться через 10 хвилин \nПосилання: '
                                        f'{second_subgroup_schedule[forward_time]["link"]}')
                except telebot.apihelper.ApiTelegramException:
                    users["second_subgroup"].remove(i)

            with open('users.json', 'w') as js:
                json.dump(users, js)

        if current_time in first_subgroup_schedule:
            for i in users["first_subgroup"]:
                try:
                    bot.send_message(i, f'Пара: "{first_subgroup_schedule[current_time]["name"]}" почалась. '
                                        f'\nПосилання: {first_subgroup_schedule[current_time]["link"]}')
                except telebot.apihelper.ApiTelegramException:
                    users["first_subgroup"].remove(i)

            with open('users.json', 'w') as js:
                json.dump(users, js)

        if current_time in second_subgroup_schedule:
            for i in users["second_subgroup"]:
                try:
                    bot.send_message(i, f'Пара: "{second_subgroup_schedule[current_time]["name"]}" почалась.'
                                        f'\nПосилання: {second_subgroup_schedule[current_time]["link"]}')
                except telebot.apihelper.ApiTelegramException:
                    users["second_subgroup"].remove(i)

            with open('users.json', 'w') as js:
                json.dump(users, js)

        time.sleep(1)


url = "http://www.google.com"
thr = threading.Thread(target=notify)
thr.start()

commands_dict = {'/start': send_welcome, '/first_subgroup': sub_group, '/second_subgroup': sub_group,
                 '/first_subgroup_schedule': show_sub_group_schedule,
                 '/second_subgroup_schedule': show_sub_group_schedule,
                 '/day_schedule': show_day_schedule, '/help': show_commands, '/leave': leave}
while True:
    try:
        requests.get(url, timeout=5)
        print('Connected to the Internet')
        bot.polling(none_stop=True)

    except (requests.ConnectionError, requests.Timeout) as exception:
        logging.error(exception)
        print("No internet connection.")
        time.sleep(5)
