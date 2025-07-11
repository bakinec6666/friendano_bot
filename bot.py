import telebot
from flask import Flask, request
import os

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
ADMINS = [6671597409]
VIP_USERS = ADMINS + []

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

users = {}
queue_random = []
queue_gender = []
queue_gay = []

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👥 Rəqəmsiz axtarış", "⚤ Cinsə görə axtarış", "🌈 Gey axtarış")
    markup.add("❌ Dayandır", "⭐ VIP almaq")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {"sex": None, "interest": None, "partner": None}
    bot.send_message(user_id, "👋 Xoş gəlmisiniz! Menyudan seçim edin:", reply_markup=main_menu())

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, "👑 Siz adminsiniz. VIP funksiyalar aktivdir.")
    else:
        bot.send_message(message.chat.id, "⛔ Bu komanda yalnız adminlər üçündür.")

@bot.message_handler(func=lambda m: m.text == "⭐ VIP almaq")
def vip_info(message):
    bot.send_message(message.chat.id, "💎 *VIP funksiyalar:*\n\n⚤ Cinsə görə axtarış\n📸 Media göndərmək\n🔞 18+ rejim\n\nVIP almaq üçün adminə yazın: @admin", parse_mode="Markdown")

def find_partner(queue, user_id):
    for uid in queue:
        if users[uid].get("partner") is None:
            queue.remove(uid)
            users[user_id]["partner"] = uid
            users[uid]["partner"] = user_id
            bot.send_message(user_id, "✅ Partnyor tapıldı! İndi yaza bilərsiniz.")
            bot.send_message(uid, "✅ Partnyor tapıldı! İndi yaza bilərsiniz.")
            return True
    return False

@bot.message_handler(func=lambda m: m.text == "👥 Rəqəmsiz axtarış")
def random_search(message):
    user_id = message.from_user.id
    users[user_id]["partner"] = None
    bot.send_message(user_id, "🔍 Təsadüfi partnyor axtarılır, gözləyin...", reply_markup=main_menu())
    if not find_partner(queue_random, user_id):
        queue_random.append(user_id)

@bot.message_handler(func=lambda m: m.text == "⚤ Cinsə görə axtarış")
def gender_search(message):
    user_id = message.from_user.id
    if user_id not in VIP_USERS:
        bot.send_message(user_id, "⛔ Bu funksiya yalnız VIP istifadəçilər üçündür.\nVIP almaq üçün @admin ilə əlaqə saxlayın.")
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
    users[user_id]["interest"] = interest
    bot.send_message(user_id, "Partnyor axtarılır, zəhmət olmasa gözləyin...", reply_markup=main_menu())
    for uid in queue_gender:
        if users.get(uid) and users[uid].get("sex") == users[user_id]["interest"] and users[uid]["interest"] == users[user_id]["sex"]:
            queue_gender.remove(uid)
            users[user_id]["partner"] = uid
            users[uid]["partner"] = user_id
            bot.send_message(user_id, "✅ Cins uyğun partnyor tapıldı!")
            bot.send_message(uid, "✅ Cins uyğun partnyor tapıldı!")
            return
    queue_gender.append(user_id)

@bot.message_handler(func=lambda m: m.text == "🌈 Gey axtarış")
def gay_search(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "🌈 Gey partnyor axtarılır, gözləyin...", reply_markup=main_menu())
    if not find_partner(queue_gay, user_id):
        queue_gay.append(user_id)

@bot.message_handler(func=lambda m: m.text == "❌ Dayandır")
def stop_chat(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        bot.send_message(partner_id, "🚫 Partnyor söhbəti dayandırdı.")
        users[partner_id]["partner"] = None
    for q in [queue_random, queue_gender, queue_gay]:
        if user_id in q:
            q.remove(user_id)
    users[user_id]["partner"] = None
    bot.send_message(user_id, "🛑 Söhbət dayandırıldı.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def relay_msg(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        try:
            bot.copy_message(partner_id, user_id, message.message_id)
        except:
            bot.send_message(user_id, "❌ Mesaj göndərilə bilmədi.")

# Webhook setup for Render
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@server.route("/", methods=["GET"])
def index():
    return "Bot işləyir!", 200

bot.remove_webhook()
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") or "https://your-service-name.onrender.com"
bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
