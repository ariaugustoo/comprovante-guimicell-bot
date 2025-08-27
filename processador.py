import re
from datetime import datetime
from pytz import timezone

# Tabela de taxas por número de parcelas (crédito)
TAXAS_CREDITO = {
    1: 4.39,
    2: 5.19,
    3: 6.19,
    4: 6.59,
    5: 7.19,
    6: 8.29,
    7: 9.19,
    8: 9.99,
    9: 10.29,
    10: 10.88,
    11: 11.99,
    12: 12.52,
    13: 13.69,
    14: 14.19,
    15: 14.69,
    16: 15.19,
    17: 15.89,
    18: 16.84
}

# Taxa PIX
TAXA_PIX = 0.2

# Banco de dados temporário (em memória)
comprovantes = []

def normalizar_valor(valor_str):
    """Converte uma string com vírgula ou ponto em float."""
    valor_str = valor_str.replace('.', '').replace(',', '.')
    return float(valor_str)

def calcular_taxa(valor, tipo, parcelas=None):
    if tipo == "pix":
        taxa_aplicada = TAXA_PIX
    elif tipo == "cartao" and parcelas:
        taxa_aplicada = TAXAS_CREDITO.get(parcelas, 0)
    else:
        taxa_aplicada = 0
    valor_liquido = valor * (1 - taxa_aplicada / 100)
    return round(taxa_aplicada, 2), round(valor_liquido, 2)

def processar_mensagem(texto):
    texto = texto.lower()
    valor_bruto = None
    parcelas = None
    tipo_pagamento = None

    # Detectar tipo de pagamento
    if "pix" in texto:
        tipo_pagamento = "pix"
    elif "x" in texto:
        tipo_pagamento = "cartao"

    # Extrair valor
    match_valor = re.search(r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)', texto)
    if match_valor:
        valor_bruto = normalizar_valor(match_valor.group(1))

    # Extrair número de parcelas
    match_parcelas = re.search(r'(\d{1,2})x', texto)
    if match_parcelas:
        parcelas = int(match_parcelas.group(1))

    # Calcular taxa e valor líquido
    if valor_bruto and tipo_pagamento:
        taxa, valor_liquido = calcular_taxa(valor_bruto, tipo_pagamento, parcelas)
        horario = datetime.now(timezone("America/Sao_Paulo")).strftime('%H:%M')
        comprovante = {
            "valor_bruto": valor_bruto,
            "parcelas": parcelas,
            "horario": horario,
            "taxa": taxa,
            "valor_liquido": valor_liquido,
            "pago": False
        }
        comprovantes.append(comprovante)
        return comprovante
    return None

def formatar_comprovante(c):
    return (
        f"📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {c['valor_bruto']:.2f}\n"
        f"💳 Parcelas: {c['parcelas'] if c['parcelas'] else '---'}\n"
        f"⏰ Horário: {c['horario']}\n"
        f"📉 Taxa aplicada: {c['taxa']}%\n"
        f"✅ Valor líquido a pagar: R$ {c['valor_liquido']:.2f}"
    )

def marcar_comprovante_pago():
    for c in reversed(comprovantes):
        if not c["pago"]:
            c["pago"] = True
            return f"✅ Último comprovante marcado como pago com sucesso!"
    return "Nenhum comprovante pendente encontrado."

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."
    msg = "*📋 Comprovantes pendentes:*\n\n"
    for i, c in enumerate(pendentes, 1):
        msg += f"{i}. 💰 R$ {c['valor_bruto']:.2f} | Parc: {c['parcelas'] or '---'} | ⏰ {c['horario']}\n"
    return msg

def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "📄 Nenhum comprovante foi marcado como pago ainda."
    msg = "*📄 Comprovantes pagos:*\n\n"
    for i, c in enumerate(pagos, 1):
        msg += f"{i}. R$ {c['valor_bruto']:.2f} | Parc: {c['parcelas'] or '---'} | ⏰ {c['horario']}\n"
    return msg

def total_pendentes():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    return f"💰 Total a pagar (pendentes): *R$ {total:.2f}*"

def total_geral():
    total = sum(c["valor_liquido"] for c in comprovantes)
    return f"📊 Total geral (todos os comprovantes): *R$ {total:.2f}*"

def ultimo_comprovante():
    if comprovantes:
        return formatar_comprovante(comprovantes[-1])
    return "Nenhum comprovante foi registrado ainda."

def comandos_suporte():
    return (
        "📚 *Comandos disponíveis:*\n"
        "• `1234,56 pix` → registra pagamento via pix\n"
        "• `1234,56 10x` → registra pagamento em 10x no cartão\n"
        "• `✅` → marca o último como pago\n"
        "• `total que devo` → mostra total dos pendentes\n"
        "• `listar pendentes` → lista os não pagos\n"
        "• `listar pagos` → lista os pagos\n"
        "• `último comprovante` → mostra o último\n"
        "• `total geral` → total de tudo\n"
        "• `ajuda` → exibe esta lista"
    )
