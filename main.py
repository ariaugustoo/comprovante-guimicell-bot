import os
from flask import Flask, request
import telegram
from processador import (
    processar_mensagem,
    marcar_como_pago,
    listar_pendentes,
    listar_pagamentos,
    solicitar_pagamento,
    limpar_dados,
    corrigir_valor_comprovante,
    quanto_devo,
    total_a_pagar,
    exibir_ajuda
)

TOKEN = os.environ["TELEGRAM_TOKEN"]
GROUP_ID = os.environ["GROUP_ID"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot de comprovantes ativo!'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    message = update.message

    if message and message.text:
        texto = message.text.lower()

        # Comandos administrativos protegidos
        if texto.startswith("limpar tudo") and message.from_user.id == ADMIN_ID:
            resposta = limpar_dados()
        elif texto.startswith("corrigir valor") and message.from_user.id == ADMIN_ID:
            resposta = corrigir_valor_comprovante(texto)
        elif texto.startswith("pagamento feito"):
            resposta = marcar_como_pago(texto)
        elif texto == "quanto devo":
            resposta = quanto_devo()
        elif texto == "total a pagar":
            resposta = total_a_pagar()
        elif texto == "listar pendentes":
            resposta = listar_pendentes()
        elif texto == "listar pagos":
            resposta = listar_pagamentos()
        elif texto == "solicitar pagamento":
            resposta = solicitar_pagamento(bot, message)
            return "OK"
        elif texto == "ajuda":
            resposta = exibir_ajuda()
        else:
            resposta = processar_mensagem(texto)

        bot.send_message(chat_id=message.chat.id, text=resposta)

    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
