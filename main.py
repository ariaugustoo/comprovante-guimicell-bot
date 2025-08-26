from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, Dispatcher
from processador import configurar_handlers
import asyncio

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"

bot = Bot(token=TOKEN)
app = Flask(__name__)

application = Application.builder().token(TOKEN).build()
configurar_handlers(application)

@app.route('/')
def home():
    return '🤖 Bot Comprovantes Guimicell Ativo!', 200

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return 'ok', 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
