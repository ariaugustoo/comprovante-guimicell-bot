import os
from telegram.ext import Updater, MessageHandler, Filters
from processador import processar_mensagem

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "8443"))

# Lista de palavras-chave que ativam o bot (ajuste conforme seus comandos)
PALAVRAS_ATIVADORAS = ["pix", "solicito", "ajuda", "comprovante", "saldo", "enviar", "fechamento"]

def mensagem_parece_comando(texto):
    texto = texto.lower().strip()
    # Checa se começa com alguma palavra-chave
    for palavra in PALAVRAS_ATIVADORAS:
        if texto.startswith(palavra):
            return True
    # Checa se está mencionando o bot (exemplo: @comprovante_dbh_novo), ajuste se quiser
    # if "@comprovante_dbh_novo" in texto:
    #     return True
    return False

def responder(update, context):
    usuario_id = update.effective_user.id
    texto = update.message.text or ""

    # Só responde se for um comando plausível ou mensagem privada
    if update.message.chat.type == "private" or mensagem_parece_comando(texto):
        resposta = processar_mensagem(texto, usuario_id)
        if not resposta:
            resposta = "❓ Comando não reconhecido. Envie 'ajuda' para ver os comandos disponíveis."
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode="Markdown")
    # Se não for comando, não faz nada (não responde)

def error_handler(update, context):
    print(f"Exception: {context.error}")

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, responder))
    dispatcher.add_error_handler(error_handler)

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
