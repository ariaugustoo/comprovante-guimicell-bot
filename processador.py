from datetime import datetime
from unidecode import unidecode

comprovantes = []
pagamentos = []

# Tabela de taxas para cartão por número de parcelas
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def normalizar_valor(valor_str):
    try:
        valor_str = valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor_str)
    except:
        return None

def processar_mensagem(mensagem):
    texto = unidecode(mensagem.lower())
    agora = datetime.now().strftime("%H:%M")

    if "pix" in texto:
        partes = texto.split()
        valor = normalizar_valor(partes[0])
        if valor is None:
            return "❌ Valor inválido. Use o formato: `1000 pix`"
        taxa = 0.2
        valor_liquido = round(valor * (1 - taxa / 100), 2)

        comprovantes.append({
            "tipo": "pix",
            "valor_bruto": valor,
            "valor_liquido": valor_liquido,
            "taxa": taxa,
            "hora": agora,
            "pago": False
        })

        return f"""📄 Comprovante analisado:
💰 Valor bruto: R$ {valor:,.2f}
💰 Tipo: PIX
⏰ Horário: {agora}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"""

    elif "x" in texto:
        partes = texto.split()
        valor = normalizar_valor(partes[0])
        try:
            parcelas = int(partes[1].replace("x", ""))
        except:
            return "❌ Número de parcelas inválido. Use o formato: `1000 10x`"

        if valor is None or parcelas not in TAXAS_CARTAO:
            return "❌ Formato inválido ou número de parcelas não suportado. Use por exemplo: `1000 3x`"

        taxa = TAXAS_CARTAO[parcelas]
        valor_liquido = round(valor * (1 - taxa / 100), 2)

        comprovantes.append({
            "tipo": f"cartão {parcelas}x",
            "valor_bruto": valor,
            "valor_liquido": valor_liquido,
            "taxa": taxa,
            "hora": agora,
            "pago": False
        })

        return f"""📄 Comprovante analisado:
💰 Valor bruto: R$ {valor:,.2f}
💰 Tipo: Cartão {parcelas}x
⏰ Horário: {agora}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"""

    return "❌ Comando não reconhecido. Digite `ajuda` para ver as opções."

def marcar_como_pago():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente para marcar como pago."

    ultimo = pendentes[-1]
    ultimo["pago"] = True
    pagamentos.append(ultimo)
    return f"✅ Pagamento de R$ {ultimo['valor_liquido']:,.2f} marcado como feito com sucesso."

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."

    texto = "📌 *Comprovantes Pendentes:*\n"
    total = 0
    for c in pendentes:
        texto += f"💸 {c['tipo']} | Bruto: R$ {c['valor_bruto']:,.2f} | Líquido: R$ {c['valor_liquido']:,.2f} | ⏰ {c['hora']}\n"
        total += c["valor_liquido"]

    texto += f"\n📊 *Total líquido a pagar:* R$ {total:,.2f}"
    return texto

def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "📭 Nenhum comprovante marcado como pago ainda."

    texto = "📗 *Comprovantes Pagos:*\n"
    total = 0
    for c in pagos:
        texto += f"✅ {c['tipo']} | Líquido: R$ {c['valor_liquido']:,.2f} | ⏰ {c['hora']}\n"
        total += c["valor_liquido"]

    texto += f"\n📦 *Total já pago:* R$ {total:,.2f}"
    return texto

def total_liquido():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    return f"💰 Total líquido a pagar (pendente): R$ {total:,.2f}"

def total_bruto():
    total = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
    return f"💰 Total bruto dos pendentes: R$ {total:,.2f}"

def solicitar_pagamento(context):
    context.bot.send_message(chat_id=context._chat_id, text="Digite o valor solicitado em R$, e após o pagamento digite 'pagamento feito'.")
    return "📬 Solicitação de pagamento iniciada."

def ajuda():
    return """📋 *Comandos disponíveis:*
• Enviar valor + forma de pagamento:
   - `1000 pix`
   - `2000 6x`
• `pagamento feito` – marca o último como pago
• `total líquido` – mostra o total a pagar com taxas
• `total a pagar` – mostra o total bruto dos pendentes
• `listar pendentes` – lista os comprovantes ainda abertos
• `listar pagos` – lista os já pagos
• `solicitar pagamento` – inicia solicitação manual
• `ajuda` – mostra esse menu
"""
