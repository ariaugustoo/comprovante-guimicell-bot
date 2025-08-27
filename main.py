import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)

app = Flask(__name__)

dispatcher = Dispatcher(bot, None, use_context=True)

def responder(update, context):
    mensagem = update.message.text
    user_id = update.message.from_user.id
    resposta = processar_mensagem(mensagem, user_id=user_id)
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), responder))

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot ativo'

def enviar_resumo():
    from processador import total_pendentes
    bot.send_message(chat_id=GROUP_ID, text=total_pendentes())

# Scheduler para enviar resumo a cada hora
scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
scheduler.add_job(enviar_resumo, 'cron', minute=0)
scheduler.start()

if __name__ == '__main__':
    app.run(port=5000)
