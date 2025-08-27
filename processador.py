import re
from datetime import datetime
from telegram import Message

comprovantes = []

def calcular_valor_liquido(valor, tipo, parcelas=1):
    if tipo == "pix":
        taxa = 0.2
    else:
        tabela_taxas = {
            1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
            6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
            11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
            16: 15.19, 17: 15.89, 18: 16.84
        }
        taxa = tabela_taxas.get(parcelas, 0)
    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def processar_mensagem(message: Message, bot, group_id):
    texto = message.text.strip().lower()

    if texto.startswith("✅"):
        if comprovantes:
            comprovantes[-1]["pago"] = True
            bot.send_message(chat_id=group_id, text="✅ Comprovante marcado como pago.")
    elif "total que devo" in texto:
        total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        bot.send_message(chat_id=group_id, text=f"💸 Total em aberto: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    elif "listar pendentes" in texto:
        pendentes = [c for c in comprovantes if not c["pago"]]
        if pendentes:
            resposta = "\n\n".join(
                f"📄 R$ {c['valor']:,.2f} - {c['parcelas']}x - {c['hora']} - 💰 Líquido: R$ {c['valor_liquido']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                for c in pendentes
            )
        else:
            resposta = "✅ Nenhum comprovante pendente."
        bot.send_message(chat_id=group_id, text=resposta)
    elif "listar pagos" in texto:
        pagos = [c for c in comprovantes if c["pago"]]
        if pagos:
            resposta = "\n\n".join(
                f"📄 R$ {c['valor']:,.2f} - {c['parcelas']}x - {c['hora']} - 💰 Líquido: R$ {c['valor_liquido']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                for c in pagos
            )
        else:
            resposta = "Nenhum comprovante marcado como pago ainda."
        bot.send_message(chat_id=group_id, text=resposta)
    elif "último comprovante" in texto:
        if comprovantes:
            c = comprovantes[-1]
            resposta = f"📄 Último comprovante:\n💰 Valor bruto: R$ {c['valor']:,.2f}\n💳 Parcelas: {c['parcelas']}x\n⏰ Horário: {c['hora']}\n📉 Taxa aplicada: {c['taxa']}%\n✅ Valor líquido a pagar: R$ {c['valor_liquido']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            resposta = "Nenhum comprovante registrado ainda."
        bot.send_message(chat_id=group_id, text=resposta)
    elif "total geral" in texto:
        total = sum(c["valor_liquido"] for c in comprovantes)
        bot.send_message(chat_id=group_id, text=f"📊 Total geral de todos os comprovantes: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    elif "ajuda" in texto:
        comandos = (
            "🤖 *Comandos disponíveis:*\n"
            "💬 Enviar valor + pix (ex: 6.438,76 pix)\n"
            "💬 Enviar valor + parcelas (ex: 7.899,99 10x)\n"
            "✅ para marcar como pago\n"
            "🧮 *total que devo* — total em aberto\n"
            "📋 *listar pendentes* — comprovantes não pagos\n"
            "📗 *listar pagos* — comprovantes pagos\n"
            "🕓 *último comprovante* — exibe o último\n"
            "📊 *total geral* — soma de todos os comprovantes"
        )
        bot.send_message(chat_id=group_id, text=comandos, parse_mode="Markdown")
    else:
        match_pix = re.match(r"([\d.,]+)\s*pix", texto)
        match_cartao = re.match(r"([\d.,]+)\s*(\d{1,2})x", texto)

        if match_pix:
            valor = float(match_pix.group(1).replace(".", "").replace(",", "."))
            valor_liquido, taxa = calcular_valor_liquido(valor, "pix")
            parcelas = 1
        elif match_cartao:
            valor = float(match_cartao.group(1).replace(".", "").replace(",", "."))
            parcelas = int(match_cartao.group(2))
            valor_liquido, taxa = calcular_valor_liquido(valor, "cartao", parcelas)
        else:
            return

        comprovante = {
            "valor": valor,
            "parcelas": parcelas,
            "hora": datetime.now().strftime("%H:%M"),
            "valor_liquido": valor_liquido,
            "taxa": taxa,
            "pago": False
        }
        comprovantes.append(comprovante)

        resposta = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {valor:,.2f}\n"
            f"💳 Parcelas: {parcelas}x\n"
            f"⏰ Horário: {comprovante['hora']}\n"
            f"📉 Taxa aplicada: {taxa}%\n"
            f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
        ).replace(",", "X").replace(".", ",").replace("X", ".")
        bot.send_message(chat_id=group_id, text=resposta)
