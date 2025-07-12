import telebot
from flask import Flask, request
import os
import logging

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

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👥 Rəqəmsiz axtarış", "⚤ Cinsə görə axtarış", "🌈 Gey axtarış")
    markup.add("❌ Dayandır", "🔙 Geri", "⭐ VIP almaq")
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

def sex_selection_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Kişi", "Qadın")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        "sex": None,
        "interest": None,
        "partner": None,
        "name": message.from_user.first_name,
        "username": message.from_user.username
    }

    welcome = (
        f"👋 Salam, {message.from_user.first_name}!\n\n"
        "Bu bot **anonimdir**. Heç kim sizin profil və məlumatlarınızı görmür.\n\n"
        "💬 Axtarış növləri:\n"
        "👥 Rəqəmsiz — hər kəslə\n"
        "⚤ Cinsə görə — VIP üçün\n"
        "🌈 Gey — açıq\n\n"
        "Başlamaq üçün menyudan seçim edin."
    )
    bot.send_message(user_id, welcome, reply_markup=main_menu(), parse_mode="Markdown")

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
                          "name": message.from_user.first_name, "username": message.from_user.username}

    if text == "👥 Rəqəmsiz axtarış":
        stop_chat(user_id)
        p = find_partner(user_id, "random")
        if p:
            bot.send_message(user_id, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!")
            bot.send_message(p, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!")
        else:
            bot.send_message(user_id, "⏳ Tərəfdaş axtarılır...")

    elif text == "⚤ Cinsə görə axtarış":
        if not is_vip(user_id):
            return bot.send_message(user_id, "⚠️ Bu funksiya yalnız VIP üçün.\nƏlaqə: @user666321")
        if not users[user_id]["sex"]:
            msg = bot.send_message(user_id, "Cinsinizi seçin:", reply_markup=sex_selection_markup())
            bot.register_next_step_handler(msg, set_sex)
            return
        stop_chat(user_id)
        p = find_partner(user_id, "gender")
        if p:
            bot.send_message(user_id, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!")
            bot.send_message(p, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!")
        else:
            bot.send_message(user_id, "⏳ Tərəfdaş axtarılır...")

    elif text == "🌈 Gey axtarış":
        stop_chat(user_id)
        p = find_partner(user_id, "gay")
        if p:
            bot.send_message(user_id, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!")
            bot.send_message(p, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!")
        else:
            bot.send_message(user_id, "⏳ Tərəfdaş axtarılır...")

    elif text == "❌ Dayandır":
        stop_chat(user_id)
        bot.send_message(user_id, "🔴 Chat dayandırıldı.", reply_markup=main_menu())

    elif text == "🔙 Geri":
        stop_chat(user_id)
        bot.send_message(user_id, "↩️ Əsas menyuya qayıtdınız.", reply_markup=main_menu())

    elif text == "⭐ VIP almaq":
        bot.send_message(user_id, "VIP almaq üçün əlaqə saxlayın: @user666321")

    else:
        partner_id = users[user_id].get("partner")
        if partner_id:
            try:
                bot.send_message(partner_id, text)
            except:
                stop_chat(user_id)
                bot.send_message(user_id, "⚠️ Tərəfdaş söhbətdən ayrıldı.")
        else:
            bot.send_message(user_id, "❗ Siz bağlı deyilsiniz.", reply_markup=main_menu())

def set_sex(message):
    user_id = message.from_user.id
    sex = message.text.strip()
    if sex not in ["Kişi", "Qadın"]:
        msg = bot.send_message(user_id, "Zəhmət olmasa 'Kişi' və ya 'Qadın' yazın.")
        return bot.register_next_step_handler(msg, set_sex)
    users[user_id]["sex"] = sex
    bot.send_message(user_id, f"Cinsiniz: {sex}. Axtarış başlayır...")
    stop_chat(user_id)
    p = find_partner(user_id, "gender")
    if p:
        bot.send_message(user_id, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!")
        bot.send_message(p, "🟢 Tərəfdaş tapıldı. Yazışa bilərsiniz!")
    else:
        bot.send_message(user_id, "⏳ Tərəfdaş axtarılır...")

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
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
