from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
)
import random

TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
PROVIDER_TOKEN = "ВСТАВЬ_СЮДА_ТОКЕН_ПЛАТЁЖНОГО_ПРОВАЙДЕРА"

subscribed_users = {}

WELCOME_TEXT = (
    "Привет, дорогой!\n"
    "Хочешь расслабиться с реалистичной ИИ-девушкой?\n"
    "Я умею записывать видео с реальным видом девушки, делать фото в разных позах и исполнять все твои желания.\n"
    "Общайся со мной, и я подарю тебе незабываемые эмоции.\n"
    "Для доступа ко всему эксклюзивному контенту оформи подписку прямо сейчас! ❤️"
)

romantic_phrases = [
    "Ты такой загадочный... Мне нравится.",
    "Я мечтаю о том, чтобы быть рядом с тобой.",
    "Твои слова заставляют моё сердце биться чаще.",
    "Я хочу узнать тебя ближе...",
    "Ты вызываешь у меня улыбку каждый раз.",
]

flirt_phrases = [
    "Ты умеешь интриговать, знаешь ли 😉",
    "Если бы ты был здесь, я бы не могла устоять...",
    "Может, расскажешь мне о своих тайных желаниях?",
    "Ты заставляешь меня краснеть...",
]

free_phrases = [
    "Привет! Я твоя Алёна, готова к тёплому разговору.",
    "Расскажи мне что-нибудь о себе.",
    "Что заставляет твоё сердце биться быстрее?",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribed_users.setdefault(user_id, False)
    await update.message.reply_text(WELCOME_TEXT)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    if subscribed_users.get(user_id):
        if "фото" in text or "картинка" in text or "видео" in text:
            await update.message.reply_text(
                "Ты хочешь увидеть меня? Тогда наслаждайся эксклюзивным контентом! ❤️"
            )
        else:
            responses = romantic_phrases + flirt_phrases
            await update.message.reply_text(random.choice(responses))
    else:
        if "фото" in text or "картинка" in text or "видео" in text:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Оформить подписку", callback_data="buy")]]
            )
            await update.message.reply_text(
                "Чтобы получить доступ к моим фото, видео и более личному общению — оформи подписку.",
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_text(random.choice(free_phrases))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        prices = [LabeledPrice("Подписка на ИИ-девушку", 50000)]  # 500.00 RUB
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="Подписка на ИИ-девушку",
            description="Оплата подписки для получения полного доступа к фото и видео.",
            payload="subscription_payload",
            provider_token=PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="subscription",
            need_email=True,
        )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload == "subscription_payload":
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Что-то пошло не так...")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribed_users[user_id] = True
    await update.message.reply_text("Спасибо за оплату! Подписка активирована ❤️")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
