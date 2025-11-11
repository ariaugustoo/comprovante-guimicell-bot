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
    calculadora_reversa_input,
    calculadora_simples_input,
    normalizar_valor,
    extrair_valor_tipo_bandeira,
)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PORT = int(os.environ.get('PORT', 8443))

_motivos_rejeicao = {}
_calculadora_awaiting = {}  # estado por user_id: {'mode':'reverse','step':'ask_value'|'ask_type'|'await_custom_type','valor':float,'reply_chat':chat_id}

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
    # adiciona Calculadora e botões de lucro apenas em private para admins
    if chat_type == "private":
        # inserir calculadora e calculadora reversa em linhas separadas para ficar claro
        keyboard.insert(1, [InlineKeyboardButton("🧮 Calculadora", callback_data="menu_calc")])
        keyboard.insert(2, [InlineKeyboardButton("💲 Quanto cobrar", callback_data="menu_calc_bruto")])
    if is_admin(user_id) and chat_type == "private":
        keyboard.insert(6, [InlineKeyboardButton("📈 Lucro do Dia", callback_data="menu_lucro")])
        keyboard.insert(7, [InlineKeyboardButton("📈 Lucro da Semana", callback_data="menu_lucro_semana")])
        keyboard.insert(8, [InlineKeyboardButton("📈 Lucro do Mês", callback_data="menu_lucro_mes")])

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

    # Se o processador pediu para abrir o menu com botões
    if resposta == "MENU_BOTAO":
        bot_menu(update, context)
        return

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

def calc_command(update, context):
    # Handler para /calc e /c - encaminha para processador
    args = context.args
    texto = "/calc " + " ".join(args) if args else "/calc"
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    resposta = processar_mensagem(texto, user_id, username)
    if resposta:
        update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

def calc_bruto_command(update, context):
    # Handler para /calc_bruto e /cb - encaminha para processador
    args = context.args
    texto = "/calc_bruto " + " ".join(args) if args else "/calc_bruto"
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    resposta = processar_mensagem(texto, user_id, username)
    if resposta:
        update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

