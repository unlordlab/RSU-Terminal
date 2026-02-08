# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from config import get_ia_model, obtener_prompt_github
from datetime import datetime
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
    """Obtiene información básica del ticker"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info
    except Exception as e:
        st.error(f"Error obteniendo datos de {ticker}: {e}")
        return None

def get_analyst_recommendations(ticker):
    """Obtiene recomendaciones de analistas reales"""
    try:
        stock = yf.Ticker(ticker)
        recommendations = stock.recommendations
        if recommendations is not None and not recommendations.empty:
            latest = recommendations.iloc[0]
            return {
                'strong_buy': int(latest.get('strongBuy', 0)),
                'buy': int(latest.get('buy', 0)),
                'hold': int(latest.get('hold', 0)),
                'sell': int(latest.get('sell', 0)),
                'strong_sell': int(latest.get('strongSell', 0)),
                'total': int(latest.get('strongBuy', 0) + latest.get('buy', 0) + 
                           latest.get('hold', 0) + latest.get('sell', 0) + 
                           latest.get('strongSell', 0))
            }
        return None
    except Exception as e:
        return None

def get_target_price(ticker):
    """Obtiene el precio objetivo de analistas"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        target_mean = info.get('targetMeanPrice')
        target_high = info.get('targetHighPrice')
        target_low = info.get('targetLowPrice')
        target_median = info.get('targetMedianPrice')
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')

        if target_mean and current_price:
            upside = ((target_mean - current_price) / current_price) * 100
        else:
            upside = None

        return {
            'mean': target_mean,
            'high': target_high,
            'low': target_low,
            'median': target_median,
            'current': current_price,
            'upside': upside
        }
    except Exception as e:
        return None

def translate_text(text, target_lang='es'):
    """Traduce texto usando una API gratuita (MyMemory)"""
    if not text or text == 'Descripción no disponible.':
        return text

    try:
        text_to_translate = text[:500] if len(text) > 500 else text
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text_to_translate)}&langpair=en|{target_lang}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get('responseStatus') == 200:
                translated = data['responseData']['translatedText']
                if len(text) > 500:
                    translated += "... [Texto truncado para traducción]"
                return translated
    except Exception:
        pass

    return text

def get_valuation_metrics(info):
    """Extrae métricas de valoración del ticker"""
    metrics = {
        'trailing_pe': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'price_to_sales': info.get('priceToSalesTrailing12Months'),
        'ev_ebitda': info.get('enterpriseToEbitda'),
        'peg_ratio': info.get('pegRatio'),
        'sector_pe': info.get('trailingPE', 0) * 0.8 if info.get('trailingPE') else None
    }
    return metrics

