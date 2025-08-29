# main.py
import os
from flask import Flask, request
import telegram
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = os.environ.get("GROUP_ID")

bot = Bot(token=TOKEN)

app = Flask(__name__)

dispatcher = Dispatcher(bot, None, use_context=True)

# Handler principal de mensagens
def handle_message(update, context):
    if update.effective_chat.id != int(GROUP_ID):
        return

    texto = update.message.text
    respostas = processar_mensagem(texto)

    for resposta in respostas:
        if resposta in ["AGUARDANDO_SOLICITACAO_VALOR", "AGUARDANDO_SOLICITACAO_PIX"]:
            continue
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode="Markdown")

# Rota principal do webhook
@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "ok"

# Registrar o handler de mensagens
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Rodar localmente (opcional para testes locais)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
