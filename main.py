from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import logging
import os
import aiohttp

from utils.processador import processar_comprovante

# Configurações de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = '8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA'

async def baixar_arquivo(file_id, bot):
    file = await bot.get_file(file_id)
    caminho = f"/tmp/{file_id}"  # caminho temporário para o arquivo

    async with aiohttp.ClientSession() as session:
        async with session.get(file.file_path) as resp:
            with open(caminho, 'wb') as f:
                f.write(await resp.read())
    return caminho

# Handler principal
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document if update.message else None
    if not document:
        return

    # Baixa o arquivo do Telegram
    path = await baixar_arquivo(document.file_id, context.bot)

    # Processa o comprovante
    resultado = processar_comprovante(path)

    # Monta a resposta
    if "erro" in resultado:
        resposta = f"⚠️ {resultado['erro']}"
    else:
        resposta = (
            f"📄 *Comprovante analisado:*\n"
            f"💰 Valor bruto: R$ {resultado['valor_bruto']:.2f}\n"
            f"💳 Parcelas: {resultado['parcelas']}x\n"
            f"⏰ Horário: {resultado['hora']}\n"
            f"📉 Taxa aplicada: {resultado['taxa_aplicada'] * 100:.2f}%\n"
            f"✅ Valor líquido a pagar: *R$ {resultado['valor_liquido']:.2f}*"
        )

    # Envia no grupo
    await update.message.reply_text(resposta, parse_mode="Markdown")

    # Remove o arquivo temporário
    os.remove(path)

# Inicialização do app
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))

    print("Bot online e funcionando!")
    app.run_polling()
