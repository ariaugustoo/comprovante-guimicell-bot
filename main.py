import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    marcar_como_pago,
    quanto_devo,
    total_a_pagar,
    iniciar_solicitacao_pagamento,
    registrar_pagamento_solicitado
)

# Carrega variáveis do ambiente
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# Inicializa bot e dispatcher
bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, use_context=True)

# Comandos
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Bot de comprovantes ativado ✅")

def comando_pagamento_feito(update, context):
    if update.effective_chat.id != GROUP_ID:
        return
    usuario_id = update.effective_user.id
    marcar_como_pago(usuario_id)

def comando_quanto_devo(update, context):
    if update.effective_chat.id != GROUP_ID:
        return
    quanto_devo()

def comando_total_a_pagar(update, context):
    if update.effective_chat.id != GROUP_ID:
        return
    total_a_pagar()

def comando_solicitar_pagamento(update, context):
    if update.effective_chat.id != GROUP_ID:
        return
    iniciar_solicitacao_pagamento(update.effective_user.id)

def mensagem(update, context):
    if update.effective_chat.id != GROUP_ID:
        return
    processar_mensagem(update)

# Registrar comandos e mensagens
def registrar_handlers():
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^pagamento feito$"), comando_pagamento_feito))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^quanto devo$"), comando_quanto_devo))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^total a pagar$"), comando_total_a_pagar))
    dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^solicitar pagamento$"), comando_solicitar_pagamento))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, mensagem))

registrar_handlers()

# Rota do webhook
@app.route('/webhook', methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

# Iniciar app com host 0.0.0.0 e porta correta
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
