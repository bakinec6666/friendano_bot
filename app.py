import os
import socket
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler, ContextTypes
)
from threading import Thread

TOKEN = os.environ.get("TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

app = Flask(__name__)

IP, PORT, METHOD = range(3)
user_data = {}

async def tcp_test(ip, port, count=20):
    loop = asyncio.get_event_loop()
    success = 0
    fail = 0

    def tcp_connect():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.close()
            return True
        except:
            return False

    tasks = [loop.run_in_executor(None, tcp_connect) for _ in range(count)]
    results = await asyncio.gather(*tasks)
    for r in results:
        if r:
            success += 1
        else:
            fail += 1
    return success, fail

async def udp_test(ip, port, count=20):
    loop = asyncio.get_event_loop()
    success = 0
    fail = 0

    def udp_send():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            sock.sendto(b"test", (ip, port))
            sock.close()
            return True
        except:
            return False

    tasks = [loop.run_in_executor(None, udp_send) for _ in range(count)]
    results = await asyncio.gather(*tasks)
    for r in results:
        if r:
            success += 1
        else:
            fail += 1
    return success, fail

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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
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
        elif method == 'udp':
            success, fail = await udp_test(ip, port)
        else:
            await query.edit_message_text("Неизвестный метод.")
            return ConversationHandler.END
        await query.edit_message_text(f"Результаты:\nУспешно: {success}\nОшибок: {fail}")
        return ConversationHandler.END
    elif data == 'reset':
        user_data[user_id] = {}
        await query.edit_message_text("Данные сброшены.")
        return ConversationHandler.END
    elif data == 'cancel':
        await query.edit_message_text("Отмена.")
        return ConversationHandler.END
    else:
        await query.edit_message_text("Неизвестная команда.")
        return ConversationHandler.END

async def ip_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ip = update.message.text.strip()
    parts = ip.split('.')
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        await update.message.reply_text("Неверный IP, попробуйте ещё раз.")
        return IP
    user_data[user_id]['ip'] = ip
    await update.message.reply_text(f"IP установлен: {ip}")
    return ConversationHandler.END

async def port_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    port_text = update.message.text.strip()
    if not port_text.isdigit():
        await update.message.reply_text("Порт должен быть числом, попробуйте ещё раз.")
        return PORT
    port = int(port_text)
    if port < 1 or port > 65535:
        await update.message.reply_text("Порт вне диапазона 1-65535.")
        return PORT
    user_data[user_id]['port'] = port
    await update.message.reply_text(f"Порт установлен: {port}")
    return ConversationHandler.END

async def method_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    method = query.data.replace('method_', '')
    user_id = query.from_user.id
    user_data[user_id]['method'] = method
    await query.answer()
    await query.edit_message_text(f"Выбран метод: {method.upper()}")
    return ConversationHandler.END

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    from telegram import Update
    json_update = request.get_json(force=True)
    update = Update.de_json(json_update, application.bot)
    asyncio.run(application.process_update(update))
    return 'OK'

@app.route('/')
def index():
    return "Бот работает"

async def main_async():
    global application
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CallbackQueryHandler(button_handler)],
        states={
            IP: [MessageHandler(filters.TEXT & ~filters.COMMAND, ip_input)],
            PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, port_input)],
            METHOD: [CallbackQueryHandler(method_choice, pattern='^method_')],
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)

    # Устанавливаем webhook с await
    await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

    # Запускаем Flask в отдельном потоке
    def run_flask():
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

if __name__ == '__main__':
    asyncio.run(main_async())
