import os
import re
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from processador import (
    processar_mensagem,
    comandos_suporte,
    listar_pendentes,
    listar_pagos,
    ultimo_comprovante,
    total_geral,
    total_pendentes
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

dispatcher = Dispatcher(bot, None, use_context=True)

# --- Funções principais ---
def handle_texto(update, context):
    mensagem = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if mensagem.strip() == "✅":
        context.bot.send_message(chat_id=chat_id, text="✅ Comprovante marcado como pago.")
        return

    resposta = processar_mensagem(mensagem, user_id)
    context.bot.send_message(chat_id=chat_id, text=resposta)

def handle_foto(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="📸 Foto recebida. Aguarde o processamento.")

def registrar_handlers():
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_texto))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_foto))
    dispatcher.add_handler(CommandHandler("ajuda", comandos_suporte))
    dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
    dispatcher.add_handler(CommandHandler("listar_pagos", listar_pagos))
    dispatcher.add_handler(CommandHandler("ultimo_comprovante", ultimo_comprovante))
    dispatcher.add_handler(CommandHandler("total_geral", total_geral))
    dispatcher.add_handler(CommandHandler("total_que_devo", total_pendentes))
    # ❌ comando com emoji REMOVIDO pois não é permitido

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot do Comprovante rodando!", 200

if __name__ == "__main__":
    registrar_handlers()
    app.run(host="0.0.0.0", port=10000)
