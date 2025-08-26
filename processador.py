import re
import pytesseract
import cv2
import numpy as np
from io import BytesIO
from PIL import Image

# Estrutura de dados em memória
comprovantes = []

# Tabela de taxas de cartão (em %)
taxas_cartao = {
    1: 4.39,  2: 5.19,  3: 6.19,  4: 6.59,  5: 7.19,
    6: 8.29,  7: 9.19,  8: 9.99,  9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}

def aplicar_taxa(valor, tipo, parcelas=None):
    if tipo == "pix":
        taxa = 0.2
    elif tipo == "cartao" and parcelas in taxas_cartao:
        taxa = taxas_cartao[parcelas]
    else:
        taxa = 0
    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def extrair_texto_imagem(file):
    image = Image.open(BytesIO(file.download_as_bytearray()))
    image_np = np.array(image)
    img_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    texto = pytesseract.image_to_string(img_cv, lang='por')
    return texto

def processar_ocr(bot, message):
    try:
        file = bot.get_file(message.photo[-1].file_id)
        texto = extrair_texto_imagem(file)
        message.reply_text("🧾 Texto extraído do comprovante:\n\n" + texto + "\n\nDigite manualmente o valor e a forma de pagamento:\nEx: 123,45 pix ou 1234.56 3x")
    except Exception as e:
        message.reply_text("❌ Erro ao processar imagem. Tente digitar manualmente o valor.\nEx: 123,45 pix ou 1234.56 3x")

def registrar_comprovante(valor, tipo, parcelas, taxa, valor_liquido, horario, status="pendente"):
    comprovantes.append({
        "valor_bruto": valor,
        "tipo": tipo,
        "parcelas": parcelas,
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "horario": horario,
        "status": status
    })

def formatar_comprovante(c):
    parcelas_info = f"\n💳 Parcelas: {c['parcelas']}x" if c["tipo"] == "cartao" else ""
    return (
        f"📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {c['valor_bruto']:.2f}"
        f"{parcelas_info}\n"
        f"📉 Taxa aplicada: {c['taxa']}%\n"
        f"✅ Valor líquido a pagar: R$ {c['valor_liquido']:.2f}"
    )

def total_por_status(status):
    return round(sum(c["valor_liquido"] for c in comprovantes if c["status"] == status), 2)

def processar_mensagem(bot, message):
    texto = message.text.strip() if message.text else ""

    # Marcar como pago (✅)
    if texto == "✅" and comprovantes:
        for c in reversed(comprovantes):
            if c["status"] == "pendente":
                c["status"] = "pago"
                message.reply_text("✅ Comprovante marcado como *pago* com sucesso!", parse_mode="Markdown")
                return
        message.reply_text("Nenhum comprovante pendente para marcar como pago.")
        return

    # Comandos extras
    if texto.lower() == "total que devo":
        total = total_por_status("pendente")
        message.reply_text(f"💵 *Total a pagar (pendentes):* R$ {total:.2f}", parse_mode="Markdown")
        return

    if texto.lower() == "total geral":
        total = round(sum(c["valor_liquido"] for c in comprovantes), 2)
        message.reply_text(f"📊 *Total geral de todos os comprovantes:* R$ {total:.2f}", parse_mode="Markdown")
        return

    if texto.lower() == "listar pendentes":
        pendentes = [c for c in comprovantes if c["status"] == "pendente"]
        if pendentes:
            resposta = "\n\n".join([formatar_comprovante(c) for c in pendentes])
        else:
            resposta = "Nenhum comprovante pendente."
        message.reply_text(resposta, parse_mode="Markdown")
        return

    if texto.lower() == "listar pagos":
        pagos = [c for c in comprovantes if c["status"] == "pago"]
        if pagos:
            resposta = "\n\n".join([formatar_comprovante(c) for c in pagos])
        else:
            resposta = "Nenhum comprovante pago ainda."
        message.reply_text(resposta, parse_mode="Markdown")
        return

    if texto.lower() == "último comprovante" and comprovantes:
        message.reply_text(formatar_comprovante(comprovantes[-1]), parse_mode="Markdown")
        return

    if texto.lower() == "ajuda":
        comandos = (
            "📌 *Comandos disponíveis:*\n\n"
            "`valor pix` → Ex: 1200,45 pix\n"
            "`valor parcelas` → Ex: 743,99 6x\n"
            "`✅` → Marca o último comprovante como pago\n"
            "`total que devo` → Mostra total pendente\n"
            "`listar pendentes` → Lista comprovantes pendentes\n"
            "`listar pagos` → Lista comprovantes pagos\n"
            "`último comprovante` → Mostra o último\n"
            "`total geral` → Soma tudo\n"
        )
        message.reply_text(comandos, parse_mode="Markdown")
        return

    # OCR (imagem)
    if message.photo:
        processar_ocr(bot, message)
        return

    # Valor manual digitado
    match_pix = re.match(r"([\d.,]+)\s*pix", texto, re.IGNORECASE)
    match_cartao = re.match(r"([\d.,]+)\s*(\d{1,2})x", texto, re.IGNORECASE)

    if match_pix:
        valor_str = match_pix.group(1).replace(",", ".")
        valor = float(valor_str)
        valor_liquido, taxa = aplicar_taxa(valor, "pix")
        registrar_comprovante(valor, "pix", None, taxa, valor_liquido, message.date)
        message.reply_text(formatar_comprovante(comprovantes[-1]), parse_mode="Markdown")
        return

    elif match_cartao:
        valor_str = match_cartao.group(1).replace(",", ".")
        parcelas = int(match_cartao.group(2))
        valor = float(valor_str)
        valor_liquido, taxa = aplicar_taxa(valor, "cartao", parcelas)
        registrar_comprovante(valor, "cartao", parcelas, taxa, valor_liquido, message.date)
        message.reply_text(formatar_comprovante(comprovantes[-1]), parse_mode="Markdown")
        return

    # Mensagem genérica
    message.reply_text("Envie o comprovante (foto) ou digite no formato:\nEx: 1540,99 pix ou 1234.56 6x")
