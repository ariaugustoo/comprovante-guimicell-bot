import re
from datetime import datetime, timedelta
from pytz import timezone

# Banco de dados em memória
comprovantes = []
solicitacoes_pagamento = []

# Constantes
TAXA_PIX = 0.002
TAXAS_CARTAO = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719,
    6: 0.0829, 7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088,
    11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
    16: 0.1519, 17: 0.1589, 18: 0.1684,
}

ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

def normalizar_valor(texto):
    try:
        texto = texto.lower().replace("r$", "").replace(" ", "").replace(",", ".")
        numeros = re.findall(r'\d+\.?\d*', texto)
        return float(numeros[0]) if numeros else None
    except:
        return None

def obter_horario():
    fuso_brasilia = timezone("America/Sao_Paulo")
    return datetime.now(fuso_brasilia).strftime("%H:%M")

def registrar_comprovante(valor, tipo, parcelas=1):
    taxa = TAXA_PIX if tipo == "PIX" else TAXAS_CARTAO.get(parcelas, 0)
    valor_liquido = round(valor * (1 - taxa), 2)
    comprovantes.append({
        "valor_bruto": valor,
        "tipo": tipo,
        "parcelas": parcelas,
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "pago": False,
        "horario": obter_horario()
    })
    return {
        "valor_bruto": valor,
        "tipo": tipo,
        "parcelas": parcelas,
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "horario": obter_horario()
    }

def marcar_como_pago(valor=None):
    if solicitacoes_pagamento and valor:
        valor_restante = valor
        for c in comprovantes:
            if not c["pago"] and valor_restante >= c["valor_liquido"]:
                c["pago"] = True
                valor_restante -= c["valor_liquido"]
            elif not c["pago"] and valor_restante > 0:
                c["valor_liquido"] -= valor_restante
                valor_restante = 0
                break
        solicitacoes_pagamento.clear()
    else:
        for c in comprovantes:
            if not c["pago"]:
                c["pago"] = True

def total_pendentes():
    return round(sum(c["valor_liquido"] for c in comprovantes if not c["pago"]), 2)

def total_bruto_pendentes():
    return round(sum(c["valor_bruto"] for c in comprovantes if not c["pago"]), 2)

def listar_comprovantes(pagos=False):
    lista = [c for c in comprovantes if c["pago"] == pagos]
    if not lista:
        return "Nenhum comprovante encontrado."
    linhas = []
    for i, c in enumerate(lista, 1):
        linhas.append(f"📄 Comprovante {i} | 💰 R$ {c['valor_bruto']:.2f} | 💳 {c['tipo']} | ⏰ {c['horario']}")
    return "\n".join(linhas)

def solicitar_pagamento(valor, chave_pix):
    solicitacoes_pagamento.append({
        "valor": valor,
        "chave": chave_pix
    })
    return f"📌 Pagamento solicitado:\n💰 Valor: R$ {valor:.2f}\n🔑 Chave Pix: {chave_pix}"

def corrigir_valor(index, novo_valor):
    try:
        c = comprovantes[index]
        taxa = TAXA_PIX if c["tipo"] == "PIX" else TAXAS_CARTAO.get(c["parcelas"], 0)
        c["valor_bruto"] = novo_valor
        c["valor_liquido"] = round(novo_valor * (1 - taxa), 2)
        return True
    except:
        return False

def limpar_tudo():
    comprovantes.clear()
    solicitacoes_pagamento.clear()

def ajuda():
    return (
        "📌 Comandos disponíveis:\n"
        "1️⃣ Enviar comprovante:\n   Ex: `1000 pix` ou `2000 3x`\n"
        "2️⃣ pagamento feito – marca como pago ✅\n"
        "3️⃣ quanto devo – valor líquido pendente\n"
        "4️⃣ total a pagar – valor bruto pendente\n"
        "5️⃣ listar pendentes – lista comprovantes não pagos\n"
        "6️⃣ listar pagos – lista comprovantes pagos\n"
        "7️⃣ solicitar pagamento – informe valor + chave Pix\n"
        "🔒 8️⃣ limpar tudo – (admin)\n"
        "🔒 9️⃣ corrigir valor – (admin)"
    )
