# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from config import get_ia_model, obtener_prompt_github
import requests
import time

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="RSU AI Report",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ────────────────────────────────────────────────

def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info
    except Exception as e:
        st.error(f"Error obteniendo datos de {ticker}: {e}")
        return None

def get_analyst_recommendations(ticker):
    try:
        stock = yf.Ticker(ticker)
        recommendations = stock.recommendations
        if recommendations is not None and not recommendations.empty:
            latest = recommendations.iloc[0]
            sb = int(latest.get('strongBuy', 0))
            b  = int(latest.get('buy', 0))
            h  = int(latest.get('hold', 0))
            s  = int(latest.get('sell', 0))
            ss = int(latest.get('strongSell', 0))
            return {
                'strong_buy': sb, 'buy': b, 'hold': h,
                'sell': s, 'strong_sell': ss,
                'total': sb + b + h + s + ss
            }
        return None
    except Exception:
        return None

def get_target_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        target_mean   = info.get('targetMeanPrice')
        target_high   = info.get('targetHighPrice')
        target_low    = info.get('targetLowPrice')
        target_median = info.get('targetMedianPrice')
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        upside = ((target_mean - current_price) / current_price * 100) if (target_mean and current_price) else None
        return {'mean': target_mean, 'high': target_high, 'low': target_low,
                'median': target_median, 'current': current_price, 'upside': upside}
    except Exception:
        return None

def translate_text(text, target_lang='es'):
    if not text or text == 'Descripción no disponible.':
        return text
    try:
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        translated_chunks = []
        for chunk in chunks:
            url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(chunk)}&langpair=en|{target_lang}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('responseStatus') == 200:
                    translated_chunks.append(data['responseData']['translatedText'])
                else:
                    translated_chunks.append(chunk)
            else:
                translated_chunks.append(chunk)
            time.sleep(0.1)
        return ' '.join(translated_chunks)
    except Exception:
        return text

def get_valuation_metrics(info):
    return {
        'trailing_pe':    info.get('trailingPE'),
        'forward_pe':     info.get('forwardPE'),
        'price_to_sales': info.get('priceToSalesTrailing12Months'),
        'ev_ebitda':      info.get('enterpriseToEbitda'),
        'peg_ratio':      info.get('pegRatio'),
        # sector averages (when available via yfinance)
        'sector_pe':      info.get('sectorTrailingPE'),
    }

