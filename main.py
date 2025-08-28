import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import processar_mensagem

# Variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = os.getenv("ADMIN_ID")

# Inicializar bot e app Flask
bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# Dispatcher para lidar com mensagens
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

# Handler de mensagens
def handle_message(update, context):
    mensagem = update.message
    texto_resposta = processar_mensagem(mensagem)
    if texto_resposta:
        context.bot.send_message(chat_id=mensagem.chat_id, text=texto_resposta)

dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_message))

# Rota principal do webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

# Rota padrão
@app.route('/')
def index():
    return "Bot de comprovantes DBH / Guimicell ativo."

# Inicialização local (Render ignora, mas mantém compatibilidade)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
