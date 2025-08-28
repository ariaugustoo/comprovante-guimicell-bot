import os
import re
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from processador import (
    processar_mensagem,
    marcar_como_pago,
    quanto_devo,
    total_a_pagar
)

load_dotenv()

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)


def registrar_handlers():
    def handle(update, context):
        if update.message.text:
            texto = update.message.text.lower()
            if "pagamento feito" in texto:
                resposta = marcar_como_pago()
                context.bot.send_message(chat_id=GROUP_ID, text=resposta)
            elif "quanto devo" in texto:
                resposta = quanto_devo()
                context.bot.send_message(chat_id=GROUP_ID, text=resposta)
            elif "total a pagar" in texto:
                resposta = total_a_pagar()
                context.bot.send_message(chat_id=GROUP_ID, text=resposta)
            else:
                resposta = processar_mensagem(update.message.text)
                context.bot.send_message(chat_id=GROUP_ID, text=resposta)

    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), handle))


@app.route(f"/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"


def resumo_automatico():
    resposta = quanto_devo()
    bot.send_message(chat_id=GROUP_ID, text=resposta)


registrar_handlers()

scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
scheduler.add_job(resumo_automatico, "interval", hours=1, id="resumo_automatico")
scheduler.start()

# 🔥 Linha necessária para o Render funcionar corretamente
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
