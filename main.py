import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Configuração do bot e Flask
app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def handle_message(update: Update, context):
    mensagem = update.message
    user_id = mensagem.from_user.id
    texto = mensagem.text.strip() if mensagem.text else ""

    resposta = processar_mensagem(texto, user_id)

    if resposta:
        bot.send_message(chat_id=mensagem.chat.id, text=resposta)

dispatcher.add_handler(MessageHandler(Filters.text & Filters.chat(chat_id=GROUP_ID), handle_message))

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return 'OK'
    return 'Invalid request'

@app.route('/')
def home():
    return 'Bot ativo!'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
