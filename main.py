import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import processar_mensagem, comandos_admin, enviar_resumo_automatico
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)

# Handlers
dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.document, processar_mensagem))
dispatcher.add_handler(CommandHandler("ajuda", comandos_admin))
dispatcher.add_handler(CommandHandler("total", comandos_admin))
dispatcher.add_handler(CommandHandler("total_geral", comandos_admin))
dispatcher.add_handler(CommandHandler("listar_pagos", comandos_admin))
dispatcher.add_handler(CommandHandler("listar_pendentes", comandos_admin))
dispatcher.add_handler(CommandHandler("último", comandos_admin))
dispatcher.add_handler(CommandHandler("limpar", comandos_admin))
dispatcher.add_handler(CommandHandler("corrigir", comandos_admin))

# Agendador com timezone correto
scheduler = BackgroundScheduler()
br_timezone = timezone("America/Sao_Paulo")
scheduler.add_job(enviar_resumo_automatico, 'interval', hours=1, timezone=br_timezone)
scheduler.start()

@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "OK"

@app.route("/")
def home():
    return "Bot ativo com webhook!"

if __name__ == "__main__":
    app.run(debug=True)
