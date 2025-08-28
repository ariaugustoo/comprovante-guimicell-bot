import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
)
from processador import (
    processar_mensagem,
    marcar_como_pago,
    listar_pendentes,
    listar_pagamentos,
    solicitar_pagamento,
    total_a_pagar,
    total_pendentes,
)

from apscheduler.schedulers.background import BackgroundScheduler
from telegram.bot import Bot
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=1, use_context=True)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === COMANDOS ===

def ajuda(update, context):
    texto = (
        "🛠 *Comandos disponíveis:*\n\n"
        "1. `999 pix` → calcula repasse com taxa 0.2%\n"
        "2. `999 3x` → calcula repasse com taxa de cartão conforme parcelas\n"
        "3. `pagamento feito` → marca último pagamento como quitado\n"
        "4. `quanto devo` → mostra valor líquido total ainda a pagar\n"
        "5. `total a pagar` → mostra valor bruto pendente\n"
        "6. `listar pendentes` → lista comprovantes não pagos\n"
        "7. `listar pagos` → lista comprovantes quitados\n"
        "8. `solicitar pagamento` → permite lojista pedir valor manual\n"
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=texto, parse_mode='Markdown')

# === HANDLERS ===

dispatcher.add_handler(CommandHandler("start", ajuda))
dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^ajuda$"), ajuda))
dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^pagamento feito$"), marcar_como_pago))
dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^listar pendentes$"), listar_pendentes))
dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^listar pagos$"), listar_pagamentos))
dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^solicitar pagamento$"), solicitar_pagamento))
dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^quanto devo$"), total_pendentes))
dispatcher.add_handler(MessageHandler(Filters.regex("(?i)^total a pagar$"), total_a_pagar))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), processar_mensagem))

# === AGENDADOR PARA RESUMO AUTOMÁTICO ===

def resumo_automatico():
    from processador import enviar_resumo_automatico
    enviar_resumo_automatico(bot, GROUP_ID)

scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
scheduler.add_job(resumo_automatico, "cron", hour="*", minute=0)
scheduler.start()

# === WEBHOOK ===

@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot ativo!"

if __name__ == "__main__":
    app.run(port=10000)
