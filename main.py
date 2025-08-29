import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import (
    processar_mensagem,
    marcar_como_pago,
    listar_pendentes,
    listar_pagamentos,
    total_pendente_liquido,
    total_bruto_pendente,
    registrar_pagamento_parcial,
    solicitar_pagamento,
    gerar_status
)

# Inicializar Flask e Bot
app = Flask(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

@app.route('/')
def home():
    return '🤖 Bot DBH/Guimicell está no ar com sucesso!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return 'ok', 200

# Manipulador de mensagens recebidas
def processar(update, context):
    mensagem = update.message.text.lower()
    chat_id = update.message.chat_id

    if "pagamento feito" in mensagem:
        resposta = marcar_como_pago()

    elif "quanto devo" in mensagem:
        valor = total_pendente_liquido()
        resposta = f"💰 Devo ao lojista: R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    elif "total a pagar" in mensagem:
        valor = total_bruto_pendente()
        resposta = f"📌 Total bruto dos comprovantes pendentes: R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    elif "listar pendentes" in mensagem:
        resposta = listar_pendentes()

    elif "listar pagos" in mensagem:
        resposta = listar_pagamentos()

    elif "ajuda" in mensagem:
        resposta = (
            "📋 *Comandos disponíveis:*\n"
            "• Envie: `1000 pix` ou `1500 10x`\n"
            "• pagamento feito ✅\n"
            "• quanto devo\n"
            "• total a pagar\n"
            "• listar pendentes\n"
            "• listar pagos\n"
            "• solicitar pagamento\n"
            "• /status"
        )

    elif "solicitar pagamento" in mensagem:
        context.user_data["esperando_valor_solicitacao"] = True
        resposta = "💬 Qual valor deseja solicitar (em reais)?"

    elif context.user_data.get("esperando_valor_solicitacao"):
        try:
            valor = float(mensagem.replace("r$", "").replace(".", "").replace(",", "."))
            context.user_data["valor_solicitacao"] = valor
            context.user_data["esperando_valor_solicitacao"] = False
            context.user_data["esperando_chave_pix"] = True
            resposta = "🔑 Agora informe a chave Pix para receber o pagamento:"
        except:
            resposta = "❌ Valor inválido. Por favor envie no formato: 300 ou 500,00"

    elif context.user_data.get("esperando_chave_pix"):
        chave = mensagem.strip()
        valor = context.user_data.pop("valor_solicitacao", 0)
        context.user_data["esperando_chave_pix"] = False
        resposta = solicitar_pagamento(valor, chave)

    else:
        resultado = processar_mensagem(mensagem)
        resposta = resultado if resultado else "❌ Formato inválido. Envie algo como:\n1000 pix\nou\n1200 6x"

    context.bot.send_message(chat_id=chat_id, text=resposta, parse_mode="Markdown")

# Registrar o handler de mensagens
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, processar))

@app.route('/comando', methods=['GET'])
def comando():
    return 'Use /webhook para interagir com o bot.'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
