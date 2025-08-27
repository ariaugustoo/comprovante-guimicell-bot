from flask import Flask, request
from processador import processar_mensagem, enviar_resumo_automatico
import os
import telegram
import threading
import time
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)

comprovantes = []

def resumo_automatico():
    while True:
        time.sleep(3600)  # 1 hora
        resumo = enviar_resumo_automatico(comprovantes)
        if resumo:
            bot.send_message(chat_id=GROUP_ID, text=resumo)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if "message" in data:
        msg = data['message']
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']
        texto = msg.get('text', '')

        resposta = processar_mensagem(texto, comprovantes, user_id, ADMIN_ID)
        if resposta:
            bot.send_message(chat_id=chat_id, text=resposta)
    return 'ok'

if __name__ == '__main__':
    threading.Thread(target=resumo_automatico).start()
    app.run(host='0.0.0.0', port=10000)
