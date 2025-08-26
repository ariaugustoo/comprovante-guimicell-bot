import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, filters, CommandHandler
from processador import processar_mensagem, listar_pendentes, listar_pagos, total_geral, total_que_devo, ultimo_comprovante
from telegram.constants import ParseMode
import logging

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg80IA"
GROUP_ID = -1002122662652

bot = Bot(token=TOKEN)

app = Flask(__name__)

# Logging (opcional)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4)

# Comandos
def start(update, context):
    update.message.reply_text("🤖 Bot de comprovantes ativo e funcionando!")

def ping(update, context):
    update.message.reply_text("🏓 Pong!")

def ajuda(update, context):
    comandos = """
📋 *Comandos disponíveis:*

✅ Marcar pagamento:
`✅`

📤 Enviar comprovante:
`6500,00 Pix` ou `6500,00 3x`

💬 Consultar:
• `total que devo`
• `listar pendentes`
• `listar pagos`
• `total geral`
• `último comprovante`
    """
    update.message.reply_text(comandos, parse_mode=ParseMode.MARKDOWN)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("ping", ping))
dispatcher.add_handler(CommandHandler("ajuda", ajuda))

# Mensagens comuns
def handle_message(update, context):
    texto = update.message.text.strip()

    if update.message.chat_id != GROUP_ID:
        return

    if texto.lower() == "listar pendentes":
        resposta = listar_pendentes()
        update.message.reply_text(resposta)
    elif texto.lower() == "listar pagos":
        resposta = listar_pagos()
        update.message.reply_text(resposta)
    elif texto.lower() == "total geral":
        resposta = total_geral()
        update.message.reply_text(resposta)
    elif texto.lower() == "total que devo":
        resposta = total_que_devo()
        update.message.reply_text(resposta)
    elif texto.lower() == "último comprovante":
        resposta = ultimo_comprovante()
        update.message.reply_text(resposta)
    elif "✅" in texto:
        resposta = processar_mensagem("✅", True)
        update.message.reply_text(resposta)
    else:
        resposta = processar_mensagem(texto)
        if resposta:
            update.message.reply_text(resposta)

dispatcher.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

# Webhook do Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Endpoint padrão
@app.route("/", methods=["GET"])
def index():
    return "Bot de comprovantes online!"

# REGISTRAR WEBHOOK NA INICIALIZAÇÃO
def set_webhook():
    url = f"https://comprovante-guimicell-bot-vmvr.onrender.com/{TOKEN}"
    bot.set_webhook(url)
    print(f"✅ Webhook setado para: {url}")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