def get_suggestions(ticker, info, recommendations, target):
    """Genera sugerencias basadas en datos reales"""
    suggestions = []

    # 1. Análisis de valoración
    pe = info.get('trailingPE')
    forward_pe = info.get('forwardPE')
    if pe and forward_pe:
        if forward_pe < pe:
            suggestions.append("📈 El Forward P/E ({:.2f}) es inferior al P/E actual ({:.2f}), sugiriendo crecimiento de beneficios esperado.".format(forward_pe, pe))
        else:
            suggestions.append("⚠️ El Forward P/E ({:.2f}) es superior al P/E actual ({:.2f}), posible contracción de márgenes esperada.".format(forward_pe, pe))

    # 2. Análisis de recomendaciones
    if recommendations and recommendations['total'] > 0:
        buy_pct = ((recommendations['strong_buy'] + recommendations['buy']) / recommendations['total']) * 100
        if buy_pct >= 70:
            suggestions.append("✅ Fuerte consenso de compra entre analistas ({:.0f}% recomiendan comprar).".format(buy_pct))
        elif buy_pct <= 30:
            suggestions.append("🔴 Débil consenso entre analistas ({:.0f}% recomiendan comprar). Precaución.".format(buy_pct))
        else:
            suggestions.append("⚖️ Consenso neutral entre analistas ({:.0f}% recomiendan comprar).".format(buy_pct))

    # 3. Análisis de precio objetivo
    if target and target['mean'] and target['current']:
        if target['upside'] > 20:
            suggestions.append("🎯 Potencial alcista significativo: +{:.1f}% hasta el precio objetivo medio (${:.2f}).".format(target['upside'], target['mean']))
        elif target['upside'] < -10:
            suggestions.append("⚠️ El precio actual supera el objetivo medio en {:.1f}%. Posible sobrevaloración.".format(abs(target['upside'])))
        else:
            suggestions.append("📊 El precio está alineado con el consenso de analistas (diferencia del {:.1f}%).".format(target['upside']))

    # 4. Métricas de crecimiento
    revenue_growth = info.get('revenueGrowth')
    if revenue_growth:
        if revenue_growth > 0.15:
            suggestions.append("🚀 Crecimiento de ingresos sólido: +{:.1f}% (trimestral).".format(revenue_growth * 100))
        elif revenue_growth < 0:
            suggestions.append("📉 Crecimiento de ingresos negativo: {:.1f}%. Revisar tendencia.".format(revenue_growth * 100))

    # 5. Salud financiera
    debt_to_equity = info.get('debtToEquity')
    if debt_to_equity:
        if debt_to_equity > 100:
            suggestions.append("💳 Ratio deuda/capital elevado ({:.1f}%). Considerar riesgo financiero.".format(debt_to_equity))
        elif debt_to_equity < 50:
            suggestions.append("💪 Estructura de capital conservadora (deuda/capital: {:.1f}%).".format(debt_to_equity))

    # 6. Dividendos
    div_yield = info.get('dividendYield')
    if div_yield and div_yield > 0:
        suggestions.append("💰 La empresa paga dividendos con un yield del {:.2f}%.".format(div_yield * 100))

    return suggestions if suggestions else ["ℹ️ Datos insuficientes para generar sugerencias específicas."]

# ────────────────────────────────────────────────
# RENDER DEL DASHBOARD
# ────────────────────────────────────────────────

