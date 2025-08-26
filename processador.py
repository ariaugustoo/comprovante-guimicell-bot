import pytesseract
import cv2
import tempfile
from PIL import Image
import re
from datetime import datetime

TAXA_PIX = 0.002
TAXAS_CARTAO = {
    i: t for i, t in zip(range(1, 19), [
        4.39, 5.19, 6.19, 6.59, 7.19, 8.29, 9.19, 9.99, 10.29,
        10.88, 11.99, 12.52, 13.69, 14.19, 14.69, 15.19, 15.89, 16.84
    ])
}

def extrair_texto_ocr(imagem):
    imagem_cv = cv2.imdecode(imagem, cv2.IMREAD_COLOR)
    texto = pytesseract.image_to_string(imagem_cv, lang='por')
    return texto

def extrair_info_texto(texto):
    valor = re.search(r'(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', texto)
    horario = re.search(r'(\d{2}:\d{2})', texto)
    parcelas = re.search(r'(\d{1,2})x', texto.lower())
    valor = valor.group(1).replace(".", "").replace(",", ".") if valor else None
    return float(valor) if valor else None, horario.group(1) if horario else "N/A", int(parcelas.group(1)) if parcelas else 1

def calcular_valor_liquido(valor, metodo, parcelas=1):
    if metodo == 'pix':
        return round(valor * (1 - TAXA_PIX), 2), TAXA_PIX * 100
    else:
        taxa = TAXAS_CARTAO.get(parcelas, 0) / 100
        return round(valor * (1 - taxa), 2), taxa * 100

async def processar_comprovante(update, context, comprovantes):
    mensagem = update.message
    valor = None
    parcelas = 1

    if mensagem.text:
        texto = mensagem.text.lower()
        valor_match = re.search(r'(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', texto)
        parcelas_match = re.search(r'(\d{1,2})x', texto)
        metodo = 'pix' if 'pix' in texto else 'cartao'
        if valor_match:
            valor = float(valor_match.group(1).replace(".", "").replace(",", "."))
        if parcelas_match:
            parcelas = int(parcelas_match.group(1))
    elif mensagem.photo or mensagem.document:
        arquivo = await mensagem.get_file()
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            await arquivo.download_to_drive(custom_path=tf.name)
            imagem = cv2.imread(tf.name)
            texto = pytesseract.image_to_string(imagem, lang="por")
            valor, horario, parcelas = extrair_info_texto(texto)
            metodo = "pix" if "pix" in texto.lower() else "cartao"
    else:
        return "❌ Não consegui entender o comprovante."

    if not valor:
        return "❌ Não foi possível identificar o valor."

    valor_liquido, taxa = calcular_valor_liquido(valor, metodo, parcelas)
    comprovante = {
        "valor": valor,
        "parcelas": parcelas,
        "metodo": metodo,
        "horario": datetime.now().strftime("%H:%M"),
        "liquido": valor_liquido,
        "pago": False
    }
    comprovantes.append(comprovante)

    return (
        f"📄 Comprovante analisado:\n"
        f"💰 Valor bruto: R$ {valor:.2f}\n"
        f"💳 Parcelas: {parcelas}x\n"
        f"⏰ Horário: {comprovante['horario']}\n"
        f"📉 Taxa aplicada: {taxa:.2f}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:.2f}"
    )

def marcar_como_pago(comprovantes):
    for comp in reversed(comprovantes):
        if not comp["pago"]:
            comp["pago"] = True
            return "✅ Comprovante marcado como pago!"
    return "⚠️ Nenhum comprovante pendente encontrado."

def total_pendentes(comprovantes):
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    return f"💰 Total de pagamentos pendentes: R$ {total:.2f}"

def listar_pendentes(comprovantes):
    lista = [f"R$ {c['liquido']:.2f} - {c['parcelas']}x" for c in comprovantes if not c["pago"]]
    return "\n".join(lista) or "✅ Nenhum pendente."

def listar_pagos(comprovantes):
    lista = [f"R$ {c['liquido']:.2f} - {c['parcelas']}x" for c in comprovantes if c["pago"]]
    return "\n".join(lista) or "❌ Nenhum pago ainda."

def ajuda():
    return (
        "📌 *Comandos disponíveis:*\n"
        "/pago – Marcar último como pago\n"
        "/totalquedevo – Total pendente\n"
        "/listarpendentes – Lista pendentes\n"
        "/listarpagos – Lista pagos\n"
        "/ultimocomprovante – Último enviado\n"
        "/totalgeral – Soma total de todos\n"
        "/ajuda – Mostrar comandos"
    )

def ultimo_comprovante(comprovantes):
    if not comprovantes:
        return "⚠️ Nenhum comprovante encontrado."
    c = comprovantes[-1]
    return f"📄 Último: R$ {c['valor']:.2f} ({c['parcelas']}x) – {'✅ Pago' if c['pago'] else '🕐 Pendente'}"

def total_geral(comprovantes):
    total = sum(c["liquido"] for c in comprovantes)
    return f"📊 Total geral (pagos + pendentes): R$ {total:.2f}"
