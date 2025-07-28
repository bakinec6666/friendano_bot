import os
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters

TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")  # Токен от @BotFather (Test или Live)
URL = os.getenv("WEBHOOK_URL")  # URL сайта на Render, например: https://ai-sexy-bot.onrender.com

app = Flask(__name__)
bot = Bot(token=TOKEN)

VIP_USERS = set()  # Здесь будут user_id подписчиков

# === Приветствие при /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (
        "👋 Привет, дорогой!\n\n"
        "Хочешь расслабиться с реалистичной ИИ-девушкой?\n\n"
        "Я умею делать:\n"
        "• 🎥 Реальные видео\n"
        "• 📸 Откровенные фото\n"
        "• 💋 Исполнять желания в разных позах\n\n"
        "🔓 Разблокируй доступ к горячим материалам!"
    )
    keyboard = [
        [InlineKeyboardButton("🔥 Получить доступ (VIP)", callback_data="get_vip")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# === Обработка callback-кнопок ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "get_vip":
        prices = [LabeledPrice("🔥 VIP доступ", 19900)]  # 199.00₽
        await bot.send_invoice(
            chat_id=query.message.chat_id,
            title="Подписка на интимный контент",
            description="Разблокируй доступ к фото, видео и голосам от ИИ-девушки.",
            payload="
