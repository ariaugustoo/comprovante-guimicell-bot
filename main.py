import os
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from processador import (
    processar_mensagem,
    comprovantes_pendentes,
    aprova_callback,
    rejeita_callback,
    get_username,
    is_admin,
    formatar_valor,
)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PORT = int(os.environ.get('PORT', 8443))

_motivos_rejeicao = {}

def send_pending_comprovante(update, context, resposta, comp_id=None):
    keyboard = [
        [
            InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar_{comp_id}"),
            InlineKeyboardButton("❌ Rejeitar", callback_data=f"rejeitar_{comp_id}")
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resposta,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

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
    if is_admin(user_id) and chat_type == "private":
        keyboard.insert(5, [InlineKeyboardButton("📈 Lucro do Dia", callback_data="menu_lucro")])
        keyboard.insert(6, [InlineKeyboardButton("📈 Lucro da Semana", callback_data="menu_lucro_semana")])
        keyboard.insert(7, [InlineKeyboardButton("📈 Lucro do Mês", callback_data="menu_lucro_mes")])

    markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "📋 *Menu de Acesso Rápido*\nEscolha uma opção:",
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN
    )

def responder(update, context):
    import re
    texto = update.message.text
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    resposta = processar_mensagem(texto, user_id, username)

    # Se resposta contém novo comprovante pendente (ID#UUID)
    m = re.search(r'ID#([a-f0-9\-]+)', str(resposta or ""))
    if m and "aguardando confirmação" in str(resposta or "").lower():
        comp_id = m.group(1)
        send_pending_comprovante(update, context, resposta, comp_id)
        return

    # Listar pendentes: mostra via botões, cada um pelo id
    if texto.lower().replace(" ", "") in ["listarpendentes", "pendentes"]:
        if not comprovantes_pendentes:
            update.message.reply_text("⏳ *Nenhum comprovante pendente aguardando aprovação.*", parse_mode=ParseMode.MARKDOWN)
        else:
            for c in comprovantes_pendentes:
                txt = (
                    f"🆔 ID: `{c['id']}`\n"
                    f"💸 Bruto: {formatar_valor(c['valor_bruto'])}\n"
                    f"✅ Líquido: {formatar_valor(c['valor_liquido'])}\n"
                    f"💳 Tipo: {c['tipo']}\n"
                    f"⏰ Hora: {c['hora']}\n"
                )
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar_{c['id']}"),
                        InlineKeyboardButton("❌ Rejeitar", callback_data=f"rejeitar_{c['id']}")
                    ]
                ]
                markup = InlineKeyboardMarkup(keyboard)
                context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text=txt,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=markup
                )
        return

    if resposta:
        update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
    else:
        if update.message.chat.type == "private":
            update.message.reply_text("❓ Comando não reconhecido. Envie 'ajuda'.")

def button_handler(update, context):
    query = update.callback_query
    data = query.data
    admin_id = ADMIN_ID

    if data == "menu_comprovante":
        query.answer()
        query.message.reply_text(
            "📥 Para enviar comprovante, digite:\n`1000,00 pix` ou `700,00 10x`.",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "menu_listar_pendentes":
        query.answer()
        if not comprovantes_pendentes:
            query.message.reply_text(
                "⏳ *Nenhum comprovante pendente aguardando aprovação.*",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            for c in comprovantes_pendentes:
                txt = (
                    f"🆔 ID: `{c['id']}`\n"
                    f"💸 Bruto: {formatar_valor(c['valor_bruto'])}\n"
                    f"✅ Líquido: {formatar_valor(c['valor_liquido'])}\n"
                    f"💳 Tipo: {c['tipo']}\n"
                    f"⏰ Hora: {c['hora']}\n"
                )
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar_{c['id']}"),
                        InlineKeyboardButton("❌ Rejeitar", callback_data=f"rejeitar_{c['id']}")
                    ]
                ]
                markup = InlineKeyboardMarkup(keyboard)
                context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=txt,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=markup
                )
    elif data.startswith("aprovar_"):
        comp_id = data.split("_", 1)[1]
        if query.from_user.id != admin_id:
            query.answer(text="Apenas o admin pode usar este botão.", show_alert=True)
            return
        texto = aprova_callback(comp_id, query.from_user)
        try:
            query.edit_message_text(text=texto, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
        query.answer("Comprovante aprovado e saldo liberado!")
    elif data.startswith("rejeitar_"):
        comp_id = data.split("_", 1)[1]
        if query.from_user.id != admin_id:
            query.answer(text="Apenas o admin pode usar este botão.", show_alert=True)
            return
        query.answer()
        chat_id = query.message.chat_id
        msg_id = query.message.message_id
        _motivos_rejeicao[admin_id] = (chat_id, msg_id, comp_id)
        context.bot.send_message(
            chat_id=query.from_user.id,
            text=f"Digite o motivo da rejeição do comprovante {comp_id}: (exemplo: Divergência de valor)"
        )
    elif data == "menu_saldo":
        resposta = processar_mensagem("total liquido", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_extrato":
        resposta = processar_mensagem("extrato", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_extrato_7":
        resposta = processar_mensagem("extrato 7dias", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_fechamento":
        resposta = processar_mensagem("fechamento do dia", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_solicitar_pag":
        query.answer()
        query.message.reply_text("📝 Para solicitar pagamento, envie:\n`solicito 300,00`", parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_ajuda":
        resposta = processar_mensagem("ajuda", query.from_user.id, get_username(query.from_user))
        query.answer()
        query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

def motivo_rejeicao_handler(update, context):
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    motivo = update.message.text
    if user_id in _motivos_rejeicao:
        chat_id, msg_id, comp_id = _motivos_rejeicao.pop(user_id)
        resposta = rejeita_callback(comp_id, update.message.from_user, motivo)
        if resposta and resposta.strip():
            try:
                context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=resposta)
            except Exception:
                context.bot.send_message(chat_id=chat_id, text=resposta)
            update.message.reply_text("Rejeição registrada!")
    else:
        resposta = processar_mensagem(motivo, user_id, username)
        if resposta and resposta.strip():
            try:
                update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                update.message.reply_text(resposta)

def start(update, context):
    msg = (
        "🤖 *GuimiCell Pagamentos Bot*\n\n"
        "• 📥 Envie comprovantes: 1000,00 pix ou 700,00 10x\n"
        "• /menu para menu rápido\n"
        "• Veja saldo: total liquido\n"
        "• Veja extrato ou pendentes\n"
        "• Ajuda: /ajuda"
    )
    update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

def ajuda(update, context):
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    resposta = processar_mensagem("ajuda", user_id, username)
    if resposta and resposta.strip():
        update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

def main():
    print("==== Bot foi iniciado e está rodando ====")
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
