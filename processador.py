def aplicar_taxa(valor, tipo_pagamento):
    valor = float(valor.replace(',', '.'))
    if tipo_pagamento == "pix":
        taxa = 0.002
    else:
        parcelas = int(tipo_pagamento.replace("x", ""))
        tabela = {
            1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659,
            5: 0.0719, 6: 0.0829, 7: 0.0919, 8: 0.0999,
            9: 0.1029, 10: 0.1088, 11: 0.1199, 12: 0.1252,
            13: 0.1369, 14: 0.1419, 15: 0.1469, 16: 0.1519,
            17: 0.1589, 18: 0.1684
        }
        taxa = tabela.get(parcelas, 0)
    valor_liquido = valor * (1 - taxa)
    return valor, taxa, valor_liquido

def processar_comprovante(valor_str, tipo_pagamento):
    try:
        valor_original, taxa, valor_liquido = aplicar_taxa(valor_str, tipo_pagamento)
        return f"""
📄 *Comprovante analisado:*
💰 Valor bruto: R$ {valor_original:,.2f}
💳 Pagamento: {tipo_pagamento.upper()}
📉 Taxa aplicada: {taxa*100:.2f}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}
""".strip()
    except:
        return "❌ Erro ao processar o comprovante. Envie no formato correto. Ex: 1200,50 pix ou 1300,00 3x"

def marcar_comprovante_como_pago(lista):
    for c in reversed(lista):
        if not c["pago"]:
            c["pago"] = True
            return "✅ Comprovante marcado como *pago*."
    return "⚠️ Nenhum comprovante pendente encontrado."

def listar_comprovantes_pendentes(lista):
    pendentes = [c for c in lista if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."
    return "\n".join([f"• {c['valor']} ({c['tipo']})" for c in pendentes])

def listar_comprovantes_pagos(lista):
    pagos = [c for c in lista if c["pago"]]
    if not pagos:
        return "❌ Nenhum comprovante pago."
    return "\n".join([f"• {c['valor']} ({c['tipo']})" for c in pagos])

def calcular_total_pendente(lista):
    total = 0
    for c in lista:
        if not c["pago"]:
            _, _, liquido = aplicar_taxa(c["valor"], c["tipo"])
            total += liquido
    return f"📌 Total pendente: R$ {total:,.2f}"

def calcular_total_geral(lista):
    total = 0
    for c in lista:
        _, _, liquido = aplicar_taxa(c["valor"], c["tipo"])
        total += liquido
    return f"📊 Total geral (pagos + pendentes): R$ {total:,.2f}"

def obter_ultimo_comprovante(lista):
    if not lista:
        return "❌ Nenhum comprovante registrado ainda."
    ultimo = lista[-1]
    status = "✅ Pago" if ultimo["pago"] else "⏳ Pendente"
    return f"📄 Último comprovante:\n• Valor: {ultimo['valor']} ({ultimo['tipo']})\n• Status: {status}"

def exibir_ajuda():
    return """
🛠️ *Comandos disponíveis:*

💳 `1000,00 pix` → Calcula com taxa PIX
💳 `1200,00 3x` → Calcula com taxa de cartão (parcelas)
✅ `✅` → Marca último como pago

📋 `listar pendentes` → Ver comprovantes pendentes  
📋 `listar pagos` → Ver comprovantes pagos  
📌 `total que devo` → Total pendente  
📊 `total geral` → Total com tudo  
🕐 `último comprovante` → Mostra o último enviado  
❓ `ajuda` → Exibe esta lista
""".strip()
