import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from processador import processar_mensagem

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8293056690:AAFYCum41SJeY00KUU988BPukgTe7qkZ-SQ")
PORT = int(os.environ.get('PORT', 8443))

def responder(update, context):
    texto = update.message.text
    user_id = update.message.from_user.id
    chat_type = update.message.chat.type

    resposta = processar_mensagem(texto, user_id)

    # Só responde "comando não reconhecido" no privado
    if resposta:
        if resposta.strip().startswith("🤖") or resposta.strip().startswith("📈") or "*" in resposta or "`" in resposta:
            update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text(resposta)
    else:
        if chat_type == "private":
            update.message.reply_text("❓ Comando não reconhecido. Envie 'ajuda' para ver os comandos disponíveis.")
        # No grupo, não responde nada se não reconhecer o comando

def start(update, context):
    update.message.reply_text("Olá! O bot está funcionando. Envie 'ajuda' para ver os comandos disponíveis.")

def ajuda(update, context):
    user_id = update.message.from_user.id
    resposta = processar_mensagem("ajuda", user_id)
    update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('ajuda', ajuda))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, responder))

    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"https://comprovante-guimicell-bot-1-63q2.onrender.com/{TELEGRAM_TOKEN}"
    )
    updater.idle()

if __name__ == '__main__':
    main()
