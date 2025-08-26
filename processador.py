import re
from datetime import datetime

TAXAS_CARTAO = {
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
    18: 16.84,
}

def normalizar_valor(valor_str):
    valor_str = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(valor_str)
    except ValueError:
        return None

def processar_comprovante(texto, tipo=None, parcelas=None):
    valor_bruto = None
    horario = None
    valor_liquido = None
    taxa = 0.0

    padrao_valor = r'((?:\d{1,3}(?:\.\d{3})*|\d+)(?:,\d{2})?)'
    padrao_horario = r'(\d{2}:\d{2})'

    valor_match = re.search(padrao_valor, texto)
    if valor_match:
        valor_bruto = normalizar_valor(valor_match.group(1))

    horario_match = re.search(padrao_horario, texto)
    if horario_match:
        horario = horario_match.group(1)

    if tipo == "pix":
        taxa = 0.2
    elif tipo == "cartao" and parcelas in TAXAS_CARTAO:
        taxa = TAXAS_CARTAO[parcelas]
    else:
        taxa = 0.0

    if valor_bruto is not None:
        valor_liquido = valor_bruto * (1 - taxa / 100)

    return {
        "valor_bruto": valor_bruto,
        "horario": horario,
        "parcelas": parcelas,
        "taxa": taxa,
        "valor_liquido": valor_liquido
    }

def calcular_valor_liquido(valor, tipo, parcelas=None):
    taxa = 0.0
    if tipo == "pix":
        taxa = 0.2
    elif tipo == "cartao" and parcelas in TAXAS_CARTAO:
        taxa = TAXAS_CARTAO[parcelas]

    valor_liquido = valor * (1 - taxa / 100)
    return valor_liquido, taxa

def formatar_comprovante(dados):
    mensagem = "📄 *Comprovante analisado:*\n"
    if dados["valor_bruto"] is not None:
        mensagem += f"💰 *Valor bruto:* R$ {dados['valor_bruto']:,.2f}\n"
    if dados["parcelas"] is not None:
        mensagem += f"💳 *Parcelas:* {dados['parcelas']}x\n"
    if dados["horario"] is not None:
        mensagem += f"⏰ *Horário:* {dados['horario']}\n"
    mensagem += f"📉 *Taxa aplicada:* {dados['taxa']}%\n"
    if dados["valor_liquido"] is not None:
        mensagem += f"✅ *Valor líquido a pagar:* R$ {dados['valor_liquido']:,.2f}\n"
    return mensagem
