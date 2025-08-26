import os
import telebot
from flask import Flask, request
from processador import processar_mensagem

API_TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg80IA"
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

GROUP_ID = -1002626449000

@bot.message_handler(content_types=['text', 'photo', 'document'])
def handle_message(message):
    if message.chat.id != GROUP_ID:
        return

    resposta = processar_mensagem(bot, message)
    if resposta:
        bot.send_message(GROUP_ID, resposta)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid request', 403

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url="https://seu-projeto-no-render.onrender.com/")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
