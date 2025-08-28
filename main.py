import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from processador import (
    processar_mensagem,
    listar_pendentes,
    listar_pagos,
    total_liquido,
    total_a_pagar,
    solicitar_pagamento,
    marcar_como_pago,
    ajuda_comandos
)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = os.environ.get("GROUP_ID")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = Bot(token=TOKEN)

app = Flask(__name__)
dispatcher = Dispatcher(bot, None, use_context=True)


def start(update, context):
    update.message.reply_text("✅ Bot ativo e funcionando!")


def ajuda(update, context):
    comandos = ajuda_comandos()
    context.bot.send_message(chat_id=update.effective_chat.id, text=comandos, parse_mode='Markdown')


def handle_message(update, context):
    texto = update.message.text.lower()

    if "pix" in texto or "x" in texto:
        resposta = processar_mensagem(texto)
        if resposta:
            context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode='Markdown')
    elif texto == "pagamento feito":
        resposta = marcar_como_pago()
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
    elif texto == "solicitar pagamento":
        context.bot.send_message(chat_id=update.effective_chat.id, text="Digite o valor para solicitar:")
    elif texto.replace(",", "").replace(".", "").isdigit():
        resposta = solicitar_pagamento(texto)
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode='Markdown')
    elif texto == "listar pendentes":
        resposta = listar_pendentes()
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode='Markdown')
    elif texto == "listar pagos":
        resposta = listar_pagos()
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode='Markdown')
    elif texto == "total líquido":
        resposta = total_liquido()
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
    elif texto == "total a pagar":
        resposta = total_a_pagar()
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
    elif texto == "ajuda":
        ajuda(update, context)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❓ Comando não reconhecido. Digite 'ajuda' para ver os comandos.")


dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))


@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok", 200


@app.route("/")
def home():
    return "🤖 Bot de Comprovantes Online", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
