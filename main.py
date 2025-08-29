import os
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import (
    processar_mensagem,
    marcar_como_pago,
    listar_pendentes,
    listar_pagamentos,
    total_pendente_liquido,
    total_bruto_pendente,
    registrar_pagamento_parcial,
    solicitar_pagamento,
    gerar_status
)

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

@app.route('/')
def home():
    return 'Bot está no ar!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        payload = request.get_json()
        if payload:
            update = Update.de_json(payload, bot)
            processar_mensagem(update)
        return 'ok', 200

# Configurar Bot e Dispatcher
from telegram import Bot
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Rota para processar comandos manuais via GET (opcional)
@app.route('/comando', methods=['GET'])
def comando():
    return 'Use /webhook para interagir com o bot.'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
