from datetime import datetime, timedelta
import pytz

comprovantes = []
solicitacoes_pagamento = {}

taxas_cartao = {
    i: taxa for i, taxa in zip(
        range(1, 19),
        [4.39, 5.19, 6.19, 6.59, 7.19, 8.29, 9.19, 9.99, 10.29,
         10.88, 11.99, 12.52, 13.69, 14.19, 14.69, 15.19, 15.89, 16.84]
    )
}
TAXA_PIX = 0.2

def normalizar_valor(texto):
    try:
        return float(texto.replace("R$", "").replace(" ", "").replace(".", "").replace(",", "."))
    except:
        return None

def processar_mensagem(update):
    mensagem = update.message.text.lower()
    user_id = update.effective_user.id
    horario = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%H:%M")

    if "pix" in mensagem:
        bruto = normalizar_valor(mensagem)
        taxa = TAXA_PIX
        liquido = bruto * (1 - taxa / 100)
        comprovantes.append({"user_id": user_id, "bruto": bruto, "tipo": "PIX", "taxa": taxa, "liquido": liquido, "pago": False, "horario": horario})
        resposta = f"📄 Comprovante analisado:\n💰 Valor bruto: R$ {bruto:,.2f}\n💰 Tipo: PIX\n⏰ Horário: {horario}\n📉 Taxa aplicada: {taxa}%\n✅ Valor líquido a pagar: R$ {liquido:,.2f}"
        update.message.reply_text(resposta.replace(",", "X").replace(".", ",").replace("X", "."))
    elif "x" in mensagem:
        partes = mensagem.split("x")
        bruto = normalizar_valor(partes[0])
        parcelas = int(partes[1].strip())
        taxa = taxas_cartao.get(parcelas, 0)
        liquido = bruto * (1 - taxa / 100)
        comprovantes.append({"user_id": user_id, "bruto": bruto, "tipo": f"{parcelas}x", "taxa": taxa, "liquido": liquido, "pago": False, "horario": horario})
        resposta = f"📄 Comprovante analisado:\n💰 Valor bruto: R$ {bruto:,.2f}\n💰 Tipo: Cartão {parcelas}x\n⏰ Horário: {horario}\n📉 Taxa aplicada: {taxa}%\n✅ Valor líquido a pagar: R$ {liquido:,.2f}"
        update.message.reply_text(resposta.replace(",", "X").replace(".", ",").replace("X", "."))

def marcar_como_pago(usuario_id):
    if usuario_id in solicitacoes_pagamento:
        valor_pendente = solicitacoes_pagamento.pop(usuario_id)
        for c in comprovantes:
            if not c["pago"] and valor_pendente > 0:
                if c["liquido"] <= valor_pendente:
                    valor_pendente -= c["liquido"]
                    c["pago"] = True
                else:
                    c["liquido"] -= valor_pendente
                    c["bruto"] = c["liquido"] / (1 - c["taxa"] / 100)
                    valor_pendente = 0
        return "✅ Pagamento parcial registrado com sucesso."
    else:
        for c in comprovantes:
            if not c["pago"]:
                c["pago"] = True
        return "✅ Todos os comprovantes foram marcados como pagos."

def quanto_devo():
    return sum(c["liquido"] for c in comprovantes if not c["pago"])

def total_a_pagar():
    return sum(c["bruto"] for c in comprovantes if not c["pago"])

def iniciar_solicitacao_pagamento(user_id):
    solicitacoes_pagamento[user_id] = None

def registrar_pagamento_solicitado(user_id, valor_str):
    valor = normalizar_valor(valor_str)
    if valor is not None and user_id in solicitacoes_pagamento:
        solicitacoes_pagamento[user_id] = valor
        return f"📥 Solicitação registrada: pagamento de R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return None
