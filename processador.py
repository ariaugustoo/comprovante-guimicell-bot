import re
from datetime import datetime

comprovantes = []

# Tabela de taxas de cartão de 1x a 18x
taxas_cartao = {
    1: 4.39,
    2: 5.19,
    3: 6.19,
    4: 6.59,
    5: 7.19,
    6: 8.29,
    7: 9.19,
    8: 9.99,
    9: 10.29,
    10: 10.88,
    11: 11.99,
    12: 12.52,
    13: 13.69,
    14: 14.19,
    15: 14.69,
    16: 15.19,
    17: 15.89,
    18: 16.84,
}

def normalizar_valor(valor_str):
    valor_str = valor_str.replace(".", "").replace(",", ".")
    try:
        return float(valor_str)
    except:
        return None

def processar_mensagem(texto):
    texto = texto.replace("r$", "").strip().lower()

    match_pix = re.match(r"([\d\.,]+)\s*pix", texto)
    match_cartao = re.match(r"([\d\.,]+)\s*(\d{1,2})x", texto)

    if match_pix:
        valor = normalizar_valor(match_pix.group(1))
        if valor is None:
            return "Valor inválido."
        taxa = 0.2
        desconto = valor * (taxa / 100)
        valor_liquido = valor - desconto
        horario = datetime.now().strftime("%H:%M")
        comprovantes.append({
            "tipo": "pix",
            "bruto": valor,
            "liquido": valor_liquido,
            "parcelas": 1,
            "horario": horario,
            "pago": False
        })
        return (
            f"Comprovante registrado:\n"
            f"Valor bruto: R$ {valor:,.2f}\n"
            f"Pagamento: PIX\n"
            f"Horário: {horario}\n"
            f"Taxa: {taxa:.1f}%\n"
            f"Valor líquido: R$ {valor_liquido:,.2f}"
        )

    elif match_cartao:
        valor = normalizar_valor(match_cartao.group(1))
        parcelas = int(match_cartao.group(2))
        if valor is None or parcelas not in taxas_cartao:
            return "Valor ou número de parcelas inválido."
        taxa = taxas_cartao[parcelas]
        desconto = valor * (taxa / 100)
        valor_liquido = valor - desconto
        horario = datetime.now().strftime("%H:%M")
        comprovantes.append({
            "tipo": "cartao",
            "bruto": valor,
            "liquido": valor_liquido,
            "parcelas": parcelas,
            "horario": horario,
            "pago": False
        })
        return (
            f"Comprovante registrado:\n"
            f"Valor bruto: R$ {valor:,.2f}\n"
            f"Pagamento: Cartão em {parcelas}x\n"
            f"Horário: {horario}\n"
            f"Taxa: {taxa:.2f}%\n"
            f"Valor líquido: R$ {valor_liquido:,.2f}"
        )

    return "Formato de mensagem inválido. Use: 2200 pix ou 5100 10x"

def registrar_pagamento():
    for c in comprovantes:
        if not c["pago"]:
            c["pago"] = True
            return f"Pagamento marcado como feito para: R$ {c['liquido']:,.2f}"
    return "Nenhum comprovante pendente encontrado."

def total_liquido_pendentes():
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    return f"Total líquido pendente: R$ {total:,.2f}"

def listar_comprovantes_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "Nenhum comprovante pendente."

    texto = "Comprovantes pendentes:\n"
    total = 0
    for i, c in enumerate(pendentes, 1):
        texto += f"{i}. R$ {c['liquido']:,.2f} - {c['tipo']} - {c['parcelas']}x - {c['horario']}\n"
        total += c["liquido"]
    texto += f"Total líquido pendente: R$ {total:,.2f}"
    return texto

def listar_comprovantes_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "Nenhum comprovante pago."

    texto = "Comprovantes pagos:\n"
    total = 0
    for i, c in enumerate(pagos, 1):
        texto += f"{i}. R$ {c['liquido']:,.2f} - {c['tipo']} - {c['parcelas']}x - {c['horario']}\n"
        total += c["liquido"]
    texto += f"Total já pago: R$ {total:,.2f}"
    return texto

def solicitar_pagamento_manual():
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    return f"Por favor, realize o pagamento do valor líquido pendente: R$ {total:,.2f}"

def limpar_tudo():
    global comprovantes
    comprovantes = []
    return "Todos os comprovantes foram apagados com sucesso."
