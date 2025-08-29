import re
from datetime import datetime, timedelta
import pytz

# Dicionário para armazenar os comprovantes
comprovantes = []
solicitacoes_pagamento = []

# Tabela de taxas por parcela
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19,
    6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88,
    11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19,
    15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

# Função para processar mensagens recebidas
def processar_mensagem(texto, horario_brasilia):
    texto = texto.lower().replace(",", ".")
    padrao_pix = re.search(r"([\d.]+)\s*pix", texto)
    padrao_cartao = re.search(r"([\d.]+)\s*(\d{1,2})x", texto)

    if padrao_pix:
        valor = float(padrao_pix.group(1))
        taxa = 0.2
        liquido = valor * (1 - taxa / 100)
        comprovantes.append({
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "horario": horario_brasilia.strftime("%H:%M"),
            "tipo": "PIX",
            "taxa": taxa,
            "pago": False
        })
        return (f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💰 Tipo: PIX\n"
                f"⏰ Horário: {horario_brasilia.strftime('%H:%M')}\n"
                f"📉 Taxa aplicada: {taxa}%\n"
                f"✅ Valor líquido a pagar: R$ {liquido:,.2f}")

    elif padrao_cartao:
        valor = float(padrao_cartao.group(1))
        parcelas = int(padrao_cartao.group(2))
        taxa = taxas_cartao.get(parcelas, 0)
        liquido = valor * (1 - taxa / 100)
        comprovantes.append({
            "valor_bruto": valor,
            "valor_liquido": liquido,
            "horario": horario_brasilia.strftime("%H:%M"),
            "tipo": f"{parcelas}x",
            "taxa": taxa,
            "pago": False
        })
        return (f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💰 Tipo: Cartão ({parcelas}x)\n"
                f"⏰ Horário: {horario_brasilia.strftime('%H:%M')}\n"
                f"📉 Taxa aplicada: {taxa}%\n"
                f"✅ Valor líquido a pagar: R$ {liquido:,.2f}")
    
    return None

def calcular_total_liquido_pendente():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    return f"💰 Devo ao lojista: R$ {total:,.2f}"

def calcular_total_bruto_pendente():
    total = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
    return f"💰 Total a pagar (sem desconto): R$ {total:,.2f}"

def listar_comprovantes(pagos=False):
    lista = [c for c in comprovantes if c["pago"] == pagos]
    if not lista:
        return "Nenhum comprovante encontrado."
    resposta = ""
    for c in lista:
        resposta += (f"💰 R$ {c['valor_bruto']:,.2f} | "
                     f"{c['tipo']} | "
                     f"⏰ {c['horario']}\n")
    total = sum(c["valor_bruto"] for c in lista)
    status = "✅ Pagos" if pagos else "⏳ Pendentes"
    resposta += f"\n📊 Total {status}: R$ {total:,.2f}"
    return resposta

def marcar_como_pago():
    for s in solicitacoes_pagamento:
        for c in comprovantes:
            if not c["pago"] and s <= c["valor_liquido"]:
                c["valor_liquido"] -= s
                if c["valor_liquido"] <= 0.01:
                    c["pago"] = True
                solicitacoes_pagamento.remove(s)
                return f"✅ Pagamento de R$ {s:,.2f} registrado com sucesso!"
    return "⚠️ Nenhum valor pendente compatível com o pagamento."

def registrar_solicitacao_pagamento(valor_str):
    try:
        valor = float(valor_str.replace(",", "."))
        solicitacoes_pagamento.append(valor)
        return f"📥 Pagamento solicitado de R$ {valor:,.2f}. Envie a chave Pix."
    except:
        return "❌ Valor inválido. Tente novamente."

def listar_pagamentos():
    return listar_comprovantes(pagos=True)