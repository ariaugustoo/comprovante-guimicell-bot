import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from processador import processar_comprovante

# Substitua pelo seu token real
TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"

# Ative o log para debug
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Função que será chamada quando uma imagem ou PDF for recebida
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        await processar_comprovante(update, context, tipo="foto")
    elif update.message.document:
        await processar_comprovante(update, context, tipo="documento")
    else:
        await update.message.reply_text("Por favor, envie um comprovante em PDF ou uma imagem.")

# Inicializa o bot
def main():
    app = Application.builder().token(TOKEN).build()

    # Recebe imagens
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))

    # Recebe PDFs (documentos)
    app.add_handler(MessageHandler(filters.Document.PDF, handle_message))

    # Inicia o polling
    print("Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
