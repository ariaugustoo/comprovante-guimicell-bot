import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot está ativo!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "ok"

def responder(update, context):
    mensagem = update.message
    resposta = processar_mensagem(mensagem)
    if resposta:
        context.bot.send_message(chat_id=mensagem.chat_id, text=resposta, parse_mode="Markdown")

from telegram.ext import CallbackContext

dispatcher = Dispatcher(bot, None, use_context=True)
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), responder))

if __name__ == "__main__":
    app.run()
