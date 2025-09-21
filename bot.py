import sqlite3, random, string
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

# ===================== Настройки =====================
TOKEN = "7323003204:AAEuLZHtAmhy0coPk3tMEQamsa9ftuUguGc"      # <- Вставь токен своего бота
ADMIN_USERNAME = "user666321"      # <- Ник Telegram администратора
ADMIN_ID = 123456789              # <- Числовой Telegram ID администратора

# ===================== Flask =====================
app = Flask(__name__)
bot = Bot(token=TOKEN)

# ===================== Database =====================
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance REAL DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS vouchers (
    code TEXT PRIMARY KEY,
    amount REAL,
    status TEXT DEFAULT 'active'
)
""")
conn.commit()

# ===================== Состояния ConversationHandler =====================
VOUCHER_INPUT = 1
SLOT_BET = 2
AVIATOR_BET = 3

# ===================== Вспомогательные функции =====================
def get_balance(user_id):
    cursor.execute("SELECT balance FROM players WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else 0

def add_balance(user_id, amount):
    cursor.execute("INSERT OR IGNORE INTO players(user_id, username) VALUES(?,?)",
                   (user_id, None))
    cursor.execute("UPDATE players SET balance = balance + ? WHERE user_id=?",
                   (amount, user_id))
    conn.commit()

def generate_voucher(amount):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    cursor.execute("INSERT INTO vouchers(code, amount) VALUES(?,?)", (code, amount))
    conn.commit()
    return code

def use_voucher(code):
    cursor.execute("SELECT amount, status FROM vouchers WHERE code=?", (code,))
    res = cursor.fetchone()
    if not res:
        return None, "Kod tapılmadı"
    if res[1] != "active":
        return None, "Kod artıq istifadə edilib"
    cursor.execute("UPDATE vouchers SET status='used' WHERE code=?", (code,))
    conn.commit()
    return res[0], None

def main_menu_keyboard():
    kb = [
        [InlineKeyboardButton("🎰 Oyunlar", callback_data="games")],
        [InlineKeyboardButton("💰 Balansı artır", callback_data="topup")],
        [InlineKeyboardButton("🎟️ Vaçeri aktivləşdir", callback_data="voucher")],
        [InlineKeyboardButton("📊 Balansım", callback_data="balance")],
    ]
    return InlineKeyboardMarkup(kb)

def games_menu_keyboard():
    kb = [
        [InlineKeyboardButton("🎰 Slota", callback_data="slot")],
        [InlineKeyboardButton("✈️ Aviator", callback_data="aviator")],
        [InlineKeyboardButton("↩️ Geri", callback_data="back")],
    ]
    return InlineKeyboardMarkup(kb)

# ===================== Handlers =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("SELECT user_id FROM players WHERE user_id=?", (user.id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO players(user_id, username, balance) VALUES(?,?,?)",
                       (user.id, user.username, 0))
        conn.commit()
        welcome_text = f"""
🎉 Xoş gəlmisiniz, {user.first_name}! 🎉

Casino dünyasına xoş gəldiniz! 🃏💰

💡 Balansınızı artırmaq üçün administrator ilə əlaqə saxlayın: 
tg://resolve?domain={ADMIN_USERNAME}

💎 Bonus fürsəti: ilk depozitinizdə 50% əlavə bonus qazanın! 🤑

🎰 İndi oyunlar seçin, əylənin və şansınızı sınayın!

