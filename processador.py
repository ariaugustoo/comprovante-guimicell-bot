import re
from datetime import datetime
from telegram import ParseMode
from dotenv import load_dotenv
import os

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))

comprovantes = []

TAXAS = {
    "pix": 0.002,
    "credito": {
        1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719, 6: 0.0829,
        7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088, 11: 0.1199, 12: 0.1252,
        13: 0.1369, 14: 0.1419, 15: 0.1469, 16: 0.1519, 17: 0.1589, 18: 0.1684
    }
}

def calcular_valor_liquido(valor, parcelas, tipo):
    taxa = TAXAS["pix"] if tipo == "pix" else TAXAS["credito"].get(parcelas, 0)
    return round(valor * (1 - taxa), 2), taxa * 100

def extrair_valor(texto):
    try:
        valor_str = re.findall(r"[\d.,]+", texto)[0].replace(".", "").replace(",", ".")
        return float(valor_str)
    except:
        return 0.0

def processar_mensagem(update, context):
    texto = update.message.text.lower()
    user = update.message.from_user
    horario = datetime.now().strftime("%H:%M")

    if "pix" in texto:
        valor = extrair_valor(texto)
        valor_liquido, taxa = calcular_valor_liquido(valor, 1, "pix")
        comprovantes.append({"user": user.id, "valor": valor, "liquido": valor_liquido, "tipo": "pix", "parcelas": 1, "pago": False})
        msg = f"""📄 *Comprovante analisado:*
💰 Valor bruto: R$ {valor:,.2f}
📆 Tipo: PIX
⏰ Horário: {horario}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"""
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    elif re.search(r"\d+\s*x", texto) or re.search(r"x\s*\d+", texto):
        valor = extrair_valor(texto)
        parcelas = int(re.findall(r"(\d+)\s*x", texto)[0]) if "x" in texto else 1
        valor_liquido, taxa = calcular_valor_liquido(valor, parcelas, "credito")
        comprovantes.append({"user": user.id, "valor": valor, "liquido": valor_liquido, "tipo": "credito", "parcelas": parcelas, "pago": False})
        msg = f"""📄 *Comprovante analisado:*
💰 Valor bruto: R$ {valor:,.2f}
📆 Parcelas: {parcelas}x
⏰ Horário: {horario}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"""
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    elif "✅" in texto:
        if comprovantes:
            comprovantes[-1]["pago"] = True
            update.message.reply_text("🟩 Último comprovante marcado como *pago*.", parse_mode=ParseMode.MARKDOWN)

    else:
        update.message.reply_text("❗ Formato inválido. Envie no formato:\nEx: *7.500,00 pix* ou *4.000,00 12x*", parse_mode=ParseMode.MARKDOWN)

def comandos_handler(update, context):
    user_id = update.message.from_user.id
    cmd = update.message.text.lower()

    if "/listar_pendentes" in cmd:
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            update.message.reply_text("✅ Nenhum comprovante pendente.")
            return
        resposta = "\n".join([f"R$ {c['liquido']:,.2f} ({c['parcelas']}x)" for c in pendentes])
        update.message.reply_text(f"📌 *Pendentes:*\n{resposta}", parse_mode=ParseMode.MARKDOWN)

    elif "/listar_pagos" in cmd:
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            update.message.reply_text("⚠️ Nenhum comprovante marcado como pago.")
            return
        resposta = "\n".join([f"R$ {c['liquido']:,.2f} ({c['parcelas']}x)" for c in pagos])
        update.message.reply_text(f"✅ *Pagos:*\n{resposta}", parse_mode=ParseMode.MARKDOWN)

    elif "/total_que_devo" in cmd:
        total = sum(c["liquido"] for c in comprovantes if not c["pago"])
        update.message.reply_text(f"💰 *Total a pagar:* R$ {total:,.2f}", parse_mode=ParseMode.MARKDOWN)

    elif "/total_geral" in cmd:
        total = sum(c["liquido"] for c in comprovantes)
        update.message.reply_text(f"📊 *Total geral:* R$ {total:,.2f}", parse_mode=ParseMode.MARKDOWN)

    elif "/ultimo_comprovante" in cmd:
        if not comprovantes:
            update.message.reply_text("Nenhum comprovante enviado ainda.")
            return
        c = comprovantes[-1]
        update.message.reply_text(f"📄 Último: R$ {c['liquido']:,.2f} - {c['parcelas']}x - {'Pago' if c['pago'] else 'Pendente'}", parse_mode=ParseMode.MARKDOWN)

    elif "/corrigir_valor" in cmd and user_id == ADMIN_ID:
        update.message.reply_text("🛠️ Em breve: comando para editar valor de um comprovante.")

    elif "/limpar_tudo" in cmd and user_id == ADMIN_ID:
        comprovantes.clear()
        update.message.reply_text("🗑️ Todos os comprovantes foram apagados com sucesso.")

    elif "/ajuda" in cmd:
        update.message.reply_text("""📘 *Comandos disponíveis:*
/listar_pendentes
/listar_pagos
/total_que_devo
/total_geral
/ultimo_comprovante
/ajuda

🔒 (admin)
/limpar_tudo
/corrigir_valor
""", parse_mode=ParseMode.MARKDOWN)

def gerar_resumo_automatico(bot, group_id):
    pendentes = [c for c in comprovantes if not c["pago"]]
    total = sum(c["liquido"] for c in pendentes)
    if total > 0:
        bot.send_message(chat_id=group_id, text=f"⏰ *Resumo automático:*\n💰 Total a pagar: R$ {total:,.2f}", parse_mode=ParseMode.MARKDOWN)
