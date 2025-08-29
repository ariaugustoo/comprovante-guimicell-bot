import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)
bot = Bot(token=TOKEN)

dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

def verificar_autorizacao(update):
    chat_id = update.effective_chat.id
    return chat_id == GROUP_ID

def handle_message(update, context):
    if verificar_autorizacao(update):
        processar_mensagem(update)

# Registrar o handler de mensagens
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

@app.route("/")
def index():
    return "Bot de comprovantes está ativo!"

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "OK"
    if __name__ == "__main__":
    # Ativando log para debugging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    
    # Inicia o servidor Flask na porta esperada pelo Render
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
