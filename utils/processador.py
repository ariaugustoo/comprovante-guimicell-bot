import re

def extrair_dados_texto(texto):
    """Extrai valor, hora, forma de pagamento e número de parcelas (se houver) do texto OCR."""
    texto = texto.lower()

    # Valor (ex: R$ 1.200,50 ou 1200,50)
    padrao_valor = re.search(r'(r?\$?\s?[\d\.]+\s?,\s?\d{2})', texto)
    valor = padrao_valor.group(1).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".") if padrao_valor else None

    # Hora (ex: 14:35 ou 09:02:33)
    padrao_hora = re.search(r'(\d{2}:\d{2}(?::\d{2})?)', texto)
    hora = padrao_hora.group(1) if padrao_hora else None

    # Forma de pagamento
    if 'crédito' in texto or 'credito' in texto:
        forma_pagamento = 'crédito'
    elif 'débito' in texto or 'debito' in texto:
        forma_pagamento = 'débito'
    elif 'pix' in texto:
        forma_pagamento = 'pix'
    elif 'dinheiro' in texto:
        forma_pagamento = 'dinheiro'
    else:
        forma_pagamento = 'indefinido'

    # Parcelas (ex: 3x, 10x)
    padrao_parcelas = re.search(r'(\d{1,2})x', texto)
    parcelas = int(padrao_parcelas.group(1)) if padrao_parcelas else 1 if forma_pagamento == 'crédito' else 0

    return {
        'valor': float(valor) if valor else None,
        'hora': hora,
        'forma_pagamento': forma_pagamento,
        'parcelas': parcelas
    }