import telebot
from flask import Flask, request
import os
import logging
import json

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
ADMINS = [6671597409]
VIP_USERS = set(ADMINS)

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
logging.basicConfig(level=logging.INFO)

users = {}  # user_id -> {sex, interest, partner, name, username}
queue_random = []
queue_gender = []
queue_gay = []

# Словарь для статистики сообщений и уровней
try:
    with open('user_activity.json', 'r') as f:
        user_activity = json.load(f)
except FileNotFoundError:
    user_activity = {}

def save_user_activity():
    with open('user_activity.json', 'w') as f:
        json.dump(user_activity, f)

def check_level_up(user_id):
    user_id_str = str(user_id)
    data = user_activity.get(user_id_str, {"messages": 0, "level": 0})
    data["messages"] += 1
    new_level = data["messages"] // 10  # Каждые 10 сообщений — уровень выше
    if new_level > data["level"]:
        data["level"] = new_level
        bot.send_message(user_id, f"🎉 Təbriklər! Sizin yeni səviyyəniz: {new_level}")
    user_activity[user_id_str] = data
    save_user_activity()

def main_menu(lang="az"):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "az":
        markup.add("👥 Rəqəmsiz axtarış", "⚤ Cinsə görə axtarış", "🌈 Gey axtarış")
        markup.add("❌ Dayandır", "🔙 Geri", "⭐ VIP almaq")
    else:  # ru
        markup.add("👥 Рандомный поиск", "⚤ Поиск по полу", "🌈 Гей поиск")
        markup.add("❌ Стоп", "🔙 Назад", "⭐ Купить VIP")
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
        bot.send_message(partner_id, "🔴 Tərəfdaş söhbəti dayandırdı.")
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
    if lang == "az":
        markup.add("Kişi", "Qadın")
    else:
        markup.add("Мужчина", "Женщина")
    return markup

