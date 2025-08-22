from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import logging

from utils.processador import processar_comprovante  # Certifique-se de que essa função está funcionando

# Configurações de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = '8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA'  # Substitua se necessário

# Handler principal
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.document:
        await processar_comprovante(update, context)

# Inicialização do app
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))

    print("Bot online e funcionando!")
    app.run_polling()
