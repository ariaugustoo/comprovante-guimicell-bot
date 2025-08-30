from datetime import datetime
import pytz
import re
import os
import shlex

# Armazenamento em memória
comprovantes = []
pagamentos = []
solicitacoes = []

# Taxas cobradas do lojista (em ordem das parcelas)
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}
taxa_pix = 0.20  # Taxa cobrada do lojista no Pix

# Suas taxas reais (em ordem das parcelas)
taxas_reais_cartao = {
    1: 3.28, 2: 3.96, 3: 4.68, 4: 5.40, 5: 6.12,
    6: 6.84, 7: 7.72, 8: 8.44, 9: 9.16, 10: 9.88,
    11: 10.60, 12: 11.32, 13: 12.04, 14: 12.76, 15: 13.48,
    16: 14.20, 17: 14.92, 18: 15.64
}
taxa_real_pix = 0.00  # Sua taxa real no Pix

def formatar_valor(valor):
    try:
        valor = float(valor)
    except Exception:
        valor = 0.0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_horario_brasilia():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso).strftime('%H:%M')

def normalizar_valor(texto):
    texto = re.sub(r'[^\d,\.]', '', texto)
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", "")
    try:
        return float(texto)
    except Exception:
        return None

def extrair_valor_tipo(texto):
    texto = texto.lower().strip()
    match = re.match(r"^(\d{1,3}(?:\.\d{3})*,\d{2}|\d+(?:,\d{2})?)\s*(pix|\d{1,2}x)$", texto)
    if match:
        valor, tipo = match.groups()
        return normalizar_valor(valor), tipo
    match = re.match(r"^(pix|\d{1,2}x)\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+(?:,\d{2})?)$", texto)
    if match:
        tipo, valor = match.groups()
        return normalizar_valor(valor), tipo
    return None, None

def calcular_valor_liquido(valor, tipo):
    tipo = tipo.lower()
    if tipo == "pix":
        taxa = taxa_pix
    elif "x" in tipo:
        parcelas = int(re.sub(r'\D', '', tipo))
        taxa = taxas_cartao.get(parcelas, 0)
        if taxa == 0:
            return None, None
    else:
        return None, None
    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def credito_disponivel():
    return round(sum(c["valor_liquido"] for c in comprovantes) - sum(p["valor"] for p in pagamentos), 2)

def fechar_dia_e_zerar_saldos():
    pendente = credito_disponivel()
    comprovantes.clear()
    pagamentos.clear()
    solicitacoes.clear()
    # Mantém saldo pendente como "PENDENTE" apenas se houver
    if pendente > 0:
        comprovantes.append({
            "valor_bruto": pendente,
            "valor_liquido": pendente,
            "tipo": "PENDENTE",
            "hora": get_horario_brasilia()
        })
    return f"✅ Fechamento realizado. Saldos de Cartão e Pix zerados. Saldo pendente mantido: {formatar_valor(pendente)}."

def corrigir_comprovante(indice, valor_txt, tipo_txt):
    try:
        indice = int(indice) - 1
        if indice < 0 or indice >= len(comprovantes):
            return "❌ Índice de comprovante inválido."
        valor = normalizar_valor(valor_txt)
        if valor is None:
            return "❌ Valor inválido."
        liquido, taxa = calcular_valor_liquido(valor, tipo_txt)
        if liquido is None:
            return "❌ Tipo de pagamento inválido."
        comprovantes[indice] = {
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "tipo": "PIX" if tipo_txt.lower() == "pix" else tipo_txt.upper(),
            "hora": get_horario_brasilia()
        }
        return f"""✅ Comprovante corrigido!
Novo valor bruto: {formatar_valor(valor)}
Novo tipo: {'PIX' if tipo_txt.lower() == 'pix' else tipo_txt.upper()}
Nova taxa: {taxa:.2f}%
Novo valor líquido: {formatar_valor(liquido)}
"""
    except Exception as e:
        return f"❌ Erro ao corrigir comprovante: {str(e)}"

def listar_comprovantes():
    if not comprovantes:
        return "📋 Nenhum comprovante cadastrado."
    linhas = ["📋 Comprovantes cadastrados:"]
    for idx, c in enumerate(comprovantes, start=1):
        linhas.append(
            f"[{idx}] {formatar_valor(c['valor_bruto'])} - {c['tipo']} - Líquido: {formatar_valor(c['valor_liquido'])} - Hora: {c['hora']}"
        )
    return "\n".join(linhas)

def relatorio_lucro():
    total_bruto_pix = total_bruto_cartao = 0.0
    total_liquido_pix = total_liquido_cartao = 0.0
    total_lucro_pix = total_lucro_cartao = 0.0

    for c in comprovantes:
        valor = c["valor_bruto"]
        tipo = c["tipo"]
        liquido_loja = c["valor_liquido"]

        if tipo == "PIX":
            taxa_loja = taxa_pix
            taxa_maquina = taxa_real_pix
            lucro_pix = valor * (taxa_loja - taxa_maquina) / 100
            total_bruto_pix += valor
            total_liquido_pix += liquido_loja
            total_lucro_pix += lucro_pix
        elif "X" in tipo:
            try:
                parcelas = int(re.sub(r'\D', '', tipo))
                taxa_loja = taxas_cartao.get(parcelas, 0)
                taxa_maquina = taxas_reais_cartao.get(parcelas, 0)
                lucro_cartao = valor * (taxa_loja - taxa_maquina) / 100
                total_bruto_cartao += valor
                total_liquido_cartao += liquido_loja
                total_lucro_cartao += lucro_cartao
            except Exception:
                pass

    total_bruto = total_bruto_pix + total_bruto_cartao
    total_liquido = total_liquido_pix + total_liquido_cartao
    total_lucro = total_lucro_pix + total_lucro_cartao

    return f"""📈 *Relatório de Lucro Diário*

PIX:
 • Bruto: {formatar_valor(total_bruto_pix)}
 • Líquido (loja): {formatar_valor(total_liquido_pix)}
 • Seu lucro: {formatar_valor(total_lucro_pix)}

Cartão:
 • Bruto: {formatar_valor(total_bruto_cartao)}
 • Líquido (loja): {formatar_valor(total_liquido_cartao)}
 • Seu lucro: {formatar_valor(total_lucro_cartao)}

TOTAL:
 • Bruto: {formatar_valor(total_bruto)}
 • Líquido (loja): {formatar_valor(total_liquido)}
 • Seu lucro: {formatar_valor(total_lucro)}
"""

