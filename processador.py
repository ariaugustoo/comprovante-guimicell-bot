import re
from datetime import datetime
from telegram import Message
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np

# Simulação de armazenamento em memória
comprovantes = []

# Tabela de taxas por número de parcelas (crédito)
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def processar_imagem(bot, message: Message):
    if message.photo:
        file_id = message.photo[-1].file_id
        file = bot.get_file(file_id)
        image_bytes = file.download_as_bytearray()
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        text = pytesseract.image_to_string(open_cv_image)
        valor = extrair_valor(text)
        parcelas = extrair_parcelas(text)
        horario = extrair_horario(text)

        if valor is None:
            bot.send_message(chat_id=message.chat_id, text="Não consegui identificar o valor no comprovante. Por favor, envie o valor digitado (ex: 1234,56 pix ou 7999,99 12x).")
            return

        tipo = 'pix' if parcelas is None else 'cartao'
        taxa = 0.2 if tipo == 'pix' else TAXAS_CARTAO.get(parcelas, 0)
        valor_liquido = round(valor * (1 - taxa / 100), 2)

        comprovante = {
            'valor': valor,
            'parcelas': parcelas,
            'horario': horario or datetime.now().strftime("%H:%M"),
            'tipo': tipo,
            'taxa': taxa,
            'valor_liquido': valor_liquido,
            'pago': False
        }

        comprovantes.append(comprovante)

        resposta = (
            f"📄 *Comprovante analisado:*\n"
            f"💰 Valor bruto: R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + "\n" +
            (f"💳 Parcelas: {parcelas}x\n" if parcelas else "") +
            f"⏰ Horário: {comprovante['horario']}\n"
            f"📉 Taxa aplicada: {taxa}%\n"
            f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        bot.send_message(chat_id=message.chat_id, text=resposta, parse_mode='Markdown')

def processar_comprovante_texto(bot, message: Message):
    texto = message.text.lower().strip()

    # Marcar como pago
    if texto == '✅':
        for c in reversed(comprovantes):
            if not c['pago']:
                c['pago'] = True
                bot.send_message(chat_id=message.chat_id, text="✅ Último comprovante marcado como pago.")
                return
        bot.send_message(chat_id=message.chat_id, text="Não há comprovantes pendentes para marcar como pago.")
        return

    # Comando: total que devo
    if "total que devo" in texto:
        total = sum(c['valor_liquido'] for c in comprovantes if not c['pago'])
        total = round(total, 2)
        bot.send_message(chat_id=message.chat_id, text=f"💰 Total a repassar (pendente): R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return

    # Comando: listar pendentes
    if "listar pendentes" in texto:
        pendentes = [c for c in comprovantes if not c['pago']]
        if not pendentes:
            bot.send_message(chat_id=message.chat_id, text="✅ Nenhum comprovante pendente.")
            return
        texto_resp = "📋 *Pendentes:*\n"
        for i, c in enumerate(pendentes, 1):
            texto_resp += f"{i}. 💰 R$ {c['valor_liquido']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            texto_resp += f" ({c['parcelas']}x)" if c['tipo'] == 'cartao' else " (pix)"
            texto_resp += f" - ⏰ {c['horario']}\n"
        bot.send_message(chat_id=message.chat_id, text=texto_resp, parse_mode='Markdown')
        return

    # Comando: listar pagos
    if "listar pagos" in texto:
        pagos = [c for c in comprovantes if c['pago']]
        if not pagos:
            bot.send_message(chat_id=message.chat_id, text="Nenhum comprovante pago ainda.")
            return
        texto_resp = "📗 *Pagos:*\n"
        for i, c in enumerate(pagos, 1):
            texto_resp += f"{i}. 💰 R$ {c['valor_liquido']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            texto_resp += f" ({c['parcelas']}x)" if c['tipo'] == 'cartao' else " (pix)"
            texto_resp += f" - ⏰ {c['horario']}\n"
        bot.send_message(chat_id=message.chat_id, text=texto_resp, parse_mode='Markdown')
        return

    # Comando: ajuda
    if "ajuda" in texto:
        bot.send_message(chat_id=message.chat_id, text=(
            "🛠 *Comandos disponíveis:*\n\n"
            "📸 Envie um comprovante como foto para análise automática (OCR)\n"
            "💬 Ou envie uma mensagem com:\n"
            "`1234,56 pix` → Aplica taxa de 0,2%\n"
            "`7999,99 10x` → Aplica taxa conforme número de parcelas\n"
            "`✅` → Marca último comprovante como pago\n"
            "`total que devo` → Mostra total pendente\n"
            "`listar pendentes` → Lista todos os pendentes\n"
            "`listar pagos` → Lista pagos\n"
            "`último comprovante` → Mostra o último\n"
            "`total geral` → Soma total de todos"
        ), parse_mode='Markdown')
        return

    # Comando: último comprovante
    if "último comprovante" in texto:
        if not comprovantes:
            bot.send_message(chat_id=message.chat_id, text="Nenhum comprovante registrado ainda.")
            return
        c = comprovantes[-1]
        bot.send_message(chat_id=message.chat_id, text=(
            f"📄 Último comprovante:\n"
            f"💰 Valor bruto: R$ {c['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + "\n" +
            (f"💳 Parcelas: {c['parcelas']}x\n" if c['tipo'] == 'cartao' else "💳 Pagamento via PIX\n") +
            f"⏰ Horário: {c['horario']}\n"
            f"📉 Taxa: {c['taxa']}%\n"
            f"✅ Valor líquido: R$ {c['valor_liquido']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") +
            ("\n✔️ Pago" if c['pago'] else "\n❌ Pendente")
        ))
        return

    # Comando: total geral
    if "total geral" in texto:
        total = sum(c['valor_liquido'] for c in comprovantes)
        total = round(total, 2)
        bot.send_message(chat_id=message.chat_id, text=f"📊 Total geral de todos os comprovantes: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return

    # Entrada manual: "valor tipo"
    match = re.match(r'([\d.,]+)\s*(pix|(\d{1,2})x)', texto)
    if match:
        valor_str = match.group(1).replace(".", "").replace(",", ".")
        tipo = 'pix' if 'pix' in texto else 'cartao'
        parcelas = int(match.group(3)) if tipo == 'cartao' else None
        valor = float(valor_str)
        taxa = 0.2 if tipo == 'pix' else TAXAS_CARTAO.get(parcelas, 0)
        valor_liquido = round(valor * (1 - taxa / 100), 2)

        comprovantes.append({
            'valor': valor,
            'parcelas': parcelas,
            'horario': datetime.now().strftime("%H:%M"),
            'tipo': tipo,
            'taxa': taxa,
            'valor_liquido': valor_liquido,
            'pago': False
        })

        bot.send_message(chat_id=message.chat_id, text=(
            f"📄 Comprovante registrado manualmente:\n"
            f"💰 Valor bruto: R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + "\n" +
            (f"💳 Parcelas: {parcelas}x\n" if tipo == 'cartao' else "") +
            f"⏰ Horário: {datetime.now().strftime('%H:%M')}\n"
            f"📉 Taxa: {taxa}%\n"
            f"✅ Valor líquido: R$ {valor_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        ))
        return

    bot.send_message(chat_id=message.chat_id, text="❌ Comando ou formato não reconhecido. Digite `ajuda` para ver os comandos disponíveis.")

# Funções auxiliares para OCR
def extrair_valor(texto):
    padrao = r'(\d{1,3}(?:[\.,]?\d{3})*[\.,]\d{2})'
    valores = re.findall(padrao, texto)
    if not valores:
        return None
    valor = valores[-1].replace(".", "").replace(",", ".")
    return float(valor)

def extrair_parcelas(texto):
    match = re.search(r'(\d{1,2})x', texto.lower())
    return int(match.group(1)) if match else None

def extrair_horario(texto):
    match = re.search(r'(\d{2}:\d{2})', texto)
    return match.group(1) if match else None
