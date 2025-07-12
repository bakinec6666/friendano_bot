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
    markup.add("❌ Dayandır", "⭐ VIP almaq")
    return markup


def is_vip(user_id):
    return user_id in VIP_USERS


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

    welcome_text = (
        f"👋 Salam, {message.from_user.first_name}!\n\n"
        "Bu bot **anonimdir**. Narahat olmayın — heç kim sizin profilinizi və məlumatlarınızı görmür.\n\n"
        "Burada anonim şəkildə insanlarla tanış ola, söhbət edə bilərsiniz.\n\n"
        "💬 Axtarış növləri:\n"
        "👥 Rəqəmsiz axtarış — hər kəslə\n"
        "⚤ Cinsə görə axtarış — VIP istifadəçilər üçün\n"
        "🌈 Gey axtarış — açıqdır\n\n"
        "❓ Suallarınız varsa, \"Yardım\" düyməsini istifadə edin.\n\n"
        "Başlamaq üçün aşağıdakı düymələrdən birini seçin:"
    )

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👥 Rəqəmsiz axtarış", "⚤ Cinsə görə axtarış", "🌈 Gey axtarış")
    markup.add("❓ Yardım")

    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode="Markdown")


@bot.message_handler(commands=['ahelp'])
def ahelp(message):
    if message.from_user.id not in ADMINS:
        return
    help_text = (
        "🔧 Admin Komandalar\n"
        "/ahelp - Bütün admin komandaları\n"
        "/users - Aktiv istifadəçiləri göstər (id + ad)\n"
        "/vip_add <id> - VIP status ver\n"
        "/vip_remove <id> - VIP sil\n"
        "/vip_add_username <username> - VIP ver @username\n"
        "/broadcast <text> - Hər kəsə mesaj göndər\n"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")


@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id not in ADMINS:
        return
    text = "🔎 Aktiv istifadəçilər:\n"
    for uid, data in users.items():
        name = data.get("name", "")
        text += f"{uid} - {name}\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['vip_add'])
def vip_add(message):
    if message.from_user.id not in ADMINS:
        return
    try:
        new_vip = int(message.text.split()[1])
        VIP_USERS.add(new_vip)
        bot.send_message(message.chat.id, f"✅ {new_vip} VIP oldu")
        bot.send_message(new_vip, "🎉 Sizə VIP status verildi!")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_add <id>")


@bot.message_handler(commands=['vip_remove'])
def vip_remove(message):
    if message.from_user.id not in ADMINS:
        return
    try:
        rem_vip = int(message.text.split()[1])
        VIP_USERS.discard(rem_vip)
        bot.send_message(message.chat.id, f"❌ {rem_vip} VIP silindi")
        bot.send_message(rem_vip, "⚠️ Sizin VIP statusunuz silindi")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_remove <id>")


@bot.message_handler(commands=['vip_add_username'])
def vip_add_by_username(message):
    if message.from_user.id not in ADMINS:
        return
    try:
        username = message.text.split()[1].replace("@", "")
        for uid, data in users.items():
            if data.get("username") == username:
                VIP_USERS.add(uid)
                bot.send_message(message.chat.id, f"✅ @{username} VIP oldu")
                bot.send_message(uid, "🎉 Sizə VIP status verildi!")
                return
        bot.send_message(message.chat.id, "❌ İstifadəçi tapılmadı")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ İstifadə: /vip_add_username @username")


@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id not in ADMINS:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.send_message(message.chat.id, "⚠️ İstifadə: /broadcast <text>")
        return
    count = 0
    remove_list = []
    for uid in list(users):
        try:
            bot.send_message(uid, f"📢 {text}")
            count += 1
        except Exception:
            remove_list.append(uid)
    for uid in remove_list:
        users.pop(uid, None)
        VIP_USERS.discard(uid)
        remove_from_all_queues(uid)
    bot.send_message(message.chat.id, f"✅ Göndərildi: {count} istifadəçiyə")


def remove_from_all_queues(user_id):
    if user_id in queue_random:
        queue_random.remove(user_id)
    if user_id in queue_gender:
        queue_gender.remove(user_id)
    if user_id in queue_gay:
        queue_gay.remove(user_id)


def find_partner(user_id, search_type):
    if search_type == "random":
        queue = queue_random
        # Просто ищем любого свободного
        # Исключая самого себя
        if users[user_id].get("partner") is not None:
            return users[user_id]["partner"]
        for other_id in queue:
            if other_id != user_id and users.get(other_id, {}).get("partner") is None:
                users[user_id]["partner"] = other_id
                users[other_id]["partner"] = user_id
                queue.remove(other_id)
                return other_id
        if user_id not in queue:
            queue.append(user_id)
        return None

    elif search_type == "gender":
        # Фильтруем по полу: ищем в queue_gender партнера противоположного пола
        if users[user_id].get("partner") is not None:
            return users[user_id]["partner"]
        user_sex = users[user_id].get("sex")
        if user_sex is None:
            return None  # Пол не установлен, не ищем
        for other_id in queue_gender:
            if other_id != user_id and users.get(other_id, {}).get("partner") is None:
                other_sex = users[other_id].get("sex")
                # Для примера — будем искать противоположный пол
                if other_sex is not None and other_sex != user_sex:
                    users[user_id]["partner"] = other_id
                    users[other_id]["partner"] = user_id
                    queue_gender.remove(other_id)
                    return other_id
        if user_id not in queue_gender:
            queue_gender.append(user_id)
        return None

    elif search_type == "gay":
        # Просто соединяем всех из очереди gay (как раньше)
        if users[user_id].get("partner") is not None:
            return users[user_id]["partner"]
        for other_id in queue_gay:
            if other_id != user_id and users.get(other_id, {}).get("partner") is None:
                users[user_id]["partner"] = other_id
                users[other_id]["partner"] = user_id
                queue_gay.remove(other_id)
                return other_id
        if user_id not in queue_gay:
            queue_gay.append(user_id)
        return None

    return None


def stop_chat(user_id):
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        users[partner_id]["partner"] = None
        # Возвращаем партнёра в нужующую очередь, исходя из их текущего поиска
        # Упростим: добавим в random очередь — можно потом усложнить
        if partner_id not in queue_random:
            queue_random.append(partner_id)
        users[user_id]["partner"] = None

    # Удаляем пользователя из всех очередей, чтобы он не висел в них
    remove_from_all_queues(user_id)
    # Также обнулим их партнера
    users[user_id]["partner"] = None


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in users:
        users[user_id] = {"sex": None, "interest": None, "partner": None,
                          "name": message.from_user.first_name, "username": message.from_user.username}

    if text == "👥 Rəqəmsiz axtarış":
        stop_chat(user_id)
        partner = find_partner(user_id, "random")
        if partner:
            bot.send_message(user_id, "🟢 Siz birinə qoşuldunuz. Sözü başla!")
            bot.send_message(partner, "🟢 Siz birinə qoşuldunuz. Sözü başla!")
        else:
            bot.send_message(user_id, "⏳ Tərəfdaş tapılır, zəhmət olmasa gözləyin...")

    elif text == "⚤ Cinsə görə axtarış":
        if not is_vip(user_id):
            bot.send_message(user_id, "⚠️ Cinsə görə axtarış yalnız VIP istifadəçilər üçündür.\n"
                                      "Qiymət: 5 manat\n"
                                      "Əlaqə üçün admin: @user666321")
            return
        if users[user_id]["sex"] is None:
            msg = bot.send_message(user_id, "Zəhmət olmasa cinsinizi seçin:", reply_markup=sex_selection_markup())
            bot.register_next_step_handler(msg, set_sex_and_search_gender)
            return
        stop_chat(user_id)
        partner = find_partner(user_id, "gender")
        if partner:
            bot.send_message(user_id, "🟢 Siz birinə qoşuldunuz. Sözü başla!")
            bot.send_message(partner, "🟢 Siz birinə qoşuldunuz. Sözü başla!")
        else:
            bot.send_message(user_id, "⏳ Tərəfdaş tapılır, zəhmət olmasa gözləyin...")

    elif text == "🌈 Gey axtarış":
        stop_chat(user_id)
        partner = find_partner(user_id, "gay")
        if partner:
            bot.send_message(user_id, "🟢 Siz birinə qoşuldunuz. Sözü başla!")
            bot.send_message(partner, "🟢 Siz birinə qoşuldunuz. Sözü başla!")
        else:
            bot.send_message(user_id, "⏳ Tərəfdaş tapılır, zəhmət olmasa gözləyin...")

    elif text == "❌ Dayandır":
        stop_chat(user_id)
        bot.send_message(user_id, "🔴 Chat dayandırıldı. Başlamaq üçün menyudan seçim edin.", reply_markup=main_menu())

    elif text == "⭐ VIP almaq":
        bot.send_message(user_id, "VIP almaq üçün admin ilə əlaqə saxlayın.")

    elif text == "❓ Yardım":
        help_text = (
            "📖 *Botdan istifadə qaydaları:*\n"
            "- *Rəqəmsiz axtarış*: Hər kəslə anonim söhbət.\n"
            "- *Cinsə görə axtarış*: Yalnız VIP istifadəçilər üçündür.\n"
            "- *Gey axtarış*: Gey istifadəçilər üçün açıqdır.\n"
            "- *Dayandır*: Cari söhbəti bitirir.\n\n"
            "Əlavə sualınız varsa, adminə müraciət edin: @user666321"
        )
        bot.send_message(user_id, help_text, parse_mode="Markdown")

    else:
        partner_id = users[user_id].get("partner")
        if partner_id:
            try:
                bot.send_message(partner_id, text)
            except Exception:
                # Если не удалось отправить — заканчиваем чат
                stop_chat(user_id)
                bot.send_message(user_id, "⚠️ Tərəfdaşınız söhbətdən ayrıldı.")
        else:
            bot.send_message(user_id, "❗ Siz heç kimlə bağlı deyilsiniz. Menyudan seçim edin.", reply_markup=main_menu())


def sex_selection_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Kişi", "Qadın")
