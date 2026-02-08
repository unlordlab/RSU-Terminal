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
        if len(text) > 500:
            chunks = [text[i:i+500] for i in range(0, len(text), 500)]
            translated_chunks = []

            for chunk in chunks:
                url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(chunk)}&langpair=en|{target_lang}"
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('responseStatus') == 200:
                        translated_chunks.append(data['responseData']['translatedText'])
                    else:
                        translated_chunks.append(chunk)
                else:
                    translated_chunks.append(chunk)

                time.sleep(0.1)

            return ' '.join(translated_chunks)
        else:
            url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=en|{target_lang}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('responseStatus') == 200:
                    return data['responseData']['translatedText']
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
    }
    return metrics

def format_financial_value(val):
    """Formatea valores financieros para mejor legibilidad"""
    if pd.isna(val):
        return "N/A"

    if isinstance(val, (int, float)):
        if abs(val) >= 1e12:
            return f"${val/1e12:.2f}T"
        elif abs(val) >= 1e9:
            return f"${val/1e9:.2f}B"
        elif abs(val) >= 1e6:
            return f"${val/1e6:.2f}M"
        elif abs(val) >= 1e3:
            return f"${val/1e3:.2f}K"
        else:
            return f"${val:.2f}"

    return str(val)

def get_suggestions(ticker, info, recommendations, target):
    """Genera sugerencias basadas en datos reales"""
    suggestions = []

    pe = info.get('trailingPE')
    forward_pe = info.get('forwardPE')
    if pe and forward_pe:
        if forward_pe < pe:
            suggestions.append("📈 El Forward P/E ({:.2f}) es inferior al P/E actual ({:.2f}), sugiriendo crecimiento de beneficios esperado.".format(forward_pe, pe))
        else:
            suggestions.append("⚠️ El Forward P/E ({:.2f}) es superior al P/E actual ({:.2f}), posible contracción de márgenes esperada.".format(forward_pe, pe))

    if recommendations and recommendations['total'] > 0:
        buy_pct = ((recommendations['strong_buy'] + recommendations['buy']) / recommendations['total']) * 100
        if buy_pct >= 70:
            suggestions.append("✅ Fuerte consenso de compra entre analistas ({:.0f}% recomiendan comprar).".format(buy_pct))
        elif buy_pct <= 30:
            suggestions.append("🔴 Débil consenso entre analistas ({:.0f}% recomiendan comprar). Precaución.".format(buy_pct))
        else:
            suggestions.append("⚖️ Consenso neutral entre analistas ({:.0f}% recomiendan comprar).".format(buy_pct))

    if target and target['mean'] and target['current']:
        if target['upside'] > 20:
            suggestions.append("🎯 Potencial alcista significativo: +{:.1f}% hasta el precio objetivo medio (${:.2f}).".format(target['upside'], target['mean']))
        elif target['upside'] < -10:
            suggestions.append("⚠️ El precio actual supera el objetivo medio en {:.1f}%. Posible sobrevaloración.".format(abs(target['upside'])))
        else:
            suggestions.append("📊 El precio está alineado con el consenso de analistas (diferencia del {:.1f}%).".format(target['upside']))

    revenue_growth = info.get('revenueGrowth')
    if revenue_growth:
        if revenue_growth > 0.15:
            suggestions.append("🚀 Crecimiento de ingresos sólido: +{:.1f}% (trimestral).".format(revenue_growth * 100))
        elif revenue_growth < 0:
            suggestions.append("📉 Crecimiento de ingresos negativo: {:.1f}%. Revisar tendencia.".format(revenue_growth * 100))

    debt_to_equity = info.get('debtToEquity')
    if debt_to_equity:
        if debt_to_equity > 100:
            suggestions.append("💳 Ratio deuda/capital elevado ({:.1f}%). Considerar riesgo financiero.".format(debt_to_equity))
        elif debt_to_equity < 50:
            suggestions.append("💪 Estructura de capital conservadora (deuda/capital: {:.1f}%).".format(debt_to_equity))

    div_yield = info.get('dividendYield')
    if div_yield and div_yield > 0:
        suggestions.append("💰 La empresa paga dividendos con un yield del {:.2f}%.".format(div_yield * 100))

    return suggestions if suggestions else ["ℹ️ Datos insuficientes para generar sugerencias específicas."]

