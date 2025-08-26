import os
import logging
from flask import Flask, request
import telegram
from processador import processar_mensagem

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002626449000

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# Ativa logs para debug
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

@app.route("/")
def home():
    return "Bot está rodando com webhook!", 200

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        if update.message:
            processar_mensagem(bot, update.message)
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
