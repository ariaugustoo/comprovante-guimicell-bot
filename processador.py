import os
import re
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TOKEN = os.getenv("TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)

comprovantes = []

def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_taxa(valor, tipo, parcelas=1):
    taxas = {
        "pix": 0.002,
        "cartao": {
            1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659, 5: 0.0719,
            6: 0.0829, 7: 0.0919, 8: 0.0999, 9: 0.1029, 10: 0.1088,
            11: 0.1199, 12: 0.1252, 13: 0.1369, 14: 0.1419, 15: 0.1469,
            16: 0.1519, 17: 0.1589, 18: 0.1684
        }
    }

    if tipo == "pix":
        taxa = taxas["pix"]
    else:
        taxa = taxas["cartao"].get(parcelas, 0)

    return valor * taxa, taxa

def processar_mensagem(msg):
    texto = msg.get("text", "").lower()
    user_id = msg["from"]["id"]
    nome = msg["from"].get("first_name", "Usuário")

    if texto == "listar pagos":
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            resposta = "📄 Nenhum comprovante pago ainda."
        else:
            resposta = "\n".join([f"{formatar_valor(c['valor'])} {'✅' if c['pago'] else ''}" for c in pagos])
        bot.send_message(chat_id=GROUP_ID, text=resposta)

    elif texto == "listar pendentes":
        pendentes = [c for c in comprovantes if not c["pago"]]
        if not pendentes:
            resposta = "🎉 Todos os comprovantes foram pagos!"
        else:
            resposta = "\n".join([f"{formatar_valor(c['valor'])}" for c in pendentes])
        bot.send_message(chat_id=GROUP_ID, text=resposta)

    elif texto == "total que devo":
        total = sum(c["valor"] for c in comprovantes if not c["pago"])
        bot.send_message(chat_id=GROUP_ID, text=f"💸 Total a pagar: {formatar_valor(total)}")

    elif texto == "total geral":
        total = sum(c["valor"] for c in comprovantes)
        bot.send_message(chat_id=GROUP_ID, text=f"📊 Total geral de comprovantes: {formatar_valor(total)}")

    elif texto == "último comprovante":
        if comprovantes:
            ult = comprovantes[-1]
            status = "✅ Pago" if ult["pago"] else "⏳ Pendente"
            resposta = f"📄 Último comprovante:\n💰 Valor: {formatar_valor(ult['valor'])}\n💳 Parcelas: {ult.get('parcelas', 'PIX')}\n📉 Status: {status}"
        else:
            resposta = "Nenhum comprovante enviado ainda."
        bot.send_message(chat_id=GROUP_ID, text=resposta)

    elif texto.startswith("✅"):
        if comprovantes:
            comprovantes[-1]["pago"] = True
            bot.send_message(chat_id=GROUP_ID, text="✅ Marcado como pago.")
        else:
            bot.send_message(chat_id=GROUP_ID, text="Nenhum comprovante para marcar como pago.")

    elif re.match(r"^[\d.,]+\s*pix$", texto):
        valor_str = texto.split()[0].replace(".", "").replace(",", ".")
        valor = float(valor_str)
        taxa_valor, taxa_perc = calcular_taxa(valor, "pix")
        liquido = valor - taxa_valor
        comprovantes.append({"valor": valor, "pago": False, "tipo": "pix"})
        msg = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: {formatar_valor(valor)}\n"
            f"📉 Taxa aplicada: {round(taxa_perc*100, 2)}%\n"
            f"✅ Valor líquido a pagar: {formatar_valor(liquido)}"
        )
        bot.send_message(chat_id=GROUP_ID, text=msg)

    elif re.match(r"^[\d.,]+\s*\d{1,2}x$", texto):
        partes = texto.split()
        valor_str = partes[0].replace(".", "").replace(",", ".")
        valor = float(valor_str)
        parcelas = int(partes[1].replace("x", ""))
        taxa_valor, taxa_perc = calcular_taxa(valor, "cartao", parcelas)
        liquido = valor - taxa_valor
        comprovantes.append({"valor": valor, "pago": False, "tipo": "cartao", "parcelas": parcelas})
        msg = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: {formatar_valor(valor)}\n"
            f"💳 Parcelas: {parcelas}x\n"
            f"📉 Taxa aplicada: {round(taxa_perc*100, 2)}%\n"
            f"✅ Valor líquido a pagar: {formatar_valor(liquido)}"
        )
        bot.send_message(chat_id=GROUP_ID, text=msg)

    elif texto == "/limpar tudo" and user_id == ADMIN_ID:
        comprovantes.clear()
        bot.send_message(chat_id=GROUP_ID, text="🧹 Todos os comprovantes foram apagados com sucesso!")

    elif texto == "/corrigir valor" and user_id == ADMIN_ID:
        bot.send_message(chat_id=GROUP_ID, text="🔧 Envie o novo valor para corrigir o último comprovante.")

    elif texto.startswith("🧮 resumo agora") and user_id == ADMIN_ID:
        total_pago = sum(c["valor"] for c in comprovantes if c["pago"])
        total_pendente = sum(c["valor"] for c in comprovantes if not c["pago"])
        resumo = (
            f"🧾 RESUMO ATUAL:\n"
            f"✅ Pagos: {formatar_valor(total_pago)}\n"
            f"💸 Pendentes: {formatar_valor(total_pendente)}"
        )
        bot.send_message(chat_id=GROUP_ID, text=resumo)

    elif texto == "ajuda":
        comandos = (
            "📋 *Comandos disponíveis:*\n"
            "- Envie: `1349,99 pix` → Taxa 0,2%\n"
            "- Envie: `4200,00 3x` → Parcelado\n"
            "- ✅ → marca último como pago\n"
            "- `listar pagos`\n"
            "- `listar pendentes`\n"
            "- `total que devo`\n"
            "- `último comprovante`\n"
            "- `total geral`\n"
            "- `ajuda`\n"
            "- `/limpar tudo` *(admin)*\n"
            "- `/corrigir valor` *(admin)*"
        )
        bot.send_message(chat_id=GROUP_ID, text=comandos, parse_mode="Markdown")
