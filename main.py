import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    listar_pendentes,
    listar_pagamentos,
    solicitar_pagamento,
    marcar_como_pago,
    quanto_devo,
    total_a_pagar,
    ajuda,
    limpar_dados,
    corrigir_valor
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)

dispatcher = Dispatcher(bot, None, workers=0, use_context=True)


def registrar_handlers():
    dispatcher.add_handler(CommandHandler("start", lambda update, context: None))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar_mensagem))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^ajuda$"), ajuda))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^listar pendentes$"), listar_pendentes))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^listar pagos$"), listar_pagamentos))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^solicitar pagamento$"), solicitar_pagamento))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^pagamento feito$"), marcar_como_pago))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^quanto devo$"), quanto_devo))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^total a pagar$"), total_a_pagar))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^limpar tudo$"), limpar_dados))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^corrigir valor$"), corrigir_valor))


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"


@app.route('/')
def index():
    return "Bot de comprovantes ativo!"


if __name__ == '__main__':
    registrar_handlers()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))