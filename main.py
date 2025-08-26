import pytesseract
from PIL import Image
import re
import io
from telegram import Update
from telegram.ext import ContextTypes
import datetime

comprovantes = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def extrair_texto(update: Update):
    if update.message.photo:
        file = update.message.effective_attachment[-1]
    else:
        file = update.message.document
    file_path = file.get_file()
    file_bytes = io.BytesIO()
    file_path.download(out=file_bytes)
    file_bytes.seek(0)
    image = Image.open(file_bytes)
    texto = pytesseract.image_to_string(image, lang='por')
    return texto

def parse_valor_e_parcelas(texto):
    texto = texto.lower().replace(',', '.').replace('x', 'x ')
    valor = None
    parcelas = 1
    tipo = 'PIX'

    # Valor + Pix
    match_pix = re.search(r'(\d+[.,]?\d*)\s*pix', texto)
    if match_pix:
        valor = float(match_pix.group(1))
        tipo = 'PIX'
        parcelas = 1

    # Valor + Parcelas (ex: 1234,56 10x)
    match_cartao = re.search(r'(\d+[.,]?\d*)\s*(\d{1,2})\s*x', texto)
    if match_cartao:
        valor = float(match_cartao.group(1))
        parcelas = int(match_cartao.group(2))
        tipo = 'CRÉDITO'

    return valor, parcelas, tipo

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text

    # ✅ Marcar como pago
    if msg and '✅' in msg:
        if comprovantes:
            comprovantes[-1]['pago'] = True
            await update.message.reply_text("✅ Comprovante marcado como pago!")
        return

    # Texto normal: tentar extrair valor e tipo
    valor, parcelas, tipo = parse_valor_e_parcelas(msg or '')

    # Se não reconheceu valor, tentar OCR
    if not valor and (update.message.photo or update.message.document):
        texto = extrair_texto(update)
        valor, parcelas, tipo = parse_valor_e_parcelas(texto)

    if not valor:
        await update.message.reply_text("❌ Não consegui identificar o valor. Envie no formato:\nEx: `6438,76 pix` ou `7899,99 10x`")
        return

    # Calcular taxa
    taxa_aplicada = 0.2 if tipo == 'PIX' else taxas_cartao.get(parcelas, 0)
    valor_liquido = round(valor * (1 - taxa_aplicada / 100), 2)
    horario = datetime.datetime.now().strftime("%H:%M")

    comprovante = {
        'valor': valor,
        'parcelas': parcelas,
        'horario': horario,
        'taxa': taxa_aplicada,
        'valor_liquido': valor_liquido,
        'pago': False
    }
    comprovantes.append(comprovante)

    resposta = (
        "📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {valor:,.2f}\n"
        f"💳 Parcelas: {parcelas}x\n"
        f"⏰ Horário: {horario}\n"
        f"📉 Taxa aplicada: {taxa_aplicada}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )
    await update.message.reply_text(resposta, parse_mode='Markdown')

async def listar_pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "*📋 Comprovantes Pendentes:*\n\n"
    for c in comprovantes:
        if not c['pago']:
            texto += f"• R$ {c['valor_liquido']:,.2f} | {c['parcelas']}x | {c['horario']}\n"
    await update.message.reply_text(texto or "Nenhum comprovante pendente.", parse_mode='Markdown')

async def listar_pagamentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "*✅ Comprovantes Pagos:*\n\n"
    for c in comprovantes:
        if c['pago']:
            texto += f"• R$ {c['valor_liquido']:,.2f} | {c['parcelas']}x | {c['horario']}\n"
    await update.message.reply_text(texto or "Nenhum comprovante pago ainda.", parse_mode='Markdown')

async def total_pendente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(c['valor_liquido'] for c in comprovantes if not c['pago'])
    await update.message.reply_text(f"💸 *Total que você deve pagar ao lojista:* R$ {total:,.2f}", parse_mode='Markdown')

async def total_geral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(c['valor_liquido'] for c in comprovantes)
    await update.message.reply_text(f"📊 *Total de todos os comprovantes (pagos e pendentes):* R$ {total:,.2f}", parse_mode='Markdown')

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "*📌 Comandos disponíveis:*\n\n"
        "• Enviar comprovante: `6438,76 pix` ou `7899,99 10x`\n"
        "• ✅ = marcar último como pago\n"
        "• /listarpendentes = listar não pagos\n"
        "• /listarpagos = listar pagos\n"
        "• /totalquedevo = soma dos pendentes\n"
        "• /totalgeral = soma geral\n"
        "• /ultimo = mostrar o último comprovante\n"
        "• /ajuda = mostrar essa lista"
    )
    await update.message.reply_text(texto, parse_mode='Markdown')

async def ultimo_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not comprovantes:
        await update.message.reply_text("Nenhum comprovante enviado ainda.")
        return
    c = comprovantes[-1]
    status = "✅ Pago" if c['pago'] else "🕓 Pendente"
    texto = (
        "📄 *Último Comprovante:*\n"
        f"💰 Valor: R$ {c['valor']:,.2f}\n"
        f"💳 Parcelas: {c['parcelas']}x\n"
        f"⏰ Horário: {c['horario']}\n"
        f"📉 Taxa: {c['taxa']}%\n"
        f"💵 Líquido: R$ {c['valor_liquido']:,.2f}\n"
        f"{status}"
    )
    await update.message.reply_text(texto, parse_mode='Markdown')