def button_handler(update, context):
    query = update.callback_query
    data = query.data or ""
    admin_id = ADMIN_ID

    # ack quick
    try:
        query.answer()
    except Exception:
        pass

    # Menu: respostas simples ou chamadas ao processador
    if data == "menu_comprovante":
        query.message.reply_text(
            "📥 Para enviar comprovante, digite:\n`1000,00 pix` ou `700,00 10x`.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if data == "menu_calc":
        query.message.reply_text(
            "🧮 *Calculadora rápida*\nUse no privado:\n`/calc 1000 pix` (bruto→líquido)\nExemplos: `/calc 1000 10x` ou `/c 1000` (alias curto)",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if data == "menu_calc_bruto":
        # Inicia fluxo interativo: tenta pedir no privado, senão abre no mesmo chat
        user_id = query.from_user.id
        try:
            # tenta enviar DM
            context.bot.send_message(chat_id=user_id, text="💲 *Quanto cobrar — Fluxo Interativo*\nDigite o valor líquido que você deseja receber (ex.: 500,00):", parse_mode=ParseMode.MARKDOWN)
            _calculadora_awaiting[user_id] = {"mode": "reverse", "step": "ask_value", "reply_chat": user_id}
            query.answer("Enviei uma mensagem no privado. Responda lá com o valor líquido desejado.")
            return
        except Exception:
            # se não conseguiu enviar DM (usuário não iniciou bot), inicia fluxo no mesmo chat
            reply_chat = query.message.chat_id
            _calculadora_awaiting[user_id] = {"mode": "reverse", "step": "ask_value", "reply_chat": reply_chat}
            try:
                context.bot.send_message(chat_id=reply_chat, text=f"💲 *Quanto cobrar — Fluxo Interativo*\n@{query.from_user.username or query.from_user.first_name}, digite aqui o valor líquido que você deseja receber (ex.: 500,00):", parse_mode=ParseMode.MARKDOWN)
            except Exception:
                # fallback: reply in message
                query.message.reply_text("💲 Digite aqui o valor líquido que você deseja receber (ex.: 500,00):", parse_mode=ParseMode.MARKDOWN)
            query.answer()
            return

    if data == "menu_listar_pendentes":
        if not comprovantes_pendentes:
            query.message.reply_text("⏳ *Nenhum comprovante pendente aguardando aprovação.*", parse_mode=ParseMode.MARKDOWN)
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
        return

    # Aprovar/rejeitar pendente por ID (UUID)
    if data.startswith("aprovar_"):
        comp_id = data.split("_", 1)[1]
        if query.from_user.id != admin_id:
            query.answer(text="Apenas o admin pode usar este botão.", show_alert=True)
            return
        texto = aprova_callback(comp_id, query.from_user)
        if texto:
            try:
                query.edit_message_text(text=texto, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                query.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
        query.answer("Comprovante processado.")
        return

    if data.startswith("rejeitar_"):
        comp_id = data.split("_", 1)[1]
        if query.from_user.id != admin_id:
            query.answer(text="Apenas o admin pode usar este botão.", show_alert=True)
            return
        # armazenar contexto para obter motivo via mensagem privada do admin
        chat_id = query.message.chat_id
        msg_id = query.message.message_id
        _motivos_rejeicao[admin_id] = (chat_id, msg_id, comp_id)
        context.bot.send_message(
            chat_id=query.from_user.id,
            text=f"Digite o motivo da rejeição do comprovante {comp_id}: (exemplo: Divergência de valor)"
        )
        return

    # ---- callbacks usados no fluxo interativo da calculadora reversa ----
    if data.startswith("calc_type_"):
        user_id = query.from_user.id
        state = _calculadora_awaiting.get(user_id)
        if not state or state.get("mode") != "reverse" or state.get("step") != "ask_type":
            query.answer("Fluxo expirado ou não iniciado. Use o botão 'Quanto cobrar' no menu.", show_alert=True)
            return
        valor_liq = state.get("valor")
        reply_chat = state.get("reply_chat", user_id)
        # map callback to tipo and bandeira
        key = data.replace("calc_type_", "")
        tipo = None
        bandeira = None
        if key == "pix":
            tipo = "pix"
        elif key in ["1x","2x","3x","6x","10x"]:
            tipo = key
        elif key == "elo_12x":
            tipo = "12x"; bandeira = "elo"
        elif key == "amex_12x":
            tipo = "12x"; bandeira = "amex"
        elif key == "custom":
            # ask user to type custom type in the same reply_chat
            _calculadora_awaiting[user_id]["step"] = "await_custom_type"
            try:
                context.bot.send_message(chat_id=reply_chat, text="✍️ Digite o tipo/bandeira desejada (ex.: `pix` ou `10x` ou `elo 12x` ou `amex 12x`):", parse_mode=ParseMode.MARKDOWN)
            except Exception:
                query.answer("Não consegui enviar a mensagem. Tente digitar o tipo no chat onde iniciou o fluxo.", show_alert=True)
            query.answer()
            return
        # compute result and send to reply_chat
        resposta = calculadora_reversa_input(valor_liq, tipo, bandeira)
        try:
            context.bot.send_message(chat_id=reply_chat, text=resposta, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        _calculadora_awaiting.pop(user_id, None)
        query.answer()
        return

    # Consultas via menu - chama processador e só envia resposta se houver texto
    if data == "menu_saldo":
        resposta = processar_mensagem("total liquido", query.from_user.id, get_username(query.from_user))
        if resposta:
            query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        return

    if data == "menu_extrato":
        resposta = processar_mensagem("extrato", query.from_user.id, get_username(query.from_user))
        if resposta:
            query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        return

    if data == "menu_extrato_7":
        resposta = processar_mensagem("extrato 7dias", query.from_user.id, get_username(query.from_user))
        if resposta:
            query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        return

    if data == "menu_fechamento":
        resposta = processar_mensagem("fechamento do dia", query.from_user.id, get_username(query.from_user))
        if resposta:
            query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        return

    if data == "menu_solicitar_pag":
        query.message.reply_text("📝 Para solicitar pagamento, envie:\n`solicito 300,00`", parse_mode=ParseMode.MARKDOWN)
        return

    if data == "menu_ajuda":
        resposta = processar_mensagem("ajuda", query.from_user.id, get_username(query.from_user))
        if resposta:
            query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        return

    # LUCRO: admin only (bot_menu only shows in private for admins)
    if data == "menu_lucro":
        if query.from_user.id != admin_id:
            query.answer(text="Apenas admin.", show_alert=True)
            return
        resposta = processar_mensagem("relatorio lucro", query.from_user.id, get_username(query.from_user))
        if resposta:
            query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        return

    if data == "menu_lucro_semana":
        if query.from_user.id != admin_id:
            query.answer(text="Apenas admin.", show_alert=True)
            return
        resposta = processar_mensagem("relatorio lucro semana", query.from_user.id, get_username(query.from_user))
        if resposta:
            query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        return

    if data == "menu_lucro_mes":
        if query.from_user.id != admin_id:
            query.answer(text="Apenas admin.", show_alert=True)
            return
        resposta = processar_mensagem("relatorio lucro mes", query.from_user.id, get_username(query.from_user))
        if resposta:
            query.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
        return

    # fallback: se callback desconhecido
    query.message.reply_text("⚠️ Ação desconhecida ou expirada. Tente novamente.", parse_mode=ParseMode.MARKDOWN)

def motivo_rejeicao_handler(update, context):
    user_id = update.message.from_user.id
    username = get_username(update.message.from_user)
    texto = update.message.text.strip()

    # Primeiro: fluxo interativo da calculadora (reverse) tem prioridade
    state = _calculadora_awaiting.get(user_id)
    if state:
        mode = state.get("mode")
        step = state.get("step")
        reply_chat = state.get("reply_chat", update.message.chat_id)
        if mode == "reverse":
            # passo 1: usuário digitou valor líquido desejado
            if step == "ask_value":
                valor = normalizar_valor(texto)
                if valor is None:
                    update.message.reply_text("❌ Valor inválido. Digite novamente o valor líquido (ex.: 500,00).")
                    return
                _calculadora_awaiting[user_id]["valor"] = valor
                _calculadora_awaiting[user_id]["step"] = "ask_type"
                # enviar opções via inline keyboard to reply_chat
                keyboard = [
                    [InlineKeyboardButton("PIX", callback_data="calc_type_pix")],
                    [InlineKeyboardButton("Cartão 1x", callback_data="calc_type_1x"), InlineKeyboardButton("Cartão 2x", callback_data="calc_type_2x")],
                    [InlineKeyboardButton("Cartão 3x", callback_data="calc_type_3x"), InlineKeyboardButton("Cartão 6x", callback_data="calc_type_6x")],
                    [InlineKeyboardButton("Cartão 10x", callback_data="calc_type_10x")],
                    [InlineKeyboardButton("ELO 12x", callback_data="calc_type_elo_12x"), InlineKeyboardButton("AMEX 12x", callback_data="calc_type_amex_12x")],
                    [InlineKeyboardButton("Personalizado (digite)", callback_data="calc_type_custom")]
                ]
                markup = InlineKeyboardMarkup(keyboard)
                try:
                    context.bot.send_message(chat_id=reply_chat, text="Escolha o tipo de recebimento (ou clique em Personalizado e digite):", reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
                except Exception:
                    update.message.reply_text("Escolha o tipo de recebimento (ou digite o tipo).", reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
                return
            # passo 2: aguardando tipo custom digitado (se o usuário escolheu custom)
            if step == "await_custom_type":
                type_text = texto.lower()
                # usamos extrair_valor_tipo_bandeira com um valor falso para capturar tipo/bandeira
                valor_dummy_str = "0,00 " + type_text
                _, tipo, bandeira = extrair_valor_tipo_bandeira(valor_dummy_str)
                if tipo is None:
                    update.message.reply_text("Tipo inválido. Exemplos válidos: `pix`, `10x`, `elo 12x`, `amex 12x`. Tente novamente.")
                    return
                valor_liq = state.get("valor")
                resposta = calculadora_reversa_input(valor_liq, tipo, bandeira)
                try:
                    context.bot.send_message(chat_id=reply_chat, text=resposta, parse_mode=ParseMode.MARKDOWN)
                except Exception:
                    update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
                _calculadora_awaiting.pop(user_id, None)
                return
        # se não foi tratado pelo fluxo, continua abaixo para motivos/rejeições ou fallback

    # Se não é fluxo de calculadora, trata motivo de rejeição (admin) como antes
    if user_id in _motivos_rejeicao:
        chat_id, msg_id, comp_id = _motivos_rejeicao.pop(user_id)
        resposta = rejeita_callback(comp_id, update.message.from_user, texto)
        if resposta and resposta.strip():
            try:
                context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=resposta)
            except Exception:
                context.bot.send_message(chat_id=chat_id, text=resposta)
            update.message.reply_text("Rejeição registrada!")
        return

    # Caso contrário encaminha ao processador normal
    resposta = processar_mensagem(texto, user_id, username)
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
    dp.add_handler(CommandHandler('calc', calc_command))
    dp.add_handler(CommandHandler('c', calc_command))            # alias curto
    dp.add_handler(CommandHandler('calc_bruto', calc_bruto_command))
    dp.add_handler(CommandHandler('cb', calc_bruto_command))     # alias curto
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
