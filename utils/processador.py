from datetime import datetime

# Taxas por quantidade de parcelas
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

comprovantes = {}

def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(".", "v").replace(",", ".").replace("v", ",")

def processar_comprovante(caminho_imagem, user_id):
    # (A leitura OCR da imagem pode ser implementada aqui futuramente)
    return "🔍 Leitura OCR ainda não implementada. Envie o valor manualmente: `6438,76 pix` ou `7.899,99 10x`."

def salvar_comprovante_manual(valor_str, parcelas, taxa_pix, user_id):
    try:
        valor = float(valor_str)
    except ValueError:
        return "❌ Valor inválido. Tente no formato: `150,00 3x` ou `6.438,76 pix`"

    if user_id not in comprovantes:
        comprovantes[user_id] = []

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

    if taxa_pix:
        taxa_percentual = taxa_pix
        valor_liquido = round(valor * (1 - taxa_percentual / 100), 2)
        tipo = "PIX"
    else:
        taxa_percentual = TAXAS_CARTAO.get(parcelas, 0)
        valor_liquido = round(valor * (1 - taxa_percentual / 100), 2)
        tipo = f"{parcelas}x no cartão"

    dados = {
        "valor_bruto": valor,
        "parcelas": parcelas,
        "taxa": taxa_percentual,
        "valor_liquido": valor_liquido,
        "data_hora": data_hora,
        "pago": False,
        "tipo": tipo
    }

    comprovantes[user_id].append(dados)

    return f"""
📄 *Comprovante registrado:*
💰 Valor bruto: {formatar_reais(valor)}
💳 Parcelas: {parcelas if not taxa_pix else 'N/A'}
⏰ Horário: {data_hora}
📉 Taxa aplicada: {taxa_percentual:.2f}%
✅ Valor líquido a pagar: {formatar_reais(valor_liquido)}
    """.strip()

def marcar_comprovante_pago(user_id):
    if user_id not in comprovantes or not comprovantes[user_id]:
        return False
    for comprovante in reversed(comprovantes[user_id]):
        if not comprovante["pago"]:
            comprovante["pago"] = True
            return True
    return False

def calcular_total_pendente(user_id):
    if user_id not in comprovantes:
        return 0.0
    return sum(c["valor_liquido"] for c in comprovantes[user_id] if not c["pago"])

def calcular_total_geral(user_id):
    if user_id not in comprovantes:
        return 0.0
    return sum(c["valor_liquido"] for c in comprovantes[user_id])

def listar_comprovantes(user_id, pagos=False):
    if user_id not in comprovantes or not comprovantes[user_id]:
        return "📂 Nenhum comprovante encontrado."

    lista = [c for c in comprovantes[user_id] if c["pago"] == pagos]
    if not lista:
        return "📂 Nenhum comprovante encontrado neste status."

    status = "✅ *Pagos*" if pagos else "🕒 *Pendentes*"
    mensagem = [f"{status}:\n"]
    for i, c in enumerate(lista, 1):
        mensagem.append(
            f"*{i}. {c['tipo']}*\n"
            f"💰 {formatar_reais(c['valor_bruto'])} → {formatar_reais(c['valor_liquido'])}\n"
            f"📉 {c['taxa']:.2f}% | ⏰ {c['data_hora']}\n"
        )
    return "\n".join(mensagem)

def get_ultimo_comprovante(user_id):
    if user_id not in comprovantes or not comprovantes[user_id]:
        return "📂 Nenhum comprovante encontrado."

    c = comprovantes[user_id][-1]
    return f"""
📌 *Último Comprovante:*
💰 Valor bruto: {formatar_reais(c['valor_bruto'])}
💳 Parcelas: {c['parcelas'] if c['tipo'] != 'PIX' else 'N/A'}
⏰ Horário: {c['data_hora']}
📉 Taxa aplicada: {c['taxa']:.2f}%
✅ Valor líquido a pagar: {formatar_reais(c['valor_liquido'])}
🧾 Status: {'✅ Pago' if c['pago'] else '🕒 Pendente'}
""".strip()
