from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import os
import re
from datetime import datetime
import pytz

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
comprovantes = []

# --- TAXAS ---
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}
TAXA_PIX = 0.2

def formatar(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def parse_valor(texto):
    valor_str = re.findall(r"[\d.,]+", texto)[0].replace(".", "").replace(",", ".")
    return float(valor_str)

def calcular_liquido(valor, forma_pagamento, parcelas=1):
    taxa = TAXA_PIX if forma_pagamento == "pix" else TAXAS_CARTAO.get(parcelas, 0)
    liquido = valor * (1 - taxa / 100)
    return round(liquido, 2), taxa

def is_admin(update):
    return update.effective_user.id == ADMIN_ID

def gerar_resumo():
    total_pago = sum(c["liquido"] for c in comprovantes if c["pago"])
    total_pendente = sum(c["liquido"] for c in comprovantes if not c["pago"])
    return (
        f"🧾 RESUMO AUTOMÁTICO:\n"
        f"✅ Pagos: {formatar(total_pago)}\n"
        f"💸 Pendentes: {formatar(total_pendente)}"
    )

def processar_mensagem(update, context):
    text = update.message.text.lower()

    if text == "✅":
        if comprovantes:
            comprovantes[-1]["pago"] = True
            update.message.reply_text("✅ Marcado como pago.")
        else:
            update.message.reply_text("Nenhum comprovante ainda.")
        return

    if text in ["total que devo", "total que eu devo"]:
        total = sum(c["liquido"] for c in comprovantes if not c["pago"])
        update.message.reply_text(f"💸 Você deve: {formatar(total)}")
        return

    if text == "listar pendentes":
        pendentes = [c for c in comprovantes if not c["pago"]]
        if pendentes:
            msg = "\n".join([f"{formatar(c['liquido'])}" for c in pendentes])
        else:
            msg = "🎉 Nenhum comprovante pendente!"
        update.message.reply_text(msg)
        return

    if text == "listar pagos":
        pagos = [c for c in comprovantes if c["pago"]]
        if pagos:
            msg = "\n".join([f"{formatar(c['liquido'])}" for c in pagos])
        else:
            msg = "Nenhum pago ainda."
        update.message.reply_text(msg)
        return

    if text == "último comprovante":
        if not comprovantes:
            update.message.reply_text("Nenhum comprovante ainda.")
            return
        c = comprovantes[-1]
        status = "✅ PAGO" if c["pago"] else "⏳ PENDENTE"
        msg = (
            f"📄 Último comprovante:\n"
            f"💰 Valor bruto: {formatar(c['bruto'])}\n"
            f"📉 Taxa: {c['taxa']}%\n"
            f"✅ Valor líquido: {formatar(c['liquido'])}\n"
            f"{status}"
        )
        update.message.reply_text(msg)
        return

    if text == "total geral":
        total = sum(c["liquido"] for c in comprovantes)
        update.message.reply_text(f"📊 Total geral: {formatar(total)}")
        return

    if text == "ajuda":
        comandos(update, context)
        return

    match_pix = re.match(r"^[\d.,]+\s*pix$", text)
    match_cartao = re.match(r"^[\d.,]+\s*\d{1,2}x$", text)

    if match_pix:
        valor = parse_valor(text)
        liquido, taxa = calcular_liquido(valor, "pix")
        comprovantes.append({"bruto": valor, "liquido": liquido, "taxa": taxa, "pago": False})
        hora = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%H:%M")
        msg = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: {formatar(valor)}\n"
            f"📉 Taxa aplicada: {taxa:.2f}%\n"
            f"✅ Valor líquido a pagar: {formatar(liquido)}\n"
            f"🕒 Horário: {hora}"
        )
        update.message.reply_text(msg)
        return

    if match_cartao:
        partes = text.split()
        valor = parse_valor(partes[0])
        parcelas = int(partes[1].replace("x", ""))
        liquido, taxa = calcular_liquido(valor, "cartao", parcelas)
        comprovantes.append({"bruto": valor, "liquido": liquido, "taxa": taxa, "pago": False})
        msg = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: {formatar(valor)}\n"
            f"💳 Parcelas: {parcelas}x\n"
            f"📉 Taxa aplicada: {taxa:.2f}%\n"
            f"✅ Valor líquido a pagar: {formatar(liquido)}"
        )
        update.message.reply_text(msg)
        return

def comandos(update, context):
    text = """
📌 *Comandos disponíveis:*
• Envie: `749,99 pix`
• Envie: `1.400,00 3x`
• ✅ → marca último como pago
• total que devo
• listar pendentes
• listar pagos
• último comprovante
• total geral
• ajuda

🔒 *Admin:*
/limpar
/corrigir 1234.56
"""
    update.message.reply_text(text, parse_mode=telegram.ParseMode.MARKDOWN)

def limpar(update, context):
    if not is_admin(update):
        return update.message.reply_text("🚫 Apenas o admin.")
    comprovantes.clear()
    update.message.reply_text("🧹 Comprovantes apagados.")

def corrigir(update, context):
    if not is_admin(update):
        return update.message.reply_text("🚫 Apenas o admin.")
    try:
        novo_valor = float(context.args[0])
        if comprovantes:
            comprovantes[-1]["bruto"] = novo_valor
            liquido, taxa = calcular_liquido(novo_valor, "pix")  # Supondo PIX por padrão
            comprovantes[-1]["liquido"] = liquido
            comprovantes[-1]["taxa"] = taxa
            update.message.reply_text("✏️ Valor corrigido.")
        else:
            update.message.reply_text("Nenhum comprovante.")
    except:
        update.message.reply_text("❗Use: /corrigir 1234.56")

# Scheduler automático
def resumo_agendado():
    if comprovantes:
        resumo = gerar_resumo()
        bot.send_message(chat_id=GROUP_ID, text=resumo)

scheduler = BackgroundScheduler()
scheduler.add_job(resumo_agendado, 'interval', hours=1)
scheduler.start()

# --- Flask routes ---
@app.route('/')
def index():
    return 'Bot ativo!'

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# --- Handlers ---
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar_mensagem))
dispatcher.add_handler(CommandHandler("ajuda", comandos))
dispatcher.add_handler(CommandHandler("limpar", limpar))
dispatcher.add_handler(CommandHandler("corrigir", corrigir, pass_args=True))

# --- Run ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


