import os
import asyncio
import socket
from flask import Flask, request
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# Константы состояний
IP, PORT, METHOD = range(3)

# Flask приложение
app = Flask(__name__)

# Глобальные переменные
user_data = {}

# Получаем переменные окружения
TOKEN = os.environ.get("TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("❌ Переменные окружения TOKEN и WEBHOOK_URL не заданы!")

application = Application.builder().token(TOKEN).build()

# Хэндлер /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {}
    keyboard = [
        [InlineKeyboardButton("Ввести IP", callback_data='enter_ip')],
        [InlineKeyboardButton("Ввести порт", callback_data='enter_port')],
        [InlineKeyboardButton("Выбрать метод", callback_data='choose_method')],
        [InlineKeyboardButton("Запустить тест", callback_data='run_test')],
        [InlineKeyboardButton("Сбросить", callback_data='reset')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выберите действие:", reply_markup=reply_markup)

# Хэндлер кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == 'enter_ip':
        await query.edit_message_text("Введите IP адрес:")
        return IP
    elif data == 'enter_port':
        await query.edit_message_text("Введите порт (1-65535):")
        return PORT
    elif data == 'choose_method':
        keyboard = [
            [InlineKeyboardButton("TCP", callback_data='method_tcp')],
            [InlineKeyboardButton("UDP", callback_data='method_udp')],
            [InlineKeyboardButton("Отмена", callback_data='cancel')]
        ]
        await query.edit_message_text("Выберите метод:", reply_markup=InlineKeyboardMarkup(keyboard))
        return METHOD
    elif data == 'run_test':
        data_user = user_data.get(user_id, {})
        ip = data_user.get('ip')
        port = data_user.get('port')
        method = data_user.get('method')
        if not ip or not port or not method:
            await query.edit_message_text("Сначала введите IP, порт и выберите метод.")
            return ConversationHandler.END
        await query.edit_message_text(f"Запускаем {method.upper()} тест на {ip}:{port}...")
        if method == 'tcp':
            success, fail = await tcp_test(ip, port)
        else:
            success, fail = await udp_test(ip, port)
        await query.edit_message_text(f"Результаты:\n✅ Успешно: {success}\n❌ Ошибок: {fail}")
        return ConversationHandler.END
    elif data == 'reset':
        user_data[user_id] = {}
        await query.edit_message_text("Все данные сброшены.")
        return ConversationHandler.END
    elif data == 'cancel':
        await query.edit_message_text("Отменено.")
        return ConversationHandler.END
    else:
        await query.edit_message_text("Неизвестная команда.")
        return ConversationHandler.END

# IP input
async def ip_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ip = update.message.text.strip()
    if not all(p.isdigit() and 0 <= int(p) <= 255 for p in ip.split('.') if p):
        await update.message.reply_text("❌ Неверный IP. Попробуйте снова.")
        return IP
    user_data[user_id]['ip'] = ip
    await update.message.reply_text(f"✅ IP установлен: {ip}")
    return ConversationHandler.END

# Port input
async def port_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    port_text = update.message.text.strip()
    if not port_text.isdigit():
        await update.message.reply_text("❌ Порт должен быть числом.")
        return PORT
    port = int(port_text)
    if not (1 <= port <= 65535):
        await update.message.reply_text("❌ Порт вне диапазона 1-65535.")
        return PORT
    user_data[user_id]['port'] = port
    await update.message.reply_text(f"✅ Порт установлен: {port}")
    return ConversationHandler.END

# Метод (TCP/UDP)
async def method_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    method = query.data.replace('method_', '')
    user_data[user_id]['method'] = method
    await query.answer()
    await query.edit_message_text(f"✅ Метод выбран: {method.upper()}")
    return ConversationHandler.END

# TCP test
async def tcp_test(ip, port, count=20):
    loop = asyncio.get_event_loop()
    def tcp():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((ip, port))
            s.close()
            return True
        except:
            return False
    results = await asyncio.gather(*[loop.run_in_executor(None, tcp) for _ in range(count)])
    return results.count(True), results.count(False)

# UDP test
async def udp_test(ip, port, count=20):
    loop = asyncio.get_event_loop()
    def udp():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.sendto(b"ping", (ip, port))
            s.close()
            return True
        except:
            return False
    results = await asyncio.gather(*[loop.run_in_executor(None, udp) for _ in range(count)])
    return results.count(True), results.count(False)

# Flask webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_update = request.get_json(force=True)
    update = Update.de_json(json_update, application.bot)
    asyncio.run(application.process_update(update))
    return "OK"

@app.route("/")
def home():
    return "✅ Бот запущен и работает."

# Асинхронный запуск
async def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(button_handler)],
        states={
            IP: [MessageHandler(filters.TEXT & ~filters.COMMAND, ip_input)],
            PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, port_input)],
            METHOD: [CallbackQueryHandler(method_choice, pattern="^method_")]
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)

    # Установка webhook
    await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

    # Flask запускаем в отдельном потоке
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()

if __name__ == "__main__":
    asyncio.run(main())
