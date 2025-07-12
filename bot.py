import telebot
from flask import Flask, request
import os
import logging

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
ADMINS = [6671597409]
VIP_USERS = set(ADMINS)  # Используем set для удобства

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

logging.basicConfig(level=logging.INFO)

users = {}
queue_random = []
queue_gender = []
queue_gay = []

# Лимит сообщений для обычных пользователей
MESSAGE_LIMIT = 20

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👥 Rəqəmsiz axtarış", "⚤ Cinsə görə axtarış", "🌈 Gey axtarış")
    markup.add("❌ Dayandır", "⭐ VIP almaq")
    return markup

def is_vip(user_id):
    return user_id in VIP_USERS

def check_limit(user_id):
    if is_vip(user_id):
        return True
    user = users.get(user_id)
    if user is None:
        users[user_id] = {"sex": None, "interest": None, "partner": None, "messages_sent": 0}
        return True
    if user.get("messages_sent", 0) < MESSAGE_LIMIT:
        return True
    else:
        return False

def increment_messages(user_id):
    if user_id not in users:
        users[user_id] = {"sex": None, "interest": None, "partner": None, "messages_sent": 0}
    users[user_id]["messages_sent"] = users[user_id].get("messages_sent", 0) + 1

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    logging.info(f"/start от пользователя {user_id}")
    users[user_id] = {"sex": None, "interest": None, "partner": None, "messages_sent": 0}
    bot.send_message(user_id, "👋 Xoş gəlmisiniz! Menyudan seçim edin:", reply_markup=main_menu())

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        bot.send_message(user_id, "⛔ Bu komanda yalnız adminlər üçündür.")
        return
    bot.send_message(
        user_id,
        "👑 Siz adminsiniz. VIP funksiyalar aktivdir.\n\n"
        "/vip_add <id> - VIP əlavə et\n"
        "/vip_remove <id> - VIP sil"
    )

@bot.message_handler(commands=['vip_add'])
def vip_add(message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        bot.send_message(user_id, "⛔ Bu komanda yalnız adminlər üçündür.")
        return
    try:
        args = message.text.split()
        new_vip = int(args[1])
    except (IndexError, ValueError):
        bot.send_message(user_id, "⚠️ İstifadə: /vip_add <user_id>")
        return
    VIP_USERS.add(new_vip)
    bot.send_message(user_id
