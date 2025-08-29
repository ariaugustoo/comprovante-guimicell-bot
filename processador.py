from datetime import datetime
import pytz

comprovantes = []
pagamentos = []
solicitacoes = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def formatar_mensagem_comprovante(valor, tipo, horario, taxa, liquido):
    return f"""📄 *Comprovante analisado:*
💰 Valor bruto: R$ {valor:,.2f}
💳 Tipo: {tipo}
⏰ Horário: {horario}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: R$ {liquido:,.2f}""".replace(",", "X").replace(".", ",").replace("X", ".")

def registrar_comprovante(valor, tipo):
    timezone = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(timezone).strftime('%H:%M')
    taxa = 0.2 if tipo == "PIX" else taxas_cartao.get(tipo, 0)
    liquido = round(valor * (1 - taxa / 100), 2)
    comprovantes.append({"valor": valor, "tipo": tipo, "horario": agora, "liquido": liquido, "pago": False})
    return formatar_mensagem_comprovante(valor, "PIX" if tipo == "PIX" else f"{tipo}x", agora, taxa, liquido)

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "📭 Nenhum comprovante pendente no momento."
    linhas = ["📋 *Comprovantes Pendentes:*"]
    for i, c in enumerate(pendentes, 1):
        linhas.append(f"{i}. 💰 R$ {c['liquido']:,.2f} | ⏰ {c['horario']} | 💳 {c['tipo']}".replace(",", "X").replace(".", ",").replace("X", "."))
    total = sum(c["liquido"] for c in pendentes)
    linhas.append(f"\n💰 Total pendente: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    return "\n".join(linhas)

def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "❌ Nenhum comprovante foi marcado como pago ainda."
    linhas = ["📄 *Comprovantes Pagos:*"]
    for i, c in enumerate(pagos, 1):
        linhas.append(f"{i}. 💰 R$ {c['liquido']:,.2f} | ⏰ {c['horario']} | 💳 {c['tipo']}".replace(",", "X").replace(".", ",").replace("X", "."))
    total = sum(c["liquido"] for c in pagos)
    linhas.append(f"\n✅ Total pago: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    return "\n".join(linhas)

def marcar_como_pago(valor):
    pendentes = [c for c in comprovantes if not c["pago"]]
    restante = valor
    for c in pendentes:
        if restante <= 0:
            break
        if c["liquido"] <= restante:
            restante -= c["liquido"]
            c["pago"] = True
        else:
            c["liquido"] -= restante
            restante = 0
    pagamentos.append(valor)
    return f"✅ Recebido! Estamos quase quitando tudo 😉"

def total_pendentes():
    return round(sum(c["liquido"] for c in comprovantes if not c["pago"]), 2)

def total_bruto_pendentes():
    return round(sum(c["valor"] for c in comprovantes if not c["pago"]), 2)

def solicitar_pagamento(valor, chave):
    credito_disponivel = total_pendentes()
    if valor > credito_disponivel:
        return f"🚫 Você só pode solicitar até R$ {credito_disponivel:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    solicitacoes.append({"valor": valor, "chave": chave})
    return f"📬 Solicitação de pagamento registrada!\n💰 Valor: R$ {valor:,.2f}\n🔑 Chave Pix: {chave}".replace(",", "X").replace(".", ",").replace("X", ".")

def status():
    total_pix = sum(c["liquido"] for c in comprovantes if c["tipo"] == "PIX")
    total_cartao = sum(c["liquido"] for c in comprovantes if c["tipo"] != "PIX")
    total_pago = sum(c["liquido"] for c in comprovantes if c["pago"])
    total_pendente = sum(c["liquido"] for c in comprovantes if not c["pago"])
    return f"""📊 *Status Geral:*
💳 Cartão (líquido): R$ {total_cartao:,.2f}
💸 PIX (líquido): R$ {total_pix:,.2f}
✅ Total pago: R$ {total_pago:,.2f}
⏳ Total pendente: R$ {total_pendente:,.2f}""".replace(",", "X").replace(".", ",").replace("X", ".")
