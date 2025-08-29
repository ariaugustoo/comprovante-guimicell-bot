import re
from datetime import datetime, timedelta
from pytz import timezone

comprovantes = []
pagamentos_feitos = []
solicitacoes_pagamento = []

# Tabela de taxas para cartão de 1x a 18x
taxas_cartao = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719,
    6: 0.0829, 7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088,
    11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
    16: 0.1519, 17: 0.1589, 18: 0.1684
}

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def extrair_valor(texto):
    match = re.search(r"([\d.,]+)", texto)
    if match:
        valor_str = match.group(1).replace('.', '').replace(',', '.')
        try:
            return float(valor_str)
        except ValueError:
            return None
    return None

def detectar_pix_ou_cartao(texto):
    texto = texto.lower()
    if "pix" in texto:
        return "pix", 0.002
    parcelas = re.findall(r'(\d{1,2})x', texto)
    if parcelas:
        n = int(parcelas[0])
        if 1 <= n <= 18:
            return f"{n}x", taxas_cartao[n]
    return None, 0

def processar_mensagem(texto):
    valor = extrair_valor(texto)
    tipo, taxa = detectar_pix_ou_cartao(texto)

    if valor and tipo:
        agora = datetime.now(timezone("America/Sao_Paulo"))
        valor_liquido = round(valor * (1 - taxa), 2)

        comprovantes.append({
            "valor_bruto": valor,
            "valor_liquido": valor_liquido,
            "tipo": tipo.upper(),
            "horario": agora.strftime("%H:%M"),
            "pago": False
        })

        return (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: {formatar_valor(valor)}\n"
            f"💰 Tipo: {tipo.upper()}\n"
            f"⏰ Horário: {agora.strftime('%H:%M')}\n"
            f"📉 Taxa aplicada: {taxa*100:.2f}%\n"
            f"✅ Valor líquido a pagar: {formatar_valor(valor_liquido)}"
        )
    return None

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum pagamento pendente."

    linhas = ["📋 *Pendentes:*"]
    total = 0
    for c in pendentes:
        linhas.append(
            f"💰 {formatar_valor(c['valor_liquido'])} - {c['tipo']} às {c['horario']}"
        )
        total += c['valor_liquido']

    linhas.append(f"\n💵 Total pendente: {formatar_valor(total)}")
    return "\n".join(linhas)

def listar_pagamentos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "📭 Nenhum comprovante foi marcado como pago ainda."

    linhas = ["📗 *Pagamentos realizados:*"]
    total = 0
    for c in pagos:
        linhas.append(
            f"✅ {formatar_valor(c['valor_liquido'])} - {c['tipo']} às {c['horario']}"
        )
        total += c['valor_liquido']

    linhas.append(f"\n💵 Total pago: {formatar_valor(total)}")
    return "\n".join(linhas)

def marcar_como_pago(valor=None):
    if valor is None:
        # se tiver solicitação de pagamento pendente
        if solicitacoes_pagamento:
            solicitado = solicitacoes_pagamento.pop(0)
            return pagamento_parcial(solicitado['valor'])
        return "❌ Nenhum valor especificado e nenhuma solicitação de pagamento pendente."

    try:
        valor = float(str(valor).replace('.', '').replace(',', '.'))
    except:
        return "❌ Valor inválido."

    return pagamento_parcial(valor)

def pagamento_parcial(valor_pago):
    pendentes = [c for c in comprovantes if not c["pago"]]
    total_pendente = sum(c["valor_liquido"] for c in pendentes)

    if valor_pago > total_pendente:
        return f"❌ Valor pago ({formatar_valor(valor_pago)}) excede o total pendente ({formatar_valor(total_pendente)})."

    for c in pendentes:
        if not c["pago"]:
            if valor_pago >= c["valor_liquido"]:
                valor_pago -= c["valor_liquido"]
                c["pago"] = True
            else:
                c["valor_liquido"] -= valor_pago
                valor_pago = 0
            if valor_pago <= 0:
                break

    return f"✅ Pagamento registrado! Valor abatido: {formatar_valor(valor_pago)}"

def calcular_total_liquido_pendente():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    return f"💰 Devo ao lojista: {formatar_valor(total)}"

def calcular_total_bruto_pendente():
    total = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
    return f"📊 Total bruto dos comprovantes pendentes: {formatar_valor(total)}"

def solicitar_pagamento(valor, chave_pix):
    try:
        valor = float(str(valor).replace('.', '').replace(',', '.'))
    except:
        return "❌ Valor inválido para solicitação."

    total_pendente = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    if valor > total_pendente:
        return f"❌ Você está solicitando mais do que o valor disponível. Total disponível: {formatar_valor(total_pendente)}"

    solicitacoes_pagamento.append({"valor": valor, "chave": chave_pix})
    return (
        f"📥 *Solicitação de pagamento registrada!*\n"
        f"💸 Valor solicitado: {formatar_valor(valor)}\n"
        f"🔑 Chave Pix: `{chave_pix}`\n\n"
        f"Aguardando confirmação com *Pagamento feito* para registrar o valor como pago."
    )

def status_geral():
    total_pago = sum(c["valor_liquido"] for c in comprovantes if c["pago"])
    total_pendente = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "PIX")
    total_cartao = sum(c["valor_liquido"] for c in comprovantes if "X" in c["tipo"])

    return (
        "📊 *Status Geral:*\n"
        f"✅ Total pago: {formatar_valor(total_pago)}\n"
        f"🕐 Total pendente: {formatar_valor(total_pendente)}\n"
        f"💸 Via PIX: {formatar_valor(total_pix)}\n"
        f"💳 Via Cartão: {formatar_valor(total_cartao)}"
    )

def fechamento_do_dia():
    hoje = datetime.now(timezone("America/Sao_Paulo")).strftime("%d/%m/%Y")

    total_pago = sum(c["valor_liquido"] for c in comprovantes if c["pago"])
    total_pendente = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "PIX")
    total_cartao = sum(c["valor_liquido"] for c in comprovantes if "X" in c["tipo"])

    return (
        f"📅 *Fechamento do dia – {hoje}:*\n"
        f"✅ Total pago: {formatar_valor(total_pago)}\n"
        f"🕐 Total pendente: {formatar_valor(total_pendente)}\n"
        f"💸 Via PIX: {formatar_valor(total_pix)}\n"
        f"💳 Via Cartão: {formatar_valor(total_cartao)}"
    )

def limpar_tudo():
    comprovantes.clear()
    pagamentos_feitos.clear()
    solicitacoes_pagamento.clear()
    return "⚠️ Todos os dados foram apagados."

def corrigir_valor(indice, novo_valor):
    try:
        novo_valor = float(str(novo_valor).replace('.', '').replace(',', '.'))
        c = comprovantes[indice]
        tipo, taxa = detectar_pix_ou_cartao(c["tipo"])
        c["valor_liquido"] = round(novo_valor * (1 - taxa), 2)
        c["valor_bruto"] = novo_valor
        return f"✏️ Valor do comprovante #{indice+1} atualizado para {formatar_valor(novo_valor)}"
    except:
        return "❌ Não foi possível atualizar o valor."
