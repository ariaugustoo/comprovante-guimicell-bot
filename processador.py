import re
from datetime import datetime, timedelta
from pytz import timezone

comprovantes = []
pagamentos_realizados = []
solicitacoes_pagamento = []

# Taxas de cartão por parcela
taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def get_horario_brasilia():
    return datetime.now(timezone('America/Sao_Paulo')).strftime('%H:%M')

def normalizar_valor(valor_str):
    valor_str = valor_str.replace('.', '').replace(',', '.')
    try:
        return float(valor_str)
    except ValueError:
        return None

def registrar_comprovante(valor_bruto, tipo, parcelas=1):
    horario = get_horario_brasilia()

    if tipo.lower() == 'pix':
        taxa = 0.2
    else:
        taxa = taxas_cartao.get(parcelas, 0)

    valor_liquido = round(valor_bruto * (1 - taxa / 100), 2)

    comprovantes.append({
        "valor_bruto": valor_bruto,
        "tipo": tipo,
        "parcelas": parcelas,
        "horario": horario,
        "pago": False,
        "valor_liquido": valor_liquido
    })

    return f"""📄 Comprovante analisado:
💰 Valor bruto: R$ {valor_bruto:,.2f}
💰 Tipo: {tipo.upper()}
⏰ Horário: {horario}
📉 Taxa aplicada: {taxa:.2f}%
✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"""

def calcular_total_pendente():
    total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
    return round(total, 2)

def calcular_total_pago():
    total = sum(c["valor_liquido"] for c in comprovantes if c["pago"])
    return round(total, 2)

def calcular_total_bruto_pendente():
    total = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
    return round(total, 2)

def listar_comprovantes(pagos=False):
    lista = [c for c in comprovantes if c["pago"] == pagos]
    if not lista:
        return "Nenhum comprovante encontrado."
    
    resposta = ""
    for i, c in enumerate(lista, 1):
        resposta += f"{i}. 💰 R$ {c['valor_bruto']:,.2f} | {c['tipo'].upper()} | ⏰ {c['horario']} | {'✅ PAGO' if c['pago'] else '❌ PENDENTE'}\n"
    return resposta

def marcar_como_pago():
    for c in comprovantes:
        if not c["pago"]:
            c["pago"] = True
            pagamentos_realizados.append(c)
            break

def marcar_pagamento_parcial(valor_pago):
    valor_restante = valor_pago
    for c in comprovantes:
        if not c["pago"]:
            if c["valor_liquido"] <= valor_restante:
                valor_restante -= c["valor_liquido"]
                c["pago"] = True
                pagamentos_realizados.append(c)
            else:
                c["valor_liquido"] -= valor_restante
                valor_restante = 0
            if valor_restante <= 0:
                break

def limpar_dados():
    comprovantes.clear()
    pagamentos_realizados.clear()
    solicitacoes_pagamento.clear()
    def solicitar_pagamento(valor, chave_pix):
    total_pendente = calcular_total_pendente()
    if valor > total_pendente:
        return f"🚫 O valor solicitado (R$ {valor:,.2f}) é maior que o saldo disponível (R$ {total_pendente:,.2f}). Solicitação negada."
    
    solicitacoes_pagamento.append({
        "valor": valor,
        "chave_pix": chave_pix,
        "horario": get_horario_brasilia()
    })
    
    return f"""📢 Pagamento solicitado:
💰 Valor: R$ {valor:,.2f}
🔑 Chave Pix: {chave_pix}
⏰ Horário: {get_horario_brasilia()}
Aguarde a confirmação com "Pagamento feito" para abatimento."""

def exibir_ajuda():
    return """📘 Comandos disponíveis:

👉 Enviar comprovante:
• Ex: 1000,00 pix
• Ex: 2500,00 6x

✅ pagamento feito
📉 quanto devo
📋 total a pagar
📜 listar pendentes
📜 listar pagos
💬 solicitar pagamento
📅 fechamento do dia
📊 /status
🔄 /corrigir valor (admin)
⚠️ /limpar tudo (admin)
"""

def fechamento_dia():
    total_pago = calcular_total_pago()
    total_pendente = calcular_total_pendente()
    total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "pix")
    total_cartao = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] != "pix")
    
    return f"""📅 *Fechamento do Dia*
✅ Total pago: R$ {total_pago:,.2f}
❌ Total pendente: R$ {total_pendente:,.2f}
💳 Total Cartão: R$ {total_cartao:,.2f}
⚡️ Total Pix: R$ {total_pix:,.2f}
"""

