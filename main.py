import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, update_queue=None, use_context=True)

def handle_message(update, context):
    try:
        if update.message:
            texto = update.message.text
            chat_id = update.message.chat_id
            nome = update.message.from_user.first_name
            resposta = processar_mensagem(texto, nome, chat_id)
            if resposta:
                bot.send_message(chat_id=chat_id, text=resposta, parse_mode="Markdown")
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

@app.route('/')
def index():
    return "Bot ativo!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
