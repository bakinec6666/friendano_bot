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
    bot.send_message(user_id, "👑 Siz adminsiniz. VIP funksiyalar aktivdir.\n\n"
                              "/vip_add <id> - VIP əlavə et\n"
                              "/vip_remove <id> - VIP sil")

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

@bot.message_handler(func=lambda m: m.text == "⭐ VIP almaq")
def vip_info(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "💎 *VIP funksiyalar:*\n\n⚤ Cinsə görə axtarış\n📸 Media göndərmək\n🔞 18+ rejim\n\nVIP almaq üçün adminə yazın: @admin", parse_mode="Markdown")

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
    if not check_limit(user_id):
        bot.send_message(user_id, f"❌ Siz gündə {MESSAGE_LIMIT} mesaj limitini keçdiniz. VIP olun və limitsiz istifadə edin.")
        return
    users[user_id]["partner"] = None
    if user_id in queue_random:
        queue_random.remove(user_id)
    if not find_partner(queue_random, user_id):
        pass

@bot.message_handler(func=lambda m: m.text == "⚤ Cinsə görə axtarış")
def gender_search(message):
    user_id = message.from_user.id
    if user_id not in VIP_USERS:
        bot.send_message(user_id, "⛔ Bu funksiya yalnız VIP istifadəçilər üçündür.\nVIP almaq üçün @admin ilə əlaqə saxlayın.")
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
    if not check_limit(user_id):
        bot.send_message(user_id, f"❌ Siz gündə {MESSAGE_LIMIT} mesaj limitini keçdiniz. VIP olun və limitsiz istifadə edin.")
        return
    users[user_id]["partner"] = None
    if user_id in queue_gay:
        queue_gay.remove(user_id)
    if not find_partner(queue_gay, user_id):
        pass

@bot.message_handler(func=lambda m: m.text == "❌ Dayandır")
def stop_chat(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    msg_count = users.get(user_id, {}).get("messages_sent", 0)

    # Сброс состояния у пользователя, но сохранить счетчик сообщений
    users[user_id] = {"sex": None, "interest": None, "partner": None, "messages_sent": msg_count}

    for q in [queue_random, queue_gender, queue_gay]:
        if user_id in q:
            q.remove(user_id)

    if partner_id and partner_id in users:
        users[partner_id]["partner"] = None
        bot.send_message(partner_id, "🚫 Partnyor söhbəti dayandırdı.", reply_markup=main_menu())

    bot.send_message(user_id, "🛑 Söhbət dayandırıldı. Yenidən seçim edin:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def relay_msg(message):
    user_id = message.from_user.id

    if not check_limit(user_id):
        bot.send_message(user_id, f"❌ Siz gündə {MESSAGE_LIMIT} mesaj limitini keçdiniz. VIP olun və limitsiz istifadə edin.")
        return

    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        try:
            bot.copy_message(partner_id, user_id, message.message_id)
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
