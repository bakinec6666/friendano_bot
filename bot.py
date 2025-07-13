import telebot
from flask import Flask, request
import os
import logging

# Инициализация
TOKEN = os.environ.get("TOKEN")
ADMINS = [6671597409]
VIP_USERS = set(ADMINS)

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Хранение данных пользователей и очередей для поиска
users = {}
queue_random = []
queue_gender = []
queue_gay = []

MENU_TEXTS = {
    "az": {
        "random_search": "👥 Rəqəmsiz axtarış",
        "gender_search": "⚤ Cinsə görə axtarış",
        "gay_search": "🌈 Gey axtarış",
        "stop": "❌ Dayandır",
        "back": "🔙 Geri",
        "buy_vip": "⭐ VIP almaq",
        "welcome": (
            "👋 Salam, {name}!\n\n"
            "Bu bot **anonimdir**. Heç kim sizin profil və məlumatlarınızı görmür.\n\n"
            "💬 Axtarış növləri:\n"
            "👥 Rəqəmsiz — hər kəslə\n"
            "⚤ Cinsə görə — VIP üçün\n"
            "🌈 Gey — açıq\n\n"
            "Başlamaq üçün menyudan seçim edin."
        ),
        "choose_sex": "Cinsinizi seçin:",
        "sex_options": ["Kişi", "Qadın"],
        "vip_only": "⚠️ Bu funksiya yalnız VIP üçün.\n
