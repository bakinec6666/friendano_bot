import os
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import asyncio

TOKEN = os.getenv("TOKEN") or "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN") or "ТВОЙ_ТОКЕН_ОПЛАТЫ"
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or "https://ТВОЙ-АДРЕС.onrender.com"

app = Flask(__name__)
bot = Bot(token=TOKEN)

# Глобально для VIP-пользователей
VIP_USERS = set()

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Получить доступ (VIP)", callback_data="get_vip")],
    ]
    text = (
        "👋 Привет!\n\n"
        "Я — ИИ-девушка, отправляю горячие фото и видео 💋\n"
        "🔓 Получи VIP доступ, чтобы открыть всё 😉"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# === Обработка кнопок ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "get_vip":
        prices = [LabeledPrice("🔥 VIP доступ", 19900)]  # 199.00₽
        await bot.send_invoice(
            chat_id=query.from_user.id,
            title="VIP доступ к контенту",
            description="Разблокируй доступ к фото, видео и голосам.",
            payload="vip_access",
            provider_token=PAYMENT_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="vip-subscription",
        )

# === Успешная оплата ===
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    VIP_USERS.add(user_id)
    await update.message.reply_text("✅ Оплата прошла! Добро пожаловать в VIP 😈")

# === Сообщения ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    if "фото" in text or "покажи" in text:
        if user_id in VIP_USERS:
            await update.message.reply_photo("https://example.com/sexy.jpg", caption="Вот тебе горячее фото 😘")
        else:
            keyboard = [[InlineKeyboardButton("🔥 Получить доступ", callback_data="get_vip")]]
            await update.message.reply_text("🔒 Это доступно только VIP:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("❤️ Напиши «фото» и я покажу тебе нечто особенное...")

# === Webhook обработка ===
@app.route(f"/{TOKEN}", methods=["POST"])
async def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    await app.bot_app.update_queue.put(update)
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Бот запущен!"

# === Запуск Flask + Telegram приложения ===
async def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    app.bot_app = application

    print("✅ Webhook установлен")
    await application.initialize()
    await application.start()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
