import datetime
import re
from pytz import timezone

# Dados em memória
comprovantes = []
pagamentos_parciais = []
solicitacoes_pagamento = []

# Taxas de cartão por parcela (1x a 18x)
TAXAS_CARTAO = {
    1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719,
    6: 0.0829, 7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088,
    11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
    16: 0.1519, 17: 0.1589, 18: 0.1684
}

def parse_valor(valor_raw):
    if isinstance(valor_raw, (int, float)):
        return float(valor_raw)
    valor = re.sub(r"[^\d,\.]", "", valor_raw)
    valor = valor.replace('.', '').replace(',', '.')
    try:
        return float(valor)
    except:
        return None

def hora_atual_brasil():
    fuso = timezone('America/Sao_Paulo')
    return datetime.datetime.now(fuso).strftime("%H:%M")

def formatar_comprovante(dados):
    taxa = '0,2%' if dados['tipo'] == 'pix' else str(round(100*TAXAS_CARTAO[dados['parcelas']], 2)) + '%'
    return (
        f"📄 Comprovante analisado:\n"
        f"💰 Valor bruto: R$ {dados['valor']:.2f}\n"
        f"💰 Tipo: {'PIX' if dados['tipo']=='pix' else f'{dados['parcelas']}x'}\n"
        f"⏰ Horário: {dados['hora']}\n"
        f"📉 Taxa aplicada: {taxa}\n"
        f"✅ Valor líquido a pagar: R$ {dados['valor_liquido']:.2f}"
    )

def registrar_comprovante(mensagem):
    texto = mensagem.text.lower()
    valor = parse_valor(texto)
    if "pix" in texto:
        taxa = 0.002
        liquido = round(valor * (1 - taxa), 2)
        dados = {
            "valor": valor,
            "tipo": "pix",
            "hora": hora_atual_brasil(),
            "valor_liquido": liquido,
            "pago": False
        }
        comprovantes.append(dados)
        return formatar_comprovante(dados)
    parcelas = re.search(r"(\d{1,2})x", texto)
    if parcelas:
        parcelas = int(parcelas.group(1))
        if parcelas in TAXAS_CARTAO:
            taxa = TAXAS_CARTAO[parcelas]
            liquido = round(valor * (1 - taxa), 2)
            dados = {
                "valor": valor,
                "tipo": "cartao",
                "parcelas": parcelas,
                "hora": hora_atual_brasil(),
                "valor_liquido": liquido,
                "pago": False
            }
            comprovantes.append(dados)
            return formatar_comprovante(dados)
    return "❌ Não entendi o formato. Envie algo como: `1000 pix` ou `3000 6x`"

def marcar_como_pago():
    total_liquido = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    total_solicitado = sum(p["valor"] for p in pagamentos_parciais)

    if total_liquido == 0:
        return "✅ Todos os comprovantes já estão pagos."

    if solicitacoes_pagamento:
        valor_pagamento = solicitacoes_pagamento[-1]['valor']
        if valor_pagamento > total_liquido - total_solicitado:
            return f"❌ Valor de pagamento ({valor_pagamento:.2f}) excede o total pendente disponível."
        pagamentos_parciais.append({"valor": valor_pagamento})
        solicitacoes_pagamento.pop()
        return f"💸 Pagamento parcial de R$ {valor_pagamento:.2f} registrado com sucesso."

    for c in comprovantes:
        if not c["pago"]:
            c["pago"] = True
    return "✅ Pagamento registrado com sucesso."

def quanto_devo():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    total -= sum(p["valor"] for p in pagamentos_parciais)
    total = max(total, 0)
    return f"💰 Devo ao lojista: R$ {total:.2f}"

def total_a_pagar():
    total = sum(c["valor"] for c in comprovantes if not c["pago"])
    return f"💰 Total bruto dos comprovantes pendentes: R$ {total:.2f}"

def listar_pendentes():
    pendentes = [c for c in comprovantes if not c["pago"]]
    if not pendentes:
        return "✅ Nenhum comprovante pendente."
    resposta = "📋 Comprovantes pendentes:\n"
    for i, c in enumerate(pendentes, 1):
        tipo = "PIX" if c["tipo"] == "pix" else f"{c['parcelas']}x"
        resposta += f"{i}. R$ {c['valor']:.2f} | Tipo: {tipo} | ⏰ {c['hora']}\n"
    return resposta

def listar_pagos():
    pagos = [c for c in comprovantes if c["pago"]]
    if not pagos:
        return "📂 Nenhum comprovante marcado como pago ainda."
    resposta = "📁 Comprovantes pagos:\n"
    for i, c in enumerate(pagos, 1):
        tipo = "PIX" if c["tipo"] == "pix" else f"{c['parcelas']}x"
        resposta += f"{i}. R$ {c['valor']:.2f} | Tipo: {tipo} | ⏰ {c['hora']}\n"
    return resposta

def solicitar_pagamento(valor_raw, chave_pix):
    valor = parse_valor(valor_raw)
    if valor is None:
        return "❌ Valor inválido. Tente novamente."
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    total -= sum(p["valor"] for p in pagamentos_parciais)
    if valor > total:
        return f"❌ Valor solicitado excede o valor devido.\n🔒 Valor disponível: R$ {total:.2f}"
    solicitacoes_pagamento.append({"valor": valor, "chave": chave_pix})
    return f"📤 Solicitação registrada!\n💰 Valor: R$ {valor:.2f}\n🔑 Chave PIX: {chave_pix}\n\nAguarde confirmação com 'pagamento feito'."

def limpar_tudo(admin_id, user_id):
    if user_id != admin_id:
        return "❌ Comando restrito ao administrador."
    comprovantes.clear()
    pagamentos_parciais.clear()
    solicitacoes_pagamento.clear()
    return "🧹 Todos os dados foram apagados com sucesso."

def corrigir_valor(index, novo_valor_raw, admin_id, user_id):
    if user_id != admin_id:
        return "❌ Comando restrito ao administrador."
    novo_valor = parse_valor(novo_valor_raw)
    if novo_valor is None or index < 1 or index > len(comprovantes):
        return "❌ Dados inválidos."
    comprovantes[index - 1]["valor"] = novo_valor
    return f"✏️ Valor do comprovante {index} corrigido para R$ {novo_valor:.2f}"

def ajuda():
    return (
        "📌 *Comandos disponíveis:*\n"
        "• `1000 pix` ou `3000 6x` → Envia comprovante\n"
        "• `pagamento feito` → Marca como pago\n"
        "• `quanto devo` → Mostra valor líquido a pagar\n"
        "• `total a pagar` → Mostra valor bruto pendente\n"
        "• `listar pendentes` → Lista os não pagos\n"
        "• `listar pagos` → Lista os pagos\n"
        "• `solicitar pagamento` → Solicita valor com chave Pix\n"
        "• `corrigir valor` → Corrige valor de comprovante (admin)\n"
        "• `limpar tudo` → Apaga tudo (admin)"
    )
