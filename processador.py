import os
import re
import uuid
import math
from datetime import datetime, timedelta
import pytz

# Logs e estruturas em memória
log_operacoes = []

comprovantes_pendentes = []
comprovantes = []
pagamentos = []
solicitacoes = []

def is_admin(user_id):
    return str(user_id) == str(os.getenv("ADMIN_ID", "0"))

def get_username(context_user):
    # Recebe um objeto user do telegram (ou qualquer objeto com username/first_name/id)
    return f"@{getattr(context_user, 'username', None) or getattr(context_user, 'first_name', None) or str(getattr(context_user, 'id', '-'))}"

# Taxas por bandeira/parcelas (exemplo fornecido)
taxas_elo = {1: 5.12, 2: 6.22, 3: 6.93, 4: 7.64, 5: 8.35, 6: 9.07, 7: 10.07, 8: 10.92, 9: 11.63, 10: 12.34, 11: 13.05, 12: 13.76, 13: 14.47, 14: 15.17, 15: 15.88, 16: 16.59, 17: 17.30, 18: 18.01}
taxas_reais_elo = {1: 4.12, 2: 5.22, 3: 5.93, 4: 6.64, 5: 7.35, 6: 8.07, 7: 9.07, 8: 9.92, 9: 10.63, 10: 11.34, 11: 12.05, 12: 12.76, 13: 13.47, 14: 14.17, 15: 14.88, 16: 15.59, 17: 16.30, 18: 17.01}
taxas_amex = {1: 5.17, 2: 5.96, 3: 6.68, 4: 7.39, 5: 8.11, 6: 8.82, 7: 9.65, 8: 10.36, 9: 11.07, 10: 11.79, 11: 12.50, 12: 13.21, 13: 13.93, 14: 14.64, 15: 15.35, 16: 16.07, 17: 16.78, 18: 17.49}
taxas_reais_amex = {1: 4.17, 2: 4.96, 3: 5.68, 4: 6.39, 5: 7.11, 6: 7.82, 7: 8.65, 8: 9.36, 9: 10.07, 10: 10.79, 11: 11.50, 12: 12.21, 13: 12.93, 14: 13.64, 15: 14.35, 16: 15.07, 17: 15.78, 18: 16.49}
taxas_cartao = {1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84}
taxas_reais_cartao = {1: 3.28, 2: 3.96, 3: 4.68, 4: 5.40, 5: 6.12, 6: 6.84, 7: 7.72, 8: 8.44, 9: 9.16, 10: 9.88, 11: 10.60, 12: 11.32, 13: 12.04, 14: 12.76, 15: 13.48, 16: 14.20, 17: 14.92, 18: 15.64}
taxa_pix = 0.20

def formatar_valor(valor):
    try:
        valor = float(valor)
    except Exception:
        valor = 0.0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_data_hora_brasilia():
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    return agora.strftime('%H:%M'), agora.strftime('%d/%m/%Y')

# Regex para valores no formato BR
VALOR_BRL_REGEX = r"(\d{1,3}(?:\.\d{3})*,\d{2})"

def normalizar_valor(texto):
    """
    Normaliza texto que contém valor para float.
    Aceita formatos: '1000', '1000.00', '1.000,00', '1000,00', etc.
    Retorna float ou None se não reconhece.
    """
    if texto is None:
        return None
    texto = str(texto).strip()
    match = re.search(VALOR_BRL_REGEX, texto)
    if match:
        valor_str = match.group(1)
        return float(valor_str.replace('.', '').replace(',', '.'))
    # remove tudo que não é dígito ou ponto/virgula
    cleaned = re.sub(r'[^\d,\.]', '', texto)
    if cleaned == '':
        return None
    # se contém vírgula e ponto, tratamos '.' como milhares e ',' como decimal
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    else:
        cleaned = cleaned.replace(',', '')
    try:
        return float(cleaned)
    except Exception:
        return None

