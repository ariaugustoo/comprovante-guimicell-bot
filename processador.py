from datetime import datetime, timedelta
import pytz

# Estrutura da memória
comprovantes = []
solicitacoes_pagamento = []

# Timezone de Brasília
fuso_brasilia = pytz.timezone("America/Sao_Paulo")

# Tabela de taxas por parcela
taxas_cartao = {
    i: taxa for i, taxa in enumerate([
        4.39, 5.19, 6.19, 6.59, 7.19, 8.29, 9.19,
        9.99, 10.29, 10.88, 11.99, 12.52, 13.69,
        14.19, 14.69, 15.19, 15.89, 16.84
    ], start=1)
}

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def extrair_info_mensagem(mensagem):
    texto = mensagem.lower().replace("r$", "").replace(",", ".").replace("pix", "").replace("x", "").strip()
    partes = texto.split()
    try:
        valor = float(partes[0])
    except:
        return None, None
    if "pix" in mensagem.lower():
        return valor, "pix"
    for i in range(1, 19):
        if f"{i}x" in mensagem.lower():
            return valor, f"{i}x"
    return valor, None

def adicionar_comprovante(valor, tipo):
    agora = datetime.now(fuso_brasilia).strftime("%H:%M")
    taxa = 0.2 if tipo == "pix" else taxas_cartao.get(int(tipo.replace("x", "")), 0)
    valor_liquido = round(valor * (1 - taxa / 100), 2)
    comprovantes.append({
        "valor_bruto": valor,
        "tipo": tipo,
        "hora": agora,
        "pago": False,
        "taxa": taxa,
        "valor_liquido": valor_liquido
    })
    return {
        "valor_bruto": formatar_valor(valor),
        "tipo": tipo.upper(),
        "hora": agora,
        "taxa": f"{taxa:.2f}%",
        "valor_liquido": formatar_valor(valor_liquido)
    }

def marcar_como_pago(valor_pago=None):
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "Nenhum comprovante pendente."
    if valor_pago:
        valor_pago = round(valor_pago, 2)
        for c in pendentes:
            if not c["pago"] and c["valor_liquido"] > 0:
                if valor_pago >= c["valor_liquido"]:
                    valor_pago -= c["valor_liquido"]
                    c["pago"] = True
                    c["valor_liquido"] = 0
                else:
                    c["valor_liquido"] -= valor_pago
                    valor_pago = 0
                    break
        return "✅ Pagamento parcial registrado com sucesso."
    else:
        pendentes[0]["pago"] = True
        return "✅ Comprovante marcado como pago."

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."
    resposta = "📋 *Comprovantes Pendentes:*\n"
    for i, c in enumerate(pendentes, 1):
        resposta += f"{i}. 💰 {formatar_valor(c['valor_liquido'])} | ⏰ {c['hora']} | Tipo: {c['tipo'].upper()}\n"
    return resposta

def listar_pagamentos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "Nenhum comprovante pago ainda."
    resposta = "✅ *Comprovantes Pagos:*\n"
    for i, c in enumerate(pagos, 1):
        resposta += f"{i}. 💰 {formatar_valor(c['valor_bruto'])} | ⏰ {c['hora']} | Tipo: {c['tipo'].upper()}\n"
    return resposta

def limpar_tudo():
    comprovantes.clear()
    return "🧹 Todos os dados foram limpos."

def corrigir_valor(indice, novo_valor):
    try:
        c = comprovantes[indice - 1]
        tipo = c['tipo']
        taxa = 0.2 if tipo == "pix" else taxas_cartao.get(int(tipo.replace("x", "")), 0)
        valor_liquido = round(novo_valor * (1 - taxa / 100), 2)
        c.update({
            "valor_bruto": novo_valor,
            "taxa": taxa,
            "valor_liquido": valor_liquido
        })
        return "✅ Valor corrigido com sucesso."
    except:
        return "❌ Erro ao corrigir o valor. Verifique o número informado."

def quanto_devo():
    total = sum(c['valor_liquido'] for c in comprovantes if not c["pago"])
    return f"💰 Devo ao lojista: {formatar_valor(total)}"

def total_bruto_pendentes():
    total = sum(c['valor_bruto'] for c in comprovantes if not c["pago"])
    return f"💵 Total a pagar (bruto): {formatar_valor(total)}"

def solicitar_pagamento(valor, chave_pix):
    solicitacoes_pagamento.append({
        "valor": valor,
        "chave_pix": chave_pix,
        "data": datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M")
    })
    return f"🧾 Solicitação registrada com sucesso.\n💸 Valor: {formatar_valor(valor)}\n🔑 Chave Pix: {chave_pix}"

def ajuda():
    return (
        "🛠 *Comandos disponíveis:*\n"
        "• Envie um valor + pix (ex: 1549,99 pix)\n"
        "• Envie um valor + parcelas (ex: 2000 6x)\n"
        "• pagamento feito – marca como pago (parcial ou total)\n"
        "• quanto devo – mostra valor líquido a repassar\n"
        "• total a pagar – mostra valor bruto total\n"
        "• listar pendentes – lista comprovantes abertos\n"
        "• listar pagos – lista os já pagos\n"
        "• solicitar pagamento – lojista envia valor e chave Pix\n"
        "• limpar tudo – limpa todos os dados (admin)\n"
        "• corrigir valor – corrige valor de um comprovante (admin)"
    )
