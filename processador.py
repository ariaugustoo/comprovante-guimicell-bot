from datetime import datetime
import re

admin_id = os.getenv("ADMIN_ID")  # pode configurar como string

comprovantes = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def normalizar_valor(texto):
    return float(texto.replace(",", ".").strip())

def calcular_valor_liquido(valor_bruto, parcelas=None):
    if parcelas:
        taxa = taxas_cartao.get(parcelas, 0) / 100
    else:
        taxa = 0.002  # 0.2% para PIX
    return round(valor_bruto * (1 - taxa), 2), taxa

def extrair_info(mensagem):
    valor_match = re.search(r"(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})", mensagem)
    parcelas_match = re.search(r"(\d{1,2})x", mensagem.lower())

    if not valor_match:
        return None, None

    valor_bruto = normalizar_valor(valor_match.group(1))
    parcelas = int(parcelas_match.group(1)) if parcelas_match else None

    return valor_bruto, parcelas

def formatar_comprovante(c):
    tipo = "💳 Cartão" if c["parcelas"] else "🏦 PIX"
    texto = f"""📄 Comprovante analisado:
💰 Valor bruto: R$ {c['valor_bruto']:.2f}
{f"💳 Parcelas: {c['parcelas']}x" if c['parcelas'] else ""}
⏰ Horário: {c['hora']}
📉 Taxa aplicada: {round(c['taxa'] * 100, 2)}%
✅ Valor líquido a pagar: R$ {c['valor_liquido']:.2f}
"""
    return texto

def processar_mensagem(update, context):
    user_id = str(update.message.from_user.id)
    texto = update.message.text.strip()
    chat_id = update.message.chat_id

    if texto == "✅":
        if comprovantes:
            comprovantes[-1]["pago"] = True
            context.bot.send_message(chat_id=chat_id, text="✅ Último comprovante marcado como pago.")
        return

    if texto.lower() == "total que devo":
        total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        context.bot.send_message(chat_id=chat_id, text=f"💸 Total pendente: R$ {total:.2f}")
        return

    if texto.lower() == "listar pendentes":
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            context.bot.send_message(chat_id=chat_id, text="✅ Nenhum pagamento pendente.")
        else:
            for c in pendentes:
                context.bot.send_message(chat_id=chat_id, text=formatar_comprovante(c))
        return

    if texto.lower() == "listar pagos":
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            context.bot.send_message(chat_id=chat_id, text="📭 Nenhum comprovante pago ainda.")
        else:
            for c in pagos:
                context.bot.send_message(chat_id=chat_id, text=formatar_comprovante(c))
        return

    if texto.lower() == "último comprovante":
        if comprovantes:
            context.bot.send_message(chat_id=chat_id, text=formatar_comprovante(comprovantes[-1]))
        else:
            context.bot.send_message(chat_id=chat_id, text="🚫 Nenhum comprovante registrado ainda.")
        return

    if texto.lower() == "total geral":
        total = sum(c["valor_liquido"] for c in comprovantes)
        context.bot.send_message(chat_id=chat_id, text=f"📊 Total geral: R$ {total:.2f}")
        return

    valor, parcelas = extrair_info(texto)
    if valor is not None:
        valor_liquido, taxa = calcular_valor_liquido(valor, parcelas)
        hora = datetime.now().strftime("%H:%M")
        comprovantes.append({
            "valor_bruto": valor,
            "valor_liquido": valor_liquido,
            "parcelas": parcelas,
            "taxa": taxa,
            "hora": hora,
            "pago": False
        })
        context.bot.send_message(chat_id=chat_id, text=formatar_comprovante(comprovantes[-1]))
    else:
        context.bot.send_message(chat_id=chat_id, text="❌ Não entendi o valor. Tente novamente.")

def listar_pendentes(update, context):
    chat_id = update.message.chat_id
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        context.bot.send_message(chat_id=chat_id, text="✅ Nenhum pagamento pendente.")
    else:
        for c in pendentes:
            context.bot.send_message(chat_id=chat_id, text=formatar_comprovante(c))

def limpar_tudo(update, context):
    if str(update.message.from_user.id) != admin_id:
        context.bot.send_message(chat_id=update.message.chat_id, text="❌ Comando restrito ao administrador.")
        return
    comprovantes.clear()
    context.bot.send_message(chat_id=update.message.chat_id, text="🧹 Todos os comprovantes foram apagados.")

def corrigir_valor(update, context):
    if str(update.message.from_user.id) != admin_id:
        context.bot.send_message(chat_id=update.message.chat_id, text="❌ Comando restrito ao administrador.")
        return
    if not comprovantes:
        context.bot.send_message(chat_id=update.message.chat_id, text="🚫 Nenhum comprovante para corrigir.")
        return
    texto = update.message.text.strip()
    valor = re.search(r"(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})", texto)
    if valor:
        novo_valor = normalizar_valor(valor.group(1))
        parcelas = comprovantes[-1]["parcelas"]
        novo_liquido, nova_taxa = calcular_valor_liquido(novo_valor, parcelas)
        comprovantes[-1].update({
            "valor_bruto": novo_valor,
            "valor_liquido": novo_liquido,
            "taxa": nova_taxa
        })
        context.bot.send_message(chat_id=update.message.chat_id, text="✅ Valor corrigido com sucesso.")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="❌ Valor inválido para correção.")

def resumo_total():
    pendentes = [c for c in comprovantes if not c["pago"]]
    pagos = [c for c in comprovantes if c["pago"]]
    total_pendentes = sum(c["valor_liquido"] for c in pendentes)
    total_pagos = sum(c["valor_liquido"] for c in pagos)
    return f"""📢 *Resumo automático*:

🔁 Pendentes: R$ {total_pendentes:.2f}
✅ Pagos: R$ {total_pagos:.2f}
📊 Total geral: R$ {total_pendentes + total_pagos:.2f}"""
