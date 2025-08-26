import os
from flask import Flask, request
from processador import processar_mensagem

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_json()
        if data and 'message' in data:
            processar_mensagem(data['message'])
        return 'OK', 200

@app.route('/', methods=['GET'])
def home():
    return 'Bot de comprovantes está ativo!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