def status_geral():
    total_bruto = sum(c["valor_bruto"] for c in comprovantes)
    total_liquido = sum(c["valor_liquido"] for c in comprovantes)
    total_pago = calcular_total_pago()
    total_pendente = calcular_total_pendente()
    total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] == "pix")
    total_cartao = sum(c["valor_liquido"] for c in comprovantes if c["tipo"] != "pix")

    return f"""📊 *Status Geral:*
🧾 Total bruto: R$ {total_bruto:,.2f}
💰 Total líquido: R$ {total_liquido:,.2f}
✅ Já pago: R$ {total_pago:,.2f}
❌ Pendentes: R$ {total_pendente:,.2f}
💳 Cartão: R$ {total_cartao:,.2f}
⚡️ Pix: R$ {total_pix:,.2f}
"""

def corrigir_valor(index, novo_valor):
    try:
        comprovantes[index]["valor_bruto"] = novo_valor
        tipo = comprovantes[index]["tipo"]
        parcelas = comprovantes[index]["parcelas"]
        taxa = 0.2 if tipo.lower() == 'pix' else taxas_cartao.get(parcelas, 0)
        comprovantes[index]["valor_liquido"] = round(novo_valor * (1 - taxa / 100), 2)
        return f"✅ Valor corrigido com sucesso. Novo valor bruto: R$ {novo_valor:,.2f}"
    except IndexError:
        return "❌ Comprovante não encontrado."
        def solicitar_pagamento(valor, chave_pix):
    total = calcular_total_pendente()
    if valor > total:
        return f"🚫 O valor solicitado (R$ {valor:,.2f}) é maior que o saldo disponível (R$ {total:,.2f})."
    
    solicitacoes_pagamento.append({
        "valor": valor,
        "chave_pix": chave_pix,
        "horario": get_horario_brasilia()
    })

    return f"""📢 *Solicitação de pagamento recebida!*
💰 Valor: R$ {valor:,.2f}
🔑 Chave Pix: {chave_pix}
⏰ Horário: {get_horario_brasilia()}

Após realizar o pagamento, envie o comando:
👉 pagamento feito {valor:,.2f}
"""

def status_geral():
    total_pago = calcular_total_pago()
    total_pendente = calcular_total_pendente()
    total_bruto = calcular_total_bruto_pendente()
    total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"].lower() == "pix" and not c["pago"])
    total_cartao = sum(c["valor_liquido"] for c in comprovantes if c["tipo"].lower() != "pix" and not c["pago"])

    return f"""📊 *Status Atual:*
💳 Total Cartão pendente: R$ {total_cartao:,.2f}
⚡ Total PIX pendente: R$ {total_pix:,.2f}
💰 Total PENDENTE: R$ {total_pendente:,.2f}
✅ Total PAGO: R$ {total_pago:,.2f}
📈 Total BRUTO pendente: R$ {total_bruto:,.2f}"""

def fechamento_do_dia():
    total_pago = calcular_total_pago()
    total_pendente = calcular_total_pendente()
    total_pix = sum(c["valor_liquido"] for c in comprovantes if c["tipo"].lower() == "pix" and not c["pago"])
    total_cartao = sum(c["valor_liquido"] for c in comprovantes if c["tipo"].lower() != "pix" and not c["pago"])

    return f"""📅 *Fechamento do Dia:*
✅ Total Pago: R$ {total_pago:,.2f}
❌ Total Pendente: R$ {total_pendente:,.2f}
⚡ PIX pendente: R$ {total_pix:,.2f}
💳 Cartão pendente: R$ {total_cartao:,.2f}"""

def ajuda():
    return """📘 *Comandos disponíveis:*
1️⃣ Enviar comprovante:
   💰 Exemplo: 1000,00 pix ou 1200,00 10x

2️⃣ *pagamento feito* — marca um comprovante como pago (ou *pagamento feito 300,00* para valor parcial)

3️⃣ *quanto devo* — mostra o total líquido pendente

4️⃣ *total a pagar* — mostra o total bruto pendente

5️⃣ *listar pendentes* — lista comprovantes não pagos

6️⃣ *listar pagos* — lista comprovantes pagos

7️⃣ *solicitar pagamento* — inicia solicitação de pagamento parcial + chave Pix

8️⃣ */status* — mostra resumo geral

9️⃣ *fechamento do dia* — resumo final do dia

🔐 *comandos avançados (admin apenas):*
- *limpar tudo*
- *corrigir valor*
"""

