import os
import asyncio
from flask import Flask, request
from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup,
    LabeledPrice, Message, SuccessfulPayment
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

TOKEN = os.environ.get("BOT_TOKEN")  # безопаснее, чем в коде
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://yourbot.onrender.com

app = Flask(__name__)
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

VIP_USERS = set()

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        text = (
            "👋 Привет!\n\n"
            "Я твоя виртуальная ИИ-девушка 😘\n\n"
            "• 🎥 Видео\n"
            "• 📸 Фото\n"
            "• 💋 Желания\n\n"
            "🔓 Получи VIP-доступ и начнём!"
        )
        keyboard = [[InlineKeyboardButton("🔥 Получить доступ (VIP)", callback_data="get_vip")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        print("⚠️ update.message is None (вероятно из-за webhook)")

# === Кнопки ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_vip":
        prices = [LabeledPrice(label="🔥 VIP доступ", amount=19900)]
        await bot.send_invoice(
            chat_id=query.from_user.id,
            title="VIP доступ к ИИ-девушке",
            description="Откровенные фото, видео и голосовые.",
            payload="vip_access",
            provider_token=PAYMENT_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="buy-vip"
        )

# === Успешная оплата ===
async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    VIP_USERS.add(user_id)
    await update.message.reply_text("✅ Оплата прошла успешно! Добро пожаловать в VIP 😘")

# === Сообщения ===
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    if "фото" in text or "покажи" in text:
        if user_id in VIP_USERS:
            await update.message.reply_photo(
                photo="https://telegra.ph/file/ea3f31c849fbcb4e24237.jpg",
                caption="Вот твоё горячее фото 😘"
            )
        else:
            keyboard = [[InlineKeyboardButton("🔥 Получить доступ", callback_data="get_vip")]]
            await update.message.reply_text("🔒 Только для VIP. Получи доступ ниже:",
                                            reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("❤️ Напиши «фото» — и я пришлю тебе кое-что горячее!")

# === Webhook ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "🤖 Бот работает!"

# === Запуск ===
if __name__ == "__main__":
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))

    async def setup_webhook():
        await bot.delete_webhook()
        await bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
        print("✅ Webhook установлен!")

    asyncio.run(setup_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
