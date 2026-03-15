# modules/telegram_notifier.py  — v2.0
# Telegram alert system with Gist-backed persistence.
# Prevents duplicate notifications across Streamlit session resets, redeploys, etc.
#
# Secrets required (Streamlit Cloud or .env):
#   TELEGRAM_BOT_TOKEN  — bot token from @BotFather
#   TELEGRAM_CHAT_ID    — target chat/channel ID
#   GIST_TOKEN          — GitHub personal access token (gist scope)
#   GIST_ID             — ID of the Gist used for alert state persistence

import os
import json
import time
import hashlib
import requests
from datetime import datetime, timezone


# ── Config ────────────────────────────────────────────────────────────────────
_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
_GIST_TOKEN = os.environ.get("GIST_TOKEN", "")
_GIST_ID    = os.environ.get("GIST_ID", "")          # reuse your existing Gist
_ALERT_FILE = "spxl_alerts.json"                      # filename inside the Gist

_HEADERS_GIST = {
    "Authorization": f"token {_GIST_TOKEN}",
    "Accept": "application/vnd.github+json",
}


# ══════════════════════════════════════════════════════════════════════════════
# GIST PERSISTENCE  (read / write alert state)
# ══════════════════════════════════════════════════════════════════════════════

def _load_alert_state() -> dict:
    """
    Fetch the alert state dict from GitHub Gist.
    Returns an empty dict on any failure (fail-open: better to send a duplicate
    than to silently miss an alert).
    """
    if not (_GIST_TOKEN and _GIST_ID):
        return {}
    try:
        r = requests.get(
            f"https://api.github.com/gists/{_GIST_ID}",
            headers=_HEADERS_GIST,
            timeout=8,
        )
        if r.status_code != 200:
            return {}
        files = r.json().get("files", {})
        if _ALERT_FILE not in files:
            return {}
        raw = files[_ALERT_FILE].get("content", "{}")
        return json.loads(raw)
    except Exception:
        return {}


def _save_alert_state(state: dict) -> bool:
    """Persist alert state dict back to GitHub Gist. Returns True on success."""
    if not (_GIST_TOKEN and _GIST_ID):
        return False
    try:
        payload = {
            "files": {
                _ALERT_FILE: {"content": json.dumps(state, indent=2)}
            }
        }
        r = requests.patch(
            f"https://api.github.com/gists/{_GIST_ID}",
            headers=_HEADERS_GIST,
            json=payload,
            timeout=8,
        )
        return r.status_code == 200
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# CORE SEND
# ══════════════════════════════════════════════════════════════════════════════

def send_alert(message: str, parse_mode: str = "HTML") -> bool:
    """
    Send a raw Telegram message. No deduplication — use send_once() for that.
    Returns True on HTTP 200.
    """
    if not (_BOT_TOKEN and _CHAT_ID):
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage",
            json={
                "chat_id":    _CHAT_ID,
                "text":       message,
                "parse_mode": parse_mode,
            },
            timeout=8,
        )
        return r.status_code == 200
    except Exception:
        return False


def send_once(key: str, message: str, ttl_hours: float = 0) -> bool:
    """
    Send `message` only if `key` has not been sent before (or TTL has expired).

    Parameters
    ----------
    key        : Unique identifier for this alert (e.g. "phase1_110.50").
    message    : HTML-formatted Telegram message.
    ttl_hours  : If > 0, the alert can be re-sent after this many hours.
                 Useful for recurring checks (e.g. CDS crossing a threshold
                 on multiple separate days).
                 If 0 (default), the alert is sent exactly once, forever.

    Returns True if the message was sent, False if it was suppressed.
    """
    state = _load_alert_state()
    now_ts = time.time()

    if key in state:
        if ttl_hours <= 0:
            return False                          # permanent dedup
        sent_at = state[key].get("ts", 0)
        if now_ts - sent_at < ttl_hours * 3600:
            return False                          # within TTL window

    ok = send_alert(message)
    if ok:
        state[key] = {
            "ts":  now_ts,
            "msg": message[:120],                 # store truncated copy for audit
        }
        _save_alert_state(state)
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# MESSAGE BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def build_phase_alert(
    phase_num: int,
    current_price: float,
    phase_level: float,
    alloc_pct: float,
    capital: float = 0.0,
    ref_high: float = 0.0,
) -> str:
    """
    Alert fired when SPXL price crosses a phase entry level.

    Parameters
    ----------
    phase_num     : 1–6
    current_price : Current SPXL price
    phase_level   : Phase trigger price
    alloc_pct     : Allocation % for this phase (0.0–1.0)
    capital       : Optional total capital for absolute $ display
    ref_high      : Optional reference high for drawdown display
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    emoji_map = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "🚨", 6: "💀"}
    emoji = emoji_map.get(phase_num, "⚡")

    dd_str = ""
    if ref_high > 0:
        dd = (current_price - ref_high) / ref_high * 100
        dd_str = f"\n📉 <b>DD desde máximo ref:</b> <code>{dd:.1f}%</code>"

    capital_str = ""
    if capital > 0:
        invest_abs = capital * alloc_pct
        capital_str = f"\n💵 <b>Inversión:</b> <code>${invest_abs:,.0f}</code> ({alloc_pct:.0%})"

    return (
        f"{emoji} <b>SPXL — FASE {phase_num} ACTIVADA</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Precio actual:</b> <code>${current_price:.2f}</code>\n"
        f"🎯 <b>Nivel de fase:</b> <code>${phase_level:.2f}</code>"
        f"{dd_str}"
        f"{capital_str}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 <i>{now_str}</i>\n"
        f"<i>RSU Trading System // Estrategia SPXL</i>"
    )


def build_target_alert(
    scenario: str,
    current_price: float,
    avg_cost: float,
    target_price: float,
    gain_pct: float,
    action: str = "",
) -> str:
    """
    Alert for approaching or hitting a take-profit target.

    Parameters
    ----------
    scenario      : "A", "B", or "C"
    current_price : Current SPXL price
    avg_cost      : Average cost of position
    target_price  : Target take-profit price
    gain_pct      : Current unrealized gain %
    action        : Optional action description (e.g. "Vender 95% de posición")
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sc_colors = {"A": "🟢", "B": "🔵", "C": "🟡"}
    sc_emoji  = sc_colors.get(scenario.upper(), "⚡")

    action_str = f"\n📋 <b>Acción:</b> {action}" if action else ""

    return (
        f"{sc_emoji} <b>SPXL — TARGET ESCENARIO {scenario.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Precio actual:</b> <code>${current_price:.2f}</code>\n"
        f"📈 <b>Ganancia actual:</b> <code>{gain_pct:+.1f}%</code>\n"
        f"🎯 <b>Target:</b> <code>${target_price:.2f}</code>\n"
        f"📊 <b>Coste medio:</b> <code>${avg_cost:.2f}</code>"
        f"{action_str}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 <i>{now_str}</i>\n"
        f"<i>RSU Trading System // Estrategia SPXL</i>"
    )


