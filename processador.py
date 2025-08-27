import re
from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime
import pytz

# Armazenamento de comprovantes
comprovantes = []
timezone = pytz.timezone('America/Sao_Paulo')

# Regex para detectar valores (com vírgula ou ponto)
def extrair_valor(texto):
    padrao = r"(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})"
    correspondencias = re.findall(padrao, texto)
    if correspondencias:
        valor_str = correspondencias[0].replace('.', '').replace(',', '.')
        return float(valor_str)
    return None

# Regex para parcelas tipo 10x, 12x
def extrair_parcelas(texto):
    match = re.search(r"(\d{1,2})x", texto.lower())
    if match:
        return int(match.group(1))
    return None

# Tabela de taxas
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19,
    15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}
taxa_pix = 0.2  # %

# ------------------------ Funções ------------------------ #

def calcular_liquido(valor, parcelas=None):
    if parcelas:
        taxa = taxas_cartao.get(parcelas, 0)
    else:
        taxa = taxa_pix
    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace('.', 'v').replace(',', '.').replace('v', ',')

def processar_mensagem(update: Update, context: CallbackContext):
    texto = update.message.text or ""
    user = update.effective_user
    parcelas = extrair_parcelas(texto)
    valor = extrair_valor(texto)

    if "pix" in texto.lower():
        tipo = "PIX"
        taxa = taxa_pix
    elif parcelas:
        tipo = "Cartão"
        taxa = taxas_cartao.get(parcelas, 0)
    else:
        update.message.reply_text("❗ Envie um valor seguido de 'pix' ou número de parcelas, ex:\n`1438,90 pix`\n`7432,90 12x`")
        return

    if valor:
        liquido, taxa_usada = calcular_liquido(valor, parcelas)
        horario = datetime.now(timezone).strftime("%H:%M")
        comprovante = {
            "valor": valor,
            "parcelas": parcelas,
            "tipo": tipo,
            "taxa": taxa_usada,
            "liquido": liquido,
            "hora": horario,
            "pago": False,
            "user": user.first_name or "Lojista"
        }
        comprovantes.append(comprovante)

        resposta = (
            "📄 *Comprovante analisado:*\n"
            f"💰 Valor bruto: {formatar_reais(valor)}\n"
            f"💳 Parcelas: {parcelas if parcelas else '-'}\n"
            f"⏰ Horário: {horario}\n"
            f"📉 Taxa aplicada: {taxa_usada}%\n"
            f"✅ Valor líquido a pagar: *{formatar_reais(liquido)}*"
        )
        update.message.reply_markdown(resposta)
    elif "✅" in texto:
        marcar_como_pago(update, context)

def marcar_como_pago(update: Update, context: CallbackContext):
    for c in reversed(comprovantes):
        if not c.get("pago"):
            c["pago"] = True
            update.message.reply_text("✅ Último comprovante marcado como *pago*.")
            return
    update.message.reply_text("⚠️ Nenhum comprovante pendente para marcar como pago.")

def listar_pendentes(update: Update, context: CallbackContext):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        update.message.reply_text("📭 Nenhum comprovante pendente.")
        return
    texto = "📌 *Pendentes:*\n"
    for i, c in enumerate(pendentes, 1):
        texto += f"{i}. {formatar_reais(c['valor'])} → {formatar_reais(c['liquido'])} ({c['tipo']} - {c['parcelas'] or 'pix'}x)\n"
    update.message.reply_markdown(texto)

def listar_pagos(update: Update, context: CallbackContext):
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        update.message.reply_text("📭 Nenhum comprovante marcado como pago.")
        return
    texto = "🟢 *Pagos:*\n"
    for i, c in enumerate(pagos, 1):
        texto += f"{i}. {formatar_reais(c['valor'])} → {formatar_reais(c['liquido'])} ({c['tipo']})\n"
    update.message.reply_markdown(texto)

def exibir_ajuda(update: Update, context: CallbackContext):
    comandos = """
🤖 *Comandos disponíveis:*

➡️ `1432,50 pix` — Registra com taxa de PIX
➡️ `7432,99 12x` — Registra com taxa do cartão
➡️ ✅ — Marca último comprovante como pago

📊 `/totalquedevo` — Total em aberto
📋 `/listarpendentes` — Lista pendentes
✅ `/listarpagos` — Lista pagos
📌 `/ultimo` ou `último` — Último comprovante
📈 `/totalgeral` — Total geral

🔒 `/limpartudo` — Apaga todos (admin)
🔒 `/corrigirvalor` — Corrige último valor (admin)
"""
    update.message.reply_markdown(comandos)

def ultimo_comprovante(update: Update, context: CallbackContext):
    if not comprovantes:
        update.message.reply_text("⚠️ Nenhum comprovante ainda.")
        return
    c = comprovantes[-1]
    status = "✅ Pago" if c["pago"] else "⏳ Pendente"
    texto = (
        f"{status}\n💰 {formatar_reais(c['valor'])}\n"
        f"📉 {c['taxa']}% → {formatar_reais(c['liquido'])}\n"
        f"💳 {c['parcelas'] or 'PIX'}x\n"
        f"⏰ {c['hora']}"
    )
    update.message.reply_text(texto)

def total_pendente(update: Update, context: CallbackContext):
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    update.message.reply_text(f"💰 Total pendente: *{formatar_reais(total)}*", parse_mode="Markdown")

def total_geral(update: Update, context: CallbackContext):
    total = sum(c["liquido"] for c in comprovantes)
    update.message.reply_text(f"📊 Total geral: *{formatar_reais(total)}*", parse_mode="Markdown")

def limpar_tudo(update: Update, context: CallbackContext):
    comprovantes.clear()
    update.message.reply_text("🗑️ Todos os comprovantes foram apagados.")

def corrigir_valor(update: Update, context: CallbackContext):
    texto = update.message.text
    novo_valor = extrair_valor(texto)
    if not novo_valor:
        update.message.reply_text("❗ Envie o valor corrigido no formato: `/corrigirvalor 1432,90`")
        return
    for c in reversed(comprovantes):
        if not c["pago"]:
            parcelas = c.get("parcelas")
            c["valor"] = novo_valor
            c["liquido"], c["taxa"] = calcular_liquido(novo_valor, parcelas)
            update.message.reply_text(f"✅ Valor corrigido: {formatar_reais(novo_valor)} → {formatar_reais(c['liquido'])}")
            return
    update.message.reply_text("⚠️ Nenhum comprovante pendente para corrigir.")
