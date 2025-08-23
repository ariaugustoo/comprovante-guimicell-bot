from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import logging
import os
import aiohttp

from utils.processador import processar_comprovante

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = '8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA'  # troque se quiser

# Função para baixar arquivo (foto ou PDF)
async def baixar_arquivo(file_id, bot):
    file = await bot.get_file(file_id)
    caminho = f"/tmp/{file_id}"  # arquivo temporário

    async with aiohttp.ClientSession() as session:
        async with session.get(file.file_path) as resp:
            with open(caminho, 'wb') as f:
                f.write(await resp.read())

    return caminho

# Função principal para tratar a mensagem
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = None

    if update.message.document:
        file_id = update.message.document.file_id
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
    else:
        return  # ignora mensagens sem documento ou foto

    # Baixar e processar
    path = await baixar_arquivo(file_id, context.bot)
    resultado = processar_comprovante(path)

    # Montar resposta
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

    await update.message.reply_text(resposta, parse_mode="Markdown")
    os.remove(path)

# Iniciar bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_message))

    print("Bot online e funcionando!")
    app.run_polling()
