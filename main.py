import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from processador import (
    processar_mensagem,
    listar_comandos,
    registrar_pagamento,
    listar_pendentes,
    listar_pagos,
    solicitar_pagamento,
    comando_ajuda,
    comando_status
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot de comprovantes online!'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    processar_mensagem(update)
    return 'ok'

if __name__ == '__main__':
    from telegram import Bot
    from telegram.ext import Updater

    bot = Bot(token=TOKEN)
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", comando_ajuda))
    dp.add_handler(CommandHandler("ajuda", comando_ajuda))
    dp.add_handler(CommandHandler("status", comando_status))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, processar_mensagem))

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
