# market.py
import streamlit as st
from datetime import datetime
from config import get_market_index, get_cnn_fear_greed
import requests

# --- FUNCIONES DE OBTENCIÓN DE DATOS (sin cambios) ---

def get_economic_calendar():
    """Eventos económicos clave del día."""
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "High", "val": "-", "prev": "-"},
    ]

def get_crypto_prices():
    """Precios de referencia de criptoactivos."""
    return [
        ("BTC", "104,231.50", "+2.4%"),
        ("ETH", "3,120.12", "-1.1%"),
        ("SOL", "245.88", "+5.7%"),
    ]

def get_earnings_calendar():
    """Empresas que reportan beneficios próximamente."""
    return [
        ("AAPL", "Feb 05", "After Market", "High"),
        ("AMZN", "Feb 05", "After Market", "High"),
        ("GOOGL", "Feb 06", "Before Bell", "High"),
        ("TSLA", "Feb 07", "After Market", "High"),
    ]

def get_insider_trading():
    """Rastreador de movimientos de directivos."""
    return [
        ("NVDA", "CEO", "SELL", "$12.5M"),
        ("MSFT", "CFO", "BUY", "$1.2M"),
        ("PLTR", "DIR", "BUY", "$450K"),
        ("TSLA", "DIR", "SELL", "$2.1M"),
    ]

def get_market_news():
    """Titulares de última hora para el Terminal."""
    return [
        ("17:45", "Fed's Powell hints at steady rates for Q1."),
        ("17:10", "Tech sector rallies on AI chip demand."),
        ("16:30", "Oil prices jump after inventory drawdown."),
        ("15:50", "EU markets close higher on easing inflation."),
    ]

def get_fed_liquidity():
    api_key = "1455ec63d36773c0e47770e312063789"
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=WALCL&api_key={api_key}&file_type=json&limit=10&sort_order=desc"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            if len(observations) >= 2:
                latest_val = float(observations[0]['value'])
                prev_val = float(observations[1]['value'])
                date_latest = observations[0]['date']
                change = latest_val - prev_val
                if change < -100:
                    status = "QT"
                    color = "#f23645"
                    desc = "Quantitative Tightening"
                elif change > 100:
                    status = "QE"
                    color = "#00ffad"
                    desc = "Quantitative Easing"
                else:
                    status = "STABLE"
                    color = "#ff9800"
                    desc = "Balance sheet stable"
                return status, color, desc, f"{latest_val/1000:.1f}T", date_latest
        return "ERROR", "#888", "API temporalmente no disponible", "N/A", "N/A"
    except:
        return "N/A", "#888", "Sin conexión a FRED", "N/A", "N/A"

# ================= RENDER PRINCIPAL =================
def render():
    # CSS de tooltips (reforzado)
    st.markdown("""
    <style>
        .tooltip-container {
            position: absolute;
            top: 50%;
            right: 12px;
            transform: translateY(-50%);
            cursor: help;
        }
        .tooltip-container .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px 12px;
            border-radius: 6px;
            position: absolute;
            z-index: 999;
            top: 140%;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s, visibility 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        .fng-legend {
            display: flex;
            justify-content: space-between;
            width: 90%;
            margin-top: 12px;
            font-size: 0.75rem;
            color: #aaa;
        }
        .fng-legend-item {
            text-align: center;
            flex: 1;
        }
        .fng-color-box {
            width: 100%;
            height: 8px;
            margin-bottom: 4px;
            border-radius: 4px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    H_MAIN = "340px" 
    H_BOTTOM = "270px"

    # ================= FILA 1 =================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1] >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{get_market_index(t)[1]:+.2f}%</div></div>
            </div>''' for t, n in indices])
        tooltip = "Rendimiento en tiempo real de los principales índices bursátiles de EE.UU."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    # ... (las otras columnas de FILA 1 sin cambios: Economic Calendar y Reddit Social Pulse)

    # ================= FILA 2 =================
    st.write("")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        val = get_cnn_fear_greed()
        if val is None:
            val_display = "N/D"
            label = "ERROR DE CONEXIÓN"
            col = "#888"
            bar_width = 50
            extra = " (refresca)"
        else:
            val_display = val
            bar_width = val
            if val <= 24:
                label, col = "EXTREME FEAR", "#d32f2f"
            elif val <= 44:
                label, col = "FEAR", "#f57c00"
            elif val <= 55:
                label, col = "NEUTRAL", "#ff9800"
            elif val <= 75:
                label, col = "GREED", "#4caf50"
            else:
                label, col = "EXTREME GREED", "#00ffad"
            extra = ""

        tooltip = "Índice CNN Fear & Greed – mide el sentimiento del mercado (datos reales vía endpoint oficial)."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        
        # Leyenda añadida aquí
        legend_html = f'''
        <div class="fng-legend">
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#d32f2f;"></div>Extreme Fear</div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#f57c00;"></div>Fear</div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#ff9800;"></div>Neutral</div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#4caf50;"></div>Greed</div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#00ffad;"></div>Extreme Greed</div>
        </div>
        '''
        
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Fear & Greed Index</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px;">
            <div style="font-size:3.8rem; font-weight:bold; color:{col};">{val_display}</div>
            <div style="color:white; font-size:1rem; letter-spacing:1.5px; font-weight:bold; margin:8px 0;">{label}{extra}</div>
            <div style="width:85%; background:#0c0e12; height:12px; border-radius:6px; margin:15px 0; border:1px solid #1a1e26; position:relative; overflow:hidden;">
                <div style="width:{bar_width}%; background:{col}; height:100%; border-radius:6px; box-shadow:0 0 15px {col}80; transition:width 0.6s ease;"></div>
            </div>
            {legend_html}
            </div></div>''', unsafe_allow_html=True)

    # ... (las otras columnas de FILA 2 y FILA 3 sin cambios: sectors, crypto, earnings, insider, news)

    # ================= FILA 4 (ya incluida previamente) =================
    # ... (VIX, FED Liquidity, 10Y Treasury sin cambios)
