import os
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, Update
from processador import processar_mensagem, aprova_callback, rejeita_callback, is_admin, get_username

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PORT = int(os.environ.get('PORT', 8443))

_motivos_rejeicao = {}

def send_pending_comprovante(update, context, resposta, idx_pendente):
    # [OPÇÃO 1: PRINT PARA LOG DEBUG]
    print("DEBUG CHAT_ID:", update.effective_chat.id, "(type:", type(update.effective_chat.id), ") / GROUP_ID do .env:", os.getenv("GROUP_ID"), "(type:", type(os.getenv("GROUP_ID")), ")")
    
    if str(update.effective_chat.id) == str(os.getenv("GROUP_ID")):
        keyboard = [
            [
                InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar_{idx_pendente}"),
                InlineKeyboardButton("❌ Rejeitar", callback_data=f"rejeitar_{idx_pendente}")
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=resposta,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=markup
        )
    else:
        update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

def bot_menu(update, context):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    keyboard = [
        [InlineKeyboardButton("📥 Enviar Comprovante", callback_data="menu_comprovante")],
        [InlineKeyboardButton("💰 Consultar Saldo", callback_data="menu_saldo")],
        [InlineKeyboardButton("📄 Extrato - Hoje", callback_data="menu_extrato")],
        [InlineKeyboardButton("📄 Extrato - 7 dias", callback_data="menu_extrato_7")],
        [InlineKeyboardButton("⏳ Listar Pendentes", callback_data="menu_listar_pendentes")],
        [InlineKeyboardButton("📊 Fechamento do Dia", callback_data="menu_fechamento")],
        [InlineKeyboardButton("📝 Solicitar Pagamento", callback_data="menu_solicitar_pag")],
        [InlineKeyboardButton("ℹ️ Ajuda", callback_data="menu_ajuda")]
    ]
    # Só admin e só no privado vê botões de lucro
    if is_admin(user_id) and chat_type == "private":
        keyboard.insert(5, [InlineKeyboardButton("📈 Lucro do Dia", callback_data="menu_lucro")])
        keyboard.insert(6, [InlineKeyboardButton("📈 Lucro da Semana", callback_data="menu_lucro_semana")])
        keyboard.insert(7, [InlineKeyboardButton("📈 Lucro do Mês", callback_data="menu_lucro_mes")])

    markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📋 *Menu de Acesso Rápido*\nEscolha uma opção:", reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def responder(update, context):
    texto = update.message.text
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    resposta = processar_mensagem(texto, user_id, username)

    _idx = None
    for k in ("aguardando confirmação", "comprovante aguardando confirmação"):
        if resposta and k in resposta.lower():
            import re
            m = re.search(r"\[(\d+)\]", resposta)
            _idx = int(m.group(1)) if m else None
            break
    if _idx:
        send_pending_comprovante(update, context, resposta, _idx)
        return

    if resposta == "MENU_BOTAO":
        bot_menu(update, context)
        return

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

    # Menus principais
    if data == "menu_comprovante":
        query.answer()
        query.message.reply_text("📥 Para enviar comprovante, digite:\n`1000,00 pix`\nou\n`700,00 10x`/`elo 10x`", parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_saldo":
        texto = processar_mensagem("total liquido", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_extrato":
        texto = processar_mensagem("extrato", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_extrato_7":
        texto = processar_mensagem("extrato 7", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_listar_pendentes":
        texto = processar_mensagem("listar pendentes", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_lucro":
        if is_admin(query.from_user.id):
            texto = processar_mensagem("relatorio lucro", query.from_user.id, get_username(query.from_user))
            query.answer()
            query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
        else:
            query.answer("Somente admin pode ver essa opção.", show_alert=True)
    elif data == "menu_lucro_semana":
        if is_admin(query.from_user.id):
            texto = processar_mensagem("relatorio lucro semana", query.from_user.id, get_username(query.from_user))
            query.answer()
            query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
        else:
            query.answer("Somente admin pode ver essa opção.", show_alert=True)
    elif data == "menu_lucro_mes":
        if is_admin(query.from_user.id):
            texto = processar_mensagem("relatorio lucro mes", query.from_user.id, get_username(query.from_user))
            query.answer()
            query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
        else:
            query.answer("Somente admin pode ver essa opção.", show_alert=True)
    elif data == "menu_fechamento":
        texto = processar_mensagem("fechamento do dia", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_solicitar_pag":
        query.answer()
        query.message.reply_text("📝 Para solicitar pagamento, envie:\n`solicito 300,00`", parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_ajuda":
        texto = processar_mensagem("ajuda", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
    elif data.startswith("aprovar_"):
        idx = int(data.split("_")[1])
        if query.from_user.id != admin_id:
            query.answer(text="Apenas o admin pode usar este botão.", show_alert=True)
            return
        texto = aprova_callback(idx, query.from_user)
        query.edit_message_text(text=texto, parse_mode=ParseMode.MARKDOWN)
        query.answer("Comprovante aprovado e saldo liberado!")
    elif data.startswith("rejeitar_"):
        idx = int(data.split("_")[1])
        if query.from_user.id != admin_id:
            query.answer(text="Apenas o admin pode usar este botão.", show_alert=True)
            return
        query.answer()
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
            # NÃO use parse_mode porque pode quebrar por caracteres especiais vindos do usuário
            context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=resposta)
        except Exception:
            context.bot.send_message(chat_id=chat_id, text=resposta)
        update.message.reply_text("Rejeição registrada!") # apenas texto puro
    else:
        resposta = processar_mensagem(motivo, user_id, username)
        try:
            update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            update.message.reply_text(resposta)

def start(update, context):
    msg = (
        "🤖 *GuimiCell Pagamentos Bot*\n\n"
        "Automatize, audite e aprove comprovantes e pagamentos de forma simples e transparente!\n\n"
        "• 📥 Envie comprovantes usando: 1000,00 pix\n"
        "• 📄 Para acessar funções rapidamente: /menu\n"
        "• 📊 Consulte seu saldo: total liquido\n"
        "• 🆘 Ajuda: /ajuda"
    )
    update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

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
    dp.add_handler(CommandHandler('menu', bot_menu))

    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, motivo_rejeicao_handler))
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
