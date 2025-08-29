import re
from datetime import datetime, timedelta
import pytz

comprovantes = []
solicitacoes_pagamento = []

TAXA_PIX = 0.002
TAXAS_CARTAO = {
    1: 0.0439,  2: 0.0519,  3: 0.0619,  4: 0.0659,  5: 0.0719,
    6: 0.0829,  7: 0.0919,  8: 0.0999,  9: 0.1029, 10: 0.1088,
    11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
    16: 0.1519, 17: 0.1589, 18: 0.1684
}

def normalizar_valor(valor_str):
    return float(valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip())

def calcular_liquido(valor, tipo, parcelas=None):
    if tipo == "pix":
        return round(valor * (1 - TAXA_PIX), 2)
    elif tipo == "cartao" and parcelas in TAXAS_CARTAO:
        return round(valor * (1 - TAXAS_CARTAO[parcelas]), 2)
    return valor

def processar_mensagem(texto):
    texto = texto.lower()
    padrao_pix = re.search(r"([\d\.,]+)\s*pix", texto)
    padrao_cartao = re.search(r"([\d\.,]+)\s*(\d{1,2})x", texto)

    if padrao_pix:
        valor = normalizar_valor(padrao_pix.group(1))
        return {
            "valor_bruto": valor,
            "tipo": "pix",
            "parcelas": None,
            "liquido": calcular_liquido(valor, "pix"),
            "horario": obter_horario_brasilia()
        }

    elif padrao_cartao:
        valor = normalizar_valor(padrao_cartao.group(1))
        parcelas = int(padrao_cartao.group(2))
        return {
            "valor_bruto": valor,
            "tipo": "cartao",
            "parcelas": parcelas,
            "liquido": calcular_liquido(valor, "cartao", parcelas),
            "horario": obter_horario_brasilia()
        }

    return None

def obter_horario_brasilia():
    fuso_brasilia = pytz.timezone("America/Sao_Paulo")
    return datetime.now(fuso_brasilia).strftime("%H:%M")

def registrar_comprovante(dados):
    comprovantes.append({
        **dados,
        "pago": False
    })

def marcar_como_pago(valor_pago):
    total_pendente = sum(c["liquido"] for c in comprovantes if not c["pago"])
    if valor_pago > total_pendente:
        return False, total_pendente

    restante = valor_pago
    for c in comprovantes:
        if not c["pago"]:
            if restante >= c["liquido"]:
                restante -= c["liquido"]
                c["pago"] = True
            else:
                c["liquido"] -= restante
                c["valor_bruto"] = round(c["liquido"] / (1 - TAXAS_CARTAO.get(c["parcelas"], TAXA_PIX)), 2) if c["tipo"] == "cartao" else round(c["liquido"] / (1 - TAXA_PIX), 2)
                restante = 0
                break
    return True, valor_pago

def total_pendente_liquido():
    return round(sum(c["liquido"] for c in comprovantes if not c["pago"]), 2)

def total_pendente_bruto():
    return round(sum(c["valor_bruto"] for c in comprovantes if not c["pago"]), 2)

def listar_pendentes():
    linhas = []
    for c in comprovantes:
        if not c["pago"]:
            tipo_str = "PIX" if c["tipo"] == "pix" else f"{c['parcelas']}x"
            linhas.append(
                f"💰 R$ {c['valor_bruto']:.2f} | {tipo_str} | ⏰ {c['horario']} | 💸 Líquido: R$ {c['liquido']:.2f}"
            )
    return "\n".join(linhas) if linhas else "✅ Nenhum comprovante pendente."

def listar_pagamentos_feitos():
    linhas = []
    for c in comprovantes:
        if c["pago"]:
            tipo_str = "PIX" if c["tipo"] == "pix" else f"{c['parcelas']}x"
            linhas.append(
                f"💰 R$ {c['valor_bruto']:.2f} | {tipo_str} | ⏰ {c['horario']} | 💸 Líquido: R$ {c['liquido']:.2f}"
            )
    return "\n".join(linhas) if linhas else "Nenhum pagamento registrado ainda."

def solicitar_pagamento(valor, chave_pix):
    solicitacoes_pagamento.append({
        "valor": valor,
        "chave_pix": chave_pix
    })
    return f"📬 Solicitação de pagamento registrada:\n💰 Valor: R$ {valor:.2f}\n🔑 Chave Pix: {chave_pix}"

def limpar_tudo():
    comprovantes.clear()
    solicitacoes_pagamento.clear()

def corrigir_valor(indice, novo_valor):
    if 0 <= indice < len(comprovantes):
        comprovantes[indice]["valor_bruto"] = novo_valor
        comprovantes[indice]["liquido"] = calcular_liquido(
            novo_valor,
            comprovantes[indice]["tipo"],
            comprovantes[indice]["parcelas"]
        )
        return True
    return False
