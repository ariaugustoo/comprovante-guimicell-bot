import logging
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    CommandHandler,
)
from utils.processador import (
    processar_comprovante,
    salvar_comprovante_manual,
    enviar_total_a_pagar,
    marcar_como_pago,
)

import asyncio
import os

# Configurações
BOT_TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002626449000

# Logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Mensagem de boas-vindas
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot de leitura de comprovantes iniciado com sucesso!")

# Captura de imagens e documentos
async def receber_arquivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        await processar_comprovante(update, context, "foto")
    elif update.message.document:
        await processar_comprovante(update, context, "documento")
    elif update.message.text:
        await salvar_comprovante_manual(update, context)

# Handler para marcar comprovantes pagos
async def verificar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await marcar_como_pago(update, context)

# Tratamento de erros
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Erro detectado: {context.error}")
    if update and hasattr(update, 'effective_message') and update.effective_message:
        await update.effective_message.reply_text("⚠️ Ocorreu um erro. Verifique o conteúdo do comprovante.")

# Agendamento do total a cada hora
async def agendar_envio_total(application):
    while True:
        await enviar_total_a_pagar(application)
        await asyncio.sleep(3600)  # 1 hora

# Inicializador
async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), receber_arquivo))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("✅"), verificar_pagamento))

    # Tratamento de erro
    application.add_error_handler(error_handler)

    # Iniciar agendamento em paralelo
    application.job_queue.run_once(lambda context: asyncio.create_task(agendar_envio_total(application)), when=5)

    print("Bot rodando...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
