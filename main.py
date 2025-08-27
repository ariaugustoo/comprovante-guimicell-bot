import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import (
    processar_mensagem,
    listar_pendentes,
    listar_confirmados,
    total_pendentes,
    total_geral,
    ultimo_comprovante,
    limpar_todos_os_dados,
    corrigir_ultimo_valor,
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0, use_context=True)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

@app.route("/")
def index():
    return "Bot de comprovantes está no ar!"

def handle_texto(update, context):
    mensagem = update.message.text.strip().lower()
    user_id = update.message.from_user.id

    if mensagem == "total que devo":
        resposta = total_pendentes()
    elif mensagem == "listar pendentes":
        resposta = listar_pendentes()
    elif mensagem == "listar pagos":
        resposta = listar_confirmados()
    elif mensagem == "total geral":
        resposta = total_geral()
    elif mensagem == "último comprovante":
        resposta = ultimo_comprovante()
    elif mensagem == "/limpar tudo":
        if user_id == ADMIN_ID:
            resposta = limpar_todos_os_dados()
        else:
            resposta = "❌ Comando restrito ao administrador."
    elif mensagem.startswith("/corrigir valor"):
        if user_id == ADMIN_ID:
            try:
                novo_valor = mensagem.replace("/corrigir valor", "").strip()
                resposta = corrigir_ultimo_valor(novo_valor)
            except:
                resposta = "❌ Não foi possível corrigir o valor."
        else:
            resposta = "❌ Comando restrito ao administrador."
    elif "✅" in mensagem:
        resposta = "✅ Comprovante marcado como pago com sucesso!"
    else:
        resposta = processar_mensagem(mensagem)

    update.message.reply_text(resposta)

def registrar_handlers():
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_texto))

registrar_handlers()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
