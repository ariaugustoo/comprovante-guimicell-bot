import os
from flask import Flask, request
import telegram
from telegram import Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    calcular_total_liquido_pendente,
    calcular_total_bruto_pendente,
    listar_comprovantes,
    marcar_como_pago,
    registrar_solicitacao_pagamento,
    listar_pagamentos
)
from datetime import datetime
import pytz

# Inicializações
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# Timezone
def horario_brasilia():
    return datetime.now(pytz.timezone("America/Sao_Paulo"))

# Comando /start
def start(update: Update, context):
    update.message.reply_text("🤖 Bot ativo e pronto para receber comprovantes!")

# Comando ajuda
def ajuda(update: Update, context):
    comandos = (
        "📋 *Comandos disponíveis:*\n"
        "💳 `1000 3x` → Envia cartão com 3 parcelas\n"
        "💸 `100 pix` → Envia Pix com taxa 0,2%\n"
        "🧾 `listar pendentes` → Lista comprovantes não pagos\n"
        "✅ `listar pagos` → Lista os pagos\n"
        "📊 `quanto devo` → Mostra total líquido devido\n"
        "📊 `total a pagar` → Mostra total bruto dos pendentes\n"
        "📥 `solicitar pagamento` → Solicita pagamento parcial\n"
        "💵 `pagamento feito` → Marca valor como pago\n"
        "🛠️ Apenas admin:\n"
        "⚠️ `limpar tudo` → Zera todos os dados\n"
        "✏️ `corrigir valor` → Corrige valor de comprovante"
    )
    update.message.reply_text(comandos, parse_mode="Markdown")

# Comandos do bot
def comando(update: Update, context):
    texto = update.message.text.lower()

    if texto == "ajuda":
        ajuda(update, context)
    elif texto == "quanto devo":
        update.message.reply_text(calcular_total_liquido_pendente())
    elif texto == "total a pagar":
        update.message.reply_text(calcular_total_bruto_pendente())
    elif texto == "listar pendentes":
        update.message.reply_text(listar_comprovantes(pagos=False))
    elif texto == "listar pagos":
        update.message.reply_text(listar_comprovantes(pagos=True))
    elif texto == "pagamento feito":
        update.message.reply_text(marcar_como_pago())
    elif texto.startswith("solicitar pagamento"):
        update.message.reply_text("Digite o valor a ser solicitado:")
        context.user_data["esperando_valor"] = True
    elif ADMIN_ID and update.message.from_user.id == ADMIN_ID:
        if texto == "limpar tudo":
            from processador import comprovantes, solicitacoes_pagamento
            comprovantes.clear()
            solicitacoes_pagamento.clear()
            update.message.reply_text("🧹 Todos os dados foram apagados.")
        elif texto.startswith("corrigir valor"):
            update.message.reply_text("⚠️ Ainda não implementado.")
    elif "esperando_valor" in context.user_data and context.user_data["esperando_valor"]:
        resposta = registrar_solicitacao_pagamento(texto)
        update.message.reply_text(resposta)
        context.user_data["esperando_valor"] = False
    else:
        resposta = processar_mensagem(texto, horario_brasilia())
        if resposta:
            update.message.reply_text(resposta)

# Webhook principal
@app.route('/webhook', methods=['POST'])
def webhook():
    dispatcher.process_update(Update.de_json(request.get_json(force=True), bot))
    return 'OK'

# Registrar Handlers
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, comando))

# Rodar localmente (Render ignora essa linha, mas é útil para testes)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))