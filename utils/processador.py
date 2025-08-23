import pytesseract
from PIL import Image
from datetime import datetime
import re

# Tabela de taxas de cartão parcelado (Guimicell)
TAXAS_CREDITO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def extrair_info_ocr(caminho_imagem):
    imagem = Image.open(caminho_imagem)
    texto = pytesseract.image_to_string(imagem, lang='por')

    valor = extrair_valor(texto)
    horario = extrair_horario(texto)
    parcelas = extrair_parcelas(texto)

    return valor, horario, parcelas

def extrair_valor(texto):
    padrao = r'R?\$?\s?(\d{1,3}(?:[.,]?\d{3})*[.,]\d{2})'
    valores = re.findall(padrao, texto)
    if valores:
        valor = valores[0].replace('.', '').replace(',', '.')
        return float(valor)
    return None

def extrair_horario(texto):
    padrao = r'(\d{2}:\d{2})'
    match = re.search(padrao, texto)
    return match.group(1) if match else datetime.now().strftime('%H:%M')

def extrair_parcelas(texto):
    padrao = r'(\d{1,2})x'
    match = re.search(padrao, texto.lower())
    return int(match.group(1)) if match else 1

def aplicar_taxa(valor, parcelas):
    if parcelas == 1:
        taxa = 0.2  # 0.2% para PIX
    else:
        taxa = TAXAS_CREDITO.get(parcelas, 16.84)
    liquido = valor * (1 - taxa / 100)
    return round(liquido, 2), taxa

def processar_comprovante(caminho, context, tipo):
    valor, horario, parcelas = extrair_info_ocr(caminho)

    if tipo == 'manual':
        return None  # será tratado externamente

    valor_liquido, taxa_aplicada = aplicar_taxa(valor, parcelas)

    return {
        'valor_bruto': valor,
        'parcelas': parcelas,
        'horario': horario,
        'taxa': taxa_aplicada,
        'valor_liquido': valor_liquido,
        'pago': False,
        'data': datetime.now().strftime('%d/%m/%Y'),
    }

def salvar_comprovante_manual(valor, parcelas, horario):
    valor_liquido, taxa_aplicada = aplicar_taxa(valor, parcelas)
    return {
        'valor_bruto': valor,
        'parcelas': parcelas,
        'horario': horario or datetime.now().strftime('%H:%M'),
        'taxa': taxa_aplicada,
        'valor_liquido': valor_liquido,
        'pago': False,
        'data': datetime.now().strftime('%d/%m/%Y'),
    }
