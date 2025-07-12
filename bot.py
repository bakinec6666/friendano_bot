import telebot from flask import Flask, request import os import logging

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc" ADMINS = [6671597409] VIP_USERS = set(ADMINS)

bot = telebot.TeleBot(TOKEN) server = Flask(name)

logging.basicConfig(level=logging.INFO)

users = {} queue_random = [] queue_gender = [] queue_gay = []

MESSAGE_LIMIT = 20

def main_menu(): markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True) markup.add("\ud83d\udc65 R\u0259q\u0259msiz axtar\u0131\u015f", "\u26a4 Cins\u0259 g\u0259r\u0259 axtar\u0131\u015f", "\ud83c\udf08 Gey axtar\u0131\u015f") markup.add("\u274c Dayand\u0131r", "\u2b50 VIP almaq") return markup

def is_vip(user_id): return user_id in VIP_USERS

def check_limit(user_id): if is_vip(user_id): return True user = users.get(user_id) if user is None: users[user_id] = {"sex": None, "interest": None, "partner": None, "messages_sent": 0} return True return user.get("messages_sent", 0) < MESSAGE_LIMIT

def increment_messages(user_id): if user_id not in users: users[user_id] = {"sex": None, "interest": None, "partner": None, "messages_sent": 0} users[user_id]["messages_sent"] += 1

@bot.message_handler(commands=['start']) def start(message): user_id = message.from_user.id users[user_id] = {"sex": None, "interest": None, "partner": None, "messages_sent": 0, "name": message.from_user.first_name, "username": message.from_user.username} bot.send_message(user_id, "\ud83d\udc4b Xo\u015f g\u0259lmisiniz! Menyudan seçim edin:", reply_markup=main_menu())

@bot.message_handler(commands=['ahelp']) def ahelp(message): if message.from_user.id not in ADMINS: return help_text = ( "\ud83d\udd27 Admin Komandalar\n" "/ahelp - B\u0259t\u0259n admin komandalar\u0131\n" "/users - Aktiv istifad\u0259\u00e7il\u0259r\u0131 g\u00f6st\u0259r (id + ad)\n" "/vip_add <id> - VIP status ver\n" "/vip_remove <id> - VIP sil\n" "/vip_add_username <username> - VIP ver @username\n" "/broadcast <text> - H\u0259r k\u0259s\u0259 mesaj g\u00f6nd\u0259r" ) bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['users']) def list_users(message): if message.from_user.id not in ADMINS: return text = "\ud83d\udd0e Aktiv istifade\u00e7iler:\n" for uid, data in users.items(): name = data.get("name", "") text += f"{uid} - {name}\n" bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['vip_add']) def vip_add(message): if message.from_user.id not in ADMINS: return try: new_vip = int(message.text.split()[1]) VIP_USERS.add(new_vip) bot.send_message(message.chat.id, f"✅ {new_vip} VIP oldu") bot.send_message(new_vip, "🎉 Sizə VIP status verildi!") except: bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_add <id>")

@bot.message_handler(commands=['vip_remove']) def vip_remove(message): if message.from_user.id not in ADMINS: return try: rem_vip = int(message.text.split()[1]) VIP_USERS.discard(rem_vip) bot.send_message(message.chat.id, f"❌ {rem_vip} VIP silindi") bot.send_message(rem_vip, "⚠️ Sizin VIP statusunuz silindi") except: bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_remove <id>")

@bot.message_handler(commands=['vip_add_username']) def vip_add_by_username(message): if message.from_user.id not in ADMINS: return try: username = message.text.split()[1].replace("@", "") for uid, data in users.items(): if data.get("username") == username: VIP_USERS.add(uid) bot.send_message(message.chat.id, f"✅ @{username} VIP oldu") bot.send_message(uid, "🎉 Sizə VIP status verildi!") return bot.send_message(message.chat.id, "❌ İstifadəçi tapılmadı") except: bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_add_username @username")

@bot.message_handler(commands=['broadcast']) def broadcast(message): if message.from_user.id not in ADMINS: return text = message.text.replace("/broadcast", "").strip() if not text: bot.send_message(message.chat.id, "⚠️ İstifadə: /broadcast <text>") return count = 0 for uid in users: try: bot.send_message(uid, f"📢 {text}") count += 1 except: pass bot.send_message(message.chat.id, f"✅ Göndərildi: {count} istifadəçiyə")

Остальная логика (поиск, сообщения, остановка, VIP info и т.п.) загружается отдельно, если нужно — могу сразу добавить сюда

Webhook setup

@server.route(f"/{TOKEN}", methods=["POST"]) def webhook(): update = telebot.types.Update.de_json(request.stream.read().decode("utf-8")) bot.process_new_updates([update]) return "OK", 200

@server.route("/") def index(): return "Bot işləyir!", 200

bot.remove_webhook() WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") if WEBHOOK_URL: bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

if name == "main": port = int(os.environ.get("PORT", 5000)) server.run(host="0.0.0.0", port=port)

