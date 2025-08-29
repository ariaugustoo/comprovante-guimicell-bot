import os
from flask import Flask, request
import telegram
from telegram import Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
from processador import (
    processar_mensagem,
    marcar_como_pago,
    quanto_devo,
    total_a_pagar,
    solicitar_pagamento,
    listar_pendentes,
    listar_pagamentos,
    mostrar_ajuda,
    limpar_tudo,
    corrigir_valor,
    status_bot
)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_ID = os.environ.get("GROUP_ID")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

def registrar_handlers():
    dispatcher.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Bot ativo!")))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), processar_mensagem))
    dispatcher.add_handler(CommandHandler("status", status_bot))
    dispatcher.add_handler(CommandHandler("limpar", limpar_tudo))
    dispatcher.add_handler(CommandHandler("corrigir", corrigir_valor))
    dispatcher.add_handler(CommandHandler("ajuda", mostrar_ajuda))
    dispatcher.add_handler(CommandHandler("listar_pendentes", listar_pendentes))
    dispatcher.add_handler(CommandHandler("listar_pagos", listar_pagamentos))

registrar_handlers()

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot ativo com webhook!'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    elif "pagamento feito" in texto:
        match = re.search(r"([\d.,]+)", texto)
        if match:
            valor_pago = normalizar_valor(match.group(1))
        else:
            valor_pago = None

        if valor_pago is None:
            valor_pago = obter_valor_total_pendente()

        if valor_pago <= 0:
            update.message.reply_text("❌ Nenhum valor pendente para pagamento.")
            return

        saldo_pendente = obter_valor_total_pendente()
        if valor_pago > saldo_pendente:
            update.message.reply_text(f"❌ Pagamento excede o valor pendente. Total pendente: R$ {saldo_pendente:.2f}")
            return

        valor_restante = valor_pago
        for comp in comprovantes:
            if not comp["pago"]:
                if valor_restante >= comp["valor_liquido"]:
                    valor_restante -= comp["valor_liquido"]
                    comp["pago"] = True
                elif valor_restante > 0:
                    comp["valor_liquido"] -= valor_restante
                    comp["valor_bruto"] = comp["valor_liquido"] / (1 - comp["taxa"])
                    valor_restante = 0
                if valor_restante <= 0:
                    break

        update.message.reply_text(f"✅ Pagamento de R$ {valor_pago:.2f} registrado com sucesso.")

    elif "quanto devo" in texto:
        total = obter_valor_total_pendente()
        update.message.reply_text(f"💰 Devo ao lojista: R$ {total:.2f}")

    elif "total a pagar" in texto:
        total_bruto = sum(c["valor_bruto"] for c in comprovantes if not c["pago"])
        update.message.reply_text(f"💰 Total bruto dos comprovantes pendentes: R$ {total_bruto:.2f}")

    elif "listar pendentes" in texto:
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            update.message.reply_text("✅ Nenhum comprovante pendente.")
            return
        resposta = "📋 *Comprovantes Pendentes:*\n"
        for i, c in enumerate(pendentes, start=1):
            resposta += (
                f"\n🔢 {i}\n"
                f"💰 Valor bruto: R$ {c['valor_bruto']:.2f}\n"
                f"💰 Tipo: {c['tipo'].capitalize()} {f'{c['parcelas']}x' if c['tipo'] == 'cartao' else ''}\n"
                f"⏰ Horário: {c['horario']}\n"
                f"✅ Valor líquido: R$ {c['valor_liquido']:.2f}\n"
            )
        update.message.reply_text(resposta, parse_mode="Markdown")

    elif "listar pagos" in texto:
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            update.message.reply_text("📭 Nenhum pagamento registrado ainda.")
            return
        resposta = "📦 *Comprovantes Pagos:*\n"
        for i, c in enumerate(pagos, start=1):
            resposta += (
                f"\n🔢 {i}\n"
                f"💰 Valor bruto: R$ {c['valor_bruto']:.2f}\n"
                f"💰 Tipo: {c['tipo'].capitalize()} {f'{c['parcelas']}x' if c['tipo'] == 'cartao' else ''}\n"
                f"⏰ Horário: {c['horario']}\n"
                f"✅ Valor líquido pago: R$ {c['valor_liquido']:.2f}\n"
            )
        update.message.reply_text(resposta, parse_mode="Markdown")

    elif "ajuda" in texto:
        comandos = (
            "📖 *Comandos disponíveis:*\n"
            "- `1000,00 pix`\n"
            "- `2500,00 10x`\n"
            "- `pagamento feito` ou `pagamento feito 300,00`\n"
            "- `quanto devo`\n"
            "- `total a pagar`\n"
            "- `listar pendentes`\n"
            "- `listar pagos`\n"
            "- `solicitar pagamento`\n"
            "- `/status` ou `fechamento do dia`\n"
        )
        update.message.reply_text(comandos, parse_mode="Markdown")
        elif "solicitar pagamento" in texto:
        if obter_valor_total_pendente() <= 0:
            update.message.reply_text("❌ Nenhum saldo disponível para solicitar pagamento.")
            return

        contexto_usuario[chat_id] = {"estado": "aguardando_valor"}
        update.message.reply_text("Digite o valor que deseja solicitar:")

    elif chat_id in contexto_usuario:
        estado_atual = contexto_usuario[chat_id].get("estado")

        if estado_atual == "aguardando_valor":
            try:
                valor_solicitado = normalizar_valor(texto)
                if valor_solicitado <= 0:
                    raise ValueError("Valor inválido")

                if valor_solicitado > obter_valor_total_pendente():
                    update.message.reply_text(
                        f"❌ Você está solicitando mais do que o valor disponível. Total disponível:"
