import os
import re
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from processador import processar_mensagem

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002122662652
WEBHOOK_URL = "https://comprovante-guimicell-bot-vmvr.onrender.com"

# Inicializa Flask e Telegram Application
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot de comprovantes ativo!")

# Handler de mensagens
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await processar_mensagem(update, context)

# Registra comandos e mensagens
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.ALL, handle_message))

# Webhook do Telegram envia POST para cá
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "OK", 200

# Inicia o app Flask e configura o webhook apenas 1 vez
if __name__ == "__main__":
    async def iniciar():
        print("⚙️ Configurando webhook...")
        await application.bot.set_webhook(WEBHOOK_URL)
        print("✅ Webhook configurado com sucesso!")
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

    asyncio.run(iniciar())
