import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from telegram.ext import CallbackContext
from processador import processar_mensagem
from dotenv import load_dotenv
from telegram import Bot

# Carregar variáveis do .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

# Verificações de segurança
if TOKEN is None or GROUP_ID is None:
    raise ValueError("TELEGRAM_TOKEN ou GROUP_ID não configurados corretamente no .env.")

# Iniciar bot e app Flask
bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=1, use_context=True)

# Configurar logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Handler para mensagens recebidas
def handle_message(update: Update, context: CallbackContext):
    if update.message:
        processar_mensagem(update, context)

dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.document, handle_message))

# Rota de teste
@app.route('/')
def index():
    return 'Bot está online!'

# Webhook do Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'

if __name__ == '__main__':
    app.run(debug=False)
