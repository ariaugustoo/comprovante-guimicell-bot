import re
from datetime import datetime

GROUP_ID = -1002122662652
TAXA_PIX = 0.002
TAXAS_CARTAO = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719,
    6: 0.0829, 7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088,
    11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
    16: 0.1519, 17: 0.1589, 18: 0.1684
}

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def processar_mensagem(bot, mensagem):
    texto = mensagem.text.strip() if mensagem.text else ""

    if not texto:
        bot.send_message(mensagem.chat.id, "❌ Mensagem inválida.")
        return

    # 🔍 Identifica valor e tipo (PIX ou cartão com parcelas)
    padrao_pix = re.match(r"([\d\.,]+)\s*pix", texto.lower())
    padrao_cartao = re.match(r"([\d\.,]+)\s*(\d{1,2})x", texto.lower())

    if padrao_pix:
        valor_bruto = float(padrao_pix.group(1).replace(".", "").replace(",", "."))
        taxa = TAXA_PIX
        valor_liquido = valor_bruto * (1 - taxa)
        mensagem_final = (
            "📄 *Comprovante analisado:*\n"
            f"💰 Valor bruto: {formatar_valor(valor_bruto)}\n"
            f"🏦 Tipo: PIX\n"
            f"📉 Taxa aplicada: {taxa * 100:.2f}%\n"
            f"✅ Valor líquido a pagar: {formatar_valor(valor_liquido)}"
        )
        bot.send_message(GROUP_ID, mensagem_final, parse_mode='Markdown')
        return

    elif padrao_cartao:
        valor_bruto = float(padrao_cartao.group(1).replace(".", "").replace(",", "."))
        parcelas = int(padrao_cartao.group(2))
        taxa = TAXAS_CARTAO.get(parcelas)

        if taxa:
            valor_liquido = valor_bruto * (1 - taxa)
            mensagem_final = (
                "📄 *Comprovante analisado:*\n"
                f"💰 Valor bruto: {formatar_valor(valor_bruto)}\n"
                f"💳 Parcelas: {parcelas}x\n"
                f"📉 Taxa aplicada: {taxa * 100:.2f}%\n"
                f"✅ Valor líquido a pagar: {formatar_valor(valor_liquido)}"
            )
            bot.send_message(GROUP_ID, mensagem_final, parse_mode='Markdown')
        else:
            bot.send_message(GROUP_ID, "❌ Quantidade de parcelas não suportada.")
        return

    # Se não identificar o tipo:
    bot.send_message(GROUP_ID, "❌ Não consegui identificar o tipo de comprovante.\nEnvie no formato:\n\n*Exemplo PIX:* 6438,76 pix\n*Exemplo Cartão:* 7999,99 10x", parse_mode='Markdown')
