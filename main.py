import logging
from flask import Flask, request
import telegram
import os
from processador import processar_mensagem
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message:
        processar_mensagem(update.message, bot, GROUP_ID)
    return 'ok'

@app.route('/')
def index():
    return 'Bot rodando com sucesso!'

if __name__ == '__main__':
    app.run()
