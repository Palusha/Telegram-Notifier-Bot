from datetime import *
import telebot
import json
import config
import threading
import time
import logging
import requests

week = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
bot = telebot.TeleBot(config.token)

with open('first_subgroup_schedule.json', encoding="utf-8") as js:
    first_subgroup_data = json.load(js)

with open('second_subgroup_schedule.json', encoding="utf-8") as js:
    second_subgroup_data = json.load(js)

with open('users.json') as js:
    users = json.load(js)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"Вітаю {message.from_user.first_name}!\n"
                                      f"Я <b>{bot.get_me().first_name}</b>,"
                                      f" бот який сповіщує студента про початок пари. "
                                      f"\nНапиши /help для перегляду доступних команд.", parse_mode='html')


@bot.message_handler(commands=['subgroup1', 'subgroup2'])
def sub_group(message):
    if message.chat.id in users[message.text[1:]]:
        bot.send_message(message.chat.id, 'Ви вже пристуні у даній підгрупі!')
    else:
        for sub in users.keys():
            if message.chat.id in users[sub]:
                users[sub].remove(message.chat.id)

        users[message.text[1:]].append(message.chat.id)
        with open('users.json', 'w') as js:
            json.dump(users, js)

        if message.text[1:] == 'subgroup1':
            bot.send_message(message.chat.id, 'Ви були додані у першу підгрупу.')
        else:
            bot.send_message(message.chat.id, 'Ви були додані у другу підгрупу.')


@bot.message_handler(commands=['help'])
def show_commands(message):
    bot.send_message(message.chat.id, "/start - Початок роботи"
                                      "\n/subgroup1 - Перша підгрупа"
                                      "\n/subgroup2 - Друга підгрупа"
                                      "\n/leave - Вимкнути сповіщення"
                                      "\n/help - Показати доступні команди")


@bot.message_handler(commands=['leave'])
def leave(message):
    if message.chat.id not in users['subgroup1'] and message.chat.id not in users['subgroup2']:
        bot.send_message(message.chat.id, 'Вас немає у списку підгруп!')
    else:
        for sub in users.keys():
            if message.chat.id in users[sub]:
                users[sub].remove(message.chat.id)

        with open('users.json', 'w') as js:
            json.dump(users, js)

        bot.send_message(message.chat.id, 'Ви успішно вимкнули сповіщення. \nЩоб ввімкнути сповіщення'
                                          ' виберіть підгрупу командою /subgroup1 або /subgroup2')


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

while True:
    thr = threading.Thread(target=notify, daemon=True)
    thr.start()

    try:
        requests.get(url, timeout=5)
        bot.polling(none_stop=True)

    except (requests.ConnectionError, requests.Timeout) as exception:
        logging.error(exception)
        print("No internet connection.")
        time.sleep(5)