import re
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Tabela de taxas de cartão por número de parcelas
TAXAS_CARTAO = {
    1: 4.39,
    2: 5.19,
    3: 6.19,
    4: 6.59,
    5: 7.19,
    6: 8.29,
    7: 9.19,
    8: 9.99,
    9: 10.29,
    10: 10.88,
    11: 11.99,
    12: 12.52,
    13: 13.69,
    14: 14.19,
    15: 14.69,
    16: 15.19,
    17: 15.89,
    18: 16.84,
}

# Lista de comprovantes analisados
comprovantes = []

def normalizar_valor(valor_str):
    valor_str = valor_str.strip().replace("R$", "").replace(" ", "")
    valor_str = valor_str.replace(".", "").replace(",", ".")
    return float(valor_str)

def calcular_valor_liquido(valor_bruto, parcelas):
    if parcelas == 0:
        taxa = 0.2
    else:
        taxa = TAXAS_CARTAO.get(parcelas, 0)

    valor_liquido = valor_bruto * (1 - taxa / 100)
    return round(valor_liquido, 2), taxa

def extrair_valor_e_parcelas(texto):
    texto = texto.lower().replace("x", " x")
    match = re.match(r'([\d.,]+)\s*(\d{1,2})\s*x', texto)
    if match:
        valor = normalizar_valor(match.group(1))
        parcelas = int(match.group(2))
        return valor, parcelas

    if 'pix' in texto:
        match = re.match(r'([\d.,]+)', texto)
        if match:
            valor = normalizar_valor(match.group(1))
            return valor, 0

    return None, None

def processar_mensagem(mensagem, bot, chat_id, user_id):
    mensagem = mensagem.strip().lower()

    if mensagem == "ajuda":
        bot.send_message(chat_id=chat_id, text="❗ Envie um valor seguido de 'pix' ou número de parcelas, ex:\n`1438,90 pix`\n`7432,90 12x`", parse_mode='Markdown')
        return

    if mensagem == "listar pagos":
        pagos = [c for c in comprovantes if c["pago"]]
        if not pagos:
            bot.send_message(chat_id=chat_id, text="✅ Nenhum comprovante marcado como pago.")
        else:
            resposta = "\n\n".join([f"💸 {c['valor_bruto']:,.2f} → R$ {c['valor_liquido']:,.2f}" for c in pagos])
            bot.send_message(chat_id=chat_id, text=f"✅ Comprovantes pagos:\n{resposta}")
        return

    if mensagem == "total que devo":
        pendentes = [c for c in comprovantes if not c["pago"]]
        total = sum(c["valor_liquido"] for c in pendentes)
        bot.send_message(chat_id=chat_id, text=f"💰 Total em aberto: R$ {total:,.2f}")
        return

    if mensagem.endswith("✅"):
        if comprovantes:
            comprovantes[-1]["pago"] = True
            bot.send_message(chat_id=chat_id, text="✅ Comprovante marcado como pago!")
        return

    valor, parcelas = extrair_valor_e_parcelas(mensagem)

    if valor is None:
        bot.send_message(chat_id=chat_id, text="❗ Envie um valor seguido de 'pix' ou número de parcelas, ex:\n`1438,90 pix`\n`7432,90 12x`", parse_mode='Markdown')
        return

    horario = datetime.now().strftime("%H:%M")
    valor_liquido, taxa = calcular_valor_liquido(valor, parcelas)

    comprovante = {
        "valor_bruto": valor,
        "parcelas": parcelas,
        "horario": horario,
        "taxa": taxa,
        "valor_liquido": valor_liquido,
        "pago": False
    }

    comprovantes.append(comprovante)

    parcelas_texto = f"{parcelas}" if parcelas > 0 else "-"
    resposta = (
        "📄 *Comprovante analisado:*\n"
        f"💰 Valor bruto: R$ {valor:,.2f}\n"
        f"📄 Parcelas: {parcelas_texto}\n"
        f"⏰ Horário: {horario}\n"
        f"📉 Taxa aplicada: {taxa}%\n"
        f"✅ Valor líquido a pagar: R$ {valor_liquido:,.2f}"
    )

    bot.send_message(chat_id=chat_id, text=resposta, parse_mode="Markdown")
