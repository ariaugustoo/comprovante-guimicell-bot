import logging
from flask import Flask, request
from telegram import Bot, Update
from processador import processar_mensagem

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002122662652
WEBHOOK_URL = f"https://comprovante-guimicell-bot-vmvr.onrender.com/{TOKEN}"

bot = Bot(token=TOKEN)
app = Flask(__name__)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

@app.route('/')
def home():
    return '✅ Bot está rodando com webhook!', 200

@app.route(f"/{TOKEN}", methods=["POST"])
def receber_mensagem():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        if update.message:
            processar_mensagem(bot, update.message)
    except Exception as e:
        logging.error(f"Erro ao processar mensagem: {e}")
    return 'OK', 200

@app.before_first_request
def configurar_webhook():
    bot.delete_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    logging.info("Webhook configurado com sucesso.")

if __name__ == "__main__":
    app.run(debug=True)
