import re
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import CallbackContext

# Armazenamento em memória
comprovantes = []
comprovantes_pagos = []

# Tabela de taxas por número de parcelas
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}
TAXA_PIX = 0.2

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def normalizar_valor(valor_str):
    valor_str = valor_str.replace(" ", "").replace("R$", "").replace(".", "").replace(",", ".")
    return float(valor_str)

def obter_horario_brasilia():
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_brasilia)

def calcular_valor_liquido(valor, taxa_percentual):
    return round(valor * (1 - taxa_percentual / 100), 2)

def processar_mensagem(update: Update, context: CallbackContext):
    texto = update.message.text.lower()
    chat_id = update.message.chat_id

    try:
        if "pix" in texto:
            valor = normalizar_valor(re.findall(r"[\d\.,]+", texto)[0])
            taxa = TAXA_PIX
            tipo = "PIX"
            parcelas = 1
        elif "x" in texto:
            valor = normalizar_valor(re.findall(r"[\d\.,]+", texto)[0])
            parcelas = int(re.findall(r"(\d{1,2})x", texto)[0])
            taxa = TAXAS_CARTAO.get(parcelas, 0)
            tipo = f"Cartão {parcelas}x"
        else:
            update.message.reply_text("❌ Formato inválido. Use algo como '1000 pix' ou '1500 6x'.")
            return

        valor_liquido = calcular_valor_liquido(valor, taxa)
        horario = obter_horario_brasilia().strftime("%H:%M")

        comprovante = {
            "bruto": valor,
            "tipo": tipo,
            "parcelas": parcelas,
            "taxa": taxa,
            "liquido": valor_liquido,
            "hora": horario,
            "pago": False
        }

        comprovantes.append(comprovante)

        resposta = (
            "📄 *Comprovante analisado:*\n"
            f"💰 *Valor bruto:* {formatar_valor(valor)}\n"
            f"💰 *Tipo:* {tipo}\n"
            f"⏰ *Horário:* {horario}\n"
            f"📉 *Taxa aplicada:* {taxa:.2f}%\n"
            f"✅ *Valor líquido a pagar:* {formatar_valor(valor_liquido)}"
        )
        update.message.reply_text(resposta, parse_mode='Markdown')

    except Exception as e:
        update.message.reply_text("❌ Erro ao processar valor. Verifique o formato e tente novamente.")

def marcar_como_pago(update: Update, context: CallbackContext):
    for c in comprovantes:
        if not c["pago"]:
            c["pago"] = True
            comprovantes_pagos.append(c)
    update.message.reply_text("✅ Comprovantes marcados como pagos!")

def total_liquido(update: Update, context: CallbackContext):
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    update.message.reply_text(f"💵 Total líquido pendente: *{formatar_valor(total)}*", parse_mode='Markdown')

def total_bruto(update: Update, context: CallbackContext):
    total = sum(c["bruto"] for c in comprovantes if not c["pago"])
    update.message.reply_text(f"💰 Total bruto dos comprovantes: *{formatar_valor(total)}*", parse_mode='Markdown')

def listar_pendentes(update: Update, context: CallbackContext):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        update.message.reply_text("✅ Nenhum comprovante pendente.")
        return
    resposta = "📋 *Comprovantes pendentes:*\n\n"
    total = 0
    for i, c in enumerate(pendentes, 1):
        resposta += (
            f"{i}. {c['tipo']} - {formatar_valor(c['bruto'])} ➡️ Líquido: {formatar_valor(c['liquido'])} às {c['hora']}\n"
        )
        total += c["liquido"]
    resposta += f"\n🔢 *Total líquido pendente:* {formatar_valor(total)}"
    update.message.reply_text(resposta, parse_mode='Markdown')

def listar_pagos(update: Update, context: CallbackContext):
    if not comprovantes_pagos:
        update.message.reply_text("⚠️ Nenhum comprovante foi marcado como pago ainda.")
        return
    resposta = "📗 *Comprovantes pagos:*\n\n"
    total = 0
    for i, c in enumerate(comprovantes_pagos, 1):
        resposta += (
            f"{i}. {c['tipo']} - {formatar_valor(c['bruto'])} ➡️ Líquido: {formatar_valor(c['liquido'])} às {c['hora']}\n"
        )
        total += c["liquido"]
    resposta += f"\n💰 *Total já pago:* {formatar_valor(total)}"
    update.message.reply_text(resposta, parse_mode='Markdown')

def solicitar_pagamento(update: Update, context: CallbackContext):
    texto = update.message.text.lower()
    numeros = re.findall(r"[\d\.,]+", texto)
    if not numeros:
        update.message.reply_text("❌ Envie o valor desejado. Ex: 'solicitar pagamento 500,00'")
        return

    valor_solicitado = normalizar_valor(numeros[0])
    saldo_pendente = sum(c["liquido"] for c in comprovantes if not c["pago"])

    if valor_solicitado > saldo_pendente:
        update.message.reply_text(f"❌ Valor solicitado maior que o disponível. Seu saldo líquido é {formatar_valor(saldo_pendente)}")
        return

    abatido = 0
    for c in comprovantes:
        if not c["pago"] and abatido < valor_solicitado:
            restante = valor_solicitado - abatido
            if c["liquido"] <= restante:
                c["pago"] = True
                comprovantes_pagos.append(c)
                abatido += c["liquido"]
            else:
                break

    update.message.reply_text(
        f"💸 Valor de {formatar_valor(valor_solicitado)} marcado como *solicitado/pago*.\n"
        f"🔁 Saldo restante a receber: {formatar_valor(saldo_pendente - valor_solicitado)}",
        parse_mode='Markdown'
    )

def ajuda(update: Update, context: CallbackContext):
    comandos = (
        "🤖 *Comandos disponíveis:*\n\n"
        "• `1000 pix` → Calcula valor líquido com taxa PIX\n"
        "• `1000 6x` → Calcula valor líquido com taxa de cartão 6x\n"
        "• `pagamento feito` → Marca todos os pendentes como pagos\n"
        "• `total líquido` → Mostra valor líquido pendente\n"
        "• `total a pagar` → Mostra valor bruto pendente\n"
        "• `listar pendentes` → Lista comprovantes não pagos\n"
        "• `listar pagos` → Lista comprovantes pagos\n"
        "• `solicitar pagamento 500,00` → Marca esse valor como pago"
    )
    update.message.reply_text(comandos, parse_mode='Markdown')

def enviar_resumo_automatico(bot, chat_id):
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    hora = obter_horario_brasilia().strftime("%H:%M")
    bot.send_message(chat_id=chat_id, text=f"🕐 {hora} – Total líquido pendente: {formatar_valor(total)}")
