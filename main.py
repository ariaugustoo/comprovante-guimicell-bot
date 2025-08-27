import os
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler, Filters, Dispatcher
from apscheduler.schedulers.background import BackgroundScheduler
from processador import (
    processar_mensagem,
    marcar_como_pago,
    listar_pendentes,
    listar_pagos,
    ajuda,
    total_que_devo,
    total_geral,
    ultimo_comprovante,
    limpar_tudo,
    corrigir_valor
)

# Carregar variáveis do .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=1)

# Handlers
dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo | (Filters.text & (~Filters.command)), processar_mensagem))
dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(r"^✅$"), marcar_como_pago))
dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
dispatcher.add_handler(CommandHandler("listar_pagos", listar_pagos))
dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(CommandHandler("total_que_devo", total_que_devo))
dispatcher.add_handler(CommandHandler("total_geral", total_geral))
dispatcher.add_handler(CommandHandler("ultimo_comprovante", ultimo_comprovante))
dispatcher.add_handler(CommandHandler("limpar_tudo", limpar_tudo))
dispatcher.add_handler(CommandHandler("corrigir_valor", corrigir_valor))

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

def enviar_resumo_periodico():
    total_pendente = total_que_devo(update=None, context=None, resumo=True)
    if total_pendente:
        bot.send_message(chat_id=GROUP_ID, text=total_pendente)

scheduler = BackgroundScheduler()
scheduler.add_job(enviar_resumo_periodico, "interval", hours=1)
scheduler.start()

if __name__ == "__main__":
    app.run(port=10000)
