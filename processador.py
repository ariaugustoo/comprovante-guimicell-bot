import re
from datetime import datetime

comprovantes = []

# Tabela de taxas por numero de parcelas
taxas_cartao = {
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

def normalizar_valor(valor_str):
    """Corrige valores com ponto e virgula misturados, ex: 1.550.00 ou 1,550.00"""
    valor_str = valor_str.replace('.', '').replace(',', '.')
    return float(valor_str)

def calcular_taxa(valor, metodo, parcelas=1):
    if metodo == 'pix':
        taxa_percentual = 0.2
    elif metodo == 'cartao':
        taxa_percentual = taxas_cartao.get(parcelas, 0)
    else:
        taxa_percentual = 0
    valor_liquido = valor * (1 - taxa_percentual / 100)
    return round(taxa_percentual, 2), round(valor_liquido, 2)

def processar_mensagem(mensagem, user_id=None):
    mensagem = mensagem.lower()

    if 'pix' in mensagem:
        match = re.search(r"([\d.,]+)", mensagem)
        if match:
            valor = normalizar_valor(match.group(1))
            taxa, valor_liquido = calcular_taxa(valor, 'pix')
            comprovantes.append({
                'valor': valor,
                'metodo': 'PIX',
                'parcelas': 1,
                'taxa': taxa,
                'liquido': valor_liquido,
                'pago': False,
                'hora': datetime.now().strftime("%H:%M")
            })
            return f"📄 Comprovante analisado:\n💰 Valor bruto: R$ {valor:.2f}\n💳 Parcelas: 1x (PIX)\n⏰ Horario: {datetime.now().strftime('%H:%M')}\n📉 Taxa aplicada: {taxa:.2f}%\n✅ Valor liquido a pagar: R$ {valor_liquido:.2f}"

    elif re.search(r'([\d.,]+)\s*(\d{1,2})x', mensagem):
        match = re.search(r'([\d.,]+)\s*(\d{1,2})x', mensagem)
        if match:
            valor = normalizar_valor(match.group(1))
            parcelas = int(match.group(2))
            taxa, valor_liquido = calcular_taxa(valor, 'cartao', parcelas)
            comprovantes.append({
                'valor': valor,
                'metodo': 'CARTAO',
                'parcelas': parcelas,
                'taxa': taxa,
                'liquido': valor_liquido,
                'pago': False,
                'hora': datetime.now().strftime("%H:%M")
            })
            return f"📄 Comprovante analisado:\n💰 Valor bruto: R$ {valor:.2f}\n💳 Parcelas: {parcelas}x\n⏰ Horario: {datetime.now().strftime('%H:%M')}\n📉 Taxa aplicada: {taxa:.2f}%\n✅ Valor liquido a pagar: R$ {valor_liquido:.2f}"

    elif mensagem == '✅':
        for comp in reversed(comprovantes):
            if not comp['pago']:
                comp['pago'] = True
                return "✅ Ultimo comprovante marcado como pago."
        return "Nenhum comprovante pendente encontrado para marcar como pago."

    elif mensagem.startswith('total que devo'):
        return total_pendentes()

    elif mensagem.startswith('listar pendentes'):
        return listar_pendentes()

    elif mensagem.startswith('listar pagos'):
        return listar_pagos()

    elif mensagem.startswith('total geral'):
        total = sum(c['valor'] for c in comprovantes)
        liquido = sum(c['liquido'] for c in comprovantes)
        return f"📊 Total geral bruto: R$ {total:.2f}\n💸 Total liquido: R$ {liquido:.2f}"

    elif mensagem.startswith('ultimo comprovante'):
        if comprovantes:
            c = comprovantes[-1]
            return f"📋 Ultimo comprovante:\n💰 Valor bruto: R$ {c['valor']:.2f}\n💳 Parcelas: {c['parcelas']}x\n📉 Taxa: {c['taxa']:.2f}%\n✅ Liquido: R$ {c['liquido']:.2f}\n📅 Hora: {c['hora']}\n🔒 Pago: {'✅' if c['pago'] else '❌'}"
        return "Nenhum comprovante registrado ainda."

    elif mensagem == 'ajuda':
        return (
            "📘 Comandos disponiveis:\n"
            "- Envie valores assim: `6499,99 pix` ou `7899,99 10x`\n"
            "- ✅ = marca ultimo comprovante como pago\n"
            "- total que devo = soma dos pendentes\n"
            "- listar pendentes = lista comprovantes nao pagos\n"
            "- listar pagos = lista pagos\n"
            "- total geral = soma de todos\n"
            "- ultimo comprovante = exibe ultimo\n"
        )

    return "❌ Formato invalido. Envie algo como '6438,90 pix' ou '7899,99 10x'."

def total_pendentes():
    total = sum(c['liquido'] for c in comprovantes if not c['pago'])
    return f"💰 Total pendente (liquido): R$ {total:.2f}"

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c['pago']]
    if not pendentes:
        return "Nenhum comprovante pendente."
    msg = "📋 Comprovantes pendentes:\n"
    for i, c in enumerate(pendentes, 1):
        msg += f"{i}. R$ {c['liquido']:.2f} ({c['parcelas']}x - {c['metodo']})\n"
    return msg

def listar_pagos():
    pagos = [c for c in comprovantes if c['pago']]
    if not pagos:
        return "Nenhum comprovante marcado como pago."
    msg = "📗 Comprovantes pagos:\n"
    for i, c in enumerate(pagos, 1):
        msg += f"{i}. R$ {c['liquido']:.2f} ({c['parcelas']}x - {c['metodo']})\n"
    return msg
