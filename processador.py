import re
from datetime import datetime
from unidecode import unidecode

# Armazena os comprovantes recebidos
comprovantes = []

# ID do administrador para comandos restritos
ADMIN_ID = 5857469519

# Tabela de taxas por parcelas de cartao (percentuais)
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}

# Remove pontuacoes e converte para float
def normalizar_valor(valor_str):
    valor_str = valor_str.replace(".", "").replace(",", ".")
    return float(re.sub(r"[^\d.]", "", valor_str))

# Processa qualquer mensagem recebida
def processar_mensagem(mensagem, user_id):
    texto = unidecode(mensagem.lower().strip())

    # 1. Pagamento via PIX
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

    # 2. Pagamento via Cartao com parcelas (ex: 7899,99 10x)
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

    # 3. Marcar ultimo comprovante como pago (responde com emoji ✅)
    if "✅" in texto:
        for c in reversed(comprovantes):
            if not c["pago"]:
                c["pago"] = True
                return "✅ Ultimo comprovante marcado como pago!"
        return "❗ Nenhum comprovante pendente para marcar como pago."

    # 4. Mostrar total pendente
    if "total que devo" in texto:
        total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        return f"💰 Total em aberto: R$ {total:,.2f}"

    # 5. Listar pendentes
    if "listar pendentes" in texto:
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            return "🎉 Nenhum comprovante pendente!"
        resposta = "📌 Pendentes:\n"
        for i, c in enumerate(pendentes, 1):
            resposta += (
                f"{i}️⃣ R$ {c['valor_bruto']:,.2f} • "
                f"{'Pix' if c['tipo']=='pix' else f'Cartao {c['parcelas']}x'} • "
                f"💸 Taxa: {c['taxa']}% • 🔻 Liquido: R$ {c['valor_liquido']:,.2f}\n"
            )
        return resposta

    # 6. Listar pagos
    if "listar pagos" in texto:
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            return "Nenhum comprovante pago ainda."
        resposta = "✅ Pagos:\n"
        for i, c in enumerate(pagos, 1):
            resposta += (
                f"{i}️⃣ R$ {c['valor_bruto']:,.2f} • "
                f"{'Pix' if c['tipo']=='pix' else f'Cartao {c['parcelas']}x'} • "
                f"💸 Taxa: {c['taxa']}% • 🔻 Liquido: R$ {c['valor_liquido']:,.2f}\n"
            )
        return resposta

    # 7. Mostrar ultimo comprovante
    if "ultimo comprovante" in texto:
        if not comprovantes:
            return "Nenhum comprovante enviado ainda."
        c = comprovantes[-1]
        status = "✅ Pago" if c["pago"] else "❌ Nao pago"
        return (
            f"📄 Ultimo comprovante:\n"
            f"💰 Valor: R$ {c['valor_bruto']:,.2f}\n"
            f"📋 Tipo: {'Pix' if c['tipo']=='pix' else f'Cartao {c['parcelas']}x'}\n"
            f"💸 Taxa: {c['taxa']}%\n"
            f"🔻 Liquido: R$ {c['valor_liquido']:,.2f}\n"
            f"⏰ Horario: {c['hora']}\n"
            f"{status}"
        )

    # 8. Mostrar total geral (pagos + pendentes)
    if "total geral" in texto:
        total = sum(c["valor_liquido"] for c in comprovantes)
        return f"📊 Total geral de comprovantes: R$ {total:,.2f}"

    # 9. Limpar todos os dados (somente admin)
    if "/limpar tudo" in texto and user_id == ADMIN_ID:
        comprovantes.clear()
        return "🗑️ Todos os comprovantes foram removidos."

    # 10. Corrigir valor do ultimo comprovante (somente admin)
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

    # Comando desconhecido
    return "❌ Formato invalido. Envie algo como '6438,90 pix' ou '7899,99 10x'."
