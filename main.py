from telegram import Update
from telegram.ext import CallbackContext
import re
from datetime import datetime
import pytz

comprovantes = []
solicitacoes_pagamento = []

TAXA_PIX = 0.002

TAXAS_CARTAO = {
    1: 0.0439,  2: 0.0519,  3: 0.0619,  4: 0.0659,  5: 0.0719,  6: 0.0829,
    7: 0.0919,  8: 0.0999,  9: 0.1029, 10: 0.1088, 11: 0.1199, 12: 0.1252,
    13: 0.1369, 14: 0.1419, 15: 0.1469, 16: 0.1519, 17: 0.1589, 18: 0.1684
}

def normalizar_valor(valor_str):
    valor_str = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    return float(valor_str)

def calcular_valor_liquido(valor, tipo, parcelas=None):
    if tipo == 'pix':
        return round(valor * (1 - TAXA_PIX), 2)
    if tipo == 'cartao' and parcelas in TAXAS_CARTAO:
        return round(valor * (1 - TAXAS_CARTAO[parcelas]), 2)
    return valor

def parse_mensagem(mensagem):
    valor = re.findall(r"([\d\.,]+)", mensagem)
    parcelas = re.findall(r"(\d{1,2})x", mensagem.lower())
    if not valor:
        return None
    valor_float = normalizar_valor(valor[0])
    if 'pix' in mensagem.lower():
        return {"valor": valor_float, "tipo": "pix", "parcelas": None}
    if parcelas:
        num_parcelas = int(parcelas[0])
        return {"valor": valor_float, "tipo": "cartao", "parcelas": num_parcelas}
    return None

def processar_mensagem(update: Update, context: CallbackContext):
    texto = update.message.text.lower()

    if "pagamento feito" in texto:
        if solicitacoes_pagamento:
            valor_solicitado = solicitacoes_pagamento.pop(0)
            for c in comprovantes:
                if not c.get("pago") and valor_solicitado <= c["valor_liquido"]:
                    c["valor_liquido"] -= valor_solicitado
                    if c["valor_liquido"] <= 0.01:
                        c["pago"] = True
                    update.message.reply_text(f"✅ Pagamento parcial de R$ {valor_solicitado:.2f} registrado.")
                    return
            update.message.reply_text("⚠️ Valor informado maior que o saldo devedor.")
        else:
            for c in comprovantes:
                if not c.get("pago"):
                    c["pago"] = True
            update.message.reply_text("✅ Pagamento registrado com sucesso.")
        return

    if "quanto devo" in texto:
        total = calcular_total_liquido()
        update.message.reply_text(f"💰 Devo ao lojista: R$ {total:.2f}")
        return

    if "total a pagar" in texto:
        total_bruto = calcular_total_bruto()
        update.message.reply_text(f"💵 Total BRUTO dos comprovantes pendentes: R$ {total_bruto:.2f}")
        return

    if "listar pendentes" in texto:
        update.message.reply_text(listar_pendentes())
        return

    if "listar pagos" in texto:
        update.message.reply_text(listar_pagamentos())
        return

    if "solicitar pagamento" in texto:
        update.message.reply_text("💬 Digite o valor que deseja solicitar:")
        context.user_data["esperando_valor"] = True
        return

    if context.user_data.get("esperando_valor"):
        try:
            valor = normalizar_valor(texto)
            solicitacoes_pagamento.append(valor)
            update.message.reply_text("🔑 Agora envie a chave Pix:")
            context.user_data["valor_solicitado"] = valor
            context.user_data["esperando_valor"] = False
            context.user_data["esperando_chave"] = True
        except:
            update.message.reply_text("❌ Valor inválido. Tente novamente.")
        return

    if context.user_data.get("esperando_chave"):
        chave = texto
        valor = context.user_data.get("valor_solicitado")
        update.message.reply_text(
            f"📬 *Solicitação de Pagamento:*\n\n"
            f"💰 Valor: R$ {valor:.2f}\n🔑 Chave Pix: `{chave}`\n\n"
            f"Aguardando pagamento...",
            parse_mode='Markdown'
        )
        context.user_data["esperando_chave"] = False
        return

    if "limpar tudo" in texto and update.effective_user.id == int(os.getenv("ADMIN_ID")):
        comprovantes.clear()
        update.message.reply_text("🗑️ Todos os comprovantes foram apagados.")
        return

    if "corrigir valor" in texto and update.effective_user.id == int(os.getenv("ADMIN_ID")):
        update.message.reply_text("💬 Envie o novo valor para o último comprovante.")
        context.user_data["corrigindo_valor"] = True
        return

    if context.user_data.get("corrigindo_valor"):
        try:
            novo_valor = normalizar_valor(texto)
            if comprovantes:
                ultimo = comprovantes[-1]
                ultimo["valor"] = novo_valor
                ultimo["valor_liquido"] = calcular_valor_liquido(novo_valor, ultimo["tipo"], ultimo["parcelas"])
                update.message.reply_text(f"✏️ Valor corrigido para R$ {novo_valor:.2f}")
            context.user_data["corrigindo_valor"] = False
        except:
            update.message.reply_text("❌ Valor inválido.")
        return

    dados = parse_mensagem(texto)
    if dados:
        dados["pago"] = False
        dados["hora"] = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%H:%M")
        dados["valor_liquido"] = calcular_valor_liquido(dados["valor"], dados["tipo"], dados.get("parcelas"))
        comprovantes.append(dados)

        mensagem = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {dados['valor']:.2f}\n"
            f"💰 Tipo: {dados['tipo'].upper()}\n"
            f"⏰ Horário: {dados['hora']}\n"
            f"📉 Taxa aplicada: {'0,2%' if dados['tipo']=='pix' else f\"{round(100*TAXAS_CARTAO[dados['parcelas']],2)}%\"}\n"
            f"✅ Valor líquido a pagar: R$ {dados['valor_liquido']:.2f}"
        )
        update.message.reply_text(mensagem)
    else:
        update.message.reply_text("❌ Comprovante não reconhecido. Envie no formato: `1000 pix` ou `1500 3x`")

