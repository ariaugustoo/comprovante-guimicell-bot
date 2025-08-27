import re
from datetime import datetime
from unidecode import unidecode

comprovantes = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99,
    12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19,
    17: 15.89, 18: 16.84
}

def normalizar_texto(texto):
    return unidecode(texto.lower().strip())

def extrair_info_comprovante(texto):
    texto = normalizar_texto(texto)
    valor = None
    parcelas = 1
    tipo = None

    valor_match = re.search(r'([\d.,]+)', texto)
    if valor_match:
        valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
        valor = float(valor_str)

    if 'pix' in texto:
        tipo = 'pix'
        parcelas = 1
    else:
        parcelas_match = re.search(r'(\d{1,2})x', texto)
        if parcelas_match:
            parcelas = int(parcelas_match.group(1))
            tipo = 'cartao'

    if valor and tipo:
        return {
            'valor_bruto': valor,
            'parcelas': parcelas,
            'tipo': tipo,
            'horario': datetime.now().strftime('%H:%M'),
            'pago': False
        }

    return None

def calcular_valor_liquido(comprovante):
    valor = comprovante['valor_bruto']
    if comprovante['tipo'] == 'pix':
        taxa = 0.2
    else:
        taxa = taxas_cartao.get(comprovante['parcelas'], 0)
    valor_liquido = valor * (1 - taxa / 100)
    comprovante['taxa'] = taxa
    comprovante['valor_liquido'] = round(valor_liquido, 2)
    return comprovante

def formatar_comprovante(comp):
    return (
        f"📄 Comprovante analisado:\n"
        f"💰 Valor bruto: R$ {comp['valor_bruto']:.2f}\n"
        f"💳 Parcelas: {comp['parcelas']}x\n"
        f"⏰ Horario: {comp['horario']}\n"
        f"📉 Taxa aplicada: {comp['taxa']}%\n"
        f"✅ Valor liquido a pagar: R$ {comp['valor_liquido']:.2f}"
    )

def marcar_como_pago():
    for comp in reversed(comprovantes):
        if not comp['pago']:
            comp['pago'] = True
            return "✅ Comprovante marcado como pago."
    return "Nenhum comprovante pendente para marcar como pago."

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c['pago']]
    if not pendentes:
        return "Nenhum comprovante pendente."
    return "\n\n".join([formatar_comprovante(c) for c in pendentes])

def listar_pagos():
    pagos = [c for c in comprovantes if c['pago']]
    if not pagos:
        return "Nenhum comprovante pago."
    return "\n\n".join([formatar_comprovante(c) for c in pagos])

def total_que_devo():
    total = sum(c['valor_liquido'] for c in comprovantes if not c['pago'])
    return f"💰 Total que voce deve pagar: R$ {total:.2f}"

def total_geral():
    total = sum(c['valor_liquido'] for c in comprovantes)
    return f"📊 Total geral de comprovantes: R$ {total:.2f}"

def ultimo_comprovante():
    if not comprovantes:
        return "Nenhum comprovante registrado ainda."
    return formatar_comprovante(comprovantes[-1])

def comandos_suporte():
    return (
        "📋 *Comandos disponiveis:*\n"
        "1️⃣ `123,45 pix` - Registra PIX com taxa de 0.2%\n"
        "2️⃣ `789,99 10x` - Registra cartao com taxa da tabela\n"
        "3️⃣ `✅` - Marca ultimo comprovante como pago\n"
        "4️⃣ `total que devo` - Soma comprovantes pendentes\n"
        "5️⃣ `listar pendentes` - Lista comprovantes em aberto\n"
        "6️⃣ `listar pagos` - Lista comprovantes ja pagos\n"
        "7️⃣ `ultimo comprovante` - Mostra o ultimo enviado\n"
        "8️⃣ `total geral` - Total de tudo\n"
    )
