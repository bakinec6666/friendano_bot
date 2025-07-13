import telebot
from flask import Flask, request
import os
import logging
from functools import wraps
import traceback

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("Не найден TOKEN в переменных окружения")

ADMINS = [6671597409]
VIP_USERS = set(ADMINS)

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

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
        "back_to_menu": "↩️ Вернулись в главное меню.",
        "vip_contact": "Чтобы купить VIP, свяжитесь: @user666321",
        "not_connected": "❗ Вы не подключены.",
        "partner_left": "⚠️ Партнёр вышел из чата.",
        "invalid_sex": "Пожалуйста, выберите 'Мужчина' или 'Женщина'."
    }
}

keyboards_cache = {}

def get_text(user_id, key):
    lang = users.get(user_id, {}).get("lang", "az")
    return MENU_TEXTS[lang][key]

def get_texts(user_id):
    lang = users.get(user_id, {}).get("lang", "az")
    return MENU_TEXTS[lang]

def main_menu(user_id):
    lang = users.get(user_id, {}).get("lang", "az")
    if lang not in keyboards_cache:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        mt = MENU_TEXTS[lang]
        markup.add(mt["random_search"], mt["gender_search"], mt["gay_search"])
        markup.add(mt["stop"], mt["back"], mt["buy_vip"])
        keyboards_cache[lang] = markup
    return keyboards_cache[lang]

def sex_selection_markup(user_id):
    lang = users.get(user_id, {}).get("lang", "az")
    options = MENU_TEXTS[lang]["sex_options"]
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(*options)
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
        try:
            bot.send_message(partner_id, get_text(partner_id, "chat_stopped"), reply_markup=main_menu(partner_id))
        except Exception:
            logging.error(f"Failed to notify partner {partner_id} about chat stop.\n{traceback.format_exc()}")
    users[user_id]["partner"] = None
    remove_from_all_queues(user_id)

def find_partner(user_id, search_type):
    user_data = users.get(user_id)
    if not user_data:
        return None
    if user_data.get("partner"):
        return user_data["partner"]

    user_sex = user_data.get("sex")
    queue = queue_random if search_type == "random" else queue_gender if search_type == "gender" else queue_gay

    for other_id in queue:
        if other_id == user_id:
            continue
        other_data = users.get(other_id)
        if not other_data or other_data.get("partner") is not None:
            continue
        if search_type == "gender":
            other_sex = other_data.get("sex")
            if user_sex is None or other_sex is None:
                continue
            if other_sex == user_sex:
                continue
        users[user_id]["partner"] = other_id
        users[other_id]["partner"] = user_id
        queue.remove(other_id)
        return other_id

    if user_id not in queue:
        queue.append(user_id)
    return None

def admin_only(func):
    @wraps(func)
    def wrapper(message):
        if message.from_user.id not in ADMINS:
            return
        return func(message)
    return wrapper

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🇦🇿 Azərbaycan", "🇷🇺 Русский")

    if user_id not in users:
        users[user_id] = {
            "sex": None,
            "interest": None,
            "partner": None,
            "name": message.from_user.first_name or "",
            "username": message.from_user.username or "",
            "lang": None
        }

    bot.send_message(user_id, "Zəhmət olmasa, dilinizi seçin / Пожалуйста, выберите язык", reply_markup=markup)

@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get("lang") is None)
def language_selection(message):
    user_id = message.from_user.id
    text = message.text.strip()
    logging.info(f"Language selection from {user_id}: {text}")

    if text == "🇦🇿 Azərbaycan":
        users[user_id]["lang"] = "az"
    elif text == "🇷🇺 Русский":
        users[user_id]["lang"] = "ru"
    else:
        msg = bot.send_message(user_id, "Zəhmət olmasa, seçim edin / Пожалуйста, выберите язык")
        bot.register_next_step_handler(msg, language_selection)
        return

    welcome_text = get_text(user_id, "welcome").format(name=users[user_id]["name"])
    bot.send_message(user_id, welcome_text, reply_markup=main_menu(user_id), parse_mode="Markdown")

@bot.message_handler(commands=['ahelp'])
@admin_only
def ahelp(message):
    bot.send_message(message.chat.id, (
        "🔧 *Admin komandaları:*\n"
        "/ahelp — yardım\n"
        "/users — aktiv istifadəçilər\n"
        "/vip_add <id> — VIP əlavə et\n"
        "/vip_remove <id> — VIP çıxar\n"
        "/vip_add_username @username — VIP əlavə et\n"
        "/broadcast <mətn> — yayımla"
    ), parse_mode="Markdown")

@bot.message_handler(commands=['users'])
@admin_only
def list_users(message):
    text = "🔎 Aktiv istifadəçilər:\n"
    for uid, data in users.items():
        name = data.get('name') or ""
        text += f"{uid} - {name}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['vip_add'])
@admin_only
def vip_add(message):
    try:
        new_id = int(message.text.split()[1])
        VIP_USERS.add(new_id)
        bot.send_message(message.chat.id, f"✅ {new_id} artıq VIP-dir")
        bot.send_message(new_id, "🎉 Sizə VIP status verildi!")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_add <id>")

@bot.message_handler(commands=['vip_remove'])
@admin_only
def vip_remove(message):
    try:
        rem_id = int(message.text.split()[1])
        VIP_USERS.discard(rem_id)
        bot.send_message(message.chat.id, f"❌ {rem_id} VIP statusu silindi")
        bot.send_message(rem_id, "⚠️ VIP statusunuz ləğv edildi")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_remove <id>")

@bot.message_handler(commands=['vip_add_username'])
@admin_only
def vip_add_username(message):
    try:
        uname = message.text.split()[1].lstrip("@")
        for uid, data in users.items():
            if data.get("username") == uname:
                VIP_USERS.add(uid)
                bot.send_message(message.chat.id, f"✅ @{uname} artıq VIP-dir")
                bot.send_message(uid, "🎉 Sizə VIP status verildi!")
                return
        bot.send_message(message.chat.id, "❌ İstifadəçi tap
