import os
import re
import sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

import pdfplumber

DB_PATH = os.getenv("DB_PATH", "data.db")

# Tabela de taxas de CRÉDITO (percentuais descontados do lojista) – 1x a 18x
CREDIT_FEES = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

PIX_FEE = 0.20  # %


# =========================
#    DB UTIL
# =========================
def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            type TEXT CHECK(type IN ('pix','card')) NOT NULL,
            gross REAL NOT NULL,
            installments INTEGER,
            fee_percent REAL NOT NULL,
            net REAL NOT NULL,
            time_str TEXT,
            paid INTEGER DEFAULT 0,
            user_id INTEGER,
            username TEXT
        )
        """)
        con.commit()


def row_to_dict(row) -> Dict[str, Any]:
    keys = ["id","created_at","type","gross","installments","fee_percent","net","time_str","paid","user_id","username"]
    return {k: row[i] for i, k in enumerate(keys)}


# =========================
#   PARSE / FORMAT
# =========================
def parse_money(s: str) -> Optional[float]:
    """Aceita '6.438,76' ou '6438.76' e retorna float (em reais)."""
    if not s:
        return None
    s = s.strip()
    s = s.replace("R$", "").replace(" ", "")
    # Se tiver vírgula decimal
    if "," in s and "." in s:
        # Remover separador de milhar e trocar vírgula por ponto
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def fmt_brl(v: float) -> str:
    """Formata 1234.5 -> R$ 1.234,50"""
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def fee_for_installments(n: int) -> float:
    return CREDIT_FEES.get(n, 0.0)


def compute_net(gross: float, fee_percent: float) -> float:
    return round(gross * (1 - fee_percent / 100.0), 2)


def agora_hora_str() -> str:
    return datetime.now().strftime("%H:%M")


# =========================
#   REGISTROS
# =========================
def registrar_pix(gross: float, horario: Optional[str] = None, author=None) -> str:
    fee = PIX_FEE
    net = compute_net(gross, fee)
    r = _inserir("pix", gross, None, fee, net, horario or agora_hora_str(), author)
    return formatar_resposta(r, titulo="📄 Comprovante analisado (PIX)")


def registrar_cartao(gross: float, parcelas: int, horario: Optional[str] = None, author=None) -> str:
    fee = fee_for_installments(parcelas)
    net = compute_net(gross, fee)
    r = _inserir("card", gross, parcelas, fee, net, horario or agora_hora_str(), author)
    return formatar_resposta(r, titulo="📄 Comprovante analisado (Cartão)")


def _inserir(tipo: str, gross: float, installments: Optional[int], fee: float, net: float,
             time_str: str, author) -> Dict[str, Any]:
    with connect() as con:
        cur = con.execute("""
            INSERT INTO receipts (created_at, type, gross, installments, fee_percent, net, time_str, paid, user_id, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, (
            datetime.now().isoformat(timespec="seconds"),
            tipo, gross, installments, fee, net, time_str,
            getattr(author, "id", None),
            getattr(author, "username", None),
        ))
        con.commit()
        rid = cur.lastrowid
        row = con.execute("SELECT * FROM receipts WHERE id = ?", (rid,)).fetchone()
        return row_to_dict(row)


def marcar_ultimo_como_pago() -> Optional[Dict[str, Any]]:
    with connect() as con:
        row = con.execute("SELECT * FROM receipts WHERE paid = 0 ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            return None
        rid = row[0]
        con.execute("UPDATE receipts SET paid = 1 WHERE id = ?", (rid,))
        con.commit()
        row = con.execute("SELECT * FROM receipts WHERE id = ?", (rid,)).fetchone()
        return row_to_dict(row)


def somar_pendentes() -> float:
    with connect() as con:
        v = con.execute("SELECT COALESCE(SUM(net), 0) FROM receipts WHERE paid = 0").fetchone()[0]
        return round(float(v or 0), 2)


def somar_pagos() -> float:
    with connect() as con:
        v = con.execute("SELECT COALESCE(SUM(net), 0) FROM receipts WHERE paid = 1").fetchone()[0]
        return round(float(v or 0), 2)


def listar(pagos: bool, limit: int = 15):
    with connect() as con:
        rows = con.execute(
            "SELECT * FROM receipts WHERE paid = ? ORDER BY id DESC LIMIT ?",
            (1 if pagos else 0, limit)
        ).fetchall()
        return [row_to_dict(r) for r in rows]


def ultimo() -> Optional[Dict[str, Any]]:
    with connect() as con:
        r = con.execute("SELECT * FROM receipts ORDER BY id DESC LIMIT 1").fetchone()
        return row_to_dict(r) if r else None


# =========================
#   FORMATAÇÃO DE RESPOSTA
# =========================
def formatar_resposta(r: Dict[str, Any], titulo: str = "📄 Comprovante analisado") -> str:
    parcelas = f"{r['installments']}x" if r['installments'] else "-"
    return (
        f"{titulo}:\n"
        f"💰 Valor bruto: {fmt_brl(r['gross'])}\n"
        f"💳 Parcelas: {parcelas}\n"
        f"⏰ Horário: {r['time_str'] or '-'}\n"
        f"📉 Taxa aplicada: {r['fee_percent']:.2f}%\n"
        f"✅ Valor líquido a pagar: <b>{fmt_brl(r['net'])}</b>"
    )


# =========================
#   EXTRAÇÃO BÁSICA DE PDF
# =========================
VALOR_REGEX = re.compile(
    r"(?<!\d)(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})|\d+\.\d{2})(?!\d)"
)
PARCELAS_REGEX = re.compile(r"(\d{1,2})\s*x", re.IGNORECASE)
HORA_REGEX = re.compile(r"\b([01]?\d|2[0-3])[:h]([0-5]\d)\b")

def extrair_de_pdf(path: str) -> Tuple[Optional[float], Optional[int], Optional[str]]:
    """
    Tenta extrair valor/parcelas/horário de PDFs com texto (sem OCR).
    Retorna (valor, parcelas, horario_str).
    """
    try:
        with pdfplumber.open(path) as pdf:
            text = ""
            for page in pdf.pages[:3]:  # primeiras páginas bastam
                text += "\n" + (page.extract_text() or "")
            if not text.strip():
                return None, None, None

            vals = [parse_money(m.group(1)) for m in VALOR_REGEX.finditer(text)]
            valor = max(vals) if vals else None  # heurística: maior valor no PDF

            par = None
            m = PARCELAS_REGEX.search(text)
            if m:
                p = int(m.group(1))
                if 1 <= p <= 18:
                    par = p

            hora = None
            hm = HORA_REGEX.search(text)
            if hm:
                hora = f"{hm.group(1).zfill(2)}:{hm.group(2)}"

            return valor, par, hora
    except Exception:
        return None, None, None
