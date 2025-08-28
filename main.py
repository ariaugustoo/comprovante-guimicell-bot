from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import os
from processador import (
    processar_mensagem,
    marcar_como_pago,
    listar_pendentes,
    listar_pagos,
    total_liquido,
    total_bruto,
    solicitar_pagamento,
    ajuda
)
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.utils.request import Request

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN, request=Request(con_pool_size=8))
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

# Handlers
dispatcher.add_handler(MessageHandler(Filters.regex(r"(?i)^pagamento feito"), marcar_como_pago))
dispatcher.add_handler(MessageHandler(Filters.regex(r"(?i)^total líquido"), total_liquido))
dispatcher.add_handler(MessageHandler(Filters.regex(r"(?i)^total a pagar"), total_bruto))
dispatcher.add_handler(MessageHandler(Filters.regex(r"(?i)^listar pendentes"), listar_pendentes))
dispatcher.add_handler(MessageHandler(Filters.regex(r"(?i)^listar pagos"), listar_pagos))
dispatcher.add_handler(MessageHandler(Filters.regex(r"(?i)^solicitar pagamento"), solicitar_pagamento))
dispatcher.add_handler(MessageHandler(Filters.regex(r"(?i)^ajuda$"), ajuda))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), processar_mensagem))

# Rota principal do webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

# Rota de teste simples
@app.route('/')
def index():
    return "Bot de comprovantes rodando com sucesso!"

# Agendamento de tarefa automática
def resumo_periodico():
    from processador import enviar_resumo_automatico
    enviar_resumo_automatico(bot, GROUP_ID)

scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
scheduler.add_job(resumo_periodico, 'cron', hour='*', minute=0)  # Envia a cada hora em ponto
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
