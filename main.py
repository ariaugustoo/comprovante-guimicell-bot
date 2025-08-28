import os
import logging
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import (
    processar_mensagem,
    registrar_pagamento,
    total_liquido_pendentes,
    listar_comprovantes_pendentes,
    listar_comprovantes_pagos,
    solicitar_pagamento_manual,
    limpar_tudo
)

# Configurações básicas
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Inicializa o dispatcher para tratar mensagens
dispatcher = Dispatcher(bot, None, workers=0)

def responder(update, context):
    texto = update.message.text.strip().lower()

    if texto == "pagamento feito":
        resposta = registrar_pagamento()

    elif texto == "total líquido":
        resposta = total_liquido_pendentes()

    elif texto == "total a pagar":
        resposta = total_liquido_pendentes()

    elif texto == "listar pendentes":
        resposta = listar_comprovantes_pendentes()

    elif texto == "listar pagos":
        resposta = listar_comprovantes_pagos()

    elif texto == "solicitar pagamento":
        resposta = solicitar_pagamento_manual()

    elif texto == "limpar tudo" and update.effective_user.id == ADMIN_ID:
        resposta = limpar_tudo()

    else:
        resposta = processar_mensagem(texto)

    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

# Rota principal
@app.route("/")
def index():
    return "Bot rodando com sucesso!"

# Rota do webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Registra os handlers
def registrar_handlers():
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, responder))

registrar_handlers()

# Executa o app (modo webhook)
if __name__ == "__main__":
    app.run(port=10000, debug=True)
