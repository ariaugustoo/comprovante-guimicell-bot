import telebot
from processador import processar_mensagem
from flask import Flask, request

API_TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid request', 403

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    processar_mensagem(bot, message)

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://comprovante-guimicell-bot.onrender.com/')
    app.run(host='0.0.0.0', port=10000)
