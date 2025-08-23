import pytesseract
from PIL import Image
import re
from datetime import datetime
from telegram import Update, Message
from io import BytesIO

# Taxas Guimicell
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}
TAXA_PIX = 0.2

# Banco de dados temporário
comprovantes = []

# Extrair valor do texto OCR
def extrair_valor(texto):
    padrao = r'(\d{1,3}(?:\.\d{3})*,\d{2})'
    encontrados = re.findall(padrao, texto)
    for valor in encontrados:
        if len(valor) >= 4:
            return float(valor.replace('.', '').replace(',', '.'))
    return None

# Extrair horário
def extrair_horario(texto):
    padrao = r'\b([01]?\d|2[0-3]):[0-5]\d\b'
    encontrados = re.findall(padrao, texto)
    return encontrados[0] if encontrados else datetime.now().strftime("%H:%M")

# Extrair parcelas
def extrair_parcelas(texto):
    padrao = r'(\d{1,2})x'
    encontrados = re.findall(padrao, texto.lower())
    return int(encontrados[0]) if encontrados else 1

# Calcular taxa e valor líquido
def calcular_liquido(valor, parcelas):
    if parcelas == 1:
        taxa = TAXA_PIX
    else:
        taxa = TAXAS_CARTAO.get(parcelas, TAXAS_CARTAO[18])  # assume 18x se não achar
    liquido = valor * (1 - taxa / 100)
    return round(taxa, 2), round(liquido, 2)

# Processar imagem/documento
async def processar_comprovante(update: Update, context, tipo):
    message: Message = update.message
    file = None

    if tipo == "foto":
        file = await message.photo[-1].get_file()
    elif tipo == "documento":
        file = await message.document.get_file()

    imagem = BytesIO()
    await file.download_to_memory(out=imagem)
    imagem.seek(0)
    texto = pytesseract.image_to_string(Image.open(imagem), lang="por")

    valor = extrair_valor(texto)
    parcelas = extrair_parcelas(texto)
    horario = extrair_horario(texto)

    if valor:
        taxa, liquido = calcular_liquido(valor, parcelas)
        comprovantes.append({
            "valor": valor,
            "parcelas": parcelas,
            "horario": horario,
            "taxa": taxa,
            "liquido": liquido,
            "pago": False
        })
        mensagem = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {valor:.2f}\n"
            f"💳 Parcelas: {parcelas}x\n"
            f"⏰ Horário: {horario}\n"
            f"📉 Taxa aplicada: {taxa}%\n"
            f"✅ Valor líquido a pagar: R$ {liquido:.2f}"
        )
    else:
        mensagem = "❌ Não consegui identificar o valor. Por favor, envie manualmente."

    await message.reply_text(mensagem)

# Fluxo manual
async def salvar_comprovante_manual(update: Update, context):
    user_id = update.message.from_user.id
    texto = update.message.text.strip()

    estado = context.user_data.get("estado", {})
    if "etapa" not in estado:
        try:
            valor = float(texto.replace("R$", "").replace(".", "").replace(",", "."))
            context.user_data["estado"] = {"etapa": "parcelas", "valor": valor}
            await update.message.reply_text("Quantas parcelas (ex: 3x)?")
        except:
            await update.message.reply_text("❌ Valor inválido. Exemplo: 1234,56")
    elif estado["etapa"] == "parcelas":
        try:
            parcelas = int(re.sub(r"\D", "", texto))
            context.user_data["estado"]["parcelas"] = parcelas
            context.user_data["estado"]["etapa"] = "horario"
            await update.message.reply_text("Qual o horário da venda? (ex: 14:30)")
        except:
            await update.message.reply_text("❌ Parcelas inválidas.")
    elif estado["etapa"] == "horario":
        horario = texto
        valor = context.user_data["estado"]["valor"]
        parcelas = context.user_data["estado"]["parcelas"]
        taxa, liquido = calcular_liquido(valor, parcelas)
        comprovantes.append({
            "valor": valor,
            "parcelas": parcelas,
            "horario": horario,
            "taxa": taxa,
            "liquido": liquido,
            "pago": False
        })
        mensagem = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {valor:.2f}\n"
            f"💳 Parcelas: {parcelas}x\n"
            f"⏰ Horário: {horario}\n"
            f"📉 Taxa aplicada: {taxa}%\n"
            f"✅ Valor líquido a pagar: R$ {liquido:.2f}"
        )
        await update.message.reply_text(mensagem)
        context.user_data["estado"] = {}

# Marcar comprovante como pago
async def marcar_como_pago(update: Update, context):
    for c in comprovantes:
        if not c["pago"]:
            c["pago"] = True
            await update.message.reply_text("✅ Comprovante marcado como pago.")
            return
    await update.message.reply_text("⚠️ Nenhum comprovante pendente encontrado.")

# Enviar total a pagar
async def enviar_total_a_pagar(application):
    total = sum(c["liquido"] for c in comprovantes if not c["pago"])
    if total > 0:
        texto = f"💵 Total a pagar (não pagos): R$ {total:.2f}"
        await application.bot.send_message(chat_id=GROUP_ID, text=texto)