def render():
    # CSS Global compacto
    st.markdown("""
    <style>
        /* Reset y base */
        .stApp {
            background: #0c0e12;
        }

        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }

        /* Variables de color */
        :root {
            --bg-dark: #0c0e12;
            --bg-card: #11141a;
            --bg-header: #0c0e12;
            --border: #1a1e26;
            --accent: #00ffad;
            --accent-hover: #00cc8a;
            --danger: #f23645;
            --warning: #ff9800;
            --text-primary: #ffffff;
            --text-secondary: #888888;
            --text-muted: #555555;
        }

        /* Contenedores */
        .group-container {
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            background: var(--bg-card);
            margin-bottom: 16px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }

        .group-header {
            background: var(--bg-header);
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .group-title {
            margin: 0;
            color: var(--text-primary);
            font-size: 14px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .group-content {
            padding: 16px;
        }

        /* Input compacto */
        .stTextInput > div {
            margin-bottom: 0 !important;
        }

        .stTextInput > div > div > input {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-primary);
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 14px;
        }

        /* Header del ticker */
        .ticker-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 16px;
        }

        .ticker-info h1 {
            margin: 0;
            color: var(--text-primary);
            font-size: 24px;
        }

        .ticker-info p {
            margin: 4px 0 0 0;
            color: var(--text-secondary);
            font-size: 12px;
        }

        .ticker-price {
            text-align: right;
        }

        .price-main {
            font-size: 28px;
            font-weight: bold;
            color: var(--text-primary);
        }

        .price-change {
            font-size: 14px;
            font-weight: bold;
        }

        /* Tarjetas de valoración */
        .valuation-card {
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            position: relative;
            height: 100%;
        }

        .val-tag {
            position: absolute;
            top: 8px;
            right: 8px;
            background: #2a3f5f;
            color: var(--accent);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: bold;
        }

        .val-label {
            color: var(--text-secondary);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
            margin-top: 4px;
        }

        .val-value {
            color: var(--text-primary);
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 2px;
        }

        .val-sub-label {
            color: var(--text-muted);
            font-size: 9px;
        }

        /* Barra de ratings */
        .rating-bar-container {
            margin-bottom: 10px;
        }

        .rating-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 3px;
            font-size: 12px;
            color: var(--text-primary);
        }

        .rating-bar-bg {
            background: var(--bg-dark);
            height: 6px;
            border-radius: 3px;
            overflow: hidden;
        }

        .rating-bar-fill {
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }

        /* Precio objetivo */
        .target-price-box {
            background: linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }

        .target-main {
            font-size: 36px;
            font-weight: bold;
            color: var(--accent);
            margin-bottom: 6px;
        }

        .target-change {
            font-size: 14px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 16px;
            display: inline-block;
        }

        .target-positive {
            background: rgba(0, 255, 173, 0.15);
            color: var(--accent);
        }

        .target-negative {
            background: rgba(242, 54, 69, 0.15);
            color: var(--danger);
        }

        /* Tooltip */
        .tooltip-container {
            position: relative;
            cursor: help;
        }

        .tooltip-icon {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #1a1e26;
            border: 1px solid #555;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 12px;
            font-weight: bold;
        }

        .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px;
            border-radius: 6px;
            position: absolute;
            z-index: 999;
            top: 28px;
            right: -8px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 11px;
            border: 1px solid #444;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }

        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }

        /* Sección RSU */
        .rsu-section {
            background: linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%);
            border: 2px solid var(--accent);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }

        .rsu-title {
            color: var(--accent);
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Sugerencias */
        .suggestion-item {
            background: var(--bg-dark);
            border-left: 3px solid var(--accent);
            padding: 10px 14px;
            margin-bottom: 8px;
            border-radius: 0 6px 6px 0;
            font-size: 13px;
            color: var(--text-primary);
            line-height: 1.4;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: var(--bg-card);
            padding: 8px;
            border-radius: 8px;
            border: 1px solid var(--border);
            margin-bottom: 16px;
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: var(--text-secondary);
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 13px;
        }

        .stTabs [aria-selected="true"] {
            background: var(--accent) !important;
            color: #000 !important;
        }

        /* Dataframe */
        .stDataFrame {
            background: var(--bg-dark);
        }

        /* Botón */
        .stButton > button {
            background: linear-gradient(90deg, var(--accent) 0%, var(--accent-hover) 100%);
            color: #000;
            border: none;
            padding: 14px 28px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            width: 100%;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 255, 173, 0.3);
        }

        /* Eliminar espacios */
        div[data-testid="stVerticalBlock"] > div {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }

        .element-container {
            margin-bottom: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ─── INPUT DEL TICKER ───
    col_input, _ = st.columns([1, 3])
    with col_input:
        t_in = st.text_input("🔍 Introducir Ticker", "NVDA").upper()

    if not t_in:
        st.warning("⚠️ Por favor, introduce un ticker válido.")
        return

    # ─── OBTENER DATOS ───
    with st.spinner(f"Cargando datos de {t_in}..."):
        info = get_stock_info(t_in)
        if not info:
            st.error(f"No se pudieron obtener datos para {t_in}")
            return

        recommendations = get_analyst_recommendations(t_in)
        target_data = get_target_price(t_in)
        metrics = get_valuation_metrics(info)

        # Traducir descripción
        business_summary = info.get('longBusinessSummary', 'Descripción no disponible.')
        translated_summary = translate_text(business_summary)

    # ─── HEADER DEL TICKER ───
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
    prev_close = info.get('previousClose') or current_price
    price_change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
    change_color = "#00ffad" if price_change >= 0 else "#f23645"

    st.markdown(f"""
        <div class="ticker-header">
            <div class="ticker-info">
                <h1>{info.get('longName', t_in)}</h1>
                <p>{info.get('sector', 'N/A')} • {info.get('industry', 'N/A')} • Market Cap: ${info.get('marketCap', 0)/1e9:.2f}B</p>
            </div>
            <div class="ticker-price">
                <div class="price-main">${current_price:.2f}</div>
                <div class="price-change" style="color: {change_color};">
                    {'+' if price_change >= 0 else ''}{price_change:.2f}%
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ─── GRÁFICO EN CONTENEDOR ───
    chart_html = f"""
    <div class="group-container" style="margin-bottom: 16px;">
        <div class="group-header">
            <span class="group-title">📈 Gráfico Avanzado - {t_in}</span>
            <div class="tooltip-container">
                <div class="tooltip-icon">?</div>
                <div class="tooltip-text">Gráfico interactivo de TradingView con datos en tiempo real.</div>
            </div>
        </div>
        <div style="height: 550px; background: #0c0e12;">
            <div id="tradingview_chart" style="height: 100%; width: 100%;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({{
                "autosize": true,
                "symbol": "{t_in}",
                "interval": "D",
                "timezone": "Europe/Madrid",
                "theme": "dark",
                "style": "1",
                "locale": "es",
                "toolbar_bg": "#0c0e12",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": true,
                "container_id": "tradingview_chart",
                "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"],
                "hide_top_toolbar": false,
                "save_image": true
            }});
            </script>
        </div>
    </div>
    """
    components.html(chart_html, height=600)

    # ─── SECCIÓN ABOUT ───
    st.markdown(f"""
        <div class="group-container">
            <div class="group-header">
                <span class="group-title">ℹ️ Sobre {info.get('shortName', t_in)}</span>
                <div class="tooltip-container">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">Descripción de la empresa traducida automáticamente al español.</div>
                </div>
            </div>
            <div class="group-content">
                <p style="color: #cccccc; line-height: 1.5; font-size: 14px; margin: 0;">{translated_summary}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ─── PESTAÑAS DE ANÁLISIS ───
    tabs = st.tabs(["📊 Visión General", "💰 Precio Objetivo", "📋 Recomendaciones", "📑 Estados Financieros"])

    # TAB 1: OVERVIEW
    with tabs[0]:
        st.markdown('<div class="group-container" style="margin: 0;">', unsafe_allow_html=True)
        st.markdown("""
            <div class="group-header">
                <span class="group-title">💵 Múltiplos de Valoración</span>
                <div class="tooltip-container">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">Métricas clave para evaluar la valoración de la empresa.</div>
                </div>
            </div>
            <div class="group-content">
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)

        valuation_data = [
            {"label": "P/E (Trailing)", "val": metrics['trailing_pe'], "tag": "Trailing", "desc": "Precio/Beneficio"},
            {"label": "P/S (TTM)", "val": metrics['price_to_sales'], "tag": "TTM", "desc": "Precio/Ventas"},
            {"label": "EV/EBITDA", "val": metrics['ev_ebitda'], "tag": "TTM", "desc": "EV/EBITDA"},
            {"label": "Forward P/E", "val": metrics['forward_pe'], "tag": "Next 12M", "desc": "P/E Futuro"},
            {"label": "PEG Ratio", "val": metrics['peg_ratio'], "tag": "Growth", "desc": "P/E ajustado"},
        ]

        for i, m in enumerate(valuation_data):
            target_col = [c1, c2, c3][i % 3]
            with target_col:
                v = f"{m['val']:.2f}x" if isinstance(m['val'], (int, float)) else "N/A"
                st.markdown(f"""
                    <div class="valuation-card">
                        <span class="val-tag">{m['tag']}</span>
                        <div class="val-label">{m['label']}</div>
                        <div class="val-value">{v}</div>
                        <div class="val-sub-label">{m['desc']}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    # TAB 2: PRECIO OBJETIVO
    with tabs[1]:
        if target_data and target_data['mean']:
            upside = target_data['upside'] or 0
            upside_class = "target-positive" if upside >= 0 else "target-negative"
            upside_symbol = "▲" if upside >= 0 else "▼"

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown(f"""
                    <div class="target-price-box">
                        <div style="color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">
                            Precio Objetivo Medio
                        </div>
                        <div class="target-main">${target_data['mean']:.2f}</div>
                        <div class="target-change {upside_class}">
                            {upside_symbol} {abs(upside):.1f}% vs Actual
                        </div>
                        <div style="color: #555; font-size: 11px; margin-top: 10px;">
                            Basado en {info.get('numberOfAnalystOpinions', 'N/A')} analistas
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                if target_data['low'] and target_data['high']:
                    st.markdown("""
                        <div class="group-container" style="height: 100%; margin: 0;">
                            <div class="group-header">
                                <span class="group-title">Rango de Precios</span>
                            </div>
                            <div class="group-content" style="display: flex; flex-direction: column; justify-content: center; gap: 16px;">
                    """, unsafe_allow_html=True)

                    metrics_range = [
                        ("Mínimo", target_data['low'], "#f23645"),
                        ("Mediana", target_data['median'], "#ff9800"),
                        ("Máximo", target_data['high'], "#00ffad"),
                    ]

                    for label, value, color in metrics_range:
                        if value:
                            st.markdown(f"""
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="color: #888; font-size: 13px;">{label}</span>
                                    <span style="color: {color}; font-size: 18px; font-weight: bold;">${value:.2f}</span>
                                </div>
                            """, unsafe_allow_html=True)

                    st.markdown('</div></div>', unsafe_allow_html=True)
        else:
            st.info("No hay datos de precio objetivo disponibles.")

    # TAB 3: RECOMENDACIONES
    with tabs[2]:
        if recommendations and recommendations['total'] > 0:
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("""
                    <div class="group-container">
                        <div class="group-header">
                            <span class="group-title">📊 Distribución de Ratings</span>
                        </div>
                        <div class="group-content">
                """, unsafe_allow_html=True)

                ratings = [
                    ("Strong Buy", recommendations['strong_buy'], "#00ffad"),
                    ("Buy", recommendations['buy'], "#4caf50"),
                    ("Hold", recommendations['hold'], "#ff9800"),
                    ("Sell", recommendations['sell'], "#f57c00"),
                    ("Strong Sell", recommendations['strong_sell'], "#f23645"),
                ]

                for label, count, color in ratings:
                    pct = (count / recommendations['total']) * 100 if recommendations['total'] > 0 else 0
                    st.markdown(f"""
                        <div class="rating-bar-container">
                            <div class="rating-label">
                                <span>{label}</span>
                                <span style="color: {color}; font-weight: bold;">{count}</span>
                            </div>
                            <div class="rating-bar-bg">
                                <div class="rating-bar-fill" style="width: {pct}%; background: {color};"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div></div>', unsafe_allow_html=True)

            with col2:
                buy_count = recommendations['strong_buy'] + recommendations['buy']
                hold_count = recommendations['hold']
                sell_count = recommendations['sell'] + recommendations['strong_sell']

                if buy_count > sell_count and buy_count > hold_count:
                    consensus = "COMPRAR"
                    consensus_color = "#00ffad"
                    consensus_pct = (buy_count / recommendations['total']) * 100
                elif sell_count > buy_count:
                    consensus = "VENDER"
                    consensus_color = "#f23645"
                    consensus_pct = (sell_count / recommendations['total']) * 100
                else:
                    consensus = "MANTENER"
                    consensus_color = "#ff9800"
                    consensus_pct = (hold_count / recommendations['total']) * 100

                st.markdown(f"""
                    <div class="target-price-box" style="height: 100%; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">
                            Consenso de Analistas
                        </div>
                        <div style="font-size: 28px; font-weight: bold; color: {consensus_color}; margin-bottom: 6px;">
                            {consensus}
                        </div>
                        <div style="color: #888; font-size: 13px;">
                            {consensus_pct:.0f}% de acuerdo
                        </div>
                        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #333;">
                            <div style="color: #555; font-size: 11px;">Total Analistas</div>
                            <div style="color: white; font-size: 20px; font-weight: bold;">{recommendations['total']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay recomendaciones de analistas disponibles.")

    # TAB 4: FINANCIALS
    with tabs[3]:
        try:
            stock = yf.Ticker(t_in)
            financials = stock.financials
            if financials is not None and not financials.empty:
                st.markdown("""
                    <div class="group-container">
                        <div class="group-header">
                            <span class="group-title">📑 Estado de Resultados</span>
                        </div>
                        <div class="group-content">
                """, unsafe_allow_html=True)
                st.dataframe(financials, use_container_width=True)
                st.markdown('</div></div>', unsafe_allow_html=True)
            else:
                st.info("Estados financieros no disponibles.")
        except Exception as e:
            st.error(f"Error cargando estados financieros: {e}")

    # ─── SECCIÓN RSU PROMPT ───
    st.markdown("""
        <div class="rsu-section">
            <div class="rsu-title">
                🤖 RSU Artificial Intelligence
            </div>
            <p style="color: #888; margin-bottom: 16px; font-size: 13px;">
                Genera un informe completo utilizando el prompt personalizado de RSU con análisis fundamental, técnico y de sentimiento.
            </p>
    """, unsafe_allow_html=True)

    if st.button("✨ GENERAR INFORME IA (PROMPT RSU)", use_container_width=True, key="rsu_button"):
        model_ia, modelo_nombre, error_ia = get_ia_model()
        if error_ia:
            st.error(f"❌ Error: {error_ia}")
        else:
            with st.spinner(f"🧠 Analizando {t_in}..."):
                try:
                    template = obtener_prompt_github()
                    if not template:
                        template = "Analiza el ticker [TICKER] desde una perspectiva fundamental, técnica y de sentimiento de mercado."

                    prompt_final = f"""Analiza la empresa con ticker {t_in} siguiendo esta estructura profesional:

{template.replace('[TICKER]', t_in)}

Datos adicionales para el análisis:
- Precio actual: ${current_price:.2f}
- P/E Ratio: {metrics['trailing_pe'] or 'N/A'}
- Precio objetivo medio: ${target_data['mean'] if target_data and target_data['mean'] else 'N/A'}
- Sector: {info.get('sector', 'N/A')}
- Crecimiento ingresos: {(info.get('revenueGrowth', 0) * 100):.1f}%

Proporciona recomendaciones claras con niveles de entrada, stop-loss y objetivos de precio."""

                    res = model_ia.generate_content(prompt_final)

                    st.markdown(f"""
                        <div class="group-container" style="margin-top: 16px;">
                            <div class="group-header">
                                <span class="group-title">📋 Informe RSU: {t_in}</span>
                            </div>
                            <div class="group-content" style="background: #0c0e12; border-left: 3px solid #00ffad;">
                                <div style="color: #e0e0e0; line-height: 1.7; font-size: 13px; white-space: pre-wrap;">
                                    {res.text}
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    st.caption(f"🤖 Generado con: {modelo_nombre} | RSU AI Analysis")

                except Exception as e:
                    st.error(f"❌ Error en la generación del informe: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ─── LISTA DE SUGERENCIAS ENUMERADAS ───
    st.markdown("""
        <div class="group-container">
            <div class="group-header">
                <span class="group-title">💡 Sugerencias de Inversión</span>
                <div class="tooltip-container">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">Análisis automatizado basado en métricas fundamentales y técnicas actuales.</div>
                </div>
            </div>
            <div class="group-content">
    """, unsafe_allow_html=True)

    suggestions = get_suggestions(t_in, info, recommendations, target_data)

    for i, suggestion in enumerate(suggestions, 1):
        st.markdown(f"""
            <div class="suggestion-item">
                <strong>{i}.</strong> {suggestion}
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

# Ejecutar render
if __name__ == "__main__":
    render()
