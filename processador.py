import os
import re
from datetime import datetime, timedelta
import pytz
import shlex

log_operacoes = []

comprovantes_pendentes = []
comprovantes = []
pagamentos = []
solicitacoes = []

def is_admin(user_id):
    return str(user_id) == str(os.getenv("ADMIN_ID", "0"))

def get_username(context_user):
    return f"@{getattr(context_user, 'username', None) or getattr(context_user, 'first_name', None) or str(getattr(context_user, 'id', '-'))}"

taxas_elo = {1: 5.12, 2: 6.22, 3: 6.93, 4: 7.64, 5: 8.35, 6: 9.07, 7: 10.07, 8: 10.92, 9: 11.63, 10: 12.34, 11: 13.05, 12: 13.76, 13: 14.47, 14: 15.17, 15: 15.88, 16: 16.59, 17: 17.30, 18: 18.01}
taxas_reais_elo = {1: 4.12, 2: 5.22, 3: 5.93, 4: 6.64, 5: 7.35, 6: 8.07, 7: 9.07, 8: 9.92, 9: 10.63, 10: 11.34, 11: 12.05, 12: 12.76, 13: 13.47, 14: 14.17, 15: 14.88, 16: 15.59, 17: 16.30, 18: 17.01}
taxas_amex = {1: 5.17, 2: 5.96, 3: 6.68, 4: 7.39, 5: 8.11, 6: 8.82, 7: 9.65, 8: 10.36, 9: 11.07, 10: 11.79, 11: 12.50, 12: 13.21, 13: 13.93, 14: 14.64, 15: 15.35, 16: 16.07, 17: 16.78, 18: 17.49}
taxas_reais_amex = {1: 4.17, 2: 4.96, 3: 5.68, 4: 6.39, 5: 7.11, 6: 7.82, 7: 8.65, 8: 9.36, 9: 10.07, 10: 10.79, 11: 11.50, 12: 12.21, 13: 12.93, 14: 13.64, 15: 14.35, 16: 15.07, 17: 15.78, 18: 16.49}
taxas_cartao = {1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84}
taxas_reais_cartao = {1: 3.28, 2: 3.96, 3: 4.68, 4: 5.40, 5: 6.12, 6: 6.84, 7: 7.72, 8: 8.44, 9: 9.16, 10: 9.88, 11: 10.60, 12: 11.32, 13: 12.04, 14: 12.76, 15: 13.48, 16: 14.20, 17: 14.92, 18: 15.64}
taxa_pix = 0.20
taxa_real_pix = 0.00

def formatar_valor(valor):
    try: valor = float(valor)
    except Exception: valor = 0.0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_data_hora_brasilia():
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    return agora.strftime('%H:%M'), agora.strftime('%Y-%m-%d')

def get_data_hoje():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso).strftime('%Y-%m-%d')

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
    try: return float(texto)
    except Exception: return None

def extrair_valor_tipo_bandeira(texto):
    texto = texto.lower().strip()
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
        elif bandeira == "amex":
            taxa = taxas_amex.get(parcelas, 0)
        else:
            taxa = taxas_cartao.get(parcelas, 0)
        if taxa == 0:
            return None, None
        liquido = valor * (1 - taxa / 100)
        return round(liquido, 2), taxa
    else:
        return None, None

def credito_disponivel():
    return round(sum(c["valor_liquido"] for c in comprovantes) - sum(p["valor"] for p in pagamentos), 2)

def registrar_acao(tipo, user_name, texto):
    hora, data = get_data_hora_brasilia()
    log_operacoes.append(f"{hora}/{data} - [{tipo}] {user_name}: {texto}")

