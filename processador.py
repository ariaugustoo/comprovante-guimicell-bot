import re
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CallbackContext

# Banco de dados temporário em memória
comprovantes = []
solicitacoes_pagamento = []

# Tabela de taxas de cartão
taxas_cartao = {
    i: taxa for i, taxa in zip(range(1, 19), [
        4.39, 5.19, 6.19, 6.59, 7.19, 8.29, 9.19, 9.99, 10.29,
        10.88, 11.99, 12.52, 13.69, 14.19, 14.69, 15.19, 15.89, 16.84
    ])
}

def normalizar_valor(valor_str):
    return float(valor_str.replace('.', '').replace(',', '.'))

def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def obter_horario_brasilia():
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%H:%M')

def calcular_taxa(valor, tipo, parcelas=None):
    if tipo == "pix":
        taxa = 0.2
    else:
        taxa = taxas_cartao.get(parcelas, 0)
    valor_liquido = valor * (1 - taxa / 100)
    return round(taxa, 2), round(valor_liquido, 2)

def processar_mensagem(update: Update, context: CallbackContext):
    texto = update.message.text.lower()
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    if "pagamento feito" in texto:
        if solicitacoes_pagamento:
            valor_pago = solicitacoes_pagamento.pop(0)["valor"]
        else:
            match = re.search(r"([\d.,]+)", texto)
            if match:
                valor_pago = normalizar_valor(match.group(1))
            else:
                update.message.reply_text("Valor inválido.")
                return

        total_pendente = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        if valor_pago > total_pendente:
            update.message.reply_text("❌ Valor excede o total devido.")
            return

        restante = valor_pago
        for c in comprovantes:
            if not c["pago"]:
                if restante >= c["valor_liquido"]:
                    restante -= c["valor_liquido"]
                    c["pago"] = True
                else:
                    c["valor_liquido"] -= restante
                    restante = 0
                if restante == 0:
                    break

        update.message.reply_text(f"✅ Pagamento de {formatar_reais(valor_pago)} registrado com sucesso.")
        return

    if "quanto devo" in texto:
        total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        update.message.reply_text(f"💰 Devo ao lojista: {formatar_reais(total)}")
        return

    if "total a pagar" in texto:
        total = sum(c["valor"] for c in comprovantes if not c["pago"])
        update.message.reply_text(f"💰 Total a pagar (sem desconto): {formatar_reais(total)}")
        return

    if texto == "solicitar pagamento":
        context.user_data["esperando_valor"] = True
        update.message.reply_text("Digite o valor que deseja solicitar:")
        return

    if context.user_data.get("esperando_valor"):
        try:
            valor = normalizar_valor(texto)
            context.user_data["valor_solicitado"] = valor
            context.user_data["esperando_valor"] = False
            context.user_data["esperando_chave"] = True
            update.message.reply_text("Agora envie a chave Pix:")
        except:
            update.message.reply_text("Valor inválido.")
        return

    if context.user_data.get("esperando_chave"):
        chave = texto.strip()
        valor = context.user_data.get("valor_solicitado")
        solicitacoes_pagamento.append({"valor": valor, "chave": chave})
        context.user_data.clear()
        update.message.reply_text(f"🔔 Solicitação registrada: {formatar_reais(valor)}\n🔑 Chave Pix: {chave}")
        return

    if user_id == int(os.getenv("ADMIN_ID")) and texto.startswith("corrigir valor"):
        match = re.search(r"([\d.,]+)", texto)
        if match and comprovantes:
            novo_valor = normalizar_valor(match.group(1))
            ultimo = comprovantes[-1]
            taxa, liquido = calcular_taxa(novo_valor, ultimo["tipo"], ultimo.get("parcelas"))
            ultimo.update({"valor": novo_valor, "valor_liquido": liquido})
            update.message.reply_text("✅ Valor corrigido.")
        else:
            update.message.reply_text("❌ Nenhum comprovante para corrigir.")
        return

    if user_id == int(os.getenv("ADMIN_ID")) and texto == "limpar tudo":
        comprovantes.clear()
        update.message.reply_text("🧹 Todos os dados foram limpos.")
        return

    if re.match(r"^[\d.,]+\s*(pix|[1-9]|1[0-8]x)$", texto):
        match = re.match(r"([\d.,]+)\s*(pix|[1-9]|1[0-8])x?", texto)
        valor = normalizar_valor(match.group(1))
        tipo = "pix" if "pix" in texto else "cartao"
        parcelas = None if tipo == "pix" else int(match.group(2))
        taxa, liquido = calcular_taxa(valor, tipo, parcelas)
        comprovantes.append({
            "valor": valor,
            "tipo": tipo,
            "parcelas": parcelas,
            "valor_liquido": liquido,
            "hora": obter_horario_brasilia(),
            "pago": False
        })
        resposta = (
            "📄 Comprovante analisado:\n"
            f"💰 Valor bruto: {formatar_reais(valor)}\n"
            f"💳 Tipo: {'PIX' if tipo == 'pix' else f'{parcelas}x'}\n"
            f"⏰ Horário: {obter_horario_brasilia()}\n"
            f"📉 Taxa aplicada: {taxa:.2f}%\n"
            f"✅ Valor líquido a pagar: {formatar_reais(liquido)}"
        )
        update.message.reply_text(resposta)
        return

    update.message.reply_text("❌ Comando não reconhecido. Digite 'ajuda' para ver as opções.")

def listar_pendentes(update: Update, context: CallbackContext):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        update.message.reply_text("✅ Não há pendentes.")
        return
    msg = "📋 *Pendentes:*\n\n"
    for c in pendentes:
        msg += (
            f"• {formatar_reais(c['valor'])} ({'PIX' if c['tipo']=='pix' else f'{c['parcelas']}x'}) "
            f"- Líquido: {formatar_reais(c['valor_liquido'])} às {c['hora']}\n"
        )
    total = sum(c["valor_liquido"] for c in pendentes)
    msg += f"\n💰 Total líquido: {formatar_reais(total)}"
    update.message.reply_text(msg, parse_mode="Markdown")

def listar_pagamentos_feitos(update: Update, context: CallbackContext):
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        update.message.reply_text("Ainda não há comprovantes pagos.")
        return
    msg = "📗 *Pagos:*\n\n"
    for c in pagos:
        msg += f"• {formatar_reais(c['valor'])} ({'PIX' if c['tipo']=='pix' else f'{c['parcelas']}x'}) às {c['hora']}\n"
    total = sum(c["valor_liquido"] for c in pagos)
    msg += f"\n✅ Total pago: {formatar_reais(total)}"
    update.message.reply_text(msg, parse_mode="Markdown")

def solicitar_pagamento(update: Update, context: CallbackContext):
    context.user_data["esperando_valor"] = True
    update.message.reply_text("Digite o valor que deseja solicitar:")

def limpar_tudo(update: Update, context: CallbackContext):
    if update.message.from_user.id != int(os.getenv("ADMIN_ID")):
        update.message.reply_text("❌ Acesso negado.")
        return
    comprovantes.clear()
    update.message.reply_text("🧹 Todos os dados foram apagados.")

def corrigir_valor(update: Update, context: CallbackContext):
    update.message.reply_text("Digite o novo valor para o último comprovante:")
