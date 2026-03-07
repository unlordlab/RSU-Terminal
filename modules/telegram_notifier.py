import requests
import streamlit as st

def send_alert(message: str) -> bool:
    """Envía mensaje al chat configurado. Devuelve True si OK."""
    try:
        token   = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url     = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={
            "chat_id":    chat_id,
            "text":       message,
            "parse_mode": "HTML"
        }, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def build_phase_alert(phase: int, current_price: float,
                      level: float, allocation_pct: float) -> str:
    icons = {1: "🟡", 2: "🟠", 3: "🔴", 4: "🚨"}
    return (
        f"{icons.get(phase,'📍')} <b>SPXL — FASE {phase} ACTIVADA</b>\n\n"
        f"💰 Precio actual:  <code>${current_price:.2f}</code>\n"
        f"🎯 Nivel de fase:  <code>${level:.2f}</code>\n"
        f"📊 Capital a invertir: <code>{allocation_pct:.0%}</code>\n\n"
        f"⚡ Ejecutar compra según protocolo RSU."
    )


def build_target_alert(current_price: float, avg_cost: float,
                       target_price: float) -> str:
    gain = (current_price - avg_cost) / avg_cost * 100
    return (
        f"🎯 <b>SPXL — OBJETIVO ALCANZADO</b>\n\n"
        f"💰 Precio actual:  <code>${current_price:.2f}</code>\n"
        f"📈 Precio medio:   <code>${avg_cost:.2f}</code>\n"
        f"✅ Take profit:    <code>${target_price:.2f}</code>\n"
        f"💵 Ganancia:       <code>+{gain:.1f}%</code>\n\n"
        f"🔴 EJECUTAR SALIDA TOTAL INMEDIATAMENTE."
    )


def build_cds_alert(cds_value: float) -> str:
    return (
        f"⚠️ <b>ALERTA CDS — STOP SISTÉMICO</b>\n\n"
        f"📊 CDS actual: <code>{cds_value:.2f}</code>\n"
        f"🚫 Umbral:     <code>10.70</code>\n\n"
        f"🛑 DETENER TODAS LAS COMPRAS INMEDIATAMENTE.\n"
        f"El stop sistémico tiene prioridad absoluta."
    )
