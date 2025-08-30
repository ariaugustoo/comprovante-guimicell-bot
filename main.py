import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem

# Configurações
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Inicializa o bot e o Flask
app = Flask(__name__)
bot = Bot(token=TOKEN)

# Configura logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Dispatcher para gerenciar mensagens
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# Função principal para processar cada mensagem recebida
def handle_message(update: Update, context):
    if update.message and update.message.chat.id == GROUP_ID:
        resposta = processar_mensagem(update.message.text, update.message.from_user.id)
        if resposta:
            context.bot.send_message(chat_id=GROUP_ID, text=resposta, parse_mode='Markdown')

# Adiciona o handler ao dispatcher
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Rota principal do webhook
@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok", 200

# Inicializa o app no Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))