def processar_mensagem(texto, user_id):
    texto = texto.lower().strip()

    # Corrigir comprovante (admin)
    if texto.startswith("corrigir valor") and user_id == int(os.getenv("ADMIN_ID", "0")):
        try:
            partes = shlex.split(texto)
            if len(partes) < 5:
                return "❌ Uso: corrigir valor <índice> <novo valor> <novo tipo>"
            _, _, indice, valor_txt, tipo_txt = partes[:5]
            return corrigir_comprovante(indice, valor_txt, tipo_txt)
        except Exception:
            return "❌ Erro de sintaxe. Exemplo: corrigir valor 1 1000,00 10x"

    # Listar comprovantes (admin)
    if texto == "listar comprovantes" and user_id == int(os.getenv("ADMIN_ID", "0")):
        return listar_comprovantes()

    # Relatório de lucro (admin)
    if texto == "relatorio lucro" and user_id == int(os.getenv("ADMIN_ID", "0")):
        return relatorio_lucro()

    valor, tipo = extrair_valor_tipo(texto)
    if valor and tipo:
        liquido, taxa = calcular_valor_liquido(valor, tipo)
        if liquido is None:
            return "❌ Tipo de pagamento inválido. Exemplo: 1000,00 pix ou 2000,00 10x"
        comprovantes.append({
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "tipo": "PIX" if tipo == "pix" else tipo.upper(),
            "hora": get_horario_brasilia()
        })
        return f"""📄 Comprovante analisado:
💰 Valor bruto: {formatar_valor(valor)}
💰 Tipo: {'PIX' if tipo == 'pix' else tipo.upper()}
⏰ Horário: {get_horario_brasilia()}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: {formatar_valor(liquido)}"""

    if texto.startswith("solicito"):
        valor = normalizar_valor(texto)
        if not valor:
            return "❌ Valor inválido para solicitação."
        credito = credito_disponivel()
        if valor > credito:
            return f"❌ Solicitação maior que o crédito disponível: {formatar_valor(credito)}"
        solicitacoes.append({"valor": valor})
        return f"📢 Solicitação de pagamento registrada: {formatar_valor(valor)}.\nAguardando confirmação com 'pagamento feito'."

    if texto.startswith("pagamento feito"):
        valor = normalizar_valor(texto)
        if valor is None:
            if not solicitacoes:
                return "❌ Nenhuma solicitação de pagamento encontrada."
            valor = solicitacoes.pop(0)["valor"]
        else:
            for s in solicitacoes:
                if abs(s["valor"] - valor) < 0.01:
                    solicitacoes.remove(s)
                    break
        credito = credito_disponivel()
        if valor > credito:
            return f"❌ O pagamento de {formatar_valor(valor)} excede o crédito disponível: {formatar_valor(credito)}"
        saldo_anterior = credito
        novo_saldo = round(credito - valor, 2)
        pagamentos.append({"valor": valor})
        return f"""✅ Pagamento registrado com sucesso.
💵 Valor: {formatar_valor(valor)}
📉 Saldo anterior: {formatar_valor(saldo_anterior)}
💰 Novo saldo disponível: {formatar_valor(novo_saldo)}"""

    if texto == "total liquido":
        pendente = credito_disponivel()
        return f"💰 Valor líquido disponível: {formatar_valor(pendente)}"

    if texto == "pagamentos realizados":
        total = sum(p["valor"] for p in pagamentos)
        return f"✅ Total pago até agora: {formatar_valor(total)}"

    if texto == "fechamento do dia":
        total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "PIX")
        total_cartao = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] != "PIX" and c["tipo"] != "PENDENTE")
        total_pago = sum(p["valor"] for p in pagamentos)
        pendente = credito_disponivel()
        return f"""📅 Fechamento do Dia:

💳 Total Cartão: {formatar_valor(total_cartao)}
💸 Total PI.: {formatar_valor(total_pix)}
✅ Total Pago: {formatar_valor(total_pago)}
📌 Total Pendente: {formatar_valor(pendente)}"""

    if texto == "fechamento diário" and user_id == int(os.getenv("ADMIN_ID", "0")):
        return fechar_dia_e_zerar_saldos()

    if texto == "limpar tudo" and user_id == int(os.getenv("ADMIN_ID", "0")):
        comprovantes.clear()
        pagamentos.clear()
        solicitacoes.clear()
        return "🧹 Todos os dados foram zerados com sucesso."

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
• listar comprovantes
• corrigir valor <índice> <novo valor> <novo tipo>
• relatorio lucro
• fechamento diário
• limpar tudo
"""

    return None