def extrair_valor_tipo_bandeira(texto):
    """
    Tenta extrair (valor_float, tipo, bandeira) a partir de um texto livre.
    Retorna (None, None, None) se não for parseável.
    """
    if not texto:
        return None, None, None
    texto = str(texto).strip().lower()
    # padrão: valor [bandeira]? [tipo]  (ex: "1000,00 elo 12x" ou "1000 10x")
    m = re.match(r"^(\d{1,3}(?:\.\d{3})*(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?)\s*(elo|amex)?\s*(pix|\d{1,2}x)?$", texto)
    if m:
        valor_str, bandeira, tipo = m.groups()
        tipo = tipo or "pix"
        bandeira = bandeira if bandeira in ("elo", "amex") else None
        valor = normalizar_valor(valor_str)
        return valor, tipo, bandeira
    # padrão: [bandeira]? [tipo]? valor  (ex: "elo 12x 1200")
    m = re.match(r"^(elo|amex)?\s*(pix|\d{1,2}x)?\s*(\d{1,3}(?:\.\d{3})*(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?)$", texto)
    if m:
        bandeira, tipo, valor_str = m.groups()
        tipo = tipo or "pix"
        bandeira = bandeira if bandeira in ("elo", "amex") else None
        valor = normalizar_valor(valor_str)
        return valor, tipo, bandeira
    # se vier apenas um número simples "500" ou "500,00"
    m = re.match(r"^(\d+(?:[.,]\d{2})?)$", texto)
    if m:
        valor = normalizar_valor(m.group(1))
        return valor, "pix", None
    return None, None, None

def calcular_valor_liquido_bandeira(valor, tipo, bandeira):
    """
    Calcula valor líquido a partir do bruto, tipo e bandeira.
    Retorna (liquido, taxa%) ou (None, None) se inválido.
    """
    tipo = (tipo or "pix").lower()
    if tipo == "pix":
        taxa = taxa_pix
        liquido = valor * (1 - taxa / 100)
        return round(liquido, 2), taxa
    if "x" in tipo:
        try:
            parcelas = int(re.sub(r'\D', '', tipo))
        except Exception:
            parcelas = 1
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
    return None, None

def calcular_bruto_para_liquido(liquido_desejado, tipo, bandeira):
    """
    Inverte a operação: dado o líquido desejado, calcula o bruto necessário.
    Arredonda sempre para cima (centavos).
    Retorna (bruto, taxa%) ou (None, None) se não for possível.
    """
    tipo = (tipo or "pix").lower()
    if tipo == "pix":
        taxa = taxa_pix
    elif "x" in tipo:
        try:
            parcelas = int(re.sub(r'\D', '', tipo))
        except Exception:
            parcelas = 1
        if bandeira == "elo":
            taxa = taxas_elo.get(parcelas, 0)
        elif bandeira == "amex":
            taxa = taxas_amex.get(parcelas, 0)
        else:
            taxa = taxas_cartao.get(parcelas, 0)
    else:
        return None, None
    if taxa == 0:
        return None, None
    bruto = liquido_desejado / (1 - taxa / 100)
    bruto_arred = math.ceil(bruto * 100) / 100.0
    return round(bruto_arred, 2), taxa

def calculadora_simples_input(valor, tipo="pix", bandeira=None):
    """
    Utilitário de apresentação: dado bruto/tipo/bandeira retorna texto com líquido e taxa.
    """
    liquido, taxa = calcular_valor_liquido_bandeira(valor, tipo, bandeira)
    if liquido is None:
        return "❌ Tipo de pagamento inválido para calculadora. Use exemplos: 1000 pix ou 1000 10x ou 1200 elo 12x"
    tipo_display = (f"{bandeira.upper()} {tipo.upper()}" if bandeira else tipo.upper())
    return (
        f"🧮 *Calculadora de recebimento*\n\n"
        f"💰 Valor bruto: `{formatar_valor(valor)}`\n"
        f"💳 Tipo: `{tipo_display}`\n"
        f"🧾 Taxa aplicada: `{taxa:.2f}%`\n"
        f"✅ Valor líquido que você receberá: `{formatar_valor(liquido)}`"
    )

def calculadora_reversa_input(liquido_desejado, tipo="pix", bandeira=None):
    """
    Utilitário de apresentação para calculadora reversa: dado líquido desejado, mostra bruto (arredondado para cima) e líquido aproximado.
    """
    bruto, taxa = calcular_bruto_para_liquido(liquido_desejado, tipo, bandeira)
    if bruto is None:
        return "❌ Não foi possível calcular o bruto para esse tipo/bandeira. Verifique entrada (ex: `500 pix` ou `500 10x` ou `500 elo 12x`)."
    tipo_display = (f"{bandeira.upper()} {tipo.upper()}" if bandeira else tipo.upper())
    liquido_aproximado, _ = calcular_valor_liquido_bandeira(bruto, tipo, bandeira)
    return (
        f"🧮 *Calculadora reversa*\n\n"
        f"✅ Você quer receber líquido: `{formatar_valor(liquido_desejado)}`\n"
        f"💳 Tipo considerado: `{tipo_display}`\n"
        f"🧾 Taxa aplicada: `{taxa:.2f}%`\n"
        f"💰 Você precisa cobrar (bruto, arredondado para cima): `{formatar_valor(bruto)}`\n"
        f"🔎 Após a taxa, você receberá aproximadamente: `{formatar_valor(liquido_aproximado)}`"
    )

