import os
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters
)
import asyncio

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"  # твой токен напрямую
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")  # укажи его в Render settings
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://yourbot.onrender.com

app = Flask(__name__)
bot = Bot(token=TOKEN)

VIP_USERS = set()

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Привет, дорогой!\n\n"
        "Хочешь расслабиться с реалистичной ИИ-девушкой?\n\n"
        "Я умею делать:\n"
        "• 🎥 Реальные видео\n"
        "• 📸 Откровенные фото\n"
        "• 💋 Исполнять желания в разных позах\n\n"
        "🔓 Разблокируй доступ к горячим материалам!"
    )
    keyboard = [[InlineKeyboardButton("🔥 Получить доступ (VIP)", callback_data="get_vip")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# === Callback-кнопки ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "get_vip":
        prices = [LabeledPrice("🔥 VIP доступ", 19900)]
        await bot.send_invoice(
            chat_id=query.message.chat_id,
            title="Подписка на интимный контент",
            description="Разблокируй фото, видео и голосовые от ИИ-девушки.",
            payload="vip_access",
            provider_token=PAYMENT_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="vip-subscription"
        )

# === Обработка успешной оплаты ===
async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.successful_payment:
        user_id = update.effective_user.id
        VIP_USERS.add(user_id)
        await update.message.reply_text("✅ Оплата прошла успешно! Доступ к интимному контенту разблокирован.")

# === Сообщения ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()
    if "фото" in text or "покажи" in text:
        if user_id in VIP_USERS:
            await update.message.reply_photo(
                photo="https://telegra.ph/file/ea3f31c849fbcb4e24237.jpg",  # заменишь
                caption="Вот тебе моё горячее фото 😘"
            )
        else:
            keyboard = [[InlineKeyboardButton("🔥 Получить доступ", callback_data="get_vip")]]
            await update.message.reply_text("🔒 Только для VIP! Оформи доступ ниже:",
                                            reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("❤️ Напиши «фото» и я пришлю тебе что-то особенное 🔥")

# === Flask Webhook ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.update_queue.put(update))
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Бот работает!"

# === Main ===
if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.ALL, handle_payment))  # все платежи

    # Установка webhook
    async def setup():
        await bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    asyncio.run(setup())

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
