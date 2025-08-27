import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from dotenv import load_dotenv
from processador import processar_mensagem

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN)

app = Flask(__name__)

dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

def handle_message(update, context):
    message = update.message
    if message.chat.id == GROUP_ID:
        resposta = processar_mensagem(message)
        if resposta:
            context.bot.send_message(chat_id=GROUP_ID, text=resposta)

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "ok", 200

@app.route('/', methods=['GET'])
def index():
    return "Bot de Comprovantes ativo", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Corrigido para uso no Render
    app.run(host='0.0.0.0', port=port)
