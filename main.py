import os
from flask import Flask, request
import telegram
from telegram import Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    normalizar_valor, registrar_comprovante, marcar_como_pago,
    resumo_status, comprovantes, calcular_valor_liquido
)

app = Flask(__name__)

bot = telegram.Bot(token=os.environ["TELEGRAM_TOKEN"])
GROUP_ID = int(os.environ["GROUP_ID"])
ADMIN_ID = int(os.environ["ADMIN_ID"])

dispatcher = Dispatcher(bot, None, use_context=True)

def enviar(msg):
    bot.send_message(chat_id=GROUP_ID, text=msg)

def start(update, context):
    update.message.reply_text("🤖 Bot ativo! Envie valores como: 1000 pix ou 3500 10x")

def ajuda(update, context):
    comandos = (
        "📌 *Comandos Disponíveis:*\n\n"
        "💰 Enviar valor: `1000 pix` ou `2500 3x`\n"
        "✅ `pagamento feito`\n"
        "📉 `quanto devo`\n"
        "📊 `total a pagar`\n"
        "🧾 `listar pendentes`\n"
        "🧾 `listar pagos`\n"
        "📬 `solicitar pagamento`\n"
        "📅 `fechamento do dia`\n"
        "📋 `/status`"
    )
    update.message.reply_text(comandos, parse_mode='Markdown')

def pagamento_feito(update, context):
    marcar_como_pago()
    update.message.reply_text("✅ Pagamento registrado com sucesso! Obrigado!")

def quanto_devo(update, context):
    pendente = sum(c["liquido"] for c in comprovantes if not c["pago"])
    update.message.reply_text(f"💰 *Devo ao lojista:* R$ {pendente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), parse_mode='Markdown')

def total_a_pagar(update, context):
    total = sum(c["valor"] for c in comprovantes if not c["pago"])
    update.message.reply_text(f"📊 *Total bruto pendente:* R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), parse_mode='Markdown')

def listar_pendentes(update, context):
    if not any(not c["pago"] for c in comprovantes):
        update.message.reply_text("🎉 Nenhum pagamento pendente!")
        return
    msg = "🧾 *Comprovantes Pendentes:*\n\n"
    for i, c in enumerate(c for c in comprovantes if not c["pago"]):
        msg += f"{i+1}. 💰 R$ {c['valor']:,.2f} - {c['tipo'].upper()} - ⏰ {c['horario']}\n"
    update.message.reply_text(msg.replace(",", "X").replace(".", ",").replace("X", "."), parse_mode='Markdown')

def listar_pagos(update, context):
    if not any(c["pago"] for c in comprovantes):
        update.message.reply_text("📭 Nenhum pagamento foi registrado ainda.")
        return
    msg = "📬 *Comprovantes Pagos:*\n\n"
    for i, c in enumerate(c for c in comprovantes if c["pago"]):
        msg += f"{i+1}. 💸 R$ {c['valor']:,.2f} - {c['tipo'].upper()} - ⏰ {c['horario']}\n"
    update.message.reply_text(msg.replace(",", "X").replace(".", ",").replace("X", "."), parse_mode='Markdown')

def fechamento_do_dia(update, context):
    pix, cartao, pago, pendente = resumo_status()
    msg = (
        "📅 *Fechamento do Dia:*\n\n"
        f"💳 Total Cartão: R$ {cartao:,.2f}\n"
        f"💸 Total PIX: R$ {pix:,.2f}\n"
        f"✅ Total Pago: R$ {pago:,.2f}\n"
        f"📌 Total Pendente: R$ {pendente:,.2f}"
    )
    update.message.reply_text(msg.replace(",", "X").replace(".", ",").replace("X", "."), parse_mode='Markdown')

def status(update, context):
    fechamento_do_dia(update, context)

def solicitar_pagamento(update, context):
    update.message.reply_text("✏️ Digite o valor que deseja solicitar (ex: 300,00):")
    return

def tratar_mensagem(update, context):
    texto = update.message.text.lower()

    if texto.startswith("solicitar pagamento"):
        solicitar_pagamento(update, context)
        return

    if "pagamento feito" in texto:
        pagamento_feito(update, context)
        return

    if "quanto devo" in texto:
        quanto_devo(update, context)
        return

    if "total a pagar" in texto:
        total_a_pagar(update, context)
        return

    if "listar pendentes" in texto:
        listar_pendentes(update, context)
        return

    if "listar pagos" in texto:
        listar_pagos(update, context)
        return

    if "fechamento do dia" in texto:
        fechamento_do_dia(update, context)
        return

    if "/status" in texto:
        status(update, context)
        return

    partes = texto.replace("r$", "").split()
    if len(partes) >= 2:
        try:
            valor = normalizar_valor(partes[0])
            if "pix" in partes[1]:
                tipo = "pix"
                horario, taxa, liquido = registrar_comprovante(valor, tipo)
            elif "x" in partes[1]:
                tipo = "cartao"
                parcelas = int(partes[1].replace("x", ""))
                horario, taxa, liquido = registrar_comprovante(valor, tipo, parcelas)
            else:
                return
            update.message.reply_text(
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💳 Tipo: {tipo.upper()}\n"
                f"⏰ Horário: {horario}\n"
                f"📉 Taxa aplicada: {taxa:.2f}%\n"
                f"✅ Valor líquido a pagar: R$ {liquido:,.2f}\n\n"
                "🎯 Estamos quase quitando tudo! 😉"
                .replace(",", "X").replace(".", ",").replace("X", "."),
                parse_mode='Markdown'
            )
        except:
            update.message.reply_text("❌ Erro ao processar valor. Use formato: `1000 pix` ou `2500 10x`", parse_mode='Markdown')

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(CommandHandler("status", status))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, tratar_mensagem))

@app.route(f"/webhook", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
