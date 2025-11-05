import os
import uuid
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, Update

# Carrega .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PORT = int(os.environ.get('PORT', 8443))

_motivos_rejeicao = {}

# ========== ESTRUTURAS AJUSTADAS PARA USAR ID EXCLUSIVO ==========
# Simulação de "banco de dados" dos comprovantes (você pode adaptar para persistência real)
comprovantes_pendentes = []
def formatar_valor(v):
    return f'R$ {float(v):,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")

def get_username(user):
    if hasattr(user, "username") and user.username:
        return "@" + user.username
    return user.full_name if hasattr(user, "full_name") else str(user.id)

def is_admin(user_id):
    return int(user_id) == int(ADMIN_ID)

def processar_mensagem(texto, user_id, username):
    # Simulação de processamento - detecta comprovante tipo "1000,00 pix"
    texto = texto.lower().replace(" ", "")
    if "pix" in texto and "," in texto:
        # É um comprovante novo!
        valor_bruto = texto.split(",")[0]
        valor_liquido = float(valor_bruto.replace(".", "").replace("r$", "")) - 2  # exemplo taxa
        comp_id = str(uuid.uuid4())[:8]
        comp = {
            "id": comp_id,
            "valor_bruto": valor_bruto,
            "valor_liquido": valor_liquido,
            "tipo": "PIX",
            "hora": "agora",
            "user": username
        }
        comprovantes_pendentes.append(comp)
        return f"Comprovante aguardando confirmação [ID#{comp_id}]\n💸 Bruto: {formatar_valor(valor_bruto)}\n✅ Líquido: {formatar_valor(valor_liquido)}\n💳 Tipo: PIX\n👤 Usuário: {username}\n\nAguarde aprovação do admin!"
    if texto == "listar pendentes":
        if not comprovantes_pendentes:
            return "⏳ *Nenhum comprovante pendente aguardando aprovação.*"
        pendentes = ""
        for c in comprovantes_pendentes:
            pendentes += (
                f"ID: `{c['id']}`\n"
                f"💸 Bruto: {formatar_valor(c['valor_bruto'])}\n"
                f"✅ Líquido: {formatar_valor(c['valor_liquido'])}\n"
                f"💳 Tipo: {c['tipo']}\n"
                f"⏰ Hora: {c['hora']}\n\n"
            )
        return "⏳ *Pendentes aguardando conferência:*\n\n" + pendentes
    # outros comandos/fluxos aqui...
    return None

def aprova_callback(comp_id, user):
    global comprovantes_pendentes
    idx = next((i for i, c in enumerate(comprovantes_pendentes) if c["id"] == comp_id), None)
    if idx is not None:
        comp = comprovantes_pendentes.pop(idx)
        return f"✅ {get_username(user)} aprovou:\n{formatar_valor(comp['valor_bruto'])} ({comp['tipo']}) – Líq: {formatar_valor(comp['valor_liquido'])}\nSaldo liberado!"
    else:
        return "❌ Índice de pendente inválido (ID não encontrado)."

def rejeita_callback(comp_id, user, motivo):
    global comprovantes_pendentes
    idx = next((i for i, c in enumerate(comprovantes_pendentes) if c["id"] == comp_id), None)
    if idx is not None:
        comp = comprovantes_pendentes.pop(idx)
        return f"❌ {get_username(user)} rejeitou:\n{formatar_valor(comp['valor_bruto'])} ({comp['tipo']})\nMotivo: {motivo}"
    else:
        return "❌ Índice de pendente inválido (ID não encontrado)."

# ========== ENVIO DE COMPROVANTE COM ID ÚNICO NOS BOTÕES ==========
def send_pending_comprovante(update, context, resposta, comp_id):
    print("DEBUG CHAT_ID:", update.effective_chat.id, "(type:", type(update.effective_chat.id), ") / GROUP_ID do .env:", os.getenv("GROUP_ID"), "(type:", type(os.getenv("GROUP_ID")), ")")
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
    update.message.reply_text("📋 *Menu de Acesso Rápido*\nEscolha uma opção:", reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def responder(update, context):
    import re
    texto = update.message.text
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    resposta = processar_mensagem(texto, user_id, username)

    # Checa se é mensagem de comprovante aguardando aprovação
    m = re.search(r"\[ID#([a-f0-9]+)\]", resposta or "")
    if m:
        comp_id = m.group(1)
        send_pending_comprovante(update, context, resposta, comp_id)
        return

    # Listar pendentes comando digitado: cada pendente em mensagem separada com botões
    if texto.lower().strip() == "listar pendentes":
        if not comprovantes_pendentes:
            update.message.reply_text("⏳ *Nenhum comprovante pendente aguardando aprovação.*", parse_mode=ParseMode.MARKDOWN)
        else:
            for c in comprovantes_pendentes:
                txt = (
                    f"ID: `{c['id']}`\n"
                    f"💸 Bruto: {formatar_valor(c['valor_bruto'])}\n"
                    f"✅ Líquido: {formatar_valor(c['valor_liquido'])}\n"
                    f"💳 Tipo: {c['tipo']}\n"
                    f"⏰ Hora: {c['hora']}"
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
            update.message.reply_text("❓ Comando não reconhecido. Envie 'ajuda' para ver os comandos disponíveis.")

def button_handler(update: Update, context):
    query = update.callback_query
    data = query.data
    admin_id = ADMIN_ID

    if data == "menu_comprovante":
        query.answer()
        query.message.reply_text("📥 Para enviar comprovante, digite:\n`1000,00 pix`\nou\n`700,00 10x`/`elo 10x`", parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_listar_pendentes":
        query.answer()
        if not comprovantes_pendentes:
            query.message.reply_text("⏳ *Nenhum comprovante pendente aguardando aprovação.*", parse_mode=ParseMode.MARKDOWN)
        else:
            for c in comprovantes_pendentes:
                txt = (
                    f"ID: `{c['id']}`\n"
                    f"💸 Bruto: {formatar_valor(c['valor_bruto'])}\n"
                    f"✅ Líquido: {formatar_valor(c['valor_liquido'])}\n"
                    f"💳 Tipo: {c['tipo']}\n"
                    f"⏰ Hora: {c['hora']}"
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
        query.edit_message_text(text=texto, parse_mode=ParseMode.MARKDOWN)
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
        context.bot.send_message(chat_id=query.from_user.id, text=f"Digite o motivo da rejeição do comprovante ID {comp_id}: (exemplo: Divergência de valor)")
    # menu restante (não-afetado pelo ajuste de id)
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

def motivo_rejeicao_handler(update, context):
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    motivo = update.message.text
    if user_id in _motivos_rejeicao:
        chat_id, msg_id, comp_id = _motivos_rejeicao.pop(user_id)
        resposta = rejeita_callback(comp_id, update.message.from_user, motivo)
        try:
            context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=resposta)
        except Exception:
            context.bot.send_message(chat_id=chat_id, text=resposta)
        update.message.reply_text("Rejeição registrada!")
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
