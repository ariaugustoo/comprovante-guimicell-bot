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

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

def responder(update, context):
    mensagem = update.message.text.lower()

    if mensagem == "pagamento feito":
        resposta = marcar_como_pago(update.effective_user.id)
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
    elif mensagem == "quanto devo":
        resposta = f"💰 Devo ao lojista: R$ {quanto_devo():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
    elif mensagem == "total a pagar":
        resposta = f"💰 Total bruto pendente: R$ {total_a_pagar():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
    elif mensagem == "solicitar pagamento":
        iniciar_solicitacao_pagamento(update.effective_user.id)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Digite o valor a ser solicitado (ex: 300,00):")
    elif mensagem.replace(",", ".").replace(".", "").isdigit():  # Captura valor digitado
        resposta = registrar_pagamento_solicitado(update.effective_user.id, mensagem)
        if resposta:
            context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
        else:
            processar_mensagem(update)
    else:
        processar_mensagem(update)

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, responder))

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"
