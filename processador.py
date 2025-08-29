import re
from datetime import datetime, timedelta
from pytz import timezone

comprovantes = []
pagamentos_parciais = []

taxas_cartao = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719,
    6: 0.0829, 7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088,
    11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
    16: 0.1519, 17: 0.1589, 18: 0.1684
}

def normalizar_valor(texto):
    texto = texto.lower().replace("r$", "").replace(" ", "").replace(".", "").replace(",", ".")
    match = re.search(r"\d+(\.\d{1,2})?", texto)
    if match:
        return float(match.group())
    return None

def obter_horario_brasilia():
    return datetime.now(timezone("America/Sao_Paulo")).strftime("%H:%M")

def registrar_comprovante(valor, tipo, parcelas=1):
    if tipo == "pix":
        taxa = 0.002
    else:
        taxa = taxas_cartao.get(parcelas, 0.04)

    liquido = round(valor * (1 - taxa), 2)
    comprovantes.append({
        "valor": valor,
        "tipo": tipo,
        "parcelas": parcelas,
        "taxa": taxa,
        "líquido": liquido,
        "horario": obter_horario_brasilia(),
        "pago": False
    })

def processar_mensagem(message):
    texto = message.text.lower()

    if "pix" in texto:
        valor = normalizar_valor(texto)
        if valor:
            registrar_comprovante(valor, tipo="pix")
            message.reply_text(
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💰 Tipo: PIX\n"
                f"⏰ Horário: {obter_horario_brasilia()}\n"
                f"📉 Taxa aplicada: 0.2%\n"
                f"✅ Valor líquido a pagar: R$ {valor * (1 - 0.002):,.2f}"
            )
        return
        def total_pendente_liquido():
            return sum(c["líquido"] for c in comprovantes if not c["pago"])


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

    for c in comprovantes:
        if not c["pago"]:
            if restante >= c["líquido"]:
                restante -= c["líquido"]
                c["pago"] = True
            else:
                c["líquido"] -= restante
                restante = 0
                break

    pagamentos_parciais[-1]["pago"] = True
    message.reply_text(f"✅ Pagamento de R$ {valor_pago:.2f} registrado com sucesso.")


def listar_pendentes(message):
    texto = "📋 *Comprovantes pendentes:*\n"
    total = 0
    for i, c in enumerate(comprovantes):
        if not c["pago"]:
            tipo = "PIX" if c["tipo"] == "pix" else f"Cartão ({c.get('parcelas', 1)}x)"
            texto += (
                f"#{i+1} | 💰 R$ {c['valor']:.2f} | {tipo} | ⏰ {c['horario']} | 📉 Líquido: R$ {c['líquido']:.2f}\n"
            )
            total += c["líquido"]
    texto += f"\n💰 Total a pagar: R$ {total:.2f}"
    message.reply_text(texto)
    def listar_pagamentos(message):
        texto = "📄 *Pagamentos já realizados:*\n"
    total = 0
    for i, c in enumerate(comprovantes):
        if c["pago"]:
            tipo = "PIX" if c["tipo"] == "pix" else f"Cartão ({c.get('parcelas', 1)}x)"
            texto += (
                f"#{i+1} | 💰 R$ {c['valor']:.2f} | {tipo} | ⏰ {c['horario']} | ✅ Líquido: R$ {c['líquido']:.2f}\n"
            )
            total += c["líquido"]
    texto += f"\n💰 Total pago ao lojista: R$ {total:.2f}"
    message.reply_text(texto)


def solicitar_pagamento(message):
    if total_pendente_liquido() <= 0:
        message.reply_text("✅ Nenhum valor pendente. Todos os pagamentos já foram realizados.")
        return

    message.reply_text("Digite o valor que deseja solicitar (ex: 300,00):")
    pagamentos_parciais.append({"etapa": "valor"})


def processar_resposta_pagamento(texto, message):
    if not pagamentos_parciais:
        return

    etapa_atual = pagamentos_parciais[-1].get("etapa")

    if etapa_atual == "valor":
        try:
            valor = float(texto.replace("R$", "").replace(",", "."))
            saldo = total_pendente_liquido()
            if valor > saldo:
                message.reply_text(f"❌ Valor solicitado é maior que o saldo disponível (R$ {saldo:.2f}).")
                pagamentos_parciais.pop()
                return
            pagamentos_parciais[-1]["valor"] = valor
            pagamentos_parciais[-1]["etapa"] = "chave"
            message.reply_text("Agora digite a *chave Pix* para pagamento:")
        except ValueError:
            message.reply_text("❌ Valor inválido. Tente novamente.")
    elif etapa_atual == "chave":
        pagamentos_parciais[-1]["chave"] = texto
        pagamentos_parciais[-1]["etapa"] = "finalizado"
        valor = pagamentos_parciais[-1]["valor"]
        chave = pagamentos_parciais[-1]["chave"]
        message.reply_text(f"💸 *Solicitação registrada com sucesso!*\nValor: R$ {valor:.2f}\n🔑 Chave Pix: `{chave}`")


def exibir_status(message):
    total_liquido = total_pendente_liquido()
    total_pago = sum(c["líquido"] for c in comprovantes if c["pago"])
    total_pix = sum(c["líquido"] for c in comprovantes if c["tipo"] == "pix")
    total_cartao = sum(c["líquido"] for c in comprovantes if c["tipo"] == "cartao")

    texto = (
        f"📊 *Status Atual:*\n"
        f"✅ Total pago: R$ {total_pago:.2f}\n"
        f"💰 Total pendente: R$ {total_liquido:.2f}\n"
        f"💸 Via Pix: R$ {total_pix:.2f}\n"
        f"💳 Via Cartão: R$ {total_cartao:.2f}"
    )
    message.reply_text(texto)


def ajuda(message):
    comandos = [
        "💬 *Comandos disponíveis:*",
        "💰 Enviar comprovante: `1000 pix` ou `1200 6x`",
        "📌 `quanto devo` - mostra valor líquido a pagar",
        "📌 `total a pagar` - mostra valor bruto pendente",
        "📌 `listar pendentes` - lista comprovantes não pagos",
        "📌 `listar pagos` - lista os já pagos",
        "📌 `pagamento feito` - confirma pagamento",
        "📌 `solicitar pagamento` - inicia processo de pagamento parcial",
        "📌 `/status` - mostra resumo do dia",
        "📌 `/limpar tudo` - (admin) limpa todos os comprovantes",
        "📌 `/corrigir valor` - (admin) corrige valor manualmente",
    ]
    message.reply_text("\n".join(comandos))
