import os
from flask import Flask, request
from telegram import Bot
from processador import (
    adicionar_comprovante, calcular_liquido, marcar_comprovante_como_pago,
    gerar_resumo, limpar_tudo, ultimo_comprovante, listar_comprovantes
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if 'message' in data:
        msg = data['message']
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']
        texto = msg.get('text', '')

        if texto.startswith("/start") and user_id == ADMIN_ID:
            bot.send_message(chat_id, "🤖 Bot está online e funcionando!")
        elif texto.startswith("/limpar") and user_id == ADMIN_ID:
            limpar_tudo()
            bot.send_message(chat_id, "Todos os comprovantes foram apagados.")
        elif texto.startswith("/corrigir") and user_id == ADMIN_ID:
            bot.send_message(chat_id, "Envie o valor corrigido.")
        elif "pix" in texto.lower():
            valor = float(texto.lower().replace("pix", "").replace("r$", "").replace(",", ".").strip())
            horario = "Manual"
            c = adicionar_comprovante(valor, None, horario, "pix")
            bot.send_message(chat_id, f"📄 Comprovante analisado:\n💰 Valor bruto: R$ {valor:,.2f}\n⏰ Horário: {horario}\n📉 Taxa aplicada: {c['taxa']}%\n✅ Valor líquido a pagar: R$ {c['liquido']:,.2f}")
        elif "x" in texto.lower():
            partes = texto.lower().replace("r$", "").replace(",", ".").split("x")
            if len(partes) == 2:
                valor = float(partes[0].strip())
                parcelas = int(partes[1].strip())
                horario = "Manual"
                c = adicionar_comprovante(valor, parcelas, horario, "cartao")
                bot.send_message(chat_id, f"📄 Comprovante analisado:\n💰 Valor bruto: R$ {valor:,.2f}\n💳 Parcelas: {parcelas}x\n⏰ Horário: {horario}\n📉 Taxa aplicada: {c['taxa']}%\n✅ Valor líquido a pagar: R$ {c['liquido']:,.2f}")
        elif texto == "✅":
            c = marcar_comprovante_como_pago()
            if c:
                bot.send_message(chat_id, f"Comprovante marcado como pago ✅")
        elif texto.lower() == "total que devo":
            pendentes, *_ = gerar_resumo()
            total = sum(c["liquido"] for c in pendentes)
            bot.send_message(chat_id, f"📌 Total a pagar: R$ {total:,.2f}")
        elif texto.lower() == "listar pendentes":
            pendentes = listar_comprovantes(pago=False)
            if pendentes:
                mensagem = "📋 Pendentes:\n"
                for i, c in enumerate(pendentes, 1):
                    mensagem += f"{i}. R$ {c['liquido']:,.2f} ({c['tipo']})\n"
                bot.send_message(chat_id, mensagem)
        elif texto.lower() == "listar pagos":
            pagos = listar_comprovantes(pago=True)
            if pagos:
                mensagem = "✅ Pagos:\n"
                for i, c in enumerate(pagos, 1):
                    mensagem += f"{i}. R$ {c['liquido']:,.2f} ({c['tipo']})\n"
                bot.send_message(chat_id, mensagem)
        elif texto.lower() == "último comprovante":
            c = ultimo_comprovante()
            if c:
                bot.send_message(chat_id, f"Último: R$ {c['liquido']:,.2f} ({c['tipo']})")
        elif texto.lower() == "total geral":
            _, _, pendente, pago, total = gerar_resumo()
            bot.send_message(chat_id, f"📊 Total geral: R$ {total:,.2f}\nPendentes: R$ {pendente:,.2f}\nPagos: R$ {pago:,.2f}")
        elif texto.lower() == "ajuda":
            comandos = """
📘 *Comandos disponíveis*:
/start – Confirma se o bot está online
✅ – Marca último como pago
total que devo – Mostra total em aberto
listar pendentes – Lista comprovantes não pagos
listar pagos – Lista comprovantes pagos
último comprovante – Mostra o último lançado
total geral – Mostra resumo total
/limpar – Limpa todos os comprovantes (admin)
/corrigir – Corrige valor (admin)
"""
            bot.send_message(chat_id, comandos, parse_mode='Markdown')

    return "ok"
