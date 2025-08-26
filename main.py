import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from processador import processar_mensagem, marcar_como_pago, listar_pendentes, listar_pagamentos, calcular_total_pendente, calcular_total_geral, ultimo_comprovante, ajuda

BOT_TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002626449000

# Inicializa o bot
bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

# Comandos
bot_app.add_handler(CommandHandler("ajuda", ajuda))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^✅$"), marcar_como_pago))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^listar pendentes$"), listar_pendentes))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^listar pagos$"), listar_pagamentos))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^total que devo$"), calcular_total_pendente))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^total geral$"), calcular_total_geral))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^último comprovante$"), ultimo_comprovante))

# Qualquer outra mensagem
bot_app.add_handler(MessageHandler(filters.ALL, processar_mensagem))

# Flask app
flask_app = Flask(__name__)

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook() -> str:
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        await bot_app.process_update(update)
    return "OK"

@flask_app.route("/", methods=["GET"])
def index():
    return "Bot rodando via webhook com sucesso!"

if __name__ == "__main__":
    import requests
    webhook_url = "https://comprovante-guimicell-bot-vmvr.onrender.com"
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}/{BOT_TOKEN}")
    print("Webhook registrado com sucesso!")
    
    bot_app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        path="/"  # ✅ CORRIGIDO
    )
