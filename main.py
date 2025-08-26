from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder
from processador import configurar_handlers
import asyncio
import os

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
WEBHOOK_URL = "https://comprovante-guimicell-bot-vmvr.onrender.com/webhook"

app = Flask(__name__)
bot_app = None

@app.route('/')
def home():
    return 'Bot está rodando com webhook!'

@app.route('/webhook', methods=['POST'])
async def webhook():
    if request.method == "POST":
        data = request.get_json(force=True)
        update = Update.de_json(data, bot_app.bot)
        await bot_app.update_queue.put(update)
    return 'ok'

async def main():
    global bot_app
    bot_app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    configurar_handlers(bot_app)
    await bot_app.bot.delete_webhook()
    await bot_app.bot.set_webhook(WEBHOOK_URL)
    print("Webhook configurado com sucesso!")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await bot_app.idle()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
