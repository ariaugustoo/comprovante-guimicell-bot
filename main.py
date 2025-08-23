import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from utils.processador import (
    processar_comprovante,
    salvar_comprovante_manual,
    marcar_comprovante_pago,
    calcular_total_pendente,
    listar_comprovantes,
    get_ultimo_comprovante,
    calcular_total_geral
)

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002626449000  # Substitua com seu grupo real

comprovantes = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot de comprovantes ativo!")

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comandos = """
📋 *Comandos disponíveis:*
1️⃣ `152.90 pix` → Registra comprovante PIX
2️⃣ `152.90 3x` → Registra comprovante cartão 3x
3️⃣ ✅ → Marca o último comprovante como *pago*
4️⃣ `total que devo` ou `/oquedevo` ou `/quantofalta` → Mostra o total em aberto
5️⃣ `listar pendentes` → Lista comprovantes em aberto
6️⃣ `listar pagos` → Lista comprovantes pagos
7️⃣ `último comprovante` → Mostra o último comprovante registrado
8️⃣ `total geral` → Mostra o total geral de todos os comprovantes
"""
    await update.message.reply_text(comandos, parse_mode="Markdown")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arquivo = update.message.document
    if not arquivo:
        return await update.message.reply_text("❌ Nenhum documento encontrado.")
    
    caminho = await arquivo.get_file()
    caminho_local = f"/tmp/{arquivo.file_name}"
    await caminho.download_to_drive(caminho_local)

    resposta = processar_comprovante(caminho_local)
    await update.message.reply_text(resposta, parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    foto = update.message.photo[-1]
    caminho = await foto.get_file()
    caminho_local = f"/tmp/{foto.file_id}.jpg"
    await caminho.download_to_drive(caminho_local)

    resposta = processar_comprovante(caminho_local)
    await update.message.reply_text(resposta, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()

    if texto.startswith("✅"):
        resposta = marcar_comprovante_pago()
    elif texto.lower() in ["total que devo", "/oquedevo", "/quantofalta"]:
        resposta = calcular_total_pendente()
    elif texto.lower() == "listar pendentes":
        resposta = listar_comprovantes(pagos=False)
    elif texto.lower() == "listar pagos":
        resposta = listar_comprovantes(pagos=True)
    elif texto.lower() == "último comprovante":
        resposta = get_ultimo_comprovante()
    elif texto.lower() == "total geral":
        resposta = calcular_total_geral()
    elif texto.lower() in ["ajuda", "/ajuda"]:
        return await ajuda(update, context)
    else:
        resposta = salvar_comprovante_manual(texto)

    await update.message.reply_text(resposta, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    print("✅ Bot está rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
