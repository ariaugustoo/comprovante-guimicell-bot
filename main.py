import os
import re
from flask import Flask, request
from telegram import Bot
from telegram.utils.request import Request
from processador import (
    processar_mensagem,
    registrar_pagamento,
    total_liquido_pendentes,
    solicitar_pagamento_manual,
    listar_comprovantes_pendentes,
    listar_comprovantes_pagos
)

# Variáveis de ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Inicialização do bot e Flask
app = Flask(__name__)
bot = Bot(token=TOKEN, request=Request(con_pool_size=8))

@app.route('/')
def home():
    return 'Bot de comprovantes está ativo!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = request.get_json()

        try:
            message = update.get("message", {})
            text = message.get("text", "")
            user_id = message.get("from", {}).get("id")
            username = message.get("from", {}).get("username", "usuário")

            print(f"Mensagem recebida de @{username} ({user_id}): {text}")

            if not text:
                return 'OK'

            text = text.strip().lower()

            if "pix" in text or "x" in text:
                resposta = processar_mensagem(text)
                if resposta:
                    bot.send_message(chat_id=GROUP_ID, text=resposta, parse_mode='HTML')

            elif text == "pagamento feito":
                resposta = registrar_pagamento()
                bot.send_message(chat_id=GROUP_ID, text=resposta, parse_mode='HTML')

            elif text == "total líquido":
                resposta = total_liquido_pendentes()
                bot.send_message(chat_id=GROUP_ID, text=resposta, parse_mode='HTML')

            elif text == "solicitar pagamento":
                resposta = solicitar_pagamento_manual()
                bot.send_message(chat_id=GROUP_ID, text=resposta, parse_mode='HTML')

            elif text == "listar pendentes":
                resposta = listar_comprovantes_pendentes()
                bot.send_message(chat_id=GROUP_ID, text=resposta, parse_mode='HTML')

            elif text == "listar pagos":
                resposta = listar_comprovantes_pagos()
                bot.send_message(chat_id=GROUP_ID, text=resposta, parse_mode='HTML')

            elif text == "ajuda":
                ajuda_texto = (
                    "*Comandos disponíveis:*\n\n"
                    "1. 2200 pix\n"
                    "2. 5100 10x\n"
                    "3. Pagamento feito\n"
                    "4. Solicitar pagamento\n"
                    "5. Total líquido\n"
                    "6. Listar pendentes\n"
                    "7. Listar pagos\n\n"
                    "*O bot responde automaticamente com o valor líquido já calculado.*"
                )
                bot.send_message(chat_id=GROUP_ID, text=ajuda_texto, parse_mode="Markdown")

            elif text == "/limpar tudo":
                if user_id == ADMIN_ID:
                    from processador import limpar_tudo
                    resposta = limpar_tudo()
                    bot.send_message(chat_id=GROUP_ID, text=resposta)
                else:
                    bot.send_message(chat_id=GROUP_ID, text="Comando restrito ao administrador.")

            else:
                print("Mensagem ignorada:", text)

        except Exception as e:
            print("ERRO no webhook:", str(e))

    return 'OK'
