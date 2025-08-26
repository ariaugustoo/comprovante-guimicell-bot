import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from processador import processar_comprovante, marcar_como_pago, total_pendentes, listar_pendentes, listar_pagos, ajuda, ultimo_comprovante, total_geral

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002626449000
WEBHOOK_URL = "https://comprovante-guimicell-bot-vmvr.onrender.com"

comprovantes = []

async def processar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != GROUP_ID:
        return

    resposta = await processar_comprovante(update, context, comprovantes)
    if resposta:
        await update.message.reply_text(resposta)

async def comando_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resposta = marcar_como_pago(comprovantes)
    await update.message.reply_text(resposta)

async def comando_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(total_pendentes(comprovantes))

async def comando_listar_pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(listar_pendentes(comprovantes))

async def comando_listar_pagos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(listar_pagos(comprovantes))

async def comando_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ajuda())

async def comando_ultimo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ultimo_comprovante(comprovantes))

async def comando_total_geral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(total_geral(comprovantes))

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL | filters.TEXT, processar))
app.add_handler(CommandHandler("pago", comando_pago))
app.add_handler(CommandHandler("totalquedevo", comando_total))
app.add_handler(CommandHandler("listarpendentes", comando_listar_pendentes))
app.add_handler(CommandHandler("listarpagos", comando_listar_pagos))
app.add_handler(CommandHandler("ajuda", comando_ajuda))
app.add_handler(CommandHandler("ultimocomprovante", comando_ultimo))
app.add_handler(CommandHandler("totalgeral", comando_total_geral))

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 10000)),
    webhook_url=f"{WEBHOOK_URL}/webhook"
)
