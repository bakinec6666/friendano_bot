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

# Получение переменных окружения
TOKEN = os.environ.get("TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("❌ Переменные окружения TOKEN или WEBHOOK_URL не заданы!")

# Flask приложение
app = Flask(__name__)

# Переменные состояний
IP, PORT, METHOD = range(3)
user_data = {}

# Тест TCP
async def tcp_test(ip, port, count=20):
    loop = asyncio.get_event_loop()
    success, fail = 0, 0

    def tcp_connect():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.close()
            return True
        except:
            return False

    results = await asyncio.gather(*[loop.run_in_executor(None, tcp_connect) for _ in range(count)])
    for r in results:
        if r: success += 1
        else: fail += 1
    return success, fail

# Тест UDP
async def udp_test(ip, port, count=20):
    loop = asyncio.get_event_loop()
    success, fail = 0, 0

    def udp_send():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            sock.sendto(b"test", (ip, port))
            sock.close()
            return True
        except:
            return False

    results = await asyncio.gather(*[loop.run_in_executor(None, udp_send) for _ in range(count)])
    for r in results:
        if r: success += 1
        else: fail += 1
    return success, fail

# Команда /start
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
    await update.message.reply_text("Привет! Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

# Обработка кнопок
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
        info = user_data.get(user_id, {})
        ip = info.get('ip')
        port = info.get('port')
        method = info.get('method')
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
        await query.edit_message_text(f"Результаты:\n✅ Успешно: {success}\n❌ Ошибок: {fail}")
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

# Ввод IP
async def ip_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ip = update.message.text.strip()
    parts = ip.split('.')
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        await update.message.reply_text("❗ Неверный IP. Попробуйте ещё раз.")
        return IP
    user_data[user_id]['ip'] = ip
    await update.message.reply_text(f"✅ IP установлен: {ip}")
    return ConversationHandler.END

# Ввод порта
async def port_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    port_text = update.message.text.strip()
    if not port_text.isdigit():
        await update.message.reply_text("Порт должен быть числом.")
        return PORT
    port = int(port_text)
    if not (1 <= port <= 65535):
        await update.message.reply_text("Порт вне диапазона 1-65535.")
        return PORT
    user_data[user_id]['port'] = port
    await update.message.reply_text(f"✅ Порт установлен: {port}")
    return ConversationHandler.END

# Выбор метода
async def method_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data.replace("method_", "")
    user_id = query.from_user.id
    user_data[user_id]['method'] = method
    await query.edit_message_text(f"Выбран метод: {method.upper()}")
    return ConversationHandler.END

# Webhook маршрут
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_update = request.get_json(force=True)
    update = Update.de_json(json_update)
    loop = asyncio.get_event_loop()
    task = loop.create_task(application.process_update(update))
    loop.run_until_complete(task)
    return 'OK'

# Главная страница
@app.route('/')
def index():
    return "✅ Бот работает!"

# Основной async запуск
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
    await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

    def run_flask():
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

    Thread(target=run_flask).start()

if __name__ == '__main__':
    asyncio.run(main_async())
