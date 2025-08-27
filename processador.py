import re
from datetime import datetime
from unidecode import unidecode

comprovantes = []
ADMIN_ID = 5857469519

TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}

def normalizar_valor(valor_str):
    valor_str = valor_str.replace(".", "").replace(",", ".")
    return float(re.sub(r"[^\d.]", "", valor_str))

def processar_mensagem(mensagem, user_id):
    texto = unidecode(mensagem.lower().strip())

    if "pix" in texto:
        match = re.search(r"([\d.,]+)\s*pix", texto)
        if match:
            valor = normalizar_valor(match.group(1))
            taxa = 0.2
            liquido = round(valor * (1 - taxa / 100), 2)
            comprovantes.append({
                "valor_bruto": valor,
                "tipo": "pix",
                "parcelas": 1,
                "taxa": taxa,
                "valor_liquido": liquido,
                "pago": False,
                "hora": datetime.now().strftime("%H:%M")
            })
            return (
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💸 Taxa: {taxa:.2f}%\n"
                f"✅ Valor liquido a pagar: R$ {liquido:,.2f}"
            )

    match = re.search(r"([\d.,]+)\s*(\d{1,2})x", texto)
    if match:
        valor = normalizar_valor(match.group(1))
        parcelas = int(match.group(2))
        taxa = TAXAS_CARTAO.get(parcelas)
        if taxa:
            liquido = round(valor * (1 - taxa / 100), 2)
            comprovantes.append({
                "valor_bruto": valor,
                "tipo": "cartao",
                "parcelas": parcelas,
                "taxa": taxa,
                "valor_liquido": liquido,
                "pago": False,
                "hora": datetime.now().strftime("%H:%M")
            })
            return (
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💳 Parcelas: {parcelas}x\n"
                f"💸 Taxa aplicada: {taxa:.2f}%\n"
                f"✅ Valor liquido a pagar: R$ {liquido:,.2f}"
            )

    if "✅" in texto:
        for c in reversed(comprovantes):
            if not c["pago"]:
                c["pago"] = True
                return "✅ Ultimo comprovante marcado como pago!"
        return "❗ Nenhum comprovante pendente para marcar como pago."

    if "total que devo" in texto:
        total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        return f"💰 Total em aberto: R$ {total:,.2f}"

    if "listar pendentes" in texto:
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            return "🎉 Nenhum comprovante pendente!"
        resposta = "📌 Pendentes:\n"
        for i, c in enumerate(pendentes, 1):
            tipo_str = "Pix" if c["tipo"] == "pix" else "Cartao {}x".format(c["parcelas"])
            resposta += (
                f"{i}️⃣ R$ {c['valor_bruto']:,.2f} • {tipo_str} • "
                f"💸 Taxa: {c['taxa']}% • 🔻 Liquido: R$ {c['valor_liquido']:,.2f}\n"
            )
        return resposta

    if "listar pagos" in texto:
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            return "Nenhum comprovante pago ainda."
        resposta = "✅ Pagos:\n"
        for i, c in enumerate(pagos, 1):
            tipo_str = "Pix" if c["tipo"] == "pix" else "Cartao {}x".format(c["parcelas"])
            resposta += (
                f"{i}️⃣ R$ {c['valor_bruto']:,.2f} • {tipo_str} • "
                f"💸 Taxa: {c['taxa']}% • 🔻 Liquido: R$ {c['valor_liquido']:,.2f}\n"
            )
        return resposta

    if "ultimo comprovante" in texto:
        if not comprovantes:
            return "Nenhum comprovante enviado ainda."
        c = comprovantes[-1]
        tipo_str = "Pix" if c["tipo"] == "pix" else "Cartao {}x".format(c["parcelas"])
        status = "✅ Pago" if c["pago"] else "❌ Nao pago"
        return (
            f"📄 Ultimo comprovante:\n"
            f"💰 Valor: R$ {c['valor_bruto']:,.2f}\n"
            f"📋 Tipo: {tipo_str}\n"
            f"💸 Taxa: {c['taxa']}%\n"
            f"🔻 Liquido: R$ {c['valor_liquido']:,.2f}\n"
            f"⏰ Horario: {c['hora']}\n"
            f"{status}"
        )

    if "total geral" in texto:
        total = sum(c["valor_liquido"] for c in comprovantes)
        return f"📊 Total geral de comprovantes: R$ {total:,.2f}"

    if "/limpar tudo" in texto and user_id == ADMIN_ID:
        comprovantes.clear()
        return "🗑️ Todos os comprovantes foram removidos."

    if "/corrigir valor" in texto and user_id == ADMIN_ID:
        match = re.search(r"/corrigir valor ([\d.,]+)", texto)
        if match and comprovantes:
            novo_valor = normalizar_valor(match.group(1))
            c = comprovantes[-1]
            taxa = c["taxa"]
            liquido = round(novo_valor * (1 - taxa / 100), 2)
            c["valor_bruto"] = novo_valor
            c["valor_liquido"] = liquido
            return (
                f"✏️ Valor corrigido com sucesso:\n"
                f"Novo valor: R$ {novo_valor:,.2f}\n"
                f"💸 Taxa: {taxa}%\n"
                f"✅ Liquido recalculado: R$ {liquido:,.2f}"
            )

    return "❌ Formato invalido. Envie algo como '6438,90 pix' ou '7899,99 10x'."
