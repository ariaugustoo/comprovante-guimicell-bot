import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem

# ✅ Configurações
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID", "-1000000000000"))  # Substitua pelo seu ID
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))       # Substitua pelo seu ID

# ✅ Inicia bot
bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# ✅ Logging para depuração
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ✅ Função chamada quando o bot receber uma nova mensagem
def handle_message(update, context):
    try:
        processar_mensagem(update)
    except Exception as e:
        logging.error(f"Erro ao processar mensagem: {e}")
        update.message.reply_text("❌ Erro ao processar a mensagem. Tente novamente.")

# ✅ Registrar handler
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_message))

# ✅ Rota para o webhook
@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "OK", 200

# ✅ Rota para testar se o bot está vivo
@app.route("/")
def index():
    return "🤖 Bot de comprovantes está ativo!", 200

# ✅ Roda o app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
