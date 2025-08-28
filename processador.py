import os
from datetime import datetime
import pytz

comprovantes = []
solicitacoes = []

tz = pytz.timezone('America/Sao_Paulo')
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

TAXA_PIX = 0.002
TAXAS_CARTAO = {
    i: taxa for i, taxa in enumerate([
        4.39, 5.19, 6.19, 6.59, 7.19, 8.29,
        9.19, 9.99, 10.29, 10.88, 11.99, 12.52,
        13.69, 14.19, 14.69, 15.19, 15.89, 16.84
    ], start=1)
}

def formatar(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def extrair_valor(texto):
    try:
        valor_str = texto.replace("pix", "").replace("x", "").replace("R$", "").strip().replace(".", "").replace(",", ".")
        return float(valor_str)
    except:
        return None

def processar_mensagem(texto):
    agora = datetime.now(tz).strftime("%H:%M")
    if "pix" in texto:
        valor = extrair_valor(texto)
        if valor:
            taxa = valor * TAXA_PIX
            liquido = valor - taxa
            comprovantes.append({"valor": valor, "tipo": "PIX", "pago": False, "hora": agora})
            return f"""📄 Comprovante analisado:
💰 Valor bruto: {formatar(valor)}
💰 Tipo: PIX
⏰ Horário: {agora}
📉 Taxa aplicada: 0.2%
✅ Valor líquido a pagar: {formatar(liquido)}"""
    elif "x" in texto:
        try:
            partes = texto.lower().split("x")
            valor = extrair_valor(partes[0])
            parcelas = int(partes[1].strip())
            taxa = TAXAS_CARTAO.get(parcelas, 0)
            liquido = valor * (1 - taxa / 100)
            comprovantes.append({"valor": valor, "tipo": f"{parcelas}x", "pago": False, "hora": agora})
            return f"""📄 Comprovante analisado:
💰 Valor bruto: {formatar(valor)}
💰 Tipo: Cartão ({parcelas}x)
⏰ Horário: {agora}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: {formatar(liquido)}"""
        except:
            return "❌ Erro ao calcular parcelas."
    return "❌ Comando inválido ou valor não reconhecido."

def marcar_como_pago(texto):
    if "pagamento feito" not in texto:
        return "❌ Comando inválido."

    valor = extrair_valor(texto)
    total = valor if valor else None

    for c in comprovantes:
        if not c["pago"]:
            taxa = TAXA_PIX * c["valor"] if c["tipo"] == "PIX" else TAXAS_CARTAO.get(int(c["tipo"].replace("x", "")), 0) / 100 * c["valor"]
            liquido = c["valor"] - taxa
            if total is None or total >= liquido:
                c["pago"] = True
                if total:
                    total -= liquido
            elif total < liquido:
                c["valor"] = total / (1 - (TAXA_PIX if c["tipo"] == "PIX" else TAXAS_CARTAO.get(int(c["tipo"].replace("x", "")), 0) / 100))
                c["pago"] = True
                break
    return "✅ Pagamento registrado com sucesso."

def quanto_devo():
    total = 0
    for c in comprovantes:
        if not c["pago"]:
            taxa = TAXA_PIX * c["valor"] if c["tipo"] == "PIX" else TAXAS_CARTAO.get(int(c["tipo"].replace("x", "")), 0) / 100 * c["valor"]
            liquido = c["valor"] - taxa
            total += liquido
    return f"💰 Devo ao lojista: {formatar(total)}"

def total_a_pagar():
    total = sum(c["valor"] for c in comprovantes if not c["pago"])
    return f"💰 Total bruto pendente: {formatar(total)}"

def listar_pendentes():
    if not comprovantes:
        return "📂 Nenhum comprovante registrado."
    texto = "📋 Comprovantes pendentes:\n"
    for c in comprovantes:
        if not c["pago"]:
            texto += f"- {formatar(c['valor'])} | {c['tipo']} | {c['hora']}\n"
    return texto.strip()

def listar_pagamentos():
    texto = "✅ Comprovantes pagos:\n"
    for c in comprovantes:
        if c["pago"]:
            texto += f"- {formatar(c['valor'])} | {c['tipo']} | {c['hora']}\n"
    return texto if texto.strip() != "✅ Comprovantes pagos:" else "📂 Nenhum comprovante pago ainda."

def solicitar_pagamento(bot, message):
    bot.send_message(chat_id=message.chat.id, text="Digite o valor que deseja solicitar (ex: 300,00):")

    def esperar_valor(update, context):
        valor = extrair_valor(update.message.text)
        if not valor:
            bot.send_message(chat_id=message.chat.id, text="Valor inválido.")
            return

        solicitacoes.append({"usuario": message.from_user.id, "valor": valor})
        bot.send_message(chat_id=message.chat.id, text="Agora envie a chave PIX para recebimento:")

        def esperar_chave(update2, context2):
            chave = update2.message.text.strip()
            bot.send_message(chat_id=message.chat.id,
                             text=f"📬 Pagamento solicitado!\n💸 Valor: {formatar(valor)}\n🔑 Chave PIX: {chave}\n\nQuando receber, digite:\n💳 pagamento feito {formatar(valor)}")

        return esperar_chave

    return "🕐 Aguardando valor para solicitação de pagamento..."

def limpar_dados():
    comprovantes.clear()
    return "🧹 Todos os dados foram apagados!"

def corrigir_valor_comprovante(texto):
    try:
        novo_valor = extrair_valor(texto)
        for c in comprovantes:
            if not c["pago"]:
                c["valor"] = novo_valor
                return f"✏️ Valor corrigido para {formatar(novo_valor)}"
        return "❌ Nenhum comprovante pendente para corrigir."
    except:
        return "❌ Erro ao corrigir valor."

def exibir_ajuda():
    return """🛠 Comandos disponíveis:

• Enviar comprovante: Ex: 1.234,56 pix ou 2.345,00 10x
• pagamento feito [valor] – marca pagamento total ou parcial
• quanto devo – mostra valor líquido com taxas
• total a pagar – mostra total bruto pendente
• listar pendentes – lista comprovantes pendentes
• listar pagos – lista comprovantes pagos
• solicitar pagamento – lojista solicita pagamento com chave Pix
• ajuda – mostra esta lista

🔐 Comandos de admin:
• limpar tudo – apaga todos os dados
• corrigir valor [novo valor] – altera o valor do próximo pendente
"""
