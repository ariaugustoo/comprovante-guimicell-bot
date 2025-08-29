import os
from flask import Flask, request
import telegram
from processador import (
    processar_mensagem, listar_pendentes, listar_pagamentos, solicitar_pagamento,
    registrar_pagamento, mostrar_total_devido, mostrar_total_bruto, mostrar_status,
    mostrar_ajuda, limpar_dados, corrigir_valor
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return '✅ Bot de comprovantes está online no Render!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        mensagem = update.message.text.lower() if update.message and update.message.text else ""
        user_id = update.message.from_user.id if update.message else None
        chat_id = update.effective_chat.id if update.effective_chat else None

        if not mensagem:
            return 'ok'

        if mensagem == "listar pendentes":
            listar_pendentes(update, None)
        elif mensagem == "listar pagos":
            listar_pagamentos(update, None)
        elif mensagem == "solicitar pagamento":
            solicitar_pagamento(update, None)
        elif mensagem == "pagamento feito":
            registrar_pagamento(update, None)
        elif mensagem == "quanto devo":
            mostrar_total_devido(update, None)
        elif mensagem == "total a pagar":
            mostrar_total_bruto(update, None)
        elif mensagem in ["/status", "status", "fechamento do dia"]:
            mostrar_status(update, None)
        elif mensagem == "ajuda":
            mostrar_ajuda(update, None)
        elif mensagem == "limpar tudo" and user_id == ADMIN_ID:
            limpar_dados(update, None)
        elif mensagem == "corrigir valor" and user_id == ADMIN_ID:
            corrigir_valor(update, None)
        else:
            processar_mensagem(update, None)

        return 'ok'
    return 'method not allowed', 405

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
