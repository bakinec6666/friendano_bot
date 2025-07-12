import telebot
from flask import Flask, request
import os
import logging

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
ADMINS = [6671597409]
VIP_USERS = set(ADMINS)

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
logging.basicConfig(level=logging.INFO)

users = {}  # user_id -> {sex, interest, partner, name, username, lang}
queue_random = []
queue_gender = []
queue_gay = []

def main_menu(lang="az"):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        markup.add("👥 Случайный поиск", "⚤ По полу", "🌈 Гей поиск")
        markup.add("❌ Остановить", "🔙 Назад", "⭐ Купить VIP")
    else:
        markup.add("👥 Rəqəmsiz axtarış", "⚤ Cinsə görə axtarış", "🌈 Gey axtarış")
        markup.add("❌ Dayandır", "🔙 Geri", "⭐ VIP almaq")
    return markup

def is_vip(user_id):
    return user_id in VIP_USERS

def remove_from_all_queues(user_id):
    for q in (queue_random, queue_gender, queue_gay):
        if user_id in q:
            q.remove(user_id)

def stop_chat(user_id):
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        users[partner_id]["partner"] = None
        remove_from_all_queues(partner_id)
        lang = users.get(partner_id, {}).get("lang", "az")
        msg = "🔴 Tərəfdaş söhbəti dayandırdı." if lang == "az" else "🔴 Партнёр прекратил чат."
        bot.send_message(partner_id, msg)
    users[user_id]["partner"] = None
    remove_from_all_queues(user_id)

def find_partner(user_id, search_type):
    user_sex = users[user_id].get("sex")
    if users[user_id].get("partner"):
        return users[user_id]["partner"]

    queue = queue_random if search_type == "random" else queue_gender if search_type == "gender" else queue_gay

    for other_id in queue:
        if other_id != user_id and users[other_id].get("partner") is None:
            if search_type == "gender":
                other_sex = users[other_id].get("sex")
                if other_sex == user_sex:
                    continue
            users[user_id]["partner"] = other_id
            users[other_id]["partner"] = user_id
            queue.remove(other_id)
            return other_id

    if user_id not in queue:
        queue.append(user_id)
    return None

def sex_selection_markup(lang="az"):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if lang == "ru":
        markup.add("Мужчина", "Женщина")
    else:
        markup.add("Kişi", "Qadın")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        "sex": None,
        "interest": None,
        "partner": None,
        "name": message.from_user.first_name,
        "username": message.from_user.username,
        "lang": None,
    }
    # Спросим язык при старте
    lang_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    lang_markup.add("🇷🇺 Русский", "🇦🇿 Azərbaycan")
    bot.send_message(user_id, "Zəhmət olmasa dil seçin / Пожалуйста, выберите язык:", reply_markup=lang_markup)

@bot.message_handler(func=lambda m: m.text in ["🇷🇺 Русский", "🇦🇿 Azərbaycan"])
def set_language(message):
    user_id = message.from_user.id
    text = message.text
    if text == "🇷🇺 Русский":
        users[user_id]["lang"] = "ru"
        welcome = (
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Этот бот **анонимен**. Никто не видит ваш профиль и данные.\n\n"
            "💬 Типы поиска:\n"
            "👥 Случайный — со всеми\n"
            "⚤ По полу — для VIP\n"
            "🌈 Гей — открытый\n\n"
            "Выберите опцию в меню ниже."
        )
        bot.send_message(user_id, welcome, reply_markup=main_menu("ru"), parse_mode="Markdown")
    else:
        users[user_id]["lang"]
