from datetime import *
import telebot
import json
import config
import threading
import time
import logging
import requests

ukr_week = ("Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця")
week = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
bot = telebot.TeleBot(config.token)

check_day_schedule = False
keyboard1 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
keyboard1.row("Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця")
cancel_markup = telebot.types.ReplyKeyboardRemove()

with open('first_subgroup_schedule.json', encoding="utf-8") as js:
    first_subgroup_data = json.load(js)

with open('second_subgroup_schedule.json', encoding="utf-8") as js:
    second_subgroup_data = json.load(js)

with open('users.json') as js:
    users = json.load(js)


def cancel(func):
    def inner(*args, **kwargs):
        global check_day_schedule
        check_day_schedule = False
        return func(*args, **kwargs)
    return inner


@bot.message_handler(commands=['start'])
@cancel
def send_welcome(message):
    bot.send_message(message.chat.id, f"Вітаю {message.from_user.first_name}!\n"
                                      f"Я <b>{bot.get_me().first_name}</b>,"
                                      f" бот який сповіщує студента про початок пари. "
                                      f"\nНапиши /help для перегляду доступних команд.",
                                      parse_mode='html', reply_markup=cancel_markup)


@bot.message_handler(commands=['first_subgroup', 'second_subgroup'])
@cancel
def sub_group(message):
    if message.chat.id in users[message.text[1:]]:
        bot.send_message(message.chat.id, 'Ви вже пристуні у даній підгрупі!', reply_markup=cancel_markup)
    else:
        for sub in users.keys():
            if message.chat.id in users[sub]:
                users[sub].remove(message.chat.id)

        users[message.text[1:]].append(message.chat.id)

        with open('users.json', 'w') as js:
            json.dump(users, js)

        if message.text[1:] == 'first_subgroup':
            bot.send_message(message.chat.id, 'Ви були додані у першу підгрупу.', reply_markup=cancel_markup)
        else:
            bot.send_message(message.chat.id, 'Ви були додані у другу підгрупу.', reply_markup=cancel_markup)


@bot.message_handler(commands=['first_subgroup_schedule', 'second_subgroup_schedule'])
@cancel
def show_sub_group_schedule(message):
    sub_group_data = [first_subgroup_data, second_subgroup_data]
    index = 0 if message.text[1:6] == 'first' else 1
    chosen_sub_group = sub_group_data[index]
    show_schedule = ''
    day_count = 0

    for day in chosen_sub_group:
        if day in week[-2:]:
            continue
        show_schedule += f'─────────\n<b>{ukr_week[day_count].upper()}:</b>\n\n'
        for lesson_time in chosen_sub_group[day]:
            show_schedule += f'➜ {lesson_time[:-3]}: \n{chosen_sub_group[day][lesson_time]["name"]}\n\n'
        day_count += 1

    bot.send_message(message.chat.id, show_schedule, parse_mode='html')


@bot.message_handler(commands=['day_schedule'])
@cancel
def show_day_schedule(message):
    global check_day_schedule
    bot.send_message(message.chat.id, 'Вибери потрібний день', reply_markup=keyboard1)
    check_day_schedule = True


@bot.message_handler(func=lambda message: message.text in ukr_week and check_day_schedule, content_types=['text'])
@cancel
def day_schedule(message):
    if message.chat.id not in users['first_subgroup'] and message.chat.id not in users['second_subgroup']:
        bot.send_message(message.chat.id, 'Вас немає у списку підгруп!', reply_markup=cancel_markup)
    else:
        if message.chat.id in users['first_subgroup']:
            sub_group_check = first_subgroup_data
        else:
            sub_group_check = second_subgroup_data
        day = week[ukr_week.index(message.text)]
        schedule_of_the_day = f'<b>{message.text}</b>:\n\n'
        for lesson_time in sub_group_check[day]:
            schedule_of_the_day += f'➜ {lesson_time}\n{sub_group_check[day][lesson_time]["name"]}\n\n'
        global check_day_schedule
        bot.send_message(message.chat.id, schedule_of_the_day, reply_markup=cancel_markup, parse_mode='html')
        check_day_schedule = False


