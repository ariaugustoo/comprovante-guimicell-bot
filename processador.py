import re
from datetime import datetime
from pytz import timezone

comprovantes = []
pagamentos = []

def parse_valor(mensagem):
    valor_str = mensagem.replace('.', '').replace(',', '.')
    try:
        return float(re.findall(r'[\d.]+', valor_str)[0])
    except (IndexError, ValueError):
        return None

def calcular_taxa(valor, parcelas=None):
    if parcelas:
        taxas = {
            1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
            7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99,
            12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19,
            17: 15.89, 18: 16.84
        }
        taxa = taxas.get(parcelas, 0)
    else:
        taxa = 0.2
    return round(valor * (taxa / 100), 2), taxa

def processar_mensagem(update):
    mensagem = update.message.text.lower()
    chat_id = update.message.chat_id
    now = datetime.now(timezone('America/Sao_Paulo')).strftime("%H:%M")

    if "pix" in mensagem:
        valor = parse_valor(mensagem)
        if valor:
            taxa_valor, taxa_percentual = calcular_taxa(valor)
            liquido = round(valor - taxa_valor, 2)
            comprovantes.append({'tipo': 'PIX', 'valor': valor, 'liquido': liquido, 'horario': now, 'pago': False})
            update.message.reply_text(
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💰 Tipo: PIX\n"
                f"⏰ Horário: {now}\n"
                f"📉 Taxa aplicada: {taxa_percentual}%\n"
                f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
            )
        else:
            update.message.reply_text("❌ Valor inválido. Tente novamente.")
        return

    parcelas_match = re.search(r'(\d+(?:[.,]\d{2})?)\s*(\d{1,2})x', mensagem)
    if parcelas_match:
        valor = float(parcelas_match.group(1).replace('.', '').replace(',', '.'))
        parcelas = int(parcelas_match.group(2))
        taxa_valor, taxa_percentual = calcular_taxa(valor, parcelas)
        liquido = round(valor - taxa_valor, 2)
        comprovantes.append({'tipo': f'{parcelas}x', 'valor': valor, 'liquido': liquido, 'horario': now, 'pago': False})
        update.message.reply_text(
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {valor:,.2f}\n"
            f"💰 Tipo: Cartão ({parcelas}x)\n"
            f"⏰ Horário: {now}\n"
            f"📉 Taxa aplicada: {taxa_percentual}%\n"
            f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
        )
        return

    if "pagamento feito" in mensagem:
        valor = parse_valor(mensagem)
        if valor:
            pagamentos.append(valor)
            update.message.reply_text(
                f"✅ Pagamento de R$ {valor:,.2f} marcado como feito com sucesso."
            )
        else:
            update.message.reply_text("❌ Valor inválido.")
        return

    if "quanto devo" in mensagem:
        total_liquido = sum(c['liquido'] for c in comprovantes if not c['pago']) - sum(pagamentos)
        update.message.reply_text(f"💰 Devo ao lojista: R$ {total_liquido:,.2f}")
        return

    if "total a pagar" in mensagem:
        total_bruto = sum(c['valor'] for c in comprovantes if not c['pago'])
        update.message.reply_text(f"💵 Total bruto (pendente): R$ {total_bruto:,.2f}")
        return

    update.message.reply_text("❌ Comando não reconhecido.\nDigite `ajuda` para ver as opções.")
