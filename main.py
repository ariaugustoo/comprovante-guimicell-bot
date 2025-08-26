import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from processador import processar_mensagem
import os

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002626449000
WEBHOOK_URL = "https://comprovante-guimicell-bot-vmvr.onrender.com"

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Inicializar Flask
app = Flask(__name__)

# Inicializar bot
bot = Bot(token=TOKEN)

# Inicializar aplicação do Telegram
bot_app = ApplicationBuilder().token(TOKEN).build()

# Handler de mensagens
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await processar_mensagem(update.message, context.bot)

bot_app.add_handler(MessageHandler(filters.ALL, handle))

@app.route("/")
def index():
    return "Bot ativo com webhook!", 200

@app.route(f"/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    bot_app.update_queue.put(update)
    return "ok", 200

async def setup_webhook():
    await bot.delete_webhook()
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
