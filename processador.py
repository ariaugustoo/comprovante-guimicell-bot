from datetime import datetime
import pytz
import re
import os
import shlex

comprovantes = []
pagamentos = []
solicitacoes = []

comandos_privados = ["relatorio lucro", "listar comprovantes", "listar pagamentos", "corrigir valor", "config taxa", "limpar tudo", "fechamento diário"]

def is_admin(user_id):
    return user_id == int(os.getenv("ADMIN_ID", "0"))

# Taxas originais ELO (imagem 4) + 1%
taxas_elo = {
    1: 5.12, 2: 6.22, 3: 6.93, 4: 7.64, 5: 8.35, 6: 9.07, 7: 10.07, 8: 10.92, 9: 11.63, 10: 12.34,
    11: 13.05, 12: 13.76, 13: 14.47, 14: 15.17, 15: 15.88, 16: 16.59, 17: 17.30, 18: 18.01
}
taxas_reais_elo = {  # Supondo taxa de máquina igual às originais
    1: 4.12, 2: 5.22, 3: 5.93, 4: 6.64, 5: 7.35, 6: 8.07, 7: 9.07, 8: 9.92, 9: 10.63, 10: 11.34,
    11: 12.05, 12: 12.76, 13: 13.47, 14: 14.17, 15: 14.88, 16: 15.59, 17: 16.30, 18: 17.01
}

# Taxas originais AMEX (imagem 3) + 1%
taxas_amex = {
    1: 5.17, 2: 5.96, 3: 6.68, 4: 7.39, 5: 8.11, 6: 8.82, 7: 9.65, 8: 10.36, 9: 11.07, 10: 11.79,
    11: 12.50, 12: 13.21, 13: 13.93, 14: 14.64, 15: 15.35, 16: 16.07, 17: 16.78, 18: 17.49
}
taxas_reais_amex = {  # Supondo taxa de máquina igual às originais
    1: 4.17, 2: 4.96, 3: 5.68, 4: 6.39, 5: 7.11, 6: 7.82, 7: 8.65, 8: 9.36, 9: 10.07, 10: 10.79,
    11: 11.50, 12: 12.21, 13: 12.93, 14: 13.64, 15: 14.35, 16: 15.07, 17: 15.78, 18: 16.49
}

# Taxas Visa/Master (já no seu código)
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}
taxas_reais_cartao = {
    1: 3.28, 2: 3.96, 3: 4.68, 4: 5.40, 5: 6.12,
    6: 6.84, 7: 7.72, 8: 8.44, 9: 9.16, 10: 9.88,
    11: 10.60, 12: 11.32, 13: 12.04, 14: 12.76, 15: 13.48,
    16: 14.20, 17: 14.92, 18: 15.64
}
taxa_pix = 0.20
taxa_real_pix = 0.00

def formatar_valor(valor):
    try:
        valor = float(valor)
    except Exception:
        valor = 0.0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_horario_brasilia():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso).strftime('%H:%M')

VALOR_BRL_REGEX = r"(\d{1,3}(?:\.\d{3})*,\d{2})"

def normalizar_valor(texto):
    texto = texto.strip()
    match = re.search(VALOR_BRL_REGEX, texto)
    if match:
        valor_str = match.group(1)
        valor_float = float(valor_str.replace('.', '').replace(',', '.'))
        return valor_float
    texto = re.sub(r'[^\d,\.]', '', texto)
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", "")
    try:
        return float(texto)
    except Exception:
        return None

def extrair_valor_tipo_bandeira(texto):
    # Novo: extrai bandeira (elo/amex) se presente
    texto = texto.lower().strip()
    # Exemplos de comandos:
    # "1000,00 elo 18x", "1000,00 amex 12x", "1000,00 10x", "1000,00 pix"
    match = re.match(r"^(\d{1,3}(?:\.\d{3})*,\d{2}|\d+(?:,\d{2})?)\s*(elo|amex)?\s*(pix|\d{1,2}x)$", texto)
    if match:
        valor, bandeira, tipo = match.groups()
        bandeira = bandeira if bandeira in ("elo", "amex") else None
        return normalizar_valor(valor), tipo, bandeira
    match = re.match(r"^(elo|amex)?\s*(pix|\d{1,2}x)\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+(?:,\d{2})?)$", texto)
    if match:
        bandeira, tipo, valor = match.groups()
        bandeira = bandeira if bandeira in ("elo", "amex") else None
        return normalizar_valor(valor), tipo, bandeira
    return None, None, None

