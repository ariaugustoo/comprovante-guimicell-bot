import os
import telebot
from flask import Flask, request
from processador import processar_comprovante, marcar_comprovante_como_pago, listar_comprovantes_pendentes, listar_comprovantes_pagos, calcular_total_pendente, obter_ultimo_comprovante, calcular_total_geral, exibir_ajuda

API_TOKEN = '8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA'
GROUP_ID = -1002122662652

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ✅ Remove webhook anterior e define novo (padrão para webhook)
bot.remove_webhook()
bot.set_webhook(url='https://comprovantes.onrender.com/' + API_TOKEN)

comprovantes = []

@bot.message_handler(content_types=['text'])
def handle_message(message):
    if message.chat.id != GROUP_ID:
        return

    texto = message.text.strip().lower()

    if texto.endswith("pix"):
        valor = texto.replace("pix", "").strip()
        resposta = processar_comprovante(valor, "pix")
        bot.reply_to(message, resposta)
        comprovantes.append({'msg': message, 'valor': valor, 'tipo': 'pix', 'pago': False})

    elif "x" in texto:
        valor, parcelas = texto.lower().split("x")[0].strip(), texto.lower().split("x")[1].strip()
        resposta = processar_comprovante(valor, f"{parcelas}x")
        bot.reply_to(message, resposta)
        comprovantes.append({'msg': message, 'valor': valor, 'tipo': f"{parcelas}x", 'pago': False})

    elif texto == "✅":
        resposta = marcar_comprovante_como_pago(comprovantes)
        bot.reply_to(message, resposta)

    elif texto == "listar pendentes":
        bot.reply_to(message, listar_comprovantes_pendentes(comprovantes))

    elif texto == "listar pagos":
        bot.reply_to(message, listar_comprovantes_pagos(comprovantes))

    elif texto == "total que devo":
        bot.reply_to(message, calcular_total_pendente(comprovantes))

    elif texto == "último comprovante":
        bot.reply_to(message, obter_ultimo_comprovante(comprovantes))

    elif texto == "total geral":
        bot.reply_to(message, calcular_total_geral(comprovantes))

    elif texto == "ajuda":
        bot.reply_to(message, exibir_ajuda())

@app.route('/' + API_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route('/')
def index():
    return "Bot rodando com webhook!", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
