from telegram import Update
from telegram.ext import CallbackContext
import re

comprovantes = []
pagamentos = []
solicitacoes = []

def parse_valor(mensagem):
    mensagem = mensagem.replace('.', '').replace(',', '.')
    match = re.search(r"(\d+(\.\d{1,2})?)", mensagem)
    return float(match.group(1)) if match else None

def tipo_pagamento(mensagem):
    if "pix" in mensagem.lower():
        return "PIX"
    elif "x" in mensagem.lower():
        return "Cartão"
    return "Indefinido"

def taxa_pagamento(mensagem):
    if "pix" in mensagem.lower():
        return 0.002
    match = re.search(r"(\d{1,2})x", mensagem.lower())
    if match:
        parcelas = int(match.group(1))
        tabela = {
            1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659,
            5: 0.0719, 6: 0.0829, 7: 0.0919, 8: 0.0999,
            9: 0.1029, 10: 0.1088, 11: 0.1199, 12: 0.1252,
            13: 0.1369, 14: 0.1419, 15: 0.1469, 16: 0.1519,
            17: 0.1589, 18: 0.1684
        }
        return tabela.get(parcelas, 0.15)
    return 0.0

def formatar(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def processar_mensagem(update: Update, context=None):
    mensagem = update.message.text.lower()
    chat_id = update.message.chat_id

    if "ajuda" in mensagem:
        update.message.reply_text(listar_comandos())
        return
    if "listar pendentes" in mensagem:
        update.message.reply_text(listar_pendentes())
        return
    if "listar pagos" in mensagem:
        update.message.reply_text(listar_pagos())
        return
    if "solicitar pagamento" in mensagem:
        update.message.reply_text("💸 Digite o valor que deseja solicitar:")
        return
    if "status" in mensagem or "fechamento do dia" in mensagem:
        update.message.reply_text(comando_status())
        return
    if "pagamento feito" in mensagem:
        update.message.reply_text(registrar_pagamento())
        return
    if "quanto devo" in mensagem:
        total = sum([c["valor_liquido"] for c in comprovantes]) - sum(pagamentos)
        update.message.reply_text(f"💰 Devo ao lojista: {formatar(total)}")
        return

    valor = parse_valor(mensagem)
    if not valor:
        update.message.reply_text("❗ Não entendi o valor. Envie no formato correto.")
        return

    tipo = tipo_pagamento(mensagem)
    taxa = taxa_pagamento(mensagem)
    liquido = round(valor * (1 - taxa), 2)

    comprovantes.append({
        "bruto": valor,
        "tipo": tipo,
        "taxa": taxa,
        "valor_liquido": liquido
    })

    resposta = f"""📄 *Comprovante analisado:*
💰 Valor bruto: {formatar(valor)}
💰 Tipo: {tipo}
📉 Taxa aplicada: {taxa*100:.2f}%
✅ Valor líquido a pagar: {formatar(liquido)}"""

    update.message.reply_text(resposta, parse_mode="Markdown")

def registrar_pagamento():
    if not solicitacoes:
        return "⚠️ Nenhuma solicitação pendente."

    valor_pago = solicitacoes.pop(0)
    total_liquido = sum(c["valor_liquido"] for c in comprovantes)
    total_pago = sum(pagamentos)

    if total_pago + valor_pago > total_liquido:
        return f"❌ O valor pago excede o total pendente."

    pagamentos.append(valor_pago)
    return f"✅ Recebido! Estamos quase quitando tudo 😉"

def listar_comandos():
    return """📋 *Comandos disponíveis:*
1. `valor + pix` → Ex: `1000 pix`
2. `valor + parcelas` → Ex: `3000 6x`
3. `listar pendentes`
4. `listar pagos`
5. `solicitar pagamento`
6. `pagamento feito`
7. `quanto devo`
8. `status` ou `fechamento do dia`
9. `ajuda`"""

def listar_pendentes():
    pendentes = [c for c in comprovantes]
    texto = ""
    for i, c in enumerate(pendentes, 1):
        texto += f"{i}. {formatar(c['valor_liquido'])} - {c['tipo']}\n"
    return f"📌 Comprovantes pendentes:\n{texto or '✅ Nenhum'}"

def listar_pagos():
    if not pagamentos:
        return "💳 Nenhum pagamento foi feito ainda."
    texto = "\n".join([f"{i+1}. {formatar(v)}" for i, v in enumerate(pagamentos)])
    return f"✅ Pagamentos realizados:\n{texto}"

def comando_status():
    total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "PIX")
    total_cartao = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "Cartão")
    total_pago = sum(pagamentos)
    total_liquido = sum(c["valor_liquido"] for c in comprovantes)
    total_pendente = total_liquido - total_pago

    return f"""📊 *Fechamento do dia:*
💳 Total em Cartão: {formatar(total_cartao)}
💸 Total em PIX: {formatar(total_pix)}
✅ Total pago: {formatar(total_pago)}
⏳ Total pendente: {formatar(total_pendente)}"""
