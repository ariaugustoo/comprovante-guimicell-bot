from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import processar_mensagem, gerar_resumo_automatico, comandos_handler
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0)

dispatcher.add_handler(CommandHandler("ajuda", comandos_handler))
dispatcher.add_handler(CommandHandler("listar_pendentes", comandos_handler))
dispatcher.add_handler(CommandHandler("listar_pagos", comandos_handler))
dispatcher.add_handler(CommandHandler("total_que_devo", comandos_handler))
dispatcher.add_handler(CommandHandler("total_geral", comandos_handler))
dispatcher.add_handler(CommandHandler("ultimo_comprovante", comandos_handler))
dispatcher.add_handler(CommandHandler("corrigir_valor", comandos_handler))
dispatcher.add_handler(CommandHandler("limpar_tudo", comandos_handler))
dispatcher.add_handler(MessageHandler(Filters.text & Filters.group, processar_mensagem))

def agendador_resumo():
    while True:
        gerar_resumo_automatico(bot, GROUP_ID)
        time.sleep(3600)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

if __name__ == "__main__":
    threading.Thread(target=agendador_resumo).start()
    app.run(port=10000)
