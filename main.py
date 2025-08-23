import logging
import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from utils.processador import processar_comprovante, salvar_comprovante_manual, marcar_comprovante_pago, calcular_total_pendente, listar_comprovantes, get_ultimo_comprovante, calcular_total_geral
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

comprovantes = []

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Comando de ajuda
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comandos = """
📋 *Comandos disponíveis*:
/ajuda - Mostra esta mensagem
✅ - Marca o último comprovante como pago
"total que devo" - Mostra o valor total pendente
"listar pendentes" - Lista todos os comprovantes não pagos
"listar pagos" - Lista os comprovantes já pagos
"último comprovante" - Mostra o último enviado
"total geral" - Total de todos (pagos + pendentes)
/o que devo - Igual ao "total que devo"
/quanto falta - Igual ao "total que devo"

*💳 Como enviar comprovantes manualmente:*
• Envie no formato: `152,90 3x` ou `152.90 3x`
• Para PIX, envie: `6438,76 pix` ou `6438.76 pix`
"""
    await update.message.reply_text(comandos, parse_mode="Markdown")

# Marcar como pago
async def marcar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if marcar_comprovante_pago(update.message.from_user.id):
        await update.message.reply_text("✅ Comprovante marcado como pago com sucesso!")
    else:
        await update.message.reply_text("❌ Nenhum comprovante encontrado para marcar como pago.")

# Mostrar total em aberto
async def total_que_devo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = calcular_total_pendente(update.message.from_user.id)
    await update.message.reply_text(f"💸 Total pendente: R$ {total:.2f}")

# Comando alternativo
quanto_falta = total_que_devo
o_que_devo = total_que_devo

# Listar pendentes
async def listar_pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = listar_comprovantes(update.message.from_user.id, pagos=False)
    await update.message.reply_text(mensagem, parse_mode="Markdown")

# Listar pagos
async def listar_pagos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = listar_comprovantes(update.message.from_user.id, pagos=True)
    await update.message.reply_text(mensagem, parse_mode="Markdown")

# Último comprovante
async def ultimo_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = get_ultimo_comprovante(update.message.from_user.id)
    await update.message.reply_text(mensagem, parse_mode="Markdown")

# Total geral
async def total_geral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = calcular_total_geral(update.message.from_user.id)
    await update.message.reply_text(f"📊 Total geral de comprovantes: R$ {total:.2f}")

# Processar imagem
async def receber_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        arquivo = await update.message.photo[-1].get_file()
        caminho = f"comprovante_{update.message.from_user.id}.jpg"
        await arquivo.download_to_drive(caminho)

        resultado = processar_comprovante(caminho, update.message.from_user.id)
        await update.message.reply_text(resultado, parse_mode="Markdown")
        os.remove(caminho)

    except Exception as e:
        await update.message.reply_text(f"Erro ao processar a imagem: {e}")

# Processar valor manual (PIX ou Cartão)
async def receber_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().lower()

    if texto in ["✅", "pago"]:
        await marcar_pago(update, context)
        return

    if texto in ["total que devo", "/total_que_devo", "/quanto_falta", "/o_que_devo"]:
        await total_que_devo(update, context)
        return

    if texto == "listar pendentes":
        await listar_pendentes(update, context)
        return

    if texto == "listar pagos":
        await listar_pagos(update, context)
        return

    if texto == "último comprovante":
        await ultimo_comprovante(update, context)
        return

    if texto == "total geral":
        await total_geral(update, context)
        return

    match_pix = re.match(r"([\d.,]+)\s*pix", texto)
    match_cartao = re.match(r"([\d.,]+)\s*(\d{1,2})x", texto)

    if match_pix:
        valor = match_pix.group(1).replace(".", "").replace(",", ".")
        resultado = salvar_comprovante_manual(valor, 1, 0.2, update.message.from_user.id)
        await update.message.reply_text(resultado, parse_mode="Markdown")

    elif match_cartao:
        valor = match_cartao.group(1).replace(".", "").replace(",", ".")
        parcelas = int(match_cartao.group(2))
        resultado = salvar_comprovante_manual(valor, parcelas, None, update.message.from_user.id)
        await update.message.reply_text(resultado, parse_mode="Markdown")

    else:
        await update.message.reply_text("❌ Valor inválido. Envie apenas o valor, como: `152,90 3x` ou `6438,76 pix`", parse_mode="Markdown")

# Inicialização
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("start", ajuda))
    app.add_handler(CommandHandler("o_que_devo", o_que_devo))
    app.add_handler(CommandHandler("quanto_falta", quanto_falta))
    app.add_handler(CommandHandler("total_que_devo", total_que_devo))
    app.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
    app.add_handler(CommandHandler("listar_pagos", listar_pagos))
    app.add_handler(CommandHandler("último_comprovante", ultimo_comprovante))
    app.add_handler(CommandHandler("total_geral", total_geral))
    app.add_handler(MessageHandler(filters.PHOTO, receber_imagem))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_texto))

    print("Bot iniciado com sucesso.")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
