import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import os
import tempfile


def extrair_dados_texto(texto):
    valor_match = re.search(r'R\$\s?([0-9\.,]+)', texto)
    valor = float(valor_match.group(1).replace('.', '').replace(',', '.')) if valor_match else 0.0

    horario_match = re.search(r'(\d{2}:\d{2}:\d{2})', texto)
    horario = horario_match.group(1) if horario_match else '00:00:00'

    parcelas_match = re.search(r'(\d{1,2})x', texto)
    parcelas = int(parcelas_match.group(1)) if parcelas_match else 1

    return valor, horario, parcelas


def aplicar_taxa(valor, parcelas):
    # Tabela de taxas
    taxas = {
        1: 4.39, 2: 5.19, 3: 6.19, 4: 7.09, 5: 7.99, 6: 8.89,
        7: 9.79, 8: 10.69, 9: 11.59, 10: 12.49, 11: 13.39,
        12: 14.29, 13: 15.19, 14: 16.09, 15: 16.99, 16: 17.89,
        17: 18.79, 18: 19.69
    }

    taxa = taxas.get(parcelas, 0)
    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa


def processar_comprovante(file_path):
    texto_extraido = ""

    # Detecta extensão e processa
    _, ext = os.path.splitext(file_path)

    try:
        if ext.lower() == '.pdf':
            imagens = convert_from_path(file_path)
            for img in imagens:
                texto_extraido += pytesseract.image_to_string(img, lang='por')
        else:
            img = Image.open(file_path)
            texto_extraido = pytesseract.image_to_string(img, lang='por')

        valor, horario, parcelas = extrair_dados_texto(texto_extraido)
        valor_liquido, taxa = aplicar_taxa(valor, parcelas)

        return {
            "valor_bruto": valor,
            "horario": horario,
            "parcelas": parcelas,
            "taxa": taxa,
            "valor_liquido": valor_liquido
        }

    except Exception as e:
        return {"erro": str(e)}
