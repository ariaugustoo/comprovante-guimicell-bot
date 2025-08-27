import re
from datetime import datetime
from pytz import timezone
import os
import json
import requests

# Taxas de cartão por número de parcelas
TAXAS_CARTAO = {
    1: 0.0439,  2: 0.0519,  3: 0.0619,  4: 0.0659,  5: 0.0719,
    6: 0.0829,  7: 0.0919,  8: 0.0999,  9: 0.1029, 10: 0.1088,
    11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
    16: 0.1519, 17: 0.1589, 18: 0.1684
}

TAXA_PIX = 0.002  # 0,2%

DATA_FILE = "comprovantes.json"
TIMEZONE = timezone("America/Sao_Paulo")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

# ---------------------- UTILITÁRIOS ----------------------

def enviar_mensagem(chat_id, texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto
    }
    requests.post(url, json=payload)

def salvar_comprovantes(comprovantes):
    with open(DATA_FILE, "w") as f:
        json.dump(comprovantes, f, indent=2)

def carregar_comprovantes():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def normalizar_valor(valor_str):
    valor_str = valor_str.replace(".", "").replace(",", ".")
    return float(valor_str)

# ---------------------- COMANDOS ----------------------

def processar_mensagem(chat_id, texto):
    comprovantes = carregar_comprovantes()
    texto = texto.strip().lower()

    if texto.endswith("pix"):
        try:
            valor_str = texto.replace("pix", "").strip()
            valor = normalizar_valor(valor_str)
            taxa = TAXA_PIX
            desconto = valor * taxa
            liquido = valor - desconto
            horario = datetime.now(TIMEZONE).strftime("%H:%M")

            comprovantes.append({
                "tipo": "pix",
                "valor": valor,
                "taxa": taxa,
                "liquido": round(liquido, 2),
                "horario": horario,
                "pago": False
            })

            salvar_comprovantes(comprovantes)

            resposta = f"""📄 Comprovante analisado:
💰 Valor bruto: R$ {valor:,.2f}
💳 Tipo: PIX
⏰ Horário: {horario}
📉 Taxa aplicada: {taxa*100:.2f}%
✅ Valor líquido a pagar: R$ {liquido:,.2f}""".replace(",", "X").replace(".", ",").replace("X", ".")

            enviar_mensagem(chat_id, resposta)
            return "OK", 200

        except Exception as e:
            enviar_mensagem(chat_id, "❌ Erro ao processar PIX. Verifique o valor.")
            return "OK", 200

    elif "x" in texto:
        try:
            match = re.match(r"([\d\.,]+)\s*(\d{1,2})x", texto)
            if not match:
                raise ValueError("Formato inválido.")

            valor = normalizar_valor(match.group(1))
            parcelas = int(match.group(2))
            taxa = TAXAS_CARTAO.get(parcelas)

            if not taxa:
                raise ValueError("Número de parcelas não suportado.")

            desconto = valor * taxa
            liquido = valor - desconto
            horario = datetime.now(TIMEZONE).strftime("%H:%M")

            comprovantes.append({
                "tipo": f"{parcelas}x",
                "valor": valor,
                "taxa": taxa,
                "liquido": round(liquido, 2),
                "horario": horario,
                "pago": False
            })

            salvar_comprovantes(comprovantes)

            resposta = f"""📄 Comprovante analisado:
💰 Valor bruto: R$ {valor:,.2f}
💳 Parcelas: {parcelas}x
⏰ Horário: {horario}
📉 Taxa aplicada: {taxa*100:.2f}%
✅ Valor líquido a pagar: R$ {liquido:,.2f}""".replace(",", "X").replace(".", ",").replace("X", ".")

            enviar_mensagem(chat_id, resposta)
            return "OK", 200

        except Exception as e:
            enviar_mensagem(chat_id, "❌ Erro ao processar cartão. Verifique o valor e parcelas.")
            return "OK", 200

    else:
        enviar_mensagem(chat_id, "❌ Formato inválido. Envie algo como '6438,90 pix' ou '7899,99 10x'.")
        return "OK", 200

def comando_total_liquido(chat_id):
    comprovantes = carregar_comprovantes()
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    resposta = f"💰 Total líquido dos comprovantes pendentes: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    enviar_mensagem(chat_id, resposta)
    return "OK", 200

def comando_total_bruto(chat_id):
    comprovantes = carregar_comprovantes()
    total = sum(c["valor"] for c in comprovantes if not c["pago"])
    resposta = f"💰 Total bruto dos comprovantes pendentes: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    enviar_mensagem(chat_id, resposta)
    return "OK", 200

def marcar_como_pago(chat_id):
    comprovantes = carregar_comprovantes()
    if not comprovantes:
        enviar_mensagem(chat_id, "❌ Nenhum comprovante para marcar como pago.")
        return "OK", 200

    for c in comprovantes:
        if not c["pago"]:
            c["pago"] = True
            salvar_comprovantes(comprovantes)
            enviar_mensagem(chat_id, "✅ Último comprovante marcado como pago.")
            return "OK", 200

    enviar_mensagem(chat_id, "✅ Todos os comprovantes já estão marcados como pagos.")
    return "OK", 200