def listar_pendentes():
    texto = ""
    for i, c in enumerate(comprovantes):
        if not c.get("pago"):
            texto += f"{i+1}. R$ {c['valor']:.2f} - {c['tipo']} - {c['hora']}\n"
    total = calcular_total_liquido()
    return texto + f"\n💰 Total líquido pendente: R$ {total:.2f}" if texto else "✅ Nenhum comprovante pendente."

def listar_pagamentos():
    pagos = [c for c in comprovantes if c.get("pago")]
    if not pagos:
        return "❌ Nenhum comprovante pago ainda."
    texto = ""
    for i, c in enumerate(pagos):
        texto += f"{i+1}. R$ {c['valor']:.2f} - {c['tipo']} - {c['hora']}\n"
    total = sum(c["valor"] for c in pagos)
    return texto + f"\n✅ Total pago: R$ {total:.2f}"

def calcular_total_liquido():
    return sum(c["valor_liquido"] for c in comprovantes if not c.get("pago"))

def calcular_total_bruto():
    return sum(c["valor"] for c in comprovantes if not c.get("pago"))

def limpar_dados(update: Update, context: CallbackContext):
    if update.effective_user.id != int(os.getenv("ADMIN_ID")):
        update.message.reply_text("⛔ Acesso negado.")
        return
    comprovantes.clear()
    update.message.reply_text("🗑️ Todos os comprovantes foram apagados.")

def corrigir_valor(update: Update, context: CallbackContext):
    if update.effective_user.id != int(os.getenv("ADMIN_ID")):
        update.message.reply_text("⛔ Acesso negado.")
        return
    update.message.reply_text("💬 Envie o novo valor para o último comprovante.")
    context.user_data["corrigindo_valor"] = True

def solicitar_pagamento(update: Update, context: CallbackContext):
    update.message.reply_text("💬 Digite o valor que deseja solicitar:")
    context.user_data["esperando_valor"] = True

def marcar_pagamento(update: Update, context: CallbackContext):
    for c in comprovantes:
        if not c.get("pago"):
            c["pago"] = True
    update.message.reply_text("✅ Pagamento registrado com sucesso.")
