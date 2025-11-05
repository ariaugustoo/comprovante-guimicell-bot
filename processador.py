import os
import re
import uuid
from datetime import datetime, timedelta
import pytz

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

def formatar_valor(valor):
    try: valor = float(valor)
    except Exception: valor = 0.0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_data_hora_brasilia():
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    return agora.strftime('%H:%M'), agora.strftime('%d/%m/%Y')

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
            f"⏰ Hora: {c['hora']}\n"
        )
    return "\n".join(linhas)

def aprovar_pendente(comp_id, admin_name):
    idx = next((i for i, c in enumerate(comprovantes_pendentes) if c["id"] == comp_id), None)
    if idx is None:
        return "❌ Esse comprovante já foi aprovado/rejeitado ou não está mais pendente."
    comp = comprovantes_pendentes.pop(idx)
    comprovantes.append(comp)
    registrar_acao('APROVAÇÃO', admin_name, f"Aprovou [{comp_id}]: {formatar_valor(comp['valor_bruto'])} ({comp['tipo']})")
    return f"""✅ [{admin_name}] aprovou:\n`{formatar_valor(comp['valor_bruto'])} ({comp['tipo']}) - Líq: {formatar_valor(comp['valor_liquido'])}`\nSaldo liberado!"""

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

def processar_mensagem(texto, user_id, username="ADMIN"):
    texto = texto.strip().lower()
    admin = is_admin(user_id)
    hora, data = get_data_hora_brasilia()

    if texto == "limpar pendentes" and admin:
        return limpar_pendentes()

    if texto in ["/menu", "menu"]:
        return "MENU_BOTAO"

    if texto in ["listar pendentes", "pendentes"]:
        return listar_pendentes()

    # ENTRADA DE NOVO COMPROVANTE (com id único)
    valor, tipo, bandeira = extrair_valor_tipo_bandeira(texto)
    if valor and tipo:
        liquido, taxa = calcular_valor_liquido_bandeira(valor, tipo, bandeira)
        if liquido is None:
            return "❌ Tipo de pagamento inválido. Exemplo: 1000,00 pix ou 2000,00 10x"
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
            f"🧾 Taxa aplicada: {taxa:.2f}%\n"
            f"✅ Valor líquido a liberar: {formatar_valor(liquido)}\n"
            f"\nAguarde conferência."
        )

    # Aprovar e rejeitar usando id
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

    # saldo total liquido
    if texto == "total liquido":
        total_liquido = credito_disponivel()
        return f"💰 *Valor líquido disponível (apenas aprovados, já descontados pagamentos):* `{formatar_valor(total_liquido)}`"

    if texto == "ajuda":
        return """🤖 *Comandos disponíveis*:

📋 Use /menu ou envie "menu" para acessar os botões de atalho!

📥 *Enviar comprovante para conferência (aprovado pelo admin):*
• `1000,00 pix`
• `1000,00 10x` ou `1000,00 elo 10x` ou `1000,00 amex 10x`

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

    return None
