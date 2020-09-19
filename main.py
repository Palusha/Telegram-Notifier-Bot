from datetime import *
import telebot
import json
import config

bot = telebot.TeleBot(config.token)

with open('schedule.json') as js:
    data = json.load(js)

with open('users.json') as js:
    users = json.load(js)

week = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
now = datetime.now()
current_time = now.strftime("%H:%M")
day_schedule = data[week[now.weekday()]]


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


@bot.message_handler(commands=['leave'])
def leave(message):
    if message.chat.id in users['subgroup1']:
        users['subgroup1'].remove(message.chat.id)

    if message.chat.id in users['subgroup2']:
        users['subgroup2'].remove(message.chat.id)

    with open('users.json', 'w') as js:
        json.dump(users, js)


bot.polling(none_stop=True)
