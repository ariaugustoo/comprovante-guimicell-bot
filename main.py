import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import processar_mensagem, listar_pendentes, listar_pagamentos_feitos, solicitar_pagamento, limpar_tudo, corrigir_valor

# Configurações iniciais
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)

# Inicializa o Flask
app = Flask(__name__)

# Dispatcher do Telegram
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Webhook para receber atualizações
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

# Manipuladores de comando
def ajuda(update, context):
    comandos = """
📋 *Comandos disponíveis:*
• Enviar valor com "pix" ou "parcelas" (ex: 1234,56 pix ou 1999,99 6x)
• pagamento feito – marca o último como pago ou abate parcial
• quanto devo – valor líquido a pagar com taxas
• total a pagar – valor bruto pendente
• listar pendentes – lista os comprovantes abertos
• listar pagos – lista os comprovantes quitados
• solicitar pagamento – lojista solicita valor + chave Pix
• limpar tudo – ⚠️ Admin zera todos os dados
• corrigir valor – ⚠️ Admin ajusta valor do último comprovante
"""
    update.message.reply_text(comandos, parse_mode="Markdown")

def registrar_handlers():
    dispatcher.add_handler(CommandHandler("ajuda", ajuda))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^ajuda$'), ajuda))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^listar pendentes$'), listar_pendentes))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^listar pagos$'), listar_pagamentos_feitos))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^solicitar pagamento$'), solicitar_pagamento))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^limpar tudo$'), limpar_tudo))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^corrigir valor$'), corrigir_valor))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar_mensagem))

registrar_handlers()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
