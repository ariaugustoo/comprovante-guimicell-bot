def formatar_valor(valor_str):
    try:
        valor_str = valor_str.replace("r$", "").replace(",", ".").replace(" ", "")
        return float(valor_str)
    except:
        return None

def obter_taxa_cartao(parcelas):
    taxas = {
        "1x": 4.39, "2x": 5.19, "3x": 6.19, "4x": 6.59, "5x": 7.19,
        "6x": 8.29, "7x": 9.19, "8x": 9.99, "9x": 10.29, "10x": 10.88,
        "11x": 11.99, "12x": 12.52, "13x": 13.69, "14x": 14.19,
        "15x": 14.69, "16x": 15.19, "17x": 15.89, "18x": 16.84
    }
    return taxas.get(parcelas.lower())

def processar_pagamento(texto):
    partes = texto.lower().replace("r$", "").split()
    if "pix" in texto:
        valor = formatar_valor(partes[0])
        if valor:
            taxa = 0.2
            liquido = valor * (1 - taxa / 100)
            return f"📌 Valor bruto: R$ {valor:.2f}\n💸 Tipo: PIX (0.2%)\n✅ Valor líquido: R$ {liquido:.2f}"
        return "Valor inválido para PIX."

    for p in partes:
        if "x" in p:
            parcelas = p
            valor_str = partes[0]
            valor = formatar_valor(valor_str)
            taxa = obter_taxa_cartao(parcelas)
            if valor and taxa:
                liquido = valor * (1 - taxa / 100)
                return f"📌 Valor bruto: R$ {valor:.2f}\n💳 Parcelado em {parcelas.upper()} ({taxa:.2f}%)\n✅ Valor líquido: R$ {liquido:.2f}"
            return "Erro ao calcular cartão. Verifique o número de parcelas."
    return "Não entendi o formato. Exemplo: '7500 pix' ou '8999,90 10x'"

def calcular_total_liquido():
    return "💰 Total líquido dos comprovantes ainda não pagos: R$ 0,00"

def calcular_total_bruto():
    return "💰 Total bruto dos comprovantes pendentes: R$ 0,00"