def calcular_valor_liquido_bandeira(valor, tipo, bandeira):
    tipo = tipo.lower()
    if tipo == "pix":
        taxa = taxa_pix
        liquido = valor * (1 - taxa / 100)
        return round(liquido, 2), taxa
    elif "x" in tipo:
        parcelas = int(re.sub(r'\D', '', tipo))
        if bandeira == "elo":
            taxa = taxas_elo.get(parcelas, 0)
            taxa_maquina = taxas_reais_elo.get(parcelas, 0)
        elif bandeira == "amex":
            taxa = taxas_amex.get(parcelas, 0)
            taxa_maquina = taxas_reais_amex.get(parcelas, 0)
        else:
            taxa = taxas_cartao.get(parcelas, 0)
            taxa_maquina = taxas_reais_cartao.get(parcelas, 0)
        if taxa == 0:
            return None, None
        liquido = valor * (1 - taxa / 100)
        return round(liquido, 2), taxa
    else:
        return None, None

def credito_disponivel():
    return round(sum(c["valor_liquido"] for c in comprovantes if c["tipo"] != "PENDENTE") - sum(p["valor"] for p in pagamentos), 2)

def corrigir_comprovante(indice, valor_txt, tipo_txt):
    try:
        indice = int(indice) - 1
        if indice < 0 or indice >= len(comprovantes):
            return "❌ Índice de comprovante inválido."
        valor, tipo, bandeira = extrair_valor_tipo_bandeira(f"{valor_txt} {tipo_txt}")
        liquido, taxa = calcular_valor_liquido_bandeira(valor, tipo, bandeira)
        if liquido is None:
            return "❌ Tipo de pagamento inválido."
        tipo_str = "PIX" if tipo.lower() == "pix" else tipo.upper()
        if bandeira:
            tipo_str = f"{bandeira.upper()} {tipo_str}"
        comprovantes[indice] = {
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "tipo": tipo_str,
            "hora": get_horario_brasilia()
        }
        return f"""✅ Comprovante corrigido!
Novo valor bruto: {formatar_valor(valor)}
Novo tipo: {tipo_str}
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

def listar_pagamentos():
    if not pagamentos:
        return "💸 Nenhum pagamento realizado."
    linhas = ["💸 Pagamentos realizados:"]
    for idx, p in enumerate(pagamentos, start=1):
        linhas.append(
            f"[{idx}] {formatar_valor(p['valor'])}"
        )
    return "\n".join(linhas)

def relatorio_lucro():
    total_bruto_pix = total_bruto_cartao = 0.0
    total_liquido_pix = total_liquido_cartao = 0.0
    total_lucro_pix = total_lucro_cartao = 0.0

    for c in comprovantes:
        if c["tipo"] == "PENDENTE":
            continue
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
        elif "ELO" in tipo:
            parcelas = int(re.search(r'(\d{1,2})X', tipo).group(1))
            taxa_loja = taxas_elo.get(parcelas, 0)
            taxa_maquina = taxas_reais_elo.get(parcelas, 0)
            lucro_elo = valor * (taxa_loja - taxa_maquina) / 100
            total_bruto_cartao += valor
            total_liquido_cartao += liquido_loja
            total_lucro_cartao += lucro_elo
        elif "AMEX" in tipo:
            parcelas = int(re.search(r'(\d{1,2})X', tipo).group(1))
            taxa_loja = taxas_amex.get(parcelas, 0)
            taxa_maquina = taxas_reais_amex.get(parcelas, 0)
            lucro_amex = valor * (taxa_loja - taxa_maquina) / 100
            total_bruto_cartao += valor
            total_liquido_cartao += liquido_loja
            total_lucro_cartao += lucro_amex
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

def fechamento_do_dia():
    total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "PIX")
    total_cartao = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] != "PIX" and c["tipo"] != "PENDENTE")
    total_pago = sum(p["valor"] for p in pagamentos)
    pendente = credito_disponivel()
    return f"""📅 Fechamento do Dia:

