from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import re

def calcular_valor_liquido(valor, tipo_pagamento, parcelas=1):
    # Tabela de taxas de crédito por número de parcelas
    taxas_cartao = {
        1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
        7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
        13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
    }

    if tipo_pagamento == "pix":
        taxa = 0.2
    elif tipo_pagamento == "cartao" and parcelas in taxas_cartao:
        taxa = taxas_cartao[parcelas]
    else:
        taxa = 0

    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def responder_comprovante(update, context):
    texto = update.message.text.lower()
    chat_id = update.message.chat_id

    # PIX
    if "pix" in texto:
        match = re.search(r"([\d.,]+)", texto)
        if match:
            valor = float(match.group(1).replace('.', '').replace(',', '.'))
            liquido, taxa = calcular_valor_liquido(valor, "pix")
            msg = (
                f"📄 *Comprovante analisado:*\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💳 Tipo: PIX\n"
                f"📉 Taxa aplicada: {taxa}%\n"
                f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
            )
            context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

    # CARTÃO com parcelas
    elif "x" in texto:
        match = re.search(r"([\d.,]+)[^\d]*(\d{1,2})x", texto)
        if match:
            valor = float(match.group(1).replace('.', '').replace(',', '.'))
            parcelas = int(match.group(2))
            liquido, taxa = calcular_valor_liquido(valor, "cartao", parcelas)
            msg = (
                f"📄 *Comprovante analisado:*\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💳 Parcelas: {parcelas}x\n"
                f"📉 Taxa aplicada: {taxa}%\n"
                f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
            )
            context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

def comando_ajuda(update, context):
    msg = (
        "📌 *Comandos disponíveis:*\n"
        "• Envie `6.500,00 pix` para calcular valor líquido com taxa de 0.2%\n"
        "• Envie `8.000,00 12x` para calcular com taxa de cartão (12x = 12.52%)\n"
        "• Envie ✅ após pagar para marcar como pago\n"
        "• Envie `total que devo` para ver o total de comprovantes pendentes"
    )
    update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

def registrar_handlers(dispatcher, GROUP_ID, ADMIN_ID):
    dispatcher.add_handler(CommandHandler("ajuda", comando_ajuda))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, responder_comprovante))
