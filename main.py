import os
import aiohttp
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from utils.processador import processar_comprovante

# Configuração do log
logging.basicConfig(level=logging.INFO)

TOKEN = '8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA'

# Baixar imagem ou PDF
async def baixar_arquivo(file_id, bot):
    file = await bot.get_file(file_id)
    caminho = f"/tmp/{file_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(file.file_path) as resp:
            with open(caminho, 'wb') as f:
                f.write(await resp.read())
    return caminho

# Quando recebe comprovante
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tipo = None
    file_id = None

    if update.message.document:
        tipo = "documento"
        file_id = update.message.document.file_id
    elif update.message.photo:
        tipo = "foto"
        file_id = update.message.photo[-1].file_id

    if not file_id:
        await update.message.reply_text("❌ Nenhum comprovante válido detectado.")
        return

    caminho = await baixar_arquivo(file_id, context.bot)
    resultado = processar_comprovante(caminho)
    os.remove(caminho)

    if "erro" in resultado:
        await update.message.reply_text(f"❌ Erro: {resultado['erro']}")
    else:
        await update.message.reply_text(
            f"""✅ Comprovante processado com sucesso:

💰 Valor bruto: R$ {resultado['valor_bruto']:.2f}
📆 Parcelas: {resultado['parcelas']}x
⏰ Hora: {resultado['hora']}
📉 Taxa aplicada: {resultado['taxa_aplicada']*100:.2f}%
💸 Valor líquido a repassar: R$ {resultado['valor_liquido']:.2f}"""
        )

# Inicializa o bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_message))
    print("✅ BOT RODANDO...")
    app.run_polling()
