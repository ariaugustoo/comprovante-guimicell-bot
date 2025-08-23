import re
from datetime import datetime
from PIL import Image
import pytesseract
import io

# Lista global de comprovantes
comprovantes = []

# Tabela de taxas de cartão
taxas_cartao = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719, 6: 0.0829,
    7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088, 11: 0.1199, 12: 0.1252,
    13: 0.1369, 14: 0.1419, 15: 0.1469, 16: 0.1519, 17: 0.1589, 18: 0.1684
}

# Função para processar imagem via OCR
def processar_comprovante(file_bytes):
    image = Image.open(io.BytesIO(file_bytes))
    texto = pytesseract.image_to_string(image)

    valor_match = re.search(r'(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', texto)
    valor = float(valor_match.group(1).replace('.', '').replace(',', '.')) if valor_match else None

    hora_match = re.search(r'(\d{2}:\d{2})', texto)
    hora = hora_match.group(1) if hora_match else datetime.now().strftime("%H:%M")

    parcelas_match = re.search(r'(\d{1,2})x', texto.lower())
    parcelas = int(parcelas_match.group(1)) if parcelas_match else 1

    if valor is None:
        raise ValueError("Valor não identificado no comprovante.")

    taxa = taxas_cartao.get(parcelas, 0.0)
    valor_liquido = round(valor * (1 - taxa), 2)

    comprovante = {
        "valor": valor,
        "parcelas": parcelas,
        "hora": hora,
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "pago": False
    }
    comprovantes.append(comprovante)
    return comprovante

# Função para salvar comprovante manual (PIX ou texto)
def salvar_comprovante_manual(valor, tipo, parcelas=1):
    taxa = 0.002 if tipo == "pix" else taxas_cartao.get(parcelas, 0.0)
    valor_liquido = round(valor * (1 - taxa), 2)

    comprovante = {
        "valor": valor,
        "parcelas": parcelas,
        "hora": datetime.now().strftime("%H:%M"),
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "pago": False
    }
    comprovantes.append(comprovante)
    return comprovante

# Marcar comprovante como pago
def marcar_comprovante_pago():
    for c in reversed(comprovantes):
        if not c["pago"]:
            c["pago"] = True
            return c
    return None

# Calcular total pendente
def calcular_total_pendente():
    return round(sum(c["valor_liquido"] for c in comprovantes if not c["pago"]), 2)

# Calcular total geral
def calcular_total_geral():
    return round(sum(c["valor_liquido"] for c in comprovantes), 2)

# Listar comprovantes pagos ou pendentes
def listar_comprovantes(pagos=False):
    return [c for c in comprovantes if c["pago"] == pagos]

# Obter último comprovante
def get_ultimo_comprovante():
    return comprovantes[-1] if comprovantes else None
