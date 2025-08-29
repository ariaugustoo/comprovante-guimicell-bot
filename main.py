import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from processador import (
    processar_mensagem, listar_pendentes, listar_pagamentos,
    marcar_como_pago, calcular_total_liquido_pendente, calcular_total_bruto_pendente,
    solicitar_pagamento, status_geral, fechamento_do_dia,
    limpar_tudo, corrigir_valor
)

# Variáveis de ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)

app = Flask(__name__)
dispatcher = Dispatcher(bot, None, use_context=True)

# ------------------ Comandos ------------------

def ajuda(update, context):
    comandos = """
📚 *Comandos disponíveis:*
• `1000 pix` – registrar comprovante Pix
• `2000 3x` – registrar cartão 3x
• `pagamento feito` – confirmar pagamento
• `solicitar pagamento` – iniciar solicitação Pix
• `quanto devo` – total líquido a pagar
• `total a pagar` – total bruto (sem taxa)
• `listar pendentes` – lista comprovantes pendentes
• `listar pagos` – lista comprovantes pagos
• `/status` – status geral
• `fechamento do dia` – resumo diário
• `/limpar tudo` – 🔒 admin: apagar tudo
• `/corrigir valor` – 🔒 admin: editar valor

ℹ️ Envie mensagens no formato *"valor pix"* ou *"valor Xx"* para registrar comprovantes.
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=comandos, parse_mode="Markdown")

def pagamento_feito(update, context):
    resposta = marcar_como_pago()
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

def quanto_devo(update, context):
    resposta = calcular_total_liquido_pendente()
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

def total_a_pagar(update, context):
    resposta = calcular_total_bruto_pendente()
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

def listar_pendentes_cmd(update, context):
    resposta = listar_pendentes()
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode="Markdown")

def listar_pagos_cmd(update, context):
    resposta = listar_pagamentos()
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode="Markdown")

def status(update, context):
    resposta = status_geral()
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode="Markdown")

def fechamento(update, context):
    resposta = fechamento_do_dia()
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode="Markdown")

def limpar_tudo_cmd(update, context):
    if update.effective_user.id == ADMIN_ID:
        resposta = limpar_tudo()
    else:
        resposta = "❌ Apenas o administrador pode usar este comando."
    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

def corrigir_valor_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Apenas o administrador pode usar este comando.")
        return

    try:
        indice = int(context.args[0])
        novo_valor = context.args[1]
        resposta = corrigir_valor(indice, novo_valor)
    except:
        resposta = "❌ Use o comando assim: /corrigir\\_valor [índice] [valor]"

    context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)

# ------------------ Solicitação de pagamento ------------------

esperando_valor = {}
esperando_chave = {}

def solicitar_pagamento_cmd(update, context):
    user_id = update.effective_user.id
    esperando_valor[user_id] = True
    context.bot.send_message(chat_id=update.effective_chat.id, text="Digite o valor que deseja solicitar:")

def tratar_mensagem(update, context):
    user_id = update.effective_user.id
    texto = update.message.text.strip()

    # Solicitação de pagamento (etapa 1 – valor)
    if esperando_valor.get(user_id):
        esperando_valor.pop(user_id)
        try:
            valor = float(texto.replace('.', '').replace(',', '.'))
            esperando_chave[user_id] = valor
            context.bot.send_message(chat_id=update.effective_chat.id, text="Digite a chave Pix para pagamento:")
        except:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Valor inválido. Tente novamente.")
        return

    # Solicitação de pagamento (etapa 2 – chave)
    if user_id in esperando_chave:
        valor = esperando_chave.pop(user_id)
        chave = texto
        resposta = solicitar_pagamento(valor, chave)
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta, parse_mode="Markdown")
        return

    # Processar comprovante (ex: "1000 pix" ou "3000 10x")
    resposta = processar_mensagem(texto)
    if resposta:
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Comando ou valor não reconhecido.")

# ------------------ Registro dos handlers ------------------

dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(CommandHandler("status", status))
dispatcher.add_handler(CommandHandler("limpar_tudo", limpar_tudo_cmd))
dispatcher.add_handler(CommandHandler("corrigir_valor", corrigir_valor_cmd, pass_args=True))

dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^quanto devo$'), quanto_devo))
dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^total a pagar$'), total_a_pagar))
dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^listar pendentes$'), listar_pendentes_cmd))
dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^listar pagos$'), listar_pagos_cmd))
dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^pagamento feito$'), pagamento_feito))
dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^fechamento do dia$'), fechamento))
dispatcher.add_handler(MessageHandler(Filters.regex(r'(?i)^solicitar pagamento$'), solicitar_pagamento_cmd))

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, tratar_mensagem))

# ------------------ Webhook ------------------

@app.route(f"/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def home():
    return "🤖 Bot DBH Comprovantes está ativo!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
