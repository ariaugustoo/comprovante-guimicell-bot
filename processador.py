import datetime
from collections import defaultdict

comprovantes = []
pagamentos = []
solicitacoes = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19,
    15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def normalizar_valor(valor_str):
    return float(valor_str.replace("R$", "").replace(".", "").replace(",", "."))

def calcular_valor_liquido(valor, tipo, parcelas=None):
    if tipo == "pix":
        taxa = 0.2
    elif tipo == "cartao" and parcelas:
        taxa = taxas_cartao.get(parcelas, 0)
    else:
        taxa = 0
    return round(valor * (1 - taxa / 100), 2), taxa

def registrar_comprovante(valor, tipo, parcelas=None):
    horario = datetime.datetime.now().strftime("%H:%M")
    liquido, taxa = calcular_valor_liquido(valor, tipo, parcelas)
    comprovantes.append({
        "valor": valor,
        "tipo": tipo,
        "parcelas": parcelas,
        "horario": horario,
        "taxa": taxa,
        "liquido": liquido,
        "pago": False
    })
    return horario, taxa, liquido

def marcar_como_pago(valor=None):
    if valor is None:
        for c in comprovantes:
            c["pago"] = True
        return
    restante = valor
    for c in comprovantes:
        if not c["pago"]:
            if c["liquido"] <= restante:
                restante -= c["liquido"]
                c["pago"] = True
            elif restante > 0:
                c["liquido"] -= restante
                restante = 0
                break

def resumo_status():
    total_pix = sum(c["liquido"] for c in comprovantes if c["tipo"] == "pix")
    total_cartao = sum(c["liquido"] for c in comprovantes if c["tipo"] == "cartao")
    total_pago = sum(c["liquido"] for c in comprovantes if c["pago"])
    total_pendente = sum(c["liquido"] for c in comprovantes if not c["pago"])
    return total_pix, total_cartao, total_pago, total_pendente
