import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from utils.processador import (
    processar_comprovante,
    salvar_comprovante_manual,
    marcar_comprovante_pago,
    calcular_total_pendente,
    listar_comprovantes,
    get_ultimo_comprovante,
    calcular_total_geral
)

# ====================== CONFIGURAÇÃO ======================
TOKEN = "8363714673:AAESwB7dBANTBXxM69CZenp8Rn0e8F5aXdM"  # ⚠️ Substitua por variável de ambiente em produção
logging.basicConfig(level=logging.INFO)
# ==========================================================


# ===================== COMANDOS ===========================

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🧾 *Comandos disponíveis:*\n\n"
        "• Envie o *valor* + *'pix'* → para pagamento via PIX\n"
        "  Ex: `2.345,99 pix`\n"
        "• Envie o *valor* + *'10x'* → para cartão parcelado\n"
        "  Ex: `1.250,00 6x`\n"
        "• Envie ✅ → para marcar o último como pago\n\n"
        "• `/total` ou `/quanto_falta` → total a pagar\n"
        "• `/listar_pendentes` → lista dos pendentes\n"
        "• `/listar_pagos` → lista dos pagos\n"
        "• `/ultimo` → mostra o último comprovante\n"
        "• `/total_geral` → pagos + pendentes\n"
        "• `/ajuda` → mostra os comandos\n"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def comando_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = calcular_total_pendente()
    await update.message.reply_text(f"💰 *Total em aberto:* R$ {total:.2f}", parse_mode="Markdown")


async def comando_listar_pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = listar_comprovantes(pagos=False)
    await update.message.reply_text(mensagem, parse_mode="Markdown")


async def comando_listar_pagos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = listar_comprovantes(pagos=True)
    await update.message.reply_text(mensagem, parse_mode="Markdown")


async def comando_ultimo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = get_ultimo_comprovante()
    await update.message.reply_text(mensagem, parse_mode="Markdown")


async def comando_total_geral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = calcular_total_geral()
    await update.message.reply_text(f"📊 *Total geral:* R$ {total:.2f}", parse_mode="Markdown")


# ===================== MENSAGENS ===========================

async def receber_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    texto = update.message.text

    if not texto:
        return

    # ✅ Marcar como pago
    if texto.strip() == "✅":
        resposta = marcar_comprovante_pago()
        await update.message.reply_text(resposta, parse_mode="Markdown")
        return

    # Processa comando de valor
    resposta = salvar_comprovante_manual(texto, user.first_name)
    await update.message.reply_text(resposta, parse_mode="Markdown")


# ===================== MAIN ================================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("total", comando_total))
    app.add_handler(CommandHandler("quanto_falta", comando_total))
    app.add_handler(CommandHandler("oquedevo", comando_total))
    app.add_handler(CommandHandler("listar_pendentes", comando_listar_pendentes))
    app.add_handler(CommandHandler("listar_pagos", comando_listar_pagos))
    app.add_handler(CommandHandler("ultimo", comando_ultimo))
    app.add_handler(CommandHandler("total_geral", comando_total_geral))

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), receber_mensagem))

    print("🤖 Bot rodando...")
    app.run_polling()


if __name__ == "__main__":
    main()