@bot.message_handler(commands=['help'])
@cancel
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
@cancel
def leave(message):
    if message.chat.id not in users['first_subgroup'] and message.chat.id not in users['second_subgroup']:
        bot.send_message(message.chat.id, 'Вас немає у списку підгруп!', reply_markup=cancel_markup)
    else:
        for sub in users.keys():
            if message.chat.id in users[sub]:
                users[sub].remove(message.chat.id)

        with open('users.json', 'w') as js:
            json.dump(users, js)

        bot.send_message(message.chat.id, 'Ви успішно вимкнули сповіщення. \nЩоб ввімкнути сповіщення'
                                          ' виберіть підгрупу командою /subgroup1 або /subgroup2',
                                          reply_markup=cancel_markup)


def notify():
    first_subgroup_schedule = first_subgroup_data[week[datetime.now().weekday()]]
    second_subgroup_schedule = second_subgroup_data[week[datetime.now().weekday()]]

    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        temp = current_time.split(':')
        forward_time_sec = int(temp[0]) * 3600 + int(temp[1]) * 60 + int(temp[2]) + 600
        forward_time = ('%02d:%02d:%02d' % (
            forward_time_sec // 3600, forward_time_sec % 3600 // 60, forward_time_sec % 3600 % 60))

        if current_time == "00:00:00":
            first_subgroup_schedule = first_subgroup_data[week[datetime.now().weekday()]]
            second_subgroup_schedule = second_subgroup_data[week[datetime.now().weekday()]]

        if forward_time in first_subgroup_schedule:
            for i in users["subgroup1"]:
                try:
                    bot.send_message(i, f'Пара "{first_subgroup_schedule[forward_time]["name"]}" '
                                        f'почнеться через 10 хвилин \nПосилання: '
                                        f'{first_subgroup_schedule[forward_time]["link"]}')
                except telebot.apihelper.ApiTelegramException:
                    users["subgroup1"].remove(i)

            with open('users.json', 'w') as js:
                json.dump(users, js)

        if forward_time in second_subgroup_schedule:
            for i in users["subgroup2"]:
                try:
                    bot.send_message(i, f'Пара "{second_subgroup_schedule[forward_time]["name"]}" '
                                        f'почнеться через 10 хвилин \nПосилання: '
                                        f'{second_subgroup_schedule[forward_time]["link"]}')
                except telebot.apihelper.ApiTelegramException:
                    users["subgroup2"].remove(i)

            with open('users.json', 'w') as js:
                json.dump(users, js)

        if current_time in first_subgroup_schedule:
            for i in users["subgroup1"]:
                try:
                    bot.send_message(i, f'Пара: "{first_subgroup_schedule[current_time]["name"]}" почалась. '
                                        f'\nПосилання: {first_subgroup_schedule[current_time]["link"]}')
                except telebot.apihelper.ApiTelegramException:
                    users["subgroup1"].remove(i)

            with open('users.json', 'w') as js:
                json.dump(users, js)

        if current_time in second_subgroup_schedule:
            for i in users["subgroup2"]:
                try:
                    bot.send_message(i, f'Пара: "{second_subgroup_schedule[current_time]["name"]}" почалась.'
                                        f'\nПосилання: {second_subgroup_schedule[current_time]["link"]}')
                except telebot.apihelper.ApiTelegramException:
                    users["subgroup2"].remove(i)

            with open('users.json', 'w') as js:
                json.dump(users, js)

        time.sleep(1)


url = "http://www.google.com"
thr = threading.Thread(target=notify)
thr.start()

while True:
    try:
        requests.get(url, timeout=5)
        print('Connected to the Internet')
        bot.polling(none_stop=True)

    except (requests.ConnectionError, requests.Timeout) as exception:
        logging.error(exception)
        print("No internet connection.")
        time.sleep(5)
