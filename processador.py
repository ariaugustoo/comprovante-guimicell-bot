from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram import ParseMode
import re
from datetime import datetime

comprovantes = []

taxas_cartao = {
    i: t for i, t in zip(range(1, 19), [
        4.39, 5.19, 6.19, 6.59, 7.19, 8.29, 9.19, 9.99, 10.29,
        10.88, 11.99, 12.52, 13.69, 14.19, 14.69, 15.19, 15.89, 16.84
    ])
}

def normalizar_valor(valor_str):
    valor_str = valor_str.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(valor_str)
    except:
        return None

def calcular_valor_liquido(valor, parcelas=None):
    if parcelas:
        taxa = taxas_cartao.get(parcelas, 0)
    else:
        taxa = 0.2
    valor_liquido = round(valor * (1 - taxa / 100), 2)
    return taxa, valor_liquido

def extrair_horario():
    agora = datetime.now().strftime('%H:%M')
    return agora

def formatar_mensagem(valor, parcelas=None):
    taxa, liquido = calcular_valor_liquido(valor, parcelas)
    horario = extrair_horario()
    return (
        "📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {valor:,.2f}\n"
        f"{f'💳 Parcelas: {parcelas}x\n' if parcelas else ''}"
        f"⏰ Horário: {horario}\n"
        f"📉 Taxa aplicada: {taxa:.2f}%\n"
        f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
    )

def processar_mensagem(update, context, group_id, admin_id):
    mensagem = update.message.text.lower()
    user_id = update.message.from_user.id

    match_pix = re.match(r'([\d.,]+)\s*pix', mensagem)
    match_cartao = re.match(r'([\d.,]+)\s*(\d{1,2})x', mensagem)

    if match_pix:
        valor = normalizar_valor(match_pix.group(1))
        if valor:
            comprovantes.append({'valor': valor, 'parcelas': None, 'pago': False})
            update.message.reply_text(formatar_mensagem(valor), parse_mode=ParseMode.MARKDOWN)

    elif match_cartao:
        valor = normalizar_valor(match_cartao.group(1))
        parcelas = int(match_cartao.group(2))
        if valor and parcelas:
            comprovantes.append({'valor': valor, 'parcelas': parcelas, 'pago': False})
            update.message.reply_text(formatar_mensagem(valor, parcelas), parse_mode=ParseMode.MARKDOWN)

    elif mensagem.strip() == "✅":
        for comprovante in reversed(comprovantes):
            if not comprovante["pago"]:
                comprovante["pago"] = True
                update.message.reply_text("✅ Último comprovante marcado como *pago*.", parse_mode=ParseMode.MARKDOWN)
                break

    elif "total que devo" in mensagem:
        total = sum(c['valor'] if c['parcelas'] is None else calcular_valor_liquido(c['valor'], c['parcelas'])[1]
                    for c in comprovantes if not c['pago'])
        update.message.reply_text(f"💰 *Total pendente:* R$ {total:,.2f}", parse_mode=ParseMode.MARKDOWN)

    elif "listar pendentes" in mensagem:
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            update.message.reply_text("✅ Nenhum comprovante pendente.")
        else:
            resposta = "📋 *Pendentes:*\n"
            for i, c in enumerate(pendentes, 1):
                taxa, liquido = calcular_valor_liquido(c['valor'], c['parcelas'])
                resposta += (
                    f"\n{i}. R$ {c['valor']:,.2f} - "
                    f"{f'{c['parcelas']}x - ' if c['parcelas'] else ''}"
                    f"Taxa: {taxa:.2f}% - Líquido: R$ {liquido:,.2f}"
                )
            update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

    elif "listar pagos" in mensagem:
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            update.message.reply_text("📭 Nenhum comprovante marcado como pago.")
        else:
            resposta = "📬 *Pagos:*\n"
            for i, c in enumerate(pagos, 1):
                taxa, liquido = calcular_valor_liquido(c['valor'], c['parcelas'])
                resposta += (
                    f"\n{i}. R$ {c['valor']:,.2f} - "
                    f"{f'{c['parcelas']}x - ' if c['parcelas'] else ''}"
                    f"Taxa: {taxa:.2f}% - Líquido: R$ {liquido:,.2f}"
                )
            update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)

    elif "ajuda" in mensagem:
        comandos = (
            "📌 *Comandos disponíveis:*\n"
            "- `1234,56 pix`: calcula com taxa PIX (0.2%)\n"
            "- `1234,56 6x`: calcula com taxa cartão (por parcela)\n"
            "- `✅`: marcar último como pago\n"
            "- `total que devo`: mostra total pendente\n"
            "- `listar pendentes`: mostra todos não pagos\n"
            "- `listar pagos`: mostra os pagos\n"
            "- `ajuda`: mostra esta lista"
        )
        update.message.reply_text(comandos, parse_mode=ParseMode.MARKDOWN)

def registrar_handlers(dispatcher, group_id, admin_id):
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                          lambda u, c: processar_mensagem(u, c, group_id, admin_id)))
