import re
from datetime import datetime
import pytz

# Taxas de cartão Guimicell por parcelas
taxas_credito = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99,
    12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19,
    17: 15.89, 18: 16.84
}

# Lista global de comprovantes
comprovantes = []

# Função principal de processamento
def processar_mensagem(texto, user_first_name="Usuário"):
    texto = texto.replace(",", ".").lower().strip()

    if "pix" in texto:
        valor = extrair_valor(texto)
        if valor:
            return calcular_pix(valor)
    elif "x" in texto:
        valor, parcelas = extrair_valor_e_parcelas(texto)
        if valor and parcelas:
            return calcular_cartao(valor, parcelas)
    return None

# Função auxiliar para extrair valor
def extrair_valor(texto):
    match = re.search(r"(\d+[.,]?\d*)", texto)
    if match:
        return float(match.group(1).replace(",", "."))
    return None

# Função auxiliar para extrair valor + parcelas
def extrair_valor_e_parcelas(texto):
    valor_match = re.search(r"(\d+[.,]?\d*)", texto)
    parcelas_match = re.search(r"(\d{1,2})x", texto)
    if valor_match and parcelas_match:
        valor = float(valor_match.group(1).replace(",", "."))
        parcelas = int(parcelas_match.group(1))
        return valor, parcelas
    return None, None

# Cálculo do valor com PIX
def calcular_pix(valor):
    taxa = 0.2
    valor_liquido = valor * (1 - taxa / 100)
    horario = obter_horario()
    salvar_comprovante("pix", valor, 0, taxa, valor_liquido, horario, False)
    return formatar_mensagem(valor, "PIX", 0, taxa, valor_liquido, horario)

# Cálculo do valor com cartão
def calcular_cartao(valor, parcelas):
    taxa = taxas_credito.get(parcelas, 0)
    valor_liquido = valor * (1 - taxa / 100)
    horario = obter_horario()
    salvar_comprovante("cartao", valor, parcelas, taxa, valor_liquido, horario, False)
    return formatar_mensagem(valor, "Cartão", parcelas, taxa, valor_liquido, horario)

# Retorna horário atual formatado
def obter_horario():
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_brasilia)
    return agora.strftime('%H:%M')

# Salva comprovante na memória
def salvar_comprovante(tipo, valor_bruto, parcelas, taxa, valor_liquido, horario, pago):
    comprovantes.append({
        "tipo": tipo,
        "valor_bruto": valor_bruto,
        "parcelas": parcelas,
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "horario": horario,
        "pago": pago
    })

# Formata mensagem de resposta
def formatar_mensagem(valor, tipo, parcelas, taxa, valor_liquido, horario):
    return (
        "📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {valor:,.2f}\n"
        f"{'💳 Parcelas: ' + str(parcelas) + 'x\n' if parcelas else ''}"
        f"⏰ Horário: {horario}\n"
        f"📉 Taxa aplicada: {taxa:.2f}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )

# Marca o último comprovante como pago
def marcar_como_pago():
    for c in reversed(comprovantes):
        if not c["pago"]:
            c["pago"] = True
            return "✅ Último comprovante marcado como pago com sucesso."
    return "⚠️ Nenhum comprovante pendente encontrado para marcar como pago."

# Lista comprovantes pendentes
def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."
    resposta = "📌 *Comprovantes Pendentes:*\n"
    for i, c in enumerate(pendentes, 1):
        resposta += (
            f"{i}. 💰 R$ {c['valor_bruto']:.2f} | {c['parcelas']}x | ⏰ {c['horario']} | 📉 {c['taxa']}% = "
            f"R$ {c['valor_liquido']:.2f}\n"
        )
    return resposta

# Lista comprovantes pagos
def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "ℹ️ Nenhum comprovante pago."
    resposta = "💵 *Comprovantes Pagos:*\n"
    for i, c in enumerate(pagos, 1):
        resposta += (
            f"{i}. 💰 R$ {c['valor_bruto']:.2f} | {c['parcelas']}x | ⏰ {c['horario']} | 📉 {c['taxa']}% = "
            f"R$ {c['valor_liquido']:.2f}\n"
        )
    return resposta

# Total geral (pagos + pendentes)
def total_geral():
    total = sum(c['valor_liquido'] for c in comprovantes)
    return f"📊 Total geral dos comprovantes: R$ {total:,.2f}"

# Total de pendentes
def total_que_devo():
    total = sum(c['valor_liquido'] for c in comprovantes if not c["pago"])
    return f"🧾 Total de pagamentos pendentes: R$ {total:,.2f}"

# Último comprovante
def ultimo_comprovante():
    if not comprovantes:
        return "ℹ️ Nenhum comprovante encontrado."
    c = comprovantes[-1]
    return (
        "📄 *Último comprovante:*\n"
        f"💰 R$ {c['valor_bruto']:.2f} | {c['parcelas']}x | ⏰ {c['horario']} | 📉 {c['taxa']}% = "
        f"R$ {c['valor_liquido']:.2f} {'✅ PAGO' if c['pago'] else '🕗 PENDENTE'}"
    )
