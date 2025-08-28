from datetime import datetime

# Tabela de taxas por número de parcelas no cartão
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

# Lista que armazena os comprovantes
comprovantes = []

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def processar_mensagem(texto):
    texto = texto.replace("r$", "").replace("reais", "").replace(",", ".").strip().lower()

    tipo_pagamento = None
    parcelas = 0
    valor = None

    if "pix" in texto:
        tipo_pagamento = "PIX"
        texto = texto.replace("pix", "").strip()
        try:
            valor = float(texto)
            taxa = 0.2
        except ValueError:
            return "❌ Valor inválido para PIX."
    elif "x" in texto:
        try:
            partes = texto.split("x")
            valor = float(partes[0].strip())
            parcelas = int(partes[1].strip())
            tipo_pagamento = f"Cartão {parcelas}x"
            taxa = taxas_cartao.get(parcelas)
            if taxa is None:
                return "❌ Número de parcelas inválido. Use de 1x a 18x."
        except (IndexError, ValueError):
            return "❌ Formato inválido. Use por exemplo: 1234,56 3x"
    else:
        return "❌ Formato inválido. Use por exemplo: 100 pix ou 1234,56 3x"

    valor_liquido = valor * (1 - taxa / 100)
    horario = datetime.now().strftime("%H:%M")

    comprovante = {
        "valor": valor,
        "tipo": tipo_pagamento,
        "parcelas": parcelas,
        "taxa": taxa,
        "liquido": valor_liquido,
        "horario": horario,
        "pago": False
    }
    comprovantes.append(comprovante)

    resposta = (
        "📄 *Comprovante analisado:*\n"
        f"💰 *Valor bruto:* {formatar_valor(valor)}\n"
        f"💰 *Tipo:* {tipo_pagamento}\n"
        f"⏰ *Horário:* {horario}\n"
        f"📉 *Taxa aplicada:* {taxa:.2f}%\n"
        f"✅ *Valor líquido a pagar:* {formatar_valor(valor_liquido)}"
    )
    return resposta

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."

    resposta = "*📋 Comprovantes Pendentes:*\n\n"
    total = 0
    for i, c in enumerate(pendentes, start=1):
        resposta += (
            f"{i}. 💰 {formatar_valor(c['valor'])} - {c['tipo']} - ⏰ {c['horario']} - "
            f"📉 {c['taxa']}% - ✅ {formatar_valor(c['liquido'])}\n"
        )
        total += c["liquido"]
    resposta += f"\n💵 *Total líquido a pagar:* {formatar_valor(total)}"
    return resposta

def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "📭 Nenhum comprovante marcado como pago."

    resposta = "*📬 Comprovantes Pagos:*\n\n"
    total = 0
    for i, c in enumerate(pagos, start=1):
        resposta += (
            f"{i}. 💰 {formatar_valor(c['valor'])} - {c['tipo']} - ⏰ {c['horario']} - "
            f"📉 {c['taxa']}% - ✅ {formatar_valor(c['liquido'])}\n"
        )
        total += c["liquido"]
    resposta += f"\n💸 *Total já pago:* {formatar_valor(total)}"
    return resposta

def registrar_pagamento():
    for c in comprovantes:
        if not c["pago"]:
            c["pago"] = True
            return f"✅ Pagamento registrado para {formatar_valor(c['liquido'])}."
    return "📭 Nenhum comprovante pendente para marcar como pago."

def total_liquido_pendente():
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    return f"💵 *Total líquido a pagar:* {formatar_valor(total)}"

def total_bruto_pendente():
    total = sum(c["valor"] for c in comprovantes if not c["pago"])
    return f"💰 *Total bruto (sem desconto):* {formatar_valor(total)}"
