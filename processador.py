import datetime
from telegram import Update
from telegram.ext import CallbackContext

comprovantes = []

taxas_cartao = {
    i: t for i, t in zip(
        range(1, 19),
        [4.39, 5.19, 6.19, 6.59, 7.19, 8.29, 9.19, 9.99, 10.29,
         10.88, 11.99, 12.52, 13.69, 14.19, 14.69, 15.19, 15.89, 16.84]
    )
}

def normalizar_valor(texto):
    texto = texto.lower().replace("r$", "").replace(" ", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None

def processar_mensagem(update: Update, context: CallbackContext):
    texto = update.message.text.lower()
    horario = datetime.datetime.now().strftime('%H:%M')

    if "pix" in texto:
        valor = normalizar_valor(texto.replace("pix", ""))
        if valor:
            taxa = 0.2
            valor_liquido = valor * (1 - taxa / 100)
            comprovantes.append({
                "valor_bruto": valor,
                "valor_liquido": valor_liquido,
                "pago": False,
                "tipo": "PIX",
                "horario": horario
            })
            msg = (
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💰 Tipo: PIX\n"
                f"⏰ Horário: {horario}\n"
                f"📉 Taxa aplicada: {taxa:.2f}%\n"
                f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
            )
            context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        return

    if "x" in texto:
        partes = texto.split()
        valor = normalizar_valor(partes[0])
        try:
            parcelas = int(partes[1].replace("x", ""))
            taxa = taxas_cartao.get(parcelas)
            if valor and taxa:
                valor_liquido = valor * (1 - taxa / 100)
                comprovantes.append({
                    "valor_bruto": valor,
                    "valor_liquido": valor_liquido,
                    "pago": False,
                    "tipo": f"Cartão {parcelas}x",
                    "horario": horario
                })
                msg = (
                    f"📄 Comprovante analisado:\n"
                    f"💰 Valor bruto: R$ {valor:,.2f}\n"
                    f"💰 Tipo: Cartão {parcelas}x\n"
                    f"⏰ Horário: {horario}\n"
                    f"📉 Taxa aplicada: {taxa:.2f}%\n"
                    f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
                )
                context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        except:
            pass
        return

def marcar_como_pago(update: Update, context: CallbackContext):
    for comp in reversed(comprovantes):
        if not comp["pago"]:
            comp["pago"] = True
            context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Último comprovante marcado como pago.")
            return
    context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Nenhum comprovante pendente encontrado.")

def listar_pendentes(update: Update, context: CallbackContext):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Nenhum pagamento pendente.")
        return
    total = sum(c["valor_liquido"] for c in pendentes)
    linhas = [f"R$ {c['valor_liquido']:,.2f} - {c['tipo']}" for c in pendentes]
    resposta = "📌 Pendentes:\n" + "\n".join(linhas) + f"\n\n💰 Total líquido: R$ {total:,.2f}"
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

def listar_pagamentos(update: Update, context: CallbackContext):
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        context.bot.send_message(chat_id=update.effective_chat.id, text="ℹ️ Nenhum pagamento feito ainda.")
        return
    total = sum(c["valor_liquido"] for c in pagos)
    linhas = [f"R$ {c['valor_liquido']:,.2f} - {c['tipo']}" for c in pagos]
    resposta = "✅ Pagos:\n" + "\n".join(linhas) + f"\n\n💰 Total pago: R$ {total:,.2f}"
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

def solicitar_pagamento(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Digite o valor e a chave Pix para solicitar pagamento.")

def total_pendentes(update: Update, context: CallbackContext):
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"💰 Devo ao lojista: R$ {total:,.2f}")

def total_a_pagar(update: Update, context: CallbackContext):
    total = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"💰 Total bruto dos comprovantes: R$ {total:,.2f}")

def enviar_resumo_automatico(bot, group_id):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return
    total = sum(c["valor_liquido"] for c in pendentes)
    msg = f"📢 Resumo automático:\n💰 Valor total líquido pendente: R$ {total:,.2f}"
    bot.send_message(chat_id=group_id, text=msg)
