import re
from datetime import datetime, timedelta
import pytz

# Banco de dados simples
comprovantes = []
pagamentos_parciais = []

# Taxas de cartão por parcela
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19,
    15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def normalizar_valor(valor_str):
    try:
        valor_str = valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor_str)
    except:
        return None

def calcular_liquido(valor, parcelas=None):
    if parcelas:
        taxa = TAXAS_CARTAO.get(parcelas, 0) / 100
    else:
        taxa = 0.002  # PIX
    return round(valor * (1 - taxa), 2), round(taxa * 100, 2)

def registrar_comprovante(valor_bruto, tipo, parcelas=None):
    horario = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%H:%M")
    valor_liquido, taxa_aplicada = calcular_liquido(valor_bruto, parcelas)
    comprovantes.append({
        "valor_bruto": valor_bruto,
        "tipo": tipo,
        "parcelas": parcelas,
        "horario": horario,
        "taxa": taxa_aplicada,
        "valor_liquido": valor_liquido,
        "pago": False
    })
    return valor_bruto, tipo, parcelas, horario, taxa_aplicada, valor_liquido

def marcar_como_pago(valor_pagamento):
    total_pendente = calcular_total_liquido()
    if valor_pagamento > total_pendente:
        return False, "❌ Valor excede o total devido ao lojista. Pagamento não registrado."

    valor_restante = valor_pagamento
    for comp in comprovantes:
        if not comp["pago"]:
            if comp["valor_liquido"] <= valor_restante:
                valor_restante -= comp["valor_liquido"]
                comp["pago"] = True
            else:
                comp["valor_liquido"] -= valor_restante
                pagamentos_parciais.append({
                    "data": datetime.now().strftime("%d/%m/%Y"),
                    "valor": valor_restante
                })
                valor_restante = 0
            if valor_restante == 0:
                break
    return True, "✅ Pagamento registrado com sucesso."

def calcular_total_liquido():
    return round(sum(comp["valor_liquido"] for comp in comprovantes if not comp["pago"]), 2)

def listar_pendentes():
    pendentes = [comp for comp in comprovantes if not comp["pago"]]
    if not pendentes:
        return "📂 Nenhum comprovante pendente."
    resposta = "📌 *Comprovantes Pendentes:*\n"
    for i, c in enumerate(pendentes, 1):
        resposta += f"\n{i}. 💰 *R${c['valor_bruto']:.2f}* | {c['tipo']} | ⏰ {c['horario']}"
    resposta += f"\n\n💰 *Total pendente:* R$ {calcular_total_liquido():.2f}"
    return resposta

def listar_pagos():
    pagos = [comp for comp in comprovantes if comp["pago"]]
    if not pagos:
        return "📂 Nenhum comprovante pago ainda."
    resposta = "✅ *Comprovantes Pagos:*\n"
    for i, c in enumerate(pagos, 1):
        resposta += f"\n{i}. R${c['valor_bruto']:.2f} | {c['tipo']} | {c['horario']}"
    return resposta
