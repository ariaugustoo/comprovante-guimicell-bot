import os
import re
import logging
import asyncio
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import processador as proc

# =========================
# CONFIGURAÇÕES DO PROJETO
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN", "8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg8OIA")
GROUP_ID = int(os.getenv("GROUP_ID", "-1002626449000"))
PUBLIC_URL = os.getenv(
    "PUBLIC_URL",
    "https://comprovante-guimicell-bot-vmvr.onrender.com"
)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("guimicell-bot")


# =========================
#   TEXT HELPERS
# =========================
AJUDA_TXT = (
    "🧾 *Comandos e formatos*\n\n"
    "• Para *PIX*: `1234,56 pix`\n"
    "• Para *Cartão*: `1234,56 3x` (1x a 18x)\n"
    "• Marcar último como pago: envie `✅`\n"
    "• `total que devo` – soma dos *pendentes*\n"
    "• `total geral` – pagos + pendentes\n"
    "• `listar pendentes` – últimos pendentes\n"
    "• `listar pagos` – últimos pagos\n"
    "• `último comprovante` – mostra o último registro\n\n"
    "_Dica:_ valores podem ter vírgula ou ponto. Ex: `6.438,76 10x`"
)

async def send_to_group(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    try:
        await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logger.exception("Falha ao enviar mensagem ao grupo: %s", e)


# =========================
#   HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 Bot de comprovantes ativo via webhook!\n\n" + AJUDA_TXT,
        parse_mode="Markdown"
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(AJUDA_TXT, parse_mode="Markdown")

async def handle_emoji_pago(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Marca o último comprovante pendente como pago."""
    row = proc.marcar_ultimo_como_pago()
    if not row:
        await update.message.reply_text("⚠️ Não encontrei pendentes para marcar como pagos.")
        return

    msg = (
        "✅ <b>Marcado como pago</b>\n"
        f"ID: <code>{row['id']}</code>\n"
        f"💰 Bruto: {proc.fmt_brl(row['gross'])}\n"
        f"📉 Taxa: {row['fee_percent']:.2f}%\n"
        f"💳 Parcelas: {row['installments'] or '-'}\n"
        f"✅ Líquido: {proc.fmt_brl(row['net'])}"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def handle_totais(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.lower().strip()

    if "total que devo" in text:
        soma = proc.somar_pendentes()
        await update.message.reply_text(f"🧮 <b>Total pendente</b>: {proc.fmt_brl(soma)}", parse_mode="HTML")
        return

    if "total geral" in text:
        pend = proc.somar_pendentes()
        pagos = proc.somar_pagos()
        total = pend + pagos
        msg = (
            "🧮 <b>Totais</b>\n"
            f"• Pendente: {proc.fmt_brl(pend)}\n"
            f"• Pago: {proc.fmt_brl(pagos)}\n"
            f"• <b>Geral:</b> {proc.fmt_brl(total)}"
        )
        await update.message.reply_text(msg, parse_mode="HTML")

async def handle_listagens(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.lower().strip()

    if "listar pendentes" in text:
        items = proc.listar(pagos=False, limit=15)
        if not items:
            await update.message.reply_text("✅ Não há pendências.")
            return
        linhas = ["⏳ <b>Pendentes (últimos)</b>"]
        for r in items:
            linhas.append(
                f"• ID {r['id']} — {proc.fmt_brl(r['net'])} "
                f"({r['type'].upper()} {f'{r['installments']}x' if r['installments'] else ''})"
            )
        await update.message.reply_text("\n".join(linhas), parse_mode="HTML")
        return

    if "listar pagos" in text:
        items = proc.listar(pagos=True, limit=15)
        if not items:
            await update.message.reply_text("ℹ️ Ainda não há pagos registrados.")
            return
        linhas = ["🟩 <b>Pagos (últimos)</b>"]
        for r in items:
            linhas.append(
                f"• ID {r['id']} — {proc.fmt_brl(r['net'])} "
                f"({r['type'].upper()} {f'{r['installments']}x' if r['installments'] else ''})"
            )
        await update.message.reply_text("\n".join(linhas), parse_mode="HTML")
        return

    if "último comprovante" in text or "ultimo comprovante" in text:
        r = proc.ultimo()
        if not r:
            await update.message.reply_text("ℹ️ Nenhum comprovante registrado ainda.")
            return
        msg = proc.formatar_resposta(r, titulo="📄 Último comprovante")
        await update.message.reply_text(msg, parse_mode="HTML")


PIX_RE = re.compile(r"^\s*([\d\.,]+)\s*pix\s*$", re.IGNORECASE)
CARD_RE = re.compile(r"^\s*([\d\.,]+)\s*(\d{1,2})x\s*$", re.IGNORECASE)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa mensagens de texto: PIX, Cartão e consultas."""
    txt = (update.message.text or "").strip()

    # ✅ marca pago (se o usuário apenas enviar o emoji)
    if txt == "✅":
        await handle_emoji_pago(update, context)
        return

    # Listagens e totais
    low = txt.lower()
    if any(k in low for k in ["total que devo", "total geral"]):
        await handle_totais(update, context)
        return

    if any(k in low for k in ["listar pendentes", "listar pagos", "último comprovante", "ultimo comprovante"]):
        await handle_listagens(update, context)
        return

    # PIX
    m = PIX_RE.match(txt)
    if m:
        bruto = proc.parse_money(m.group(1))
        if bruto is None:
            await update.message.reply_text("⚠️ Valor inválido. Exemplo: `6438,76 pix`", parse_mode="Markdown")
            return
        resp = proc.registrar_pix(bruto, author=update.effective_user)
        await update.message.reply_text(resp, parse_mode="HTML")
        return

    # Cartão
    m = CARD_RE.match(txt)
    if m:
        bruto = proc.parse_money(m.group(1))
        parcelas = int(m.group(2))
        if bruto is None or not (1 <= parcelas <= 18):
            await update.message.reply_text("⚠️ Formato inválido. Ex: `7899,99 10x` (1 a 18x).")
            return
        resp = proc.registrar_cartao(bruto, parcelas, author=update.effective_user)
        await update.message.reply_text(resp, parse_mode="HTML")
        return

    # Caso não reconheça o padrão
    await update.message.reply_text(
        "❓ Não reconheci o formato. Use:\n"
        "• `1234,56 pix`\n"
        "• `1234,56 3x`\n"
        "ou envie `ajuda`",
        parse_mode="Markdown"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tenta ler PDFs (texto nativo). Se não conseguir, pede o valor manual."""
    document = update.message.document
    if not document:
        return

    file = await document.get_file()
    file_path = await file.download_to_drive(custom_path="upload_" + document.file_unique_id)

    valor, parcelas, horario = proc.extrair_de_pdf(file_path)
    if valor:
        # Se PDF tinha valor legível, assumir PIX por padrão e pedir confirmação
        resp = proc.registrar_pix(valor, horario=horario, author=update.effective_user)
        await update.message.reply_text("📎 PDF lido (texto). Se estiver correto, ok.\n" + resp, parse_mode="HTML")
    else:
        await update.message.reply_text(
            "📎 Recebi o arquivo mas não consegui ler o valor.\n"
            "Envie no formato: `1234,56 pix` ou `1234,56 3x`.",
            parse_mode="Markdown"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sem OCR pesado por padrão. Pede entrada manual amigável."""
    await update.message.reply_text(
        "🖼️ Recebi a imagem do comprovante.\n"
        "Para agilizar, envie o valor no formato: `1234,56 pix` ou `1234,56 3x`.",
        parse_mode="Markdown"
    )


# =========================
#   MAIN (WEBHOOK SERVER)
# =========================
def main() -> None:
    proc.init_db()  # garante o banco

    application = Application.builder().token(TOKEN).build()

    # Comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ajuda", ajuda))

    # Documentos e fotos
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Inicia servidor webhook (aiohttp interno do PTB)
    port = int(os.environ.get("PORT", "10000"))
    logger.info("Subindo webhook em 0.0.0.0:%s", port)

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,  # rota secreta
        webhook_url=f"{PUBLIC_URL}/{TOKEN}",
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