def corrigir_comprovante(indice, valor_txt, tipo_txt, admin_name):
    try:
        indice = int(indice) - 1
        if indice < 0 or indice >= len(comprovantes):
            return "❌ Índice de comprovante inválido."
        antigo = comprovantes[indice]
        valor, tipo, bandeira = extrair_valor_tipo_bandeira(f"{valor_txt} {tipo_txt}")
        liquido, taxa = calcular_valor_liquido_bandeira(valor, tipo, bandeira)
        if liquido is None:
            return "❌ Tipo de pagamento inválido."
        tipo_str = "PIX" if tipo.lower() == "pix" else tipo.upper()
        if bandeira: tipo_str = f"{bandeira.upper()} {tipo_str}"
        hora, data = get_data_hora_brasilia()
        comprovantes[indice] = {
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "tipo": tipo_str,
            "hora": hora,
            "data": data
        }
        registrar_acao('CORREÇÃO', admin_name,
            f"Corrigiu [{indice+1}]: de {formatar_valor(antigo['valor_bruto'])} ({antigo['tipo']}) para {formatar_valor(valor)} ({tipo_str})"
        )
        return f"""⚠️ *Comprovante corrigido pelo admin!*
Antigo: `{formatar_valor(antigo['valor_bruto'])} ({antigo['tipo']})`
Novo valor bruto: `{formatar_valor(valor)}`
Novo tipo: `{tipo_str}`
Nova taxa: `{taxa:.2f}%`
Novo valor líquido: `{formatar_valor(liquido)}`"""
    except Exception as e:
        return f"❌ Erro ao corrigir comprovante: {str(e)}"

def listar_comprovantes(dia=None):
    comps = comprovantes if not dia else [c for c in comprovantes if c["data"] == dia]
    if not comps:
        return "📋 *Nenhum comprovante aprovado.*"
    linhas = [f"📋 *Comprovantes aprovados{' do dia' if dia else ''}:*"]
    for idx, c in enumerate(comps, start=1):
        linhas.append(
            f"`[{idx}]` {formatar_valor(c['valor_bruto'])} → Líq: {formatar_valor(c['valor_liquido'])} - {c['tipo']} - {c['hora']}/{c['data']}"
        )
    return "\n".join(linhas)

def listar_pagamentos(dia=None):
    pays = pagamentos if not dia else [p for p in pagamentos if p["data"] == dia]
    if not pays:
        return "💸 *Nenhum pagamento realizado.*"
    linhas = [f"💸 *Pagamentos realizados{' do dia' if dia else ''}:*"]
    for idx, p in enumerate(pays, start=1):
        linhas.append(
            f"`[{idx}]` {formatar_valor(p['valor'])} {p['hora']}/{p['data']}"
        )
    return "\n".join(linhas)

def listar_pendentes():
    if not comprovantes_pendentes:
        return "⏳ *Nenhum comprovante pendente aguardando aprovação.*"
    linhas = ["⏳ *Comprovantes pendentes (aguardam conferência do admin):*"]
    for idx, c in enumerate(comprovantes_pendentes, start=1):
        linhas.append(
            f"`[{idx}]` {formatar_valor(c['valor_bruto'])} → Líq: {formatar_valor(c['valor_liquido'])} - {c['tipo']} - {c['hora']}/{c['data']}"
        )
    return "\n".join(linhas)

def aprovar_pendente(indice, admin_name):
    try:
        indice = int(indice) - 1
        if indice < 0 or indice >= len(comprovantes_pendentes):
            return "❌ Índice de pendente inválido."
        comp = comprovantes_pendentes.pop(indice)
        comprovantes.append(comp)
        registrar_acao('APROVAÇÃO', admin_name, f"Aprovou [{indice+1}]: {formatar_valor(comp['valor_bruto'])} ({comp['tipo']})")
        return f"""✅ [{admin_name}] aprovou:\n`{formatar_valor(comp['valor_bruto'])} ({comp['tipo']}) - Líq: {formatar_valor(comp['valor_liquido'])}`\nSaldo liberado!"""
    except Exception:
        return "❌ Erro ao aprovar. Exemplo: aprovar 1"

