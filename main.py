import os
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    listar_pendentes,
    listar_pagos,
    solicitar_pagamento,
    registrar_pagamento,
    limpar_dados,
    corrigir_valor_comando,
    calcular_valor_liquido_total,
    calcular_valor_bruto_total,
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

dispatcher = Dispatcher(bot, None, use_context=True)


# === COMANDOS ===

def ajuda(update, context):
    comandos = """
📋 *Comandos disponíveis:*
1. `valor pix` → Ex: 6438,76 pix
2. `valor cartão` → Ex: 7899,99 10x
3. `pagamento feito` → Marca último comprovante ou valor solicitado como pago
4. `quanto devo` → Mostra valor líquido pendente
5. `total a pagar` → Mostra valor bruto pendente
6. `listar pendentes` → Lista comprovantes pendentes
7. `listar pagos` → Lista comprovantes pagos
8. `solicitar pagamento` → Solicita valor parcial e envia chave Pix
🔐 *Admin:*
9. `corrigir valor` → Corrige último valor
10. `limpar tudo` → Limpa todos os registros
"""
    context.bot.send_message(chat_id=update.effective_chat.id, text=comandos, parse_mode=telegram.ParseMode.MARKDOWN)

def comando_limpar(update, context):
    if update.effective_user.id == ADMIN_ID:
        limpar_dados()
        update.message.reply_text("🧹 Todos os dados foram apagados.")
    else:
        update.message.reply_text("❌ Você não tem permissão para usar esse comando.")

def comando_corrigir(update, context):
    if update.effective_user.id == ADMIN_ID:
        corrigir_valor_comando(update)
    else:
        update.message.reply_text("❌ Você não tem permissão para usar esse comando.")

def comando_pagamento_feito(update, context):
    registrar_pagamento(update)

def comando_quanto_devo(update, context):
    total_liquido = calcular_valor_liquido_total()
    update.message.reply_text(f"💰 Devo ao lojista: R$ {total_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

def comando_total_a_pagar(update, context):
    total_bruto = calcular_valor_bruto_total()
    update.message.reply_text(f"📊 Total bruto pendente: R$ {total_bruto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# === REGISTRO DE HANDLERS ===

def registrar_handlers():
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), processar_mensagem))
    dispatcher.add_handler(CommandHandler("ajuda", ajuda))
    dispatcher.add_handler(CommandHandler("listarpendentes", listar_pendentes))
    dispatcher.add_handler(CommandHandler("listarpagos", listar_pagos))
    dispatcher.add_handler(CommandHandler("solicitarpagamento", solicitar_pagamento))
    dispatcher.add_handler(CommandHandler("pagamentofeito", comando_pagamento_feito))
    dispatcher.add_handler(CommandHandler("pagamento_feito", comando_pagamento_feito))
    dispatcher.add_handler(CommandHandler("quantodevo", comando_quanto_devo))
    dispatcher.add_handler(CommandHandler("totalapagar", comando_total_a_pagar))
    dispatcher.add_handler(CommandHandler("limpartudo", comando_limpar))
    dispatcher.add_handler(CommandHandler("corrigirvalor", comando_corrigir))

registrar_handlers()

# === FLASK ===

@app.route(f"/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "OK"

# === TESTE LOCAL OPCIONAL ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
