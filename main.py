import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN)

app = Flask(__name__)

dispatcher = Dispatcher(bot, None, workers=1)

def handle_message(update, context):
    processar_mensagem(update)

dispatcher.add_handler(MessageHandler(Filters.text & Filters.chat(GROUP_ID), handle_message))

@app.route('/')
def index():
    return 'Bot ativo!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'

if __name__ == '__main__':
    app.run(port=10000)
