import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    listar_pendentes,
    limpar_tudo,
    corrigir_valor,
    resumo_total
)
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN)

dispatcher = Dispatcher(bot, None, workers=0)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="🤖 Bot ativo e funcionando!")

def ajuda(update, context):
    comandos = """
📋 *Comandos disponíveis:*

1. `123,45 pix` – Registra pagamento PIX
2. `123,45 3x` – Registra cartão em 3 parcelas
3. ✅ – Marca último comprovante como pago
4. `total que devo` – Total pendente
5. `listar pendentes` – Lista comprovantes pendentes
6. `listar pagos` – Lista comprovantes pagos
7. `último comprovante` – Mostra o último enviado
8. `total geral` – Total geral (pagos + pendentes)
9. `ajuda` – Lista de comandos

*Comandos administrativos (somente admin):*
- `/limpar tudo` – Apaga todos os registros
- `/corrigir valor` – Corrige valor do último comprovante
"""
    context.bot.send_message(chat_id=update.effective_chat.id, text=comandos, parse_mode="Markdown")

def resumo_automatico():
    texto_resumo = resumo_total()
    bot.send_message(chat_id=GROUP_ID, text=texto_resumo)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(CommandHandler("limpar", limpar_tudo))
dispatcher.add_handler(CommandHandler("corrigir", corrigir_valor))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), processar_mensagem))
dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))

scheduler = BackgroundScheduler()
scheduler.add_job(resumo_automatico, 'interval', hours=1)
scheduler.start()

@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

if __name__ == "__main__":
    app.run()
