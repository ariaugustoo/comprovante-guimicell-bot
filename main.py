import os
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters
from flask import Flask, request
from processador import processar_mensagem
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Inicializa bot e Flask
bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0)

# Handler principal
def registrar_handlers():
    def handler(update, context):
        processar_mensagem(update, context)

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handler))
    dispatcher.add_handler(MessageHandler(Filters.command, handler))

registrar_handlers()

# Endpoint raiz (para testes)
@app.route('/')
def index():
    return 'Bot de comprovantes rodando!'

# Endpoint do webhook
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)  # ✅ Dispara o handler automaticamente com contexto
        return 'ok'
    return 'Method Not Allowed', 405

# Start Flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
