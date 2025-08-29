import os
from flask import Flask, request
import telegram
from telegram import Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    marcar_como_pago,
    quanto_devo,
    total_a_pagar,
    solicitar_pagamento,
    listar_pendentes,
    listar_pagamentos,
    mostrar_ajuda,
    limpar_tudo,
    corrigir_valor,
    status_bot
)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = os.environ.get("GROUP_ID")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

def registrar_handlers():
    dispatcher.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Bot ativo!")))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), processar_mensagem))
    dispatcher.add_handler(CommandHandler("status", status_bot))
    dispatcher.add_handler(CommandHandler("limpar", limpar_tudo))
    dispatcher.add_handler(CommandHandler("corrigir", corrigir_valor))
    dispatcher.add_handler(CommandHandler("ajuda", mostrar_ajuda))
    dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
    dispatcher.add_handler(CommandHandler("listar_pagos", listar_pagamentos))

registrar_handlers()

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot ativo com webhook!'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
