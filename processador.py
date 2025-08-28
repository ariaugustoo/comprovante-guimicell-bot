import re

comprovantes = []

TAXA_PIX = 0.002
TAXAS_CARTAO = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719,
    6: 0.0829, 7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088,
    11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
    16: 0.1519, 17: 0.1589, 18: 0.1684
}

def normalizar_valor(valor):
    valor = valor.replace('.', '').replace(',', '.')
    return float(re.findall(r'\d+\.\d+|\d+', valor)[0])

def processar_mensagem(mensagem):
    valor = normalizar_valor(mensagem)
    if "pix" in mensagem:
        taxa = TAXA_PIX
        tipo = "PIX"
        parcelas = None
    else:
        parcelas = int(re.search(r'(\d{1,2})x', mensagem).group(1))
        taxa = TAXAS_CARTAO.get(parcelas, 0)
        tipo = f"Cartão {parcelas}x"

    valor_liquido = round(valor * (1 - taxa), 2)

    comprovantes.append({
        "valor": valor,
        "parcelas": parcelas,
        "taxa": taxa,
        "liquido": valor_liquido,
        "pago": False
    })

    return (
        f"📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {valor:,.2f}\n"
        f"💳 Tipo: {tipo}\n"
        f"📉 Taxa aplicada: {taxa * 100:.2f}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )

def marcar_como_pago():
    for comp in reversed(comprovantes):
        if not comp["pago"]:
            comp["pago"] = True
            return "✅ Último comprovante marcado como *pago*."
    return "Nenhum comprovante pendente encontrado."

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."
    texto = "📌 *Comprovantes Pendentes:*\n"
    total = 0
    for i, c in enumerate(pendentes, 1):
        texto += f"{i}. R$ {c['valor']:.2f} ({'PIX' if c['parcelas'] is None else f'{c['parcelas']}x'})\n"
        total += c["valor"]
    texto += f"\n💰 *Total bruto pendente:* R$ {total:.2f}"
    return texto

def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "📭 Nenhum comprovante foi pago ainda."
    texto = "📬 *Comprovantes Pagos:*\n"
    total = 0
    for i, c in enumerate(pagos, 1):
        texto += f"{i}. R$ {c['valor']:.2f} ({'PIX' if c['parcelas'] is None else f'{c['parcelas']}x'})\n"
        total += c["valor"]
    texto += f"\n✅ *Total pago:* R$ {total:.2f}"
    return texto

def mostrar_ajuda():
    return (
        "📌 *Comandos disponíveis:*\n\n"
        "• `1000 pix` → calcula valor líquido com taxa de PIX\n"
        "• `3000 6x` → calcula valor líquido com taxa de cartão\n"
        "• `pagamento feito` → marca último comprovante como pago\n"
        "• `listar pendentes` → lista todos os pendentes\n"
        "• `listar pagos` → lista os pagos\n"
        "• `total líquido` → soma líquida dos pendentes\n"
        "• `total a pagar` → soma bruta dos pendentes\n"
        "• `solicitar pagamento` → digite valor manual para registrar"
    )

def solicitar_pagamento():
    return "Digite o valor do pagamento (ex: `2500 pix` ou `3000 3x`) para registrar manualmente."

def total_liquido():
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    return f"💰 *Total líquido a pagar:* R$ {total:.2f}"

def total_bruto():
    total = sum(c["valor"] for c in comprovantes if not c["pago"])
    return f"💵 *Total bruto a pagar:* R$ {total:.2f}"
