from datetime import datetime

comprovantes = []

def normalizar_valor(valor_str):
    try:
        valor_str = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
        return float(valor_str)
    except:
        return None

def detectar_pagamento(mensagem):
    return mensagem.strip().lower() == 'pagamento feito'

def marcar_como_pago():
    for comprovante in reversed(comprovantes):
        if not comprovante.get("pago", False):
            comprovante["pago"] = True
            return comprovante
    return None

def calcular_taxa(valor, parcelas, tipo):
    if tipo == 'pix':
        return 0.002  # 0,2%
    elif tipo == 'cartao':
        taxas_cartao = {
            1: 0.0439,  2: 0.0519,  3: 0.0619,  4: 0.0659,  5: 0.0719,
            6: 0.0829,  7: 0.0919,  8: 0.0999,  9: 0.1029, 10: 0.1088,
            11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
            16: 0.1519, 17: 0.1589, 18: 0.1684
        }
        return taxas_cartao.get(parcelas, 0)
    return 0

def processar_mensagem(mensagem):
    texto = mensagem.text.strip().lower()

    if detectar_pagamento(texto):
        comprovante = marcar_como_pago()
        if comprovante:
            return f"✅ Último comprovante marcado como pago: R$ {comprovante['valor_bruto']:.2f}"
        else:
            return "⚠️ Nenhum comprovante pendente encontrado para marcar como pago."

    if texto == 'total líquido':
        total = sum(c['valor_liquido'] for c in comprovantes if not c.get("pago", False))
        return f"💰 Total líquido dos comprovantes pendentes: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if texto == 'total a pagar':
        total = sum(c['valor_bruto'] for c in comprovantes if not c.get("pago", False))
        return f"💰 Total bruto dos comprovantes pendentes: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if texto == 'listar pendentes':
        pendentes = [c for c in comprovantes if not c.get("pago", False)]
        if not pendentes:
            return "✅ Nenhum comprovante pendente encontrado."
        resposta = "📄 *Comprovantes Pendentes:*\n\n"
        for c in pendentes:
            resposta += f"📌 R$ {c['valor_bruto']:.2f} - {c['parcelas']}x - {c['tipo']} - {c['horario']}\n"
        total = sum(c['valor_bruto'] for c in pendentes)
        resposta += f"\n💰 *Total bruto:* R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return resposta

    if texto == 'listar pagos':
        pagos = [c for c in comprovantes if c.get("pago", False)]
        if not pagos:
            return "📭 Nenhum pagamento foi registrado ainda."
        resposta = "📗 *Comprovantes Pagos:*\n\n"
        for c in pagos:
            resposta += f"✅ R$ {c['valor_bruto']:.2f} - {c['parcelas']}x - {c['tipo']} - {c['horario']}\n"
        total = sum(c['valor_bruto'] for c in pagos)
        resposta += f"\n💸 *Total pago:* R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return resposta

    if texto.startswith('solicitar pagamento'):
        try:
            partes = texto.split()
            valor_str = partes[-1]
            valor = normalizar_valor(valor_str)
            if valor:
                comprovantes.append({
                    "valor_bruto": valor,
                    "valor_liquido": valor,  # pagamento manual = sem taxa
                    "tipo": "manual",
                    "parcelas": 1,
                    "horario": datetime.now().strftime('%H:%M'),
                    "pago": True
                })
                return f"💸 Pagamento de R$ {valor:.2f} registrado e abatido do total pendente."
        except:
            return "❌ Erro ao processar o valor digitado. Use: `solicitar pagamento 100,00`"

    if texto == 'ajuda':
        return (
            "🧾 *Comandos disponíveis:*\n\n"
            "📥 Enviar comprovante:\n"
            "`1000,00 pix` ou `3000,00 6x`\n\n"
            "✅ *pagamento feito* — marca o último como pago\n"
            "💸 *total líquido* — mostra total a repassar\n"
            "💰 *total a pagar* — valor bruto dos pendentes\n"
            "📋 *listar pendentes* — lista todos pendentes\n"
            "📗 *listar pagos* — lista todos pagos\n"
            "🧾 *solicitar pagamento 100,00* — registra valor manual e abate"
        )

    partes = texto.split()
    if len(partes) == 2:
        valor_str, info = partes
        valor = normalizar_valor(valor_str)
        if valor:
            if info == "pix":
                taxa = calcular_taxa(valor, 1, 'pix')
                liquido = valor * (1 - taxa)
                comprovantes.append({
                    "valor_bruto": valor,
                    "valor_liquido": liquido,
                    "tipo": "pix",
                    "parcelas": 1,
                    "horario": datetime.now().strftime('%H:%M'),
                    "pago": False
                })
                return (
                    f"📄 Comprovante analisado:\n"
                    f"💰 Valor bruto: R$ {valor:,.2f}\n"
                    f"💳 Parcelas: 1x\n"
                    f"⏰ Horário: {datetime.now().strftime('%H:%M')}\n"
                    f"📉 Taxa aplicada: {taxa*100:.2f}%\n"
                    f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
                ).replace(",", "X").replace(".", ",").replace("X", ".")
            elif 'x' in info:
                try:
                    parcelas = int(info.replace("x", ""))
                    taxa = calcular_taxa(valor, parcelas, 'cartao')
                    liquido = valor * (1 - taxa)
                    comprovantes.append({
                        "valor_bruto": valor,
                        "valor_liquido": liquido,
                        "tipo": "cartao",
                        "parcelas": parcelas,
                        "horario": datetime.now().strftime('%H:%M'),
                        "pago": False
                    })
                    return (
                        f"📄 Comprovante analisado:\n"
                        f"💰 Valor bruto: R$ {valor:,.2f}\n"
                        f"💳 Parcelas: {parcelas}x\n"
                        f"⏰ Horário: {datetime.now().strftime('%H:%M')}\n"
                        f"📉 Taxa aplicada: {taxa*100:.2f}%\n"
                        f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
                    ).replace(",", "X").replace(".", ",").replace("X", ".")
                except:
                    pass

    return "❌ Formato inválido. Envie algo como '6438,90 pix' ou '7899,99 10x'."
