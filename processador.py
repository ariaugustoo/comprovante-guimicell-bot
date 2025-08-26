import pytesseract
from PIL import Image
import re
import io

# Dicionário para armazenar os comprovantes
comprovantes = []

# Tabela de taxas
taxas_credito = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99,
    12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19,
    17: 15.89, 18: 16.84
}

def aplicar_taxa(valor, tipo, parcelas=1):
    if tipo == "pix":
        taxa = 0.2
    else:
        taxa = taxas_credito.get(parcelas, 0)
    valor_liquido = valor * (1 - taxa / 100)
    return taxa, round(valor_liquido, 2)

def extrair_texto_imagem(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    texto = pytesseract.image_to_string(image, lang='por')
    return texto

def parse_valor(texto):
    match = re.search(r'(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', texto)
    if match:
        return float(match.group(1).replace('.', '').replace(',', '.'))
    return None

def parse_parcelas(texto):
    match = re.search(r'(\d{1,2})x', texto.lower())
    if match:
        return int(match.group(1))
    return 1

async def processar_mensagem(update):
    texto = update.message.text
    valor = None
    parcelas = 1
    tipo = "pix"
    horario = update.message.date.strftime("%H:%M")

    # Se for imagem
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        image_bytes = await file.download_as_bytearray()
        texto_extraido = extrair_texto_imagem(image_bytes)
        valor = parse_valor(texto_extraido)
        parcelas = parse_parcelas(texto_extraido)
        tipo = "cartão" if parcelas > 1 else "pix"
    # Se for mensagem de texto manual
    elif texto:
        valor_match = re.search(r'(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', texto)
        if valor_match:
            valor = float(valor_match.group(1).replace('.', '').replace(',', '.'))
        if 'x' in texto.lower():
            parcelas = parse_parcelas(texto)
            tipo = "cartão"
        elif 'pix' in texto.lower():
            tipo = "pix"

    if valor:
        taxa, valor_liquido = aplicar_taxa(valor, tipo, parcelas)
        comprovante = {
            "valor_bruto": valor,
            "parcelas": parcelas,
            "horario": horario,
            "tipo": tipo,
            "taxa": taxa,
            "valor_liquido": valor_liquido,
            "pago": False
        }
        comprovantes.append(comprovante)

        return f"""📄 *Comprovante analisado*:
💰 Valor bruto: R$ {valor:,.2f}
💳 Parcelas: {parcelas}x
⏰ Horário: {horario}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}
""".replace(',', 'X').replace('.', ',').replace('X', '.')
    else:
        return "❌ Não foi possível identificar o valor. Envie novamente ou digite manualmente (ex: `1534,90 pix`)"

def marcar_como_pago():
    for comprovante in reversed(comprovantes):
        if not comprovante["pago"]:
            comprovante["pago"] = True
            return "✅ Último comprovante marcado como pago."
    return "❌ Nenhum comprovante pendente encontrado."

def calcular_total():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    return f"📊 Total a pagar (pendente): R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."
    resposta = "📋 Comprovantes pendentes:\n"
    for i, c in enumerate(pendentes, 1):
        resposta += f"{i}. R$ {c['valor_liquido']:,.2f} ({c['parcelas']}x - {c['horario']})\n"
    return resposta.replace(',', 'X').replace('.', ',').replace('X', '.')

def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "📗 Nenhum comprovante pago ainda."
    resposta = "📗 Comprovantes pagos:\n"
    for i, c in enumerate(pagos, 1):
        resposta += f"{i}. R$ {c['valor_liquido']:,.2f} ({c['parcelas']}x - {c['horario']})\n"
    return resposta.replace(',', 'X').replace('.', ',').replace('X', '.')

def mostrar_ultimo():
    if comprovantes:
        c = comprovantes[-1]
        status = "✅ PAGO" if c["pago"] else "❌ NÃO PAGO"
        return f"""📄 Último comprovante:
💰 Valor bruto: R$ {c['valor_bruto']:,.2f}
💳 Parcelas: {c['parcelas']}x
⏰ Horário: {c['horario']}
📉 Taxa aplicada: {c['taxa']}%
✅ Valor líquido: R$ {c['valor_liquido']:,.2f}
📌 Status: {status}
""".replace(',', 'X').replace('.', ',').replace('X', '.')
    return "❌ Nenhum comprovante registrado ainda."

def total_geral():
    total = sum(c["valor_liquido"] for c in comprovantes)
    return f"💰 Total geral (todos): R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
