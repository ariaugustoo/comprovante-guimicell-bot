from datetime import datetime, timedelta
import pytz

comprovantes = []
pagamentos_feitos = []

taxas_cartao = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719, 6: 0.0829,
    7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088, 11: 0.1199, 12: 0.1252,
    13: 0.1369, 14: 0.1419, 15: 0.1469, 16: 0.1519, 17: 0.1589, 18: 0.1684
}

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_horario():
    fuso = pytz.timezone("America/Sao_Paulo")
    return datetime.now(fuso).strftime("%H:%M")

def parse_valor(valor_str):
    try:
        valor = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        return float(valor)
    except:
        return None

def processar_mensagem(update, context=None):
    texto = update.message.text.lower()
    valor = parse_valor(texto)

    if not valor:
        return

    if "pix" in texto:
        taxa = 0.002
        liquido = round(valor * (1 - taxa), 2)
        comprovantes.append({
            "valor_bruto": valor,
            "parcelas": "PIX",
            "taxa": taxa,
            "valor_liquido": liquido,
            "hora": formatar_horario(),
            "pago": False
        })
        mensagem = f"""📄 Comprovante analisado:
💰 Valor bruto: {formatar_valor(valor)}
💰 Tipo: PIX
⏰ Horário: {formatar_horario()}
📉 Taxa aplicada: {taxa*100:.2f}%
✅ Valor líquido a pagar: {formatar_valor(liquido)}"""
        update.message.reply_text(mensagem)

    elif "x" in texto:
        try:
            partes = texto.split("x")
            valor_total = parse_valor(partes[0])
            parcelas = int(partes[1].strip())

            if parcelas not in taxas_cartao:
                update.message.reply_text("❌ Número de parcelas inválido. Use de 1x até 18x.")
                return

            taxa = taxas_cartao[parcelas]
            liquido = round(valor_total * (1 - taxa), 2)
            comprovantes.append({
                "valor_bruto": valor_total,
                "parcelas": f"{parcelas}x",
                "taxa": taxa,
                "valor_liquido": liquido,
                "hora": formatar_horario(),
                "pago": False
            })

            mensagem = f"""📄 Comprovante analisado:
💰 Valor bruto: {formatar_valor(valor_total)}
💰 Tipo: Cartão em {parcelas}x
⏰ Horário: {formatar_horario()}
📉 Taxa aplicada: {taxa*100:.2f}%
✅ Valor líquido a pagar: {formatar_valor(liquido)}"""
            update.message.reply_text(mensagem)

        except:
            update.message.reply_text("❌ Erro ao processar o valor parcelado.")

def listar_pendentes(update, context=None):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        update.message.reply_text("✅ Todos os comprovantes foram pagos.")
        return

    msg = "📋 *Comprovantes pendentes:*\n"
    total = 0
    for c in pendentes:
        msg += f"• {formatar_valor(c['valor_liquido'])} – {c['parcelas']} – ⏰ {c['hora']}\n"
        total += c["valor_liquido"]
    msg += f"\n💰 Total: {formatar_valor(total)}"
    update.message.reply_text(msg, parse_mode="Markdown")

def listar_pagos(update, context=None):
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        update.message.reply_text("Nenhum pagamento registrado ainda.")
        return

    msg = "✅ *Comprovantes pagos:*\n"
    total = 0
    for c in pagos:
        msg += f"• {formatar_valor(c['valor_liquido'])} – {c['parcelas']} – ⏰ {c['hora']}\n"
        total += c["valor_liquido"]
    msg += f"\n💰 Total: {formatar_valor(total)}"
    update.message.reply_text(msg, parse_mode="Markdown")

def registrar_pagamento(update, context=None):
    texto = update.message.text.lower()
    valor_digitado = parse_valor(texto)

    pendentes = [c for c in comprovantes if not c["pago"]]
    total_pendente = sum(c["valor_liquido"] for c in pendentes)

    if not pendentes:
        update.message.reply_text("✅ Nenhum comprovante pendente.")
        return

    if valor_digitado:
        if valor_digitado > total_pendente:
            update.message.reply_text(f"❌ O valor excede o total devido de {formatar_valor(total_pendente)}.")
            return

        restante = valor_digitado
        for c in pendentes:
            if c["pago"]:
                continue
            if restante >= c["valor_liquido"]:
                restante -= c["valor_liquido"]
                c["pago"] = True
            else:
                c["valor_liquido"] -= restante
                restante = 0
                break
        pagamentos_feitos.append(valor_digitado)
        update.message.reply_text(f"✅ Pagamento de {formatar_valor(valor_digitado)} registrado.")
    else:
        for c in reversed(comprovantes):
            if not c["pago"]:
                c["pago"] = True
                pagamentos_feitos.append(c["valor_liquido"])
                update.message.reply_text(f"✅ Pagamento de {formatar_valor(c['valor_liquido'])} registrado.")
                break

def solicitar_pagamento(update, context=None):
    update.message.reply_text("Digite o valor que deseja solicitar:")
    context.user_data["aguardando_valor"] = True

def corrigir_valor_comando(update):
    if not comprovantes:
        update.message.reply_text("Nenhum comprovante para corrigir.")
        return
    ultimo = comprovantes[-1]
    novo_valor = parse_valor(update.message.text)
    if not novo_valor:
        update.message.reply_text("Valor inválido.")
        return
    taxa = ultimo["taxa"]
    ultimo["valor_bruto"] = novo_valor
    ultimo["valor_liquido"] = round(novo_valor * (1 - taxa), 2)
    update.message.reply_text(f"Valor corrigido para {formatar_valor(ultimo['valor_bruto'])}, líquido: {formatar_valor(ultimo['valor_liquido'])}.")

def limpar_dados():
    comprovantes.clear()
    pagamentos_feitos.clear()

def calcular_valor_liquido_total():
    return round(sum(c["valor_liquido"] for c in comprovantes if not c["pago"]), 2)

def calcular_valor_bruto_total():
    return round(sum(c["valor_bruto"] for c in comprovantes if not c["pago"]), 2)
