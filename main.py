import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher
from processador import registrar_handlers
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, update_queue=None, use_context=True)

registrar_handlers(dispatcher, GROUP_ID, ADMIN_ID)

# Agendador de resumo automático a cada hora
scheduler = BackgroundScheduler(timezone=pytz.timezone('America/Sao_Paulo'))
from processador import enviar_resumo_automatico
scheduler.add_job(enviar_resumo_automatico, 'cron', minute=0, id='resumo_job', args=[bot, GROUP_ID])
scheduler.start()

@app.route('/')
def home():
    return 'Bot do Comprovante rodando com webhook!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

if __name__ == "__main__":
    app.run(port=10000)
