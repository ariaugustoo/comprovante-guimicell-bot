import re
from datetime import datetime

comprovantes = []
pagamentos_parciais = []

TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}
TAXA_PIX = 0.2

def normalizar_valor(valor_str):
    valor_str = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(valor_str)
    except:
        return None

def calcular_liquido(valor, tipo_pagamento, parcelas=1):
    if tipo_pagamento == "pix":
        taxa = TAXA_PIX
    elif tipo_pagamento == "cartao":
        taxa = TAXAS_CARTAO.get(parcelas, 0)
    else:
        taxa = 0
    liquido = valor * (1 - taxa / 100)
    return round(liquido, 2), taxa

def processar_mensagem(update):
    message = update.message
    texto = message.text.lower().strip()
    chat_id = message.chat_id
    nome = message.from_user.first_name

    if "pix" in texto:
        valor = normalizar_valor(texto)
        if valor:
            liquido, taxa = calcular_liquido(valor, "pix")
            horario = datetime.now().strftime("%H:%M")
            comprovantes.append({
                "valor": valor,
                "tipo": "pix",
                "liquido": liquido,
                "horario": horario,
                "pago": False
            })
            message.reply_text(
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:.2f}\n"
                f"💰 Tipo: PIX\n"
                f"⏰ Horário: {horario}\n"
                f"📉 Taxa aplicada: {taxa}%\n"
                f"✅ Valor líquido a pagar: R$ {liquido:.2f}"
            )
        else:
            message.reply_text("❌ Valor inválido no comprovante.")

    elif "x" in texto:
        partes = texto.split("x")
        valor = normalizar_valor(partes[0])
        try:
            parcelas = int(partes[1].strip())
        except:
            parcelas = 1
        if valor and parcelas in TAXAS_CARTAO:
            liquido, taxa = calcular_liquido(valor, "cartao", parcelas)
            horario = datetime.now().strftime("%H:%M")
            comprovantes.append({
                "valor": valor,
                "tipo": "cartao",
                "parcelas": parcelas,
                "liquido": liquido,
                "horario": horario,
                "pago": False
            })
            message.reply_text(
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:.2f}\n"
                f"💰 Tipo: Cartão ({parcelas}x)\n"
                f"⏰ Horário: {horario}\n"
                f"📉 Taxa aplicada: {taxa}%\n"
                f"✅ Valor líquido a pagar: R$ {liquido:.2f}"
            )
        else:
            message.reply_text("❌ Erro ao processar o comprovante de cartão.")
            if texto == "listar pendentes":
                listar_pendentes(message)
    elif texto == "listar pagos":
        listar_pagamentos(message)
    elif texto == "quanto devo":
        total = total_pendente_liquido()
        message.reply_text(f"💰 Devo ao lojista: R$ {total:.2f}")
    elif texto == "total a pagar":
        total = total_bruto_pendente()
        message.reply_text(f"💰 Total bruto dos pendentes: R$ {total:.2f}")
    elif texto == "ajuda":
        message.reply_text(
            "📋 Comandos disponíveis:\n"
            "• Enviar: `1000 pix` ou `1000 10x`\n"
            "• quanto devo\n"
            "• total a pagar\n"
            "• listar pendentes\n"
            "• listar pagos\n"
            "• solicitar pagamento\n"
            "• pagamento feito\n"
            "• /status"
        )
    elif texto == "solicitar pagamento":
        message.reply_text("Digite o valor que deseja solicitar:")
    elif re.match(r"^\d+([.,]?\d{0,2})?$", texto) and message.reply_to_message:
        valor_solicitado = normalizar_valor(texto)
        if valor_solicitado and total_pendente_liquido() >= valor_solicitado:
            pagamentos_parciais.append({
                "valor": valor_solicitado,
                "pago": False,
                "pix": None
            })
            message.reply_text("Agora envie sua chave PIX:")
        else:
            message.reply_text("❌ Valor solicitado maior que o disponível.")
    elif "@" in texto and pagamentos_parciais and not pagamentos_parciais[-1]["pix"]:
        pagamentos_parciais[-1]["pix"] = texto
        valor = pagamentos_parciais[-1]["valor"]
        pix = pagamentos_parciais[-1]["pix"]
        message.reply_text(
            f"📢 Solicitação de pagamento recebida:\n"
            f"💰 Valor solicitado: R$ {valor:.2f}\n"
            f"🔑 Chave Pix: {pix}\n"
            f"Aguardando confirmação com 'pagamento feito'"
        )
    elif texto == "pagamento feito":
        registrar_pagamento_parcial(message)
    elif texto == "/status" or texto == "fechamento do dia":
        gerar_status(message)

