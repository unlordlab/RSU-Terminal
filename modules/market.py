
import streamlit as st
import pandas as pd
import requests
from fredapi import Fred
from datetime import datetime
from config import get_market_index

# --- CONFIGURACIÓN ---
# Sustituye esta clave por tu FRED API key real
FRED_API_KEY = "1455ec63d36773c0e47770e312063789"

# --- FUNCIONES DE EXTRACCIÓN REAL ---

def get_fear_greed_cnn():
    """
    Extrae el índice real directamente de CNN Business.
    Devuelve: valor (0-100), color hex, etiqueta de texto.
    """
    try:
        url = "https://production.dataviz.cnn.io/index/feargreed/static/feargreed"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()

        val = int(data["now"]["value"])

        # Lógica de colores dinámica similar a CNN
        if val <= 25:
            color, label = "#f23645", "EXTREME FEAR"
        elif val <= 45:
            color, label = "#ffa500", "FEAR"
        elif val <= 55:
            color, label = "#888888", "NEUTRAL"
        elif val <= 75:
            color, label = "#00ffad", "GREED"
        else:
            color, label = "#00d1ff", "EXTREME GREED"

        return val, color, label
    except Exception:
        # Fallback neutro por si la API falla
        return 50, "#888888", "NEUTRAL (API Sync...)"

def get_fed_status_real():
    """
    Obtiene el último cambio relevante en el balance de la FED (serie WALCL).
    Devuelve: estado ("QT"/"QE"), color, delta en dólares.
    """
    try:
        fred = Fred(api_key=FRED_API_KEY)
        data = fred.get_series("WALCL").dropna()

        # Nos quedamos con los puntos donde la FED ha cambiado balance
        unique_vals = data[data.diff() != 0]
        last_val = unique_vals.iloc[-1]
        prev_val = unique_vals.iloc[-2]
        delta = float(last_val - prev_val)

        status = "QT (Drenando)" if delta < 0 else "QE (Inyectando)"
        color = "#f23645" if delta < 0 else "#00ffad"

        return status, color, delta
    except Exception:
        # Fallback fijo si falla la API de FRED
        return "QT (Drenando)", "#f23645", -12500000000.0

# --- FUNCIONES DE DATOS (MOCK / ESTÁTICOS) ---

def get_economic_calendar():
    """Eventos económicos clave del día (mock)."""
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "High", "val": "-", "prev": "-"},
    ]

def get_earnings_calendar():
    """Empresas que reportan beneficios próximamente (mock)."""
    return [
        ("AAPL", "Feb 05", "After Market", "High"),
        ("AMZN", "Feb 05", "After Market", "High"),
        ("GOOGL", "Feb 06", "Before Bell", "High"),
        ("TSLA", "Feb 07", "After Market", "High"),
    ]

def get_insider_trading():
    """Rastreador de movimientos de directivos (mock)."""
    return [
        ("NVDA", "CEO", "SELL", "$12.5M"),
        ("MSFT", "CFO", "BUY", "$1.2M"),
        ("PLTR", "DIR", "BUY", "$450K"),
        ("TSLA", "DIR", "SELL", "$2.1M"),
    ]

def get_market_news():
    """Titulares de última hora para el Terminal (mock)."""
    return [
        ("17:45", "Fed's Powell hints at steady rates for Q1."),
        ("17:10", "Tech sector rallies on AI chip demand."),
        ("16:30", "Oil prices jump after inventory drawdown."),
        ("15:50", "EU markets close higher on easing inflation."),
    ]

# --- RENDER PRINCIPAL DEL TERMINAL ---

