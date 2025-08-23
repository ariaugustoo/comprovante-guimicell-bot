import logging
from telegram import Update
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

# Configurações
BOT_TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002626449000  # Use seu Group ID correto

# Logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Boas-vindas
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot de leitura de comprovantes iniciado com sucesso!")

# Recebimento
async def receber_arquivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        await processar_comprovante(update, context, "foto")
    elif update.message.document:
        await processar_comprovante(update, context, "documento")
    elif update.message.text:
        await salvar_comprovante_manual(update, context)

# Marcar como pago
async def verificar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await marcar_como_pago(update, context)

# Tratamento de erro
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Erro detectado: {context.error}")
    if update and hasattr(update, 'effective_message') and update.effective_message:
        await update.effective_message.reply_text("⚠️ Ocorreu um erro. Verifique o conteúdo do comprovante.")

# Envio do total a cada hora
async def enviar_total_periodico(context: ContextTypes.DEFAULT_TYPE):
    await enviar_total_a_pagar(context.application)

# Inicializador
async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Adiciona handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), receber_arquivo))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("✅"), verificar_pagamento))
    application.add_error_handler(error_handler)

    # Inicia job queue (agendamento automático de 1 em 1 hora)
    job_queue = application.job_queue
    job_queue.run_repeating(enviar_total_periodico, interval=3600, first=10)

    print("Bot rodando...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
