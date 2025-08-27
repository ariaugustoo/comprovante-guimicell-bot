import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

def processar(update, context):
    mensagem = update.message.text
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    processar_mensagem(mensagem, bot, chat_id, user_id)

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar))

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot rodando com webhook!'

if __name__ == '__main__':
    app.run()
