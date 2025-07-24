import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"
VIP_USERS = [6671597409]  # Buraya VIP istifadəçilərin ID-lərini əlavə et

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# İstifadəçi vəziyyəti və partnyorlar
user_states = {}
partners = {}

# Start menyusu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_states[user.id] = "free"
    keyboard = [
        [InlineKeyboardButton("🔄 Random axtarış", callback_data="random")],
        [InlineKeyboardButton("💬 Hamı ilə söhbət", callback_data="bisexual")],
        [InlineKeyboardButton("👫 Cinsə görə axtarış (VIP)", callback_data="gender")],
        [InlineKeyboardButton("⭐ VIP al", callback_data="buy_vip")]
    ]
    await update.message.reply_text(
        "👋 Salam! Axtarış növünü seç:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Callback düymələr
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "random":
        await start_search(query, context, mode="random")
    elif query.data == "bisexual":
        await start_search(query, context, mode="bisexual")
    elif query.data == "gender":
        if user_id in VIP_USERS:
            await start_search(query, context, mode="gender")
        else:
            await query.message.reply_text("❌ Bu funksiya yalnız VIP istifadəçilər üçündür.")
    elif query.data == "buy_vip":
        await query.message.reply_text("💳 VIP olmaq üçün adminlə əlaqə saxla: @youradmin")
    elif query.data == "leave":
        await leave_chat(user_id, context)

# Axtarış funksiyası
async def start_search(query, context, mode):
    user_id = query.from_user.id
    user_states[user_id] = mode

    # Eyni rejimdə axtaran istifadəçi tap
    for uid, state in user_states.items():
        if uid != user_id and state == mode:
            # Eşləşdir
            user_states[user_id] = "chatting"
            user_states[uid] = "chatting"
            partners[user_id] = uid
            partners[uid] = user_id

            # Tərəfləri məlumatlandır
            await context.bot.send_message(uid, "🤝 Söhbət tapıldı! İndi mesaj yaza və media göndərə bilərsən.\n🔙 Geri çıxmaq üçün menyudan istifadə et.")
            await context.bot.send_message(user_id, "🤝 Söhbət tapıldı! İndi mesaj yaza və media göndərə bilərsən.\n🔙 Geri çıxmaq üçün menyudan istifadə et.")

            # Geri düyməsi
            leave_button = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="leave")]])
            await query.message.reply_text("🗨 Söhbət başladı!", reply_markup=leave_button)
            return

    await query.message.reply_text("🔎 Gözləyin, istifadəçi axtarılır...")

# Söhbətdən çıx
async def leave_chat(user_id, context):
    partner_id = partners.get(user_id)

    user_states[user_id] = "free"
    partners.pop(user_id, None)

    if partner_id:
        user_states[partner_id] = "free"
        partners.pop(partner_id, None)
        await context.bot.send_message(partner_id, "❗ Qarşı tərəf söhbəti tərk etdi.")
    
    await context.bot.send_message(user_id, "🔚 Söhbətdən çıxdınız. Baş menyuya qayıtdınız.")
    await context.bot.send_message(user_id, "⬇️ Menyu:", reply_markup=main_menu())

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Random axtarış", callback_data="random")],
        [InlineKeyboardButton("💬 Hamı ilə söhbət", callback_data="bisexual")],
        [InlineKeyboardButton("👫 Cinsə görə axtarış (VIP)", callback_data="gender")],
        [InlineKeyboardButton("⭐ VIP al", callback_data="buy_vip")]
    ])

# Mesajları ötürmək
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = partners.get(user_id)

    if user_states.get(user_id) != "chatting" or not partner_id:
        await update.message.reply_text("❗ Hazırda söhbətdə deyilsiniz. Menyudan seçim edin.")
        return

    try:
        await update.message.copy(chat_id=partner_id)
    except Exception as e:
        logger.error(f"Mesaj ötürülmədi: {e}")
        await update.message.reply_text("❌ Qarşı tərəfə göndərilə bilmədi.")

# Botu işə sal
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))

    print("✅ Bot işə düşdü.")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
