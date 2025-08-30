# processador.py

import datetime
from decimal import Decimal, InvalidOperation

comprovantes = []
pagamentos_feitos = []
solicitacoes_pagamento = []

taxas_cartao = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

def normalizar_valor(valor_str):
    valor_str = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    return float(valor_str)

def obter_horario_brasilia():
    agora_utc = datetime.datetime.utcnow()
    fuso_brasilia = datetime.timezone(datetime.timedelta(hours=-3))
    return agora_utc.replace(tzinfo=datetime.timezone.utc).astimezone(fuso_brasilia).strftime("%H:%M")

def calcular_valor_liquido(valor, tipo, parcelas=None):
    if tipo == "pix":
        taxa = 0.2
    elif tipo == "cartao":
        taxa = taxas_cartao.get(parcelas, 0)  # padrão 0% se não achar
    else:
        taxa = 0
    valor_liquido = valor * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

# ✅ ESSA É A FUNÇÃO QUE FOI CORRIGIDA AQUI
def processar_mensagem(texto, user_id):
    texto = texto.lower()
    resposta = ""

    # (exemplo de comando)
    if "ajuda" in texto:
        resposta = (
            "📌 *Comandos disponíveis:*\n\n"
            "💸 Enviar comprovante: `valor pix` ou `valor 3x`\n"
            "📍 `quanto devo` – mostra quanto você ainda tem pra receber\n"
            "📍 `total a pagar` – mostra o valor bruto pendente\n"
            "📍 `listar pendentes` – lista todos os comprovantes abertos\n"
            "📍 `listar pagos` – mostra os pagos\n"
            "📍 `pagamento feito` – marca último pagamento como pago\n"
            "📍 `solicitar pagamento` – pede pagamento parcial\n"
            "📍 `/status` – mostra resumo geral\n"
        )
        return resposta

    # Aqui seguem os outros comandos do bot, como:
    # - registrar comprovantes com "1000 pix" ou "5000 10x"
    # - listar pagos
    # - calcular total
    # - pagamento feito
    # - etc.

    return resposta or "🤖 Comando não reconhecido. Digite *ajuda* para ver a lista de comandos."