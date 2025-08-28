import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

def handle_message(update, context):
    if update.effective_message:
        response = processar_mensagem(update.effective_message.text, update.effective_user.first_name)
        if response:
            context.bot.send_message(chat_id=os.getenv("GROUP_ID"), text=response, parse_mode="HTML")

dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_message))

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"
