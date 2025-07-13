import os
import socket
import asyncio
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Dispatcher, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler, ContextTypes
)

# Твой токен здесь (рекомендуется хранить в переменных окружения)
TOKEN = "7323003204:AAGK9y-OOit1gt1tfponSRjYislQgbP_xls"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://yourapp.onrender.com - ставь в Render

app = Flask(__name__)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, update_queue=None, use_context=True)

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
            sock = socket.socket(socket.AF
