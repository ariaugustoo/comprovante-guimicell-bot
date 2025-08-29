import os
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    registrar_comprovante,
    marcar_como_pago,
    total_pendente_liquido,
    total_pendente_bruto,
    listar_pendentes,
    listar_pagamentos_feitos,
    solicitar_pagamento,
    limpar_tudo,
    corrigir_valor
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID", "0"))
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

bot = telegram.Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# Comando /start
def start(update, context):
    update.message.reply_text("🤖 Bot de Comprovantes ativo e pronto para uso!")

# Mensagens de texto
def handle_message(update, context):
    mensagem = update.message.text.strip().lower()
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    if mensagem in ["quanto devo", "valor líquido"]:
        valor = total_pendente_liquido()
        resposta = f"💰 Devo ao lojista: R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        context.bot.send_message(chat_id=chat_id, text=resposta)
        return

    if mensagem in ["total a pagar", "valor bruto"]:
        valor = total_pendente_bruto()
        resposta = f"📊 Valor bruto dos comprovantes: R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        context.bot.send_message(chat_id=chat_id, text=resposta)
        return

    if mensagem == "listar pendentes":
        resposta = listar_pendentes()
        context.bot.send_message(chat_id=chat_id, text=resposta)
        return

    if mensagem == "listar pagos":
        resposta = listar_pagamentos_feitos()
        context.bot.send_message(chat_id=chat_id, text=resposta)
        return

    if mensagem.startswith("pagamento feito"):
        try:
            partes = mensagem.split()
            valor_pago = float(partes[-1].replace(",", "."))
            sucesso, valor = marcar_como_pago(valor_pago)
            if sucesso:
                context.bot.send_message(chat_id=chat_id, text=f"✅ Pagamento de R$ {valor:.2f} registrado com sucesso.")
            else:
                context.bot.send_message(chat_id=chat_id, text=f"❌ Pagamento excede o valor devido. Total pendente: R$ {valor:.2f}")
        except:
            context.bot.send_message(chat_id=chat_id, text="❗ Use: pagamento feito 300.00")
        return

    if mensagem == "limpar tudo" and user_id == ADMIN_ID:
        limpar_tudo()
        context.bot.send_message(chat_id=chat_id, text="🧹 Todos os dados foram apagados.")
        return

    if mensagem.startswith("corrigir valor") and user_id == ADMIN_ID:
        try:
            partes = mensagem.split()
            indice = int(partes[2])
            novo_valor = float(partes[3].replace(",", "."))
            sucesso = corrigir_valor(indice, novo_valor)
            if sucesso:
                context.bot.send_message(chat_id=chat_id, text=f"✅ Valor do comprovante {indice} corrigido.")
            else:
                context.bot.send_message(chat_id=chat_id, text="❌ Índice inválido.")
        except:
            context.bot.send_message(chat_id=chat_id, text="❗ Use: corrigir valor 0 150.00")
        return

    if mensagem == "ajuda":
        comandos = (
            "📋 *Comandos disponíveis:*\n\n"
            "• 💳 Envie: `1000 pix` ou `3000 6x`\n"
            "• ✅ `pagamento feito 300`\n"
            "• 📌 `quanto devo` (líquido)\n"
            "• 📌 `total a pagar` (bruto)\n"
            "• 📌 `listar pendentes`\n"
            "• 📌 `listar pagos`\n"
            "• 🔧 `limpar tudo` (admin)\n"
            "• ✏️ `corrigir valor 0 150.00` (admin)\n"
        )
        context.bot.send_message(chat_id=chat_id, text=comandos, parse_mode=telegram.ParseMode.MARKDOWN)
        return

    # Processa mensagens com valor
    dados = processar_mensagem(mensagem)
    if dados:
        registrar_comprovante(dados)
        tipo = "PIX" if dados["tipo"] == "pix" else f"{dados['parcelas']}x"
        resposta = (
            f"📄 *Comprovante analisado:*\n"
            f"💰 Valor bruto: R$ {dados['valor_bruto']:.2f}\n"
            f"💳 Tipo: {tipo}\n"
            f"⏰ Horário: {dados['horario']}\n"
            f"📉 Taxa aplicada: {'0,2%' if dados['tipo']=='pix' else f'{round(100*TAXAS_CARTAO[dados['parcelas']],2)}%'}\n"
            f"✅ Valor líquido a pagar: R$ {dados['liquido']:.2f}"
        ).replace(".", ",")
        context.bot.send_message(chat_id=chat_id, text=resposta, parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        context.bot.send_message(chat_id=chat_id, text="❌ Não entendi. Envie: `1000 pix` ou `3000 6x`")

# Dispatcher do Telegram
def registrar_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_message))

# Webhook
@app.route('/webhook', methods=["POST"])
def webhook():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

# Inicialização do bot
dispatcher = Dispatcher(bot, None, workers=0)
registrar_handlers(dispatcher)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
