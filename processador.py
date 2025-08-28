from datetime import datetime

comprovantes = []

TAXA_PIX = 0.002
TAXAS_CARTAO = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719,
    6: 0.0829, 7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088,
    11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419,
    15: 0.1469, 16: 0.1519, 17: 0.1589, 18: 0.1684
}

def normalizar_valor(valor_str):
    valor_str = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(valor_str)
    except ValueError:
        return None

def calcular_liquido(valor, tipo, parcelas=None):
    if tipo == "PIX":
        taxa = TAXA_PIX
    else:
        taxa = TAXAS_CARTAO.get(parcelas, 0)
    liquido = round(valor * (1 - taxa), 2)
    return liquido, taxa

def registrar_pagamento(valor_str, tipo_pagamento, parcelas=None):
    valor = normalizar_valor(valor_str)
    if valor is None:
        return "❌ Valor inválido. Por favor, envie no formato correto. Ex: 2200 pix ou 3000 6x"

    liquido, taxa = calcular_liquido(valor, tipo_pagamento, parcelas)
    horario = datetime.now().strftime("%H:%M")
    comprovante = {
        "valor": valor,
        "tipo": tipo_pagamento,
        "parcelas": parcelas,
        "liquido": liquido,
        "horario": horario,
        "pago": False
    }
    comprovantes.append(comprovante)

    if tipo_pagamento == "PIX":
        emoji = "💰"
    else:
        emoji = "💳"

    msg = f"📄 Comprovante registrado:\n"
    msg += f"💵 Valor bruto: R$ {valor:,.2f}\n"
    msg += f"{emoji} Pagamento: {tipo_pagamento}"
    if parcelas:
        msg += f" em {parcelas}x"
    msg += f"\n⏰ Horário: {horario}"
    msg += f"\n📉 Taxa: {taxa * 100:.1f}%"
    msg += f"\n✅ Valor líquido: R$ {liquido:,.2f}"

    return msg

def marcar_como_pago():
    for comp in reversed(comprovantes):
        if not comp["pago"]:
            comp["pago"] = True
            return "✅ Último comprovante marcado como pago."
    return "ℹ️ Nenhum comprovante pendente encontrado."

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "🟢 Nenhum comprovante pendente."
    total = sum(c["valor"] for c in pendentes)
    texto = "📋 Comprovantes pendentes:\n"
    for i, c in enumerate(pendentes, 1):
        texto += f"{i}. R$ {c['valor']:,.2f} ({c['tipo']}) - {c['horario']}\n"
    texto += f"\n💰 Total bruto: R$ {total:,.2f}"
    return texto

def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "❌ Nenhum comprovante pago ainda."
    total = sum(c["valor"] for c in pagos)
    texto = "✅ Comprovantes pagos:\n"
    for i, c in enumerate(pagos, 1):
        texto += f"{i}. R$ {c['valor']:,.2f} ({c['tipo']}) - {c['horario']}\n"
    texto += f"\n💸 Total bruto pago: R$ {total:,.2f}"
    return texto

def total_liquido():
    pendentes = [c for c in comprovantes if not c["pago"]]
    total = sum(c["liquido"] for c in pendentes)
    return f"💵 Total líquido a repassar: R$ {total:,.2f}"

def total_a_pagar():
    pendentes = [c for c in comprovantes if not c["pago"]]
    total = sum(c["valor"] for c in pendentes)
    return f"💸 Total bruto pendente: R$ {total:,.2f}"

def ajuda_comandos():
    return (
        "📌 *Comandos disponíveis:*\n\n"
        "💰 Envie o valor + 'pix' → calcula e registra com 0.2% de taxa\n"
        "💳 Envie valor + parcelas (ex: 3000 6x) → calcula com taxa de cartão\n"
        "✅ *pagamento feito* → marca o último como pago\n"
        "📋 *listar pendentes* → lista todos os comprovantes em aberto\n"
        "✅ *listar pagos* → mostra os já pagos\n"
        "📉 *total líquido* → valor com desconto da taxa\n"
        "💸 *total a pagar* → valor bruto pendente\n"
        "✍️ *solicitar pagamento* → registra um valor pago manualmente"
    )

def solicitar_pagamento(valor_str):
    valor = normalizar_valor(valor_str)
    if valor is None:
        return "❌ Valor inválido. Ex: 1000,00"
    comprovante = {
        "valor": valor,
        "tipo": "MANUAL",
        "parcelas": None,
        "liquido": valor,
        "horario": datetime.now().strftime("%H:%M"),
        "pago": True
    }
    comprovantes.append(comprovante)
    return f"📝 Pagamento de R$ {valor:,.2f} registrado manualmente como pago."