def listar_pendentes(message):
    if not comprovantes:
        message.reply_text("Não há comprovantes pendentes.")
        return

    texto = "📌 Comprovantes pendentes:\n"
    total = 0
    for i, c in enumerate(comprovantes):
        if not c["pago"]:
            tipo = "PIX" if c["tipo"] == "pix" else f"Cartão ({c.get('parcelas', 1)}x)"
            texto += (
                f"#{i+1} | 💰 R$ {c['valor']:.2f} | 🧾 {tipo} | "
                f"⏰ {c['horario']} | 🔻 Líquido: R$ {c['liquido']:.2f}\n"
            )
            total += c["liquido"]
    texto += f"\n💰 Total líquido pendente: R$ {total:.2f}"
    message.reply_text(texto)

def listar_pagamentos(message):
    if not comprovantes:
        message.reply_text("Ainda não há pagamentos registrados.")
        return

    texto = "✅ Pagamentos realizados:\n"
    total = 0
    for i, c in enumerate(comprovantes):
        if c["pago"]:
            tipo = "PIX" if c["tipo"] == "pix" else f"Cartão ({c.get('parcelas', 1)}x)"
            texto += (
                f"#{i+1} | 💰 R$ {c['valor']:.2f} | 🧾 {tipo} | "
                f"⏰ {c['horario']} | 🔺 Líquido: R$ {c['liquido']:.2f}\n"
            )
            total += c["liquido"]
    texto += f"\n💰 Total pago ao lojista: R$ {total:.2f}"
    message.reply_text(texto)

def total_pendente_liquido():
    return sum(c["liquido"] for c in comprovantes if not c["pago"])

def total_bruto_pendente():
    return sum(c["valor"] for c in comprovantes if not c["pago"])
def marcar_como_pago(message):
    for c in comprovantes:
        if not c["pago"]:
            c["pago"] = True
    message.reply_text("✅ Todos os comprovantes foram marcados como pagos.")

def registrar_pagamento_parcial(message):
    if not pagamentos_parciais:
        message.reply_text("❌ Nenhuma solicitação de pagamento ativa.")
        return

    valor_pago = pagamentos_parciais[-1]["valor"]
    restante = valor_pago
    total_pendente = total_pendente_liquido()

    if valor_pago > total_pendente:
        message.reply_text("❌ Valor pago excede o total pendente.")
        return

    for c in comprovantes:
        if not c["pago"]:
            if c["liquido"] <= restante:
                restante -= c["liquido"]
                c["pago"] = True
            else:
                c["liquido"] -= restante
                if c["tipo"] == "pix":
                    c["valor"] = c["liquido"] / (1 - 0.002)
                else:
                    taxa = TAXAS_CARTAO.get(c.get("parcelas", 1), 0)
                    c["valor"] = c["liquido"] / (1 - taxa / 100)
                restante = 0
                break

    pagamentos_parciais[-1]["pago"] = True
    message.reply_text("✅ Pagamento parcial registrado com sucesso.")

def gerar_status(message):
    total_liquido = sum(c["liquido"] for c in comprovantes)
    total_pago = sum(c["liquido"] for c in comprovantes if c["pago"])
    total_pendente = sum(c["liquido"] for c in comprovantes if not c["pago"])
    total_pix = sum(c["liquido"] for c in comprovantes if c["tipo"] == "pix")
    total_cartao = sum(c["liquido"] for c in comprovantes if c["tipo"] == "cartao")

    texto = (
        f"📊 Status geral:\n"
        f"💳 Total Cartão: R$ {total_cartao:.2f}\n"
        f"💸 Total PIX: R$ {total_pix:.2f}\n"
        f"✅ Total Pago: R$ {total_pago:.2f}\n"
        f"📍 Total Pendente: R$ {total_pendente:.2f}\n"
        f"🧾 Total Geral: R$ {total_liquido:.2f}"
    )
    message.reply_text(texto)
