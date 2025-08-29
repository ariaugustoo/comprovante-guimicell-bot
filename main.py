import os
from flask import Flask, request
import telegram
from processador import processar_mensagem, registrar_handlers
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = os.environ.get("GROUP_ID")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dp.process_update(update)
    return "ok"

dp = Dispatcher(bot, None, workers=0)
registrar_handlers(dp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
