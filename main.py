from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import processar_comprovante, gerar_resumo_pendentes, gerar_resumo_geral, listar_comprovantes, limpar_todos_os_comprovantes, corrigir_ultimo_valor
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
import threading

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# Inicializa o dispatcher para lidar com mensagens
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# Armazena comprovantes
comprovantes = []

# Envia resumo automático a cada hora
def enviar_resumo_horario():
    if comprovantes:
        resumo = gerar_resumo_pendentes(comprovantes)
        bot.send_message(chat_id=GROUP_ID, text=resumo)

scheduler = BackgroundScheduler()
scheduler.add_job(enviar_resumo_horario, 'interval', hours=1)
scheduler.start()

# Verifica se o usuário é o administrador
def is_admin(update):
    return update.effective_user.id == ADMIN_ID

# Manipuladores de comandos
def ajuda(update, context):
    comandos = """
📌 *Comandos disponíveis:*

1️⃣ `6.438,76 pix` → Calcula com taxa PIX (0.2%)
2️⃣ `7.899,99 10x` → Calcula com taxa cartão (10x)
3️⃣ ✅ → Marca último comprovante como *pago*
4️⃣ `total que devo` → Total *pendente* ao lojista
5️⃣ `listar pendentes` → Lista *todos pendentes*
6️⃣ `listar pagos` → Lista *comprovantes pagos*
7️⃣ `último comprovante` → Mostra último enviado
8️⃣ `total geral` → Mostra total geral (pago + pendente)
9️⃣ `ajuda` → Lista todos os comandos

🔒 *Apenas para admin:*
• `/limpar tudo` → Apaga todos os comprovantes
• `/corrigir valor` → Corrige valor do último
"""
    update.message.reply_text(comandos, parse_mode=telegram.ParseMode.MARKDOWN)

def comando_total_devo(update, context):
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    update.message.reply_text(f"💸 Total que você deve ao lojista: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

def comando_total_geral(update, context):
    total = sum(c["valor_liquido"] for c in comprovantes)
    update.message.reply_text(f"📊 Total geral dos comprovantes: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

def comando_listar_pendentes(update, context):
    lista = listar_comprovantes(comprovantes, pago=False)
    update.message.reply_text(lista)

def comando_listar_pagos(update, context):
    lista = listar_comprovantes(comprovantes, pago=True)
    update.message.reply_text(lista)

def comando_ultimo(update, context):
    if comprovantes:
        ultimo = comprovantes[-1]
        status = "✅ PAGO" if ultimo["pago"] else "⏳ PENDENTE"
        msg = (
            f"📄 Último comprovante:\n"
            f"💰 Valor bruto: R$ {ultimo['valor_bruto']:,.2f}\n"
            f"📉 Taxa aplicada: {ultimo['taxa']}%\n"
            f"✅ Valor líquido: R$ {ultimo['valor_liquido']:,.2f}\n"
            f"{status}"
        ).replace(",", "X").replace(".", ",").replace("X", ".")
        update.message.reply_text(msg)
    else:
        update.message.reply_text("Nenhum comprovante enviado ainda.")

def comando_limpar(update, context):
    if not is_admin(update):
        update.message.reply_text("🚫 Apenas o administrador pode usar este comando.")
        return
    limpar_todos_os_comprovantes(comprovantes)
    update.message.reply_text("🧹 Todos os comprovantes foram apagados!")

def comando_corrigir(update, context):
    if not is_admin(update):
        update.message.reply_text("🚫 Apenas o administrador pode usar este comando.")
        return
    if context.args:
        novo_valor = context.args[0].replace(",", ".")
        try:
            novo_valor = float(novo_valor)
            corrigir_ultimo_valor(comprovantes, novo_valor)
            update.message.reply_text("✏️ Valor corrigido com sucesso.")
        except:
            update.message.reply_text("⚠️ Valor inválido.")
    else:
        update.message.reply_text("❗Use assim: /corrigir 1234.56")

def marcar_como_pago(update, context):
    if comprovantes:
        comprovantes[-1]["pago"] = True
        update.message.reply_text("✅ Comprovante marcado como *pago*!", parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        update.message.reply_text("❗Ainda não há comprovantes.")

# Lida com fotos e mensagens
def mensagem(update, context):
    texto = update.message.text or ""
    anexos = update.message.photo or update.message.document

    if texto.strip() == "✅":
        return marcar_como_pago(update, context)

    if texto.lower() in ["total que devo", "total que eu devo"]:
        return comando_total_devo(update, context)

    if texto.lower() == "listar pendentes":
        return comando_listar_pendentes(update, context)

    if texto.lower() == "listar pagos":
        return comando_listar_pagos(update, context)

    if texto.lower() == "último comprovante":
        return comando_ultimo(update, context)

    if texto.lower() == "total geral":
        return comando_total_geral(update, context)

    if texto.lower() == "ajuda":
        return ajuda(update, context)

    if texto or anexos:
        comprovante = processar_comprovante(update, context)
        if comprovante:
            comprovantes.append(comprovante)

# Rota webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Rota raiz para teste
@app.route('/')
def index():
    return 'Bot ativo!'

# Registra comandos
dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.document, mensagem))
dispatcher.add_handler(CommandHandler("ajuda", ajuda))
dispatcher.add_handler(CommandHandler("total", comando_total_devo))
dispatcher.add_handler(CommandHandler("totalgeral", comando_total_geral))
dispatcher.add_handler(CommandHandler("listarpendentes", comando_listar_pendentes))
dispatcher.add_handler(CommandHandler("listarpagos", comando_listar_pagos))
dispatcher.add_handler(CommandHandler("último", comando_ultimo))
dispatcher.add_handler(CommandHandler("limpar", comando_limpar))
dispatcher.add_handler(CommandHandler("corrigir", comando_corrigir, pass_args=True))

# Executa app no Render (porta dinâmica)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

