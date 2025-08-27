import re
from datetime import datetime

# Tabela de taxas (em %)
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}
TAXA_PIX = 0.2  # Em %

def parse_valor(valor_str):
    valor_str = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    return float(valor_str)

def calcular_liquido(valor, forma_pagamento, parcelas=1):
    if forma_pagamento == "pix":
        taxa = TAXA_PIX
    else:
        taxa = TAXAS_CARTAO.get(parcelas, 0)
    liquido = valor * (1 - taxa / 100)
    return round(liquido, 2), taxa

def processar_mensagem(update, bot, group_id):
    message = update.message
    text = message.text.lower()

    valor_match = re.search(r'(\d{1,3}(?:[\.\,]\d{3})*(?:[\.,]\d{2}))', text)
    parcelas_match = re.search(r'(\d{1,2})x', text)
    is_pix = "pix" in text

    if not valor_match:
        bot.send_message(chat_id=group_id, text="❗ Formato inválido. Envie no formato:\nEx: `7.500,00 pix` ou `4.000,00 12x`", parse_mode="Markdown")
        return

    valor = parse_valor(valor_match.group(1))
    parcelas = int(parcelas_match.group(1)) if parcelas_match else 1
    forma = "pix" if is_pix else "cartão"
    liquido, taxa = calcular_liquido(valor, forma, parcelas)

    hora = datetime.now().strftime("%H:%M")

    resposta = f"""
📄 *Comprovante analisado*:
💰 Valor bruto: R$ {valor:,.2f}
💳 Parcelas: {parcelas}x
⏰ Horário: {hora}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: R$ {liquido:,.2f}
    """.strip()

    bot.send_message(chat_id=group_id, text=resposta, parse_mode="Markdown")
