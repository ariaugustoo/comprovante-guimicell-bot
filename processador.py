from datetime import datetime
import pytz
import re

# Armazenamento em memória (para testes)
comprovantes = []
pagamentos = []
solicitacoes = []

# Taxas por tipo de pagamento
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}
taxa_pix = 0.20

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_horario_brasilia():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso).strftime('%H:%M')

def normalizar_valor(texto):
    texto = texto.replace("R$", "").replace(" ", "")
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except:
        return None

def calcular_valor_liquido(valor, tipo):
    if tipo.lower() == "pix":
        taxa = taxa_pix
    elif "x" in tipo.lower():
        parcelas = int(re.sub(r'\D', '', tipo))
        taxa = taxas_cartao.get(parcelas, 0)
    else:
        return None, None
    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def processar_mensagem(texto, user_id):
    texto = texto.lower().strip()

    if "pix" in texto or "x" in texto:
        valor = normalizar_valor(texto)
        tipo = "pix" if "pix" in texto else texto
        if not valor:
            return "❌ Valor inválido. Envie no formato: 1000,00 pix ou 2000,00 10x"

        liquido, taxa = calcular_valor_liquido(valor, tipo)
        if liquido is None:
            return "❌ Tipo de pagamento inválido."

        comprovantes.append({
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "tipo": "PIX" if "pix" in tipo else tipo.upper(),
            "hora": get_horario_brasilia()
        })

        return f"""📄 Comprovante analisado:
💰 Valor bruto: {formatar_valor(valor)}
💰 Tipo: {'PIX' if 'pix' in tipo else tipo.upper()}
⏰ Horário: {get_horario_brasilia()}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: {formatar_valor(liquido)}"""

    if texto == "total liquido":
        pendente = sum(c["valor_liquido"] for c in comprovantes) - sum(p["valor"] for p in pagamentos)
        return f"💰 Valor líquido disponível: {formatar_valor(pendente)}"

    if texto == "pagamentos realizados":
        total = sum(p["valor"] for p in pagamentos)
        return f"✅ Total pago até agora: {formatar_valor(total)}"

    if texto == "fechamento do dia":
        total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "PIX")
        total_cartao = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] != "PIX")
        total_pago = sum(p["valor"] for p in pagamentos)
        pendente = total_pix + total_cartao - total_pago
        return f"""📅 Fechamento do Dia:

💳 Total Cartão: {formatar_valor(total_cartao)}
💸 Total PI.: {formatar_valor(total_pix)}
✅ Total Pago: {formatar_valor(total_pago)}
📌 Total Pendente: {formatar_valor(pendente)}"""

    if texto.startswith("solicito"):
        valor = normalizar_valor(texto)
        if not valor:
            return "❌ Valor inválido para solicitação."

        credito = sum(c["valor_liquido"] for c in comprovantes) - sum(p["valor"] for p in pagamentos)
        if valor > credito:
            return f"❌ Solicitação maior que o crédito disponível: {formatar_valor(credito)}"

        solicitacoes.append({"valor": valor})
        return f"📢 Solicitação de pagamento registrada: {formatar_valor(valor)}.\nAguardando confirmação com 'pagamento feito'."

    if "pagamento feito" in texto:
        valor = normalizar_valor(texto)
        if valor is None:
            # Se não tem valor, usa o último valor solicitado
            if not solicitacoes:
                return "❌ Nenhuma solicitação de pagamento encontrada."
            valor = solicitacoes.pop(0)["valor"]
        else:
            # Se tem valor, tira da fila o equivalente
            for s in solicitacoes:
                if s["valor"] == valor:
                    solicitacoes.remove(s)
                    break

        credito = sum(c["valor_liquido"] for c in comprovantes) - sum(p["valor"] for p in pagamentos)
        if valor > credito:
            return f"❌ O pagamento de {formatar_valor(valor)} excede o crédito disponível: {formatar_valor(credito)}"

        saldo_anterior = credito
        novo_saldo = round(credito - valor, 2)
        pagamentos.append({"valor": valor})

        return f"""✅ Pagamento registrado com sucesso.
💵 Valor: {formatar_valor(valor)}
📉 Saldo anterior: {formatar_valor(saldo_anterior)}
💰 Novo saldo disponível: {formatar_valor(novo_saldo)}"""

    if texto == "limpar tudo" and user_id == int(os.getenv("ADMIN_ID")):
        comprovantes.clear()
        pagamentos.clear()
        solicitacoes.clear()
        return "🧹 Todos os dados foram zerados com sucesso."

    if texto == "corrigir valor" and user_id == int(os.getenv("ADMIN_ID")):
        return "⚠️ Função de correção ainda não implementada."

    if texto == "ajuda":
        return """🤖 *Comandos disponíveis*:

📥 Enviar comprovante:
`1000,00 pix` ou `2000,00 10x`

📤 Solicitar pagamento:
`solicito 300,00`

✅ Confirmar pagamento:
`pagamento feito` ou `pagamento feito 300,00`

📊 Consultas:
• total liquido
• pagamentos realizados
• fechamento do dia

🔒 Admin:
• limpar tudo
• corrigir valor
"""

    return None
