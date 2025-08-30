import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import processar_mensagem
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = Bot(token=TOKEN)
app = Flask(__name__)

dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

def handle_message(update, context):
    texto = update.message.text
    user_id = update.message.from_user.id
    resposta = processar_mensagem(texto, user_id)
    if resposta:
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

@app.route('/')
def home():
    return 'Bot está no ar!'

if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)