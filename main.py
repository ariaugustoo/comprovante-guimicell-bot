import os
from telegram.ext import Updater, MessageHandler, Filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", "8443"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

def responder(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Olá, seu bot está rodando via Webhook no Render!")

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, responder))

    print("Iniciando bot usando webhook...")
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
    )
    updater.idle()

if __name__ == "__main__":
    main()
