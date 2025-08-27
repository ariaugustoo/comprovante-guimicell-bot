import re
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

comprovantes = []
resumo_enviado = False

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def calcular_liquido(valor, parcelas=None):
    if parcelas:
        taxa = taxas_cartao.get(parcelas, 0)
    else:
        taxa = 0.2  # PIX
    liquido = valor * (1 - taxa / 100)
    return round(liquido, 2), taxa

def adicionar_comprovante(valor, parcelas, horario, tipo, pago=False):
    liquido, taxa = calcular_liquido(valor, parcelas)
    comprovante = {
        "valor": valor,
        "parcelas": parcelas,
        "horario": horario,
        "tipo": tipo,
        "taxa": taxa,
        "liquido": liquido,
        "pago": pago,
        "timestamp": datetime.now()
    }
    comprovantes.append(comprovante)
    return comprovante

def marcar_comprovante_como_pago():
    for c in reversed(comprovantes):
        if not c["pago"]:
            c["pago"] = True
            return c
    return None

def gerar_resumo():
    pendentes = [c for c in comprovantes if not c["pago"]]
    pagos = [c for c in comprovantes if c["pago"]]
    total_pendentes = sum(c["liquido"] for c in pendentes)
    total_pagos = sum(c["liquido"] for c in pagos)
    total_geral = total_pendentes + total_pagos
    return pendentes, pagos, total_pendentes, total_pagos, total_geral

def limpar_tudo():
    comprovantes.clear()

def ultimo_comprovante():
    return comprovantes[-1] if comprovantes else None

def listar_comprovantes(pago):
    return [c for c in comprovantes if c["pago"] == pago]
