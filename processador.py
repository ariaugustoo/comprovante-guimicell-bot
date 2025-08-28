comprovantes = []

def normalizar_valor(valor_str):
    try:
        valor_str = valor_str.replace("R$", "").replace(",", ".").replace(" ", "")
        valor_str = ''.join(c for c in valor_str if c.isdigit() or c == '.')
        return round(float(valor_str), 2)
    except:
        return None

def extrair_info_pagamento(mensagem):
    mensagem = mensagem.lower()
    if "pix" in mensagem:
        tipo = "pix"
        valor = normalizar_valor(mensagem)
        parcelas = None
    elif "x" in mensagem:
        tipo = "cartao"
        partes = mensagem.split("x")
        valor = normalizar_valor(partes[0])
        try:
            parcelas = int(partes[1].strip())
        except:
            parcelas = 1
    else:
        tipo = None
        valor = normalizar_valor(mensagem)
        parcelas = None

    return valor, tipo, parcelas

def calcular_taxa(tipo, parcelas):
    if tipo == "pix":
        return 0.002
    elif tipo == "cartao":
        taxas_cartao = {
            1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719,
            6: 0.0829, 7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088,
            11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
            16: 0.1519, 17: 0.1589, 18: 0.1684
        }
        return taxas_cartao.get(parcelas, 0)
    else:
        return 0

def calcular_valor_liquido(valor, taxa):
    if valor is None:
        return 0.0
    return round(valor * (1 - taxa), 2)

def processar_mensagem(texto):
    global comprovantes
    valor, tipo, parcelas = extrair_info_pagamento(texto)
    if valor is None or tipo is None:
        return "❌ Não consegui entender o comprovante. Envie no formato:\n\n👉 `1000 pix` ou `2500 6x`"

    taxa = calcular_taxa(tipo, parcelas)
    valor_liquido = calcular_valor_liquido(valor, taxa)

    comprovantes.append({
        "valor_bruto": valor,
        "tipo": tipo,
        "parcelas": parcelas,
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "pago": False
    })

    msg = (
        "📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {valor:,.2f}\n"
        f"💳 Tipo: {'PIX' if tipo == 'pix' else f'{parcelas}x'}\n"
        f"📉 Taxa aplicada: {taxa*100:.2f}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )
    return msg

def marcar_como_pago():
    for c in comprovantes:
        if not c["pago"]:
            c["pago"] = True
            return "✅ Último comprovante marcado como pago."
    return "⚠️ Nenhum comprovante pendente encontrado."

def comando_total_liquido():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    return f"💰 *Total líquido a pagar:* R$ {total:,.2f}"

def comando_total_bruto():
    total = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
    return f"📊 *Total bruto (sem desconto):* R$ {total:,.2f}"

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."

    linhas = []
    for c in pendentes:
        linha = f"📄 {c['valor_bruto']:,.2f} | {'PIX' if c['parcelas'] is None else f\"{c['parcelas']}x\"} | R$ {c['valor_liquido']:,.2f}"
        linhas.append(linha)

    total = sum(c["valor_liquido"] for c in pendentes)
    return "*🧾 Comprovantes Pendentes:*\n" + "\n".join(linhas) + f"\n\n💰 *Total líquido:* R$ {total:,.2f}"

def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "⚠️ Nenhum comprovante marcado como pago ainda."

    linhas = []
    for c in pagos:
        linha = f"✅ {c['valor_bruto']:,.2f} | {'PIX' if c['parcelas'] is None else f\"{c['parcelas']}x\"} | R$ {c['valor_liquido']:,.2f}"
        linhas.append(linha)

    total = sum(c["valor_liquido"] for c in pagos)
    return "*✅ Comprovantes Pagos:*\n" + "\n".join(linhas) + f"\n\n💰 *Total pago:* R$ {total:,.2f}"

def solicitar_pagamento_manual(valor_manual):
    try:
        valor = normalizar_valor(valor_manual)
        if valor is None:
            return "❌ Valor inválido. Envie no formato: `1234,56` ou `1234.56`"

        comprovantes.append({
            "valor_bruto": valor,
            "tipo": "manual",
            "parcelas": None,
            "taxa": 0.0,
            "valor_liquido": valor,
            "pago": True
        })

        return f"✅ Valor manual de R$ {valor:,.2f} registrado como *pago*."
    except:
        return "❌ Erro ao processar valor manual."
