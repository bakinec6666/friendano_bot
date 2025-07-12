import telebot
from flask import Flask, request
import os
import logging

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
ADMINS = [6671597409]
VIP_USERS = set(ADMINS)  # Используем set для удобства
BANNED_USERS = set()

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

logging.basicConfig(level=logging.INFO)

users = {}
queue_random = []
queue_gender = []
queue_gay = []

# Лимит сообщений для обычных пользователей (исключая рандом и гей поиск)
MESSAGE_LIMIT = 20

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👥 Rəqəmsiz axtarış", "⚤ Cinsə görə axtarış", "🌈 Gey axtarış")
    markup.add("❌ Dayandır", "⭐ VIP almaq")
    return markup

def is_vip(user_id):
    return user_id in VIP_USERS

def check_limit(user_id, check_media_limit=True):
    if is_vip(user_id):
        return True
    user = users.get(user_id)
    if user is None:
        users[user_id] = {"sex": None, "interest": None, "partner": None, "messages_sent": 0}
        return True
    # Для сообщений в рандомном и гей чатах лимит не проверяем, для других да
    if not check_media_limit:
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
    bot.send_message(user_id, "👑 Siz adminsiniz. VIP funksiyalar aktivdir.\n\n"
                              "/vip_add <id> - VIP əlavə et\n"
                              "/vip_remove <id> - VIP sil\n"
                              "/ban <id> - İstifadəçini blokla\n"
                              "/unban <id> - Blokdan çıxar\n"
                              "/stats - Statistikaya bax\n"
                              "/ahelp - Admin komandaları")

