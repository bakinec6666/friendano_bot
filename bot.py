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
        "back_to_menu": "↩️ Вернулись в главное меню.",
        "vip_contact": "Чтобы купить VIP, свяжитесь: @user666321",
        "not_connected": "❗ Вы не подключены.",
        "partner_left": "⚠️ Партнёр вышел из чата.",
        "invalid_sex": "Пожалуйста, выберите 'Мужчина' или 'Женщина'."
    }
}

def get_text(user_id, key):
    lang = users.get(user_id, {}).get("lang", "az")
    return MENU_TEXTS[lang][key]

def main_menu(user_id):
    lang = users.get(user_id, {}).get("lang", "az")
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    mt = MENU_TEXTS[lang]
    markup.add(mt["random_search"], mt["gender_search"], mt["gay_search"])
    markup.add(mt["stop"], mt["back"], mt["buy_vip"])
    return markup

def sex_selection_markup(user_id):
    lang = users.get(user_id, {}).get("lang", "az")
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    options = MENU_TEXTS[lang]["sex_options"]
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
            bot.send_message(partner_id, get_text(partner_id, "chat_stopped"))
        except:
            pass
    users[user_id]["partner"] = None
    remove_from_all_queues(user_id)

def find_partner(user_id, search_type):
    user_sex = users[user_id].get("sex")
    if users[user_id].get("partner"):
        return users[user_id]["partner"]

    if search_type == "random":
        queue = queue_random
    elif search_type == "gender":
        queue = queue_gender
    else:
        queue = queue_gay

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

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🇦🇿 Azərbaycan", "🇷🇺 Русский")
    bot.send_message(user_id, "Zəhmət olmasa, seçim edin / Пожалуйста, выберите язык", reply_markup=markup)

    users[user_id] = {
        "sex": None,
        "interest": None,
        "partner": None,
        "name": message.from_user.first_name or "",
        "username": message.from_user.username or "",
        "lang": None
    }

@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get("lang") is None)
def language_selection(message):
    user_id = message.from_user.id
    text = message.text.strip()

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
def ahelp(message):
    if message.from_user.id not in ADMINS:
        return
    bot.send_message(message.chat.id, (
        "🔧 *Admin komandaları:*\n"
        "/ahelp — это помощь\n"
        "/users — активные пользователи\n"
        "/vip_add <id>\n"
        "/vip_remove <id>\n"
        "/vip_add_username @username\n"
        "/broadcast <текст> — рассылка сообщений"
    ), parse_mode="Markdown")

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id not in ADMINS:
        return
    text = "🔎 Активные пользователи:\n"
    for uid, data in users.items():
        text += f"{uid} - {data.get('name', '')}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['vip_add'])
def vip_add(message):
    if message.from_user.id not in ADMINS:
        return
    try:
        new_id = int(message.text.split()[1])
        VIP_USERS.add(new_id)
        bot.send_message(message.chat.id, f"✅ {new_id} теперь VIP")
        bot.send_message(new_id, "🎉 Вам выдан VIP статус!")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ Использование: /vip_add <id>")

@bot.message_handler(commands=['vip_remove'])
def vip_remove(message):
    if message.from_user.id not in ADMINS:
        return
    try:
        rem_id = int(message.text.split()[1])
        VIP_USERS.discard(rem_id)
        bot.send_message(message.chat.id, f"❌ {rem_id} VIP статус снят")
        bot.send_message(rem_id, "⚠️ Ваш VIP статус был снят")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ Использование: /vip_remove <id>")

@bot.message_handler(commands=['vip_add_username'])
def vip_add_username(message):
    if message.from_user.id not in ADMINS:
        return
    try:
        uname = message.text.split()[1].replace("@", "")
        for uid, data in users.items():
            if data.get("username") == uname:
                VIP_USERS.add(uid)
                bot.send_message(message.chat.id, f"✅ @{uname} теперь VIP")
                bot.send_message(uid, "🎉 Вам выдан VIP статус!")
                return
        bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ Использование: /vip_add_username @username")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id not in ADMINS:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        return bot.send_message(message.chat.id, "⚠️ Использование: /broadcast <текст>")
    count = 0
    for uid in list(users):
        try:
            bot.send_message(uid, f"📢 {text}")
            count += 1
        except Exception:
            continue
    bot.send_message(message.chat.id, f"✅ Сообщение отправлено: {count} пользователям")

