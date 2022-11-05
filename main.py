import os
import random
import string

import qrcode
import telebot
from pyqiwip2p import QiwiP2P
from telebot import types

from data import bot_token

bot = telebot.TeleBot(bot_token)
chars = list(f'{string.ascii_letters}{string.digits}')


class Create_Check:
    def __init__(self, name, price, idd, token) -> None:
        self.name = name
        self.price = price
        self.id = idd

        self.qiwi_p2p = QiwiP2P(auth_key=token)
        self.bill = self.qiwi_p2p.bill(amount=self.price, lifetime=10)

        self.path = ''.join([random.choice(chars) for _ in range(20)])
        self.img = qrcode.make(self.bill.pay_url)
        self.img.save(f'{self.path}.png')

        with open(f'{self.path}.png', 'rb') as file:
            bot.send_photo(self.id, file)
            bot.send_message(self.id, f'Название: {self.name}\nЦена: {self.price}')
        os.remove(f'{self.path}.png')

    def check_payment(self):
        if self.qiwi_p2p.check(bill_id=self.bill.bill_id).status == "PAID":
            bot.send_message(self.id, f'Название: {self.name}\nЦена: {self.price}\n\nОПЛАТА ПРОИЗВЕДЕНА УСПЕШНО')
            return True
        return False

    def check_overdue(self):
        if self.qiwi_p2p.check(bill_id=self.bill.bill_id).status == "EXPIRED":
            bot.send_message(self.id, f'Название: {self.name}\nЦена: {self.price}\n\nПРОСРОЧЕН')
            return True
        return False

all_users = {}

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = 0
        self.checks = []
        self.token = None
    
    def start(self, message):
        markup = types.ReplyKeyboardMarkup(row_width=1 ,resize_keyboard=True)
        btn1 = types.KeyboardButton('➕ Создать счёт')
        btn2 = types.KeyboardButton('🧾 Мои счета')
        btn3 = types.KeyboardButton('✅ Проверить оплату')
        btn4 = types.KeyboardButton('!!!  ИЗМЕНИТЬ ТОКЕН  !!!')
        markup.row(btn1, btn2)
        markup.row(btn3)
        markup.row(btn4)
        self.send_message('Автор @krouz_cz', reply_markup=markup)

    def main(self, message):
        if message.text == '➕ Создать счёт':
            if self.token == None:
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton('Ссылка', url='https://qiwi.com/api')
                markup.add(btn1)
                self.send_message('Введите свой qiwi token\nЕго можно получить по ссылке', markup)
                return
            self.data = 1
            self.send_message('Введите название заказа')
        elif message.text == '🧾 Мои счета':
            self.data = 0
            self.get_checks(message.from_user.id)
        elif message.text == '✅ Проверить оплату':
            self.data = 0
            self.check_payment()
        elif message.text == '!!!  ИЗМЕНИТЬ ТОКЕН  !!!':
            self.send_message('Введите новый токен')
            self.data = 3
        elif self.data == 1:
            self.name = message.text
            bot.send_message(message.from_user.id, 'Введите цену заказа')
            self.data = 2
        elif self.data == 2:
            self.checks.append(Create_Check(self.name, message.text, message.from_user.id, self.token))
            name = ''
        elif self.data == 3:
            self.token = message.text
            self.data = 0
            self.send_message('Успешно')
        else:
            self.data = 0

    def handler(self, msg):
        if msg.text in ['/start', '/help']:
            self.start(msg)
        else:
            self.main(msg)

    def query_handler(self, call):
        pass
        # print(f'{self.user_id}: {call.data}')

    def send_message(self, msg, reply_markup=None):
        bot.send_message(self.user_id, msg, reply_markup=reply_markup)

    def get_checks(self, msg):
        if len(self.checks) == 0:
            bot.send_message(msg, 'У вас нет активных счетов')
        else:
            for check in self.checks:
                bot.send_message(msg, f'Название: {check.name}\nЦена: {check.price}')

    def check_payment(self):
        for item in self.checks:
            if iiem.check_payment() or item.check_overdue():
                checks.remove(item)
    

@bot.callback_query_handler(func=lambda call:True)
def query_handler(call):
    global all_users

    if not all_users.get(call.from_user.id):
        all_users[call.from_user.id] = User(call.from_user.id)

    all_users.get(call.from_user.id).query_handler(call)


@bot.message_handler(content_types=['text'])
def main(msg):
    global all_users

    if not all_users.get(msg.from_user.id):
        all_users[msg.from_user.id] = User(msg.from_user.id)

    all_users.get(msg.from_user.id).handler(msg)

bot.infinity_polling()
