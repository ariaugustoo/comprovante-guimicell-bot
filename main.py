import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import (
    processar_mensagem,
    marcar_como_pago,
    total_pendentes,
    listar_pendentes,
    listar_confirmados_pagamento,
    ajuda_comandos,
    total_geral,
    listar_todos_confirmados,
    ultimo_comprovante
)

# Variáveis de ambiente
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = Bot(token=TOKEN)

app = Flask(__name__)

dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

def registrar_handlers():
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.chat(GROUP_ID), processar_mensagem))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^✅$') & Filters.chat(GROUP_ID), marcar_como_pago))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^total que devo$') & Filters.chat(GROUP_ID), total_pendentes))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^listar pendentes$') & Filters.chat(GROUP_ID), listar_pendentes))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^listar pagos$') & Filters.chat(GROUP_ID), listar_confirmados_pagamento))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^ajuda$') & Filters.chat(GROUP_ID), ajuda_comandos))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^total geral$') & Filters.chat(GROUP_ID), total_geral))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^último comprovante$') & Filters.chat(GROUP_ID), ultimo_comprovante))

@app.route('/')
def home():
    return 'Bot está rodando com sucesso!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok!"

if __name__ == '__main__':
    registrar_handlers()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
