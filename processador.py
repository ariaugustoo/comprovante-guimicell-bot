import re
from telegram import Update
from telegram.ext import ContextTypes

comprovantes = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

# Função principal
async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = update.message.text.strip()
    user = update.message.from_user.first_name

    if "pix" in mensagem.lower():
        valor_bruto = extrair_valor(mensagem)
        if valor_bruto is not None:
            taxa = 0.2
            valor_liquido = valor_bruto * (1 - taxa / 100)
            comprovantes.append({
                "valor": valor_bruto,
                "valor_liquido": valor_liquido,
                "forma": "PIX",
                "pago": False
            })
            await update.message.reply_text(
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor_bruto:,.2f}\n"
                f"📉 Taxa aplicada: {taxa}%\n"
                f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
            )
    elif "x" in mensagem.lower():
        valor_bruto = extrair_valor(mensagem)
        parcelas = extrair_parcelas(mensagem)
        if valor_bruto is not None and parcelas in taxas_cartao:
            taxa = taxas_cartao[parcelas]
            valor_liquido = valor_bruto * (1 - taxa / 100)
            comprovantes.append({
                "valor": valor_bruto,
                "valor_liquido": valor_liquido,
                "forma": f"{parcelas}x",
                "pago": False
            })
            await update.message.reply_text(
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor_bruto:,.2f}\n"
                f"💳 Parcelas: {parcelas}x\n"
                f"📉 Taxa aplicada: {taxa}%\n"
                f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
            )

# Marca o último comprovante como pago
async def marcar_como_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for comprovante in reversed(comprovantes):
        if not comprovante["pago"]:
            comprovante["pago"] = True
            await update.message.reply_text("✅ Comprovante marcado como pago.")
            return
    await update.message.reply_text("Nenhum comprovante pendente para marcar como pago.")

# Lista os comprovantes pendentes
async def listar_pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        await update.message.reply_text("✅ Nenhum pagamento pendente.")
        return
    texto = "📌 *Comprovantes Pendentes:*\n\n"
    for i, c in enumerate(pendentes, 1):
        texto += f"{i}. {c['forma']} - R$ {c['valor_liquido']:,.2f}\n"
    await update.message.reply_text(texto, parse_mode="Markdown")

# Lista os comprovantes pagos
async def listar_pagamentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        await update.message.reply_text("Nenhum pagamento foi marcado como pago ainda.")
        return
    texto = "✅ *Pagamentos Marcados:*\n\n"
    for i, c in enumerate(pagos, 1):
        texto += f"{i}. {c['forma']} - R$ {c['valor_liquido']:,.2f}\n"
    await update.message.reply_text(texto, parse_mode="Markdown")

# Calcula o total pendente
async def calcular_total_pendente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    await update.message.reply_text(f"💰 Total em aberto: R$ {total:,.2f}")

# Calcula o total geral
async def calcular_total_geral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(c["valor_liquido"] for c in comprovantes)
    await update.message.reply_text(f"📊 Total geral de repasses (pagos + pendentes): R$ {total:,.2f}")

# Retorna o último comprovante
async def ultimo_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not comprovantes:
        await update.message.reply_text("Nenhum comprovante registrado ainda.")
        return
    c = comprovantes[-1]
    status = "✅ Pago" if c["pago"] else "⏳ Pendente"
    await update.message.reply_text(
        f"📄 Último Comprovante:\n"
        f"💰 Valor bruto: R$ {c['valor']:,.2f}\n"
        f"📉 Valor líquido: R$ {c['valor_liquido']:,.2f}\n"
        f"💳 Forma: {c['forma']}\n"
        f"{status}"
    )

# Ajuda
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Comandos disponíveis:*\n\n"
        "• Envie um valor com `pix` (ex: `6438,76 pix`)\n"
        "• Envie um valor com parcelas (ex: `7.899,99 10x`)\n"
        "• ✅ — marcar o último comprovante como pago\n"
        "• listar pendentes — lista todos pendentes\n"
        "• listar pagos — lista pagos\n"
        "• total que devo — total em aberto\n"
        "• total geral — todos os repasses\n"
        "• último comprovante — ver o último\n"
        "• ajuda — exibe esta ajuda",
        parse_mode="Markdown"
    )

# Funções auxiliares
def extrair_valor(texto):
    match = re.search(r"(\d{1,3}(?:[.,]?\d{3})*(?:[.,]\d{2}))", texto)
    if match:
        valor = match.group(1).replace(".", "").replace(",", ".")
        return float(valor)
    return None

def extrair_parcelas(texto):
    match = re.search(r"(\d{1,2})x", texto.lower())
    if match:
        return int(match.group(1))
    return None