def build_cds_alert(cds_value: float, threshold: float = 10.7) -> str:
    """Alert when HY CDS spread exceeds the STOP threshold."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"⚠️ <b>ALERTA CDS — COMPRAS PAUSADAS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>BAMLH0A0HYM2:</b> <code>{cds_value:.2f}</code>\n"
        f"🚫 <b>Umbral de stop:</b> <code>{threshold:.2f}</code>\n"
        f"⛔ CDS por encima del umbral — <b>NO ejecutar nuevas fases</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 <i>{now_str}</i>\n"
        f"<i>RSU Trading System // Estrategia SPXL</i>"
    )


def build_trailing_stop_alert(
    scenario: str,
    current_price: float,
    peak_price: float,
    trail_pct: float,
    stop_price: float,
) -> str:
    """Alert when a trailing stop is triggered on a runner position."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"🔴 <b>SPXL — TRAILING STOP ACTIVADO (Escenario {scenario.upper()})</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💥 <b>Precio actual:</b> <code>${current_price:.2f}</code>\n"
        f"📍 <b>Máximo del runner:</b> <code>${peak_price:.2f}</code>\n"
        f"🛑 <b>Stop (−{trail_pct:.0%}):</b> <code>${stop_price:.2f}</code>\n"
        f"📋 Cerrar posición runner ahora\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 <i>{now_str}</i>\n"
        f"<i>RSU Trading System // Estrategia SPXL</i>"
    )


# ══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE: fire all phase checks in one call (use in spxl_strategy.py)
# ══════════════════════════════════════════════════════════════════════════════

def check_and_notify_phases(
    current_price: float,
    levels: dict,              # {"phase1": float, ..., "phase6": float}
    alloc_cfg: list,           # CFG["phase_alloc"]
    ref_high: float = 0.0,
    capital: float = 0.0,
) -> list[int]:
    """
    Check all 6 phase levels and send Telegram alerts for newly crossed ones.
    Uses send_once() with key = f"phase{n}_{level:.2f}" to deduplicate.

    Returns list of phase numbers that triggered in this call.
    """
    triggered = []
    for ph_num in range(1, 7):
        ph_level = levels.get(f"phase{ph_num}", 0.0)
        if ph_level <= 0:
            continue
        if current_price <= ph_level:
            key = f"spxl_phase{ph_num}_{ph_level:.2f}"
            msg = build_phase_alert(
                phase_num=ph_num,
                current_price=current_price,
                phase_level=ph_level,
                alloc_pct=alloc_cfg[ph_num - 1],
                capital=capital,
                ref_high=ref_high,
            )
            sent = send_once(key, msg, ttl_hours=0)    # fire once per level
            if sent:
                triggered.append(ph_num)
    return triggered


def check_and_notify_cds(
    cds_value: float,
    threshold: float = 10.7,
    ttl_hours: float = 24.0,   # re-alert daily if still above threshold
) -> bool:
    """
    Send CDS stop alert if value exceeds threshold.
    Re-alerts every `ttl_hours` hours while condition persists.
    Returns True if alert was sent.
    """
    if cds_value is None or cds_value <= threshold:
        return False
    key = f"spxl_cds_above_{threshold:.1f}"
    msg = build_cds_alert(cds_value, threshold)
    return send_once(key, msg, ttl_hours=ttl_hours)
