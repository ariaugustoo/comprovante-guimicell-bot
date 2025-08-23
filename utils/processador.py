import pytesseract
from PIL import Image
import tempfile
import os
from telegram import Update
import re
from datetime import datetime

# Tabela de taxas por número de parcelas
TAXAS = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29, 7: 9.19, 8: 9.99,
    9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}

comprovantes_processados = {}

def extrair_info(texto):
    valor_match = re.search(r"([\d.]+,\d{2})", texto)
    valor = float(valor_match.group(1).replace(".", "").replace(",", ".")) if valor_match else None

    parcelas_match = re.search(r"(\d+)[xX]", texto)
    parcelas = int(parcelas_match.group(1)) if parcelas_match else 1

    hora_match = re.search(r"(\d{2}:\d{2})", texto)
    hora = hora_match.group(1) if hora_match else datetime.now().strftime("%H:%M")

    return valor, parcelas, hora

def calcular_liquido(valor, parcelas):
    if parcelas == 0:
        taxa = 0.2
    elif parcelas in TAXAS:
        taxa = TAXAS[parcelas]
    else:
        taxa = 0.2
    return valor * (1 - taxa / 100), taxa

async def processar_comprovante(update: Update, context, valor_manual=None):
    user = update.message.from_user.first_name
    mensagem_id = update.message.message_id
    chat_id = update.message.chat_id

    if valor_manual:
        try:
            bruto = float(valor_manual.replace(".", "").replace(",", "."))
        except:
            await context.bot.send_message(chat_id, "❌ Valor inválido. Envie um número como 1234,56")
            return

        parcelas = 1
        hora = datetime.now().strftime("%H:%M")
    else:
        foto = await update.message.photo[-1].get_file()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            await foto.download_to_drive(f.name)
            texto = pytesseract.image_to_string(Image.open(f.name))
            bruto, parcelas, hora = extrair_info(texto)
            os.unlink(f.name)

    if not bruto:
        await context.bot.send_message(chat_id, "❌ Não consegui ler o valor. Responda esta mensagem com o valor manualmente.")
        return

    valor_liquido, taxa = calcular_liquido(bruto, parcelas)

    mensagem = (
        f"📄 Comprovante analisado:\n"
        f"💰 Valor bruto: R$ {bruto:,.2f}\n"
        f"💳 Parcelas: {parcelas}x\n"
        f"⏰ Horário: {hora}\n"
        f"📉 Taxa aplicada: {taxa:.2f}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )

    comprovantes_processados[mensagem_id] = valor_liquido

    await context.bot.send_message(chat_id, mensagem)

    # Somar total a pagar (sem ✅)
    total = sum(v for k, v in comprovantes_processados.items() if '✅' not in context.chat_data.get(str(k), ''))
    await context.bot.send_message(chat_id, f"📊 Total a pagar (sem pagos): R$ {total:,.2f}")
