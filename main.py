import os
import telebot
import time
import json
from flask import Flask, request
from processador import processar_comprovante

TOKEN = os.getenv("BOT_TOKEN", "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA")
GROUP_ID = int(os.getenv("GROUP_ID", "-1002626449000"))

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

comprovantes = []

@bot.message_handler(commands=["start", "ajuda"])
def send_help(message):
    comandos = """
📋 *Comandos disponíveis:*

1️⃣ `valor pix` → Ex: `6438,76 pix`
2️⃣ `valor cartão` → Ex: `7899,99 10x`
3️⃣ `✅` → Marca como pago o último comprovante
4️⃣ `total que devo` → Total pendente
5️⃣ `listar pendentes` → Lista todos em aberto
6️⃣ `listar pagos` → Lista pagos
7️⃣ `último comprovante` → Mostra o último enviado
8️⃣ `total geral` → Tudo (pago + pendente)
"""
    bot.reply_to(message, comandos, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def processar_mensagem(message):
    global comprovantes

    texto = message.text.strip()
    chat_id = message.chat.id

    if chat_id != GROUP_ID:
        return

    if texto.startswith("✅"):
        for comp in reversed(comprovantes):
            if not comp.get("pago"):
                comp["pago"] = True
                bot.reply_to(message, f"✅ Comprovante de R$ {comp['valor_bruto']} marcado como *pago*.", parse_mode="Markdown")
                return
        bot.reply_to(message, "Nenhum comprovante pendente encontrado.")

    elif texto.lower() == "total que devo":
        total = sum(c["valor_liquido"] for c in comprovantes if not c.get("pago"))
        bot.reply_to(message, f"💰 Total pendente: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    elif texto.lower() == "listar pendentes":
        pendentes = [c for c in comprovantes if not c.get("pago")]
        if not pendentes:
            bot.reply_to(message, "✅ Nenhum comprovante pendente.")
            return
        resposta = "\n".join([f"💳 {c['parcelas']}x - R$ {c['valor_bruto']} → 💰 R$ {c['valor_liquido']}" for c in pendentes])
        bot.reply_to(message, "📌 Pendentes:\n" + resposta)

    elif texto.lower() == "listar pagos":
        pagos = [c for c in comprovantes if c.get("pago")]
        if not pagos:
            bot.reply_to(message, "📭 Nenhum comprovante pago.")
            return
        resposta = "\n".join([f"✅ {c['parcelas']}x - R$ {c['valor_bruto']} → R$ {c['valor_liquido']}" for c in pagos])
        bot.reply_to(message, "📬 Pagos:\n" + resposta)

    elif texto.lower() == "último comprovante":
        if not comprovantes:
            bot.reply_to(message, "Nenhum comprovante registrado.")
            return
        c = comprovantes[-1]
        status = "✅ PAGO" if c.get("pago") else "❌ PENDENTE"
        bot.reply_to(message, f"""
📄 Último comprovante:
💰 Valor bruto: R$ {c['valor_bruto']}
💳 Parcelas: {c['parcelas']}
📉 Taxa aplicada: {c['taxa']}%
✅ Valor líquido: R$ {c['valor_liquido']}
📌 Status: {status}
""")

    elif texto.lower() == "total geral":
        total = sum(c["valor_liquido"] for c in comprovantes)
        bot.reply_to(message, f"📊 Total geral (pago + pendente): R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    else:
        resultado = processar_comprovante(texto)
        if resultado:
            comprovantes.append(resultado)
            bot.reply_to(message, f"""
📄 Comprovante analisado:
💰 Valor bruto: R$ {resultado['valor_bruto']}
💳 Parcelas: {resultado['parcelas']}
📉 Taxa aplicada: {resultado['taxa']}%
✅ Valor líquido a pagar: R$ {resultado['valor_liquido']}
""")
        else:
            bot.reply_to(message, "❌ Não consegui entender o comprovante. Envie no formato:\n\n`6438,76 pix` ou `7899,99 10x`")

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot ativo!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"https://comprovante-guimicell-bot.onrender.com/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