def processar_mensagem(texto):
    texto = texto.lower().strip()

    if texto.startswith("/status"):
        return status_geral()

    elif "fechamento do dia" in texto:
        return fechamento_do_dia()

    elif "ajuda" in texto:
        return ajuda()

    elif texto.startswith("quanto devo"):
        total = calcular_total_pendente()
        return f"💰 Devo ao lojista: R$ {total:,.2f}"

    elif texto.startswith("total a pagar"):
        bruto = calcular_total_bruto_pendente()
        return f"📌 Total bruto a pagar: R$ {bruto:,.2f}"
            elif texto.startswith("listar pagos"):
        texto = "📄 *Pagamentos já realizados:*\n"
        for i, c in enumerate(comprovantes):
            if c["pago"]:
                texto += f"\n#{i+1} 💰 Valor bruto: R$ {c['valor_bruto']:,.2f}\n"
                texto += f"💳 Tipo: {c['tipo']}\n"
                texto += f"⏰ Horário: {c['horario']}\n"
                texto += f"📉 Taxa aplicada: {c['taxa_aplicada']:.2f}%\n"
                texto += f"✅ Valor líquido: R$ {c['valor_liquido']:,.2f}\n"
        return texto or "Nenhum pagamento realizado ainda."

    elif texto.startswith("listar pendentes"):
        texto = "📄 *Comprovantes pendentes:*\n"
        for i, c in enumerate(comprovantes):
            if not c["pago"]:
                texto += f"\n#{i+1} 💰 Valor bruto: R$ {c['valor_bruto']:,.2f}\n"
                texto += f"💳 Tipo: {c['tipo']}\n"
                texto += f"⏰ Horário: {c['horario']}\n"
                texto += f"📉 Taxa aplicada: {c['taxa_aplicada']:.2f}%\n"
                texto += f"✅ Valor líquido: R$ {c['valor_liquido']:,.2f}\n"
        return texto or "Todos os comprovantes foram pagos. ✅"

    elif texto.startswith("limpar tudo"):
        if str(ADMIN_ID) not in texto:
            return "🚫 Comando permitido apenas ao administrador."
        comprovantes.clear()
        pagamentos_parciais.clear()
        solicitacoes_pagamento.clear()
        return "🧹 Todos os dados foram limpos com sucesso."

    elif texto.startswith("corrigir valor"):
        if str(ADMIN_ID) not in texto:
            return "🚫 Comando permitido apenas ao administrador."
        return "⚙️ Para corrigir um valor, envie o comando no formato:\nex: corrigir valor 1 1200,00\n(sendo 1 o número do comprovante)"

    elif "solicitar pagamento" in texto:
        return "Digite o valor que deseja solicitar (ex: 180,00):"

    elif re.match(r"^\d{1,6},\d{2}$", texto):
        ultimo_comando = solicitacoes_pagamento[-1] if solicitacoes_pagamento else None
        if ultimo_comando and "chave_pix" not in ultimo_comando:
            valor = float(texto.replace(",", "."))
            if valor > calcular_total_pendente():
                solicitacoes_pagamento.pop()
                return f"🚫 Você não pode solicitar R$ {valor:,.2f} pois ultrapassa o valor pendente."
            solicitacoes_pagamento[-1]["valor"] = valor
            return "Agora digite a *chave Pix* para esta solicitação:"
        else:
            return "❓ Este valor foi enviado fora do fluxo de solicitação."

    elif "@" in texto or "br" in texto:
        if solicitacoes_pagamento and "valor" in solicitacoes_pagamento[-1] and "chave_pix" not in solicitacoes_pagamento[-1]:
            solicitacoes_pagamento[-1]["chave_pix"] = texto
            return solicitar_pagamento(
                solicitacoes_pagamento[-1]["valor"],
                solicitacoes_pagamento[-1]["chave_pix"]
            )

    elif texto.startswith("pagamento feito"):
        valor_match = re.search(r"(\d{1,6},\d{2})", texto)
        if valor_match:
            valor_pago = float(valor_match.group(1).replace(",", "."))
        else:
            valor_pago = None

        if valor_pago:
            total_pendente = calcular_total_pendente()
            if valor_pago > total_pendente:
                return f"🚫 O valor de R$ {valor_pago:,.2f} é maior do que o saldo pendente de R$ {total_pendente:,.2f}."
            pagamentos_parciais.append({
                "valor": valor_pago,
                "horario": get_horario_brasilia()
            })
            return f"✅ Pagamento parcial de R$ {valor_pago:,.2f} registrado com sucesso!"

        else:
            for c in comprovantes:
                if not c["pago"]:
                    c["pago"] = True
            return "✅ Todos os comprovantes foram marcados como pagos."
                elif texto == "quanto devo":
        total = calcular_total_pendente()
        return f"💰 Devo ao lojista: R$ {total:,.2f}"

    elif texto == "total a pagar":
        total = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
        return f"💰 Valor bruto pendente (sem desconto): R$ {total:,.2f}"

    elif texto == "/status" or texto.lower().strip() == "status":