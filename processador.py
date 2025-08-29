# processador.py
import re
from datetime import datetime, timedelta
from pytz import timezone

comprovantes = []
pagamentos_parciais = []
solicitacoes = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99,
    12: 12.52, 13: 13.69, 14: 14.19, 15: 14.69,
    16: 15.19, 17: 15.89, 18: 16.84
}

def parse_valor(valor_str):
    try:
        return float(valor_str.replace('.', '').replace(',', '.'))
    except ValueError:
        return None

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def obter_horario_brasilia():
    fuso_brasilia = timezone('America/Sao_Paulo')
    return datetime.now(fuso_brasilia).strftime("%H:%M")

def calcular_valor_liquido(valor, tipo, parcelas=None):
    if tipo == "PIX":
        taxa = 0.2
    else:
        taxa = taxas_cartao.get(parcelas, 0)

    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def processar_mensagem(texto):
    texto = texto.lower().strip()
    mensagens = []

    if "pix" in texto:
        match = re.search(r"([\d.,]+)\s*pix", texto)
        if match:
            valor_str = match.group(1)
            valor = parse_valor(valor_str)
            if valor:
                valor_liquido, taxa = calcular_valor_liquido(valor, "PIX")
                comprovantes.append({
                    "valor": valor,
                    "tipo": "PIX",
                    "horario": obter_horario_brasilia(),
                    "taxa": taxa,
                    "liquido": valor_liquido,
                    "pago": False
                })
                mensagens.append(
                    f"📄 *Comprovante analisado:*\n"
                    f"💰 Valor bruto: {formatar_valor(valor)}\n"
                    f"💰 Tipo: PIX\n"
                    f"⏰ Horário: {obter_horario_brasilia()}\n"
                    f"📉 Taxa aplicada: {taxa:.2f}%\n"
                    f"✅ Valor líquido a pagar: {formatar_valor(valor_liquido)}"
                )
    elif "x" in texto:
        match = re.search(r"([\d.,]+)\s*(\d{1,2})x", texto)
        if match:
            valor_str = match.group(1)
            parcelas = int(match.group(2))
            valor = parse_valor(valor_str)
            if valor and parcelas in taxas_cartao:
                valor_liquido, taxa = calcular_valor_liquido(valor, "Cartão", parcelas)
                comprovantes.append({
                    "valor": valor,
                    "tipo": f"{parcelas}x",
                    "horario": obter_horario_brasilia(),
                    "taxa": taxa,
                    "liquido": valor_liquido,
                    "pago": False
                })
                mensagens.append(
                    f"📄 *Comprovante analisado:*\n"
                    f"💰 Valor bruto: {formatar_valor(valor)}\n"
                    f"💰 Tipo: Cartão ({parcelas}x)\n"
                    f"⏰ Horário: {obter_horario_brasilia()}\n"
                    f"📉 Taxa aplicada: {taxa:.2f}%\n"
                    f"✅ Valor líquido a pagar: {formatar_valor(valor_liquido)}"
                )
    elif "pagamento feito" in texto:
        match = re.search(r"([\d.,]+)", texto)
        if match:
            valor_str = match.group(1)
            valor = parse_valor(valor_str)
            if valor is not None:
                valor_restante = valor
                for c in comprovantes:
                    if not c["pago"] and valor_restante > 0:
                        if valor_restante >= c["liquido"]:
                            valor_restante -= c["liquido"]
                            c["pago"] = True
                        else:
                            c["liquido"] -= valor_restante
                            valor_restante = 0
                mensagens.append("✅ Pagamento registrado e valor abatido com sucesso!")
    elif "quanto devo" in texto:
        total_liquido = sum(c["liquido"] for c in comprovantes if not c["pago"])
        mensagens.append(f"💰 Devo ao lojista: {formatar_valor(total_liquido)}")
    elif "total a pagar" in texto:
        total_bruto = sum(c["valor"] for c in comprovantes if not c["pago"])
        mensagens.append(f"💰 Valor bruto total pendente: {formatar_valor(total_bruto)}")
    elif "listar pendentes" in texto:
        texto = "📄 *Comprovantes pendentes:*\n"
        for c in comprovantes:
            if not c["pago"]:
                texto += (
                    f"- {formatar_valor(c['valor'])} ({c['tipo']}) "
                    f"⏰ {c['horario']} 💰 Líquido: {formatar_valor(c['liquido'])}\n"
                )
        mensagens.append(texto)
    elif "listar pagos" in texto:
        texto = "📄 *Pagamentos já realizados:*\n"
        for c in comprovantes:
            if c["pago"]:
                texto += (
                    f"- {formatar_valor(c['valor'])} ({c['tipo']}) "
                    f"⏰ {c['horario']} 💰 Líquido: {formatar_valor(c['liquido'])}\n"
                )
        mensagens.append(texto)
    elif "solicitar pagamento" in texto:
        mensagens.append("Digite o valor que deseja solicitar:")
        mensagens.append("AGUARDANDO_SOLICITACAO_VALOR")
    elif re.match(r"^[\d.,]+$", texto):
        valor = parse_valor(texto)
        if valor is not None:
            total_disponivel = sum(c["liquido"] for c in comprovantes if not c["pago"])
            if valor > total_disponivel:
                mensagens.append(f"❌ Você está solicitando mais do que o valor disponível. Total disponível: {formatar_valor(total_disponivel)}")
            else:
                solicitacoes.append({"valor": valor})
                mensagens.append("Digite a chave Pix para pagamento:")
                mensagens.append("AGUARDANDO_SOLICITACAO_PIX")
    elif "@" in texto and solicitacoes:
        solicitacao = solicitacoes.pop(0)
        mensagens.append(
            f"📤 Pagamento solicitado com sucesso!\n"
            f"💸 Valor: {formatar_valor(solicitacao['valor'])}\n"
            f"🔑 Chave Pix: {texto}\n"
            f"⏰ Solicitado às {obter_horario_brasilia()}"
        )
    elif "ajuda" in texto:
        mensagens.append(
            "🆘 *Comandos disponíveis:*\n"
            "- `1000,00 pix`\n"
            "- `1500,00 3x`\n"
            "- `listar pendentes`\n"
            "- `listar pagos`\n"
            "- `quanto devo`\n"
            "- `total a pagar`\n"
            "- `pagamento feito 300,00`\n"
            "- `solicitar pagamento`\n"
            "- `ajuda`"
        )

    return mensagens
