import os
import re
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import processar_mensagem, comandos_suporte
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

pendentes = []
pagos = []

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="🤖 Bot do Guimicell ativo!")

def ajuda(update, context):
    comandos = comandos_suporte()
    context.bot.send_message(chat_id=update.effective_chat.id, text=comandos)

def limpar_tudo(update, context):
    if update.effective_user.id == ADMIN_ID:
        pendentes.clear()
        pagos.clear()
        context.bot.send_message(chat_id=update.effective_chat.id, text="🧹 Todos os comprovantes foram apagados.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="🚫 Comando permitido apenas ao administrador.")

def listar_pendentes(update, context):
    if not pendentes:
        context.bot.send_message(chat_id=update.effective_chat.id, text="📂 Nenhum comprovante pendente.")
        return
    resposta = "📌 *Comprovantes Pendentes:*\n"
    for c in pendentes:
        resposta += f"{c['texto']}\n"
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode='Markdown')

def listar_pagos(update, context):
    if not pagos:
        context.bot.send_message(chat_id=update.effective_chat.id, text="📂 Nenhum comprovante marcado como pago.")
        return
    resposta = "✅ *Comprovantes Pagos:*\n"
    for c in pagos:
        resposta += f"{c['texto']}\n"
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode='Markdown')

def total_geral(update, context):
    total = sum(c["valor_liquido"] for c in pendentes + pagos)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"💰 *Total Geral:* R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), parse_mode='Markdown')

def total_que_devo(update, context):
    total = sum(c["valor_liquido"] for c in pendentes)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"📉 *Total a Pagar:* R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), parse_mode='Markdown')

def ultimo_comprovante(update, context):
    if pendentes:
        context.bot.send_message(chat_id=update.effective_chat.id, text="🕘 Último comprovante pendente:\n" + pendentes[-1]["texto"])
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="📭 Nenhum comprovante pendente.")

def marcar_como_pago(update, context):
    if pendentes:
        c = pendentes.pop()
        pagos.append(c)
        context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Comprovante marcado como pago:\n" + c["texto"])
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="📭 Nenhum comprovante para marcar como pago.")

def resumo_automatico():
    if pendentes:
        total = sum(c["valor_liquido"] for c in pendentes)
        texto = f"⏰ *Resumo Automático (a cada hora)*\nTotal a pagar: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        bot.send_message(chat_id=GROUP_ID, text=texto, parse_mode='Markdown')

def registrar_handlers():
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("ajuda", ajuda))
    dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
    dispatcher.add_handler(CommandHandler("listar_pagos", listar_pagos))
    dispatcher.add_handler(CommandHandler("total_que_devo", total_que_devo))
    dispatcher.add_handler(CommandHandler("total_geral", total_geral))
    dispatcher.add_handler(CommandHandler("último_comprovante", ultimo_comprovante))
    dispatcher.add_handler(CommandHandler("limpar_tudo", limpar_tudo))
    dispatcher.add_handler(CommandHandler("✅", marcar_como_pago))
    dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.document, lambda update, context: processar_mensagem(update, context, pendentes, pagos)))

registrar_handlers()

scheduler = BackgroundScheduler(timezone='America/Sao_Paulo')
scheduler.add_job(resumo_automatico, 'cron', minute=0)
scheduler.start()

@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "ok", 200

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
