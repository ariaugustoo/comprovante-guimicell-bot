import pytesseract
from PIL import Image
from pdf2image import convert_from_path

import re

# Tabelas de taxas simuladas (exemplo Guimicell)
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
    16: 0.2049,
    17: 0.2159,
    18: 0.2269,
}

def extrair_texto(path: str) -> str:
    if path.lower().endswith(".pdf"):
        imagens = convert_from_path(path)
        texto = "\n".join([pytesseract.image_to_string(img) for img in imagens])
    else:
        imagem = Image.open(path)
        texto = pytesseract.image_to_string(imagem)

    return texto

def processar_comprovante(path: str) -> dict:
    try:
        texto = extrair_texto(path)

        # Extrai valor
        match_valor = re.search(r"([\d\.]+,\d{2})", texto)
        valor_bruto = float(match_valor.group(1).replace('.', '').replace(',', '.')) if match_valor else 0.0

        # Extrai parcelas
        match_parcelas = re.search(r"(\d{1,2})x", texto, re.IGNORECASE)
        parcelas = int(match_parcelas.group(1)) if match_parcelas else 1

        # Extrai hora
        match_hora = re.search(r"\b(\d{2}:\d{2})\b", texto)
        hora = match_hora.group(1) if match_hora else "00:00"

        # Pega taxa pela quantidade de parcelas
        taxa = TAXAS.get(parcelas, 0.04)  # taxa padrão de 4% se não encontrado

        valor_liquido = valor_bruto * (1 - taxa)

        return {
            "valor_bruto": valor_bruto,
            "parcelas": parcelas,
            "hora": hora,
            "taxa_aplicada": taxa,
            "valor_liquido": valor_liquido
        }

    except Exception as e:
        return {"erro": f"Erro ao processar comprovante: {str(e)}"}
