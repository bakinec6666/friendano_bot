import telebot
from flask import Flask, request
import os

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

users = {}
queue = []

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {"sex": None, "interest": None, "partner": None}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👦 Mən kişiyəm", "👧 Mən qadınam")
    bot.send_message(user_id, "Cinsinizi seçin:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["👦 Mən kişiyəm", "👧 Mən qadınam"])
def choose_interest(message):
    user_id = message.from_user.id
    sex = "kişi" if "kişiyəm" in message.text else "qadın"
    users[user_id]["sex"] = sex
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧔 Mən kişiylə söhbət etmək istəyirəm", "👩 Mən qadınla söhbət etmək istəyirəm")
    bot.send_message(user_id, "Kimlə söhbət etmək istəyirsiniz?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["🧔 Mən kişiylə söhbət etmək istəyirəm", "👩 Mən qadınla söhbət etmək istəyirəm"])
def find_partner(message):
    user_id = message.from_user.id
    interest = "kişi" if "kişiylə" in message.text else "qadın"
    users[user_id]["interest"] = interest
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("❌ Dayandır")
    bot.send_message(user_id, "Partnyor axtarılır, zəhmət olmasa gözləyin...", reply_markup=markup)

    for uid in queue:
        if users[uid]["interest"] == users[user_id]["sex"] and users[user_id]["interest"] == users[uid]["sex"]:
            queue.remove(uid)
            users[user_id]["partner"] = uid
            users[uid]["partner"] = user_id
            bot.send_message(user_id, "✅ Partnyor tapıldı! İndi yaza bilərsiniz.")
            bot.send_message(uid, "✅ Partnyor tapıldı! İndi yaza bilərsiniz.")
            return

    queue.append(user_id)

@bot.message_handler(func=lambda m: m.text == "❌ Dayandır")
def stop_chat(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")

    if partner_id:
        bot.send_message(partner_id, "🚫 Partnyor söhbəti dayandırdı.")
        users[partner_id]["partner"] = None
    if user_id in queue:
        queue.remove(user_id)
    users[user_id]["partner"] = None
    bot.send_message(user_id, "🛑 Söhbət dayandırıldı.")

@bot.message_handler(func=lambda m: True)
def relay_msg(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        try:
            bot.copy_message(partner_id, user_id, message.message_id)
        except:
            bot.send_message(user_id, "❌ Mesaj göndərilə bilmədi.")

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
