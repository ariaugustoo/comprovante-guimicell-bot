import os
from flask import Flask, request
import telegram
from processador import processar_pagamento, calcular_total_liquido, calcular_total_bruto

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telegram.Bot(token=TELEGRAM_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot rodando com webhook!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id
        mensagem = update.message.text.strip().lower()

        if not mensagem:
            return 'ok'

        if mensagem.endswith("pix") or "x" in mensagem:
            resposta = processar_pagamento(mensagem)
            bot.send_message(chat_id=chat_id, text=resposta)
        
        elif mensagem == "pagamento feito":
            resposta = "✅ Comprovante marcado como pago!"
            bot.send_message(chat_id=chat_id, text=resposta)

        elif mensagem == "total liquido":
            resposta = calcular_total_liquido()
            bot.send_message(chat_id=chat_id, text=resposta)

        elif mensagem == "total a pagar":
            resposta = calcular_total_bruto()
            bot.send_message(chat_id=chat_id, text=resposta)

        else:
            bot.send_message(chat_id=chat_id, text="❓ Comando não reconhecido. Use: '7500 pix', '7990 10x', 'total liquido' ou 'total a pagar'.")

    return 'ok'
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
