from flask import Flask, request
from telegram import Bot, Update
from processador import (
    processar_mensagem,
    listar_pendentes,
    listar_pagos,
    marcar_como_pago,
    obter_ultimo_comprovante,
    calcular_total_geral,
    calcular_total_pendentes
)
import logging

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002122662652
bot = Bot(token=TOKEN)

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot está rodando com webhook!", 200

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        if update.message:
            processar_mensagem(bot, update.message)
    except Exception as e:
        logging.error(f"Erro no webhook: {e}")
    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True)
