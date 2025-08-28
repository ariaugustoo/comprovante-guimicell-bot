import re
from datetime import datetime, timedelta
import pytz

# Taxas por parcelas
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}

taxa_pix = 0.2

# Listas globais
comprovantes = []
pagamentos = []

def normalizar_valor(valor_str):
    valor_str = valor_str.replace('.', '').replace(',', '.')
    return float(valor_str)

def processar_mensagem(mensagem, nome_usuario):
    mensagem = mensagem.strip().lower()

    # Pagamento feito
    if "pagamento feito" in mensagem:
        if comprovantes:
            ultimo = [c for c in comprovantes if c["id"] not in [p["id"] for p in pagamentos]]
            if ultimo:
                comprovante = ultimo[-1]
                pagamentos.append({
                    "id": comprovante["id"],
                    "valor": comprovante["liquido"]
                })
                return f"✅ Pagamento registrado para R$ {comprovante['liquido']:.2f}."
            return "❌ Nenhum comprovante pendente para marcar como pago."
        return "❌ Nenhum comprovante encontrado."

    # Total líquido pendente
    if "total líquido" in mensagem:
        total = sum(c["liquido"] for c in comprovantes if c["id"] not in [p["id"] for p in pagamentos])
        return f"💰 <b>Total líquido a pagar:</b> R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Total bruto pendente
    if "total a pagar" in mensagem:
        total = sum(c["valor"] for c in comprovantes if c["id"] not in [p["id"] for p in pagamentos])
        return f"💵 <b>Total bruto dos comprovantes pendentes:</b> R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Solicitação de pagamento parcial
    if mensagem.startswith("solicitar pagamento"):
        partes = mensagem.split()
        if len(partes) >= 3:
            try:
                valor = normalizar_valor(partes[2])
                pagamentos.append({
                    "id": f"manual_{len(pagamentos)+1}",
                    "valor": valor
                })
                return f"📬 <b>Solicitação de Pagamento:</b> 💸 Valor: R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            except:
                return "❌ Valor inválido. Tente algo como: solicitar pagamento 300,00"
        else:
            return "❌ Formato inválido. Use: solicitar pagamento 300,00"

    # Padrões de entrada: valor pix ou valor Xx
    match_pix = re.search(r'([\d.,]+)\s*pix', mensagem)
    match_cartao = re.search(r'([\d.,]+)\s*(\d{1,2})x', mensagem)

    fuso_brasilia = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(fuso_brasilia).strftime("%H:%M")

    if match_pix:
        try:
            valor = normalizar_valor(match_pix.group(1))
            taxa = taxa_pix
            liquido = round(valor * (1 - taxa / 100), 2)
            id_comprovante = f"{len(comprovantes)+1}_pix"
            comprovantes.append({
                "id": id_comprovante,
                "valor": valor,
                "liquido": liquido
            })
            return (
                f"🧾 <b>Comprovante analisado:</b>\n"
                f"💰 <b>Valor bruto:</b> R$ {valor:,.2f}\n"
                f"💲 <b>Tipo:</b> PIX\n"
                f"⏰ <b>Horário:</b> {agora}\n"
                f"📉 <b>Taxa aplicada:</b> {taxa:.2f}%\n"
                f"✅ <b>Valor líquido a pagar:</b> R$ {liquido:,.2f}"
            ).replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return "❌ Valor inválido para PIX."

    elif match_cartao:
        try:
            valor = normalizar_valor(match_cartao.group(1))
            parcelas = int(match_cartao.group(2))
            if parcelas not in taxas_cartao:
                return "❌ Número de parcelas não suportado (1x a 18x)."
            taxa = taxas_cartao[parcelas]
            liquido = round(valor * (1 - taxa / 100), 2)
            id_comprovante = f"{len(comprovantes)+1}_{parcelas}x"
            comprovantes.append({
                "id": id_comprovante,
                "valor": valor,
                "liquido": liquido
            })
            return (
                f"🧾 <b>Comprovante analisado:</b>\n"
                f"💰 <b>Valor bruto:</b> R$ {valor:,.2f}\n"
                f"💲 <b>Tipo:</b> Cartão ({parcelas}x)\n"
                f"⏰ <b>Horário:</b> {agora}\n"
                f"📉 <b>Taxa aplicada:</b> {taxa:.2f}%\n"
                f"✅ <b>Valor líquido a pagar:</b> R$ {liquido:,.2f}"
            ).replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return "❌ Valor inválido para cartão."

    # Ajuda
    if "ajuda" in mensagem:
        return (
            "📌 <b>Comandos disponíveis:</b>\n"
            "➡️ 100 pix → registra PIX\n"
            "➡️ 1234,56 10x → registra Cartão\n"
            "➡️ pagamento feito → marca último como pago\n"
            "➡️ total líquido → soma dos não pagos\n"
            "➡️ total a pagar → valor bruto pendente\n"
            "➡️ solicitar pagamento 300,00 → abate valor\n"
        )

    return "❌ Formato inválido. Use por exemplo: 100 pix ou 1234,56 3x"
