import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)
from processador import processar_comprovante, salvar_comprovante_manual

TOKEN = "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA"
GROUP_ID = -1002626449000

# Estados temporários por usuário
estados = {}

# Configurações de log
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Comando de inicialização
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot de comprovantes iniciado com sucesso!")

# Quando enviar imagem ou PDF
async def receber_arquivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
    elif update.message.document:
        file = await update.message.document.get_file()
    else:
        await update.message.reply_text("❌ Formato não suportado.")
        return

    caminho = f"temp_{user_id}.jpg"
    await file.download_to_drive(caminho)

    resultado = processar_comprovante(caminho)
    if resultado:
        valor, parcelas, horario, taxa, liquido = resultado
        mensagem = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {valor}\n"
            f"💳 Parcelas: {parcelas}\n"
            f"⏰ Horário: {horario}\n"
            f"📉 Taxa aplicada: {taxa}\n"
            f"✅ Valor líquido a pagar: R$ {liquido}"
        )
        await update.message.reply_text(mensagem)
    else:
        estados[user_id] = {"etapa": "valor"}
        await update.message.reply_text("❌ Não consegui ler o valor.\nDigite manualmente como: *1234,56*", parse_mode="Markdown")

# Quando digitar mensagem de texto
async def receber_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    texto = update.message.text.strip()

    if user_id not in estados:
        return

    etapa = estados[user_id].get("etapa")

    if etapa == "valor":
        # Corrige ponto de milhar
        texto = texto.replace(".", "").replace("R$", "").strip()
        try:
            valor = float(texto.replace(",", "."))
            estados[user_id]["valor"] = valor
            estados[user_id]["etapa"] = "parcelas"
            await update.message.reply_text("Digite o número de parcelas (ex: 6):")
        except:
            await update.message.reply_text("❌ Valor inválido. Envie um número como 1234,56")

    elif etapa == "parcelas":
        try:
            parcelas = int(texto)
            estados[user_id]["parcelas"] = parcelas
            estados[user_id]["etapa"] = "horario"
            await update.message.reply_text("Digite o horário da venda (ex: 15:47):")
        except:
            await update.message.reply_text("❌ Parcelas inválidas. Exemplo: 3")

    elif etapa == "horario":
        horario = texto
        dados = estados[user_id]
        resultado = salvar_comprovante_manual(
            dados["valor"], dados["parcelas"], horario
        )
        valor, parcelas, horario, taxa, liquido = resultado
        mensagem = (
            f"📄 Comprovante analisado:\n"
            f"💰 Valor bruto: R$ {valor:.2f}\n"
            f"💳 Parcelas: {parcelas}x\n"
            f"⏰ Horário: {horario}\n"
            f"📉 Taxa aplicada: {taxa}\n"
            f"✅ Valor líquido a pagar: R$ {liquido}"
        )
        await update.message.reply_text(mensagem)
        del estados[user_id]

# Inicialização
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receber_arquivo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_texto))
    app.run_polling()

if __name__ == "__main__":
    main()
