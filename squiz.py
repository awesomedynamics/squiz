import telebot
from telebot import types
from pymongo import MongoClient
import datetime
from flask import Flask, request
from flask_sslify import SSLify
import os
from mongo_api import update_booking, update_log, register_user, create_registration

#подключаемся к монго
client = MongoClient(os.environ["MONGODB_URL"], username = os.environ["MONGODB_USERNAME"], password = os.environ["MONGODB_PASSWORD"], authSource = os.environ["MONGODB_AUTHSOURCE"])
db = client[os.environ["MONGODB_AUTHSOURCE"]]
bookings_coll = db.bookings
log_coll = db.log

no_keyboard = types.ReplyKeyboardRemove()

bot = telebot.TeleBot(os.environ["TOKEN"])
server = Flask(__name__)
sslify=SSLify(server)

#handling start or help command
@bot.message_handler(commands=['start','help'])
def start_command(message: telebot.types.Message):

    username = str(message.chat.first_name) + " " + str(message.chat.last_name)

    startText = "Привет, " + username + "! Я - бот Squiz!\nЯ зарегистрирую тебя, напомню об игре и вообще я "
    bot.send_message(message.chat.id, startText)

    main_menu(message)


#  обрабатываем кнопку В главное меню
@bot.message_handler(func=lambda message: message.text is not None and message.text == "В главное меню")
def main_menu(message: telebot.types.Message):
    commands = ["Хочу играть!", "Написать нам"]

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    get_phone_button = types.KeyboardButton(text='Оставлю номер, позвоните', request_contact=True)

    markup.row(commands[0], commands[1])
    markup.row(get_phone_button)

    bot.send_message(message.chat.id, "нажми на кнопку - получишь результат",
                     reply_markup=markup)

@bot.message_handler(func=lambda message: message.text is not None and message.text == "Хочу играть!")
def get_games_list(message: telebot.types.Message):

    games_list = [{"event": "игра 100.1",
    "date": "1 апреля",
    "type": "normal",
    "status": "open",
    "site": "HopHead",
    "time": "17:00",
    "address": "бауманская 16"}, {"event": "игра 101",
    "date": "2 апреля",
    "type": "normal",
    "status": "open",
    "site": "Дорогая я перезвоню",
    "time": "17:00",
    "address": "Пятницкий пер.,2"}, {"event": "игра 102",
    "date": "3 апреля",
    "type": "normal",
    "status": "open",
    "site": "25:45",
    "time": "20:00",
    "address": "Пятницкий пер.,2"}]

    for g in games_list:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text = "зарегистрироваться", callback_data=g['event']))
        bot.send_message(message.chat.id, text = g['event'] + "," + g['date'] + "," + g['site']+ ", начало в " + g['time'],
                     reply_markup=markup)

# saving the contact
@bot.message_handler(content_types= ["contact"])
def free_text(message: telebot.types.Message):

    answer = "ура! регистрация прошла успешно!"
    update_log(chat_id=message.chat.id, message=message)
    bot.send_message(message.chat.id, answer)
    update_booking(chat_id=message.chat.id, contact=message.contact.phone_number)
    main_menu(message)

@bot.callback_query_handler(func = lambda call: True)
def event_registration(call):
    create_registration(call)

    reply_markup = types.ForceReply()
    bot.send_message(chat_id=call.from_user.id, text="название команды:", reply_markup=reply_markup)

@bot.message_handler(func = lambda message: message.reply_to_message is not None and message.reply_to_message.text == "название команды:")
def  team_size(message: telebot.types.Message):

    # апдейтим контакт в монго
    update_booking(chat_id=message.chat.id, team_name=message.text)
    reply_markup = types.ForceReply()
    bot.send_message(chat_id=message.chat.id, text="количество человек в команде:", reply_markup=reply_markup)

@bot.message_handler(func = lambda message: message.reply_to_message is not None and message.reply_to_message.text == "количество человек в команде:")
def  team_size(message: telebot.types.Message):

    # апдейтим контакт в монго
    update_booking(chat_id=message.chat.id, team_size=message.text)
    get_phone_button = types.KeyboardButton(text='отправить номер телефона', request_contact=True)
    answer = "осталось оставить номер телефона, нажми на кнопку!"
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(get_phone_button)
    bot.send_message(message.chat.id, answer, reply_markup=markup)

#  handling free text message
@bot.message_handler()
def record_contact(message: telebot.types.Contact):

    answer = "Я пока ничего об этом не знаю, но ты можешь оставить свой номер и мы перезвоним! "
    get_phone_button = types.KeyboardButton(text='Оставлю номер, позвоните', request_contact=True)
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(get_phone_button)
    update_log(chat_id=message.chat.id, message=message)
    bot.send_message(message.chat.id, answer, reply_markup=markup)





@server.route("/bot", methods=['POST','GET'])
def getMessage():
    if request.method == 'POST':
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!",200
    return '<h1>Hello bot</h1>'

@server.route("/")
def webhook():
     bot.remove_webhook()
     bot.set_webhook(url=os.environ["APP_URL"])
     return "!", 200