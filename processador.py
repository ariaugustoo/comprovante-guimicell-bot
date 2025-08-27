import re
from datetime import datetime
from telegram import Update
from telegram.ext import CallbackContext
import pytz

comprovantes = []

def normalizar_valor(valor_str):
    valor_str = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return round(float(valor_str), 2)
    except ValueError:
        return None

def calcular_taxa(valor, tipo, parcelas=None):
    if tipo == "pix":
        taxa = 0.002  # 0.2%
    elif tipo == "cartao" and parcelas:
        taxas_cartao = {
            1: 0.0439,  2: 0.0519,  3: 0.0619,  4: 0.0659,  5: 0.0719,
            6: 0.0829,  7: 0.0919,  8: 0.0999,  9: 0.1029, 10: 0.1088,
            11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
            16: 0.1519, 17: 0.1589, 18: 0.1684
        }
        taxa = taxas_cartao.get(parcelas, 0)
    else:
        taxa = 0
    return round(valor * taxa, 2), taxa

def adicionar_comprovante(valor, tipo, user, parcelas=None):
    valor_float = normalizar_valor(valor)
    if not valor_float:
        return None

    desconto, taxa_percentual = calcular_taxa(valor_float, tipo, parcelas)
    valor_liquido = round(valor_float - desconto, 2)

    comprovante = {
        "id": len(comprovantes) + 1,
        "user": user,
        "valor_bruto": valor_float,
        "parcelas": parcelas if parcelas else 1,
        "horario": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%H:%M"),
        "tipo": tipo,
        "taxa_percentual": round(taxa_percentual * 100, 2),
        "valor_liquido": valor_liquido,
        "pago": False
    }
    comprovantes.append(comprovante)
    return comprovante

def formatar_comprovante(c):
    return (
        f"📄 Comprovante #{c['id']}:\n"
        f"👤 Usuário: {c['user']}\n"
        f"💰 Valor bruto: R$ {c['valor_bruto']:.2f}\n"
        f"💳 Parcelas: {c['parcelas']}x\n"
        f"⏰ Horário: {c['horario']}\n"
        f"📉 Taxa aplicada: {c['taxa_percentual']}%\n"
        f"✅ Valor líquido a pagar: R$ {c['valor_liquido']:.2f}\n"
        f"{'🟢 Pago' if c['pago'] else '🔴 Pendente'}"
    )

def registrar_handlers(dispatcher, GROUP_ID, ADMIN_ID):
    def responder(update: Update, context: CallbackContext):
        msg = update.message.text.lower()
        user = update.message.from_user.first_name

        # Verifica se é um valor de comprovante
        match_pix = re.match(r"([\d.,]+)\s*pix", msg)
        match_cartao = re.match(r"([\d.,]+)\s*(\d{1,2})x", msg)
        
        if match_pix:
            valor = match_pix.group(1)
            comp = adicionar_comprovante(valor, "pix", user)
            if comp:
                update.message.reply_text(formatar_comprovante(comp))
            return

        if match_cartao:
            valor, parcelas = match_cartao.groups()
            comp = adicionar_comprovante(valor, "cartao", user, int(parcelas))
            if comp:
                update.message.reply_text(formatar_comprovante(comp))
            return

        if "✅" in msg:
            if comprovantes:
                comprovantes[-1]["pago"] = True
                update.message.reply_text(f"Comprovante #{comprovantes[-1]['id']} marcado como pago ✅")
            return

        if "total que devo" in msg:
            total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
            update.message.reply_text(f"📌 Total em aberto: R$ {total:.2f}")
            return

        if "total geral" in msg:
            total = sum(c["valor_liquido"] for c in comprovantes)
            update.message.reply_text(f"💰 Total geral (pagos + pendentes): R$ {total:.2f}")
            return

        if "listar pendentes" in msg:
            pendentes = [c for c in comprovantes if not c["pago"]]
            if not pendentes:
                update.message.reply_text("✅ Nenhum comprovante pendente.")
            else:
                for c in pendentes:
                    update.message.reply_text(formatar_comprovante(c))
            return

        if "listar pagos" in msg:
            pagos = [c for c in comprovantes if c["pago"]]
            if not pagos:
                update.message.reply_text("⚠️ Nenhum comprovante pago.")
            else:
                for c in pagos:
                    update.message.reply_text(formatar_comprovante(c))
            return

        if "último comprovante" in msg:
            if comprovantes:
                update.message.reply_text(formatar_comprovante(comprovantes[-1]))
            else:
                update.message.reply_text("Nenhum comprovante enviado ainda.")
            return

        if "ajuda" in msg:
            update.message.reply_text(
                "📋 *Comandos disponíveis:*\n"
                "💰 Enviar valor PIX: `1000,00 pix`\n"
                "💳 Enviar cartão: `1000,00 6x`\n"
                "✅ Marcar último como pago: `✅`\n"
                "📌 Ver total que devo: `total que devo`\n"
                "📄 Listar pendentes: `listar pendentes`\n"
                "✅ Listar pagos: `listar pagos`\n"
                "🕒 Último comprovante: `último comprovante`\n"
                "📊 Total geral: `total geral`"
            )
            return

    dispatcher.add_handler(MessageHandler(None, responder))

from telegram.ext import MessageHandler, Filters

def enviar_resumo_automatico(bot, GROUP_ID):
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    msg = f"🕗 Resumo automático:\n📌 Total em aberto: R$ {total:.2f}\nComprovantes pendentes: {len([c for c in comprovantes if not c['pago']])}"
    bot.send_message(chat_id=GROUP_ID, text=msg)