def rejeitar_pendente(indice, admin_name, motivo):
    try:
        indice = int(indice) - 1
        if indice < 0 or indice >= len(comprovantes_pendentes):
            return "❌ Índice de pendente inválido."
        comp = comprovantes_pendentes.pop(indice)
        registrar_acao('REJEIÇÃO', admin_name, f"Rejeitou [{indice+1}] ({comp['tipo']}) {formatar_valor(comp['valor_bruto'])}. Motivo: {motivo}")
        return f"🚫 [{admin_name}] rejeitou:\n`{formatar_valor(comp['valor_bruto'])} ({comp['tipo']}) - Líq: {formatar_valor(comp['valor_liquido'])}`\nMotivo: {motivo}"
    except Exception:
        return "❌ Erro ao rejeitar. Exemplo: rejeitar 1 <motivo>"

def relatorio_lucro(periodo="dia"):
    fuso = pytz.timezone('America/Sao_Paulo')
    dt_now = datetime.now(fuso)
    if periodo == "dia":
        data_ini = data_fim = dt_now.strftime('%Y-%m-%d')
        titulo = f"Lucro do dia {data_ini}"
    elif periodo == "semana":
        data_fim = dt_now.strftime('%Y-%m-%d')
        data_ini = (dt_now - timedelta(days=6)).strftime('%Y-%m-%d')
        titulo = f"Lucro da semana ({data_ini} a {data_fim})"
    elif periodo == "mes":
        data_ini = dt_now.replace(day=1).strftime('%Y-%m-%d')
        data_fim = dt_now.strftime('%Y-%m-%d')
        titulo = f"Lucro do mês ({data_ini} a {data_fim})"
    else:
        data_ini = data_fim = dt_now.strftime('%Y-%m-%d')
        titulo = f"Lucro do dia {data_ini}"

    def dentro(data):
        return data_ini <= data <= data_fim

    total_bruto_pix = total_bruto_cartao = 0.0
    total_liquido_pix = total_liquido_cartao = 0.0
    total_lucro_pix = total_lucro_cartao = 0.0

    for c in (x for x in comprovantes if dentro(x["data"])):
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

    return f"""📈 *{titulo}*

*PIX:*
 • Bruto: `{formatar_valor(total_bruto_pix)}`
 • Líquido (loja): `{formatar_valor(total_liquido_pix)}`
 • Seu lucro: `{formatar_valor(total_lucro_pix)}`

*Cartão:*
 • Bruto: `{formatar_valor(total_bruto_cartao)}`
 • Líquido (loja): `{formatar_valor(total_liquido_cartao)}`
 • Seu lucro: `{formatar_valor(total_lucro_cartao)}`

*TOTAL:*
 • Bruto: `{formatar_valor(total_bruto)}`
 • Líquido (loja): `{formatar_valor(total_liquido)}`
 • Seu lucro: `{formatar_valor(total_lucro)}`
"""

def fechamento_do_dia():
    _, hoje = get_data_hora_brasilia()
    return extrato_visual("hoje")

def zerar_saldos():
    comprovantes.clear()
    pagamentos.clear()
    solicitacoes.clear()
    return "✅ *Fechamento realizado.* Saldos de cartão e pix zerados (saldo anterior permanece; consulte comando `total liquido`)."

def extrato_visual(periodo="hoje"):
    fuso = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso).strftime('%Y-%m-%d')
    if periodo == "hoje":
        data_inicial = data_final = hoje
        titulo_periodo = hoje
    elif periodo == "7dias":
        dt = datetime.now(fuso)
        data_final = dt.strftime('%Y-%m-%d')
        data_inicial = (dt - timedelta(days=6)).strftime('%Y-%m-%d')
        titulo_periodo = f"{data_inicial} a {data_final}"
    else:
        data_inicial = data_final = hoje
        titulo_periodo = hoje

    def dentro(dt):
        return data_inicial <= dt <= data_final

    linhas = []
    linhas.append(f"📄 *Extrato Detalhado* — {titulo_periodo}\n")
    linhas.append("Nº | Bruto     | Líq     | Tipo        | Situação     | Hora")
    linhas.append("---|-----------|---------|-------------|--------------|------")
    todas = []

    for idx, c in enumerate([x for x in comprovantes if dentro(x["data"])], start=1):
        todas.append((
            c["hora"],
            f"{idx}  | {formatar_valor(c['valor_bruto']):<9}| {formatar_valor(c['valor_liquido']):<7}| {c['tipo']:<11}| {'Aprovado':<12}| {c['hora']}"
        ))
    for idx, c in enumerate([x for x in comprovantes_pendentes if dentro(x["data"])], start=1):
        todas.append((
            c["hora"],
            f"-   | {formatar_valor(c['valor_bruto']):<9}| {formatar_valor(c['valor_liquido']):<7}| {c['tipo']:<11}| {'Pendente':<12}| {c['hora']}"
        ))
    for idx, p in enumerate([x for x in pagamentos if dentro(x["data"])], start=1):
        todas.append((
            p["hora"],
            f"-   | {'-'*9} | {formatar_valor(p['valor']):<7}| {'Pagamento':<11}| {'Pago':<12}| {p['hora']}"
        ))
    todas.sort(key=lambda t: t[0])
    for _, linha in todas:
        linhas.append(linha)
    if len(linhas) == 3:
        linhas.append("_Nenhum lançamento no período._")
    return "\n".join(linhas)

