import re
from datetime import datetime
from pytesseract import image_to_string
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io

# Taxas por número de parcelas (1x a 18x)
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

# Armazena os comprovantes temporariamente na memória
comprovantes = []

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

async def processar_mensagem(update, context):
    mensagem = update.message.text
    fotos = update.message.photo
    documento = update.message.document

    if mensagem:
        await interpretar_texto(update, context, mensagem)
    elif fotos:
        await processar_imagem(update, context, fotos)
    elif documento and documento.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("📎 PDFs ainda não são suportados neste bot.")

async def interpretar_texto(update, context, mensagem):
    texto = mensagem.replace(",", ".").replace("R$", "").strip()
    chat_id = update.effective_chat.id

    if texto.lower() == "ajuda":
        await update.message.reply_text("""📄 *Comandos disponíveis:*
- `1000 pix` → calcula com taxa de 0,2%
- `5000 10x` → calcula valor líquido com taxa de cartão
- `✅` → marca último comprovante como pago
- `total que devo` → soma dos valores pendentes
- `listar pendentes` → mostra comprovantes não pagos
- `listar pagos` → mostra comprovantes pagos
- `último comprovante` → exibe o último
- `total geral` → soma de todos

_O bot aplica a taxa automaticamente e responde no grupo com o valor líquido a ser repassado ao lojista._
""", parse_mode="Markdown")
        return

    if texto == "✅":
        if comprovantes:
            comprovantes[-1]["pago"] = True
            await update.message.reply_text("✅ Comprovante marcado como pago.")
        else:
            await update.message.reply_text("⚠️ Nenhum comprovante encontrado.")
        return

    if texto.lower() == "total que devo":
        total = sum(c["liquido"] for c in comprovantes if not c["pago"])
        await update.message.reply_text(f"📌 Total pendente: {formatar_valor(total)}")
        return

    if texto.lower() == "total geral":
        total = sum(c["liquido"] for c in comprovantes)
        await update.message.reply_text(f"📊 Total geral: {formatar_valor(total)}")
        return

    if texto.lower() == "listar pendentes":
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            await update.message.reply_text("✅ Nenhum comprovante pendente.")
            return
        resposta = "*📄 Pendentes:*\n"
        for c in pendentes:
            resposta += f"- {formatar_valor(c['bruto'])} • {c['tipo']} • {c['parcelas']}x • {c['hora']} • {formatar_valor(c['liquido'])}\n"
        await update.message.reply_text(resposta, parse_mode="Markdown")
        return

    if texto.lower() == "listar pagos":
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            await update.message.reply_text("❌ Nenhum comprovante pago.")
            return
        resposta = "*✅ Pagos:*\n"
        for c in pagos:
            resposta += f"- {formatar_valor(c['bruto'])} • {c['tipo']} • {c['parcelas']}x • {c['hora']} • {formatar_valor(c['liquido'])}\n"
        await update.message.reply_text(resposta, parse_mode="Markdown")
        return

    if texto.lower() == "último comprovante":
        if not comprovantes:
            await update.message.reply_text("⚠️ Nenhum comprovante registrado.")
            return
        c = comprovantes[-1]
        resposta = f"""📄 Último comprovante:
💰 Valor bruto: {formatar_valor(c['bruto'])}
💳 Parcelas: {c['parcelas']}x
⏰ Horário: {c['hora']}
📉 Taxa aplicada: {c['taxa']}%
✅ Valor líquido a pagar: {formatar_valor(c['liquido'])}"""
        await update.message.reply_text(resposta)
        return

    # Detecção manual
    if "pix" in texto.lower():
        try:
            valor = float(re.findall(r"[\d.]+", texto)[0])
            taxa = 0.2
            liquido = valor * (1 - taxa / 100)
            comprovantes.append({
                "bruto": valor,
                "tipo": "PIX",
                "parcelas": 1,
                "hora": datetime.now().strftime("%H:%M"),
                "taxa": taxa,
                "liquido": liquido,
                "pago": False
            })
            resposta = f"""📄 Comprovante analisado:
💰 Valor bruto: {formatar_valor(valor)}
💳 Parcelas: 1x
⏰ Horário: {datetime.now().strftime("%H:%M")}
📉 Taxa aplicada: {taxa}%
✅ Valor líquido a pagar: {formatar_valor(liquido)}"""
            await update.message.reply_text(resposta)
        except:
            await update.message.reply_text("❌ Não entendi o valor. Tente: `1000 pix`")
        return

    match = re.match(r"([\d.,]+)\s*(\d{1,2})x", mensagem.lower())
    if match:
        valor = float(match.group(1).replace(",", "."))
        parcelas = int(match.group(2))
        taxa = TAXAS_CARTAO.get(parcelas, 0)
        liquido = valor * (1 - taxa / 100)
        comprovantes.append({
            "bruto": valor,
            "tipo": "Cartão",
            "parcelas": parcelas,
            "hora": datetime.now().strftime("%H:%M"),
            "taxa": taxa,
            "liquido": liquido,
            "pago": False
        })
        resposta = f"""📄 Comprovante analisado:
💰 Valor bruto: {formatar_valor(valor)}
💳 Parcelas: {parcelas}x
⏰ Horário: {datetime.now().strftime("%H:%M")}
📉 Taxa aplicada: {taxa}%
✅ Valor líquido a pagar: {formatar_valor(liquido)}"""
        await update.message.reply_text(resposta)
        return

    await update.message.reply_text("❌ Comando não reconhecido. Digite `ajuda` para ver os comandos disponíveis.")

async def processar_imagem(update, context, fotos):
    foto = fotos[-1]
    arquivo = await foto.get_file()
    conteudo = await arquivo.download_as_bytearray()
    imagem = Image.open(io.BytesIO(conteudo)).convert("RGB")

    # Pré-processamento
    img_array = np.array(imagem)
    img_cinza = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    _, img_thresh = cv2.threshold(img_cinza, 150, 255, cv2.THRESH_BINARY)

    texto_extraido = image_to_string(img_thresh, lang='por')

    match_valor = re.search(r"(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})", texto_extraido)
    valor = float(match_valor.group(1).replace(".", "").replace(",", ".")) if match_valor else 0

    if valor:
        resposta = f"📸 Valor identificado via OCR: {formatar_valor(valor)}\nPor favor, envie o número de parcelas (ex: `8x`) ou digite `1000 pix`."
        await update.message.reply_text(resposta)
    else:
        await update.message.reply_text("❌ Não consegui identificar o valor no comprovante. Por favor, envie o valor manualmente (ex: `1000 pix`).")
