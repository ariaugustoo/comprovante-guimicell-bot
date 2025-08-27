import re
from datetime import datetime

comprovantes = []
ID_ADMIN = 5857469519  # Substitua pelo seu ID real se necessário

# Tabela de taxas de cartao
taxas_cartao = {
    1: 0.0439,
    2: 0.0519,
    3: 0.0619,
    4: 0.0659,
    5: 0.0719,
    6: 0.0829,
    7: 0.0919,
    8: 0.0999,
    9: 0.1029,
    10: 0.1088,
    11: 0.1199,
    12: 0.1252,
    13: 0.1369,
    14: 0.1419,
    15: 0.1469,
    16: 0.1519,
    17: 0.1589,
    18: 0.1684
}

# Normaliza valor: aceita ponto ou virgula
def normalizar_valor(valor_str):
    valor_str = valor_str.replace("R$", "").replace(" ", "").replace(",", ".")
    return float(re.sub(r"[^\d.]", "", valor_str))

# Processa mensagens comuns
def processar_mensagem(mensagem, user_id):
    mensagem = mensagem.lower()

    if "pix" in mensagem:
        valor = normalizar_valor(mensagem)
        taxa = 0.002
        valor_liquido = round(valor * (1 - taxa), 2)
        comprovantes.append({
            "tipo": "pix",
            "valor": valor,
            "parcelas": 1,
            "taxa": taxa,
            "valor_liquido": valor_liquido,
            "hora": datetime.now().strftime("%H:%M"),
            "pago": False
        })
        return (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {valor:.2f}\n"
            f"💳 Pagamento: PIX\n"
            f"📉 Taxa aplicada: {taxa * 100:.2f}%\n"
            f"✅ Valor liquido a pagar: R$ {valor_liquido:.2f}"
        )

    elif "x" in mensagem:
        match = re.search(r"([\d.,]+)\s*(\d{1,2})x", mensagem)
        if match:
            valor = normalizar_valor(match.group(1))
            parcelas = int(match.group(2))
            taxa = taxas_cartao.get(parcelas, 0)
            valor_liquido = round(valor * (1 - taxa), 2)
            comprovantes.append({
                "tipo": "cartao",
                "valor": valor,
                "parcelas": parcelas,
                "taxa": taxa,
                "valor_liquido": valor_liquido,
                "hora": datetime.now().strftime("%H:%M"),
                "pago": False
            })
            return (
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:.2f}\n"
                f"💳 Parcelas: {parcelas}x\n"
                f"📉 Taxa aplicada: {taxa * 100:.2f}%\n"
                f"✅ Valor liquido a pagar: R$ {valor_liquido:.2f}"
            )

    return "❌ Formato invalido. Envie algo como '6438,90 pix' ou '7899,99 10x'."

# Comando: /listar_pendentes
def listar_pendentes(update, context):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Nenhum comprovante pendente.")
        return
    resposta = "📋 Comprovantes pendentes:\n"
    for i, c in enumerate(pendentes, 1):
        resposta += (
            f"{i}. R$ {c['valor']:.2f} - {c['parcelas']}x - {c['hora']} - "
            f"💸 Liquido: R$ {c['valor_liquido']:.2f}\n"
        )
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

# Comando: /listar_pagos
def listar_pagos(update, context):
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Nenhum comprovante marcado como pago.")
        return
    resposta = "📗 Comprovantes pagos:\n"
    for i, c in enumerate(pagos, 1):
        resposta += (
            f"{i}. R$ {c['valor']:.2f} - {c['parcelas']}x - {c['hora']} - "
            f"💸 Liquido: R$ {c['valor_liquido']:.2f}\n"
        )
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

# Comando: /ultimo_comprovante
def ultimo_comprovante(update, context):
    if not comprovantes:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Nenhum comprovante enviado ainda.")
        return
    c = comprovantes[-1]
    status = "✅ Pago" if c["pago"] else "🕗 Pendente"
    resposta = (
        f"📄 Ultimo comprovante:\n"
        f"💰 Valor: R$ {c['valor']:.2f}\n"
        f"💳 Parcelas: {c['parcelas']}x\n"
        f"⏰ Hora: {c['hora']}\n"
        f"📉 Taxa: {c['taxa']*100:.2f}%\n"
        f"💸 Liquido: R$ {c['valor_liquido']:.2f}\n"
        f"{status}"
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

# Comando: /total_geral
def total_geral(update, context):
    total = sum(c["valor_liquido"] for c in comprovantes)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"💰 Total geral (todos): R$ {total:.2f}")

# Comando: /total_que_devo
def total_pendentes(update, context):
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"💸 Total pendente a pagar: R$ {total:.2f}")

# Comando: /ajuda
def comandos_suporte(update, context):
    comandos = (
        "📌 *Comandos disponiveis:*\n"
        "/ajuda – Exibe esta ajuda\n"
        "/listar_pendentes – Lista os comprovantes pendentes\n"
        "/listar_pagos – Lista os comprovantes pagos\n"
        "/ultimo_comprovante – Mostra o ultimo comprovante\n"
        "/total_geral – Soma de todos os comprovantes\n"
        "/total_que_devo – Total apenas dos pendentes\n"
        "✅ – Marcar comprovante como pago (digite no chat)\n\n"
        "📥 Para registrar um comprovante, envie:\n"
        "→ Ex: 7899,99 10x\n"
        "→ Ou: 6438,76 pix"
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=comandos, parse_mode="Markdown")
