import os
import re
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# HANDLER DE MENSAGENS
def handle_message(update, context):
    if update.effective_chat.id != int(GROUP_ID):
        return
    processar_mensagem(update, context)

dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.document, handle_message))

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'OK'

@app.route('/')
def index():
    return 'Bot rodando!'

# Envio automático de resumo a cada hora
def enviar_resumo_automatico():
    from processador import enviar_resumo_comprovantes
    enviar_resumo_comprovantes(bot, GROUP_ID)

scheduler = BackgroundScheduler()
scheduler.add_job(enviar_resumo_automatico, 'interval', hours=1)
scheduler.start()

if __name__ == '__main__':
    app.run(port=5000, debug=False)
