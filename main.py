import os
from flask import Flask, request
from processador import processar_mensagem, comando_total_liquido, comando_total_bruto, marcar_como_pago
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot está rodando com sucesso!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]
        message_text = data["message"].get("text", "").strip()

        if message_text:
            texto = message_text.lower()
            if texto == "pagamento feito":
                return marcar_como_pago(chat_id)
            elif texto == "total líquido":
                return comando_total_liquido(chat_id)
            elif texto == "total a pagar":
                return comando_total_bruto(chat_id)
            else:
                return processar_mensagem(chat_id, message_text)

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
