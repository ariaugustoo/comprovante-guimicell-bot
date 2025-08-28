import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from telegram.ext import Updater
from processador import processar_mensagem, marcar_como_pago, listar_pendentes, listar_pagos, total_liquido, total_bruto, solicitar_pagamento, ajuda

# Variáveis de ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Inicializa bot e app Flask
bot = Bot(token=TOKEN)
app = Flask(__name__)

# Corrigido: usar Updater para evitar erro de workers
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Função principal para processar mensagens recebidas
def handle_message(update, context):
    message_text = update.message.text.lower()

    if message_text == "pagamento feito":
        resposta = marcar_como_pago()
    elif message_text == "total líquido":
        resposta = total_liquido()
    elif message_text == "total a pagar":
        resposta = total_bruto()
    elif message_text == "listar pendentes":
        resposta = listar_pendentes()
    elif message_text == "listar pagos":
        resposta = listar_pagos()
    elif message_text == "solicitar pagamento":
        resposta = solicitar_pagamento(context)
    elif message_text == "ajuda":
        resposta = ajuda()
    else:
        resposta = processar_mensagem(message_text)

    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

# Adiciona handler
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Rota do webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# Mantém a aplicação viva
if __name__ == '__main__':
    print("Bot rodando com webhook...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
