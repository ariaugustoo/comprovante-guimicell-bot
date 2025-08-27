import os
import re
from datetime import datetime
from telegram import Update
from telegram.ext import CallbackContext
from dotenv import load_dotenv

load_dotenv()

GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

comprovantes = []
resumo_cache = {}

taxas_credito = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99,
    12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}

def parse_valor(texto):
    valor_match = re.search(r"(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})", texto)
    if valor_match:
        return float(valor_match.group(1).replace(".", "").replace(",", "."))
    return None

def processar_mensagem(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    texto = update.message.caption or update.message.text or ""

    if update.message.photo or update.message.document:
        update.message.reply_text("🧾 Por favor, envie o valor do comprovante. Ex: `548,32 pix` ou `4.899,99 12x`")
        return

    valor = parse_valor(texto)
    parcelas = re.search(r"(\d{1,2})x", texto.lower())
    is_pix = "pix" in texto.lower()

    if not valor:
        update.message.reply_text("❌ Valor inválido. Ex: `548,32 pix` ou `4.899,99 12x`")
        return

    tipo = "pix" if is_pix else "cartao"
    qtd_parcelas = int(parcelas.group(1)) if parcelas else 1

    if tipo == "pix":
        taxa = 0.2
    else:
        taxa = taxas_credito.get(qtd_parcelas, 0)

    valor_liquido = round(valor * (1 - taxa / 100), 2)

    comprovantes.append({
        "valor": valor,
        "parcelas": qtd_parcelas,
        "tipo": tipo,
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "data": datetime.now().strftime("%d/%m %H:%M"),
        "pago": False
    })

    resposta = (
        "📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {valor:,.2f}\n"
        f"💳 Parcelas: {qtd_parcelas}x\n"
        f"⏰ Horário: {comprovantes[-1]['data']}\n"
        f"📉 Taxa aplicada: {taxa:.2f}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )
    update.message.reply_text(resposta, parse_mode="Markdown")

def comandos_admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    msg = update.message.text.lower()

    if "ajuda" in msg:
        update.message.reply_text(
            "📋 *Comandos disponíveis:*\n"
            "`valor pix` → Ex: 638,12 pix\n"
            "`valor + parcelas` → Ex: 799,90 5x\n"
            "/total → Mostra valor total a pagar\n"
            "/total_geral → Total pago + pendente\n"
            "/listar_pagos\n"
            "/listar_pendentes\n"
            "/último → Último comprovante\n"
            "/limpar → [Somente ADM]\n"
            "/corrigir → [Somente ADM]",
            parse_mode="Markdown"
        )
        return

    if "último" in msg:
        if comprovantes:
            c = comprovantes[-1]
            update.message.reply_text(f"🕓 Último: R$ {c['valor']:.2f} | {c['parcelas']}x | {c['tipo']} | {c['data']}")
        else:
            update.message.reply_text("⚠️ Nenhum comprovante registrado.")
        return

    if "listar_pendentes" in msg:
        lista = [f"🔸 R$ {c['valor']} | {c['parcelas']}x | {c['data']}" for c in comprovantes if not c['pago']]
        update.message.reply_text("\n".join(lista) or "✅ Nenhum pendente.")
        return

    if "listar_pagos" in msg:
        lista = [f"✅ R$ {c['valor']} | {c['parcelas']}x | {c['data']}" for c in comprovantes if c['pago']]
        update.message.reply_text("\n".join(lista) or "Nenhum pago.")
        return

    if "total" in msg:
        total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        update.message.reply_text(f"📌 *Total a pagar:* R$ {total:,.2f}", parse_mode="Markdown")
        return

    if "total_geral" in msg:
        pago = sum(c["valor_liquido"] for c in comprovantes if c["pago"])
        pendente = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        update.message.reply_text(
            f"📊 *Resumo Geral:*\n"
            f"✅ Pago: R$ {pago:,.2f}\n"
            f"⏳ Pendente: R$ {pendente:,.2f}",
            parse_mode="Markdown"
        )
        return

    if "/limpar" in msg and user_id == ADMIN_ID:
        comprovantes.clear()
        update.message.reply_text("🧹 Todos os comprovantes foram apagados.")
        return

    if "/corrigir" in msg and user_id == ADMIN_ID:
        update.message.reply_text("🛠 Função de correção será implementada.")
        return

    update.message.reply_text("🤖 Comando não reconhecido. Use /ajuda.")

def enviar_resumo_automatico():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    texto = f"⏰ *Resumo automático:*\nTotal pendente: R$ {total:,.2f}"
    from telegram import Bot
    bot = Bot(token=os.getenv("TOKEN"))
    bot.send_message(chat_id=GROUP_ID, text=texto, parse_mode="Markdown")
