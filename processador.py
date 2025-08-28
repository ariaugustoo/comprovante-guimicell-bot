import os
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import (
    registrar_pagamento,
    marcar_como_pago,
    listar_pendentes,
    listar_pagos,
    total_liquido,
    total_a_pagar,
    ajuda_comandos,
    solicitar_pagamento
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

dispatcher = Dispatcher(bot, None, workers=1, use_context=True)

def resposta_automatica(update, context):
    mensagem = update.message.text.lower()

    if "pix" in mensagem:
        valor = mensagem.replace("pix", "").strip()
        resposta = registrar_pagamento(valor, "PIX")
        update.message.reply_text(resposta)
    elif "x" in mensagem:
        try:
            partes = mensagem.split("x")
            valor = partes[0].strip()
            parcelas = int(partes[1].strip())
            resposta = registrar_pagamento(valor, "CARTAO", parcelas)
            update.message.reply_text(resposta)
        except:
            update.message.reply_text("❌ Formato inválido. Tente: 3000 6x")
    elif "pagamento feito" in mensagem:
        update.message.reply_text(marcar_como_pago())
    elif "listar pendentes" in mensagem:
        update.message.reply_text(listar_pendentes())
    elif "listar pagos" in mensagem:
        update.message.reply_text(listar_pagos())
    elif "total líquido" in mensagem:
        update.message.reply_text(total_liquido())
    elif "total a pagar" in mensagem:
        update.message.reply_text(total_a_pagar())
    elif "ajuda" in mensagem:
        update.message.reply_text(ajuda_comandos())
    elif "solicitar pagamento" in mensagem:
        update.message.reply_text("✍️ Envie o valor do pagamento recebido. Ex: 1000,00")
    elif "," in mensagem or "." in mensagem:
        # Caso o lojista tenha enviado o valor manual depois de "solicitar pagamento"
        resposta = solicitar_pagamento(mensagem)
        update.message.reply_text(resposta)

handler = MessageHandler(Filters.text & (~Filters.command), resposta_automatica)
dispatcher.add_handler(handler)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot rodando com sucesso!'

if __name__ == '__main__':
    app.run(debug=True, port=10000)
