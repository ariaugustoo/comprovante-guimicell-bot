import re
from datetime import datetime, timedelta

comprovantes = []
pagamentos_realizados = []
solicitacoes_pagamento = []

# Tabela de taxas
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}

def normalizar_valor(valor_str):
    valor_str = valor_str.replace('.', '').replace(',', '.')
    try:
        return float(valor_str)
    except ValueError:
        return None

def calcular_taxa(valor, tipo, parcelas=1):
    if tipo == 'PIX':
        taxa = 0.2
    else:
        taxa = taxas_cartao.get(parcelas, 0)
    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def formatar_resposta(valor, tipo, parcelas, taxa, valor_liquido):
    horario = datetime.now().strftime('%H:%M')
    return (
        f"📄 *Comprovante analisado:*\n"
        f"💰 *Valor bruto:* R$ {valor:,.2f}\n"
        f"💳 *Tipo:* {tipo} {'- ' + str(parcelas) + 'x' if tipo == 'Cartão' else ''}\n"
        f"⏰ *Horário:* {horario}\n"
        f"📉 *Taxa aplicada:* {taxa}%\n"
        f"✅ *Valor líquido a pagar:* R$ {valor_liquido:,.2f}"
    )

def registrar_comprovante(valor, tipo, parcelas, valor_liquido, taxa):
    comprovantes.append({
        "valor": valor,
        "tipo": tipo,
        "parcelas": parcelas,
        "valor_liquido": valor_liquido,
        "horario": datetime.now(),
        "pago": False,
        "taxa": taxa
    })

def processar_mensagem(mensagem, user_id):
    mensagem = mensagem.lower()

    if 'pix' in mensagem:
        match = re.search(r'([\d.,]+)\s*pix', mensagem)
        if match:
            valor = normalizar_valor(match.group(1))
            if valor is not None:
                valor_liquido, taxa = calcular_taxa(valor, 'PIX')
                registrar_comprovante(valor, 'PIX', 1, valor_liquido, taxa)
                return formatar_resposta(valor, 'PIX', 1, taxa, valor_liquido)

    elif 'x' in mensagem:
        match = re.search(r'([\d.,]+)\s*(\d{1,2})x', mensagem)
        if match:
            valor = normalizar_valor(match.group(1))
            parcelas = int(match.group(2))
            if valor is not None:
                valor_liquido, taxa = calcular_taxa(valor, 'Cartão', parcelas)
                registrar_comprovante(valor, 'Cartão', parcelas, valor_liquido, taxa)
                return formatar_resposta(valor, 'Cartão', parcelas, taxa, valor_liquido)

    elif mensagem.startswith("pagamento feito"):
        valor_match = re.search(r'([\d.,]+)', mensagem)
        if valor_match:
            valor_pago = normalizar_valor(valor_match.group(1))
            return registrar_pagamento(valor_pago)
        else:
            return registrar_pagamento()

    elif mensagem == "quanto devo":
        total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        return f"💰 *Devo ao lojista:* R$ {total:,.2f}"

    elif mensagem == "total a pagar":
        total = sum(c["valor"] for c in comprovantes if not c["pago"])
        return f"💰 *Total bruto dos pendentes:* R$ {total:,.2f}"

    elif mensagem == "listar pendentes":
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            return "✅ Nenhum comprovante pendente."
        texto = "*📋 Comprovantes pendentes:*\n"
        for c in pendentes:
            texto += (
                f"• R$ {c['valor']:,.2f} | {c['tipo']} {f'{c['parcelas']}x' if c['tipo'] == 'Cartão' else ''} | "
                f"💸 Líquido: R$ {c['valor_liquido']:,.2f}\n"
            )
        return texto

    elif mensagem == "listar pagos":
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            return "🔎 Nenhum comprovante marcado como pago ainda."
        texto = "*✅ Comprovantes pagos:*\n"
        for c in pagos:
            texto += (
                f"• R$ {c['valor']:,.2f} | {c['tipo']} {f'{c['parcelas']}x' if c['tipo'] == 'Cartão' else ''} | "
                f"💸 Líquido: R$ {c['valor_liquido']:,.2f}\n"
            )
        return texto

    elif mensagem == "ajuda":
        return (
            "🧾 *Comandos disponíveis:*\n\n"
            "• `1000 pix` → registra comprovante via Pix\n"
            "• `3000 6x` → registra cartão em 6x\n"
            "• `pagamento feito` → marca como pago\n"
            "• `pagamento feito 300` → pagamento parcial de R$300\n"
            "• `quanto devo` → mostra total líquido pendente\n"
            "• `total a pagar` → total bruto pendente\n"
            "• `listar pendentes` → lista os não pagos\n"
            "• `listar pagos` → lista os pagos\n"
            "• `ajuda` → mostra esse menu"
        )

    return "❗ Comando não reconhecido. Envie algo como `1500 pix` ou `2000 10x`. Use `ajuda` para ver os comandos."

def registrar_pagamento(valor_pago=None):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."

    total_pendente = sum(c["valor_liquido"] for c in pendentes)

    if valor_pago is None or valor_pago >= total_pendente:
        for c in pendentes:
            c["pago"] = True
        return "✅ Todos os comprovantes pendentes foram marcados como pagos."

    restante = valor_pago
    for c in pendentes:
        if not c["pago"]:
            if restante >= c["valor_liquido"]:
                restante -= c["valor_liquido"]
                c["pago"] = True
            else:
                c["valor_liquido"] -= restante
                restante = 0
                break

    return f"✅ Pagamento parcial de R$ {valor_pago:,.2f} registrado. Saldo restante será mantido como pendente."