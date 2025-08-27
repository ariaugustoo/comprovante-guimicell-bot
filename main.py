from flask import Flask, request
import os
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from apscheduler.schedulers.background import BackgroundScheduler
from processador import (
    processar_mensagem,
    listar_pendentes,
    listar_pagamentos,
    limpar_tudo,
    corrigir_valor,
    resumo_total,
    comando_ajuda,
    ultimo_comprovante,
    total_que_devo,
    total_geral
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# Comandos
dispatcher.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("🤖 Bot ativo!")))
dispatcher.add_handler(CommandHandler("ajuda", comando_ajuda))
dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
dispatcher.add_handler(CommandHandler("listar_pagamentos", listar_pagamentos))
dispatcher.add_handler(CommandHandler("total_que_devo", total_que_devo))
dispatcher.add_handler(CommandHandler("total_geral", total_geral))
dispatcher.add_handler(CommandHandler("último_comprovante", ultimo_comprovante))
dispatcher.add_handler(CommandHandler("resumo_total", resumo_total))
dispatcher.add_handler(CommandHandler("limpar_tudo", limpar_tudo))
dispatcher.add_handler(CommandHandler("corrigir_valor", corrigir_valor))

# Mensagens e imagens
dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo, processar_mensagem))

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

# Tarefa agendada para resumo a cada hora
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: resumo_total(None, None, bot=bot, chat_id=GROUP_ID), 'interval', hours=1)
scheduler.start()

if __name__ == '__main__':
    app.run(port=5000)
