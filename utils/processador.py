import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import re

# Tabelas de taxas simuladas (Guimicell)
TAXAS = {
    1: 0.0439,
    2: 0.0519,
    3: 0.0619,
    4: 0.0729,
    5: 0.0839,
    6: 0.0949,
    7: 0.1059,
    8: 0.1169,
    9: 0.1279,
    10: 0.1389,
    11: 0.1499,
    12: 0.1609,
    13: 0.1719,
    14: 0.1829,
    15: 0.1939,
    16: 0.2040,
    17: 0.2159,
    18: 0.2269,
}

def extrair_texto(caminho):
    if caminho.endswith('.pdf'):
        imagens = convert_from_path(caminho)
        texto = ""
        for img in imagens:
            texto += pytesseract.image_to_string(img)
        return texto
    else:
        img = Image.open(caminho)
        return pytesseract.image_to_string(img)

def processar_comprovante(caminho):
    try:
        texto = extrair_texto(caminho)

        # Extrair valor com vírgula ou ponto
        valor_match = re.search(r'([\d\.]+,\d{2})', texto)
        valor_str = valor_match.group(1).replace('.', '').replace(',', '.') if valor_match else None
        valor_bruto = float(valor_str) if valor_str else None

        # Extrair número de parcelas (ex: "6 PARCELAS" ou "EM 6X")
        parcelas_match = re.search(r'(\d{1,2})\s*(PARCELAS|X|x)', texto)
        parcelas = int(parcelas_match.group(1)) if parcelas_match else 1

        # Extrair horário (ex: 15:47 ou 09:32)
        hora_match = re.search(r'(\d{2}:\d{2})', texto)
        hora = hora_match.group(1) if hora_match else "Não encontrado"

        # Definir taxa com base nas parcelas
        taxa_aplicada = TAXAS.get(parcelas, 0.10)  # taxa padrão 10% se não encontrar

        # Calcular valor líquido
        valor_liquido = valor_bruto * (1 - taxa_aplicada) if valor_bruto else 0.0

        return {
            "valor_bruto": valor_bruto,
            "parcelas": parcelas,
            "hora": hora,
            "taxa_aplicada": taxa_aplicada,
            "valor_liquido": valor_liquido
        }

    except Exception as e:
        return {"erro": f"Erro ao processar o comprovante: {str(e)}"}
