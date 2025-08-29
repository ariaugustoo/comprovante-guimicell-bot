from datetime import datetime, timedelta
import pytz

# Banco de dados em memória
comprovantes = []
solicitacoes_pagamento = []

# Fuso horário
fuso_brasilia = pytz.timezone("America/Sao_Paulo")

# Tabela de taxas por número de parcelas
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

# Funções auxiliares
def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_taxa(valor, parcelas):
    if parcelas == 0:
        taxa = 0.2
    else:
        taxa = taxas_cartao.get(parcelas, 0)
    valor_liquido = valor * (1 - taxa / 100)
    return taxa, round(valor_liquido, 2)

# Comando: enviar comprovante (ex: 1200 pix ou 2300 6x)
def processar_mensagem(update, context):
    mensagem = update.message.text.lower().replace(",", ".").replace("x", "x")
    chat_id = update.effective_chat.id

    try:
        if "pix" in mensagem:
            valor = float(mensagem.split("pix")[0].strip())
            parcelas = 0
            tipo = "PIX"
        elif "x" in mensagem:
            partes = mensagem.split("x")
            valor = float(partes[0].strip())
            parcelas = int(partes[1].strip())
            tipo = f"Cartão {parcelas}x"
        else:
            context.bot.send_message(chat_id=chat_id, text="❌ Formato inválido. Use algo como:\n👉 `1200 pix` ou `2500 6x`")
            return

        taxa, valor_liquido = calcular_taxa(valor, parcelas)
        horario = datetime.now(fuso_brasilia).strftime("%H:%M")

        comprovantes.append({
            "valor_bruto": valor,
            "tipo": tipo,
            "parcelas": parcelas,
            "taxa": taxa,
            "valor_liquido": valor_liquido,
            "horario": horario,
            "pago": False
        })

        resposta = (
            "📄 Comprovante analisado:\n"
            f"💰 Valor bruto: {formatar_reais(valor)}\n"
            f"💳 Tipo: {tipo}\n"
            f"⏰ Horário: {horario}\n"
            f"📉 Taxa aplicada: {taxa:.2f}%\n"
            f"✅ Valor líquido a pagar: {formatar_reais(valor_liquido)}\n"
            "📍Estamos quase quitando tudo! 😉"
        )

        context.bot.send_message(chat_id=chat_id, text=resposta)

    except Exception as e:
        context.bot.send_message(chat_id=chat_id, text="⚠️ Erro ao processar o comprovante. Verifique o formato e tente novamente.")

# Comando: listar pendentes
def listar_pendentes(update, context):
    chat_id = update.effective_chat.id
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        context.bot.send_message(chat_id=chat_id, text="✅ Nenhum pagamento pendente no momento.")
        return
    resposta = "📋 Comprovantes pendentes:\n\n"
    total = 0
    for i, c in enumerate(pendentes, 1):
        resposta += (
            f"{i}. 💰 {formatar_reais(c['valor_liquido'])} | {c['tipo']} | ⏰ {c['horario']}\n"
        )
        total += c["valor_liquido"]
    resposta += f"\n📍 Total pendente: {formatar_reais(total)}"
    context.bot.send_message(chat_id=chat_id, text=resposta)

# Comando: listar pagos
def listar_pagamentos(update, context):
    chat_id = update.effective_chat.id
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        context.bot.send_message(chat_id=chat_id, text="📭 Nenhum comprovante foi marcado como pago ainda.")
        return
    resposta = "📬 Comprovantes pagos:\n\n"
    total = 0
    for i, c in enumerate(pagos, 1):
        resposta += (
            f"{i}. 💰 {formatar_reais(c['valor_liquido'])} | {c['tipo']} | ⏰ {c['horario']}\n"
        )
        total += c["valor_liquido"]
    resposta += f"\n✅ Total pago: {formatar_reais(total)}"
    context.bot.send_message(chat_id=chat_id, text=resposta)

# Comando: solicitar pagamento
def solicitar_pagamento(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text="💬 Digite o valor que deseja solicitar (ex: 300,00):")
    return

# Comando: registrar pagamento
def registrar_pagamento(update, context):
    chat_id = update.effective_chat.id
    total_devido = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])

    if not solicitacoes_pagamento:
        context.bot.send_message(chat_id=chat_id, text="⚠️ Nenhuma solicitação ativa. Use 'solicitar pagamento' antes.")
        return

    valor_pago = solicitacoes_pagamento.pop(0)
    valor_pago = float(valor_pago)

    if valor_pago > total_devido:
        context.bot.send_message(chat_id=chat_id, text="❌ O valor pago excede o total pendente.")
        return

    for c in comprovantes:
        if not c["pago"]:
            if valor_pago >= c["valor_liquido"]:
                valor_pago -= c["valor_liquido"]
                c["pago"] = True
            else:
                c["valor_liquido"] -= valor_pago
                valor_pago = 0
            if valor_pago <= 0:
                break

    context.bot.send_message(chat_id=chat_id, text="✅ Pagamento registrado com sucesso! Obrigado 🙏")

# Comando: quanto devo
def mostrar_total_devido(update, context):
    chat_id = update.effective_chat.id
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    context.bot.send_message(chat_id=chat_id, text=f"💰 Devo ao lojista: {formatar_reais(total)}")

# Comando: total a pagar bruto
def mostrar_total_bruto(update, context):
    chat_id = update.effective_chat.id
    total = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
    context.bot.send_message(chat_id=chat_id, text=f"💰 Total bruto pendente: {formatar_reais(total)}")

# Comando: status ou fechamento do dia
def mostrar_status(update, context):
    chat_id = update.effective_chat.id
    total_pago = sum(c["valor_liquido"] for c in comprovantes if c["pago"])
    total_pendente = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "PIX")
    total_cartao = sum(c["valor_liquido"] for c in comprovantes if "Cartão" in c["tipo"])

    resposta = (
        "📅 Fechamento do Dia:\n"
        f"💳 Total Cartão: {formatar_reais(total_cartao)}\n"
        f"💸 Total Pix: {formatar_reais(total_pix)}\n"
        f"✅ Total Pago: {formatar_reais(total_pago)}\n"
        f"📍 Total Pendente: {formatar_reais(total_pendente)}"
    )
    context.bot.send_message(chat_id=chat_id, text=resposta)

# Comando: ajuda
def mostrar_ajuda(update, context):
    chat_id = update.effective_chat.id
    resposta = (
        "🤖 Comandos disponíveis:\n\n"
        "💳 Enviar valor cartão: `2500 10x`\n"
        "💸 Enviar valor Pix: `1200 pix`\n"
        "🧾 listar pendentes\n"
        "📬 listar pagos\n"
        "💰 quanto devo\n"
        "💵 total a pagar\n"
        "📊 /status ou fechamento do dia\n"
        "📤 solicitar pagamento\n"
        "✅ pagamento feito\n"
        "🆘 ajuda"
    )
    context.bot.send_message(chat_id=chat_id, text=resposta)

# Admin: limpar tudo
def limpar_dados(update, context):
    comprovantes.clear()
    solicitacoes_pagamento.clear()
    context.bot.send_message(chat_id=update.effective_chat.id, text="🗑️ Todos os dados foram apagados.")

# Admin: corrigir valor (placeholder)
def corrigir_valor(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Função 'corrigir valor' ainda será implementada.")
