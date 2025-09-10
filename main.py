import os
from telegram.ext import Updater, MessageHandler, Filters

# Carrega variáveis do ambiente (Render/Heroku)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "8443"))

def responder(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Olá! Seu bot está funcionando via webhook no Render 🚀"
    )

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Handler para todas as mensagens de texto
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, responder))

    # Inicia o webhook (endpoint: /<TELEGRAM_TOKEN>)
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
    )
    updater.idle()

if __name__ == "__main__":
    print("Iniciando bot usando webhook...")
    main()
