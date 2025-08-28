from datetime import datetime
import re

comprovantes = []
ADMIN_ID = "5857469519"

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def aplicar_taxa(valor, parcelas):
    if parcelas is None:
        taxa = 0.2  # PIX
    else:
        taxa = taxas_cartao.get(parcelas, 0)
    return round(valor * (1 - taxa / 100), 2)

def normalizar_valor(texto):
    texto = texto.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    return float(re.findall(r"\d+\.\d+", texto)[0])

def processar_mensagem(mensagem):
    texto = mensagem.text.lower()
    nome = mensagem.from_user.first_name
    user_id = str(mensagem.from_user.id)

    if "pix" in texto:
        try:
            valor = normalizar_valor(texto)
            valor_liquido = aplicar_taxa(valor, None)
            comprovantes.append({
                "valor_bruto": valor,
                "parcelas": None,
                "valor_liquido": valor_liquido,
                "pago": False,
                "timestamp": datetime.now()
            })
            return f"📄 Comprovante registrado:\n💰 Valor bruto: R$ {valor:,.2f}\n💳 Forma: PIX\n📉 Taxa: 0.2%\n✅ Valor líquido: R$ {valor_liquido:,.2f}"
        except:
            return "Erro ao processar valor PIX."

    if "x" in texto:
        try:
            match = re.search(r"(\d+[.,]?\d*)\s*(\d{1,2})x", texto)
            if match:
                valor = float(match.group(1).replace(".", "").replace(",", "."))
                parcelas = int(match.group(2))
                valor_liquido = aplicar_taxa(valor, parcelas)
                comprovantes.append({
                    "valor_bruto": valor,
                    "parcelas": parcelas,
                    "valor_liquido": valor_liquido,
                    "pago": False,
                    "timestamp": datetime.now()
                })
                return f"📄 Comprovante registrado:\n💰 Valor bruto: R$ {valor:,.2f}\n💳 Parcelas: {parcelas}x\n📉 Taxa: {taxas_cartao[parcelas]}%\n✅ Valor líquido: R$ {valor_liquido:,.2f}"
        except:
            return "Erro ao processar valor no cartão."

    if texto == "pagamento feito":
        for c in reversed(comprovantes):
            if not c["pago"]:
                c["pago"] = True
                return "✅ Último comprovante marcado como pago com sucesso."
        return "Nenhum comprovante pendente para marcar como pago."

    if texto == "total líquido":
        total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        return f"💰 Total líquido a pagar (pendente): R$ {total:,.2f}"

    if texto == "total a pagar":
        total = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
        return f"💰 Total bruto pendente: R$ {total:,.2f}"

    if texto == "listar pagos":
        pagos = [c for c in comprovantes if c["pago"]]
        return formatar_comprovantes(pagos, "✅ Comprovantes pagos:")

    if texto == "listar pendentes":
        pendentes = [c for c in comprovantes if not c["pago"]]
        return formatar_comprovantes(pendentes, "📌 Comprovantes pendentes:")

    if texto == "ajuda":
        return (
            "🧠 *Comandos disponíveis:*\n"
            "• `valor pix` → registra comprovante via PIX\n"
            "• `valor 3x` → registra comprovante no cartão\n"
            "• `pagamento feito` → marca último comprovante como pago\n"
            "• `total líquido` → mostra valor líquido a repassar\n"
            "• `total a pagar` → mostra valor bruto pendente\n"
            "• `listar pagos` → exibe lista de comprovantes pagos\n"
            "• `listar pendentes` → exibe lista de comprovantes pendentes\n"
            "• `solicitar pagamento` → abate valor manualmente (admin)"
        )

    if texto.startswith("solicitar pagamento") and user_id == ADMIN_ID:
        try:
            valor = normalizar_valor(texto)
            pendentes = [c for c in comprovantes if not c["pago"]]
            restante = valor
            for c in pendentes:
                if restante >= c["valor_liquido"]:
                    c["pago"] = True
                    restante -= c["valor_liquido"]
            return f"💰 Valor solicitado de R$ {valor:,.2f} abatido com sucesso dos comprovantes pendentes."
        except:
            return "Erro ao processar valor digitado."

    return None

def formatar_comprovantes(lista, titulo):
    if not lista:
        return f"{titulo}\nNenhum encontrado."
    
    linhas = []
    for c in lista:
        parcelas_str = "PIX" if c['parcelas'] is None else f"{c['parcelas']}x"
        linha = f"📄 {c['valor_bruto']:,.2f} | {parcelas_str} | R$ {c['valor_liquido']:,.2f}"
        linhas.append(linha)

    total = sum(c['valor_liquido'] for c in lista)
    return f"{titulo}\n" + "\n".join(linhas) + f"\n\n🔢 Total: R$ {total:,.2f}"
