import os
from flask import Flask, request
import telegram
from processador import (
    processar_mensagem,
    registrar_pagamento,
    total_liquido_pendente,
    total_bruto_pendente,
    listar_pendentes,
    listar_pagos
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message:
        processar_update(update.message)
    return 'ok'

def processar_update(message):
    texto = message.text.strip().lower()

    if texto.startswith("/start"):
        bot.send_message(chat_id=message.chat_id, text="🤖 Bot de comprovantes ativo!")
        return

    if texto == "ajuda":
        comandos = (
            "📌 *Comandos disponíveis:*\n\n"
            "💸 *Comprovante:* Ex: `1000 pix` ou `1500 6x`\n"
            "✅ *Pagamento feito* – marca o último como pago\n"
            "📋 *Listar pendentes* – mostra comprovantes ainda não pagos\n"
            "📬 *Listar pagos* – mostra comprovantes já pagos\n"
            "💵 *Total líquido* – total líquido de pagamentos a fazer\n"
            "💰 *Total a pagar* – valor bruto total dos comprovantes pendentes\n"
            "📲 *Solicitar pagamento* – digite por exemplo: `solicitar pagamento 700 chavepix@email.com`"
        )
        bot.send_message(chat_id=message.chat_id, text=comandos, parse_mode="Markdown")
        return

    if texto == "pagamento feito":
        resposta = registrar_pagamento()
        bot.send_message(chat_id=message.chat_id, text=resposta)
        return

    if texto == "listar pendentes":
        resposta = listar_pendentes()
        bot.send_message(chat_id=message.chat_id, text=resposta, parse_mode="Markdown")
        return

    if texto == "listar pagos":
        resposta = listar_pagos()
        bot.send_message(chat_id=message.chat_id, text=resposta, parse_mode="Markdown")
        return

    if texto == "total líquido":
        resposta = total_liquido_pendente()
        bot.send_message(chat_id=message.chat_id, text=resposta, parse_mode="Markdown")
        return

    if texto == "total a pagar":
        resposta = total_bruto_pendente()
        bot.send_message(chat_id=message.chat_id, text=resposta, parse_mode="Markdown")
        return

    if texto.startswith("solicitar pagamento"):
        partes = texto.split()
        if len(partes) == 3:
            valor = partes[2]
            chave = partes[2]
            resposta = f"📬 *Solicitação de Pagamento:*\n💵 Valor: {valor}\n🔑 Chave Pix: `{chave}`"
        elif len(partes) == 4:
            valor = partes[2]
            chave = partes[3]
            resposta = f"📬 *Solicitação de Pagamento:*\n💵 Valor: {valor}\n🔑 Chave Pix: `{chave}`"
        else:
            resposta = "❌ Formato inválido. Use: `solicitar pagamento 700 chavepix@email.com`"
        bot.send_message(chat_id=message.chat_id, text=resposta, parse_mode="Markdown")
        return

    # Tenta processar como comprovante
    resposta = processar_mensagem(texto)
    bot.send_message(chat_id=message.chat_id, text=resposta, parse_mode="Markdown")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
