import re

GROUP_ID = -1002626449000

# Tabela de taxas
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}
taxa_pix = 0.2

# Histórico dos comprovantes
comprovantes = []

def normalizar_valor(valor_str):
    return float(valor_str.replace('.', '').replace(',', '.'))

def calcular_taxa(valor, tipo, parcelas=None):
    if tipo == 'pix':
        taxa = taxa_pix
    elif tipo == 'cartao' and parcelas in taxas_cartao:
        taxa = taxas_cartao[parcelas]
    else:
        return None
    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def processar_mensagem(bot, message):
    texto = message.text.lower()

    if texto.startswith('/ping'):
        bot.send_message(message.chat.id, "🤖 Bot ativo e funcionando!")
        return

    if texto == "ajuda":
        comandos = (
            "📋 *Comandos disponíveis:*\n"
            "`100,00 pix` → Aplica taxa PIX\n"
            "`1500,00 3x` → Aplica taxa Cartão 3x\n"
            "`total que devo` → Soma pendentes\n"
            "`listar pendentes` → Lista não pagos\n"
            "`listar pagos` → Lista pagos\n"
            "`✅` → Marca último como pago\n"
            "`último comprovante` → Mostra o último\n"
            "`total geral` → Total de todos\n"
        )
        bot.send_message(message.chat.id, comandos, parse_mode="Markdown")
        return

    if texto.startswith("total que devo"):
        total = sum(c['liquido'] for c in comprovantes if not c['pago'])
        bot.send_message(message.chat.id, f"💰 Total em aberto: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return

    if texto.startswith("total geral"):
        total = sum(c['liquido'] for c in comprovantes)
        bot.send_message(message.chat.id, f"📊 Total geral: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return

    if texto.startswith("listar pendentes"):
        pendentes = [c for c in comprovantes if not c['pago']]
        if not pendentes:
            bot.send_message(message.chat.id, "✅ Nenhum pagamento pendente.")
            return
        resposta = "📌 *Comprovantes Pendentes:*\n"
        for c in pendentes:
            resposta += f"• R$ {c['valor']:,.2f} - {c['parcelas']}x - 💳 {c['liquido']:,.2f}\n".replace(",", "X").replace(".", ",").replace("X", ".")
        bot.send_message(message.chat.id, resposta, parse_mode="Markdown")
        return

    if texto.startswith("listar pagos"):
        pagos = [c for c in comprovantes if c['pago']]
        if not pagos:
            bot.send_message(message.chat.id, "🕐 Nenhum comprovante marcado como pago.")
            return
        resposta = "✅ *Comprovantes Pagos:*\n"
        for c in pagos:
            resposta += f"• R$ {c['valor']:,.2f} - {c['parcelas']}x - 💳 {c['liquido']:,.2f}\n".replace(",", "X").replace(".", ",").replace("X", ".")
        bot.send_message(message.chat.id, resposta, parse_mode="Markdown")
        return

    if texto.startswith("último comprovante"):
        if comprovantes:
            c = comprovantes[-1]
            status = "✅ PAGO" if c['pago'] else "⏳ PENDENTE"
            msg = f"📄 Último comprovante:\n💰 R$ {c['valor']:,.2f}\n📉 Líquido: R$ {c['liquido']:,.2f}\n💳 {c['parcelas']}x\n{status}".replace(",", "X").replace(".", ",").replace("X", ".")
            bot.send_message(message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "Nenhum comprovante registrado.")
        return

    if texto == "✅":
        for c in reversed(comprovantes):
            if not c['pago']:
                c['pago'] = True
                bot.send_message(message.chat.id, "✅ Último comprovante marcado como pago!")
                return
        bot.send_message(message.chat.id, "Nenhum comprovante pendente para marcar como pago.")
        return

    match_pix = re.match(r"([\d\.,]+)\s*pix", texto)
    match_cartao = re.match(r"([\d\.,]+)\s*(\d{1,2})x", texto)

    if match_pix:
        valor = normalizar_valor(match_pix.group(1))
        liquido, taxa = calcular_taxa(valor, 'pix')
        comprovantes.append({'valor': valor, 'liquido': liquido, 'tipo': 'pix', 'parcelas': 1, 'pago': False})
        bot.send_message(message.chat.id, f"📄 Comprovante analisado:\n💰 Valor bruto: R$ {valor:,.2f}\n⏰ Taxa aplicada: {taxa:.2f}%\n✅ Valor líquido: R$ {liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return

    elif match_cartao:
        valor = normalizar_valor(match_cartao.group(1))
        parcelas = int(match_cartao.group(2))
        if parcelas not in taxas_cartao:
            bot.send_message(message.chat.id, f"❌ Parcelamento {parcelas}x não suportado.")
            return
        liquido, taxa = calcular_taxa(valor, 'cartao', parcelas)
        comprovantes.append({'valor': valor, 'liquido': liquido, 'tipo': 'cartao', 'parcelas': parcelas, 'pago': False})
        bot.send_message(message.chat.id, f"📄 Comprovante analisado:\n💰 Valor bruto: R$ {valor:,.2f}\n💳 Parcelas: {parcelas}x\n📉 Taxa aplicada: {taxa:.2f}%\n✅ Valor líquido: R$ {liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return
