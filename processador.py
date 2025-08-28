import re
from datetime import datetime
from telegram import Update
from telegram.ext import CallbackContext
import os

comprovantes = []
solicitacoes = []

ADMIN_ID = int(os.environ.get("ADMIN_ID"))

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}

def normalizar_valor(texto):
    try:
        valor = re.findall(r"\d+[.,]?\d*", texto.replace(" ", "").replace("R$", ""))[0]
        valor = valor.replace(".", "").replace(",", ".")
        return float(valor)
    except:
        return None

def extrair_parcelas(texto):
    match = re.search(r"(\d{1,2})x", texto.lower())
    return int(match.group(1)) if match else None

def calcular_liquido(valor, tipo, parcelas=None):
    if tipo == "pix":
        return round(valor * 0.998, 2), 0.2
    elif tipo == "cartao" and parcelas:
        taxa = taxas_cartao.get(parcelas, 0)
        return round(valor * (1 - taxa / 100), 2), taxa
    return valor, 0

def processar_mensagem(update: Update, context: CallbackContext):
    msg = update.message.text.lower()
    user_id = update.message.from_user.id
    valor = normalizar_valor(msg)
    parcelas = extrair_parcelas(msg)
    horario = datetime.now().strftime("%H:%M")

    if "pix" in msg and valor:
        liquido, taxa = calcular_liquido(valor, "pix")
        comprovantes.append({"valor": valor, "liquido": liquido, "tipo": "PIX", "horario": horario, "pago": False})
        update.message.reply_text(
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {valor:,.2f}\n"
            f"💰 Tipo: PIX\n"
            f"⏰ Horário: {horario}\n"
            f"📉 Taxa aplicada: {taxa}%\n"
            f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
        )

    elif parcelas and valor:
        liquido, taxa = calcular_liquido(valor, "cartao", parcelas)
        comprovantes.append({"valor": valor, "liquido": liquido, "tipo": f"{parcelas}x", "horario": horario, "pago": False})
        update.message.reply_text(
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {valor:,.2f}\n"
            f"💰 Tipo: Cartão ({parcelas}x)\n"
            f"⏰ Horário: {horario}\n"
            f"📉 Taxa aplicada: {taxa}%\n"
            f"✅ Valor líquido a pagar: R$ {liquido:,.2f}"
        )

    elif "pagamento feito" in msg:
        if valor:
            for i, c in enumerate(comprovantes):
                if not c["pago"]:
                    if valor >= c["liquido"]:
                        comprovantes[i]["pago"] = True
                        update.message.reply_text("✅ Pagamento total marcado como feito.")
                    else:
                        comprovantes[i]["liquido"] -= valor
                        update.message.reply_text(f"✅ Pagamento parcial de R$ {valor:,.2f} registrado.")
                    break
        else:
            for c in comprovantes:
                if not c["pago"]:
                    c["pago"] = True
                    update.message.reply_text("✅ Pagamento total marcado como feito.")
                    break

    elif "solicitar pagamento" in msg:
        update.message.reply_text("Digite o valor que deseja solicitar (ex: 689,40)")
        solicitacoes.append({"user_id": user_id, "fase": "valor"})

    elif user_id in [s["user_id"] for s in solicitacoes if s["fase"] == "valor"]:
        for s in solicitacoes:
            if s["user_id"] == user_id and s["fase"] == "valor":
                s["valor"] = valor
                s["fase"] = "chave"
                update.message.reply_text("Digite a chave PIX para receber o valor solicitado.")
                return

    elif user_id in [s["user_id"] for s in solicitacoes if s["fase"] == "chave"]:
        for s in solicitacoes:
            if s["user_id"] == user_id and s["fase"] == "chave":
                chave = update.message.text.strip()
                update.message.reply_text(
                    f"📬 Solicitação enviada!\n"
                    f"💰 Valor: R$ {s['valor']:,.2f}\n"
                    f"🔑 Chave PIX: {chave}\n\n"
                    f"Assim que o pagamento for feito, digite:\n"
                    f"`pagamento feito {s['valor']}`"
                )
                solicitacoes.remove(s)
                return

def registrar_pagamento(update: Update, context: CallbackContext):
    update.message.text = "pagamento feito"
    processar_mensagem(update, context)

def resumo_automatico():
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    if total > 0:
        bot = Bot(token=os.environ.get("TELEGRAM_TOKEN"))
        bot.send_message(chat_id=os.environ.get("GROUP_ID"), text=f"💰 Total pendente a pagar: R$ {total:,.2f}")

def quanto_devo(update: Update, context: CallbackContext):
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    update.message.reply_text(f"💰 Devo ao lojista: R$ {total:,.2f}")

def total_a_pagar(update: Update, context: CallbackContext):
    total = sum(c["valor"] for c in comprovantes if not c["pago"])
    update.message.reply_text(f"📊 Total bruto dos comprovantes: R$ {total:,.2f}")

def listar_pendentes(update: Update, context: CallbackContext):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        update.message.reply_text("✅ Não há comprovantes pendentes.")
        return
    texto = "📌 Comprovantes pendentes:\n"
    for c in pendentes:
        texto += f"💰 {c['tipo']} - R$ {c['valor']:,.2f} - ⏰ {c['horario']}\n"
    update.message.reply_text(texto)

def listar_pagamentos(update: Update, context: CallbackContext):
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        update.message.reply_text("📂 Nenhum comprovante pago ainda.")
        return
    texto = "📁 Comprovantes pagos:\n"
    for c in pagos:
        texto += f"💳 {c['tipo']} - R$ {c['valor']:,.2f} - ⏰ {c['horario']}\n"
    update.message.reply_text(texto)

def limpar_dados(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        update.message.reply_text("🚫 Comando exclusivo do administrador.")
        return
    comprovantes.clear()
    update.message.reply_text("🧹 Todos os dados foram limpos com sucesso.")

def corrigir_valor(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        update.message.reply_text("🚫 Comando exclusivo do administrador.")
        return
    update.message.reply_text("Envie o novo valor para o último comprovante pendente.")
    context.user_data["corrigir_valor"] = True

def ajuda(update: Update, context: CallbackContext):
    comandos = (
        "📋 *Comandos disponíveis:*\n"
        "• `pix` ou `valor 3x` – Registra novo comprovante\n"
        "• `pagamento feito` – Marca como pago (parcial ou total)\n"
        "• `solicitar pagamento` – Solicita valor com chave PIX\n"
        "• `listar pendentes` – Lista todos os comprovantes pendentes\n"
        "• `listar pagamentos` – Lista comprovantes já pagos\n"
        "• `quanto devo` – Valor líquido a pagar\n"
        "• `total a pagar` – Total bruto dos comprovantes\n"
        "• `/limpar` – [Admin] Limpa todos os dados\n"
        "• `/corrigir` – [Admin] Corrige valor de comprovante\n"
    )
    update.message.reply_text(comandos, parse_mode="Markdown")
