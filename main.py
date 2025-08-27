import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import CommandHandler, Dispatcher, MessageHandler, Filters
from dotenv import load_dotenv
from processador import (
    processar_mensagem, marcar_como_pago, listar_pendentes,
    listar_pagos, exibir_ajuda, ultimo_comprovante,
    total_pendente, total_geral, limpar_tudo, corrigir_valor
)

# Carrega variáveis de ambiente (.env)
load_dotenv()
TOKEN = os.getenv("TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Bot e app Flask
bot = Bot(token=TOKEN)
app = Flask(__name__)

# Ativa logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Dispatcher do Telegram
dispatcher = Dispatcher(bot, None, use_context=True)

# -------------------- COMANDOS -------------------- #

# ✅ Comandos normais
dispatcher.add_handler(CommandHandler("ajuda", exibir_ajuda))
dispatcher.add_handler(CommandHandler("totalquedevo", total_pendente))
dispatcher.add_handler(CommandHandler("listarpendentes", listar_pendentes))
dispatcher.add_handler(CommandHandler("listarpagos", listar_pagos))
dispatcher.add_handler(CommandHandler("ultimo", ultimo_comprovante))  # comando sem acento
dispatcher.add_handler(CommandHandler("totalgeral", total_geral))

# ✅ Versão alternativa: mensagem simples "último" (sem barra)
dispatcher.add_handler(MessageHandler(Filters.text(["último", "Ultimo", "ULTIMO"]), ultimo_comprovante))

# ✅ Comandos restritos (apenas admin)
def admin_only(func):
    def wrapper(update, context):
        if update.effective_user.id == ADMIN_ID:
            return func(update, context)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Acesso negado.")
    return wrapper

dispatcher.add_handler(CommandHandler("limpartudo", admin_only(limpar_tudo)))
dispatcher.add_handler(CommandHandler("corrigirvalor", admin_only(corrigir_valor)))

# ✅ Tratamento de mensagens normais (texto, imagem, etc.)
dispatcher.add_handler(MessageHandler(Filters.all, processar_mensagem))

# -------------------- WEBHOOK FLASK -------------------- #

@app.route('/')
def home():
    return 'Bot ativo com webhook!'

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
