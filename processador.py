import os
import re
import pytesseract
from PIL import Image
from datetime import datetime
from telegram import Update
from telegram.ext import CallbackContext
from io import BytesIO

# ADMIN
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Tabela de taxas
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

# Lista em memória
comprovantes = []

def processar_mensagem(update: Update, context: CallbackContext):
    msg = update.message
    if msg.document or msg.photo:
        arquivo = msg.document or msg.photo[-1]
        file = arquivo.get_file()
        imagem = Image.open(BytesIO(file.download_as_bytearray()))
        texto_extraido = pytesseract.image_to_string(imagem)

        match_valor = re.search(r'([\d\.,]+)', texto_extraido)
        match_hora = re.search(r'(\d{2}:\d{2})', texto_extraido)
        if match_valor:
            valor_str = match_valor.group(1).replace('.', '').replace(',', '.')
            valor = float(valor_str)
            hora = match_hora.group(1) if match_hora else datetime.now().strftime("%H:%M")
            registrar_comprovante(update, tipo="imagem", valor=valor, hora=hora)
        else:
            msg.reply_text("❌ Não consegui ler o valor. Envie manualmente (ex: `1432,50 pix` ou `7899,99 10x`).")
    elif msg.text:
        texto = msg.text.lower().strip()
        if "pix" in texto:
            valor = extrair_valor(texto)
            if valor:
                registrar_comprovante(update, tipo="pix", valor=valor)
        elif "x" in texto:
            valor = extrair_valor(texto)
            parcelas = extrair_parcelas(texto)
            if valor and parcelas:
                registrar_comprovante(update, tipo="cartao", valor=valor, parcelas=parcelas)

def registrar_comprovante(update, tipo, valor, hora=None, parcelas=None):
    hora = hora or datetime.now().strftime("%H:%M")
    if tipo == "pix":
        taxa = 0.2
    elif tipo == "cartao" and parcelas in taxas_cartao:
        taxa = taxas_cartao[parcelas]
    else:
        update.message.reply_text("❌ Erro ao calcular taxa.")
        return
    valor_liquido = round(valor * (1 - taxa / 100), 2)
    comprovante = {
        "id": len(comprovantes) + 1,
        "valor": valor,
        "parcelas": parcelas,
        "hora": hora,
        "tipo": tipo,
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "pago": False
    }
    comprovantes.append(comprovante)
    texto = (
        f"📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {valor:,.2f}\n"
        f"{'💳 Parcelas: ' + str(parcelas) + 'x\n' if parcelas else ''}"
        f"⏰ Horário: {hora}\n"
        f"📉 Taxa aplicada: {taxa:.2f}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )
    update.message.reply_text(texto, parse_mode="Markdown")

def extrair_valor(texto):
    match = re.search(r"([\d\.,]+)", texto)
    if match:
        return float(match.group(1).replace('.', '').replace(',', '.'))
    return None

def extrair_parcelas(texto):
    match = re.search(r"(\d{1,2})x", texto)
    if match:
        return int(match.group(1))
    return None

def marcar_como_pago(update: Update, context: CallbackContext):
    if comprovantes:
        comprovantes[-1]["pago"] = True
        update.message.reply_text("✅ Último comprovante marcado como *pago*.", parse_mode="Markdown")
    else:
        update.message.reply_text("Nenhum comprovante para marcar como pago.")

def listar_pendentes(update: Update, context: CallbackContext):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        update.message.reply_text("✅ Todos os comprovantes foram pagos.")
        return
    resposta = "*Comprovantes pendentes:*\n\n"
    for c in pendentes:
        resposta += f"#{c['id']} - R$ {c['valor_liquido']:,.2f} às {c['hora']} ({c['tipo']})\n"
    update.message.reply_text(resposta, parse_mode="Markdown")

def listar_pagos(update: Update, context: CallbackContext):
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        update.message.reply_text("Nenhum comprovante pago.")
        return
    resposta = "*Comprovantes pagos:*\n\n"
    for c in pagos:
        resposta += f"#{c['id']} - R$ {c['valor_liquido']:,.2f} às {c['hora']} ({c['tipo']})\n"
    update.message.reply_text(resposta, parse_mode="Markdown")

def ajuda(update: Update, context: CallbackContext):
    comandos = (
        "*Comandos disponíveis:*\n"
        "/listar_pendentes – Lista comprovantes não pagos\n"
        "/listar_pagos – Lista comprovantes pagos\n"
        "/ultimo_comprovante – Mostra o último recebido\n"
        "/total_que_devo – Total de valores a pagar\n"
        "/total_geral – Total geral (pagos + pendentes)\n"
        "/limpar_tudo – ⚠️ Apaga todos os dados (admin)\n"
        "/corrigir_valor – Corrige o valor do último comprovante (admin)\n"
        "✅ – Marca o último como pago\n\n"
        "*Exemplos de entrada:*\n"
        "`1549,00 pix`\n"
        "`4389,99 10x`"
    )
    update.message.reply_text(comandos, parse_mode="Markdown")

def total_que_devo(update: Update = None, context: CallbackContext = None, resumo=False):
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    resposta = f"💸 Total pendente: R$ {total:,.2f}"
    if resumo:
        return resposta
    if update:
        update.message.reply_text(resposta)

def total_geral(update: Update, context: CallbackContext):
    total = sum(c["valor_liquido"] for c in comprovantes)
    update.message.reply_text(f"📊 Total geral dos comprovantes: R$ {total:,.2f}")

def ultimo_comprovante(update: Update, context: CallbackContext):
    if comprovantes:
        c = comprovantes[-1]
        texto = (
            f"📄 *Último comprovante:*\n"
            f"💰 Valor bruto: R$ {c['valor']:,.2f}\n"
            f"{'💳 Parcelas: ' + str(c['parcelas']) + 'x\n' if c['parcelas'] else ''}"
            f"⏰ Horário: {c['hora']}\n"
            f"📉 Taxa: {c['taxa']}%\n"
            f"✅ Valor líquido: R$ {c['valor_liquido']:,.2f}\n"
            f"{'🔒 Pago' if c['pago'] else '🕓 Pendente'}"
        )
        update.message.reply_text(texto, parse_mode="Markdown")
    else:
        update.message.reply_text("Nenhum comprovante encontrado.")

def limpar_tudo(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Comando restrito ao administrador.")
        return
    comprovantes.clear()
    update.message.reply_text("🗑️ Todos os comprovantes foram apagados.")

def corrigir_valor(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Comando restrito ao administrador.")
        return
    if not context.args or not comprovantes:
        update.message.reply_text("❌ Envie o novo valor. Ex: /corrigir_valor 1250,00")
        return
    try:
        novo_valor = float(context.args[0].replace('.', '').replace(',', '.'))
        c = comprovantes[-1]
        c["valor"] = novo_valor
        if c["tipo"] == "pix":
            c["valor_liquido"] = round(novo_valor * (1 - 0.2 / 100), 2)
        elif c["parcelas"] in taxas_cartao:
            taxa = taxas_cartao[c["parcelas"]]
            c["taxa"] = taxa
            c["valor_liquido"] = round(novo_valor * (1 - taxa / 100), 2)
        update.message.reply_text("✅ Valor corrigido com sucesso.")
    except:
        update.message.reply_text("❌ Erro ao corrigir o valor.")
