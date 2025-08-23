import pytesseract
from PIL import Image
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
import re

GROUP_ID = -1008126124610  # substitua pelo seu se necessário

# Tabela de taxas
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

TAXA_PIX = 0.2

# Lista de comprovantes processados
comprovantes_processados = []

# OCR principal
async def processar_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE, tipo: str):
    try:
        if tipo == "foto":
            file = await update.message.photo[-1].get_file()
        elif tipo == "documento":
            file = await update.message.document.get_file()
        else:
            await update.message.reply_text("Tipo de comprovante inválido.")
            return

        image_bytes = await file.download_as_bytearray()
        image = Image.open(BytesIO(image_bytes))
        texto = pytesseract.image_to_string(image, lang='por')

        match_valor = re.search(r'R?\$?\s?(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', texto)
        match_horario = re.search(r'(\d{2}:\d{2})', texto)
        match_parcelas = re.search(r'(\d{1,2})x', texto)

        if match_valor:
            valor_bruto_str = match_valor.group(1).replace('.', '').replace(',', '.')
            valor_bruto = float(valor_bruto_str)
            horario = match_horario.group(1) if match_horario else "Horário não encontrado"
            parcelas = int(match_parcelas.group(1)) if match_parcelas else 1
            taxa = TAXAS_CARTAO.get(parcelas, TAXAS_CARTAO[1])
            valor_liquido = round(valor_bruto * (1 - taxa / 100), 2)

            mensagem = (
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor_bruto:,.2f}\n"
                f"💳 Parcelas: {parcelas}x\n"
                f"⏰ Horário: {horario}\n"
                f"📉 Taxa aplicada: {taxa}%\n"
                f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
            )

            comprovantes_processados.append({'valor': valor_liquido, 'pago': False})
            await update.message.reply_text(mensagem)

        else:
            await update.message.reply_text("❌ Não consegui identificar o valor. Por favor, digite manualmente.\nDigite assim: `3500 6x 15:47`", parse_mode="Markdown")
            context.user_data['esperando_valor_manual'] = True

    except Exception as e:
        await update.message.reply_text(f"Erro ao processar: {e}")

# Valor manual
async def salvar_comprovante_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.user_data.get('esperando_valor_manual'):
            return

        partes = update.message.text.strip().split()
        if len(partes) < 1:
            await update.message.reply_text("Formato inválido. Use: `3500 6x 15:47`")
            return

        valor_bruto = float(partes[0].replace(',', '.'))
        parcelas = int(partes[1].lower().replace("x", "")) if len(partes) > 1 else 1
        horario = partes[2] if len(partes) > 2 else "Horário não informado"

        taxa = TAXAS_CARTAO.get(parcelas, TAXAS_CARTAO[1])
        valor_liquido = round(valor_bruto * (1 - taxa / 100), 2)

        mensagem = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {valor_bruto:,.2f}\n"
            f"💳 Parcelas: {parcelas}x\n"
            f"⏰ Horário: {horario}\n"
            f"📉 Taxa aplicada: {taxa}%\n"
            f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
        )

        comprovantes_processados.append({'valor': valor_liquido, 'pago': False})
        await update.message.reply_text(mensagem)

        context.user_data['esperando_valor_manual'] = False

    except Exception as e:
        await update.message.reply_text(f"Erro ao salvar comprovante manual: {e}")

# Enviar total a pagar
async def enviar_total_a_pagar(application):
    total = sum(c['valor'] for c in comprovantes_processados if not c['pago'])
    mensagem = f"📢 *Total a pagar (não pagos):* R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    await application.bot.send_message(chat_id=GROUP_ID, text=mensagem, parse_mode="Markdown")

# Marcar como pago
async def marcar_como_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if '✅' in update.message.text:
            texto = update.message.text
            match = re.search(r'R\$ ([\d.,]+)', texto)
            if match:
                valor_texto = match.group(1).replace('.', '').replace(',', '.')
                valor = float(valor_texto)
                for c in comprovantes_processados:
                    if not c['pago'] and abs(c['valor'] - valor) < 0.01:
                        c['pago'] = True
                        break
    except Exception:
        pass
