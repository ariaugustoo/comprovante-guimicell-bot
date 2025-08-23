import pytesseract
from PIL import Image
import re
from datetime import datetime

# Tabela de taxas atualizada para Guimicell
TAXAS_CARTAO = {
    1: 4.39,
    2: 5.19,
    3: 6.19,
    4: 6.59,
    5: 7.19,
    6: 8.29,
    7: 9.19,
    8: 9.99,
    9: 10.29,
    10: 10.88,
    11: 11.99,
    12: 12.52,
    13: 13.69,
    14: 14.19,
    15: 14.69,
    16: 15.19,
    17: 15.89,
    18: 16.84
}

TAXA_PIX = 0.2  # 0,2% de desconto

# Processa imagem com OCR
def extrair_texto_da_imagem(caminho_imagem):
    imagem = Image.open(caminho_imagem)
    texto = pytesseract.image_to_string(imagem, lang='por')
    return texto

# Extrai valor e parcelas do texto OCR
def extrair_dados_comprovante(texto):
    valor_match = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
    parcelas_match = re.search(r'(\d{1,2}) ?[xX]', texto)

    valor = float(valor_match.group(1).replace('.', '').replace(',', '.')) if valor_match else None
    parcelas = int(parcelas_match.group(1)) if parcelas_match else 1

    return valor, parcelas

# Extrai horário da imagem (ou usa horário atual como fallback)
def extrair_horario(texto):
    horario_match = re.search(r'(\d{2}[:h]\d{2})', texto)
    if horario_match:
        horario = horario_match.group(1).replace('h', ':')
    else:
        horario = datetime.now().strftime('%H:%M')
    return horario

# Calcula o valor líquido a pagar com base nas taxas
def calcular_valor_liquido(valor_bruto, parcelas):
    if parcelas == 1:
        taxa = TAXA_PIX
    else:
        taxa = TAXAS_CARTAO.get(parcelas, 0)

    valor_liquido = valor_bruto * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

# Gera mensagem de resposta formatada
def gerar_resposta(valor_bruto, parcelas, horario, taxa, valor_liquido):
    return f"""📄 Comprovante analisado:
💰 Valor bruto: R$ {valor_bruto:,.2f}
💳 Parcelas: {parcelas}x
⏰ Horário: {horario}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}""".replace('.', ',')

# Função principal
def processar_comprovante(caminho_imagem):
    texto = extrair_texto_da_imagem(caminho_imagem)
    valor, parcelas = extrair_dados_comprovante(texto)
    horario = extrair_horario(texto)

    if valor is None:
        return None, "❌ Não consegui identificar o valor no comprovante. Por favor, envie o valor manualmente no formato 1234,56"

    valor_liquido, taxa = calcular_valor_liquido(valor, parcelas)
    mensagem = gerar_resposta(valor, parcelas, horario, taxa, valor_liquido)
    return valor, mensagem
