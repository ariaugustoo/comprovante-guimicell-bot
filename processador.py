from datetime import datetime
import re

comprovantes = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}


def normalizar_valor(valor_str):
    valor_str = re.sub(r'[^\d,\.]', '', valor_str)
    valor_str = valor_str.replace('.', '').replace(',', '.')
    try:
        return float(valor_str)
    except ValueError:
        return None


def registrar_pagamento(valor_str, tipo, parcelas=None):
    valor = normalizar_valor(valor_str)
    if valor is None:
        return "❌ Valor inválido. Envie no formato: 1000,00 ou 1000.00"

    horario = datetime.now().strftime("%H:%M")

    if tipo == "PIX":
        taxa = 0.2
        liquido = round(valor * (1 - taxa / 100), 2)
        emoji = "💰"
        mensagem = (
            f"{emoji} *Comprovante registrado:*\n"
            f"Valor bruto: R$ {valor:.2f}\n"
            f"Pagamento: PIX\n"
            f"Horário: {horario}\n"
            f"Taxa: {taxa}%\n"
            f"Valor líquido: R$ {liquido:.2f}"
        )
    elif tipo == "CARTAO":
        if parcelas not in taxas_cartao:
            return "❌ Parcelas inválidas. Use de 1x a 18x."
        taxa = taxas_cartao[parcelas]
        liquido = round(valor * (1 - taxa / 100), 2)
        emoji = "💳"
        mensagem = (
            f"{emoji} *Comprovante registrado:*\n"
            f"Valor bruto: R$ {valor:.2f}\n"
            f"Pagamento: Cartão {parcelas}x\n"
            f"Horário: {horario}\n"
            f"Taxa: {taxa}%\n"
            f"Valor líquido: R$ {liquido:.2f}"
        )
    else:
        return "❌ Tipo de pagamento inválido."

    comprovantes.append({
        "valor_bruto": valor,
        "tipo": tipo,
        "parcelas": parcelas,
        "horario": horario,
        "taxa": taxa,
        "valor_liquido": liquido,
        "pago": False
    })

    return mensagem


def processar_mensagem(texto):
    if "pix" in texto:
        valor_str = texto.replace("pix", "").strip()
        return registrar_pagamento(valor_str, "PIX")

    match = re.match(r"([\d.,]+)\s*(\d{1,2})x", texto)
    if match:
        valor_str = match.group(1)
        parcelas = int(match.group(2))
        return registrar_pagamento(valor_str, "CARTAO", parcelas)

    return "❌ Formato inválido. Tente '1000 pix' ou '1000 6x'"


def marcar_como_pago():
    for comprovante in comprovantes:
        if not comprovante["pago"]:
            comprovante["pago"] = True
            return f"✅ Comprovante de R$ {comprovante['valor_bruto']:.2f} marcado como *pago*."
    return "🎉 Todos os comprovantes já foram pagos!"


def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente!"
    total = sum(c["valor_liquido"] for c in pendentes)
    resposta = "📌 *Comprovantes pendentes:*\n"
    for c in pendentes:
        resposta += f"• R$ {c['valor_bruto']:.2f} - {c['tipo']} - {c['horario']}\n"
    resposta += f"\n💰 Total líquido pendente: R$ {total:.2f}"
    return resposta


def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "📭 Nenhum comprovante foi marcado como pago ainda."
    total = sum(c["valor_liquido"] for c in pagos)
    resposta = "📄 *Comprovantes pagos:*\n"
    for c in pagos:
        resposta += f"• ✅ R$ {c['valor_bruto']:.2f} - {c['tipo']} - {c['horario']}\n"
    resposta += f"\n💵 Total já pago: R$ {total:.2f}"
    return resposta


def total_liquido():
    pendentes = [c for c in comprovantes if not c["pago"]]
    total = sum(c["valor_liquido"] for c in pendentes)
    return f"📉 Total líquido pendente: R$ {total:.2f}"


def total_a_pagar():
    pendentes = [c for c in comprovantes if not c["pago"]]
    total = sum(c["valor_bruto"] for c in pendentes)
    return f"💸 Total bruto a pagar: R$ {total:.2f}"


def solicitar_pagamento(valor_str):
    return registrar_pagamento(valor_str, "PIX")


def ajuda_comandos():
    return (
        "📋 *Comandos disponíveis:*\n\n"
        "• Enviar valor + 'pix' → Calcula valor líquido com 0,2%\n"
        "  Ex: `1000 pix`\n"
        "• Enviar valor + parcelas → Calcula com taxas do cartão\n"
        "  Ex: `1000 6x`\n"
        "• pagamento feito → Marca 1 comprovante como pago\n"
        "• listar pendentes → Lista os comprovantes pendentes\n"
        "• listar pagos → Lista os comprovantes pagos\n"
        "• total líquido → Mostra total líquido pendente\n"
        "• total a pagar → Mostra total bruto a pagar\n"
        "• ajuda → Exibe esta lista de comandos"
    )