# ────────────────────────────────────────────────
# RENDER DEL DASHBOARD
# ────────────────────────────────────────────────

def render():
    # CSS Global - Estructura compacta sin espacios
    st.markdown("""
    <style>
        .stApp {
            background: #0c0e12;
        }

        .main .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
            max-width: 100%;
        }

        /* CONTENEDOR PRINCIPAL - Sin espacios */
        .box-container {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 16px;
        }

        .box-header {
            background: #0c0e12;
            padding: 14px 18px;
            border-bottom: 1px solid #1a1e26;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .box-title {
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            margin: 0;
        }

        .box-content {
            padding: 18px;
            background: #11141a;
        }

        /* Header del ticker */
        .ticker-box {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            padding: 18px 22px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .ticker-name {
            font-size: 26px;
            font-weight: bold;
            color: #ffffff;
            margin: 0;
        }

        .ticker-meta {
            font-size: 13px;
            color: #888888;
            margin-top: 4px;
        }

        .ticker-price-box {
            text-align: right;
        }

        .ticker-price {
            font-size: 30px;
            font-weight: bold;
            color: #ffffff;
        }

        .ticker-change {
            font-size: 15px;
            font-weight: bold;
        }

        /* Métricas */
        .metric-box {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            padding: 16px;
            position: relative;
            height: 100%;
        }

        .metric-tag {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #2a3f5f;
            color: #00ffad;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        }

        .metric-label {
            color: #888888;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            margin-top: 6px;
        }

        .metric-value {
            color: #ffffff;
            font-size: 22px;
            font-weight: bold;
        }

        .metric-desc {
            color: #555555;
            font-size: 10px;
            margin-top: 4px;
        }

        /* Ratings */
        .rating-item {
            margin-bottom: 12px;
        }

        .rating-top {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
            font-size: 13px;
        }

        .rating-name {
            color: #ffffff;
        }

        .rating-count {
            font-weight: bold;
        }

        .rating-bar {
            background: #0c0e12;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
        }

        .rating-fill {
            height: 100%;
            border-radius: 4px;
        }

        /* Precio objetivo */
        .target-box {
            background: linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%);
            border: 1px solid #1a1e26;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
        }

        .target-label {
            color: #888888;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .target-price {
            font-size: 40px;
            font-weight: bold;
            color: #00ffad;
            margin-bottom: 8px;
        }

        .target-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }

        .target-up {
            background: rgba(0, 255, 173, 0.15);
            color: #00ffad;
        }

        .target-down {
            background: rgba(242, 54, 69, 0.15);
            color: #f23645;
        }

        /* Tooltip */
        .tip-wrap {
            position: relative;
            cursor: help;
        }

        .tip-icon {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #1a1e26;
            border: 1px solid #555;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 13px;
            font-weight: bold;
        }

        .tip-text {
            visibility: hidden;
            width: 260px;
            background: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px;
            border-radius: 6px;
            position: absolute;
            z-index: 1000;
            top: 28px;
            right: 0;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 11px;
            border: 1px solid #444;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }

        .tip-wrap:hover .tip-text {
            visibility: visible;
            opacity: 1;
        }

        /* RSU */
        .rsu-box {
            background: linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%);
            border: 2px solid #00ffad;
            border-radius: 12px;
            padding: 24px;
            margin: 20px 0;
        }

        .rsu-title {
            color: #00ffad;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 12px;
        }

        /* Sugerencias */
        .suggestion-item {
            background: #0c0e12;
            border-left: 3px solid #00ffad;
            padding: 14px 18px;
            margin-bottom: 10px;
            border-radius: 0 8px 8px 0;
            color: #ffffff;
            font-size: 14px;
            line-height: 1.5;
        }

        /* Botón verde */
        .stButton > button {
            background: linear-gradient(90deg, #00ffad 0%, #00cc8a 100%) !important;
            color: #000000 !important;
            border: none !important;
            padding: 16px 32px !important;
            border-radius: 8px !important;
            font-size: 15px !important;
            font-weight: bold !important;
            width: 100% !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: #11141a;
            padding: 10px;
            border-radius: 10px;
            border: 1px solid #1a1e26;
            margin-bottom: 16px;
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: #888888;
            border-radius: 6px;
            padding: 10px 20px;
            font-size: 13px;
        }

        .stTabs [aria-selected="true"] {
            background: #00ffad !important;
            color: #000000 !important;
        }

        /* Tabla financiera */
        .fin-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        .fin-table th {
            background: #1a1e26;
            color: #00ffad;
            padding: 12px;
            text-align: left;
            font-weight: bold;
            border-bottom: 2px solid #2a3f5f;
        }

        .fin-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #1a1e26;
            color: #ffffff;
        }

        .fin-table tr:hover td {
            background: #0c0e12;
        }

        /* Input */
        .stTextInput > div {
            margin-bottom: 12px !important;
        }

        /* Eliminar espacios */
        div[data-testid="stVerticalBlock"] > div {
            margin-bottom: 0 !important;
        }

        .element-container {
            margin-bottom: 0 !important;
        }

        /* Ocultar elementos vacíos */
        .element-container:empty {
            display: none !important;
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

        # Traducir descripción al español
        business_summary = info.get('longBusinessSummary', 'Descripción no disponible.')
        translated_summary = translate_text(business_summary)

    # ─── HEADER DEL TICKER ───
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
    prev_close = info.get('previousClose') or current_price
    price_change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
    change_color = "#00ffad" if price_change >= 0 else "#f23645"

    st.markdown(f"""
        <div class="ticker-box">
            <div>
                <div class="ticker-name">{info.get('longName', t_in)}</div>
                <div class="ticker-meta">{info.get('sector', 'N/A')} • {info.get('industry', 'N/A')} • Market Cap: ${info.get('marketCap', 0)/1e9:.2f}B</div>
            </div>
            <div class="ticker-price-box">
                <div class="ticker-price">${current_price:.2f}</div>
                <div class="ticker-change" style="color: {change_color};">
                    {'+' if price_change >= 0 else ''}{price_change:.2f}%
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ─── GRÁFICO TRADINGVIEW - CONTENEDOR COMPLETO ───
    chart_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>body {{ margin: 0; padding: 0; background: #0c0e12; }}</style>
    </head>
    <body>
        <div id="tv_chart" style="width: 100%; height: 480px;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
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
            "container_id": "tv_chart",
            "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"]
        }});
        </script>
    </body>
    </html>
    """

    # Contenedor completo del gráfico
    st.markdown(f"""
        <div class="box-container">
            <div class="box-header">
                <span class="box-title">📈 Gráfico Avanzado - {t_in}</span>
                <div class="tip-wrap">
                    <div class="tip-icon">?</div>
                    <div class="tip-text">Gráfico interactivo de TradingView con datos en tiempo real.</div>
                </div>
            </div>
            <div style="height: 480px; background: #0c0e12;">
    """, unsafe_allow_html=True)

    components.html(chart_html, height=480)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # ─── SECCIÓN ABOUT - EN ESPAÑOL ───
    st.markdown(f"""
        <div class="box-container">
            <div class="box-header">
                <span class="box-title">ℹ️ Sobre {info.get('shortName', t_in)}</span>
                <div class="tip-wrap">
                    <div class="tip-icon">?</div>
                    <div class="tip-text">Descripción de la empresa traducida al español.</div>
                </div>
            </div>
            <div class="box-content">
                <p style="color: #cccccc; line-height: 1.6; font-size: 14px; margin: 0;">{translated_summary}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ─── PESTAÑAS DE ANÁLISIS ───
    tabs = st.tabs(["📊 Visión General", "💰 Precio Objetivo", "📋 Recomendaciones", "📑 Estados Financieros"])

    # TAB 1: OVERVIEW - TODO DENTRO DEL CONTENEDOR
    with tabs[0]:
        # Inicio del contenedor
        st.markdown("""
            <div class="box-container">
                <div class="box-header">
                    <span class="box-title">💵 Múltiplos de Valoración</span>
                    <div class="tip-wrap">
                        <div class="tip-icon">?</div>
                        <div class="tip-text">Métricas clave para evaluar la valoración de la empresa.</div>
                    </div>
                </div>
                <div class="box-content">
        """, unsafe_allow_html=True)

        # Contenido dentro del contenedor
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
                    <div class="metric-box">
                        <span class="metric-tag">{m['tag']}</span>
                        <div class="metric-label">{m['label']}</div>
                        <div class="metric-value">{v}</div>
                        <div class="metric-desc">{m['desc']}</div>
                    </div>
                """, unsafe_allow_html=True)

        # Cierre del contenedor
        st.markdown("</div></div>", unsafe_allow_html=True)

    # TAB 2: PRECIO OBJETIVO
    with tabs[1]:
        if target_data and target_data['mean']:
            upside = target_data['upside'] or 0
            upside_class = "target-up" if upside >= 0 else "target-down"
            upside_symbol = "▲" if upside >= 0 else "▼"

            # Inicio del contenedor
            st.markdown('<div class="box-container"><div class="box-content">', unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown(f"""
                    <div class="target-box">
                        <div class="target-label">Precio Objetivo Medio</div>
                        <div class="target-price">${target_data['mean']:.2f}</div>
                        <div class="target-badge {upside_class}">
                            {upside_symbol} {abs(upside):.1f}% vs Actual
                        </div>
                        <div style="color: #555555; font-size: 12px; margin-top: 12px;">
                            Basado en {info.get('numberOfAnalystOpinions', 'N/A')} analistas
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                if target_data['low'] and target_data['high']:
                    st.markdown("""
                        <div style="background: linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%); border: 1px solid #1a1e26; border-radius: 12px; padding: 24px; height: 100%;">
                            <div style="color: #ffffff; font-size: 14px; font-weight: bold; margin-bottom: 20px; text-align: center;">RANGO DE PRECIOS</div>
                    """, unsafe_allow_html=True)

                    metrics_range = [
                        ("Mínimo", target_data['low'], "#f23645"),
                        ("Mediana", target_data['median'], "#ff9800"),
                        ("Máximo", target_data['high'], "#00ffad"),
                    ]

                    for label, value, color in metrics_range:
                        if value:
                            st.markdown(f"""
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                                    <span style="color: #888888; font-size: 14px;">{label}</span>
                                    <span style="color: {color}; font-size: 20px; font-weight: bold;">${value:.2f}</span>
                                </div>
                            """, unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

            # Cierre del contenedor
            st.markdown('</div></div>', unsafe_allow_html=True)
        else:
            st.info("No hay datos de precio objetivo disponibles.")

    # TAB 3: RECOMENDACIONES
    with tabs[2]:
        if recommendations and recommendations['total'] > 0:
            # Inicio del contenedor
            st.markdown('<div class="box-container"><div class="box-content">', unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("""
                    <div style="margin-bottom: 20px;">
                        <div style="color: #ffffff; font-size: 14px; font-weight: bold; margin-bottom: 16px;">📊 Distribución de Ratings</div>
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
                        <div class="rating-item">
                            <div class="rating-top">
                                <span class="rating-name">{label}</span>
                                <span class="rating-count" style="color: {color};">{count}</span>
                            </div>
                            <div class="rating-bar">
                                <div class="rating-fill" style="width: {pct}%; background: {color};"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

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
                    <div class="target-box" style="height: auto;">
                        <div style="color: #888888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">
                            Consenso de Analistas
                        </div>
                        <div style="font-size: 32px; font-weight: bold; color: {consensus_color}; margin-bottom: 8px;">
                            {consensus}
                        </div>
                        <div style="color: #888888; font-size: 14px;">
                            {consensus_pct:.0f}% de acuerdo
                        </div>
                        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #333333;">
                            <div style="color: #555555; font-size: 11px;">Total Analistas</div>
                            <div style="color: #ffffff; font-size: 24px; font-weight: bold;">{recommendations['total']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # Cierre del contenedor
            st.markdown('</div></div>', unsafe_allow_html=True)
        else:
            st.info("No hay recomendaciones de analistas disponibles.")

    # TAB 4: FINANCIALS
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
                    'Total Assets': 'Activos Totales',
                    'Total Liabilities': 'Pasivos Totales',
                    'Total Stockholder Equity': 'Patrimonio Neto',
                    'Long Term Debt': 'Deuda a Largo Plazo',
                    'Current Assets': 'Activos Corrientes',
                    'Current Liabilities': 'Pasivos Corrientes',
                }

                # Inicio del contenedor
                table_html = '<div class="box-container"><div class="box-header"><span class="box-title">📑 Estado de Resultados</span></div><div class="box-content"><table class="fin-table">'

                table_html += '<thead><tr><th>Métrica</th>'
                for col in financials.columns:
                    date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)[:10]
                    table_html += f'<th>{date_str}</th>'
                table_html += '</tr></thead><tbody>'

                for idx in financials.index:
                    display_name = index_mapping.get(idx, idx)
                    table_html += f'<tr><td style="font-weight: bold; color: #888;">{display_name}</td>'
                    for col in financials.columns:
                        val = financials.loc[idx, col]
                        formatted = format_financial_value(val)
                        table_html += f'<td>{formatted}</td>'
                    table_html += '</tr>'

                # Cierre del contenedor
                table_html += '</tbody></table></div></div>'

                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.info("Estados financieros no disponibles.")
        except Exception as e:
            st.error(f"Error cargando estados financieros: {e}")

    # ─── SECCIÓN RSU PROMPT ───
    st.markdown("""
        <div class="rsu-box">
            <div class="rsu-title">
                🤖 RSU Artificial Intelligence
            </div>
            <p style="color: #888888; margin-bottom: 20px; font-size: 14px; line-height: 1.5;">
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
                        <div class="box-container" style="margin-top: 20px;">
                            <div class="box-header">
                                <span class="box-title">📋 Informe RSU: {t_in}</span>
                            </div>
                            <div class="box-content" style="background: #0c0e12; border-left: 3px solid #00ffad;">
                                <div style="color: #e0e0e0; line-height: 1.8; font-size: 14px; white-space: pre-wrap;">
                                    {res.text}
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    st.caption(f"🤖 Generado con: {modelo_nombre} | RSU AI Analysis")

                except Exception as e:
                    st.error(f"❌ Error en la generación del informe: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ─── SUGERENCIAS - TODO DENTRO DEL CONTENEDOR ───
    suggestions = get_suggestions(t_in, info, recommendations, target_data)

    # Inicio del contenedor
    st.markdown("""
        <div class="box-container">
            <div class="box-header">
                <span class="box-title">💡 Sugerencias de Inversión</span>
                <div class="tip-wrap">
                    <div class="tip-icon">?</div>
                    <div class="tip-text">Análisis automatizado basado en métricas fundamentales y técnicas actuales.</div>
                </div>
            </div>
            <div class="box-content">
    """, unsafe_allow_html=True)

    # Contenido dentro del contenedor
    for i, suggestion in enumerate(suggestions, 1):
        st.markdown(f"""
            <div class="suggestion-item">
                <strong>{i}.</strong> {suggestion}
            </div>
        """, unsafe_allow_html=True)

    # Cierre del contenedor
    st.markdown('</div></div>', unsafe_allow_html=True)

# Ejecutar render
if __name__ == "__main__":
    render()

