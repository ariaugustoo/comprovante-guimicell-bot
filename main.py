import os
import telegram
from flask import Flask, request
from dotenv import load_dotenv
from processador import processar_mensagem

load_dotenv()

TOKEN = os.getenv("TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    processar_mensagem(update, bot, GROUP_ID)
    return 'ok'

@app.route('/')
def home():
    return 'Bot online!'

if __name__ == '__main__':
    app.run(debug=True)