def format_financial_value(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "N/A"
    if isinstance(val, (int, float)):
        if abs(val) >= 1e12: return f"${val/1e12:.2f}T"
        elif abs(val) >= 1e9:  return f"${val/1e9:.2f}B"
        elif abs(val) >= 1e6:  return f"${val/1e6:.2f}M"
        elif abs(val) >= 1e3:  return f"${val/1e3:.2f}K"
        else:                  return f"${val:.2f}"
    return str(val)

def get_suggestions(ticker, info, recommendations, target):
    suggestions = []
    pe = info.get('trailingPE')
    forward_pe = info.get('forwardPE')
    if pe and forward_pe:
        if forward_pe < pe:
            suggestions.append(f"📈 Forward P/E ({forward_pe:.2f}x) inferior al P/E actual ({pe:.2f}x) — crecimiento de beneficios esperado.")
        else:
            suggestions.append(f"⚠️ Forward P/E ({forward_pe:.2f}x) superior al P/E actual ({pe:.2f}x) — posible contracción de márgenes.")

    if recommendations and recommendations['total'] > 0:
        buy_pct = ((recommendations['strong_buy'] + recommendations['buy']) / recommendations['total']) * 100
        if buy_pct >= 70:
            suggestions.append(f"✅ Fuerte consenso alcista entre analistas ({buy_pct:.0f}% recomiendan comprar).")
        elif buy_pct <= 30:
            suggestions.append(f"🔴 Débil consenso entre analistas ({buy_pct:.0f}% recomiendan comprar). Precaución.")
        else:
            suggestions.append(f"⚖️ Consenso neutral entre analistas ({buy_pct:.0f}% recomiendan comprar).")

    if target and target.get('mean') and target.get('current'):
        upside = target['upside']
        if upside and upside > 20:
            suggestions.append(f"🎯 Potencial alcista significativo: +{upside:.1f}% hasta precio objetivo (${target['mean']:.2f}).")
        elif upside and upside < -10:
            suggestions.append(f"⚠️ Precio actual supera el objetivo medio en {abs(upside):.1f}%. Posible sobrevaloración.")
        elif upside is not None:
            suggestions.append(f"📊 Precio alineado con consenso de analistas (diferencia: {upside:.1f}%).")

    revenue_growth = info.get('revenueGrowth')
    if revenue_growth:
        if revenue_growth > 0.15:
            suggestions.append(f"🚀 Crecimiento de ingresos sólido: +{revenue_growth*100:.1f}% (trimestral).")
        elif revenue_growth < 0:
            suggestions.append(f"📉 Crecimiento de ingresos negativo: {revenue_growth*100:.1f}%. Revisar tendencia.")

    debt_to_equity = info.get('debtToEquity')
    if debt_to_equity:
        if debt_to_equity > 100:
            suggestions.append(f"💳 Ratio deuda/capital elevado ({debt_to_equity:.1f}). Considerar riesgo financiero.")
        elif debt_to_equity < 50:
            suggestions.append(f"💪 Estructura de capital conservadora (deuda/capital: {debt_to_equity:.1f}).")

    div_yield = info.get('dividendYield')
    if div_yield and div_yield > 0:
        suggestions.append(f"💰 La empresa paga dividendos con yield del {div_yield*100:.2f}%.")

    return suggestions if suggestions else ["ℹ️ Datos insuficientes para generar sugerencias específicas."]


# ────────────────────────────────────────────────
# CSS GLOBAL (estética roadmap_2026 + VT323)
# ────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp { background: #0c0e12; }

        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }

        /* ── TIPOGRAFÍA VT323 ── */
        .vt-title {
            font-family: 'VT323', monospace;
            color: #00ffad;
            text-transform: uppercase;
            letter-spacing: 3px;
            text-shadow: 0 0 18px #00ffad55;
        }
        .vt-subtitle {
            font-family: 'VT323', monospace;
            color: #00d9ff;
            letter-spacing: 2px;
        }
        .vt-label {
            font-family: 'VT323', monospace;
            color: #888;
            font-size: 1rem;
            letter-spacing: 1px;
        }

        /* ── LANDING ── */
        .landing-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 70vh;
            text-align: center;
        }
        .landing-title {
            font-family: 'VT323', monospace;
            font-size: 5rem;
            color: #00ffad;
            text-shadow: 0 0 30px #00ffad66;
            border-bottom: 2px solid #00ffad44;
            padding-bottom: 10px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 4px;
        }
        .landing-desc {
            font-family: 'VT323', monospace;
            font-size: 1.3rem;
            color: #00d9ff;
            letter-spacing: 3px;
            margin-bottom: 40px;
        }

        /* ── INPUT ── */
        .stTextInput > div > div > input {
            background: #0c0e12 !important;
            border: 1px solid #00ffad44 !important;
            border-radius: 6px !important;
            color: #00ffad !important;
            font-family: 'VT323', monospace !important;
            font-size: 1.6rem !important;
            text-align: center;
            letter-spacing: 4px;
            padding: 12px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #00ffad !important;
            box-shadow: 0 0 10px #00ffad33 !important;
        }
        .stTextInput label {
            font-family: 'VT323', monospace !important;
            color: #888 !important;
            font-size: 1rem !important;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        /* ── BOTÓN ── */
        .stButton > button {
            background: linear-gradient(90deg, #00ffad, #00cc8a) !important;
            color: #000 !important;
            border: none !important;
            border-radius: 6px !important;
            font-family: 'VT323', monospace !important;
            font-size: 1.4rem !important;
            letter-spacing: 3px !important;
            padding: 14px 40px !important;
            width: 100% !important;
            text-transform: uppercase !important;
        }
        .stButton > button:hover {
            box-shadow: 0 0 20px #00ffad55 !important;
        }

        /* ── MÓDULOS ── */
        .mod-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #00ffad22;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
            box-shadow: 0 0 15px #00ffad08;
        }
        .mod-header {
            background: #0c0e12;
            padding: 12px 18px;
            border-bottom: 1px solid #00ffad22;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .mod-title {
            font-family: 'VT323', monospace;
            color: #00ffad;
            font-size: 1.3rem;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin: 0;
        }
        .mod-body { padding: 18px; }

        /* ── TICKER HEADER ── */
        .ticker-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #00ffad33;
            border-radius: 8px;
            padding: 18px 24px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 0 20px #00ffad11;
        }
        .ticker-name {
            font-family: 'VT323', monospace;
            font-size: 2.4rem;
            color: #00ffad;
            letter-spacing: 3px;
            text-shadow: 0 0 10px #00ffad44;
        }
        .ticker-meta {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        .ticker-price {
            font-family: 'VT323', monospace;
            font-size: 2.8rem;
            color: #fff;
            text-align: right;
        }
        .ticker-change {
            font-family: 'VT323', monospace;
            font-size: 1.3rem;
            text-align: right;
        }

        /* ── MÉTRICAS DE VALORACIÓN ── */
        .metric-box {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 16px;
            position: relative;
            margin-bottom: 10px;
            height: 100%;
        }
        .metric-tag {
            position: absolute;
            top: 10px; right: 10px;
            background: #1a2d4a;
            color: #00d9ff;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'VT323', monospace;
            font-size: 0.85rem;
            letter-spacing: 1px;
        }
        .metric-label {
            font-family: 'VT323', monospace;
            color: #888;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 6px;
            margin-top: 4px;
        }
        .metric-value {
            font-family: 'VT323', monospace;
            color: #fff;
            font-size: 2rem;
            letter-spacing: 1px;
        }
        .metric-sector {
            font-family: 'Courier New', monospace;
            color: #444;
            font-size: 10px;
            margin-top: 3px;
        }
        .metric-desc {
            font-family: 'Courier New', monospace;
            color: #555;
            font-size: 10px;
            margin-top: 2px;
        }

        /* ── RATINGS ── */
        .rating-item { margin-bottom: 14px; }
        .rating-top {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        .rating-name {
            font-family: 'VT323', monospace;
            color: #ccc;
            font-size: 1.1rem;
            letter-spacing: 1px;
        }
        .rating-count {
            font-family: 'VT323', monospace;
            font-size: 1.1rem;
            font-weight: bold;
        }
        .rating-bar {
            background: #0c0e12;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
        }
        .rating-fill { height: 100%; border-radius: 4px; }

        /* ── PRECIO OBJETIVO ── */
        .target-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 24px;
            text-align: center;
        }
        .target-label {
            font-family: 'VT323', monospace;
            color: #888;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 8px;
        }
        .target-price {
            font-family: 'VT323', monospace;
            font-size: 3.5rem;
            color: #00ffad;
            text-shadow: 0 0 15px #00ffad44;
        }
        .target-badge-up {
            display: inline-block;
            padding: 4px 14px;
            border-radius: 20px;
            font-family: 'VT323', monospace;
            font-size: 1.1rem;
            background: rgba(0,255,173,0.12);
            color: #00ffad;
            border: 1px solid #00ffad33;
        }
        .target-badge-down {
            display: inline-block;
            padding: 4px 14px;
            border-radius: 20px;
            font-family: 'VT323', monospace;
            font-size: 1.1rem;
            background: rgba(242,54,69,0.12);
            color: #f23645;
            border: 1px solid #f2364533;
        }

        /* ── CONSENSO ── */
        .consensus-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 24px;
            text-align: center;
            height: 100%;
        }

        /* ── RSU BOX ── */
        .rsu-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 2px solid #00ffad44;
            border-radius: 8px;
            padding: 24px;
            margin: 20px 0;
            box-shadow: 0 0 20px #00ffad11;
        }
        .rsu-title {
            font-family: 'VT323', monospace;
            color: #00ffad;
            font-size: 1.6rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        /* ── SUGERENCIAS ── */
        .suggestion-item {
            background: #0c0e12;
            border-left: 3px solid #00ffad;
            padding: 12px 16px;
            margin-bottom: 10px;
            border-radius: 0 6px 6px 0;
            font-family: 'Courier New', monospace;
            color: #ccc;
            font-size: 13px;
            line-height: 1.5;
        }

        /* ── ABOUT ── */
        .about-text {
            font-family: 'Courier New', monospace;
            color: #ccc;
            line-height: 1.8;
            font-size: 0.9rem;
        }

        /* ── TABS ── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: #0c0e12;
            padding: 8px;
            border-radius: 8px;
            border: 1px solid #00ffad22;
            margin-bottom: 16px;
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: #666;
            border-radius: 6px;
            padding: 8px 18px;
            font-family: 'VT323', monospace;
            font-size: 1rem;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .stTabs [aria-selected="true"] {
            background: #00ffad !important;
            color: #000 !important;
        }

        /* ── TOOLTIP ── */
        .tip-box { position: relative; cursor: help; }
        .tip-icon {
            width: 20px; height: 20px;
            border-radius: 50%;
            background: #1a1e26;
            border: 1px solid #444;
            display: flex; align-items: center; justify-content: center;
            color: #888; font-size: 12px; font-weight: bold;
        }
        .tip-text {
            visibility: hidden;
            width: 240px;
            background: #1e222d;
            color: #ccc;
            text-align: left;
            padding: 10px;
            border-radius: 6px;
            position: absolute;
            z-index: 1000;
            top: 26px; right: 0;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 11px;
            border: 1px solid #333;
            font-family: 'Courier New', monospace;
        }
        .tip-box:hover .tip-text { visibility: visible; opacity: 1; }

        /* ── HR ── */
        hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00ffad44, transparent); margin: 24px 0; }

        /* ── HIGHLIGHT QUOTE ── */
        .hq {
            background: #00ffad11;
            border: 1px solid #00ffad33;
            border-radius: 8px;
            padding: 16px 20px;
            font-family: 'VT323', monospace;
            font-size: 1.2rem;
            color: #00ffad;
            text-align: center;
            letter-spacing: 1px;
        }

        /* eliminar márgenes extra de streamlit */
        div[data-testid="stVerticalBlock"] > div { margin-bottom: 0 !important; }
        .element-container { margin-bottom: 0 !important; }
        .stTextInput > div { margin-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    inject_css()

    # ── BANNER SUPERIOR ──
    st.markdown("""
    <div style="text-align:center; margin-bottom: 8px;">
        <div class="vt-label">[SECURE CONNECTION ESTABLISHED // RSU ANALYTICS v2.0]</div>
    </div>
    """, unsafe_allow_html=True)

    # ── INPUT DEL TICKER (siempre visible) ──
    col_l, col_c, col_r = st.columns([1.5, 2, 1.5])
    with col_c:
        st.markdown("""
        <div style="text-align:center; margin-bottom: 6px;">
            <div class="landing-title">📊 RSU AI REPORT</div>
            <div class="landing-desc">ANÁLISIS FUNDAMENTAL · TÉCNICO · ANALISTAS</div>
        </div>
        """, unsafe_allow_html=True)
        t_in = st.text_input("Introduce el ticker", placeholder="NVDA, AAPL, META…", label_visibility="collapsed").upper().strip()

    if not t_in:
        # pantalla de bienvenida
        st.markdown("""
        <div style="text-align:center; margin-top: 20px;">
            <div class="hq">▸ Introduce un ticker para iniciar el análisis ◂</div>
            <div style="margin-top: 30px; font-family: 'Courier New', monospace; color: #444; font-size: 12px;">
                Powered by Yahoo Finance · TradingView · Gemini AI
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── OBTENER DATOS ──
    with st.spinner(f"[ CARGANDO {t_in} ... ]"):
        info = get_stock_info(t_in)
        if not info or not info.get('regularMarketPrice') and not info.get('currentPrice'):
            st.error(f"❌ No se encontraron datos para el ticker '{t_in}'. Verifica que sea válido.")
            return

        recommendations = get_analyst_recommendations(t_in)
        target_data     = get_target_price(t_in)
        metrics         = get_valuation_metrics(info)
        business_summary = info.get('longBusinessSummary', '')
        translated_summary = translate_text(business_summary) if business_summary else 'Descripción no disponible.'

    # ── HEADER DEL TICKER ──
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
    prev_close    = info.get('previousClose') or current_price
    price_change  = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
    change_color  = "#00ffad" if price_change >= 0 else "#f23645"
    change_arrow  = "▲" if price_change >= 0 else "▼"
    market_cap    = info.get('marketCap', 0)

    st.markdown(f"""
    <div class="ticker-box">
        <div>
            <div class="ticker-name">{info.get('shortName', t_in)}</div>
            <div class="ticker-meta">
                {info.get('sector', 'N/A')} &nbsp;·&nbsp; {info.get('industry', 'N/A')} &nbsp;·&nbsp;
                Market Cap: {format_financial_value(market_cap)}
            </div>
        </div>
        <div>
            <div class="ticker-price">${current_price:,.2f}</div>
            <div class="ticker-change" style="color:{change_color};">
                {change_arrow} {abs(price_change):.2f}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── GRÁFICO TRADINGVIEW ──
    chart_html = f"""<!DOCTYPE html><html><head>
    <style>body{{margin:0;padding:0;background:#0c0e12;}}</style></head><body>
    <div id="tv_chart" style="width:100%;height:480px;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{
        "autosize":true,"symbol":"{t_in}","interval":"D",
        "timezone":"Europe/Madrid","theme":"dark","style":"1","locale":"es",
        "toolbar_bg":"#0c0e12","enable_publishing":false,"hide_side_toolbar":false,
        "allow_symbol_change":true,"container_id":"tv_chart",
        "studies":["RSI@tv-basicstudies","MASimple@tv-basicstudies"]
    }});
    </script></body></html>"""

    st.markdown(f"""
    <div class="mod-box">
        <div class="mod-header">
            <span class="mod-title">📈 Gráfico Avanzado — {t_in}</span>
            <div class="tip-box">
                <div class="tip-icon">?</div>
                <div class="tip-text">Gráfico interactivo TradingView con datos en tiempo real.</div>
            </div>
        </div>
        <div style="height:480px; background:#0c0e12;">
    """, unsafe_allow_html=True)
    components.html(chart_html, height=480)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── SOBRE LA EMPRESA ──
    st.markdown(f"""
    <div class="mod-box">
        <div class="mod-header">
            <span class="mod-title">ℹ️ Sobre {info.get('shortName', t_in)}</span>
            <div class="tip-box">
                <div class="tip-icon">?</div>
                <div class="tip-text">Descripción oficial de la empresa (traducida al español).</div>
            </div>
        </div>
        <div class="mod-body">
            <p class="about-text">{translated_summary}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── PESTAÑAS PRINCIPALES ──
    tabs = st.tabs(["📊 Visión General", "💰 Precio Objetivo", "📋 Recomendaciones", "📑 Financieros"])

    # ────── TAB 1: VISIÓN GENERAL ──────
    with tabs[0]:
        st.markdown("""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">💵 Múltiplos de Valoración</span>
                <div class="tip-box">
                    <div class="tip-icon">?</div>
                    <div class="tip-text">Métricas clave para evaluar si la empresa cotiza cara o barata respecto a sus fundamentales.</div>
                </div>
            </div>
            <div class="mod-body">
        """, unsafe_allow_html=True)

        valuation_data = [
            ("P/E", metrics['trailing_pe'], "Trailing", "Precio / Beneficio"),
            ("P/S", metrics['price_to_sales'], "TTM", "Precio / Ventas"),
            ("EV/EBITDA", metrics['ev_ebitda'], "TTM", "Valor Empresa / EBITDA"),
            ("Forward P/E", metrics['forward_pe'], "Próx. 12M", "Precio / BPA Futuro"),
            ("PEG Ratio", metrics['peg_ratio'], "P/E ÷ Crecimiento", "Valoración ajustada al crecimiento"),
        ]

        c1, c2, c3 = st.columns(3)
        for i, (label, val, tag, desc) in enumerate(valuation_data):
            col = [c1, c2, c3][i % 3]
            with col:
                v = f"{val:.2f}×" if isinstance(val, (int, float)) and val == val else "N/A"
                st.markdown(f"""
                <div class="metric-box">
                    <span class="metric-tag">{tag}</span>
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{v}</div>
                    <div class="metric-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

    # ────── TAB 2: PRECIO OBJETIVO ──────
    with tabs[1]:
        if target_data and target_data.get('mean'):
            upside = target_data.get('upside') or 0
            badge_class = "target-badge-up" if upside >= 0 else "target-badge-down"
            upside_arrow = "▲" if upside >= 0 else "▼"
            n_analysts = info.get('numberOfAnalystOpinions', 'N/D')

            st.markdown('<div class="mod-box"><div class="mod-body">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                <div class="target-box">
                    <div class="target-label">Precio Objetivo Medio de Analistas</div>
                    <div class="target-price">${target_data['mean']:,.2f}</div>
                    <div class="{badge_class}" style="margin: 8px auto; display: inline-block;">
                        {upside_arrow} +{abs(upside):.1f}% vs actual (${target_data['current']:,.2f})
                    </div>
                    <div style="font-family:'Courier New',monospace; color:#444; font-size:11px; margin-top:12px;">
                        Basado en {n_analysts} analistas
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if target_data.get('low') and target_data.get('high'):
                    ranges = [
                        ("Objetivo Mínimo", target_data['low'], "#f23645"),
                        ("Objetivo Mediana", target_data.get('median'), "#ff9800"),
                        ("Objetivo Máximo", target_data['high'], "#00ffad"),
                    ]
                    rows_html = ""
                    for rlabel, rval, rcolor in ranges:
                        if rval:
                            rows_html += f"""
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
                                <span style="font-family:'Courier New',monospace; color:#888; font-size:13px;">{rlabel}</span>
                                <span style="font-family:'VT323',monospace; color:{rcolor}; font-size:1.8rem;">${rval:,.2f}</span>
                            </div>"""
                    st.markdown(f"""
                    <div class="target-box" style="text-align:left;">
                        <div style="font-family:'VT323',monospace; color:#fff; font-size:1.1rem; letter-spacing:2px; text-align:center; margin-bottom:20px; text-transform:uppercase;">
                            Rango de Precios Objetivo
                        </div>
                        {rows_html}
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.info("No hay datos de precio objetivo disponibles para este ticker.")

    # ────── TAB 3: RECOMENDACIONES DE ANALISTAS ──────
    with tabs[2]:
        if recommendations and recommendations['total'] > 0:
            st.markdown('<div class="mod-box"><div class="mod-body">', unsafe_allow_html=True)
            col1, col2 = st.columns([3, 2])

            with col1:
                # Header módulo distribución
                st.markdown(f"""
                <div style="font-family:'VT323',monospace; color:#00ffad; font-size:1.1rem; letter-spacing:2px; text-transform:uppercase; margin-bottom:16px;">
                    Distribución de Ratings &nbsp;
                    <span style="color:#888; font-size:0.85rem;">({recommendations['total']} analistas)</span>
                </div>
                """, unsafe_allow_html=True)

                ratings_es = [
                    ("Compra Fuerte",  recommendations['strong_buy'],   "#00ffad"),
                    ("Comprar",        recommendations['buy'],           "#4caf50"),
                    ("Mantener",       recommendations['hold'],          "#ff9800"),
                    ("Vender",         recommendations['sell'],          "#f57c00"),
                    ("Venta Fuerte",   recommendations['strong_sell'],   "#f23645"),
                ]
                for rlabel, count, color in ratings_es:
                    pct = (count / recommendations['total'] * 100) if recommendations['total'] > 0 else 0
                    st.markdown(f"""
                    <div class="rating-item">
                        <div class="rating-top">
                            <span class="rating-name">{rlabel}</span>
                            <span class="rating-count" style="color:{color};">{count}</span>
                        </div>
                        <div class="rating-bar">
                            <div class="rating-fill" style="width:{pct}%; background:{color};"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with col2:
                buy_count  = recommendations['strong_buy'] + recommendations['buy']
                hold_count = recommendations['hold']
                sell_count = recommendations['sell'] + recommendations['strong_sell']

                if buy_count > sell_count and buy_count > hold_count:
                    consensus, c_color = "ALCISTA", "#00ffad"
                    consensus_pct = (buy_count / recommendations['total']) * 100
                elif sell_count > buy_count:
                    consensus, c_color = "BAJISTA", "#f23645"
                    consensus_pct = (sell_count / recommendations['total']) * 100
                else:
                    consensus, c_color = "NEUTRAL", "#ff9800"
                    consensus_pct = (hold_count / recommendations['total']) * 100

                positive_pct = (buy_count / recommendations['total']) * 100

                st.markdown(f"""
                <div class="consensus-box">
                    <div style="font-family:'VT323',monospace; color:#888; font-size:0.9rem; text-transform:uppercase; letter-spacing:2px; margin-bottom:12px;">
                        Consenso de Analistas
                    </div>
                    <div style="font-family:'VT323',monospace; font-size:2.5rem; color:{c_color}; text-shadow:0 0 12px {c_color}44; margin-bottom:6px;">
                        {consensus}
                    </div>
                    <div style="font-family:'Courier New',monospace; color:#888; font-size:13px; margin-bottom:20px;">
                        {consensus_pct:.0f}% de acuerdo
                    </div>
                    <div style="border-top:1px solid #1a1e26; padding-top:16px;">
                        <div style="font-family:'VT323',monospace; color:#555; font-size:0.85rem; letter-spacing:1px;">POSITIVOS</div>
                        <div style="font-family:'VT323',monospace; color:#00ffad; font-size:2rem;">{positive_pct:.0f}%</div>
                    </div>
                    <div style="border-top:1px solid #1a1e26; padding-top:16px; margin-top:10px;">
                        <div style="font-family:'VT323',monospace; color:#555; font-size:0.85rem; letter-spacing:1px;">TOTAL ANALISTAS</div>
                        <div style="font-family:'VT323',monospace; color:#fff; font-size:2rem;">{recommendations['total']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.info("No hay recomendaciones de analistas disponibles para este ticker.")

    # ────── TAB 4: ESTADOS FINANCIEROS ──────
    with tabs[3]:
        try:
            stock = yf.Ticker(t_in)
            financials = stock.financials
            if financials is not None and not financials.empty:
                index_mapping = {
                    'Total Revenue': 'Ingresos Totales',
                    'Net Income': 'Beneficio Neto',
                    'Operating Income': 'Beneficio Operativo',
                    'EBITDA': 'EBITDA',
                    'Gross Profit': 'Beneficio Bruto',
                    'Research Development': 'I+D',
                    'Selling General Administrative': 'Gastos SG&A',
                    'Total Operating Expenses': 'Gastos Operativos',
                    'Income Before Tax': 'Beneficio antes de Impuestos',
                    'Income Tax Expense': 'Impuesto sobre Beneficios',
                    'Interest Expense': 'Gastos por Intereses',
                }
                financials.index = [index_mapping.get(str(i), str(i)) for i in financials.index]

                st.markdown("""
                <div class="mod-box">
                    <div class="mod-header">
                        <span class="mod-title">📑 Estado de Resultados</span>
                    </div>
                    <div class="mod-body">
                """, unsafe_allow_html=True)
                st.dataframe(financials, use_container_width=True)
                st.markdown("</div></div>", unsafe_allow_html=True)
            else:
                st.info("Estados financieros no disponibles.")
        except Exception as e:
            st.error(f"Error cargando estados financieros: {e}")

    # ── SEPARADOR ──
    st.markdown("<hr>", unsafe_allow_html=True)

    # ── RSU AI PROMPT ──
    st.markdown("""
    <div class="rsu-box">
        <div class="rsu-title">🤖 RSU Artificial Intelligence</div>
        <p style="font-family:'Courier New',monospace; color:#888; font-size:13px; line-height:1.6; margin-bottom:16px;">
            Genera un informe completo con el prompt personalizado RSU: análisis fundamental, técnico y de sentimiento de mercado.
        </p>
    """, unsafe_allow_html=True)

    if st.button("✨ GENERAR INFORME IA (PROMPT RSU)", key="rsu_button"):
        model_ia, modelo_nombre, error_ia = get_ia_model()
        if error_ia:
            st.error(f"❌ Error: {error_ia}")
        else:
            with st.spinner(f"[ ANALIZANDO {t_in} ... ]"):
                try:
                    template = obtener_prompt_github()
                    if not template:
                        template = "Analiza el ticker [TICKER] desde una perspectiva fundamental, técnica y de sentimiento de mercado."

                    prompt_final = f"""Analiza la empresa con ticker {t_in} siguiendo esta estructura profesional:

{template.replace('[TICKER]', t_in)}

Datos adicionales para el análisis:
- Precio actual: ${current_price:.2f}
- P/E Ratio: {metrics['trailing_pe'] or 'N/A'}
- Precio objetivo medio: ${target_data['mean'] if target_data and target_data.get('mean') else 'N/A'}
- Sector: {info.get('sector', 'N/A')}
- Crecimiento ingresos: {(info.get('revenueGrowth', 0) or 0) * 100:.1f}%

Proporciona recomendaciones claras con niveles de entrada, stop-loss y objetivos de precio."""

                    res = model_ia.generate_content(prompt_final)

                    st.markdown(f"""
                    <div class="mod-box" style="margin-top:16px;">
                        <div class="mod-header">
                            <span class="mod-title">📋 Informe RSU: {t_in}</span>
                        </div>
                        <div class="mod-body" style="background:#0c0e12; border-left:3px solid #00ffad;">
                            <div style="font-family:'Courier New',monospace; color:#e0e0e0; line-height:1.8; font-size:13px; white-space:pre-wrap;">{res.text}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption(f"🤖 Generado con: {modelo_nombre} | RSU AI Analysis")

                except Exception as e:
                    st.error(f"❌ Error en la generación del informe: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── SUGERENCIAS ──
    suggestions = get_suggestions(t_in, info, recommendations, target_data)

    st.markdown("""
    <div class="mod-box">
        <div class="mod-header">
            <span class="mod-title">💡 Sugerencias de Inversión</span>
            <div class="tip-box">
                <div class="tip-icon">?</div>
                <div class="tip-text">Análisis automatizado basado en métricas fundamentales y técnicas actuales. No es asesoramiento financiero.</div>
            </div>
        </div>
        <div class="mod-body">
    """, unsafe_allow_html=True)

    for i, suggestion in enumerate(suggestions, 1):
        st.markdown(f"""
        <div class="suggestion-item"><strong style="color:#00ffad;">{i}.</strong> {suggestion}</div>
        """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── FOOTER ──
    st.markdown("""
    <div style="text-align:center; margin-top:40px; padding:20px; border-top:1px solid #1a1e26;">
        <div style="font-family:'VT323',monospace; color:#333; font-size:0.85rem; letter-spacing:2px;">
            [END OF REPORT // RSU_AI_REPORT_v2.0]<br>
            [DATA SOURCE: YAHOO FINANCE · TRADINGVIEW · GEMINI AI]<br>
            [STATUS: ACTIVE]
        </div>
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────
if __name__ == "__main__":
    render()




