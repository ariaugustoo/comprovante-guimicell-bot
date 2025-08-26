import datetime
import re

comprovantes = []

TAXAS_CARTAO = {
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
    18: 16.84
}

def aplicar_taxa(valor, taxa_percentual):
    return round(valor * (1 - taxa_percentual / 100), 2)

def parse_valor(texto):
    try:
        texto = texto.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        return float(re.findall(r'\d+(?:\.\d+)?', texto)[0])
    except:
        return None

def parse_parcelas(texto):
    match = re.search(r'(\d{1,2})x', texto.lower())
    if match:
        return int(match.group(1))
    return None

def processar_mensagem(texto, autor):
    texto = texto.lower()
    valor = parse_valor(texto)
    parcelas = parse_parcelas(texto)
    horario = datetime.datetime.now().strftime("%H:%M")
    tipo = "pix"
    taxa_aplicada = 0.2

    if "pix" in texto:
        tipo = "pix"
        taxa_aplicada = 0.2
    elif parcelas:
        tipo = f"{parcelas}x no cartão"
        taxa_aplicada = TAXAS_CARTAO.get(parcelas, 0)

    if valor is None:
        return "❌ Valor não identificado. Envie no formato: `1234,56 pix` ou `1234,56 3x`."

    valor_liquido = aplicar_taxa(valor, taxa_aplicada)

    comprovante = {
        "autor": autor,
        "valor_bruto": valor,
        "parcelas": parcelas if parcelas else 1,
        "tipo": tipo,
        "horario": horario,
        "taxa": taxa_aplicada,
        "valor_liquido": valor_liquido,
        "pago": False
    }
    comprovantes.append(comprovante)

    return (
        "📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {valor:,.2f}\n"
        f"💳 Tipo: {tipo}\n"
        f"⏰ Horário: {horario}\n"
        f"📉 Taxa aplicada: {taxa_aplicada}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )

def marcar_como_pago():
    for comprovante in reversed(comprovantes):
        if not comprovante["pago"]:
            comprovante["pago"] = True
            return "✅ Comprovante marcado como pago!"
    return "Nenhum comprovante pendente encontrado."

def listar_pendentes():
    if not any(not c["pago"] for c in comprovantes):
        return "✅ Nenhum comprovante pendente."
    texto = "📋 *Comprovantes Pendentes:*\n"
    for i, c in enumerate(comprovantes):
        if not c["pago"]:
            texto += f"{i+1}. R$ {c['valor_liquido']:.2f} - {c['tipo']} - {c['horario']}\n"
    return texto

def listar_pagos():
    if not any(c["pago"] for c in comprovantes):
        return "📄 Nenhum comprovante pago ainda."
    texto = "✅ *Comprovantes Pagos:*\n"
    for i, c in enumerate(comprovantes):
        if c["pago"]:
            texto += f"{i+1}. R$ {c['valor_liquido']:.2f} - {c['tipo']} - {c['horario']}\n"
    return texto

def total_geral():
    total = sum(c["valor_liquido"] for c in comprovantes)
    return f"📊 Total geral (pagos + pendentes): R$ {total:,.2f}"

def total_que_devo():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    return f"📌 Total que ainda deve ser pago: R$ {total:,.2f}"

def ultimo_comprovante():
    if not comprovantes:
        return "Nenhum comprovante enviado ainda."
    c = comprovantes[-1]
    return (
        "📄 *Último Comprovante:*\n"
        f"💰 Valor bruto: R$ {c['valor_bruto']:,.2f}\n"
        f"💳 Tipo: {c['tipo']}\n"
        f"⏰ Horário: {c['horario']}\n"
        f"📉 Taxa aplicada: {c['taxa']}%\n"
        f"✅ Valor líquido: R$ {c['valor_liquido']:,.2f}\n"
        f"📌 Status: {'✅ Pago' if c['pago'] else '❌ Pendente'}"
    )
