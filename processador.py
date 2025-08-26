import re
from datetime import datetime

# Tabela de taxas por número de parcelas
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

COMPROVANTES = []

def calcular_liquido(valor, tipo, parcelas=1):
    if tipo == "pix":
        taxa = 0.2
    else:
        taxa = TAXAS_CARTAO.get(parcelas, 0)
    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def parse_valor(texto):
    valor_match = re.search(r"([\d\.,]+)", texto)
    if not valor_match:
        return None
    valor_str = valor_match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(valor_str)
    except ValueError:
        return None

def parse_parcelas(texto):
    parcelas_match = re.search(r"(\d{1,2})x", texto.lower())
    if parcelas_match:
        return int(parcelas_match.group(1))
    return 1

def processar_mensagem(bot, mensagem):
    texto = mensagem.text.lower() if mensagem.text else ""
    user = mensagem.from_user.first_name
    horario = datetime.now().strftime("%H:%M")

    if texto == "ajuda":
        ajuda = (
            "📌 *Comandos disponíveis:*\n"
            "💰 `valor pix` — Ex: `2438,99 pix`\n"
            "💳 `valor + parcelas` — Ex: `3999,99 10x`\n"
            "✅ — Marca último comprovante como pago\n"
            "📊 `total que devo` — Mostra total pendente\n"
            "📋 `listar pendentes` — Lista os não pagos\n"
            "📗 `listar pagos` — Lista os pagos\n"
            "🔍 `último comprovante` — Mostra o último\n"
            "🧮 `total geral` — Soma tudo\n"
        )
        bot.send_message(chat_id=mensagem.chat_id, text=ajuda, parse_mode="Markdown")
        return

    if "pix" in texto or "x" in texto:
        valor = parse_valor(texto)
        parcelas = parse_parcelas(texto)
        tipo = "pix" if "pix" in texto else "cartao"
        valor_liquido, taxa = calcular_liquido(valor, tipo, parcelas)

        comprovante = {
            "valor": valor,
            "parcelas": parcelas,
            "liquido": valor_liquido,
            "horario": horario,
            "pago": False
        }
        COMPROVANTES.append(comprovante)

        resposta = (
            f"📄 *Comprovante analisado:*\n"
            f"💰 Valor bruto: R$ {valor:,.2f}\n"
            f"{'💳 Parcelas: ' + str(parcelas) + 'x' if tipo == 'cartao' else ''}\n"
            f"⏰ Horário: {horario}\n"
            f"📉 Taxa aplicada: {taxa:.2f}%\n"
            f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
        )
        bot.send_message(chat_id=mensagem.chat_id, text=resposta, parse_mode="Markdown")
        return

    if "✅" in texto and COMPROVANTES:
        COMPROVANTES[-1]["pago"] = True
        bot.send_message(chat_id=mensagem.chat_id, text="✅ Último comprovante marcado como pago.")
        return

    if "total que devo" in texto:
        total = sum(c["liquido"] for c in COMPROVANTES if not c["pago"])
        bot.send_message(chat_id=mensagem.chat_id, text=f"📊 Total pendente: R$ {total:,.2f}")
        return

    if "listar pendentes" in texto:
        pendentes = [c for c in COMPROVANTES if not c["pago"]]
        if not pendentes:
            msg = "🎉 Nenhum comprovante pendente!"
        else:
            msg = "\n".join([f"• R$ {c['liquido']:,.2f} às {c['horario']}" for c in pendentes])
        bot.send_message(chat_id=mensagem.chat_id, text=msg)
        return

    if "listar pagos" in texto:
        pagos = [c for c in COMPROVANTES if c["pago"]]
        if not pagos:
            msg = "❌ Nenhum comprovante pago ainda."
        else:
            msg = "\n".join([f"• R$ {c['liquido']:,.2f} às {c['horario']}" for c in pagos])
        bot.send_message(chat_id=mensagem.chat_id, text=msg)
        return

    if "último comprovante" in texto and COMPROVANTES:
        c = COMPROVANTES[-1]
        msg = (
            f"📄 Último comprovante:\n"
            f"💰 R$ {c['valor']:,.2f} | 💳 {c['parcelas']}x\n"
            f"📉 Taxa: {round(100 * (1 - c['liquido'] / c['valor']), 2):.2f}%\n"
            f"✅ Líquido: R$ {c['liquido']:,.2f} às {c['horario']}\n"
            f"{'🔒 PAGO' if c['pago'] else '🕗 PENDENTE'}"
        )
        bot.send_message(chat_id=mensagem.chat_id, text=msg)
        return

    if "total geral" in texto:
        total = sum(c["liquido"] for c in COMPROVANTES)
        bot.send_message(chat_id=mensagem.chat_id, text=f"📊 Total geral (pago + pendente): R$ {total:,.2f}")
        return
