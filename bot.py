import telebot
from flask import Flask, request
import os
import logging

TOKEN = os.environ.get("TOKEN")
ADMINS = [6671597409]
VIP_USERS = set(ADMINS)

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
logging.basicConfig(level=logging.INFO)

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
        "vip_only": "⚠️ Bu funksiya yalnız VIP üçün.\nƏlaqə: @user666321",
        "partner_found": "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!",
        "searching_partner": "⏳ Tərəfdaş axtarılır...",
        "chat_stopped": "🔴 Chat dayandırıldı.",
        "back_to_menu": "↩️ Əsas menyuya qayıtdınız.",
        "vip_contact": "VIP almaq üçün əlaqə saxlayın: @user666321",
        "not_connected": "❗ Siz bağlı deyilsiniz.",
        "partner_left": "⚠️ Tərəfdaş söhbətdən ayrıldı.",
        "invalid_sex": "Zəhmət olmasa 'Kişi' və ya 'Qadın' yazın."
    },
    "ru": {
        "random_search": "👥 Рандомный поиск",
        "gender_search": "⚤ По полу",
        "gay_search": "🌈 Гей поиск",
        "stop": "❌ Остановить",
        "back": "🔙 Назад",
        "buy_vip": "⭐ Купить VIP",
        "welcome": (
            "👋 Привет, {name}!\n\n"
            "Этот бот **анонимен**. Никто не видит ваш профиль и данные.\n\n"
            "💬 Виды поиска:\n"
            "👥 Рандомный — со всеми\n"
            "⚤ По полу — только для VIP\n"
            "🌈 Гей — открытый\n\n"
            "Выберите пункт в меню, чтобы начать."
        ),
        "choose_sex": "Выберите пол:",
        "sex_options": ["Мужчина", "Женщина"],
        "vip_only": "⚠️ Эта функция доступна только VIP.\nСвязь: @user666321",
        "partner_found": "🟢 Партнёр найден. Можно переписываться!",
        "searching_partner": "⏳ Идет поиск партнёра...",
        "chat_stopped": "🔴 Чат остановлен.",
        "
