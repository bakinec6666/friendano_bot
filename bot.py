import os
import logging
from flask import Flask, request
from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# --- Логирование ---
logging.basicConfig(level=logging.INFO)

# --- Переменные окружения ---
TOKEN = os.getenv("TOKEN", "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc")
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- Flask-приложение ---
app = Flask(__name__)
VIP_USERS = set()

# --- Обработчик /start ---
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
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- Обработка кнопок ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_vip":
        if not PAYMENT_TOKEN:
            await query.message.reply_text("⚠️ Платежи пока не настроены.")
            return

        prices = [LabeledPrice("🔥 VIP доступ", 19900)]
        await query.message.bot.send_invoice(
            chat_id=query.from_user.id,
            title="Подписка на интимный контент",
            description="Разблокируй фото, видео и голосовые от ИИ-девушки.",
            payload="vip_access",
            provider_token=PAYMENT_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="vip-subscription"
        )

# --- Обработка сообщений и оплаты ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.effective_message

    if not message:
        return

    if message.successful_payment:
        VIP_USERS.add(user_id)
        await message.reply_text("✅ Оплата прошла успешно! Доступ к интимному контенту разблокирован.")
        return

    text = message.text.lower()
    if "фото" in text or "покажи" in text:
        if user_id in VIP_USERS:
            await message.reply_photo(
                photo="https://telegra.ph/file/ea3f31c849fbcb4e24237.jpg",
                caption="Вот тебе моё горячее фото 😘"
            )
        else:
            keyboard = [[InlineKeyboardButton("🔥 Получить доступ", callback_data="get_vip")]]
            await message.reply_text("🔒 Только для VIP! Оформи доступ ниже:",
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text("❤️ Напиши «фото» — и я пришлю тебе кое-что особенное 😘")

# --- Настройка Telegram-приложения ---
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Webhook обработчик ---
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "🤖 Бот работает!"

# --- Запуск ---
if __name__ == "__main__":
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        await application.initialize()
        await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
        print("✅ Webhook установлен!")

    loop.run_until_complete(run())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
