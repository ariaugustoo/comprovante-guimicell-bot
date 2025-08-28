import os
from flask import Flask, request
import telegram
from processador import processar_mensagem

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

bot = telegram.Bot(token=TELEGRAM_TOKEN)

@app.route('/')
def index():
    return "Bot está rodando! ✅"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            update = telegram.Update.de_json(request.get_json(force=True), bot)
            chat_id = update.message.chat.id
            user_message = update.message.text.strip()

            # Só processa mensagens do grupo certo
            if str(chat_id) == str(GROUP_ID):
                resposta = processar_mensagem(user_message)
                if resposta:
                    bot.send_message(chat_id=chat_id, text=resposta)
        except Exception as e:
            print(f"Erro no webhook: {e}")
        return 'ok'

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=10000)
