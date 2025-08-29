import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    listar_pendentes,
    listar_pagamentos,
    solicitar_pagamento,
    marcar_pagamento,
    calcular_total_liquido,
    calcular_total_bruto,
    limpar_dados,
    corrigir_valor,
)
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import pytz
from datetime import datetime

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

dispatcher = Dispatcher(bot, None, workers=0)

# 🕐 Enviar resumo automático a cada hora
def enviar_resumo():
    texto = listar_pendentes()
    if texto:
        bot.send_message(chat_id=GROUP_ID, text=f"⏰ *Resumo automático de pendências:*\n\n{texto}", parse_mode='Markdown')

scheduler = BackgroundScheduler(timezone=pytz.timezone("America/Sao_Paulo"))
scheduler.add_job(enviar_resumo, "cron", minute=0)
scheduler.start()

# 📌 Rota para o Webhook
@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "OK"

# ✅ Handlers
def registrar_handlers():
    dispatcher.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("🤖 Bot ativo e pronto para uso!")))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar_mensagem))

    dispatcher.add_handler(CommandHandler("ajuda", lambda update, context: update.message.reply_text(
        "📋 *Comandos disponíveis:*\n\n"
        "• pagamento feito\n"
        "• quanto devo\n"
        "• total a pagar\n"
        "• listar pendentes\n"
        "• listar pagos\n"
        "• solicitar pagamento\n"
        "• limpar tudo (admin)\n"
        "• corrigir valor (admin)\n", parse_mode='Markdown')))

    dispatcher.add_handler(CommandHandler("listar_pendentes", lambda update, context: update.message.reply_text(listar_pendentes())))
    dispatcher.add_handler(CommandHandler("listar_pagos", lambda update, context: update.message.reply_text(listar_pagamentos())))
    dispatcher.add_handler(CommandHandler("solicitar_pagamento", solicitar_pagamento))
    dispatcher.add_handler(CommandHandler("pagamento_feito", marcar_pagamento))
    dispatcher.add_handler(CommandHandler("quanto_devo", lambda update, context: update.message.reply_text(f"💰 Devo ao lojista: R$ {calcular_total_liquido():.2f}")))
    dispatcher.add_handler(CommandHandler("total_a_pagar", lambda update, context: update.message.reply_text(f"💵 Total BRUTO dos comprovantes pendentes: R$ {calcular_total_bruto():.2f}")))

    dispatcher.add_handler(CommandHandler("limpar_tudo", limpar_dados))
    dispatcher.add_handler(CommandHandler("corrigir_valor", corrigir_valor))

registrar_handlers()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
