import os
from telegram.ext import Updater, CommandHandler

TELEGRAM_TOKEN = "8293056690:AAFYCum41SJeY00KUU988BPukgTe7qkZ-SQ"  # Novo token

def start(update, context):
    update.message.reply_text('Olá! O bot está funcionando.')

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))

    # Para rodar com webhook (Render)
    PORT = int(os.environ.get('PORT', 8443))
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"https://comprovante-guimicell-bot-1.onrender.com/{TELEGRAM_TOKEN}"
    )
    updater.idle()

if __name__ == '__main__':
    main()
