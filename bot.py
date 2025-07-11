
import telebot
from telebot import types

# === TOKEN ===
TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
bot = telebot.TeleBot(TOKEN)

# === ADMIN ID ===
ADMINS = [6671597409]

# === DATA ===
users = {}
queue = {"kiЕџi": [], "qadД±n": [], "unknown": []}

# === START ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {"sex": "unknown", "is_vip": user_id in ADMINS, "partner": None}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("рџ‘¦ MЙ™n kiЕџiyЙ™m", "рџ‘§ MЙ™n qadД±nam")
    bot.send_message(user_id, "Cinsinizi seГ§in:", reply_markup=markup)

# === SEX CHOICE ===
@bot.message_handler(func=lambda m: m.text in ["рџ‘¦ MЙ™n kiЕџiyЙ™m", "рџ‘§ MЙ™n qadД±nam"])
def set_sex(message):
    user_id = message.from_user.id
    sex = "kiЕџi" if "kiЕџiyЙ™m" in message.text else "qadД±n"
    users[user_id]["sex"] = sex
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("рџ‘Ґ SГ¶hbЙ™tЙ™ baЕџla", "вќЊ DayandД±r", "в­ђ VIP almaq")
    if users[user_id]["is_vip"]:
        markup.add("рџ”“ Admin panel")
    bot.send_message(user_id, f"Cins seГ§ildi: {sex}", reply_markup=markup)

# === ADMIN PANEL ===
@bot.message_handler(commands=['admin'])
@bot.message_handler(func=lambda m: m.text == "рџ”“ Admin panel")
def admin_panel(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, "рџ‘‘ Siz adminsiniz. VIP funksiyalar aktivdir.")
    else:
        bot.send_message(message.chat.id, "в›” Bu funksiya yalnД±z adminlЙ™r ГјГ§ГјndГјr.")

# === VIP INFO ===
@bot.message_handler(func=lambda m: m.text == "в­ђ VIP almaq")
def vip_info(message):
    bot.send_message(message.chat.id, """VIP funksiyalar:
рџ”Ќ CinsЙ™ gГ¶rЙ™ axtarД±Еџ
рџ“ё Media gГ¶ndЙ™rmЙ™k
рџ”ћ 18+ rejim

VIP almaq ГјГ§Гјn adminЙ™ yazД±n: @admin""")

# === START CHAT ===
@bot.message_handler(func=lambda m: m.text == "рџ‘Ґ SГ¶hbЙ™tЙ™ baЕџla")
def find_partner(message):
    user_id = message.from_user.id
    user = users.get(user_id)
    if not user:
        bot.send_message(user_id, "ZЙ™hmЙ™t olmasa /start yazД±n.")
        return

    if not user["is_vip"]:
        bot.send_message(user_id, "вќ— Bu funksiya VIP istifadЙ™Г§ilЙ™r ГјГ§ГјndГјr.")
        return

    target_sex = "qadД±n" if user["sex"] == "kiЕџi" else "kiЕџi"
    if queue[target_sex]:
        partner_id = queue[target_sex].pop(0)
        users[user_id]["partner"] = partner_id
        users[partner_id]["partner"] = user_id
        bot.send_message(user_id, "вњ… Partnyor tapД±ldД±! Д°ndi yaza bilЙ™rsiniz.")
        bot.send_message(partner_id, "вњ… Partnyor tapД±ldД±! Д°ndi yaza bilЙ™rsiniz.")
    else:
        queue[user["sex"]].append(user_id)
        bot.send_message(user_id, "рџ”Ћ Partnyor axtarД±lД±r... ZЙ™hmЙ™t olmasa gГ¶zlЙ™yin.")

# === STOP CHAT ===
@bot.message_handler(func=lambda m: m.text == "вќЊ DayandД±r")
def stop_chat(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")

    if partner_id:
        users[partner_id]["partner"] = None
        bot.send_message(partner_id, "вќЊ Partnyor sГ¶hbЙ™ti dayandД±rdД±.")
    if user_id in queue[users.get(user_id, {}).get("sex", "unknown")]:
        queue[users[user_id]["sex"]].remove(user_id)
    users[user_id]["partner"] = None
    bot.send_message(user_id, "рџ›‘ SГ¶hbЙ™t dayandД±rД±ldД±.")

# === RELAY MESSAGE ===
@bot.message_handler(func=lambda m: True)
def relay(message):
    user_id = message.from_user.id
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        bot.copy_message(partner_id, user_id, message.message_id)

# === START BOT ===
print("вњ… Bot iЕџlЙ™yir...")
bot.infinity_polling()
