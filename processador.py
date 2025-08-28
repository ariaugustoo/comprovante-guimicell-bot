from datetime import datetime
from pytz import timezone

comprovantes = []
pagamentos_solicitados = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def normalizar_valor(valor_str):
    return float(valor_str.replace('.', '').replace(',', '.'))

def calcular_liquido(valor, tipo_pagamento, parcelas=None):
    if tipo_pagamento == 'pix':
        taxa = 0.2
    else:
        taxa = taxas_cartao.get(parcelas, 0)
    liquido = round(valor * (1 - taxa / 100), 2)
    return taxa, liquido

def obter_horario_brasilia():
    return datetime.now(timezone('America/Sao_Paulo')).strftime('%H:%M')

def adicionar_comprovante(valor, tipo, parcelas=None):
    taxa, liquido = calcular_liquido(valor, tipo, parcelas)
    comprovantes.append({
        'valor_bruto': valor,
        'tipo': f"{tipo.capitalize()} {parcelas}x" if parcelas else tipo.upper(),
        'horario': obter_horario_brasilia(),
        'taxa': taxa,
        'liquido': liquido,
        'pago': False
    })
    return {
        'valor_bruto': valor,
        'tipo': f"{tipo.capitalize()} {parcelas}x" if parcelas else tipo.upper(),
        'horario': obter_horario_brasilia(),
        'taxa': taxa,
        'liquido': liquido
    }

def marcar_como_pago(valor_pago):
    restante = valor_pago
    for c in comprovantes:
        if not c['pago']:
            if restante >= c['liquido']:
                restante -= c['liquido']
                c['pago'] = True
            else:
                c['liquido'] -= restante
                restante = 0
                break
    global pagamentos_solicitados
    pagamentos_solicitados = [p for p in pagamentos_solicitados if p > valor_pago]

def calcular_total_liquido_pendente():
    return round(sum(c['liquido'] for c in comprovantes if not c['pago']), 2)

def solicitar_pagamento(valor):
    pagamentos_solicitados.append(valor)

def abater_pagamento_solicitado(valor):
    solicitar_pagamento(valor)
    marcar_como_pago(valor)

def listar_comprovantes(pagos=False):
    lista = ""
    for c in comprovantes:
        if c['pago'] == pagos:
            lista += (
                f"📄 Comprovante:\n"
                f"💰 Valor bruto: R$ {c['valor_bruto']:.2f}\n"
                f"💳 Tipo: {c['tipo']}\n"
                f"⏰ Horário: {c['horario']}\n"
                f"📉 Taxa aplicada: {c['taxa']:.2f}%\n"
                f"✅ Valor líquido a pagar: R$ {c['liquido']:.2f}\n\n"
            )
    return lista if lista else "Nenhum comprovante encontrado."
