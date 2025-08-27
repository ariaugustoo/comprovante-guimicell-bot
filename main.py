import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher
from processador import registrar_handlers
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=1, use_context=True)

registrar_handlers(dispatcher, GROUP_ID, ADMIN_ID)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

@app.route("/")
def index():
    return "Bot rodando com sucesso!", 200
