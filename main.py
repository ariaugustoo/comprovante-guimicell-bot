import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    marcar_como_pago,
    listar_pendentes,
    listar_pagamentos,
    solicitar_pagamento,
    mostrar_ajuda,
    limpar_dados,
    corrigir_valor,
    quanto_devo,
    total_a_pagar
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0)

# Handlers de texto
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar_mensagem))

# Comandos
dispatcher.add_handler(CommandHandler("pagamento_feito", marcar_como_pago))
dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
dispatcher.add_handler(CommandHandler("listar_pagos", listar_pagamentos))
dispatcher.add_handler(CommandHandler("solicitar_pagamento", solicitar_pagamento))
dispatcher.add_handler(CommandHandler("ajuda", mostrar_ajuda))
dispatcher.add_handler(CommandHandler("limpar_tudo", limpar_dados))
dispatcher.add_handler(CommandHandler("corrigir_valor", corrigir_valor))
dispatcher.add_handler(CommandHandler("quanto_devo", quanto_devo))
dispatcher.add_handler(CommandHandler("total_a_pagar", total_a_pagar))

@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
