import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from processador import (
    processar_comprovante, listar_pendentes, listar_pagamentos, 
    calcular_total_pendente, calcular_total_geral, ultimo_comprovante, ajuda
)

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg80IA"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot do Guimicell ativo e pronto para uso!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
    app.add_handler(CommandHandler("listar_pagos", listar_pagamentos))
    app.add_handler(CommandHandler("total_que_devo", calcular_total_pendente))
    app.add_handler(CommandHandler("total_geral", calcular_total_geral))
    app.add_handler(CommandHandler("último_comprovante", ultimo_comprovante))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(MessageHandler(filters.ALL, processar_comprovante))

    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        url_path=TOKEN,
        webhook_url="https://comprovante-guimicell-bot-vmvr.onrender.com/" + TOKEN
    )

if __name__ == "__main__":
    main()