def credito_disponivel():
    """
    Soma dos comprovantes aprovados (valor_liquido) menos pagamentos já feitos.
    """
    return round(sum(c["valor_liquido"] for c in comprovantes) - sum(p["valor"] for p in pagamentos), 2)

def registrar_acao(tipo, user_name, texto):
    hora, data = get_data_hora_brasilia()
    log_operacoes.append(f"{hora}/{data} - [{tipo}] {user_name}: {texto}")

def limpar_pendentes():
    comprovantes_pendentes.clear()
    return "✅ Todos os comprovantes pendentes foram removidos com sucesso."

def listar_pendentes():
    if not comprovantes_pendentes:
        return "⏳ *Nenhum comprovante pendente aguardando aprovação.*"
    linhas = ["⏳ *Pendentes aguardando conferência:*"]
    for c in comprovantes_pendentes:
        linhas.append(
            f"🆔 ID: `{c['id']}`\n"
            f"💸 Bruto: {formatar_valor(c['valor_bruto'])}\n"
            f"✅ Líquido: {formatar_valor(c['valor_liquido'])}\n"
            f"💳 Tipo: {c['tipo']}\n"
            f"⏰ Hora: {c['hora']} {c['data']}\n"
        )
    return "\n".join(linhas)

def aprovar_pendente(comp_id, admin_name):
    idx = next((i for i, c in enumerate(comprovantes_pendentes) if c["id"] == comp_id), None)
    if idx is None:
        return "❌ Esse comprovante já foi aprovado/rejeitado ou não está mais pendente."
    comp = comprovantes_pendentes.pop(idx)
    comprovantes.append(comp)
    registrar_acao('APROVAÇÃO', admin_name, f"Aprovou [{comp_id}]: {formatar_valor(comp['valor_bruto'])} ({comp['tipo']})")
    return f"✅ [{admin_name}] aprovou:\n`{formatar_valor(comp['valor_bruto'])} ({comp['tipo']}) - Líq: {formatar_valor(comp['valor_liquido'])}`\nSaldo liberado!"

def rejeitar_pendente(comp_id, admin_name, motivo):
    idx = next((i for i, c in enumerate(comprovantes_pendentes) if c["id"] == comp_id), None)
    if idx is None:
        return "❌ Esse comprovante já foi aprovado/rejeitado ou não está mais pendente."
    comp = comprovantes_pendentes.pop(idx)
    registrar_acao('REJEIÇÃO', admin_name, f"Rejeitou [{comp_id}] ({comp['tipo']}) {formatar_valor(comp['valor_bruto'])}. Motivo: {motivo}")
    return f"🚫 [{admin_name}] rejeitou:\n`{formatar_valor(comp['valor_bruto'])} ({comp['tipo']}) - Líq: {formatar_valor(comp['valor_liquido'])}`\nMotivo: {motivo}"

def aprova_callback(comp_id, admin_user):
    return aprovar_pendente(comp_id, get_username(admin_user))

def rejeita_callback(comp_id, admin_user, motivo):
    return rejeitar_pendente(comp_id, get_username(admin_user), motivo)

