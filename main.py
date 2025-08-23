import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext,
    JobQueue
)
from utils.processador import processar_comprovante, salvar_comprovante_manual
from datetime import datetime
import json
import tempfile

# Ative o log
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Variáveis de ambiente
TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1002626449000"))  # substitua pelo ID real

# Armazenamento temporário
comprovantes = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot de comprovantes iniciado!")

async def handle_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return

    file = await update.message.photo[-1].get_file()
    file_path = os.path.join(tempfile.gettempdir(), f"{file.file_id}.jpg")
    await file.download_to_drive(file_path)

    resultado = processar_comprovante(file_path, context, tipo="ocr")

    if not resultado:
        await update.message.reply_text("❌ Não consegui ler o comprovante. Por favor, envie o valor manualmente.")
        return

    comprovantes.append(resultado)

    resposta = (
        f"📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {resultado['valor_bruto']:.2f}\n"
        f"💳 Parcelas: {resultado['parcelas']}x\n"
        f"⏰ Horário: {resultado['horario']}\n"
        f"📉 Taxa aplicada: {resultado['taxa']}%\n"
        f"✅ Valor líquido a pagar: R$ {resultado['valor_liquido']:.2f}"
    )
    await update.message.reply_text(resposta, parse_mode="Markdown")

async def handle_valor_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().replace("R$", "").replace(",", ".")
    try:
        valor = float(texto)
    except ValueError:
        await update.message.reply_text("❌ Valor inválido. Envie apenas o valor, como: `152.90`")
        return

    # Salva valor manual com padrão 1x
    resultado = salvar_comprovante_manual(valor, parcelas=1, horario=None)
    comprovantes.append(resultado)

    resposta = (
        f"📄 *Comprovante manual registrado:*\n"
        f"💰 Valor bruto: R$ {resultado['valor_bruto']:.2f}\n"
        f"💳 Parcelas: {resultado['parcelas']}x\n"
        f"⏰ Horário: {resultado['horario']}\n"
        f"📉 Taxa aplicada: {resultado['taxa']}%\n"
        f"✅ Valor líquido a pagar: R$ {resultado['valor_liquido']:.2f}"
    )
    await update.message.reply_text(resposta, parse_mode="Markdown")

async def agendar_envio_total(context: CallbackContext):
    total = sum(c['valor_liquido'] for c in comprovantes if not c.get("pago", False))
    texto = f"📊 *Total a pagar (pendente):* R$ {total:.2f}"
    await context.bot.send_message(chat_id=GROUP_ID, text=texto, parse_mode="Markdown")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_imagem))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_valor_manual))

    # Agendamento automático
    job_queue: JobQueue = application.job_queue
    job_queue.run_repeating(agendar_envio_total, interval=3600, first=10)

    print("🚀 Bot rodando com sucesso...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
