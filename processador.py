from datetime import datetime, timedelta
import pytz

comprovantes = []
pagamentos_parciais = []

taxas_cartao = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659,
    5: 0.0719, 6: 0.0829, 7: 0.0919, 8: 0.0999,
    9: 0.1029, 10: 0.1088, 11: 0.1199, 12: 0.1252,
    13: 0.1369, 14: 0.1419, 15: 0.1469, 16: 0.1519,
    17: 0.1589, 18: 0.1684
}
taxa_pix = 0.002  # 0,2%

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def obter_horario_brasilia():
    fuso_brasilia = pytz.timezone("America/Sao_Paulo")
    return datetime.now(fuso_brasilia).strftime("%H:%M")

def processar_mensagem(mensagem):
    try:
        texto = mensagem.lower().replace("r$", "").replace("reais", "").strip()
        valor = None
        parcelas = 1
        tipo = None

        if "pix" in texto:
            tipo = "PIX"
            texto = texto.replace("pix", "").strip()
            valor = float(texto.replace(".", "").replace(",", "."))

        elif "x" in texto:
            tipo = "Cartão"
            partes = texto.split("x")
            if len(partes) == 2:
                valor_str, parcelas_str = partes
                valor = float(valor_str.replace(".", "").replace(",", "."))
                parcelas = int(parcelas_str.strip())

        if valor is None or tipo is None:
            return None

        if tipo == "PIX":
            taxa = taxa_pix
        else:
            taxa = taxas_cartao.get(parcelas, 0)

        valor_liquido = valor * (1 - taxa)

        comprovantes.append({
            "valor": valor,
            "tipo": tipo,
            "parcelas": parcelas,
            "taxa": taxa,
            "valor_liquido": valor_liquido,
            "horario": obter_horario_brasilia(),
            "pago": False
        })

        return (
            "📄 Comprovante analisado:\n"
            f"💰 Valor bruto: {formatar_valor(valor)}\n"
            f"💳 Tipo: {tipo} ({parcelas}x)\n" if tipo == "Cartão" else f"💳 Tipo: {tipo}\n"
            f"⏰ Horário: {comprovantes[-1]['horario']}\n"
            f"📉 Taxa aplicada: {taxa*100:.2f}%\n"
            f"✅ Valor líquido a pagar: {formatar_valor(valor_liquido)}"
        )

    except Exception as e:
        return f"⚠️ Erro ao processar o comprovante. Verifique o formato e tente novamente.\n{e}"

def marcar_como_pago():
    for c in comprovantes:
        if not c['pago']:
            c['pago'] = True
            return "✅ Pagamento marcado com sucesso!"
    return "⚠️ Nenhum comprovante pendente encontrado."

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c['pago']]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."
    resposta = "📋 *Comprovantes Pendentes:*\n"
    for c in pendentes:
        resposta += f"- {formatar_valor(c['valor_liquido'])} ({c['tipo']}) ⏰ {c['horario']}\n"
    resposta += f"\n💰 Total pendente: {formatar_valor(sum(c['valor_liquido'] for c in pendentes))}"
    return resposta

def listar_pagamentos():
    pagos = [c for c in comprovantes if c['pago']]
    if not pagos:
        return "❌ Nenhum pagamento realizado ainda."
    resposta = "📗 *Pagamentos Realizados:*\n"
    for c in pagos:
        resposta += f"- {formatar_valor(c['valor_liquido'])} ({c['tipo']}) ⏰ {c['horario']}\n"
    resposta += f"\n💸 Total pago: {formatar_valor(sum(c['valor_liquido'] for c in pagos))}"
    return resposta

def total_pendente_liquido():
    return sum(c["valor_liquido"] for c in comprovantes if not c["pago"])

def total_bruto_pendente():
    return sum(c["valor"] for c in comprovantes if not c["pago"])

def registrar_pagamento_parcial(valor):
    saldo = total_pendente_liquido()
    if saldo <= 0:
        return "✅ Nenhum valor pendente no momento."

    if valor > saldo:
        return f"⚠️ O valor pago excede o saldo pendente ({formatar_valor(saldo)}). Tente novamente."

    restante = valor
    for c in comprovantes:
        if not c["pago"]:
            if c["valor_liquido"] <= restante:
                restante -= c["valor_liquido"]
                c["pago"] = True
            else:
                c["valor_liquido"] -= restante
                c["valor"] = c["valor_liquido"] / (1 - c["taxa"])
                restante = 0
            if restante <= 0:
                break
    pagamentos_parciais.append(valor)
    return f"✅ Pagamento parcial de {formatar_valor(valor)} registrado com sucesso."

def solicitar_pagamento(valor, chave_pix):
    saldo = total_pendente_liquido()
    if saldo <= 0:
        return "✅ Nenhum valor disponível para solicitar no momento."

    if valor > saldo:
        return f"⚠️ Valor solicitado ({formatar_valor(valor)}) excede o saldo disponível ({formatar_valor(saldo)})."

    return (
        "📩 *Solicitação de Pagamento Recebida:*\n"
        f"💰 Valor solicitado: {formatar_valor(valor)}\n"
        f"🔑 Chave Pix: `{chave_pix}`\n\n"
        "💬 Envie o comprovante após o pagamento com a mensagem 'pagamento feito' para abater este valor."
    )

def gerar_status():
    total_pago = sum(c['valor_liquido'] for c in comprovantes if c['pago'])
    total_pendente = sum(c['valor_liquido'] for c in comprovantes if not c['pago'])
    total_pix = sum(c['valor_liquido'] for c in comprovantes if c['tipo'] == 'PIX')
    total_cartao = sum(c['valor_liquido'] for c in comprovantes if c['tipo'] == 'Cartão')

    return (
        "📊 *Fechamento do Dia:*\n"
        f"💳 Total em Cartão: {formatar_valor(total_cartao)}\n"
        f"💵 Total em Pix: {formatar_valor(total_pix)}\n"
        f"✅ Total Pago: {formatar_valor(total_pago)}\n"
        f"⏳ Total Pendente: {formatar_valor(total_pendente)}"
    )
