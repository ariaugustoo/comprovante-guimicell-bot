from telegram import Update
from telegram.ext import CallbackContext
import pytesseract
from PIL import Image
import cv2
import numpy as np
import io
import re
from datetime import datetime

# Dicionário para armazenar comprovantes em memória
comprovantes = []

# Tabela de taxas
taxas_cartao = {
    1: 0.0439,  2: 0.0519,  3: 0.0619,  4: 0.0659,  5: 0.0719,  6: 0.0829,
    7: 0.0919,  8: 0.0999,  9: 0.1029, 10: 0.1088, 11: 0.1199, 12: 0.1252,
    13: 0.1369, 14: 0.1419, 15: 0.1469, 16: 0.1519, 17: 0.1589, 18: 0.1684
}
taxa_pix = 0.002

def extrair_texto_imagem(file_bytes):
    image = Image.open(io.BytesIO(file_bytes))
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    texto = pytesseract.image_to_string(img_cv, lang='por')
    return texto

def calcular_valor_liquido(valor_bruto, parcelas=None, tipo='pix'):
    if tipo == 'pix':
        taxa = taxa_pix
    else:
        taxa = taxas_cartao.get(parcelas, 0)
    valor_liquido = valor_bruto * (1 - taxa)
    return round(valor_liquido, 2), taxa

def formatar_resposta(valor_bruto, parcelas, horario, taxa, valor_liquido):
    resposta = (
        "📄 *Comprovante analisado:*\n"
        f"💰 *Valor bruto:* R$ {valor_bruto:,.2f}\n"
        f"💳 *Parcelas:* {parcelas if parcelas else 'PIX'}\n"
        f"⏰ *Horário:* {horario}\n"
        f"📉 *Taxa aplicada:* {taxa * 100:.2f}%\n"
        f"✅ *Valor líquido a pagar:* R$ {valor_liquido:,.2f}"
    )
    return resposta

def normalizar_valor(valor_str):
    valor_str = valor_str.replace("R$", "").replace(" ", "").replace(",", ".")
    return float(re.findall(r'\d+\.\d+|\d+', valor_str)[0])

def processar_comprovante(update: Update, context: CallbackContext):
    message = update.message
    if message.text:
        texto = message.text.lower()
        if texto == "✅":
            marcar_como_pago(update, context)
            return
        elif "pix" in texto:
            try:
                valor = normalizar_valor(texto)
                valor_liquido, taxa = calcular_valor_liquido(valor, tipo='pix')
                horario = datetime.now().strftime("%H:%M")
                comprovantes.append({
                    'valor_bruto': valor,
                    'parcelas': None,
                    'horario': horario,
                    'valor_liquido': valor_liquido,
                    'status': 'pendente'
                })
                resposta = formatar_resposta(valor, None, horario, taxa, valor_liquido)
                message.reply_text(resposta, parse_mode='Markdown')
            except:
                message.reply_text("Erro ao processar valor PIX.")
        elif "x" in texto:
            try:
                valor = normalizar_valor(texto)
                parcelas = int(re.findall(r'(\d+)x', texto)[0])
                valor_liquido, taxa = calcular_valor_liquido(valor, parcelas, tipo='cartao')
                horario = datetime.now().strftime("%H:%M")
                comprovantes.append({
                    'valor_bruto': valor,
                    'parcelas': parcelas,
                    'horario': horario,
                    'valor_liquido': valor_liquido,
                    'status': 'pendente'
                })
                resposta = formatar_resposta(valor, parcelas, horario, taxa, valor_liquido)
                message.reply_text(resposta, parse_mode='Markdown')
            except:
                message.reply_text("Erro ao processar valor com parcelas.")
        return

    if message.photo or message.document:
        file = message.photo[-1].get_file() if message.photo else message.document.get_file()
        file_bytes = file.download_as_bytearray()
        texto_extraido = extrair_texto_imagem(file_bytes)

        valores = re.findall(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})', texto_extraido)
        parcelas_match = re.search(r'(\d{1,2})x', texto_extraido.lower())
        horario = datetime.now().strftime("%H:%M")

        if valores:
            valor = normalizar_valor(valores[0])
            if parcelas_match:
                parcelas = int(parcelas_match.group(1))
                valor_liquido, taxa = calcular_valor_liquido(valor, parcelas, tipo='cartao')
            else:
                parcelas = None
                valor_liquido, taxa = calcular_valor_liquido(valor, tipo='pix')

            comprovantes.append({
                'valor_bruto': valor,
                'parcelas': parcelas,
                'horario': horario,
                'valor_liquido': valor_liquido,
                'status': 'pendente'
            })

            resposta = formatar_resposta(valor, parcelas, horario, taxa, valor_liquido)
            message.reply_text(resposta, parse_mode='Markdown')
        else:
            message.reply_text("❌ Não consegui identificar o valor. Por favor, envie o valor manualmente (ex: 1249,90 pix ou 1249,90 3x).")

