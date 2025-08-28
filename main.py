from flask import Flask, request
import os
from processador import (
    processar_mensagem,
    marcar_como_pago,
    listar_pendentes,
    listar_pagos,
    mostrar_ajuda,
    solicitar_pagamento,
    total_liquido,
    total_bruto
)
import telegram

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
bot = telegram.Bot(token=TOKEN)

@app.route('/')
def home():
    return 'Bot DBH - Online ✅'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        message = update.message

        if message and message.text:
            texto = message.text.strip().lower()

            if 'pix' in texto or 'x' in texto:
                resposta = processar_mensagem(texto)
            elif texto == "pagamento feito":
                resposta = marcar_como_pago()
            elif texto == "listar pendentes":
                resposta = listar_pendentes()
            elif texto == "listar pagos":
                resposta = listar_pagos()
            elif texto == "ajuda":
                resposta = mostrar_ajuda()
            elif texto == "solicitar pagamento":
                resposta = solicitar_pagamento()
            elif texto == "total líquido":
                resposta = total_liquido()
            elif texto == "total a pagar":
                resposta = total_bruto()
            else:
                resposta = None

            if resposta:
                bot.send_message(chat_id=GROUP_ID, text=resposta)

        return 'ok', 200
