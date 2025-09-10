import os
from telegram.ext import Updater, MessageHandler, Filters
from processador import processar_mensagem

# Carrega variáveis do ambiente do Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "8443"))

def responder(update, context):
    usuario_id = update.effective_user.id
    texto = update.message.text or ""
    resposta = processar_mensagem(texto, usuario_id)
    if not resposta:
        resposta = "❓ Comando não reconhecido. Envie 'ajuda' para ver os comandos disponíveis."
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resposta,
        parse_mode="Markdown"
    )

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Responde para qualquer mensagem de texto (exceto comandos nativos do Telegram)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, responder))

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
