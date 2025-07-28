import os
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters

TOKEN = os.getenv("7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc")
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
            payload="vip_access",
            provider_token=PAYMENT_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="vip-subscription",
        )

# === Обработка успешной оплаты ===
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    VIP_USERS.add(user_id)
    await update.message.reply_text("✅ Оплата прошла успешно! Доступ к интимному контенту разблокирован.")

# === Отправка фото (только VIP) ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()
    if "фото" in text or "покажи" in text:
        if user_id in VIP_USERS:
            await update.message.reply_photo(photo="https://example.com/sexy.jpg", caption="Вот тебе моё горячее фото 😘")
        else:
            await update.message.reply_text("🔒 Доступ к фото только для VIP. Нажми на кнопку ниже:")
            keyboard = [[InlineKeyboardButton("🔥 Получить доступ", callback_data="get_vip")]]
            await update.message.reply_text("Разблокируй фото, купив доступ:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("❤️ Напиши «фото» чтобы я отправила тебе кое-что 🔥")

# === Webhook обработка ===
@app.route(f"/{TOKEN}", methods=["POST"])
async def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    await application.update_queue.put(update)
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Бот работает!"

# === Запуск приложения ===
if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Настрой webhook
    async def set_webhook():
        await bot.set_webhook(f"{URL}/{TOKEN}")

    import asyncio
    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
