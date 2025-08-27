from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    comando_pix,
    comando_cartao,
    marcar_como_pago,
    listar_pendentes,
    listar_pagamentos,
    ajuda,
    ultimo_comprovante,
    total_geral,
    limpar_tudo,
    corrigir_valor,
    resumo_automatico
)
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)

# Handlers de Comandos
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar_mensagem))
dispatcher.add_handler(CommandHandler("start", ajuda))
dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
dispatcher.add_handler(CommandHandler("listar_pagamentos", listar_pagamentos))
dispatcher.add_handler(CommandHandler("ultimo_comprovante", ultimo_comprovante))
dispatcher.add_handler(CommandHandler("total_geral", total_geral))

dispatcher.add_handler(CommandHandler("limpar_tudo", limpar_tudo, pass_args=True))
dispatcher.add_handler(CommandHandler("corrigir_valor", corrigir_valor, pass_args=True))

# Webhook do Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot está no ar!'

# Tarefa de resumo automático a cada 1 hora
def agendar_resumo():
    while True:
        try:
            resumo_automatico(bot, GROUP_ID)
        except Exception as e:
            print(f"[Resumo automático] Erro: {e}")
        time.sleep(3600)

threading.Thread(target=agendar_resumo, daemon=True).start()

if __name__ == '__main__':
    app.run(port=10000)