@bot.message_handler(commands=['ahelp'])
def ahelp(message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        bot.send_message(user_id, "⛔ Bu komanda yalnız adminlər üçündür.")
        return
    help_text = (
        "👑 *Admin komandaları:*\n\n"
        "/vip_add <user_id> - İstifadəçini VIP et\n"
        "/vip_remove <user_id> - İstifadəçinin VIP statusunu sil\n"
        "/ban <user_id> - İstifadəçini blokla\n"
        "/unban <user_id> - Blokdan çıxar\n"
        "/stats - İstifadəçi statistikası\n"
        "/ahelp - Bu kömək mesajı\n"
    )
    bot.send_message(user_id, help_text, parse_mode="Markdown")

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
    bot.send_message(user_id, f"✅ İstifadəçi {new_vip} VIP olaraq əlavə edildi.")
    bot.send_message(new_vip, "🎉 Sizə VIP status verildi!")

@bot.message_handler(commands=['vip_remove'])
def vip_remove(message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        bot.send_message(user_id, "⛔ Bu komanda yalnız adminlər üçündür.")
        return
    try:
        args = message.text.split()
        rem_vip = int(args[1])
    except (IndexError, ValueError):
        bot.send_message(user_id, "⚠️ İstifadə: /vip_remove <user_id>")
        return
    if rem_vip in VIP_USERS:
        VIP_USERS.remove(rem_vip)
        bot.send_message(user_id, f"✅ İstifadəçi {rem_vip} VIP-dən silindi.")
        bot.send_message(rem_vip, "⚠️ Sizin VIP statusunuz silindi.")
    else:
        bot.send_message(user_id, f"❌ İstifadəçi {rem_vip} VIP siyahısında deyil.")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        bot.send_message(user_id, "⛔ Bu komanda yalnız adminlər üçündür.")
        return
    try:
        args = message.text.split()
        ban_id = int(args[1])
    except (IndexError, ValueError):
        bot.send_message(user_id, "⚠️ İstifadə: /ban <user_id>")
        return
    BANNED_USERS.add(ban_id)
    bot.send_message(user_id, f"⛔ İstifadəçi {ban_id} bloklandı.")
    bot.send_message(ban_id, "🚫 Siz bloklandınız. Botdan istifadə edə bilməzsiniz.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        bot.send_message(user_id, "⛔ Bu komanda yalnız adminlər üçündür.")
        return
    try:
        args = message.text.split()
        unban_id = int(args[1])
    except (IndexError, ValueError):
        bot.send_message(user_id, "⚠️ İstifadə: /unban <user_id>")
        return
    if unban_id in BANNED_USERS:
        BANNED_USERS.remove(unban_id)
        bot.send_message(user_id, f"✅ İstifadəçi {unban_id} blokdan çıxdı.")
        bot.send_message(unban_id, "✅ Blokdan çıxdınız. İndi botdan istifadə edə bilərsiniz.")
    else:
        bot.send_message(user_id, f"❌ İstifadəçi {unban_id} blokda deyil.")

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        bot.send_message(user_id, "⛔ Bu komanda yalnız adminlər üçündür.")
        return

    total_users = len(users)
    vip_count = len(VIP_USERS)
    banned_count = len(BANNED_USERS)

    lines = [
        f"👥 Ümumi istifadəçilər: {total_users}",
        f"⭐ VIP istifadəçilər: {vip_count}",
        f"⛔ Bloklananlar: {banned_count}",
        "\n📋 İstifadəçi siyahısı:"
    ]

    for uid, data in users.items():
        try:
            user_info = bot.get_chat(uid)
            username = f"@{user_info.username}" if user_info.username else f"{user_info.first_name}"
        except Exception:
            username = "Naməlum istifadəçi"
        lines.append(f"{uid} - {username}")

    bot.send_message(user_id, "\n".join(lines))

@bot.message_handler(func=lambda m: m.text == "⭐ VIP almaq")
def vip_info(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "💎 *VIP funksiyalar:*\n\n⚤ Cinsə görə axtarış\n\nVIP almaq üçün adminə yazın: @admin", parse_mode="Markdown")

def find_partner(queue, user_id):
    logging.info(f"Поиск партнёра для {user_id} в очереди {queue}")
    for uid in queue:
        if uid != user_id and users.get(uid) and users[uid].get("partner") is None:
            queue.remove(uid)
            users[user_id]["partner"] = uid
            users[uid]["partner"] = user_id
            bot.send_message(user_id, "✅ Partnyor tapıldı! İndi yaza bilərsiniz.")
            bot.send_message(uid, "✅ Partnyor tapıldı! İndi yaza bilərsiniz.")
            return True
    if user_id not in queue:
        queue.append(user_id)
        bot.send_message(user_id, "⏳ Partnyor tapılmadı. Zəhmət olmasa gözləyin...")
    return False

@bot.message_handler(func=lambda m: m.text == "👥 Rəqəmsiz axtarış")
def random_search(message):
    user_id = message.from_user.id
    if user_id in BANNED_USERS:
        bot.send_message(user_id, "⛔ Siz bloklanmısınız. Botdan istifadə edə bilməzsiniz.")
        return
    users[user_id]["partner"] = None
    if user_id in queue_random:
        queue_random.remove(user_id)
    find_partner(queue_random, user_id)

@bot.message_handler(func=lambda m: m.text == "⚤ Cinsə görə axtarış")
def gender_search(message):
    user_id = message.from_user.id
    if user_id not in VIP_USERS:
        bot.send_message(user_id, "⛔ Bu funksiya yalnız VIP istifadəçilər üçündür.\nVIP almaq üçün @admin ilə əlaqə saxlayın.")
        return
    if user_id in BANNED_USERS:
        bot.send_message(user_id, "⛔ Siz bloklanmısınız. Botdan istifadə edə bilməzsiniz.")
        return
    if not check_limit(user_id):
        bot.send_message(user_id, f"❌ Siz gündə {MESSAGE_LIMIT} mesaj limitini keçdiniz. VIP olun və limitsiz istifadə edin.")
        return
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👦 Mən kişiyəm", "👧 Mən qadınam")
    bot.send_message(user_id, "Cinsinizi seçin:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["👦 Mən kişiyəm", "👧 Mən qadınam"])
def choose_interest_gender(message):
    user_id = message.from_user.id
    sex = "kişi" if "kişiyəm" in message.text else "qadın"
    users[user_id]["sex"] = sex
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧔 Mən kişiylə söhbət etmək istəyirəm", "👩 Mən qadınla söhbət etmək istəyirəm")
    bot.send_message(user_id, "Kimlə söhbət etmək istəyirsiniz?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["🧔 Mən kişiylə söhbət etmək istəyirəm", "👩 Mən qadınla söhbət etmək istəyirəm"])
def do_gender_match(message):
    user_id = message.from_user.id
    interest = "kişi" if "kişiylə" in message.text else "qadın"
    if user_id in BANNED_USERS:
        bot.send_message(user_id, "⛔ Siz bloklanmısınız. Botdan istifadə edə bilməzsiniz.")
        return
    if not check_limit(user_id):
        bot.send_message(user_id, f"❌ Siz gündə {MESSAGE_LIMIT} mesaj limitini keçdiniz. VIP olun və limitsiz istifadə edin.")
        return
    users[user_id]["interest"] = interest
    bot.send_message(user_id, "Partnyor axtarılır, zəhmət olmasa gözləyin...", reply_markup=main_menu())

    if user_id in queue_gender:
        queue_gender.remove(user_id)

    for uid in queue_gender:
        if users.get(uid) and users[uid].get("sex") == interest and users[uid].get("interest") == users[user_id]["sex"]:
            queue_gender.remove(uid)
            users[user_id]["partner"] = uid
            users[uid]["partner"] = user_id
            bot.send_message(user_id, "✅ Cins uyğun partnyor tapıldı!")
            bot.send_message(uid, "✅ Cins uyğun partnyor tapıldı!")
            return
    queue_gender.append(user_id)
    bot.send_message(user_id, "⏳ Partnyor tapılmadı. Zəhmət olmasa gözləyin...")

@bot.message_handler(func=lambda m: m.text == "🌈 Gey axtarış")
def gay_search(message):
    user_id = message.from_user.id
    if user_id in BANNED_USERS:
        bot.send_message(user_id, "⛔ Siz bloklanmısınız. Botdan istifadə edə bilməzsiniz.")
        return
    users[user_id]["partner"] = None
    if user_id in queue_gay:
        queue_gay.remove(user_id)
    find_partner(queue_gay, user_id)

@bot.message_handler(func=lambda m: m.text == "❌ Dayandır")
def stop_chat(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    msg_count = users.get(user_id, {}).get("messages_sent", 0)

    users[user_id] = {"sex": None, "interest": None, "partner": None, "messages_sent": msg_count}

    for q in [queue_random, queue_gender, queue_gay]:
        if user_id in q:
            q.remove(user_id)

    if partner_id and partner_id in users:
        users[partner_id]["partner"] = None
        bot.send_message(partner_id, "🚫 Partnyor söhbəti dayandırdı.", reply_markup=main_menu())

    bot.send_message(user_id, "🛑 Söhbət dayandırıldı. Yenidən seçim edin:", reply_markup=main_menu())

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker'])
def relay_msg(message):
    user_id = message.from_user.id
    if user_id in BANNED_USERS:
        bot.send_message(user_id, "⛔ Siz bloklanmısınız. Botdan istifadə edə bilməzsiniz.")
        return

    # Проверка лимита только для текстовых сообщений и документов, аудио, голоса, стикеры считаем безлимитными
    check_media_limit = True
    if message.content_type in ['photo', 'video', 'document', 'audio', 'voice', 'sticker']:
        check_media_limit = False

    if not check_limit(user_id, check_media_limit=check_media_limit):
        bot.send_message(user_id, f"❌ Siz gündə {MESSAGE_LIMIT} mesaj limitini keçdiniz. VIP olun və limitsiz istifadə edin.")
        return

    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        try:
            if message.content_type == 'text':
                bot.send_message(partner_id, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(partner_id, message.video.file_id, caption=message.caption)
            elif message.content_type == 'document':
                bot.send_document(partner_id, message.document.file_id, caption=message.caption)
            elif message.content_type == 'audio':
                bot.send_audio(partner_id, message.audio.file_id, caption=message.caption)
            elif message.content_type == 'voice':
                bot.send_voice(partner_id, message.voice.file_id, caption=message.caption)
            elif message.content_type == 'sticker':
                bot.send_sticker(partner_id, message.sticker.file_id)
            increment_messages(user_id)
        except Exception as e:
            logging.warning(f"Не удалось переслать сообщение от {user_id} к {partner_id}: {e}")
            bot.send_message(user_id, "❌ Mesaj göndərilə bilmədi.")
    else:
        bot.send_message(user_id, "🔎 Partnyor tapmaq üçün menyudan seçim edin.", reply_markup=main_menu())

# Webhook setup
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@server.route("/", methods=["GET"])
def index():
    return "Bot işləyir!", 200

bot.remove_webhook()
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") or "https://your-service-name.onrender.com"
bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Запуск сервера на порту {port}")
    server.run(host="0.0.0.0", port=port)
