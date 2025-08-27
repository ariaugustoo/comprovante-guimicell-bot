import re

def calcular_taxa(valor, parcelas):
    taxas = {
        1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
        6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
        11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19,
        15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
    }
    taxa = taxas.get(parcelas, 0)
    return round(valor * (1 - taxa / 100), 2), taxa

def processar_mensagem(texto, lista, user_id, admin_id):
    texto = texto.replace(",", ".")
    if texto.lower().endswith("pix"):
        valor = float(re.findall(r"[\d.]+", texto)[0])
        liquido = round(valor * 0.998, 2)
        lista.append({"tipo": "pix", "valor": valor, "liquido": liquido, "status": "pendente"})
        return f"📄 Comprovante analisado:\n💰 Valor bruto: R$ {valor:.2f}\n🏦 Tipo: PIX\n📉 Taxa: 0.2%\n✅ Valor líquido: R$ {liquido:.2f}"

    elif "x" in texto.lower():
        match = re.search(r"([\d.]+)\s*(\d{1,2})x", texto.lower())
        if match:
            valor = float(match.group(1))
            parcelas = int(match.group(2))
            liquido, taxa = calcular_taxa(valor, parcelas)
            lista.append({"tipo": f"{parcelas}x", "valor": valor, "liquido": liquido, "status": "pendente"})
            return f"📄 Comprovante analisado:\n💰 Valor bruto: R$ {valor:.2f}\n💳 Parcelas: {parcelas}x\n📉 Taxa: {taxa:.2f}%\n✅ Valor líquido: R$ {liquido:.2f}"

    elif texto == "✅":
        for item in reversed(lista):
            if item["status"] == "pendente":
                item["status"] = "pago"
                return "✅ Comprovante marcado como *pago*."
        return "Nenhum comprovante pendente encontrado para marcar como pago."

    elif texto.lower() == "total que devo":
        total = sum(item["liquido"] for item in lista if item["status"] == "pendente")
        return f"📌 Total que você deve ao lojista: R$ {total:.2f}"

    elif texto.lower() == "total pago":
        total = sum(item["liquido"] for item in lista if item["status"] == "pago")
        return f"💸 Total já pago ao lojista: R$ {total:.2f}"

    elif texto.lower() == "total geral":
        total = sum(item["liquido"] for item in lista)
        return f"📊 Total geral de comprovantes: R$ {total:.2f}"

    elif texto.lower() == "listar pendentes":
        return "\n".join([f"🔸 R$ {item['liquido']:.2f} ({item['tipo']})" for item in lista if item["status"] == "pendente"]) or "Nenhum comprovante pendente."

    elif texto.lower() == "listar pagos":
        return "\n".join([f"✅ R$ {item['liquido']:.2f} ({item['tipo']})" for item in lista if item["status"] == "pago"]) or "Nenhum comprovante pago."

    elif texto.lower() == "último comprovante":
        if lista:
            item = lista[-1]
            return f"Último comprovante:\n💰 {item['valor']} ({item['tipo']}) - {item['status']}"
        return "Nenhum comprovante enviado ainda."

    elif texto.lower() == "/limpar tudo" and user_id == admin_id:
        lista.clear()
        return "🧹 Todos os comprovantes foram apagados."

    elif texto.lower() == "/corrigir valor" and user_id == admin_id:
        if lista:
            lista.pop()
            return "⚠️ Último comprovante removido para correção."
        return "Nenhum comprovante para remover."

    elif texto.lower() == "ajuda":
        return """🧾 Comandos disponíveis:
• 289,90 pix → Registra PIX
• 500,00 10x → Registra cartão
• ✅ → Marca como pago
• total que devo → Mostra total pendente
• total pago → Mostra quanto já foi pago
• total geral → Soma de tudo
• listar pagos / pendentes
• último comprovante
• /corrigir valor (admin)
• /limpar tudo (admin)"""

    return None

def enviar_resumo_automatico(lista):
    pendente = sum(item["liquido"] for item in lista if item["status"] == "pendente")
    pago = sum(item["liquido"] for item in lista if item["status"] == "pago")
    if pendente == 0 and pago == 0:
        return None
    return f"📋 *Resumo automático (última hora)*\n🔹 Total pendente: R$ {pendente:.2f}\n✅ Total pago: R$ {pago:.2f}"
