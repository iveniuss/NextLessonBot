import telebot
import logging
from time import sleep
import sqlite3
from config import TOKEN, ADMIN_ID

bot = telebot.TeleBot(TOKEN, skip_pending=True)
logging.basicConfig(filename="logs.log", level=logging.INFO, format=' %(asctime)s - %(levelname)s - %(message)s',
                    encoding="utf8")
conn = sqlite3.connect("NLB.db")
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users(user_id INT PRIMARY KEY, groupp INT);")
conn.commit()
allowedusers = []
try:
    cur.execute("SELECT * FROM users")
    u = cur.fetchall()
    for user in u:
        allowedusers.append([user[0], user[1]])
    conn.close()
except Exception as e:
    logging.error("no users" + str(e))
logging.info("start bot")
print("messaging")


@bot.message_handler(commands=['start'])
def start(message):
    log_message(message)
    if not (([message.from_user.id, 1] in allowedusers) or ([message.from_user.id, 2] in allowedusers)):
        keyboard = telebot.types.InlineKeyboardMarkup()
        key_g1 = telebot.types.InlineKeyboardButton(text='1', callback_data='change group 1')
        key_g2 = telebot.types.InlineKeyboardButton(text='2', callback_data='change group 2')
        key_cancel = telebot.types.InlineKeyboardButton(text='отмена', callback_data='cancel')
        keyboard.add(key_g1, key_g2)
        keyboard.add(key_cancel)
        bot.send_message(message.from_user.id,
                         text="Привет, когда закончится пара этот бот напомнит, какая следующая, чтобы тебе не "
                              "пришлось искать расписание. Кроме того, бот постоянно обновляет расписание, "
                              "поэтому ты будешь в курсе изменений.\nЕсли хочешь зарегестрироваться, укажи группу",
                         reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, "Вы уже зарегестрированы")


@bot.message_handler(commands=['db'])
def users(message):
    log_message(message)
    if message.from_user.id == ADMIN_ID:
        bot.send_document(ADMIN_ID, open("NLB.db", 'rb'))


@bot.message_handler(commands=['logs'])
def logs(message):
    log_message(message)
    if message.from_user.id == ADMIN_ID:
        bot.send_document(ADMIN_ID, open("logs.log", 'rb'))


@bot.message_handler(commands=['settings'])
def settings(message):
    log_message(message)
    if not (([message.from_user.id, 1] in allowedusers) or ([message.from_user.id, 2] in allowedusers)):
        bot.send_message(message.from_user.id, "Вы еще не зарегестрированы")
    else:
        u = "0"
        for i in allowedusers:
            if i[0] == message.from_user.id:
                u = str(i[1])
                break
        keyboard = telebot.types.InlineKeyboardMarkup()
        key_change = telebot.types.InlineKeyboardButton(text='изменить группу', callback_data='change')
        key_delete = telebot.types.InlineKeyboardButton(text='удалить', callback_data='delete')
        key_cancel = telebot.types.InlineKeyboardButton(text='отмена', callback_data='cancel')
        keyboard.add(key_change)
        keyboard.add(key_delete)
        keyboard.add(key_cancel)
        bot.send_message(message.from_user.id, reply_markup=keyboard,
                         text=f"Ваша группа - {u}\nХотите изменить группу или удалить себя из списка?")


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "change":
        keyboard = telebot.types.InlineKeyboardMarkup()
        key_g1 = telebot.types.InlineKeyboardButton(text='1', callback_data='change group 1')
        key_g2 = telebot.types.InlineKeyboardButton(text='2', callback_data='change group 2')
        key_cancel = telebot.types.InlineKeyboardButton(text='отмена', callback_data='cancel')
        keyboard.add(key_g1, key_g2)
        keyboard.add(key_cancel)
        bot.edit_message_text("Выберите группу", call.message.chat.id, call.message.id, reply_markup=keyboard)
        logging.info(
            f"user choosing gpoup: {call.message.chat.first_name} {call.message.chat.last_name} : {call.message.chat.username} : {call.message.chat.id}")
    elif call.data == "delete":
        r = 0
        for i in range(len(allowedusers)):
            if allowedusers[i][0] == call.message.chat.id:
                r = i
                break
        allowedusers[r][1] = -2
        rewrite_users()
        bot.edit_message_text("Готово", call.message.chat.id, call.message.id)
        logging.info(
            f"user deleted: {call.message.chat.first_name} {call.message.chat.last_name} : {call.message.chat.username} : {call.message.chat.id}")
    elif call.data == "cancel":
        bot.delete_message(call.message.chat.id, call.message.id)
        logging.info(
            f"user cancel: {call.message.chat.first_name} {call.message.chat.last_name} : {call.message.chat.username} : {call.message.chat.id}")
    elif call.data == "change group 1":
        r = -1
        for i in range(len(allowedusers)):
            if allowedusers[i][0] == call.message.chat.id:
                r = i
                break
        if r == -1:
            allowedusers.append([call.message.chat.id, 1])
        else:
            allowedusers[r][1] = 1
        rewrite_users()
        bot.edit_message_text("Готово", call.message.chat.id, call.message.id)
        logging.info(
            f"user chose group 1: {call.message.chat.first_name} {call.message.chat.last_name} : {call.message.chat.username} : {call.message.chat.id}")
    elif call.data == "change group 2":
        r = -1
        for i in range(len(allowedusers)):
            if allowedusers[i][0] == call.message.chat.id:
                r = i
                break
        if r == -1:
            allowedusers.append([call.message.chat.id, 2])
        else:
            allowedusers[r][1] = 2
        rewrite_users()
        bot.edit_message_text("Готово", call.message.chat.id, call.message.id)
        logging.info(
            f"user chose group 2: {call.message.chat.first_name} {call.message.chat.last_name} : {call.message.chat.username} : {call.message.chat.id}")


@bot.message_handler(content_types=['text'])
def text(message):
    log_message(message)
    bot.send_message(message.from_user.id,
                     "Что Вы хотите сделать?\n/start - регистрация\n/settings - настройки")


def rewrite_users():
    conn = sqlite3.connect("NLB.db")
    cur = conn.cursor()
    for user1 in allowedusers:
        if user1[1] != -2:
            user = (user1[0], user1[1])
            cur.execute("DELETE FROM users WHERE user_id=?;", (user1[0],))
            cur.execute("INSERT INTO users VALUES (?,?);", user)
        else:
            cur.execute("DELETE FROM users WHERE user_id=?;", (user1[0],))
    conn.commit()
    conn.close()


def log_message(m):
    logging.info(
        f"msg: {m.text} : {m.from_user.first_name} {m.from_user.last_name} : {m.from_user.username} : {m.from_user.id}")


while True:
    try:
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        logging.error("network trouble" + str(e))
        sleep(15)
