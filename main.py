import os
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from processador import processar_mensagem, is_admin, comandos_privados

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

def responder(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    texto = update.message.text.strip().lower()

    # Verifica se o comando deve ser restrito ao privado
    for cmd in comandos_privados:
        if texto.startswith(cmd):
            if update.message.chat.type != "private":
                # Se não for privado, pede para enviar no privado
                update.message.reply_text("⚠️ Este comando só pode ser usado no privado com o bot.")
                return
            resposta = processar_mensagem(texto, user_id)
            if resposta:
                update.message.reply_text(resposta)
            return

    resposta = processar_mensagem(texto, user_id)
    if resposta:
        # Se for no privado, responde no privado
        if update.message.chat.type == "private":
            update.message.reply_text(resposta)
        # Se for no grupo, responde para o grupo
        elif update.message.chat.id == GROUP_ID:
            context.bot.send_message(chat_id=GROUP_ID, text=resposta)
        # Se for outro lugar, responde no mesmo chat
        else:
            update.message.reply_text(resposta)

def main():
    use_webhook = os.getenv("USE_WEBHOOK", "false").lower() == "true"
    PORT = int(os.getenv("PORT", "8443"))
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Ex: https://seu-app.onrender.com/TELEGRAM_TOKEN

    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, responder))

    if use_webhook:
        # No Render/cloud, use webhook
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
        )
    else:
        # Local/localhost: usa polling, limpando webhook (evita conflitos)
        updater.bot.delete_webhook()
        updater.start_polling()

    updater.idle()

if __name__ == "__main__":
    main()
