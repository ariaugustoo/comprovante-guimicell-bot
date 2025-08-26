import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

GROUP_ID = -1002626449000
TX_PIX = 0.002

TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19,
    15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

comprovantes = []

def parse_valor(texto):
    texto = texto.replace("r$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(re.findall(r"\d+\.?\d*", texto)[0])
    except:
        return None

def calcular_taxa(valor, parcelas=None):
    if parcelas:
        taxa_pct = TAXAS_CARTAO.get(parcelas, 0) / 100
    else:
        taxa_pct = TX_PIX
    return round(valor * taxa_pct, 2)

def formatar_msg(valor, parcelas, horario, tipo, valor_liquido):
    if tipo == "pix":
        taxa_pct = TX_PIX * 100
    else:
        taxa_pct = TAXAS_CARTAO.get(parcelas, 0)

    return f"""📄 Comprovante analisado:
💰 Valor bruto: R$ {valor:,.2f}
💳 Parcelas: {parcelas if parcelas else 'PIX'}
⏰ Horário: {horario}
📉 Taxa aplicada: {taxa_pct:.2f}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"""

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower().strip()
    horario = datetime.now().strftime("%H:%M")

    if "pix" in texto:
        valor = parse_valor(texto)
        if valor:
            taxa = calcular_taxa(valor)
            valor_liquido = round(valor - taxa, 2)
            msg = formatar_msg(valor, None, horario, "pix", valor_liquido)
            comprovantes.append({"valor": valor, "parcelas": None, "horario": horario, "liquido": valor_liquido, "pago": False})
            await update.message.reply_text(msg)

    elif "x" in texto:
        match = re.search(r"([\d\.,]+)\s*(\d{1,2})x", texto)
        if match:
            valor = parse_valor(match.group(1))
            parcelas = int(match.group(2))
            taxa = calcular_taxa(valor, parcelas)
            valor_liquido = round(valor - taxa, 2)
            msg = formatar_msg(valor, parcelas, horario, "cartao", valor_liquido)
            comprovantes.append({"valor": valor, "parcelas": parcelas, "horario": horario, "liquido": valor_liquido, "pago": False})
            await update.message.reply_text(msg)

    elif texto == "✅":
        for c in reversed(comprovantes):
            if not c["pago"]:
                c["pago"] = True
                await update.message.reply_text("✅ Comprovante marcado como pago.")
                return
        await update.message.reply_text("Nenhum comprovante pendente para marcar como pago.")

    elif "total que devo" in texto:
        total = sum(c["liquido"] for c in comprovantes if not c["pago"])
        await update.message.reply_text(f"💸 Total pendente: R$ {total:,.2f}")

    elif "listar pendentes" in texto:
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            await update.message.reply_text("✅ Nenhum comprovante pendente.")
        else:
            msg = "\n\n".join([f"R$ {c['valor']:,.2f} - {c['parcelas'] if c['parcelas'] else 'PIX'} - {c['horario']}" for c in pendentes])
            await update.message.reply_text(f"📋 Pendentes:\n\n{msg}")

    elif "listar pagos" in texto:
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            await update.message.reply_text("Nenhum comprovante pago ainda.")
        else:
            msg = "\n\n".join([f"R$ {c['valor']:,.2f} - {c['parcelas'] if c['parcelas'] else 'PIX'} - {c['horario']}" for c in pagos])
            await update.message.reply_text(f"✅ Pagos:\n\n{msg}")

    elif "último comprovante" in texto:
        if comprovantes:
            c = comprovantes[-1]
            status = "✅ Pago" if c["pago"] else "⏳ Pendente"
            await update.message.reply_text(
                f"📄 Último comprovante:\nR$ {c['valor']:,.2f} - {c['parcelas'] if c['parcelas'] else 'PIX'} - {c['horario']}\nStatus: {status}")
        else:
            await update.message.reply_text("Nenhum comprovante ainda.")

    elif "total geral" in texto:
        total = sum(c["liquido"] for c in comprovantes)
        await update.message.reply_text(f"📊 Total geral (pagos + pendentes): R$ {total:,.2f}")

async def comando_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
📌 *Comandos disponíveis:*

• `6543,88 pix` → Calcula taxa de PIX (0,2%)
• `7599,99 10x` → Calcula taxa de cartão (por parcela)
• `✅` → Marca último comprovante como pago
• `total que devo` → Mostra total pendente
• `listar pendentes` → Lista comprovantes não pagos
• `listar pagos` → Lista os pagos
• `último comprovante` → Exibe o último enviado
• `total geral` → Soma tudo (pago + pendente)
""", parse_mode="Markdown")

def configurar_handlers(app):
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), processar_mensagem))
    app.add_handler(CommandHandler("ajuda", comando_ajuda))
