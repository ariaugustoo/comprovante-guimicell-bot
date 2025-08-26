import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from processador import processar_comprovante, armazenar_comprovante, calcular_total_pendente, listar_comprovantes, marcar_comprovante_como_pago, obter_ultimo_comprovante

# === CONFIGURAÇÕES ===
TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002626449000
TAXA_PIX = 0.2  # 0,2%

# === LOG ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === MENSAGEM DE AJUDA ===
AJUDA = """
📌 *Comandos disponíveis:*
• `valor pix` → Aplica 0,2% de taxa e responde valor líquido
• `valor 3x` → Aplica taxa de crédito conforme parcelas
• `✅` → Marca último comprovante como pago
• `total que devo` → Mostra o total de repasses pendentes
• `listar pendentes` → Lista comprovantes pendentes
• `listar pagos` → Lista comprovantes já pagos
• `último comprovante` → Mostra último comprovante enviado
• `total geral` → Total geral de valores processados
"""

# === HANDLER PRINCIPAL ===
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.chat_id != GROUP_ID:
        return

    message = update.message
    text = message.text.strip() if message.text else ""
    fotos = message.photo
    documento = message.document

    if fotos:
        await message.reply_text("🧐 Lendo imagem, um momento...")
        resultado = await processar_comprovante(message, context.bot, tipo="foto")
        if resultado:
            armazenar_comprovante(resultado)
            resposta = (
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {resultado['valor_bruto']:.2f}\n"
                f"💳 Parcelas: {(f\"{resultado['parcelas']}x\" if resultado['parcelas'] else 'N/A')}\n"
                f"⏰ Horário: {resultado['horario']}\n"
                f"📉 Taxa aplicada: {resultado['taxa_aplicada']}%\n"
                f"✅ Valor líquido a pagar: R$ {resultado['valor_liquido']:.2f}"
            )
            await message.reply_text(resposta)
        else:
            await message.reply_text("❌ Não consegui entender a imagem. Envie o valor manualmente.")
        return

    if documento and documento.file_name.endswith(".pdf"):
        await message.reply_text("🧐 Lendo PDF, um momento...")
        resultado = await processar_comprovante(message, context.bot, tipo="pdf")
        if resultado:
            armazenar_comprovante(resultado)
            resposta = (
                f"📄 Comprovante analisado:\n"
                f"💰 Valor bruto: R$ {resultado['valor_bruto']:.2f}\n"
                f"💳 Parcelas: {(f\"{resultado['parcelas']}x\" if resultado['parcelas'] else 'N/A')}\n"
                f"⏰ Horário: {resultado['horario']}\n"
                f"📉 Taxa aplicada: {resultado['taxa_aplicada']}%\n"
                f"✅ Valor líquido a pagar: R$ {resultado['valor_liquido']:.2f}"
            )
            await message.reply_text(resposta)
        else:
            await message.reply_text("❌ Não consegui ler o PDF. Envie o valor manualmente.")
        return

    if "pix" in text.lower():
        try:
            valor = float(text.lower().replace("pix", "").replace("r$", "").replace(",", ".").strip())
            taxa = TAXA_PIX
            liquido = valor * (1 - taxa / 100)
            await message.reply_text(
                f"💸 *PIX com taxa de {taxa}%*\n"
                f"Valor bruto: R$ {valor:.2f}\n"
                f"Valor líquido a repassar: R$ {liquido:.2f}"
            )
            armazenar_comprovante({
                'valor_bruto': valor,
                'valor_liquido': liquido,
                'taxa_aplicada': taxa,
                'horario': message.date.strftime("%H:%M"),
                'parcelas': None,
                'pago': False
            })
        except:
            await message.reply_text("❌ Não entendi o valor. Ex: `6438,76 pix`")
        return

    if "x" in text.lower() and "pix" not in text.lower():
        try:
            partes = text.lower().split("x")
            valor = float(partes[0].replace("r$", "").replace(",", ".").strip())
            parcelas = int(partes[1].strip())
            from processador import calcular_taxa_cartao
            taxa = calcular_taxa_cartao(parcelas)
            liquido = valor * (1 - taxa / 100)
            await message.reply_text(
                f"💳 *Cartão em {parcelas}x com taxa de {taxa}%*\n"
                f"Valor bruto: R$ {valor:.2f}\n"
                f"Valor líquido a repassar: R$ {liquido:.2f}"
            )
            armazenar_comprovante({
                'valor_bruto': valor,
                'valor_liquido': liquido,
                'taxa_aplicada': taxa,
                'horario': message.date.strftime("%H:%M"),
                'parcelas': parcelas,
                'pago': False
            })
        except:
            await message.reply_text("❌ Formato inválido. Ex: `6899,99 10x`")
        return

    if "✅" in text:
        msg = marcar_comprovante_como_pago()
        await message.reply_text(msg)
        return

    if "total que devo" in text.lower():
        total = calcular_total_pendente()
        await message.reply_text(f"💰 Total pendente a pagar: R$ {total:.2f}")
        return

    if "listar pendentes" in text.lower():
        lista = listar_comprovantes(pago=False)
        await message.reply_text(lista)
        return

    if "listar pagos" in text.lower():
        lista = listar_comprovantes(pago=True)
        await message.reply_text(lista)
        return

    if "último comprovante" in text.lower():
        ultimo = obter_ultimo_comprovante()
        await message.reply_text(ultimo)
        return

    if "total geral" in text.lower():
        from processador import calcular_total_geral
        total = calcular_total_geral()
        await message.reply_text(f"📊 Total geral de valores processados: R$ {total:.2f}")
        return

    if "ajuda" in text.lower():
        await message.reply_markdown(AJUDA)
        return

# === INICIAR APLICAÇÃO ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle))
    print("🤖 Bot rodando com webhook...")
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        url_path=TOKEN.split(":")[0],
        webhook_url=f"https://comprovante-guimicell-bot-vmvr.onrender.com/{TOKEN.split(':')[0]}"
    )
