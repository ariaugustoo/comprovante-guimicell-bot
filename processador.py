import re
from datetime import datetime
from telegram import Bot, Message
import pytesseract
import cv2
import numpy as np
from PIL import Image
from io import BytesIO

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002122662652

pendentes = []
pagos = []

TAXA_PIX = 0.002
TAXAS_CARTAO = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719, 6: 0.0829,
    7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088, 11: 0.1199, 12: 0.1252,
    13: 0.1369, 14: 0.1419, 15: 0.1469, 16: 0.1519, 17: 0.1589, 18: 0.1684
}

def extrair_texto_imagem(file_bytes):
    imagem = Image.open(BytesIO(file_bytes))
    imagem_cv = cv2.cvtColor(np.array(imagem), cv2.COLOR_RGB2BGR)
    return pytesseract.image_to_string(imagem_cv)

def normalizar_valor(valor_str):
    return float(valor_str.replace(".", "").replace(",", "."))

def calcular_liquido(valor, tipo, parcelas=1):
    taxa = TAXA_PIX if tipo == "pix" else TAXAS_CARTAO.get(parcelas, 0)
    return round(valor * (1 - taxa), 2), taxa

def registrar_comprovante(valor, tipo, horario, parcelas=1):
    liquido, taxa = calcular_liquido(valor, tipo, parcelas)
    comprovante = {
        "valor": valor,
        "tipo": tipo,
        "horario": horario,
        "parcelas": parcelas,
        "taxa": taxa,
        "liquido": liquido
    }
    pendentes.append(comprovante)
    return comprovante

def responder_mensagem(bot: Bot, message: Message, texto: str):
    bot.send_message(chat_id=GROUP_ID, text=texto)

def processar_mensagem(bot: Bot, message: Message):
    texto = message.text.lower() if message.text else ""

    if message.photo:
        responder_mensagem(bot, message, "🧾 Imagem recebida! Por favor, digite o valor e o tipo de pagamento (ex: 5899,99 pix ou 3.999,90 10x)")
        return

    if "pix" in texto:
        match = re.search(r"([\d.,]+)\s*pix", texto)
        if match:
            valor = normalizar_valor(match.group(1))
            horario = datetime.now().strftime("%H:%M")
            comprovante = registrar_comprovante(valor, "pix", horario)
            resposta = (
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {comprovante['valor']:.2f}\n"
                f"💳 Parcelas: À vista (PIX)\n"
                f"⏰ Horário: {comprovante['horario']}\n"
                f"📉 Taxa aplicada: {comprovante['taxa']*100:.2f}%\n"
                f"✅ Valor líquido a pagar: R$ {comprovante['liquido']:.2f}"
            )
            responder_mensagem(bot, message, resposta)
        return

    match_cartao = re.search(r"([\d.,]+)\s*(\d{1,2})x", texto)
    if match_cartao:
        valor = normalizar_valor(match_cartao.group(1))
        parcelas = int(match_cartao.group(2))
        horario = datetime.now().strftime("%H:%M")
        comprovante = registrar_comprovante(valor, "cartao", horario, parcelas)
        resposta = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {comprovante['valor']:.2f}\n"
            f"💳 Parcelas: {comprovante['parcelas']}x\n"
            f"⏰ Horário: {comprovante['horario']}\n"
            f"📉 Taxa aplicada: {comprovante['taxa']*100:.2f}%\n"
            f"✅ Valor líquido a pagar: R$ {comprovante['liquido']:.2f}"
        )
        responder_mensagem(bot, message, resposta)
        return

    if "✅" in texto:
        if pendentes:
            comprovante = pendentes.pop(0)
            pagos.append(comprovante)
            responder_mensagem(bot, message, "✅ Comprovante marcado como pago.")
        else:
            responder_mensagem(bot, message, "⚠️ Nenhum comprovante pendente para marcar como pago.")
        return

    if "listar pendentes" in texto:
        if pendentes:
            resposta = "📋 *Comprovantes Pendentes:*\n\n"
            for c in pendentes:
                resposta += (
                    f"• 💰 R$ {c['valor']:.2f} - "
                    f"{c['parcelas']}x - "
                    f"⏰ {c['horario']} - "
                    f"💸 Líquido: R$ {c['liquido']:.2f}\n"
                )
        else:
            resposta = "✅ Nenhum comprovante pendente."
        responder_mensagem(bot, message, resposta)
        return

    if "listar pagos" in texto:
        if pagos:
            resposta = "📗 *Comprovantes Pagos:*\n\n"
            for c in pagos:
                resposta += (
                    f"• R$ {c['valor']:.2f} - "
                    f"{c['parcelas']}x - "
                    f"{c['horario']} - "
                    f"💸 Líquido: R$ {c['liquido']:.2f}\n"
                )
        else:
            resposta = "📗 Nenhum comprovante foi marcado como pago ainda."
        responder_mensagem(bot, message, resposta)
        return

    if "último comprovante" in texto:
        if pendentes:
            c = pendentes[-1]
            resposta = (
                f"📌 Último Comprovante:\n"
                f"💰 R$ {c['valor']:.2f} - "
                f"{c['parcelas']}x - "
                f"{c['horario']} - "
                f"💸 Líquido: R$ {c['liquido']:.2f}"
            )
        else:
            resposta = "⚠️ Nenhum comprovante registrado ainda."
        responder_mensagem(bot, message, resposta)
        return

    if "total que devo" in texto:
        total = sum(c['liquido'] for c in pendentes)
        resposta = f"📊 Total em aberto (a pagar): R$ {total:.2f}"
        responder_mensagem(bot, message, resposta)
        return

    if "total geral" in texto:
        total = sum(c['liquido'] for c in pendentes + pagos)
        resposta = f"📊 Total geral (todos os comprovantes): R$ {total:.2f}"
        responder_mensagem(bot, message, resposta)
        return

    if "ajuda" in texto:
        comandos = (
            "🤖 *Comandos disponíveis:*\n\n"
            "`1234,56 pix` → Registrar PIX\n"
            "`7890,00 10x` → Registrar cartão parcelado\n"
            "`✅` → Marcar como pago\n"
            "`listar pendentes` → Ver pendentes\n"
            "`listar pagos` → Ver pagos\n"
            "`último comprovante` → Ver o último\n"
            "`total que devo` → Soma pendentes\n"
            "`total geral` → Soma de tudo\n"
            "`ajuda` → Ver comandos"
        )
        responder_mensagem(bot, message, comandos)

# Funções auxiliares para importações futuras (se quiser usar em dashboard)
def listar_pendentes():
    return pendentes

def listar_pagos():
    return pagos

def marcar_como_pago():
    if pendentes:
        pagos.append(pendentes.pop(0))

def obter_ultimo_comprovante():
    return pendentes[-1] if pendentes else None

def calcular_total_geral():
    return sum(c["liquido"] for c in pendentes + pagos)

def calcular_total_pendentes():
    return sum(c["liquido"] for c in pendentes)
