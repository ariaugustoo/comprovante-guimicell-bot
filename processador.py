import re
from datetime import datetime

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59,
    5: 7.19, 6: 8.29, 7: 9.19, 8: 9.99,
    9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19,
    17: 15.89, 18: 16.84
}
TAXA_PIX = 0.2

comprovantes = []

def formatar_mensagem(valor_bruto, parcelas, taxa, valor_liquido):
    return (
        f"📄 Comprovante analisado:\n"
        f"💰 Valor bruto: R$ {valor_bruto:,.2f}\n"
        f"💳 Parcelas: {parcelas}x\n"
        f"📉 Taxa aplicada: {taxa:.2f}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )

def processar_mensagem(bot, message):
    texto = message.caption if message.caption else message.text

    if not texto:
        return None

    texto = texto.lower().replace(",", ".")
    match_pix = re.match(r"([\d.]+)\s*pix", texto)
    match_cartao = re.match(r"([\d.]+)\s*(\d{1,2})x", texto)

    if match_pix:
        valor = float(match_pix.group(1))
        taxa = TAXA_PIX
        valor_liquido = valor * (1 - taxa / 100)
        comprovantes.append({"valor": valor, "parcelas": 1, "taxa": taxa, "liquido": valor_liquido, "pago": False})
        return formatar_mensagem(valor, 1, taxa, valor_liquido)

    elif match_cartao:
        valor = float(match_cartao.group(1))
        parcelas = int(match_cartao.group(2))
        taxa = taxas_cartao.get(parcelas, 0)
        valor_liquido = valor * (1 - taxa / 100)
        comprovantes.append({"valor": valor, "parcelas": parcelas, "taxa": taxa, "liquido": valor_liquido, "pago": False})
        return formatar_mensagem(valor, parcelas, taxa, valor_liquido)

    elif texto == "total que devo":
        total = sum(c["liquido"] for c in comprovantes if not c["pago"])
        return f"💸 Total a pagar (pendente): R$ {total:,.2f}"

    elif texto == "total geral":
        total = sum(c["liquido"] for c in comprovantes)
        return f"📊 Total geral (incluindo pagos): R$ {total:,.2f}"

    elif texto == "listar pendentes":
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            return "✅ Todos os comprovantes foram pagos."
        return "\n\n".join([formatar_mensagem(c["valor"], c["parcelas"], c["taxa"], c["liquido"]) for c in pendentes])

    elif texto == "listar pagos":
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            return "Nenhum comprovante foi marcado como pago ainda."
        return "\n\n".join([formatar_mensagem(c["valor"], c["parcelas"], c["taxa"], c["liquido"]) for c in pagos])

    elif texto == "último comprovante":
        if not comprovantes:
            return "Nenhum comprovante registrado ainda."
        ultimo = comprovantes[-1]
        return formatar_mensagem(ultimo["valor"], ultimo["parcelas"], ultimo["taxa"], ultimo["liquido"])

    elif "✅" in texto:
        if comprovantes:
            comprovantes[-1]["pago"] = True
            return "✅ Último comprovante marcado como pago."
        else:
            return "Nenhum comprovante encontrado para marcar como pago."

    elif texto == "ajuda":
        return (
            "📌 Comandos disponíveis:\n"
            "• `200,00 pix` → Aplica taxa de 0,2%\n"
            "• `3644,90 10x` → Aplica taxa da tabela de cartão\n"
            "• `✅` → Marca último comprovante como pago\n"
            "• `total que devo` → Mostra total pendente\n"
            "• `listar pendentes` → Lista comprovantes não pagos\n"
            "• `listar pagos` → Lista comprovantes pagos\n"
            "• `último comprovante` → Mostra último registro\n"
            "• `total geral` → Soma tudo (pago + pendente)"
        )

    return None
