import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from processador import (
    processar_mensagem,
    comando_pagamento_feito,
    comando_quanto_devo,
    comando_total_a_pagar,
    comando_listar_pendentes,
    comando_listar_pagos,
    comando_solicitar_pagamento,
    comando_ajuda,
    comando_limpar_tudo,
    comando_corrigir_valor
)

# Carregar variáveis de ambiente
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Configurar logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Inicializar Flask e Bot
app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Comandos do bot
dispatcher.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("🤖 Bot ativo!")))
dispatcher.add_handler(CommandHandler("ajuda", comando_ajuda))
dispatcher.add_handler(CommandHandler("quanto_devo", comando_quanto_devo))
dispatcher.add_handler(CommandHandler("total_a_pagar", comando_total_a_pagar))
dispatcher.add_handler(CommandHandler("listar_pendentes", comando_listar_pendentes))
dispatcher.add_handler(CommandHandler("listar_pagos", comando_listar_pagos))
dispatcher.add_handler(CommandHandler("solicitar_pagamento", comando_solicitar_pagamento))
dispatcher.add_handler(CommandHandler("pagamento_feito", comando_pagamento_feito))

# Comandos de admin
dispatcher.add_handler(CommandHandler("limpar_tudo", comando_limpar_tudo, filters=Filters.user(user_id=ADMIN_ID)))
dispatcher.add_handler(CommandHandler("corrigir_valor", comando_corrigir_valor, filters=Filters.user(user_id=ADMIN_ID)))

# Qualquer outra mensagem
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar_mensagem))

# Webhook do Render
@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

# Agendador (opcional)
def tarefa_repetitiva():
    bot.send_message(chat_id=GROUP_ID, text="⏰ Rodando tarefa agendada.")

scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
# scheduler.add_job(tarefa_repetitiva, 'interval', hours=1)  # Exemplo de tarefa
scheduler.start()

# Iniciar servidor no Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
