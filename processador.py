from telegram import Update, MessageEntity
from telegram.ext import CallbackContext
import re

# Simulações em memória
comprovantes = []
pagos = []
ultimo = None

# Admin ID (proteção de comandos sensíveis)
import os
from dotenv import load_dotenv
load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID"))

def processar_mensagem(update: Update, context: CallbackContext):
    global comprovantes, ultimo

    msg = update.message.text

    if msg:
        msg = msg.replace(',', '.')
        valor_match = re.search(r"(\d+\.\d{2})", msg)
        if "pix" in msg.lower():
            if valor_match:
                valor = float(valor_match.group(1))
                taxa = 0.002
                liquido = round(valor * (1 - taxa), 2)
                resposta = (
                    f"📄 Comprovante analisado:\n"
                    f"💰 Valor bruto: R$ {valor:.2f}\n"
                    f"💳 Tipo: PIX\n"
                    f"📉 Taxa aplicada: {taxa * 100:.2f}%\n"
                    f"✅ Valor líquido a pagar: R$ {liquido:.2f}"
                )
                comprovantes.append({"valor": valor, "liquido": liquido, "pago": False})
                ultimo = resposta
                update.message.reply_text(resposta)
                return

        parcelas = re.search(r"(\d+)[xX]", msg)
        if valor_match and parcelas:
            valor = float(valor_match.group(1))
            qtd_parcelas = int(parcelas.group(1))
            taxas = {
                1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719,
                6: 0.0829, 7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088,
                11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
                16: 0.1519, 17: 0.1589, 18: 0.1684
            }
            taxa = taxas.get(qtd_parcelas, 0.15)
            liquido = round(valor * (1 - taxa), 2)
            resposta = (
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:.2f}\n"
                f"💳 Parcelas: {qtd_parcelas}x\n"
                f"📉 Taxa aplicada: {taxa * 100:.2f}%\n"
                f"✅ Valor líquido a pagar: R$ {liquido:.2f}"
            )
            comprovantes.append({"valor": valor, "liquido": liquido, "pago": False})
            ultimo = resposta
            update.message.reply_text(resposta)
            return

    if msg == "✅":
        for i in range(len(comprovantes)):
            if not comprovantes[i]["pago"]:
                comprovantes[i]["pago"] = True
                pagos.append(comprovantes[i])
                update.message.reply_text("✅ Comprovante marcado como pago.")
                return
        update.message.reply_text("Nenhum comprovante pendente para marcar como pago.")

def listar_pendentes(update: Update, context: CallbackContext):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        update.message.reply_text("✅ Nenhum comprovante pendente.")
    else:
        texto = "\n".join([f"- R$ {c['liquido']:.2f}" for c in pendentes])
        update.message.reply_text(f"📄 Comprovantes pendentes:\n{texto}")

def listar_pagamentos(update: Update, context: CallbackContext):
    if not pagos:
        update.message.reply_text("📂 Nenhum pagamento registrado.")
    else:
        texto = "\n".join([f"- R$ {c['liquido']:.2f}" for c in pagos])
        update.message.reply_text(f"✅ Pagamentos realizados:\n{texto}")

def limpar_tudo(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Comando restrito ao administrador.")
        return
    comprovantes.clear()
    pagos.clear()
    update.message.reply_text("🧹 Todos os dados foram apagados.")

def corrigir_valor(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Comando restrito ao administrador.")
        return
    if comprovantes:
        comprovantes[-1]["liquido"] -= 1
        update.message.reply_text("✏️ Último valor corrigido com sucesso.")
    else:
        update.message.reply_text("⚠️ Nenhum comprovante para corrigir.")

def resumo_total(update: Update = None, context: CallbackContext = None, bot=None, chat_id=None):
    pendente = sum(c["liquido"] for c in comprovantes if not c["pago"])
    pago = sum(c["liquido"] for c in pagos)
    texto = (
        f"📊 Resumo automático:\n"
        f"💰 Total pendente: R$ {pendente:.2f}\n"
        f"✅ Total pago: R$ {pago:.2f}"
    )
    if bot and chat_id:
        bot.send_message(chat_id=chat_id, text=texto)
    elif update:
        update.message.reply_text(texto)

def comando_ajuda(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📘 *Comandos disponíveis:*\n"
        "🔹 pix ou 2.500,00 pix → calcula com taxa\n"
        "🔹 8.900,00 10x → calcula cartão\n"
        "🔹 ✅ → marca último como pago\n"
        "/listar_pendentes → listar abertos\n"
        "/listar_pagamentos → listar pagos\n"
        "/total_que_devo → total pendente\n"
        "/total_geral → tudo\n"
        "/último_comprovante → último analisado\n"
        "/resumo_total → resumo simples\n"
        "/ajuda → comandos\n"
        "/limpar_tudo → (admin)\n"
        "/corrigir_valor → (admin)"
    )

def ultimo_comprovante(update: Update, context: CallbackContext):
    if ultimo:
        update.message.reply_text(f"📄 Último comprovante:\n{ultimo}")
    else:
        update.message.reply_text("Nenhum comprovante registrado ainda.")

def total_que_devo(update: Update, context: CallbackContext):
    pendente = sum(c["liquido"] for c in comprovantes if not c["pago"])
    update.message.reply_text(f"📌 Total que você deve: R$ {pendente:.2f}")

def total_geral(update: Update, context: CallbackContext):
    total = sum(c["liquido"] for c in comprovantes)
    update.message.reply_text(f"📦 Total geral: R$ {total:.2f}")
