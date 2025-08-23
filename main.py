import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from utils.processador import processar_comprovante

# === CONFIGURAÇÕES ===
TOKEN = '8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA'  # Seu token do bot
GROUP_ID = -1008126124610  # ID do grupo onde o bot irá responder

# === LOGS ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === MANIPULA MENSAGENS ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Se for uma imagem
    if update.message.photo:
        await processar_comprovante(update, context, GROUP_ID)
    
    # Se for uma resposta com valor manual
    elif update.message.text and update.message.reply_to_message:
        await processar_comprovante(update, context, GROUP_ID, valor_manual=update.message.text)

# === INÍCIO DO BOT ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    print("🤖 Bot rodando com sucesso!")
    app.run_polling()