# ========== RELATÓRIOS E EXTRATOS ==========
def extrato_visual(periodo="hoje"):
    fuso = pytz.timezone('America/Sao_Paulo')
    hoje_dt = datetime.now(fuso)
    data_format = "%d/%m/%Y"
    if periodo == "hoje":
        data_ini_dt = data_fim_dt = hoje_dt
        titulo_periodo = hoje_dt.strftime(data_format)
    elif "7" in periodo:
        data_fim_dt = hoje_dt
        data_ini_dt = hoje_dt - timedelta(days=6)
        titulo_periodo = f"{data_ini_dt.strftime(data_format)} a {data_fim_dt.strftime(data_format)}"
    else:
        data_ini_dt = data_fim_dt = hoje_dt
        titulo_periodo = hoje_dt.strftime(data_format)

    def dentro(dt_str):
        try:
            dt_obj = datetime.strptime(dt_str, data_format)
            return data_ini_dt.date() <= dt_obj.date() <= data_fim_dt.date()
        except Exception:
            return False

    linhas = [f"📄 *Extrato Detalhado — {titulo_periodo}*"]

    total_bruto_pix = 0.0
    total_bruto_cartao = 0.0
    total_pagamentos = 0.0

    aprovados = [x for x in comprovantes if dentro(x.get("data", ""))]
    for idx, c in enumerate(aprovados, start=1):
        tipo = c.get("tipo", "")
        linhas.append(
            f"{idx}️⃣ [Aprovado]\n"
            f"💸 Bruto: {formatar_valor(c['valor_bruto'])}\n"
            f"✅ Líquido: {formatar_valor(c['valor_liquido'])}\n"
            f"💳 Tipo: {tipo}\n"
            f"⏰ Hora: {c.get('hora', '')} {c.get('data', '')}"
        )
        if "PIX" in tipo.upper():
            total_bruto_pix += c["valor_bruto"]
        else:
            total_bruto_cartao += c["valor_bruto"]

    pend = [x for x in comprovantes_pendentes if dentro(x.get("data", ""))]
    for c in pend:
        linhas.append(
            f"⏳ [Pendente]\n"
            f"💸 Bruto: {formatar_valor(c['valor_bruto'])}\n"
            f"✅ Líquido: {formatar_valor(c['valor_liquido'])}\n"
            f"💳 Tipo: {c.get('tipo','')}\n"
            f"⏰ Hora: {c.get('hora','')} {c.get('data','')}"
        )

    pays = [x for x in pagamentos if dentro(x.get("data", ""))]
    for p in pays:
        linhas.append(
            f"💵 [Pagamento feito]\n"
            f"🏷 Valor: {formatar_valor(p['valor'])}\n"
            f"⏰ Hora: {p.get('hora','')} {p.get('data','')}"
        )
        total_pagamentos += p["valor"]

    linhas.append("\n*Totais finais (bruto):*")
    linhas.append(f" • PIX: `{formatar_valor(total_bruto_pix)}`")
    linhas.append(f" • Cartões: `{formatar_valor(total_bruto_cartao)}`")
    linhas.append(f" • Pagamentos registrados: `{formatar_valor(total_pagamentos)}`")

    if len(linhas) == 1:
        linhas.append("_Nenhum lançamento no período._")
    return "\n\n".join(linhas)

def relatorio_lucro(periodo="dia"):
    fuso = pytz.timezone('America/Sao_Paulo')
    dt_now = datetime.now(fuso)
    data_format = "%d/%m/%Y"
    if periodo == "dia":
        data_ini_dt = data_fim_dt = dt_now
        titulo = f"Lucro do dia {dt_now.strftime(data_format)}"
    elif periodo == "semana":
        data_fim_dt = dt_now
        data_ini_dt = dt_now - timedelta(days=6)
        titulo = f"Lucro da semana ({data_ini_dt.strftime(data_format)} a {data_fim_dt.strftime(data_format)})"
    elif periodo == "mes":
        data_ini_dt = dt_now.replace(day=1)
        data_fim_dt = dt_now
        titulo = f"Lucro do mês ({data_ini_dt.strftime(data_format)} a {data_fim_dt.strftime(data_format)})"
    else:
        data_ini_dt = data_fim_dt = dt_now
        titulo = f"Lucro do dia {dt_now.strftime(data_format)}"

    def dentro(dt_str):
        try:
            dt_obj = datetime.strptime(dt_str, data_format)
            return data_ini_dt.date() <= dt_obj.date() <= data_fim_dt.date()
        except Exception:
            return False

    total_bruto_pix = total_bruto_cartao = 0.0
    total_liquido_pix = total_liquido_cartao = 0.0
    total_lucro_pix = total_lucro_cartao = 0.0

    for c in (x for x in comprovantes if dentro(x.get("data", ""))):
        valor = c["valor_bruto"]
        tipo = c.get("tipo", "")
        liquido_loja = c["valor_liquido"]

        if "PIX" in tipo.upper():
            taxa_loja = taxa_pix
            taxa_maquina = 0.0
            lucro_pix = valor * (taxa_loja - taxa_maquina) / 100
            total_bruto_pix += valor
            total_liquido_pix += liquido_loja
            total_lucro_pix += lucro_pix
        elif "ELO" in tipo.upper():
            m = re.search(r'(\d{1,2})X', tipo.upper())
            parcelas = int(m.group(1)) if m else 1
            taxa_loja = taxas_elo.get(parcelas, 0)
            taxa_maquina = taxas_reais_elo.get(parcelas, 0)
            lucro_elo = valor * (taxa_loja - taxa_maquina) / 100
            total_bruto_cartao += valor
            total_liquido_cartao += liquido_loja
            total_lucro_cartao += lucro_elo
        elif "AMEX" in tipo.upper():
            m = re.search(r'(\d{1,2})X', tipo.upper())
            parcelas = int(m.group(1)) if m else 1
            taxa_loja = taxas_amex.get(parcelas, 0)
            taxa_maquina = taxas_reais_amex.get(parcelas, 0)
            lucro_amex = valor * (taxa_loja - taxa_maquina) / 100
            total_bruto_cartao += valor
            total_liquido_cartao += liquido_loja
            total_lucro_cartao += lucro_amex
        elif "X" in tipo.upper():
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

