import os
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters
from processador import *

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

def start(update, context):
    update.message.reply_text("🤖 Bot ativo e pronto!")

def responder(update, context):
    texto = update.message.text.lower()

    if "pix" in texto:
        valor = normalizar_valor(texto.split("pix")[0].strip())
        dados = adicionar_comprovante(valor, 'pix')
        resposta = (
            f"📄 *Comprovante analisado:*\n"
            f"💰 *Valor bruto:* R$ {dados['valor_bruto']:.2f}\n"
            f"💳 *Tipo:* {dados['tipo']}\n"
            f"⏰ *Horário:* {dados['horario']}\n"
            f"📉 *Taxa aplicada:* {dados['taxa']:.2f}%\n"
            f"✅ *Valor líquido a pagar:* R$ {dados['valor_bruto'] - (dados['valor_bruto'] * dados['taxa'] / 100):.2f}"
        )
        update.message.reply_text(resposta, parse_mode='Markdown')

    elif "x" in texto:
        try:
            partes = texto.split("x")
            valor = normalizar_valor(partes[0].strip())
            parcelas = int(partes[1].strip())
            dados = adicionar_comprovante(valor, 'cartao', parcelas)
            resposta = (
                f"📄 *Comprovante analisado:*\n"
                f"💰 *Valor bruto:* R$ {dados['valor_bruto']:.2f}\n"
                f"💳 *Tipo:* {dados['tipo']}\n"
                f"⏰ *Horário:* {dados['horario']}\n"
                f"📉 *Taxa aplicada:* {dados['taxa']:.2f}%\n"
                f"✅ *Valor líquido a pagar:* R$ {dados['valor_bruto'] - (dados['valor_bruto'] * dados['taxa'] / 100):.2f}"
            )
            update.message.reply_text(resposta, parse_mode='Markdown')
        except:
            update.message.reply_text("❌ Erro ao processar parcelas.")

    elif "total líquido" in texto:
        total = calcular_total_liquido_pendente()
        update.message.reply_text(f"💵 *Total líquido pendente:* R$ {total:.2f}", parse_mode='Markdown')

    elif "pagamento feito" in texto:
        try:
            valor = normalizar_valor(texto.split("feito")[1].strip())
            marcar_como_pago(valor)
            update.message.reply_text("✅ Comprovantes marcados como pagos!")
        except:
            update.message.reply_text("❌ Envie o valor corretamente. Ex: 'pagamento feito 1000,00'")

    elif "solicitar pagamento" in texto:
        partes = texto.split("solicitar pagamento")
        if len(partes) == 2:
            try:
                valor = normalizar_valor(partes[1].strip())
                abater_pagamento_solicitado(valor)
                restante = calcular_total_liquido_pendente()
                update.message.reply_text(
                    f"💸 Valor de R$ {valor:.2f} marcado como *solicitado/pago*.\n"
                    f"📥 Saldo restante a receber: R$ {restante:.2f}",
                    parse_mode='Markdown'
                )
            except:
                update.message.reply_text("❌ Valor inválido.")
        else:
            update.message.reply_text("❌ Envie o valor desejado. Ex: 'solicitar pagamento 500,00'")

    elif "listar pagos" in texto:
        pagos = listar_comprovantes(pagos=True)
        update.message.reply_text(pagos)

    elif "listar pendentes" in texto:
        pendentes = listar_comprovantes(pagos=False)
        update.message.reply_text(pendentes)

    elif "ajuda" in texto:
        comandos = (
            "📌 *Comandos disponíveis:*\n"
            "- 1000 pix\n"
            "- 5000 10x\n"
            "- total líquido\n"
            "- pagamento feito 1000\n"
            "- solicitar pagamento 1000\n"
            "- listar pagos\n"
            "- listar pendentes\n"
            "- ajuda"
        )
        update.message.reply_text(comandos, parse_mode='Markdown')

def registrar_handlers(dispatcher):
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), responder))

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot DBH rodando com sucesso!'

dispatcher = Dispatcher(bot, None, workers=0)
registrar_handlers(dispatcher)
