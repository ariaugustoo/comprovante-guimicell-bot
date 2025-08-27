import os
import logging
from flask import Flask, request
from processador import processar_mensagem
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" in update:
        message = update["message"]
        processar_mensagem(message)
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Bot rodando com sucesso via webhook!"

if __name__ == "__main__":
    app.run()