def marcar_como_pago(update: Update, context: CallbackContext):
    for comprovante in reversed(comprovantes):
        if comprovante['status'] == 'pendente':
            comprovante['status'] = 'pago'
            update.message.reply_text("✅ Último comprovante marcado como pago!")
            return
    update.message.reply_text("Nenhum comprovante pendente para marcar como pago.")

def listar_pendentes(update: Update, context: CallbackContext):
    pendentes = [c for c in comprovantes if c['status'] == 'pendente']
    if not pendentes:
        update.message.reply_text("Nenhum comprovante pendente.")
        return
    texto = "*📋 Comprovantes Pendentes:*\n\n"
    for i, c in enumerate(pendentes, 1):
        tipo = f"{c['parcelas']}x" if c['parcelas'] else "PIX"
        texto += f"{i}. 💰 R$ {c['valor_bruto']:,.2f} | {tipo} | ⏰ {c['horario']}\n"
    update.message.reply_text(texto, parse_mode='Markdown')

def listar_pagamentos(update: Update, context: CallbackContext):
    pagos = [c for c in comprovantes if c['status'] == 'pago']
    if not pagos:
        update.message.reply_text("Nenhum comprovante marcado como pago.")
        return
    texto = "*📗 Comprovantes Pagos:*\n\n"
    for i, c in enumerate(pagos, 1):
        tipo = f"{c['parcelas']}x" if c['parcelas'] else "PIX"
        texto += f"{i}. 💰 R$ {c['valor_bruto']:,.2f} | {tipo} | ⏰ {c['horario']}\n"
    update.message.reply_text(texto, parse_mode='Markdown')

def calcular_total_pendente(update: Update, context: CallbackContext):
    total = sum(c['valor_liquido'] for c in comprovantes if c['status'] == 'pendente')
    update.message.reply_text(f"💸 *Total a pagar (pendentes):* R$ {total:,.2f}", parse_mode='Markdown')

def calcular_total_geral(update: Update, context: CallbackContext):
    total = sum(c['valor_liquido'] for c in comprovantes)
    update.message.reply_text(f"💰 *Total geral de comprovantes:* R$ {total:,.2f}", parse_mode='Markdown')

def ultimo_comprovante(update: Update, context: CallbackContext):
    if not comprovantes:
        update.message.reply_text("Nenhum comprovante registrado.")
        return
    c = comprovantes[-1]
    tipo = f"{c['parcelas']}x" if c['parcelas'] else "PIX"
    resposta = formatar_resposta(
        c['valor_bruto'], c['parcelas'], c['horario'],
        taxas_cartao.get(c['parcelas'], taxa_pix) if c['parcelas'] else taxa_pix,
        c['valor_liquido']
    )
    update.message.reply_text("📌 *Último comprovante:*\n\n" + resposta, parse_mode='Markdown')

def ajuda(update: Update, context: CallbackContext):
    texto = (
        "*📖 Comandos disponíveis:*\n"
        "1️⃣ Envie comprovante em PDF ou imagem\n"
        "2️⃣ Ou envie valor manual (ex: `1490,00 pix`, `1899,99 10x`)\n"
        "\n"
        "✅ = marca último comprovante como pago\n"
        "/listar_pendentes – Ver pendentes\n"
        "/listar_pagos – Ver pagos\n"
        "/total_que_devo – Total em aberto\n"
        "/total_geral – Total geral\n"
        "/último_comprovante – Ver último\n"
        "/ajuda – Mostrar comandos"
    )
    update.message.reply_text(texto, parse_mode='Markdown')
