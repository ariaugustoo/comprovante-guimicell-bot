from datetime import datetime
import re

comprovantes = []
solicitacoes_pagamento = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def parse_valor(texto):
    try:
        texto = texto.replace(".", "").replace(",", ".")
        return float(re.findall(r'\d+\.?\d*', texto)[0])
    except:
        return None

def processar_mensagem(texto):
    texto = texto.lower()
    valor = parse_valor(texto)
    parcelas = None
    taxa = 0
    tipo = ""
    
    if "pix" in texto:
        taxa = 0.2
        tipo = "PIX"
    elif "x" in texto:
        match = re.search(r'(\d{1,2})x', texto)
        if match:
            parcelas = int(match.group(1))
            taxa = taxas_cartao.get(parcelas, 0)
            tipo = f"Cartão {parcelas}x"
    
    if valor is None or taxa == 0 and not tipo:
        return "❌ Não entendi o comprovante. Envie no formato: `1000 pix` ou `1500 3x`."

    valor_liquido = round(valor * (1 - taxa / 100), 2)
    hora = datetime.now().strftime("%H:%M")

    comprovantes.append({
        "valor_bruto": valor,
        "valor_liquido": valor_liquido,
        "parcelas": parcelas,
        "tipo": tipo,
        "horario": hora,
        "pago": False
    })

    return (
        f"📄 Comprovante analisado:\n"
        f"💰 Valor bruto: R$ {valor:,.2f}\n"
        f"💰 Tipo: {tipo}\n"
        f"⏰ Horário: {hora}\n"
        f"📉 Taxa aplicada: {taxa}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )

def marcar_como_pago():
    for c in comprovantes:
        if not c["pago"]:
            c["pago"] = True
            return f"✅ Comprovante de R$ {c['valor_liquido']:,.2f} marcado como pago."
    return "ℹ️ Nenhum comprovante pendente para marcar como pago."

def quanto_devo():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    return f"💰 Devo ao lojista: R$ {total:,.2f}"

def total_a_pagar():
    total = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
    return f"💰 Total a pagar (sem desconto): R$ {total:,.2f}"
