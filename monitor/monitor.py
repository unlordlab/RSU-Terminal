#!/usr/bin/env python3
"""
monitor.py — RSU Portfolio Telegram Notifier
Compara el estado actual del Google Sheet con el snapshot anterior
y envía notificaciones Telegram cuando hay entradas o salidas.

Uso:
    python monitor.py

Cron (cada 5 minutos):
    */5 * * * * /usr/bin/python3 /ruta/a/monitor.py >> /ruta/a/monitor.log 2>&1
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
# Rellena estos valores o pásalos como variables de entorno
SHEET_URL      = os.environ.get("URL_CARTERA", "")          # URL CSV del Google Sheet
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")       # Token del bot
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "")     # Tu chat ID

SNAPSHOT_FILE  = Path(__file__).parent / "snapshot.json"    # Estado anterior
LOG_PREFIX     = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"

# ── HELPERS ───────────────────────────────────────────────────────────────────
def log(msg: str):
    print(f"{LOG_PREFIX} {msg}", flush=True)

def send_telegram(msg: str) -> bool:
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=10
        )
        return r.status_code == 200
    except Exception as e:
        log(f"ERROR Telegram: {e}")
        return False

def clean_numeric(value):
    if pd.isna(value):
        return 0.0
    val_str = str(value).strip().replace("$", "").replace("%", "").replace(" ", "")
    if "," in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    try:
        return float(val_str)
    except Exception:
        return 0.0

def load_sheet() -> pd.DataFrame:
    df = pd.read_csv(SHEET_URL).dropna(how="all")
    df.columns = [c.strip() for c in df.columns]
    df["Estado"] = df["Estado"].astype(str).str.strip().str.upper()
    df["Ticker"] = df["Ticker"].astype(str).str.strip()
    df["Fecha"]  = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha", "Ticker"])
    for col in ["Precio Compra", "Precio Actual"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric)
    return df

def load_snapshot() -> dict:
    if SNAPSHOT_FILE.exists():
        with open(SNAPSHOT_FILE) as f:
            return json.load(f)
    return {}

def save_snapshot(data: dict):
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    log("Iniciando check...")

    if not SHEET_URL or not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        log("ERROR: Faltan variables de entorno. Revisa URL_CARTERA, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID")
        return

    # Cargar sheet
    try:
        df = load_sheet()
    except Exception as e:
        log(f"ERROR cargando sheet: {e}")
        return

    abiertas = df[df["Estado"] == "ABIERTA"].copy()

    # Estado actual: dict {ticker: {precio_compra, fecha}}
    current = {}
    for _, row in abiertas.iterrows():
        ticker = row["Ticker"]
        current[ticker] = {
            "precio_compra": float(row.get("Precio Compra", 0)),
            "fecha": row["Fecha"].strftime("%d/%m/%Y") if pd.notna(row["Fecha"]) else "—",
        }

    # Cargar snapshot anterior
    previous = load_snapshot()

    tickers_now  = set(current.keys())
    tickers_prev = set(previous.keys())

    entradas = tickers_now  - tickers_prev
    salidas  = tickers_prev - tickers_now

    log(f"Abiertas ahora:    {sorted(tickers_now)}")
    log(f"Snapshot anterior: {sorted(tickers_prev)}")
    log(f"Entradas:  {sorted(entradas)}")
    log(f"Salidas:   {sorted(salidas)}")

    if not entradas and not salidas:
        log("Sin cambios.")
        save_snapshot(current)
        return

    # ── Notificar entradas ────────────────────────────────────────────────
    for ticker in sorted(entradas):
        info = current[ticker]
        msg = (
            f"🟢 <b>NUEVA ENTRADA</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 Ticker:        <code>{ticker}</code>\n"
            f"💰 P. Compra:     <code>${info['precio_compra']:,.2f}</code>\n"
            f"📅 Fecha:         <code>{info['fecha']}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>[CARTERA RSU // POSICIÓN ABIERTA]</i>"
        )
        ok = send_telegram(msg)
        log(f"ENTRADA {ticker} → Telegram {'✅' if ok else '❌'}")

    # ── Notificar salidas ─────────────────────────────────────────────────
    for ticker in sorted(salidas):
        info = previous[ticker]

        # Buscar P&L en cerradas si está disponible
        cerrada = df[(df["Estado"] == "CERRADA") & (df["Ticker"].str.strip().str.upper() == ticker.strip().upper())]
        pnl_str = "—"
        if not cerrada.empty and "Precio Actual" in cerrada.columns and "Precio Compra" in cerrada.columns:
            last = cerrada.sort_values("Fecha", ascending=False).iloc[0]
            pc = float(last["Precio Compra"])
            pa = float(last["Precio Actual"])
            if pc != 0:
                pnl = (pa - pc) / pc * 100
                sign = "+" if pnl >= 0 else ""
                pnl_str = f"{sign}{pnl:.2f}%"
                emoji = "✅" if pnl >= 0 else "❌"
            else:
                emoji = "📤"
        else:
            emoji = "📤"

        msg = (
            f"🔴 <b>POSICIÓN CERRADA</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📉 Ticker:        <code>{ticker}</code>\n"
            f"💰 P. Entrada:    <code>${info['precio_compra']:,.2f}</code>\n"
            f"📊 P&L:           <code>{pnl_str}</code> {emoji}\n"
            f"📅 Entrada:       <code>{info['fecha']}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>[CARTERA RSU // POSICIÓN CERRADA]</i>"
        )
        ok = send_telegram(msg)
        log(f"SALIDA {ticker} P&L:{pnl_str} → Telegram {'✅' if ok else '❌'}")

    save_snapshot(current)
    log("Check completado.")

if __name__ == "__main__":
    main()
