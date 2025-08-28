from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import os
from dotenv import load_dotenv
from processador import (
    processar_mensagem,
    marcar_como_pago,
    total_pendentes,
    total_bruto,
    registrar_pagamento_solicitado
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)
bot = Bot(token=TOKEN)

# Dispatcher com suporte a webhooks
dispatcher = Dispatcher(bot, None, workers=1)

# HANDLERS
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Bot ativo!")

def ajuda(update, context):
    comandos = (
        "📋 Comandos disponíveis:\n"
        "- Enviar valor + pix (ex: 1234,56 pix)\n"
        "- Enviar valor + parcelas (ex: 2000 6x)\n"
        "- pagamento feito ✅\n"
        "- quanto devo (valor líquido com taxas)\n"
        "- total a pagar (valor bruto)\n"
        "- solicitar pagamento"
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=comandos)

def solicitar_pagamento(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Digite o valor a solicitar:")
    return

def mensagem(update, context):
    texto = update.message.text.lower()
    if texto == "pagamento feito" and update.effective_user.id == ADMIN_ID:
        resposta = marcar_como_pago()
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
    elif "solicitar pagamento" in texto:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Digite o valor e chave pix:")
    elif "quanto devo" in texto:
        valor = total_pendentes()
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"💰 Devo ao lojista: R$ {valor:.2f}")
    elif "total a pagar" in texto:
        valor = total_bruto()
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"📦 Valor bruto total pendente: R$ {valor:.2f}")
    else:
        resposta = processar_mensagem(texto)
        if resposta:
            context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

# REGISTRO DOS HANDLERS
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), mensagem))

# FLASK ROUTES
@app.route('/')
def index():
    return "Bot do Comprovante está ativo!"

@app.route('/webhook', methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'OK'

# INICIALIZAÇÃO DO WEBHOOK
if __name__ == '__main__':
    app.run(debug=False)
