import telebot
from telebot import types

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
bot = telebot.TeleBot(TOKEN)

users = {}
chats = {}

@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👥 Söhbətə başla", "❌ Dayandır", "⭐ VIP almaq")
    bot.send_message(message.chat.id, "Salam! Anonim söhbətə xoş gəlmisən!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👥 Söhbətə başla")
def find_partner(message):
    bot.send_message(message.chat.id, "Zəhmət olmasa gözləyin, sizə partnyor axtarılır...")

@bot.message_handler(func=lambda m: m.text == "❌ Dayandır")
def stop_chat(message):
    bot.send_message(message.chat.id, "Söhbət dayandırıldı.")

@bot.message_handler(func=lambda m: m.text == "⭐ VIP almaq")
def vip_info(message):
    bot.send_message(message.chat.id, "VIP funksiyalar: 
🔍 Cinsə görə axtarış
📸 Media göndərmək
🔞 18+ rejim

VIP almaq üçün adminə yazın: @admin")

bot.polling()