📊 Balansınızı yoxlamaq üçün “Balansım” düyməsinə klikləyin.
"""
        await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("Xoş gəldiniz geri!", reply_markup=main_menu_keyboard())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "topup":
        await query.edit_message_text(
            f"Balans artırmaq üçün administrator ilə əlaqə saxlayın:\n"
            f"tg://resolve?domain={ADMIN_USERNAME}"
        )

    elif query.data == "balance":
        bal = get_balance(user.id)
        await query.edit_message_text(f"Sizin balansınız: {bal:.2f} AZN")

    elif query.data == "voucher":
        await query.edit_message_text("Vaçer kodunu daxil edin:")
        return VOUCHER_INPUT

    elif query.data == "games":
        await query.edit_message_text("Oyun seçin:", reply_markup=games_menu_keyboard())

    elif query.data == "slot":
        await query.edit_message_text("🎰 Slota oyununa xoş gəldiniz!\nMəbləği daxil edin (AZN):")
        return SLOT_BET

    elif query.data == "aviator":
        await query.edit_message_text("✈️ Aviator oyununa xoş gəldiniz!\nMəbləği daxil edin (AZN):")
        return AVIATOR_BET

    elif query.data == "back":
        await query.edit_message_text("Əsas menyu:", reply_markup=main_menu_keyboard())

# ===================== Voucher =====================
async def voucher_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    code = update.message.text.strip().upper()
    amount, err = use_voucher(code)
    if err:
        await update.message.reply_text(err)
        return ConversationHandler.END
    add_balance(user.id, amount)
    await update.message.reply_text(f"Uğurla aktivləşdirildi! {amount:.2f} AZN balansınıza əlavə olundu.")
    return ConversationHandler.END

# ===================== Slot Game =====================
async def slot_bet_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        bet = float(update.message.text.strip())
    except:
        await update.message.reply_text("Ədəd daxil edin!")
        return ConversationHandler.END

    balance = get_balance(user.id)
    if bet > balance:
        await update.message.reply_text("Balansınız yetərli deyil!")
        return ConversationHandler.END

    add_balance(user.id, -bet)
    symbols = ["🍒","🍋","🍉","🍇","🍀"]
    result = random.choices(symbols, k=3)
    await update.message.reply_text(f"🎰 {' | '.join(result)}")

    if result[0] == result[1] == result[2]:
        win = bet * 5
        add_balance(user.id, win)
        await update.message.reply_text(f"Təbriklər! Uduş: {win:.2f} AZN")
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win = bet * 2
        add_balance(user.id, win)
        await update.message.reply_text(f"Yaxşı! Uduş: {win:.2f} AZN")
    else:
        await update.message.reply_text("Uduş olmadı. Daha yaxşı şansla!")

    return ConversationHandler.END

# ===================== Aviator Game =====================
async def aviator_bet_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        bet = float(update.message.text.strip())
    except:
        await update.message.reply_text("Ədəd daxil edin!")
        return ConversationHandler.END

    balance = get_balance(user.id)
    if bet > balance:
        await update.message.reply_text("Balansınız yetərli deyil!")
        return ConversationHandler.END

    add_balance(user.id, -bet)
    crash = round(random.uniform(1.0, 15.0), 2)
    context.user_data["aviator"] = {"bet": bet, "crash": crash, "cashed_out": False}

    await update.message.reply_text(f"Uçuş başladı! Maksimal koeff: {crash}\nMesaj yazın: 'cashout' kəş-aot üçün")
    return ConversationHandler.END

async def aviator_cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.message.text.lower() != "cashout":
        return
    data = context.user_data.get("aviator")
    if not data or data["cashed_out"]:
        return
    bet = data["bet"]
    crash = data["crash"]
    coeff = round(random.uniform(1.0, crash), 2)
    win = bet * coeff
    add_balance(user.id, win)
    data["cashed_out"] = True
    await update.message.reply_text(f"Kəş-aot edildi! Koef: {coeff:.2f}, Uduş: {win:.2f} AZN")

# ===================== Admin Commands =====================
async def createvoucher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("Bu əmri yalnız admin istifadə edə bilər.")
        return
    if not context.args or not context.args[0].replace(".", "").isdigit():
        await update.message.reply_text("İstifadə: /createvoucher <məbləğ>")
        return
    amount = float(context.args[0])
    code = generate_voucher(amount)
    await update.message.reply_text(f"Vaçer yaradıldı: {code} → {amount:.2f} AZN")

# ===================== Flask Webhook =====================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    ApplicationBuilder().token(TOKEN).build().process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Bot işləyir!"

# ===================== Main =====================
if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(callback_handler)],
        states={
            VOUCHER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, voucher_input)],
            SLOT_BET: [MessageHandler(filters.TEXT & ~filters.COMMAND, slot_bet
