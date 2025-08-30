# processador.py
import re
from datetime import datetime, timedelta
from collections import defaultdict

comprovantes = []
pagamentos_realizados = []
solicitacoes_pagamento = []

# Tabela de taxas de cartão por número de parcelas
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29, 7: 9.19,
    8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}


def parse_valor(texto):
    match = re.search(r"(\d+[.,]?\d*)", texto)
    if match:
        valor_str = match.group(1).replace(".", "").replace(",", ".")
        try:
            return float(valor_str)
        except ValueError:
            return None
    return None


def identificar_tipo_pagamento(texto):
    if "pix" in texto.lower():
        return "PIX"
    match = re.search(r"(\d{1,2})x", texto.lower())
    if match:
        return f"{match.group(1)}x"
    return None


def calcular_taxa(tipo_pagamento):
    if tipo_pagamento == "PIX":
        return 0.2
    elif tipo_pagamento.endswith("x"):
        parcelas = int(tipo_pagamento.replace("x", ""))
        return TAXAS_CARTAO.get(parcelas, 0)
    return 0


def calcular_valor_liquido(valor, taxa):
    return round(valor * (1 - taxa / 100), 2)


def formatar_mensagem_comprovante(valor, tipo, taxa, valor_liquido):
    horario = datetime.now().strftime("%H:%M")
    return (
        "📄 Comprovante analisado:\n"
        f"💰 Valor bruto: R$ {valor:,.2f}".replace(".", ",") + "\n"
        f"💰 Tipo: {tipo}\n"
        f"⏰ Horário: {horario}\n"
        f"📉 Taxa aplicada: {taxa:.2f}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}".replace(".", ",")
    )


def processar_mensagem(texto):
    valor = parse_valor(texto)
    tipo = identificar_tipo_pagamento(texto)

    if valor is None or tipo is None:
        return "❌ Não consegui entender o valor ou o tipo de pagamento. Envie no formato: 1000,00 pix ou 1000,00 6x."

    taxa = calcular_taxa(tipo)
    valor_liquido = calcular_valor_liquido(valor, taxa)

    comprovante = {
        "valor": valor,
        "tipo": tipo,
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "horario": datetime.now(),
        "pago": False
    }
    comprovantes.append(comprovante)

    return formatar_mensagem_comprovante(valor, tipo, taxa, valor_liquido)


def listar_pendentes():
    resposta = "📌 *Comprovantes Pendentes:*\n"
    total = 0
    for c in comprovantes:
        if not c["pago"]:
            resposta += f"• 💰 R$ {c['valor']:,.2f}".replace(".", ",")
            resposta += f" | {c['tipo']} | ⏰ {c['horario'].strftime('%H:%M')}\n"
            total += c["valor_liquido"]
    resposta += f"\n💰 Total líquido pendente: R$ {total:,.2f}".replace(".", ",")
    return resposta


def listar_pagamentos():
    resposta = "✅ *Comprovantes Pagos:*\n"
    total = 0
    for c in comprovantes:
        if c["pago"]:
            resposta += f"• R$ {c['valor']:,.2f}".replace(".", ",")
            resposta += f" | {c['tipo']} | ⏰ {c['horario'].strftime('%H:%M')}\n"
            total += c["valor_liquido"]
    resposta += f"\n💰 Total pago: R$ {total:,.2f}".replace(".", ",")
    return resposta


def calcular_total_pendente():
    return sum(c["valor_liquido"] for c in comprovantes if not c["pago"])


def calcular_total_pago():
    return sum(c["valor_liquido"] for c in comprovantes if c["pago"])


def marcar_pagamento(valor_pago):
    saldo = calcular_total_pendente()
    if valor_pago > saldo:
        return f"❌ Você está solicitando mais do que o valor disponível. Total disponível: R$ {saldo:,.2f}".replace(".", ",")

    valor_restante = valor_pago
    for c in comprovantes:
        if not c["pago"]:
            if c["valor_liquido"] <= valor_restante:
                valor_restante -= c["valor_liquido"]
                c["pago"] = True
            else:
                c["valor_liquido"] -= valor_restante
                c["valor"] = c["valor_liquido"] / (1 - c["taxa"] / 100)
                valor_restante = 0
                break
        if valor_restante <= 0:
            break
    return f"✅ Pagamento de R$ {valor_pago:,.2f} registrado com sucesso.".replace(".", ",")


def solicitar_pagamento(valor, chave_pix):
    total = calcular_total_pendente()
    if valor > total:
        return f"❌ Você está solicitando mais do que o valor disponível. Total disponível: R$ {total:,.2f}".replace(".", ",")

    solicitacoes_pagamento.append({
        "valor": valor,
        "chave_pix": chave_pix,
        "horario": datetime.now()
    })
    return (
        "📢 *Solicitação de Pagamento:*\n"
        f"💸 Valor: R$ {valor:,.2f}".replace(".", ",") + "\n"
        f"🔑 Chave PIX: {chave_pix}\n"
        "✅ Aguarde confirmação com 'pagamento feito'."
    )


def limpar_dados():
    comprovantes.clear()
    pagamentos_realizados.clear()
    solicitacoes_pagamento.clear()
    return "🧹 Todos os dados foram limpos com sucesso."


def status_resumo():
    total_pago = calcular_total_pago()
    total_pendente = calcular_total_pendente()
    total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "PIX")
    total_cartao = sum(c["valor_liquido"] for c in comprovantes if "x" in c["tipo"])

    return (
        "📊 *Status Atual:*\n"
        f"✅ Total pago: R$ {total_pago:,.2f}".replace(".", ",") + "\n"
        f"⏳ Total pendente: R$ {total_pendente:,.2f}".replace(".", ",") + "\n"
        f"💳 Total via Cartão: R$ {total_cartao:,.2f}".replace(".", ",") + "\n"
        f"💸 Total via PIX: R$ {total_pix:,.2f}".replace(".", ",")
    )


def ajuda():
    return (
        "📌 *Comandos Disponíveis:*\n"
        "• 1000,00 pix → registra comprovante PIX\n"
        "• 2000,00 6x → registra cartão 6x\n"
        "• listar pendentes → lista não pagos\n"
        "• listar pagos → lista pagos\n"
        "• pagamento feito 500,00 → registra pagamento parcial\n"
        "• solicitar pagamento → iniciar pedido\n"
        "• status → mostra total\n"
        "• limpar tudo → limpa dados (admin)\n"
    )