from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from processador import processar_mensagem
import os

TOKEN = '8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA'
GROUP_ID = -1002626449000
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f'https://comprovante-guimicell-bot-vmvr.onrender.com{WEBHOOK_PATH}'

app = Flask(__name__)
bot_app = Application.builder().token(TOKEN).build()

# Comandos
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Comandos disponíveis:\n"
        "- Envie o valor + 'pix' (ex: `1000,00 pix`)\n"
        "- Envie o valor + parcelas (ex: `1000,00 10x`)\n"
        "- ✅ marca comprovante como pago\n"
        "- 'total que devo'\n"
        "- 'listar pendentes'\n"
        "- 'listar pagos'\n"
        "- 'último comprovante'\n"
        "- 'total geral'"
    )

bot_app.add_handler(CommandHandler("ajuda", ajuda))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        bot_app.update_queue.put(update)
        return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot do Comprovante está rodando!", 200

if __name__ == "__main__":
    bot_app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL,
        webhook_path=WEBHOOK_PATH,
    )
