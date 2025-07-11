
import telebot
from flask import Flask, request
import os

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# РџРѕР»СЊР·РѕРІР°С‚РµР»Рё Рё РѕС‡РµСЂРµРґСЊ
users = {}
queue = []

# === START ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {"sex": None, "interest": None, "partner": None}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("рџ‘¦ MЙ™n kiЕџiyЙ™m", "рџ‘§ MЙ™n qadД±nam")
    bot.send_message(user_id, "Cinsinizi seГ§in:", reply_markup=markup)

# === SEX CHOICE ===
@bot.message_handler(func=lambda m: m.text in ["рџ‘¦ MЙ™n kiЕџiyЙ™m", "рџ‘§ MЙ™n qadД±nam"])
def choose_interest(message):
    user_id = message.from_user.id
    sex = "kiЕџi" if "kiЕџiyЙ™m" in message.text else "qadД±n"
    users[user_id]["sex"] = sex
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("рџ§” MЙ™n kiЕџiylЙ™ sГ¶hbЙ™t istЙ™yirЙ™m", "рџ‘© MЙ™n qadД±nla sГ¶hbЙ™t istЙ™yirЙ™m")
    bot.send_message(user_id, "KimlЙ™ sГ¶hbЙ™t etmЙ™k istЙ™yirsiniz?", reply_markup=markup)

# === INTEREST CHOICE ===
@bot.message_handler(func=lambda m: m.text in ["рџ§” MЙ™n kiЕџiylЙ™ sГ¶hbЙ™t istЙ™yirЙ™m", "рџ‘© MЙ™n qadД±nla sГ¶hbЙ™t istЙ™yirЙ™m"])
def find_partner(message):
    user_id = message.from_user.id
    interest = "kiЕџi" if "kiЕџiylЙ™" in message.text else "qadД±n"
    users[user_id]["interest"] = interest
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("вќЊ DayandД±r")
    bot.send_message(user_id, "Partnyor axtarД±lД±r, zЙ™hmЙ™t olmasa gГ¶zlЙ™yin...", reply_markup=markup)

    # AxtarД±Еџ
    for uid in queue:
        if users[uid]["interest"] == users[user_id]["sex"] and users[user_id]["interest"] == users[uid]["sex"]:
            queue.remove(uid)
            users[user_id]["partner"] = uid
            users[uid]["partner"] = user_id
            bot.send_message(user_id, "вњ… Partnyor tapД±ldД±! Д°ndi yaza bilЙ™rsiniz.")
            bot.send_message(uid, "вњ… Partnyor tapД±ldД±! Д°ndi yaza bilЙ™rsiniz.")
            return

    queue.append(user_id)

# === STOP CHAT ===
@bot.message_handler(func=lambda m: m.text == "вќЊ DayandД±r")
def stop_chat(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")

    if partner_id:
        bot.send_message(partner_id, "рџљ« Partnyor sГ¶hbЙ™ti dayandД±rdД±.")
        users[partner_id]["partner"] = None
    if user_id in queue:
        queue.remove(user_id)
    users[user_id]["partner"] = None
    bot.send_message(user_id, "рџ›‘ SГ¶hbЙ™t dayandД±rД±ldД±.")

# === RELAY ===
@bot.message_handler(func=lambda m: True)
def relay_msg(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        try:
            bot.copy_message(partner_id, user_id, message.message_id)
        except:
            bot.send_message(user_id, "вќЊ Mesaj gГ¶ndЙ™rilЙ™ bilmЙ™di.")

# === FLASK WEBHOOK ===
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@server.route("/", methods=["GET"])
def index():
    return "Bot iЕџlЙ™yir!", 200

# === WEBHOOK SET ===
bot.remove_webhook()
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") or "https://your-service-name.onrender.com"
bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

# === RUN FLASK ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
