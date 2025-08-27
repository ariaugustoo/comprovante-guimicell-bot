import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from processador import processar_mensagem, listar_pendentes, listar_pagamentos, limpar_tudo, corrigir_valor, resumo_total
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# Define o fuso horário de Brasília
tz_brasilia = timezone("America/Sao_Paulo")

# Comandos básicos
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="🤖 Bot de comprovantes ativado!")

def ajuda(update, context):
    comandos = """
📋 *Comandos disponíveis:*

1. `123,45 pix` – Aplica taxa de 0,2%
2. `1234,56 3x` – Aplica taxa conforme parcelas
3. `✅` – Marca como pago o último comprovante
4. `total que devo` – Mostra total pendente
5. `listar pendentes` – Lista comprovantes pendentes
6. `listar pagos` – Lista comprovantes pagos
7. `último comprovante` – Exibe o último enviado
8. `total geral` – Mostra total pago + pendente

🔒 *Apenas administrador:*
- `/limpar_tudo`
- `/corrigir_valor [ID] [NOVO_VALOR]`
"""
    context.bot.send_message(chat_id=update.effective_chat.id, text=comandos, parse_mode="Markdown")

def limpar_tudo_cmd(update, context):
    if update.effective_user.id == ADMIN_ID:
        limpar_tudo()
        context.bot.send_message(chat_id=update.effective_chat.id, text="🧹 Todos os comprovantes foram apagados.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Você não tem permissão para isso.")

def corrigir_valor_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Você não tem permissão para isso.")
        return
    try:
        id_corrigir = int(context.args[0])
        novo_valor = float(str(context.args[1]).replace(",", "."))
        sucesso = corrigir_valor(id_corrigir, novo_valor)
        if sucesso:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Valor corrigido com sucesso.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ ID não encontrado.")
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Use o formato: /corrigir_valor [ID] [VALOR]")

# Agendador de resumo automático a cada 1 hora
def enviar_resumo_automatico():
    texto = resumo_total()
    bot.send_message(chat_id=GROUP_ID, text=texto)

scheduler = BackgroundScheduler(timezone=tz_brasilia)
scheduler.add_job(enviar_resumo_automatico, 'interval', hours=1)
scheduler.start()

# Rota do webhook (responde ao Telegram)
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "OK", 200

# Comandos e mensagens
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(CommandHandler("limpar_tudo", limpar_tudo_cmd))
dispatcher.add_handler(CommandHandler("corrigir_valor", corrigir_valor_cmd, pass_args=True))
dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.document.category("image/"), processar_mensagem))

# Rota raiz (GET)
@app.route("/", methods=["GET"])
def home():
    return "Bot de Comprovantes ativo!", 200
