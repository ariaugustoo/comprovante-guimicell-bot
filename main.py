import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from processador import processar_mensagem, calcular_total, marcar_como_pago, listar_pendentes, listar_pagos, mostrar_ultimo, total_geral

TOKEN = "8293056690:AAEYab0kMkXvnCR8A3Su4bn4j3uV6WMmcrk"
GROUP_ID = -1003089523643
WEBHOOK_URL = "https://comprovante-guimicell-bot-vmvr.onrender.com"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot de comprovantes ativo e funcionando!")

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comandos = """
📄 *Comandos disponíveis*:

1️⃣ Envie uma imagem ou PDF de comprovante para análise automática.

2️⃣ Ou envie no formato manual:
• `1549,99 pix`
• `7399.90 10x`

✅ `✅` – marca último comprovante como pago
📊 `total que devo` – mostra valor pendente
📋 `listar pendentes` – lista todos não pagos
📗 `listar pagos` – lista os pagos
🔁 `último comprovante` – mostra o último recebido
💰 `total geral` – soma total de todos
❓ `ajuda` – mostra esse menu

_Todas as mensagens devem ser enviadas no grupo oficial._
"""
    await update.message.reply_text(comandos, parse_mode='Markdown')

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = await processar_mensagem(update)
    if response:
        await update.message.reply_text(response)

async def comando_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resposta = marcar_como_pago()
    await update.message.reply_text(resposta)

async def comando_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resposta = calcular_total()
    await update.message.reply_text(resposta)

async def comando_pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resposta = listar_pendentes()
    await update.message.reply_text(resposta)

async def comando_pagos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resposta = listar_pagos()
    await update.message.reply_text(resposta)

async def comando_ultimo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resposta = mostrar_ultimo()
    await update.message.reply_text(resposta)

async def comando_total_geral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resposta = total_geral()
    await update.message.reply_text(resposta)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^✅$"), comando_pago))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^total que devo$"), comando_total))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^listar pendentes$"), comando_pendentes))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^listar pagos$"), comando_pagos))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^último comprovante$"), comando_ultimo))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^total geral$"), comando_total_geral))
    app.add_handler(MessageHandler(filters.ALL, handle))

    # Webhook no Render
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

if __name__ == "__main__":
    main()