@bot.message_handler(func=lambda m: True, content_types=['text'])
def chat_handler(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in users or users[user_id].get("lang") is None:
        start(message)
        return

    if text == get_text(user_id, "random_search"):
        stop_chat(user_id)
        p = find_partner(user_id, "random")
        if p:
            bot.send_message(user_id, get_text(user_id, "partner_found"))
            bot.send_message(p, get_text(p, "partner_found"))
        else:
            bot.send_message(user_id, get_text(user_id, "searching_partner"))

    elif text == get_text(user_id, "gender_search"):
        if not is_vip(user_id):
            bot.send_message(user_id, get_text(user_id, "vip_only"))
            return
        if not users[user_id]["sex"]:
            msg = bot.send_message(user_id, get_text(user_id, "choose_sex"), reply_markup=sex_selection_markup(user_id))
            bot.register_next_step_handler(msg, set_sex)
            return
        stop_chat(user_id)
        p = find_partner(user_id, "gender")
        if p:
            bot.send_message(user_id, get_text(user_id, "partner_found"))
            bot.send_message(p, get_text(p, "partner_found"))
        else:
            bot.send_message(user_id, get_text(user_id, "searching_partner"))

    elif text == get_text(user_id, "gay_search"):
        stop_chat(user_id)
        p = find_partner(user_id, "gay")
        if p:
            bot.send_message(user_id, get_text(user_id, "partner_found"))
            bot.send_message(p, get_text(p, "partner_found"))
        else:
            bot.send_message(user_id, get_text(user_id, "searching_partner"))

    elif text == get_text(user_id, "stop"):
        stop_chat(user_id)
        bot.send_message(user_id, get_text(user_id, "chat_stopped"), reply_markup=main_menu(user_id))

    elif text == get_text(user_id, "back"):
        stop_chat(user_id)
        bot.send_message(user_id, get_text(user_id, "back_to_menu"), reply_markup=main_menu(user_id))

    elif text == get_text(user_id, "buy_vip"):
        bot.send_message(user_id, get_text(user_id, "vip_contact"))

    else:
        partner_id = users[user_id].get("partner")
        if partner_id:
            try:
                bot.send_message(partner_id, text)
            except Exception:
                stop_chat(user_id)
                bot.send_message(user_id, get_text(user_id, "partner_left"))
        else:
            bot.send_message(user_id, get_text(user_id, "not_connected"), reply_markup=main_menu(user_id))

def set_sex(message):
    user_id = message.from_user.id
    sex = message.text.strip()
    lang = users[user_id].get("lang", "az")
    valid_options = MENU_TEXTS[lang]["sex_options"]
    if sex not in valid_options:
        msg = bot.send_message(user_id, get_text(user_id, "invalid_sex"))
        bot.register_next_step_handler(msg, set_sex)
        return
    users[user_id]["sex"] = sex
    bot.send_message(user_id, f"{get_text(user_id, 'choose_sex')} {sex}. {get_text(user_id, 'searching_partner')}")
    stop_chat(user_id)
    p = find_partner(user_id, "gender")
    if p:
        bot.send_message(user_id, get_text(user_id, "partner_found"))
        bot.send_message(p, get_text(p, "partner_found"))
    else:
        bot.send_message(user_id, get_text(user_id, "searching_partner"))

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        try:
            bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
        except Exception:
            pass

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        try:
            bot.send_video(partner_id, message.video.file_id, caption=message.caption)
        except Exception:
            pass

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        try:
            bot.send_voice(partner_id, message.voice.file_id)
        except Exception:
            pass

@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        try:
            bot.send_sticker(partner_id, message.sticker.file_id)
        except Exception:
            pass

@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@server.route("/")
def index():
    return "Bot işləyir! / Бот работает!", 200

bot.remove_webhook()
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")
if WEBHOOK_URL:
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
