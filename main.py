import os
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem, listar_pendentes, listar_pagamentos, solicitar_pagamento,
    registrar_pagamento, mostrar_total_devido, mostrar_total_bruto, mostrar_status,
    mostrar_ajuda, limpar_dados, corrigir_valor
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

dispatcher = Dispatcher(bot, None, use_context=True)

# Comandos de texto
def texto_handler(update, context):
    mensagem = update.message.text.lower()
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id

    if mensagem == "listar pendentes":
        listar_pendentes(update, context)
    elif mensagem == "listar pagos":
        listar_pagamentos(update, context)
    elif mensagem == "solicitar pagamento":
        solicitar_pagamento(update, context)
    elif mensagem == "pagamento feito":
        registrar_pagamento(update, context)
    elif mensagem == "quanto devo":
        mostrar_total_devido(update, context)
    elif mensagem == "total a pagar":
        mostrar_total_bruto(update, context)
    elif mensagem in ["/status", "status", "fechamento do dia"]:
        mostrar_status(update, context)
    elif mensagem == "ajuda":
        mostrar_ajuda(update, context)
    elif mensagem == "limpar tudo" and user_id == ADMIN_ID:
        limpar_dados(update, context)
    elif mensagem == "corrigir valor" and user_id == ADMIN_ID:
        corrigir_valor(update, context)
    else:
        processar_mensagem(update, context)

dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), texto_handler))

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return 'ok'
    return 'Method Not Allowed', 405

@app.route('/')
def index():
    return 'Bot está online!'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