💳 Total Cartão: {formatar_valor(total_cartao)}
💸 Total PIX: {formatar_valor(total_pix)}
✅ Total Pago: {formatar_valor(total_pago)}
📌 Total Pendente: {formatar_valor(pendente)}"""

def zerar_saldos():
    pendente = credito_disponivel()
    comprovantes.clear()
    pagamentos.clear()
    solicitacoes.clear()
    if pendente > 0:
        comprovantes.append({
            "valor_bruto": pendente,
            "valor_liquido": pendente,
            "tipo": "PENDENTE",
            "hora": get_horario_brasilia()
        })
    return f"✅ Fechamento realizado. Saldos de Cartão e Pix zerados. Saldo pendente mantido: {formatar_valor(pendente)}."

def processar_mensagem(texto, user_id):
    texto = texto.lower().strip()

    if texto.startswith("corrigir valor") and is_admin(user_id):
        try:
            partes = shlex.split(texto)
            if len(partes) < 5:
                return "❌ Uso: corrigir valor <índice> <novo valor> <novo tipo>"
            _, _, indice, valor_txt, tipo_txt = partes[:5]
            return corrigir_comprovante(indice, valor_txt, tipo_txt)
        except Exception:
            return "❌ Erro de sintaxe. Exemplo: corrigir valor 1 1000,00 10x"

    if texto == "listar comprovantes" and is_admin(user_id):
        return listar_comprovantes()

    if texto == "listar pagamentos" and is_admin(user_id):
        return listar_pagamentos()

    if texto == "relatorio lucro" and is_admin(user_id):
        return relatorio_lucro()

    if texto == "config taxa" and is_admin(user_id):
        return "⚙️ Para alterar taxas, edite diretamente no código ou peça uma função personalizada!"

    if texto == "limpar tudo" and is_admin(user_id):
        comprovantes.clear()
        pagamentos.clear()
        solicitacoes.clear()
        return "🧹 Todos os dados foram zerados com sucesso."

    if texto == "fechamento diário" and is_admin(user_id):
        return zerar_saldos()

    if texto == "meu id":
        return f"Seu user_id: {user_id}"

    valor, tipo, bandeira = extrair_valor_tipo_bandeira(texto)
    if valor and tipo:
        liquido, taxa = calcular_valor_liquido_bandeira(valor, tipo, bandeira)
        if liquido is None:
            return "❌ Tipo de pagamento inválido. Exemplo: 1000,00 pix ou 2000,00 10x"
        tipo_str = "PIX" if tipo == "pix" else tipo.upper()
        if bandeira:
            tipo_str = f"{bandeira.upper()} {tipo_str}"
        comprovantes.append({
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "tipo": tipo_str,
            "hora": get_horario_brasilia()
        })
        return f"""📄 Comprovante analisado:
💰 Valor bruto: {formatar_valor(valor)}
💰 Tipo: {tipo_str}
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
        total_liquido = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] != "PENDENTE") - sum(p["valor"] for p in pagamentos)
        return f"💰 Valor líquido disponível: {formatar_valor(total_liquido)}"

    if texto == "pagamentos realizados":
        total = sum(p["valor"] for p in pagamentos)
        return f"✅ Total pago até agora: {formatar_valor(total)}"

    if texto == "fechamento do dia":
        return fechamento_do_dia()

    if texto == "ajuda":
        return """🤖 *Comandos disponíveis*:

📥 Enviar comprovante:
`1000,00 pix`
`1000,00 10x`
`1000,00 elo 10x`
`1000,00 amex 10x`

📤 Solicitar pagamento:
`solicito 300,00`

✅ Confirmar pagamento:
`pagamento feito` ou `pagamento feito 300,00`

📊 Consultas:
• total liquido
• pagamentos realizados
• fechamento do dia
• meu id

🔒 Admin (somente no privado):
• listar comprovantes
• listar pagamentos
• corrigir valor <índice> <novo valor> <novo tipo>
• relatorio lucro
• fechamento diário
• limpar tudo
"""

    return None
