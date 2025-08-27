import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    gerar_resumo,
    marcar_como_pago,
    listar_pendentes,
    listar_pagamentos,
    limpar_comprovantes,
    ultimo_comprovante,
    total_geral,
    ajuda,
    corrigir_valor
)

# Carrega variáveis de ambiente do .env se estiver rodando localmente
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0)

# Handlers de comandos
dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(CommandHandler("listarpendentes", listar_pendentes))
dispatcher.add_handler(CommandHandler("listarpagos", listar_pagamentos))
dispatcher.add_handler(CommandHandler("limpartudo", limpar_comprovantes, filters=Filters.user(user_id=ADMIN_ID)))
dispatcher.add_handler(CommandHandler("corrigirvalor", corrigir_valor, filters=Filters.user(user_id=ADMIN_ID)))
dispatcher.add_handler(CommandHandler("últimocomprovante", ultimo_comprovante))
dispatcher.add_handler(CommandHandler("totalgeral", total_geral))

# Handlers de mensagens e marcação como pago
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), processar_mensagem))
dispatcher.add_handler(MessageHandler(Filters.regex("✅"), marcar_como_pago))

# Webhook do Telegram
@app.route(f'/{TOKEN}', methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# Página de teste de status
@app.route("/", methods=["GET"])
def index():
    return "🤖 Bot rodando com sucesso!", 200

# Inicialização
if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    port = int(os.environ.get("PORT", 5000))  # Porta usada pelo Render
    app.run(host="0.0.0.0", port=port)        # CORREÇÃO: escuta em 0.0.0.0
