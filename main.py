from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher
from dotenv import load_dotenv
import os
import processador

# Carregar variáveis de ambiente
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0, use_context=True)

# Registrar os handlers
processador.registrar_handlers(dispatcher, GROUP_ID, ADMIN_ID)

@app.route('/', methods=['GET'])
def index():
    return 'Bot está online ✅'

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

if __name__ == '__main__':
    app.run(port=10000)
