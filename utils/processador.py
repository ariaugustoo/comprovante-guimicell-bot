import re
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from datetime import datetime

# Dicionário de taxas por número de parcelas
TAXAS_CARTAO_GUIMICELL = {
    1: 0.0439,
    2: 0.0519,
    3: 0.0619,
    4: 0.0699,
    5: 0.0779,
    6: 0.0859,
    7: 0.0899,
    8: 0.0939,
    9: 0.0999,
    10: 0.1039,
    11: 0.1079,
    12: 0.1119,
    13: 0.1159,
    14: 0.1199,
    15: 0.1239,
    16: 0.1279,
    17: 0.1319,
    18: 0.1359
}

def extrair_texto_comprovante(path_arquivo):
    if path_arquivo.lower().endswith('.pdf'):
        imagens = convert_from_path(path_arquivo)
        texto = ''
        for imagem in imagens:
            texto += pytesseract.image_to_string(imagem, lang='por')
        return texto
    else:
        imagem = Image.open(path_arquivo)
        return pytesseract.image_to_string(imagem, lang='por')

def extrair_dados(texto):
    # Extrai valor com R$ ou sem R$
    valor_match = re.search(r'R?\$?\s?(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', texto)
    valor = None
    if valor_match:
        valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
        valor = float(valor_str)

    # Extrai quantidade de parcelas
    parcelas_match = re.search(r'(\d{1,2})x', texto.lower())
    parcelas = int(parcelas_match.group(1)) if parcelas_match else 1

    # Extrai horário (padrão HH:MM ou HH:MM:SS)
    hora_match = re.search(r'\b(\d{2}:\d{2}(?::\d{2})?)\b', texto)
    hora = hora_match.group(1) if hora_match else None

    return valor, parcelas, hora

def calcular_valor_liquido(valor_bruto, parcelas):
    taxa = TAXAS_CARTAO_GUIMICELL.get(parcelas, 0.0)
    valor_liquido = round(valor_bruto * (1 - taxa), 2)
    return valor_liquido, taxa

def processar_comprovante(path_arquivo):
    texto_extraido = extrair_texto_comprovante(path_arquivo)
    valor, parcelas, hora = extrair_dados(texto_extraido)

    if valor is None:
        return {
            "erro": "Não foi possível identificar o valor no comprovante."
        }

    valor_liquido, taxa_aplicada = calcular_valor_liquido(valor, parcelas)

    return {
        "valor_bruto": valor,
        "parcelas": parcelas,
        "hora": hora or datetime.now().strftime("%H:%M"),
        "taxa_aplicada": taxa_aplicada,
        "valor_liquido": valor_liquido,
        "texto_extraido": texto_extraido
    }
