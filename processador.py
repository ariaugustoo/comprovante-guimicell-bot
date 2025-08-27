from telegram import Update
from telegram.ext import CallbackContext
import re
from datetime import datetime
import os

# Memória temporária
comprovantes = []
ultimo = {}

# Configurações
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99,
    12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19,
    17: 15.89, 18: 16.84
}

def calcular_liquido(valor, tipo, parcelas=None):
    if tipo == "pix":
        return valor * 0.998
    elif tipo == "cartao" and parcelas in taxas_cartao:
        return valor * (1 - taxas_cartao[parcelas] / 100)
    else:
        return valor

def parse_valor(texto):
    try:
        return float(texto.replace("R$", "").replace(".", "").replace(",", "."))
    except:
        return None

def processar_mensagem(update: Update, context: CallbackContext):
    texto = update.message.text.lower()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if "pix" in texto:
        comando_pix(update, context)
    elif "x" in texto:
        comando_cartao(update, context)
    elif "✅" in texto:
        marcar_como_pago(update, context)
    elif "total que devo" in texto:
        total_pendente = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        context.bot.send_message(chat_id=chat_id, text=f"🧾 Total em aberto: R$ {total_pendente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        update.message.reply_text("Comando não reconhecido. Use /ajuda para ver os comandos disponíveis.")

def comando_pix(update: Update, context: CallbackContext):
    texto = update.message.text
    valor = parse_valor(texto)
    if valor:
        liquido = calcular_liquido(valor, "pix")
        comprovante = {
            "tipo": "pix",
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "pago": False,
            "horario": datetime.now().strftime("%H:%M"),
            "parcelas": None
        }
        comprovantes.append(comprovante)
        ultimo["comprovante"] = comprovante
        msg = (
            f"📄 *Comprovante analisado:*\n"
            f"💰 Valor bruto: R$ {valor:,.2f}\n"
            f"⏰ Horário: {comprovante['horario']}\n"
            f"📉 Taxa aplicada: 0.2%\n"
            f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
        ).replace(",", "X").replace(".", ",").replace("X", ".")
        update.message.reply_text(msg, parse_mode="Markdown")

def comando_cartao(update: Update, context: CallbackContext):
    texto = update.message.text
    match = re.search(r"([\d\.,]+)\s*(\d{1,2})x", texto)
    if match:
        valor = parse_valor(match.group(1))
        parcelas = int(match.group(2))
        if valor and parcelas in taxas_cartao:
            taxa = taxas_cartao[parcelas]
            liquido = calcular_liquido(valor, "cartao", parcelas)
            comprovante = {
                "tipo": "cartao",
                "valor_bruto": valor,
                "valor_liquido": liquido,
                "pago": False,
                "horario": datetime.now().strftime("%H:%M"),
                "parcelas": parcelas
            }
            comprovantes.append(comprovante)
            ultimo["comprovante"] = comprovante
            msg = (
                f"📄 *Comprovante analisado:*\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💳 Parcelas: {parcelas}x\n"
                f"⏰ Horário: {comprovante['horario']}\n"
                f"📉 Taxa aplicada: {taxa}%\n"
                f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
            ).replace(",", "X").replace(".", ",").replace("X", ".")
            update.message.reply_text(msg, parse_mode="Markdown")

def marcar_como_pago(update: Update, context: CallbackContext):
    for c in reversed(comprovantes):
        if not c["pago"]:
            c["pago"] = True
            update.message.reply_text("✅ Comprovante marcado como pago.")
            return
    update.message.reply_text("Não há comprovantes pendentes para marcar como pagos.")

def listar_pendentes(update: Update, context: CallbackContext):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        update.message.reply_text("✅ Nenhum comprovante pendente.")
        return
    texto = "📋 Comprovantes pendentes:\n"
    for i, c in enumerate(pendentes, 1):
        texto += f"{i}. R$ {c['valor_liquido']:,.2f} - {c['tipo']} - {c['horario']}\n"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    update.message.reply_text(texto)

def listar_pagamentos(update: Update, context: CallbackContext):
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        update.message.reply_text("Nenhum pagamento registrado ainda.")
        return
    texto = "📄 Pagamentos realizados:\n"
    for i, c in enumerate(pagos, 1):
        texto += f"{i}. R$ {c['valor_liquido']:,.2f} - {c['tipo']} - {c['horario']}\n"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    update.message.reply_text(texto)

def ajuda(update: Update, context: CallbackContext):
    comandos = (
        "📋 *Comandos disponíveis:*\n"
        "• `valor pix` – Calcula valor líquido com taxa PIX 0,2%\n"
        "• `valor 4x` – Calcula valor com taxa cartão conforme parcela\n"
        "• `✅` – Marca o último comprovante como pago\n"
        "• `/listar_pendentes` – Lista comprovantes em aberto\n"
        "• `/listar_pagamentos` – Lista comprovantes pagos\n"
        "• `/ultimo_comprovante` – Mostra último comprovante\n"
        "• `/total_geral` – Mostra total de pagos + pendentes\n"
        "• `/limpar_tudo senha` – ⚠️ Limpa tudo (apenas admin)\n"
        "• `/corrigir_valor valor` – Corrige último valor (admin)"
    )
    update.message.reply_text(comandos, parse_mode="Markdown")

def ultimo_comprovante(update: Update, context: CallbackContext):
    if "comprovante" not in ultimo:
        update.message.reply_text("Nenhum comprovante encontrado ainda.")
        return
    c = ultimo["comprovante"]
    texto = (
        f"🕓 Último comprovante:\n"
        f"Tipo: {c['tipo']}\n"
        f"Bruto: R$ {c['valor_bruto']:,.2f}\n"
        f"Líquido: R$ {c['valor_liquido']:,.2f}\n"
        f"Parcelas: {c['parcelas'] or '-'}\n"
        f"Pago: {'✅' if c['pago'] else '❌'}"
    ).replace(",", "X").replace(".", ",").replace("X", ".")
    update.message.reply_text(texto)

def total_geral(update: Update, context: CallbackContext):
    total = sum(c["valor_liquido"] for c in comprovantes)
    update.message.reply_text(f"📊 Total geral: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

def limpar_tudo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        update.message.reply_text("❌ Comando restrito ao administrador.")
        return
    comprovantes.clear()
    update.message.reply_text("🧹 Todos os comprovantes foram apagados.")

def corrigir_valor(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        update.message.reply_text("❌ Comando restrito ao administrador.")
        return
    if not context.args:
        update.message.reply_text("Informe o novo valor. Ex: /corrigir_valor 1234,56")
        return
    novo_valor = parse_valor(context.args[0])
    if novo_valor and "comprovante" in ultimo:
        c = ultimo["comprovante"]
        c["valor_bruto"] = novo_valor
        if c["tipo"] == "pix":
            c["valor_liquido"] = calcular_liquido(novo_valor, "pix")
        else:
            c["valor_liquido"] = calcular_liquido(novo_valor, "cartao", c["parcelas"])
        update.message.reply_text("🔁 Valor corrigido com sucesso.")
    else:
        update.message.reply_text("Erro ao corrigir valor.")

def resumo_automatico(bot, group_id):
    pendentes = [c for c in comprovantes if not c["pago"]]
    pagos = [c for c in comprovantes if c["pago"]]
    total_pend = sum(c["valor_liquido"] for c in pendentes)
    total_pago = sum(c["valor_liquido"] for c in pagos)
    total = total_pend + total_pago
    mensagem = (
        f"⏰ *Resumo automático:*\n"
        f"🟡 Pendentes: R$ {total_pend:,.2f}\n"
        f"🟢 Pagos: R$ {total_pago:,.2f}\n"
        f"📊 Total geral: R$ {total:,.2f}"
    ).replace(",", "X").replace(".", ",").replace("X", ".")
    bot.send_message(chat_id=group_id, text=mensagem, parse_mode="Markdown")
