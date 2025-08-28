from datetime import datetime, timedelta
import pytz
import re

# Timezone de Brasília
tz = pytz.timezone('America/Sao_Paulo')

comprovantes = []
pagamentos = []
solicitacoes = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19,
    15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def normalizar_valor(valor):
    valor = valor.replace('.', '').replace(',', '.')
    return float(valor)

def processar_mensagem(mensagem):
    texto = mensagem.text.lower()
    agora = datetime.now(tz).strftime('%H:%M')

    # PIX
    if "pix" in texto:
        match = re.search(r'([\d\.,]+)\s*pix', texto)
        if match:
            valor = normalizar_valor(match.group(1))
            taxa = 0.2
            valor_liquido = valor * (1 - taxa / 100)
            comprovantes.append({
                "valor_bruto": valor,
                "tipo": "PIX",
                "horario": agora,
                "taxa": taxa,
                "valor_liquido": valor_liquido,
                "pago": False
            })
            return f"""📄 Comprovante analisado:
💰 Valor bruto: R$ {valor:,.2f}
💰 Tipo: PIX
⏰ Horário: {agora}
📉 Taxa aplicada: {taxa}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}""".replace(",", "X").replace(".", ",").replace("X", ".")

    # Cartão
    match = re.search(r'([\d\.,]+)\s*(\d{1,2})x', texto)
    if match:
        valor = normalizar_valor(match.group(1))
        parcelas = int(match.group(2))
        if parcelas in taxas_cartao:
            taxa = taxas_cartao[parcelas]
            valor_liquido = valor * (1 - taxa / 100)
            comprovantes.append({
                "valor_bruto": valor,
                "tipo": f"{parcelas}x",
                "horario": agora,
                "taxa": taxa,
                "valor_liquido": valor_liquido,
                "pago": False
            })
            return f"""📄 Comprovante analisado:
💰 Valor bruto: R$ {valor:,.2f}
💰 Tipo: Cartão ({parcelas}x)
⏰ Horário: {agora}
📉 Taxa aplicada: {taxa}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}""".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return "❌ Erro ao calcular parcelas."

    # Pagamento feito
    if texto.startswith("pagamento feito"):
        try:
            valor = normalizar_valor(texto.split("feito")[1].strip())
            pagamentos.append(valor)
            return "✅ Pagamento registrado com sucesso."
        except:
            return "❌ Valor inválido. Use: pagamento feito 300,00"

    if texto == "quanto devo":
        total = sum(c['valor_liquido'] for c in comprovantes if not c['pago']) - sum(pagamentos)
        if total < 0:
            total = 0.00
        return f"💰 Devo ao lojista: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if texto == "total a pagar":
        total_bruto = sum(c['valor_bruto'] for c in comprovantes if not c['pago'])
        return f"💰 Valor bruto total pendente: R$ {total_bruto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if texto == "listar pendentes":
        pendentes = [c for c in comprovantes if not c['pago']]
        if not pendentes:
            return "📂 Nenhum comprovante pendente."
        resposta = "📋 Comprovantes Pendentes:\n"
        for c in pendentes:
            resposta += f"- 💰 R$ {c['valor_liquido']:,.2f} | {c['tipo']} | ⏰ {c['horario']}\n"
        return resposta.replace(",", "X").replace(".", ",").replace("X", ".")

    if texto == "listar pagos":
        pagos = [c for c in comprovantes if c['pago']]
        if not pagos:
            return "📂 Nenhum comprovante pago ainda."
        resposta = "✅ Comprovantes Pagos:\n"
        for c in pagos:
            resposta += f"- 💰 R$ {c['valor_liquido']:,.2f} | {c['tipo']} | ⏰ {c['horario']}\n"
        return resposta.replace(",", "X").replace(".", ",").replace("X", ".")

    if texto == "solicitar pagamento":
        solicitacoes.append({"status": "aguardando_valor"})
        return "Digite o valor que deseja solicitar (ex: 300,00):"

    if solicitacoes and solicitacoes[-1]["status"] == "aguardando_valor":
        try:
            valor = normalizar_valor(texto)
            solicitacoes[-1]["valor"] = valor
            solicitacoes[-1]["status"] = "aguardando_chave"
            return "Agora envie a chave Pix para o pagamento:"
        except:
            return "❌ Comando inválido ou valor não reconhecido."

    if solicitacoes and solicitacoes[-1]["status"] == "aguardando_chave":
        solicitacoes[-1]["chave"] = texto
        solicitacoes[-1]["status"] = "completo"
        valor = solicitacoes[-1]["valor"]
        chave = solicitacoes[-1]["chave"]
        return f"""📩 Solicitação de Pagamento Recebida:
💰 Valor solicitado: R$ {valor:,.2f}
🔑 Chave Pix: {chave}
⏳ Aguardando pagamento...""".replace(",", "X").replace(".", ",").replace("X", ".")

    return "❌ Comando inválido ou valor não reconhecido."
