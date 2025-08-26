import re
from datetime import datetime
from PIL import Image
import pytesseract

comprovantes = []

# Tabela de taxas por número de parcelas (crédito)
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99,
    12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}

# Função para normalizar valores
def normalizar_valor(texto):
    texto = texto.replace(' ', '').replace('R$', '').replace('r$', '')
    texto = texto.replace('.', '').replace(',', '.')
    try:
        return float(texto)
    except ValueError:
        return None

# OCR para extrair texto da imagem
def extrair_info_ocr(caminho):
    imagem = Image.open(caminho)
    texto = pytesseract.image_to_string(imagem, lang='por')
    return extrair_valores_texto(texto)

# Função para extrair valor, horário e parcelas de um texto OCR ou mensagem
def extrair_valores_texto(texto):
    texto = texto.replace('x', 'x ').replace('X', 'x ')  # segurança

    # Expressões regulares para capturar valor e parcelas
    valor_match = re.search(r'(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', texto)
    parcelas_match = re.search(r'(\d{1,2})\s*x', texto.lower())

    valor = normalizar_valor(valor_match.group(1)) if valor_match else None
    parcelas = int(parcelas_match.group(1)) if parcelas_match else 1

    horario = datetime.now().strftime('%H:%M')
    return valor, horario, parcelas

# Detectar tipo de pagamento e aplicar taxa
def calcular_liquido(valor, parcelas=1, tipo='cartao'):
    if tipo == 'pix':
        taxa = 0.2
    else:
        taxa = TAXAS_CARTAO.get(parcelas, 0)

    valor_liquido = round(valor * (1 - taxa / 100), 2)
    return taxa, valor_liquido

# Registrar comprovante vindo de OCR
def processar_comprovante(caminho_imagem):
    valor, horario, parcelas = extrair_info_ocr(caminho_imagem)
    if not valor:
        return None
    taxa, valor_liquido = calcular_liquido(valor, parcelas)
    comprovante = {
        'valor': valor,
        'parcelas': parcelas,
        'horario': horario,
        'taxa': taxa,
        'valor_liquido': valor_liquido,
        'status': 'pendente'
    }
    comprovantes.append(comprovante)
    return comprovante

# Registrar comprovante manual
def salvar_comprovante_manual(texto):
    texto = texto.lower().strip()
    valor, horario, parcelas = extrair_valores_texto(texto)

    if not valor:
        return None

    if 'pix' in texto:
        tipo = 'pix'
        parcelas = 1
    else:
        tipo = 'cartao'

    taxa, valor_liquido = calcular_liquido(valor, parcelas, tipo)

    comprovante = {
        'valor': valor,
        'parcelas': parcelas,
        'horario': horario,
        'taxa': taxa,
        'valor_liquido': valor_liquido,
        'status': 'pendente'
    }
    comprovantes.append(comprovante)
    return comprovante

# Marcar comprovante como pago (último pendente)
def marcar_comprovante_pago():
    for comprovante in reversed(comprovantes):
        if comprovante['status'] == 'pendente':
            comprovante['status'] = 'pago'
            return comprovante
    return None

# Calcular total em aberto
def calcular_total_pendente():
    return round(sum(c['valor_liquido'] for c in comprovantes if c['status'] == 'pendente'), 2)

# Calcular total geral
def calcular_total_geral():
    return round(sum(c['valor_liquido'] for c in comprovantes), 2)

# Listar comprovantes pendentes/pagos
def listar_comprovantes(status='pendente'):
    return [c for c in comprovantes if c['status'] == status]

# Obter último comprovante
def get_ultimo_comprovante():
    return comprovantes[-1] if comprovantes else None
