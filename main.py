import logging
from flask import Flask, request
from telegram import Bot, Update
from processador import (
    processar_comprovante,
    marcar_como_pago,
    total_pendentes,
    listar_pendentes,
    listar_pagos,
    ajuda,
    ultimo_comprovante,
    total_geral
)

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002626449000

bot = Bot(token=TOKEN)
app = Flask(__name__)

# Logs
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/")
def home():
    return "Bot está rodando com webhook!", 200

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        message = update.effective_message

        if message.chat.id != GROUP_ID:
            return "Ignorado: outro grupo", 200

        if message.text:
            texto = message.text.strip().lower()

            if texto.endswith("pix"):
                processar_comprovante(bot, message, tipo="pix")
            elif "x" in texto:
                processar_comprovante(bot, message, tipo="cartao")
            elif texto == "✅":
                marcar_como_pago(bot, message)
            elif texto == "total que devo":
                total_pendentes(bot, message)
            elif texto == "listar pendentes":
                listar_pendentes(bot, message)
            elif texto == "listar pagos":
                listar_pagos(bot, message)
            elif texto == "ajuda":
                ajuda(bot, message)
            elif texto == "último comprovante":
                ultimo_comprovante(bot, message)
            elif texto == "total geral":
                total_geral(bot, message)

        elif message.photo or message.document:
            processar_comprovante(bot, message, tipo="imagem")

    except Exception as e:
        logger.error(f"Erro no webhook: {e}")

    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True)
