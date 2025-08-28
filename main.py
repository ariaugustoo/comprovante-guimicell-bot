import os
from flask import Flask, request
import telegram
from processador import (
    processar_mensagem,
    registrar_pagamento,
    listar_pendentes,
    listar_pagos,
    total_liquido_pendente,
    total_bruto_pendente
)

# Carregando variáveis de ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot Comprovantes DBH - ONLINE ✅'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        if update.message:
            texto = update.message.text
            chat_id = update.message.chat.id

            if not texto:
                return "OK"

            texto = texto.strip().lower()

            if texto == "ajuda":
                resposta = (
                    "📌 *Comandos disponíveis:*\n\n"
                    "• Enviar valor + pix (ex: `1234,56 pix`)\n"
                    "• Enviar valor + parcelas (ex: `1234,56 3x`)\n"
                    "• `pagamento feito` – marcar 1 como pago\n"
                    "• `listar pendentes` – listar comprovantes pendentes\n"
                    "• `listar pagos` – listar comprovantes pagos\n"
                    "• `total líquido` – valor líquido ainda a pagar\n"
                    "• `total a pagar` – valor bruto pendente"
                )
            elif texto == "pagamento feito":
                resposta = registrar_pagamento()
            elif texto == "listar pendentes":
                resposta = listar_pendentes()
            elif texto == "listar pagos":
                resposta = listar_pagos()
            elif texto == "total líquido":
                resposta = total_liquido_pendente()
            elif texto == "total a pagar":
                resposta = total_bruto_pendente()
            else:
                resposta = processar_mensagem(texto)

            bot.send_message(chat_id=chat_id, text=resposta, parse_mode=telegram.ParseMode.MARKDOWN)

        return 'OK'