def aprova_callback(idx, admin_user):
    return aprovar_pendente(idx, get_username(admin_user))

def rejeita_callback(idx, admin_user, motivo):
    return rejeitar_pendente(idx, get_username(admin_user), motivo)

def processar_mensagem(texto, user_id, username="ADMIN"):
    texto = texto.strip().lower()
    admin = is_admin(user_id)
    hora, data = get_data_hora_brasilia()

    if texto == "/menu" or texto == "menu":
        return "MENU_BOTAO"

    if texto == "extrato" or texto == "/extrato":
        return extrato_visual("hoje")
    if "7" in texto and "extrato" in texto:
        return extrato_visual("7dias")

    if texto == "extrato do dia":
        return extrato_visual("hoje")

    if texto == "meu id":
        return f"Seu user_id: {user_id}\nEste chat_id: {username}"

    # -- RELATORIO LUCRO --
    if texto.startswith("relatorio lucro") and admin:
        if "semana" in texto:
            return relatorio_lucro("semana")
        elif "mes" in texto:
            return relatorio_lucro("mes")
        else:
            return relatorio_lucro("dia")

    if texto.startswith("corrigir valor") and admin:
        try:
            partes = shlex.split(texto)
            if len(partes) < 5:
                return "❌ Uso: corrigir valor <índice> <novo valor> <novo tipo>"
            _, _, indice, valor_txt, tipo_txt = partes[:5]
            return corrigir_comprovante(indice, valor_txt, tipo_txt, username)
        except Exception:
            return "❌ Erro de sintaxe. Exemplo: corrigir valor 1 1000,00 10x"

    if texto == "listar comprovantes" and admin:
        return listar_comprovantes()

    if texto == "listar pagamentos" and admin:
        return listar_pagamentos()

    if texto == "config taxa" and admin:
        return "⚙️ *Para alterar taxas, edite diretamente no código ou peça uma função personalizada!*"

    if texto == "limpar tudo" and admin:
        comprovantes.clear()
        comprovantes_pendentes.clear()
        pagamentos.clear()
        solicitacoes.clear()
        log_operacoes.clear()
        return "🧹 *Todos os dados foram zerados com sucesso.*"

    if texto == "fechamento diário" and admin:
        return zerar_saldos()

    valor, tipo, bandeira = extrair_valor_tipo_bandeira(texto)
    if valor and tipo:
        liquido, taxa = calcular_valor_liquido_bandeira(valor, tipo, bandeira)
        if liquido is None:
            return "❌ Tipo de pagamento inválido. Exemplo: 1000,00 pix ou 2000,00 10x"
        tipo_str = "PIX" if tipo == "pix" else tipo.upper()
        if bandeira:
            tipo_str = f"{bandeira.upper()} {tipo_str}"

        comprovantes_pendentes.append({
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "tipo": tipo_str,
            "hora": hora,
            "data": data
        })
        idx = len(comprovantes_pendentes)
        registrar_acao('ENVIO', username,
            f"Enviou comprovante pendente [{idx}]: {formatar_valor(valor)} ({tipo_str})"
        )
        return (
            f"⏳ *Comprovante aguardando confirmação do admin*\n"
            f"`[{idx}]` 💰 Valor bruto: `{formatar_valor(valor)}`\n"
            f"💳 Tipo: `{tipo_str}`\n"
            f"⏰ Horário: `{hora}/{data}`\n"
            f"📉 Taxa aplicada: `{taxa:.2f}%`\n"
            f"✅ Valor líquido a liberar: `{formatar_valor(liquido)}`\n"
            "Aguarde conferência. O admin deve aprovar/rejeitar para liberar o saldo!"
        )

    if texto.startswith("solicito"):
        valor = normalizar_valor(texto)
        credito = credito_disponivel()
        if not valor:
            return "❌ Valor inválido para solicitação."
        if valor > credito:
            return f"❌ Solicitação maior que o crédito disponível: `{formatar_valor(credito)}`"
        solicitacoes.append({"valor": valor})
        registrar_acao("SOLICITAÇÃO", username, f"Solicitação de pagamento de {formatar_valor(valor)}")
        return f"📝 *Solicitação de pagamento registrada:* `{formatar_valor(valor)}`. Aguarde confirmação do admin com 'pagamento feito'."

    if texto.startswith("pagamento feito"):
        valor = normalizar_valor(texto)
        credito = credito_disponivel()
        if valor is None:
            if not solicitacoes:
                return "❌ Nenhuma solicitação de pagamento encontrada."
            valor = solicitacoes.pop(0)["valor"]
        else:
            for s in solicitacoes:
                if abs(s["valor"] - valor) < 0.01:
                    solicitacoes.remove(s)
                    break
        if valor > credito:
            return f"❌ O pagamento de `{formatar_valor(valor)}` excede o crédito disponível: `{formatar_valor(credito)}`"
        saldo_anterior = credito
        novo_saldo = round(credito - valor, 2)
        pagamentos.append({"valor": valor, "hora": hora, "data": data})
        registrar_acao("PAGAMENTO", username, f"Pagou {formatar_valor(valor)} (Saldo antes: {formatar_valor(saldo_anterior)})")
        return f"""✅ *Pagamento registrado com sucesso!*
💵 Valor: `{formatar_valor(valor)}`
📉 Saldo anterior: `{formatar_valor(saldo_anterior)}`
💰 Novo saldo disponível: `{formatar_valor(novo_saldo)}`"""

    if texto == "total liquido":
        total_liquido = credito_disponivel()
        return f"💰 *Valor líquido disponível (apenas comprovantes aprovados):* `{formatar_valor(total_liquido)}`"

    if texto == "pagamentos realizados":
        total = sum(p["valor"] for p in pagamentos)
        return f"✅ *Total pago até agora:* `{formatar_valor(total)}`"

    if texto == "fechamento do dia":
        return extrato_visual("hoje")

    if texto == "ajuda":
        return """🤖 *Comandos disponíveis*:

📋 Use /menu ou envie "menu" para acessar os botões de atalho!

📥 *Enviar comprovante para conferência (aprovado pelo admin):*
• `1000,00 pix`
• `1000,00 10x` ou `1000,00 elo 10x` ou `1000,00 amex 10x`

⏸️ *Consultar pendentes de conferência:*
• *Admin*: `listar pendentes`

☑️ *Aprovar ou rejeitar (admin ou botão do bot):*
 • `aprovar 1`
 • `rejeitar 1 motivo da recusa`

🔄 *Corrigir comprovante (admin):*
 • `corrigir valor 1 1200,00 12x`

📤 *Solicitar pagamento:*
• `solicito 300,00`

✅ *Confirmar pagamento:*
• `pagamento feito` ou `pagamento feito 300,00`

📊 *Consultas:*
• total liquido
• pagamentos realizados
• fechamento do dia
• extrato
• extrato 7dias
• relatorio lucro
• relatorio lucro semana
• relatorio lucro mes
• meu id
"""
    return None
