import os
import re
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8293056690:AAFYCum41SJeY00KUU988BPukgTe7qkZ-SQ")
ADMIN_ID = os.getenv("ADMIN_ID", "8126124610")
GROUP_ID = os.getenv("GROUP_ID", "-1003089523643")
PORT = int(os.environ.get('PORT', 8443))

# Comando /start
def start(update, context):
    update.message.reply_text('Olá! O bot está funcionando.')

# Comando /ajuda
def ajuda(update, context):
    update.message.reply_text(
        "Comandos disponíveis:\n"
        "/start - Inicia o bot\n"
        "/ajuda - Mostra esta mensagem de ajuda\n"
        "Para solicitar valores, envie 'Solicito VALOR'\n"
        "Outros comandos personalizados..."
    )

# Processa solicitações de valor
def solicita_valor(update, context):
    message = update.message.text
    match = re.search(r"Solicito\s*([\d.,]+)", message, re.IGNORECASE)
    if match:
        valor = match.group(1)
        # Aqui você pode adicionar a lógica para verificar saldo, limites, etc.
        # Exemplo de resposta:
        update.message.reply_text(f"❌ Solicitação maior que o crédito disponível: R$ 0,00")
    else:
        # Não reconheceu como solicitação de valor
        comando_nao_reconhecido(update, context)

# Comando de fechamento diário
def fechamento_diario(update, context):
    message = update.message.text.lower()
    if "fechamento diário" in message or "fechamento realizado" in message:
        update.message.reply_text(
            "✅ Fechamento realizado. Saldos de Cartão e Pix zerados. Saldo pendente mantido: R$ 8.073,09."
        )
    else:
        comando_nao_reconhecido(update, context)

# Resposta para comandos não reconhecidos
def comando_nao_reconhecido(update, context):
    update.message.reply_text(
        "❓ Comando não reconhecido. Envie '/ajuda' para ver os comandos disponíveis."
    )

# Handler geral para mensagens de texto
def mensagens(update, context):
    text = update.message.text.lower()
    if text.startswith("solicito"):
        solicita_valor(update, context)
    elif "fechamento diário" in text or "fechamento realizado" in text:
        fechamento_diario(update, context)
    else:
        comando_nao_reconhecido(update, context)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Comandos com barra
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('ajuda', ajuda))

    # Mensagens de texto (sem barra)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, mensagens))

    # Para rodar com webhook (Render)
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"https://comprovante-guimicell-bot-1-63q2.onrender.com/{TELEGRAM_TOKEN}"
    )
    updater.idle()

if __name__ == '__main__':
    main()