def render():
    st.set_page_config(page_title="Institutional Terminal", layout="wide")
    st.markdown(
        '<h1 style="margin-top:-50px; text-align:center;">Institutional Terminal</h1>',
        unsafe_allow_html=True,
    )

    # Alturas para simetría
    H_MAIN = "340px"
    H_BOTTOM = "270px"

    # CSS para tooltips, contenedores, etc.
    st.markdown(
        """
        <style>
        .group-container {
            background: #0b0e14;
            border-radius: 12px;
            border: 1px solid #1a1e26;
            margin-bottom: 10px;
        }
        .group-header {
            padding: 8px 14px;
            border-bottom: 1px solid #1a1e26;
            background: #0f1218;
        }
        .group-title {
            color: #ffffff;
            font-size: 12px;
            font-weight: 600;
            margin: 0;
        }
        .group-content {
            padding: 10px 14px;
        }
        .header-with-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
        }
        .info-circle {
            height: 18px;
            width: 18px;
            background: #333;
            color: #888;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            cursor: help;
            border: 1px solid #444;
            position: relative;
        }
        .info-circle .tooltiptext {
            visibility: hidden;
            width: 220px;
            background: #0c0e12;
            color: #fff;
            text-align: left;
            border: 1px solid #1a1e26;
            padding: 12px;
            border-radius: 8px;
            position: absolute;
            z-index: 100;
            right: 0;
            top: 25px;
            font-size: 11px;
            font-weight: normal;
        }
        .info-circle:hover .tooltiptext {
            visibility: visible;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- FILA 1 ---
    col1, col2, col3 = st.columns(3)

    # Columna 1: Market Indices
    with col1:
        indices = [
            ("^GSPC", "S&P 500"),
            ("^IXIC", "NASDAQ 100"),
            ("^DJI", "DOW JONES"),
            ("^RUT", "RUSSELL 2000"),
        ]

        cards = []
        for ticker, name in indices:
            price, pct = get_market_index(ticker)
            cards.append(
                f"""
                <div style="
                    background:#0c0e12;
                    padding:12px 15px;
                    border-radius:10px;
                    margin-bottom:10px;
                    border:1px solid #1a1e26;
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                ">
                    <div>
                        <div style="font-weight:bold; color:white; font-size:13px;">
                            {name}
                        </div>
                        <div style="color:#555; font-size:10px;">
                            {ticker}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:white; font-weight:bold; font-size:13px;">
                            {price:,.2f}
                        </div>
                        <div style="color:{'#00ffad' if pct >= 0 else '#f23645'}; font-size:11px;">
                            {pct:+.2f}%
                        </div>
                    </div>
                </div>
                """
            )
        indices_html = "".join(cards)

        st.markdown(
            f"""
            <div class="group-container">
                <div class="group-header">
                    <p class="group-title">Market Indices</p>
                </div>
                <div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">
                    {indices_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Columna 2: Economic Calendar
    with col2:
        evs = get_economic_calendar()
        rows = []
        for ev in evs:
            color = "#f23645" if ev["imp"] == "High" else "#ffa500"
            rows.append(
                f"""
                <div style="
                    padding:10px;
                    border-bottom:1px solid #1a1e26;
                    display:flex;
                    align-items:center;
                ">
                    <div style="color:#888; font-size:10px; width:45px;">
                        {ev['time']}
                    </div>
                    <div style="flex-grow:1; margin-left:10px;">
                        <div style="color:white; font-size:11px;">
                            {ev['event']}
                        </div>
                        <div style="color:{color}; font-size:8px;">
                            {ev['imp']} IMPACT
                        </div>
                    </div>
                    <div style="text-align:right; font-size:9px; color:#777;">
                        <div>Val: {ev['val']}</div>
                        <div>Prev: {ev['prev']}</div>
                    </div>
                </div>
                """
            )
        ev_html = "".join(rows)

        st.markdown(
            f"""
            <div class="group-container">
                <div class="group-header">
                    <p class="group-title">Economic Calendar</p>
                </div>
                <div class="group-content" style="background:#11141a; height:{H_MAIN}; overflow-y:auto;">
                    {ev_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Columna 3: Reddit Social Pulse (mock tickers calientes)
    with col3:
        hot_tickers = ["NVDA", "TSLA", "PLTR", "AAPL", "AMD"]
        reddit_html = "".join(
            [
                f"""
                <div style="
                    background:#0c0e12;
                    padding:8px 15px;
                    border-radius:8px;
                    margin-bottom:6px;
                    border:1px solid #1a1e26;
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                ">
                    <span style="color:#00ffad; font-weight:bold; font-size:12px;">
                        {tkr}
                    </span>
                    <span style="color:#f23645; font-size:8px;">
                        HOT 🔥
                    </span>
                </div>
                """
                for tkr in hot_tickers
            ]
        )

        st.markdown(
            f"""
            <div class="group-container">
                <div class="group-header">
                    <p class="group-title">Reddit Social Pulse</p>
                </div>
                <div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; overflow-y:auto;">
                    {reddit_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --- FILA 2 (Fear & Greed, Sectors, Risk & Fed) ---
    st.write("")
    c1, c2, c3 = st.columns(3)

    # Fear & Greed (CNN)
    with c1:
        fg_val, fg_color, fg_label = get_fear_greed_cnn()
        st.markdown(
            f"""
            <div class="group-container">
                <div class="group-header">
                    <div class="header-with-info">
                        <span class="group-title">Fear & Greed (CNN)</span>
                        <div class="info-circle">
                            ?
                            <span class="tooltiptext">
                                Dato real de CNN Business. Refleja el sentimiento
                                de mercado basado en 7 indicadores técnicos.
                            </span>
                        </div>
                    </div>
                </div>
                <div class="group-content" style="
                    background:#11141a;
                    height:{H_MAIN};
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    justify-content:center;
                ">
                    <div style="font-size:4rem; font-weight:bold; color:{fg_color};">
                        {fg_val}
                    </div>
                    <div style="color:white; font-size:0.9rem; font-weight:bold;">
                        {fg_label}
                    </div>
                    <div style="
                        width:80%;
                        background:#0c0e12;
                        height:8px;
                        border-radius:4px;
                        margin-top:20px;
                        border:1px solid #1a1e26;
                    ">
                        <div style="
                            width:{fg_val}%;
                            background:{fg_color};
                            height:100%;
                            border-radius:4px;
                        "></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Sectors Heatmap (mock)
    with c2:
        sectors = [
            ("TECH", +1.24),
            ("FINL", -0.45),
            ("ENER", +2.10),
            ("CONS", -0.80),
            ("HLTH", +0.12),
            ("UTIL", -0.25),
        ]

        sec_html = "".join(
            [
                f"""
                <div style="
                    background:{'#00ffad11' if p >= 0 else '#f2364511'};
                    border:1px solid {'#00ffad44' if p >= 0 else '#f2364544'};
                    padding:10px;
                    border-radius:6px;
                    text-align:center;
                ">
                    <div style="color:white; font-size:9px;">
                        {name}
                    </div>
                    <div style="color:{'#00ffad' if p >= 0 else '#f23645'};
                                font-size:11px; font-weight:bold;">
                        {p:+.2f}%
                    </div>
                </div>
                """
                for name, p in sectors
            ]
        )

        st.markdown(
            f"""
            <div class="group-container">
                <div class="group-header">
                    <p class="group-title">Sectors Heatmap</p>
                </div>
                <div class="group-content" style="
                    background:#11141a;
                    height:{H_MAIN};
                    padding:15px;
                    display:grid;
                    grid-template-columns:repeat(3,1fr);
                    gap:10px;
                ">
                    {sec_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Risk & Fed (VIX + FED balance)
    with c3:
        v_val, _ = get_market_index("^VIX")
        f_status, f_color, f_delta = get_fed_status_real()

        st.markdown(
            f"""
            <div class="group-container">
                <div class="group-header">
                    <div class="header-with-info">
                        <span class="group-title">Risk & Fed</span>
                        <div class="info-circle">
                            ?
                            <span class="tooltiptext">
                                <b>QT:</b> La FED reduce balance (retira liquidez).<br>
                                <b>QE:</b> La FED expande balance (inyecta liquidez).
                            </span>
                        </div>
                    </div>
                </div>
                <div class="group-content" style="
                    background:#11141a;
                    height:{H_MAIN};
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    justify-content:center;
                ">
                    <div style="font-size:0.7rem; color:#888;">
                        VIX INDEX
                    </div>
                    <div style="
                        font-size:3.2rem;
                        font-weight:bold;
                        color:{'#f23645' if float(v_val) > 20 else '#00ffad'};
                    ">
                        {float(v_val):.2f}
                    </div>
                    <hr style="width:70%; border-color:#1a1e26; margin:15px;">
                    <div style="
                        background:{f_color}22;
                        color:{f_color};
                        padding:8px 15px;
                        border-radius:6px;
                        font-weight:bold;
                    ">
                        {f_status}
                    </div>
                    <div style="color:#444; font-size:10px; margin-top:10px;">
                        Weekly Delta: {f_delta/1_000_000_000:+.2f}B
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --- FILA 3 (Earnings, Insider, News) ---
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)

    # Earnings Calendar
    with f3c1:
        earn_html = "".join(
            [
                f"""
                <div style="
                    background:#0c0e12;
                    padding:10px;
                    border-radius:8px;
                    margin-bottom:8px;
                    border:1px solid #1a1e26;
                    display:flex;
                    justify-content:space-between;
                ">
                    <div>
                        <div style="color:#00ffad; font-size:12px; font-weight:bold;">
                            {ticker}
                        </div>
                        <div style="color:#444; font-size:9px;">
                            {date}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#888; font-size:8px;">
                            {time}
                        </div>
                        <div style="color:#f23645; font-size:8px;">
                            {imp} IMPACT
                        </div>
                    </div>
                </div>
                """
                for ticker, date, time, imp in get_earnings_calendar()
            ]
        )

        st.markdown(
            f"""
            <div class="group-container">
                <div class="group-header">
                    <p class="group-title">Earnings Calendar</p>
                </div>
                <div class="group-content" style="
                    background:#11141a;
                    height:{H_BOTTOM};
                    padding:15px;
                    overflow-y:auto;
                ">
                    {earn_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Insider Tracker
    with f3c2:
        ins_html = "".join(
            [
                f"""
                <div style="
                    background:#0c0e12;
                    padding:10px;
                    border-radius:8px;
                    margin-bottom:8px;
                    border:1px solid #1a1e26;
                    display:flex;
                    justify-content:space-between;
                ">
                    <div>
                        <div style="color:white; font-size:11px;">
                            {ticker}
                        </div>
                        <div style="color:#555; font-size:9px;">
                            {person}
                        </div>
                    </div>
                    <div style="
                        color:{'#00ffad' if side == 'BUY' else '#f23645'};
                        font-size:10px;
                        font-weight:bold;
                    ">
                        {side}
                    </div>
                </div>
                """
                for ticker, person, side, amount in get_insider_trading()
            ]
        )

        st.markdown(
            f"""
            <div class="group-container">
                <div class="group-header">
                    <p class="group-title">Insider Tracker</p>
                </div>
                <div class="group-content" style="
                    background:#11141a;
                    height:{H_BOTTOM};
                    padding:15px;
                    overflow-y:auto;
                ">
                    {ins_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # News Terminal
    with f3c3:
        news_html = "".join(
            [
                f"""
                <div style="
                    padding:10px;
                    border-bottom:1px solid #1a1e26;
                ">
                    <div style="color:#00ffad; font-size:9px;">
                        NEWS {time}
                    </div>
                    <div style="color:white; font-size:11px; margin-top:4px;">
                        {text}
                    </div>
                </div>
                """
                for time, text in get_market_news()
            ]
        )

        st.markdown(
            f"""
            <div class="group-container">
                <div class="group-header">
                    <p class="group-title">News Terminal</p>
                </div>
                <div class="group-content" style="
                    background:#11141a;
                    height:{H_BOTTOM};
                    overflow-y:auto;
                ">
                    {news_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

if __name__ == "__main__":
    render()

