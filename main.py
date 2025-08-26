import telebot
from flask import Flask, request
from processador import processar_mensagem

TOKEN = '8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg80IA'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    return 'ok', 200

@bot.message_handler(content_types=['text', 'photo', 'document'])
def receber_mensagem(mensagem):
    processar_mensagem(bot, mensagem)

if __name__ == '__main__':
    import os
    import logging

    logger = telebot.logger
    telebot.logger.setLevel(logging.INFO)

    bot.remove_webhook()
    bot.set_webhook(url='https://comprovante-guimicell-bot.onrender.com/')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
