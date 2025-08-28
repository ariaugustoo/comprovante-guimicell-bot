import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from apscheduler.schedulers.background import BackgroundScheduler
from processador import (
    processar_mensagem,
    resumo_automatico,
    limpar_dados,
    corrigir_valor,
    listar_pendentes,
    listar_pagamentos,
    solicitar_pagamento,
    registrar_pagamento,
    quanto_devo,
    total_a_pagar,
    ajuda
)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

app = Flask(__name__)
bot = Bot(token=TOKEN)

dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# Handlers de comandos
def start(update, context): update.message.reply_text("Bot ativo.")
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(CommandHandler("limpar", limpar_dados))
dispatcher.add_handler(CommandHandler("corrigir", corrigir_valor))
dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
dispatcher.add_handler(CommandHandler("listar_pagamentos", listar_pagamentos))
dispatcher.add_handler(CommandHandler("solicitar_pagamento", solicitar_pagamento))
dispatcher.add_handler(CommandHandler("quanto_devo", quanto_devo))
dispatcher.add_handler(CommandHandler("total_a_pagar", total_a_pagar))
dispatcher.add_handler(CommandHandler("pagamento_feito", registrar_pagamento))

# Handler de mensagens gerais
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), processar_mensagem))

# Log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Resumo automático a cada hora
scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
scheduler.add_job(resumo_automatico, 'interval', hours=1)
scheduler.start()

@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