def detect_language_from_country(country_code):
    # Пример: AZ -> азербайджанский, RU -> русский
    if country_code == "RU":
        return "ru"
    return "az"

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Сохраняем язык пользователя для меню
    # Попробуем получить country_code из Telegram (есть в message.from_user.language_code)
    # Но это не всегда точно, поэтому можно через IP или отдельный сервис
    lang = "az"
    if message.from_user.language_code:
        if message.from_user.language_code.startswith("ru"):
            lang = "ru"
    users[user_id] = {
        "sex": None,
        "interest": None,
        "partner": None,
        "name": message.from_user.first_name,
        "username": message.from_user.username,
        "lang": lang
    }

    welcome_az = (
        f"👋 Salam, {message.from_user.first_name}!\n\n"
        "Bu bot **anonimdir**. Heç kim sizin profil və məlumatlarınızı görmür.\n\n"
        "💬 Axtarış növləri:\n"
        "👥 Rəqəmsiz — hər kəslə\n"
        "⚤ Cinsə görə — VIP üçün\n"
        "🌈 Gey — açıq\n\n"
        "Başlamaq üçün menyudan seçim edin."
    )
    welcome_ru = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Этот бот **анонимен**. Никто не видит ваш профиль и данные.\n\n"
        "💬 Типы поиска:\n"
        "👥 Рандомный — со всеми\n"
        "⚤ Поиск по полу — для VIP\n"
        "🌈 Гей — открытый\n\n"
        "Выберите в меню, чтобы начать."
    )

    welcome = welcome_ru if lang == "ru" else welcome_az
    bot.send_message(user_id, welcome, reply_markup=main_menu(lang), parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    data = user_activity.get(str(user_id), {"messages": 0, "level": 0})
    lang = users.get(user_id, {}).get("lang", "az")
    if lang == "ru":
        text = f"📊 Ваши статистики:\nСообщений отправлено: {data['messages']}\nУровень: {data['level']}"
    else:
        text = f"📊 Statistikalarınız:\nGöndərilən mesajlar: {data['messages']}\nSəviyyə: {data['level']}"
    bot.send_message(user_id, text)

@bot.message_handler(commands=['ahelp'])
def ahelp(message):
    if message.from_user.id not in ADMINS:
        return
    bot.send_message(message.chat.id, (
        "🔧 *Admin komandaları:*\n"
        "/ahelp — bu yardım\n"
        "/users — aktiv istifadəçilər\n"
        "/vip_add <id>\n"
        "/vip_remove <id>\n"
        "/vip_add_username @username\n"
        "/broadcast <text> — mesaj göndər"
    ), parse_mode="Markdown")

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id not in ADMINS:
        return
    text = "🔎 Aktiv istifadəçilər:\n"
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
        bot.send_message(message.chat.id, f"✅ {new_id} VIP edildi")
        bot.send_message(new_id, "🎉 Sizə VIP status verildi!")
    except:
        bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_add <id>")

@bot.message_handler(commands=['vip_remove'])
def vip_remove(message):
    if message.from_user.id not in ADMINS:
        return
    try:
        rem_id = int(message.text.split()[1])
        VIP_USERS.discard(rem_id)
        bot.send_message(message.chat.id, f"❌ {rem_id} VIP silindi")
        bot.send_message(rem_id, "⚠️ VIP statusunuz ləğv edildi")
    except:
        bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_remove <id>")

@bot.message_handler(commands=['vip_add_username'])
def vip_add_username(message):
    if message.from_user.id not in ADMINS:
        return
    try:
        uname = message.text.split()[1].replace("@", "")
        for uid, data in users.items():
            if data.get("username") == uname:
                VIP_USERS.add(uid)
                bot.send_message(message.chat.id, f"✅ @{uname} VIP oldu")
                bot.send_message(uid, "🎉 Sizə VIP status verildi!")
                return
        bot.send_message(message.chat.id, "❌ İstifadəçi tapılmadı")
    except:
        bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_add_username @username")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id not in ADMINS:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        return bot.send_message(message.chat.id, "⚠️ İstifadə: /broadcast <text>")
    count = 0
    for uid in list(users):
        try:
            bot.send_message(uid, f"📢 {text}")
            count += 1
        except:
            continue
    bot.send_message(message.chat.id, f"✅ Mesaj göndərildi: {count} nəfərə")

@bot.message_handler(func=lambda m: True, content_types=['text'])
def chat_handler(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in users:
        users[user_id] = {"sex": None, "interest": None, "partner": None,
                          "name": message.from_user.first_name, "username": message.from_user.username, "lang": "az"}

    # Обновляем статистику и проверяем уровень
    check_level_up(user_id)

    lang = users[user_id].get("lang", "az")

    if (lang == "az" and text == "👥 Rəqəmsiz axtarış") or (lang == "ru" and text == "👥 Рандомный поиск"):
        stop_chat(user_id)
        p = find_partner(user_id, "random")
        if p:
            bot.send_message(user_id, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!" if lang=="az" else "🟢 Партнер найден. Можете писать!")
            bot.send_message(p, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!" if lang=="az" else "🟢 Партнер найден. Можете писать!")
        else:
            bot.send_message(user_id, "⏳ Tərəfdaş axtarılır..." if lang=="az" else "⏳ Партнер ищется...")

    elif (lang == "az" and text == "⚤ Cinsə görə axtarış") or (lang == "ru" and text == "⚤ Поиск по полу"):
        if not is_vip(user_id):
            bot.send_message(user_id, "⚠️ Bu funksiya yalnız VIP üçün.\nƏlaqə: @user666321" if lang=="az" else "⚠️ Эта функция только для VIP.\nСвязь: @user666321")
            return
        if not users[user_id]["sex"]:
            msg = bot.send_message(user_id, "Cinsinizi seçin:" if lang=="az" else "Выберите пол:", reply_markup=sex_selection_markup(lang))
            bot.register_next_step_handler(msg, set_sex)
            return
        stop_chat(user_id)
        p = find_partner(user_id, "gender")
        if p:
            bot.send_message(user_id, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!" if lang=="az" else "🟢 Партнер найден. Можете писать!")
            bot.send_message(p, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!" if lang=="az" else "🟢 Партнер найден. Можете писать!")
        else:
            bot.send_message(user_id, "⏳ Tərəfdaş axtarılır..." if lang=="az" else "⏳ Партнер ищется...")

    elif (lang == "az" and text == "🌈 Gey axtarış") or (lang == "ru" and text == "🌈 Гей поиск"):
        stop_chat(user_id)
        p = find_partner(user_id, "gay")
        if p:
            bot.send_message(user_id, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!" if lang=="az" else "🟢 Партнер найден. Можете писать!")
            bot.send_message(p, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!" if lang=="az" else "🟢 Партнер найден. Можете писать!")
        else:
            bot.send_message(user_id, "⏳ Tərəfdaş axtarılır..." if lang=="az" else "⏳ Партнер ищется...")

    elif (lang == "az" and text == "❌ Dayandır") or (lang == "ru" and text == "❌ Стоп"):
        stop_chat(user_id)
        bot.send_message(user_id, "🔴 Chat dayandırıldı." if lang=="az" else "🔴 Чат остановлен.", reply_markup=main_menu(lang))

    elif (lang == "az" and text == "🔙 Geri") or (lang == "ru" and text == "🔙 Назад"):
        stop_chat(user_id)
        bot.send_message(user_id, "↩️ Əsas menyuya qayıtdınız." if lang=="az" else "↩️ Вы вернулись в главное меню.", reply_markup=main_menu(lang))

    elif (lang == "az" and text == "⭐ VIP almaq") or (lang == "ru" and text == "⭐ Купить VIP"):
        bot.send_message(user_id, "VIP almaq üçün əlaqə saxlayın: @user666321" if lang=="az" else "Связаться для покупки VIP: @user666321")

    else:
        partner_id = users[user_id].get("partner")
        if partner_id:
            try:
                bot.send_message(partner_id, text)
            except:
                stop_chat(user_id)
                bot.send_message(user_id, "⚠️ Tərəfdaş söhbətdən ayrıldı." if lang=="az" else "⚠️ Партнер покинул чат.")
        else:
            bot.send_message(user_id, "❗ Siz bağlı deyilsiniz." if lang=="az" else "❗ Вы не подключены.", reply_markup=main_menu(lang))

def set_sex(message):
    user_id = message.from_user.id
    sex = message.text.strip()
    lang = users[user_id].get("lang", "az")
    if (lang == "az" and sex not in ["Kişi", "Qadın"]) or (lang == "ru" and sex not in ["Мужчина", "Женщина"]):
        msg = bot.send_message(user_id, "Zəhmət olmasa 'Kişi' və ya 'Qadın' yazın." if lang=="az" else "Пожалуйста, введите 'Мужчина' или 'Женщина'.")
        return bot.register_next_step_handler(msg, set_sex)
    users[user_id]["sex"] = sex
    bot.send_message(user_id, ("Cinsiniz: " + sex + ". Axtarış başlayır...") if lang=="az" else ("Ваш пол: " + sex + ". Поиск начинается..."))
    stop_chat(user_id)
    p = find_partner(user_id, "gender")
    if p:
        bot.send_message(user_id, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!" if lang=="az" else "🟢 Партнер найден. Можете писать!")
        bot.send_message(p, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!" if lang=="az" else "🟢 Партнер найден. Можете писать!")
    else:
        bot.send_message(user_id, "⏳ Tərəfdaş axtarılır..." if lang=="az" else "⏳ Партнер ищется...")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        bot.send_video(partner_id, message.video.file_id, caption=message.caption)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        bot.send_voice(partner_id, message.voice.file_id)

@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        bot.send_sticker(partner_id, message.sticker.file_id)

@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@server.route("/")
def index():
    return "Bot işləyir!", 200

bot.remove_webhook()
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")
if WEBHOOK_URL:
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

if __name__ == "__main__":
    port = int(os.environ
