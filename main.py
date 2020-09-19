from datetime import *
import telebot
import json
import config
import threading
import time

bot = telebot.TeleBot(config.token)

with open('schedule.json') as js:
    data = json.load(js)

with open('users.json') as js:
    users = json.load(js)

week = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"Вітаю {message.from_user.first_name}!\n"
                                      f"Я <b>{bot.get_me().first_name}</b>,"
                                      f" бот який сповіщує студента про початок пари.", parse_mode='html')


@bot.message_handler(commands=['subgroup1', 'subgroup2'])
def sub_group(message):
    print(message.text)

    if message.chat.id in users['subgroup1']:
        users['subgroup1'].remove(message.chat.id)

    if message.chat.id in users['subgroup2']:
        users['subgroup2'].remove(message.chat.id)

    users[message.text[1:]].append(message.chat.id)
    with open('users.json', 'w') as js:
        json.dump(users, js)


@bot.message_handler(commands=['help'])
def show_commands(message):
    bot.send_message(message.chat.id, "/start - Початок роботи"
                                      "\n/subgroup1 - Перша підгрупа"
                                      "\n/subgroup2 - Друга підгрупа"
                                      "\n/leave - Вимкнути сповіщення"
                                      "\n/help - Показати доступні команди")


@bot.message_handler(commands=['leave'])
def leave(message):
    if message.chat.id in users['subgroup1']:
        users['subgroup1'].remove(message.chat.id)

    if message.chat.id in users['subgroup2']:
        users['subgroup2'].remove(message.chat.id)

    with open('users.json', 'w') as js:
        json.dump(users, js)


@bot.message_handler(content_types=['text'])
def show(message):
    print(message.text)


def notify():
    count = 0
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        forward_time = current_time[0:3] + str(int(current_time[3:5]) + 10) + current_time[5:]

        if current_time == "00:00:00":
            count = 0

        if count == 0:
            day_schedule = data[week[now.weekday()]]
            count = 1

        if forward_time in day_schedule:
            for i in users["subgroup1"]:
                bot.send_message(i, f'Скоро розпочнеться пара: "{day_schedule[forward_time]["subgroup1"]["name"]}"'
                                    f'\nПосилання: google.com')

            for i in users["subgroup2"]:
                bot.send_message(i, f'Скоро розпочнеться пара: "{day_schedule[forward_time]["subgroup2"]["name"]}"'
                                    f'\nПосилання: google.com')

        if current_time in day_schedule:
            for i in users["subgroup1"]:
                bot.send_message(i, f'Пара: "{day_schedule[current_time]["subgroup1"]["name"]}" почалась '
                                    f'\nПосилання: google.com')

            for i in users["subgroup2"]:
                bot.send_message(i, f'Пара: "{day_schedule[current_time]["subgroup2"]["name"]}" почалась '
                                    f'\nПосилання: google.com')
        time.sleep(1)


thr = threading.Thread(target=notify, args=())
thr.start()

bot.polling(none_stop=True)
