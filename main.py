import os
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, Update
from processador import processar_mensagem, aprova_callback, rejeita_callback, is_admin, get_username

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
PORT = int(os.environ.get('PORT', 8443))

# _motivos_rejeicao espera (chat_id, msg_id, idx) => motivo depois via reply
_motivos_rejeicao = {}

def send_pending_comprovante(update, context, resposta, idx_pendente):
    admin_id = ADMIN_ID
    keyboard = None
    # Só mostra botões se for no grupo e o admin está lá
    # Botões são inline e apenas o admin pode clicar
    if update.effective_chat.id == GROUP_ID:
        keyboard = [
            [
                InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar_{idx_pendente}"),
                InlineKeyboardButton("❌ Rejeitar", callback_data=f"rejeitar_{idx_pendente}")
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        sent = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=resposta,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=markup
        )
    else:
        update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

def responder(update, context):
    texto = update.message.text
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    resposta = processar_mensagem(texto, user_id, username)
    # Testa se resposta é comprovante pendente
    _idx = None
    for k in ("aguardando confirmação", "Comprovante aguardando confirmação"):
        if resposta and k in resposta:
            m = re.search(r"\[(\d+)\]", resposta)
            _idx = int(m.group(1)) if m else None
            break

    if _idx and is_admin(user_id):
        # Se admin mandou, mostra resposta e botões só para admin no grupo
        send_pending_comprovante(update, context, resposta, _idx)
    elif _idx:
        # Se o lojista mandou, manda para o grupo com botões (apenas admin pode agir)
        send_pending_comprovante(update, context, resposta, _idx)
    else:
        # Respostas normais
        if resposta:
            if resposta.strip().startswith("🤖") or resposta.strip().startswith("📈") or "*" in resposta or "`" in resposta:
                update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
            else:
                update.message.reply_text(resposta)
        else:
            if update.message.chat.type == "private":
                update.message.reply_text("❓ Comando não reconhecido. Envie 'ajuda' para ver os comandos disponíveis.")

def button_handler(update: Update, context):
    query = update.callback_query
    data = query.data
    admin_id = ADMIN_ID

    # Apenas admin pode agir nos botões!
    if query.from_user.id != admin_id:
        query.answer(text="Apenas o admin pode usar este botão.", show_alert=True)
        return

    # Aprovar fluxo
    if data.startswith("aprovar_"):
        idx = int(data.split("_")[1])
        texto = aprova_callback(idx, query.from_user)
        query.edit_message_text(text=texto, parse_mode=ParseMode.MARKDOWN)
        query.answer("Comprovante aprovado e saldo liberado!") 

    # Rejeitar fluxo
    elif data.startswith("rejeitar_"):
        idx = int(data.split("_")[1])
        # Solicitar motivo via mensagem direta
        query.answer()
        # Marca o admin/main para deixar o próximo reply contar como motivo rejeição
        chat_id = query.message.chat_id
        msg_id = query.message.message_id
        _motivos_rejeicao[admin_id] = (chat_id, msg_id, idx)
        context.bot.send_message(chat_id=query.from_user.id, text=f"Digite o motivo da rejeição do comprovante #{idx}: (exemplo: Divergência de valor)")

def motivo_rejeicao_handler(update, context):
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    motivo = update.message.text
    if user_id in _motivos_rejeicao:
        chat_id, msg_id, idx = _motivos_rejeicao.pop(user_id)
        resposta = rejeita_callback(idx, update.message.from_user, motivo)
        try:
            context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=resposta, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # Mensagem "apagada ou já editada"
            context.bot.send_message(chat_id=chat_id, text=resposta, parse_mode=ParseMode.MARKDOWN)
        update.message.reply_text("Rejeição registrada!", parse_mode=ParseMode.MARKDOWN)
    else:
        # Comando normal, tratativa opcional
        resposta = processar_mensagem(motivo, user_id, username)
        if resposta:
            update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

def start(update, context):
    update.message.reply_text("Olá! O bot está funcionando. Envie 'ajuda' para ver os comandos disponíveis.")

def ajuda(update, context):
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    resposta = processar_mensagem("ajuda", user_id, username)
    update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('ajuda', ajuda))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, motivo_rejeicao_handler))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, responder)) 

    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"https://comprovante-guimicell-bot-1-63q2.onrender.com/{TELEGRAM_TOKEN}"
    )
    updater.idle()

if __name__ == '__main__':
    main()
