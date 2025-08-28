import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from processador import (
    processar_mensagem,
    marcar_como_pago,
    listar_pendentes,
    listar_pagamentos,
    ajuda,
    solicitar_pagamento,
    quanto_devo,
    total_a_pagar
)

# Configurações
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# Inicialização do Flask
app = Flask(__name__)

# Inicialização do Bot
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=1, use_context=True)

# Handlers de comandos
dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
dispatcher.add_handler(CommandHandler("listar_pagamentos", listar_pagamentos))
dispatcher.add_handler(CommandHandler("pagamento_feito", marcar_como_pago))
dispatcher.add_handler(CommandHandler("solicitar_pagamento", solicitar_pagamento))
dispatcher.add_handler(CommandHandler("quanto_devo", quanto_devo))
dispatcher.add_handler(CommandHandler("total_a_pagar", total_a_pagar))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar_mensagem))

# Rota de Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'OK', 200

# Home (opcional)
@app.route('/')
def home():
    return '✅ Bot DBH está online!', 200

# Execução no Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