# ========== PROCESSADOR PRINCIPAL ==========
def processar_mensagem(texto, user_id, username="ADMIN"):
    """
    Ponto único de entrada para mensagens de texto (não comandos).
    Retorna string com resposta a ser enviada pelo main.py ou 'MENU_BOTAO' para abrir menu.
    """
    if texto is None:
        return None
    texto = texto.strip().lower()
    admin = is_admin(user_id)
    hora, data = get_data_hora_brasilia()

    # Calculadora direta (bruto -> líquido)
    if texto.startswith("/calc") or texto.startswith("calc ") or texto.startswith("calcular") or texto.startswith("/c ") or texto.startswith("c "):
        partes = texto.split(maxsplit=1)
        if len(partes) < 2 or not partes[1].strip():
            return ("🧮 *Calculadora*\nUse (exemplos simples): `/calc 1000 pix` ou `/c 1000` ou `/calc 1000 10x`. Se passar só o valor, assumimos PIX: `/calc 1000`")
        payload = partes[1].strip()
        valor, tipo, bandeira = extrair_valor_tipo_bandeira(payload)
        if valor is None:
            return "❌ Valor inválido. Use o formato: `1000 pix` ou `1000 10x`"
        return calculadora_simples_input(valor, tipo or "pix", bandeira)

    # Calculadora reversa (quanto cobrar para obter X líquido)
    if texto.startswith("/calc_bruto") or texto.startswith("calc_bruto") or texto.startswith("/cb") or texto.startswith("cb ") or texto.startswith("quanto cobrar"):
        partes = texto.split(maxsplit=1)
        if len(partes) < 2 or not partes[1].strip():
            return ("🧮 *Calculadora Reversa*\nUse: `/calc_bruto 500 pix` ou `/cb 500` (assume PIX) ou `/calc_bruto 500 10x`")
        payload = partes[1].strip()
        valor_liq, tipo, bandeira = extrair_valor_tipo_bandeira(payload)
        if valor_liq is None:
            return "❌ Valor inválido. Use: `500 pix` ou `500 10x`"
        return calculadora_reversa_input(valor_liq, tipo or "pix", bandeira)

    # Limpeza (admin)
    if texto == "limpar pendentes" and admin:
        return limpar_pendentes()
    if texto == "limpar tudo" and admin:
        comprovantes.clear()
        pagamentos.clear()
        solicitacoes.clear()
        comprovantes_pendentes.clear()
        log_operacoes.clear()
        return "🧹 Todos os dados foram zerados com sucesso."

    # Menu / ajuda
    if texto in ["/menu", "menu"]:
        return "MENU_BOTAO"
    if texto in ["/ajuda", "ajuda"]:
        return """🤖 *Comandos disponíveis*:

📋 Use /menu ou envie "menu" para acessar os botões de atalho!

📥 *Enviar comprovante para conferência (aprovado pelo admin):*
• `1000,00 pix`
• `1000,00 10x` ou `1000,00 elo 10x` ou `1000,00 amex 10x`

🧮 *Calculadora simples (bruto → líquido):*
• `/calc 1000 pix` ou `/c 1000` (se só passar valor assume PIX)

🧮 *Calculadora reversa (quanto cobrar para obter X líquido):*
• `/calc_bruto 500 pix` ou `/cb 500` (se só passar valor assume PIX)

⏸️ *Consultar pendentes de conferência:*
• *Admin*: `listar pendentes`

☑️ *Aprovar ou rejeitar (admin ou botão do bot):*
 • `aprovar <ID>`
 • `rejeitar <ID> <motivo>`

🔄 *Corrigir comprovante (admin):*
 • `corrigir valor <ID> 1200,00 12x`

📤 *Solicitar pagamento:*
• `solicito 300,00`

✅ *Confirmar pagamento:*
• `pagamento feito` ou `pagamento feito 300,00`

📊 *Consultas:*
• `total liquido`
• `pagamentos realizados`
• `fechamento do dia`
• `extrato`
• `extrato 7dias`
• `relatorio lucro`
• `relatorio lucro semana`
• `relatorio lucro mes`
• `meu id`
"""

    # Listagens (admin)
    if texto in ["listar pendentes", "pendentes"]:
        return listar_pendentes()
    if texto == "listar pagamentos" and admin:
        return listar_pagamentos()
    if texto == "listar comprovantes" and admin:
        return listar_comprovantes()

    # Extratos / relatórios
    if texto in ["extrato", "extrato de hoje", "extrato do dia", "/extrato"]:
        return extrato_visual("hoje")
    if "7" in texto and "extrato" in texto:
        return extrato_visual("7dias")
    if texto == "fechamento do dia" or texto == "fechamento diário":
        return extrato_visual("hoje")
    if texto.startswith("relatorio lucro"):
        if "semana" in texto:
            return relatorio_lucro("semana")
        elif "mes" in texto:
            return relatorio_lucro("mes")
        else:
            return relatorio_lucro("dia")

    # Aprovar / rejeitar (admin)
    if texto.startswith("aprovar") and admin:
        partes = texto.split()
        if len(partes) < 2:
            return "❌ Use: aprovar <ID do pendente>."
        comp_id = partes[1]
        return aprovar_pendente(comp_id, username)

    if texto.startswith("rejeitar") and admin:
        partes = texto.split()
        if len(partes) < 3:
            return "❌ Use: rejeitar <ID> <motivo>."
        comp_id, motivo = partes[1], " ".join(partes[2:])
        return rejeitar_pendente(comp_id, username, motivo)

    # Saldo, pagamentos, solicitações
    if texto == "total liquido":
        total_liquido = credito_disponivel()
        return f"💰 *Valor líquido disponível (apenas aprovados, já descontados pagamentos):* `{formatar_valor(total_liquido)}`"
    if texto == "pagamentos realizados":
        total = sum(p["valor"] for p in pagamentos)
        return f"✅ *Total pago até agora:* `{formatar_valor(total)}`"

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
        return f"✅ *Pagamento registrado com sucesso!*\n💵 Valor: `{formatar_valor(valor)}`\n📉 Saldo anterior: `{formatar_valor(saldo_anterior)}` \n💰 Novo saldo disponível: `{formatar_valor(novo_saldo)}`"

    if texto == "meu id":
        return f"Seu user_id: {user_id}\nEste chat_id: {username}"

    # Entrada direta de comprovante (ex.: "1000 pix" cria pendente)
    valor, tipo, bandeira = extrair_valor_tipo_bandeira(texto)
    if valor and tipo:
        liquido, taxa = calcular_valor_liquido_bandeira(valor, tipo, bandeira)
        if liquido is None:
            return "❌ Tipo de pagamento inválido. Exemplo: 1000 pix ou 2000 10x"
        uuid_id = str(uuid.uuid4())
        comprovantes_pendentes.append({
            "id": uuid_id,
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "tipo": (f"{bandeira.upper()} {tipo.upper()}" if bandeira else tipo.upper()),
            "hora": hora,
            "data": data
        })
        return (
            f"⏳ Comprovante aguardando confirmação\n"
            f"ID#{uuid_id}\n"
            f"💰 Valor bruto: {formatar_valor(valor)}\n"
            f"💳 Tipo: {(f'{bandeira.upper()} {tipo.upper()}' if bandeira else tipo.upper())}\n"
            f"🕰️ Horário: {hora} {data}\n"
            f"🧾 Taxa aplicada: {taxa:.2f}%\n\n✅ Valor líquido a liberar: {formatar_valor(liquido)}\n\nAguarde conferência."
        )

    return None
