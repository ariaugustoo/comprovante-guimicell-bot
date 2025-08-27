import re
from datetime import datetime
from pytz import timezone

comprovantes = []

taxas_cartao = {
    i: t for i, t in zip(range(1, 19), [
        4.39, 5.19, 6.19, 6.59, 7.19, 8.29, 9.19, 9.99, 10.29,
        10.88, 11.99, 12.52, 13.69, 14.19, 14.69, 15.19, 15.89, 16.84
    ])
}

def formatar_valor(valor):
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

def processar_mensagem(update, context):
    global comprovantes
    mensagem = update.message.text or ""
    user_id = update.message.from_user.id
    now = datetime.now(timezone('America/Sao_Paulo'))
    hora = now.strftime('%H:%M')

    if mensagem.strip() == "ajuda":
        comandos = (
            "🧾 *Comandos disponíveis:*\n\n"
            "`1438,90 pix` → registra comprovante PIX\n"
            "`7432,90 12x` → registra cartão 12x\n"
            "`✅` → marca último como pago\n"
            "`listar pagos` → lista comprovantes pagos\n"
            "`listar pendentes` → lista os não pagos\n"
            "`total que devo` → mostra total pendente\n"
            "`total geral` → pagos + pendentes\n"
            "`último comprovante` → mostra o último\n"
            "`/limpar tudo` → (admin) apaga todos\n"
            "`/corrigir valor` → (admin) edita último valor"
        )
        context.bot.send_message(chat_id=update.effective_chat.id, text=comandos, parse_mode='Markdown')
        return

    if mensagem.strip().lower() == "listar pagos":
        pagos = [c for c in comprovantes if c["pago"]]
        if pagos:
            resposta = "\n\n".join([f'✅ {formatar_valor(c["valor_liquido"])} ({c["tipo"]})' for c in pagos])
        else:
            resposta = "Nenhum comprovante pago."
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
        return

    if mensagem.strip().lower() == "listar pendentes":
        pendentes = [c for c in comprovantes if not c["pago"]]
        if pendentes:
            resposta = "\n\n".join([f'🕗 {formatar_valor(c["valor_liquido"])} ({c["tipo"]})' for c in pendentes])
        else:
            resposta = "Nenhum comprovante pendente."
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
        return

    if mensagem.strip().lower() == "total que devo":
        total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'💰 Total pendente: {formatar_valor(total)}')
        return

    if mensagem.strip().lower() == "total geral":
        total = sum(c["valor_liquido"] for c in comprovantes)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'📊 Total geral: {formatar_valor(total)}')
        return

    if mensagem.strip().lower() == "último comprovante":
        if comprovantes:
            ultimo = comprovantes[-1]
            resposta = (
                f'📄 Último comprovante:\n'
                f'💰 Valor bruto: {formatar_valor(ultimo["valor_bruto"])}\n'
                f'📉 Taxa: {ultimo["taxa"]}%\n'
                f'✅ Líquido: {formatar_valor(ultimo["valor_liquido"])}\n'
                f'⏰ Hora: {ultimo["hora"]}\n'
                f'💳 Tipo: {ultimo["tipo"]}\n'
                f'📌 Pago: {"Sim" if ultimo["pago"] else "Não"}'
            )
            context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Nenhum comprovante registrado.")
        return

    if mensagem.strip() == "✅":
        if comprovantes:
            comprovantes[-1]["pago"] = True
            context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Comprovante marcado como pago.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Nenhum comprovante para marcar.")
        return

    if mensagem.strip().startswith("/limpar tudo") and str(user_id) == os.getenv("ADMIN_ID"):
        comprovantes = []
        context.bot.send_message(chat_id=update.effective_chat.id, text="🗑️ Lista de comprovantes apagada.")
        return

    if mensagem.strip().startswith("/corrigir valor") and str(user_id) == os.getenv("ADMIN_ID"):
        partes = mensagem.split()
        if len(partes) == 3 and partes[2].replace(",", "").replace(".", "").isdigit():
            novo_valor = float(partes[2].replace(",", "."))
            if comprovantes:
                comprovantes[-1]["valor_bruto"] = novo_valor
                tipo = comprovantes[-1]["tipo"]
                taxa = 0.2 if tipo == "pix" else taxas_cartao.get(comprovantes[-1]["parcelas"], 0)
                valor_liquido = novo_valor * (1 - taxa / 100)
                comprovantes[-1]["valor_liquido"] = round(valor_liquido, 2)
                context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Valor corrigido.")
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Nenhum comprovante para corrigir.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Uso: /corrigir valor 1438,90")
        return

    match = re.search(r'([\d.,]+)\s*(pix|(\d{1,2})x)', mensagem.lower())
    if match:
        valor_raw = match.group(1).replace('.', '').replace(',', '.')
        tipo = match.group(2)
        parcelas = int(match.group(3)) if match.group(3) else 0
        valor_bruto = float(valor_raw)

        if "pix" in tipo:
            taxa = 0.2
            tipo_str = "pix"
        else:
            taxa = taxas_cartao.get(parcelas, 0)
            tipo_str = f'{parcelas}x'

        valor_liquido = round(valor_bruto * (1 - taxa / 100), 2)

        comprovante = {
            "valor_bruto": valor_bruto,
            "parcelas": parcelas if parcelas > 0 else "-",
            "hora": hora,
            "taxa": taxa,
            "valor_liquido": valor_liquido,
            "tipo": tipo_str,
            "pago": False
        }

        comprovantes.append(comprovante)

        resposta = (
            f'📄 Comprovante analisado:\n'
            f'💰 Valor bruto: {formatar_valor(valor_bruto)}\n'
            f'💳 Parcelas: {comprovante["parcelas"]}\n'
            f'⏰ Horário: {hora}\n'
            f'📉 Taxa aplicada: {taxa}%\n'
            f'✅ Valor líquido a pagar: {formatar_valor(valor_liquido)}'
        )
        context.bot.send_message(chat_id=update.effective_chat.id, text=resposta)
    else:
        aviso = (
            "❗ Envie um valor seguido de 'pix' ou número de parcelas, ex:\n"
            "`1438,90 pix`\n"
            "`7432,90 12x`"
        )
        context.bot.send_message(chat_id=update.effective_chat.id, text=aviso, parse_mode='Markdown')

def enviar_resumo_comprovantes(bot, group_id):
    pendentes = [c for c in comprovantes if not c["pago"]]
    total = sum(c["valor_liquido"] for c in pendentes)
    if pendentes:
        texto = f'🕒 *Resumo automático:*\n💰 Total pendente: {formatar_valor(total)}\n🧾 Comprovantes não pagos: {len(pendentes)}'
        bot.send_message(chat_id=group_id, text=texto, parse_mode='Markdown')
