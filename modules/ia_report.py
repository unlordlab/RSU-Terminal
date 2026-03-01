# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import math
import datetime
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
# HELPERS
# ────────────────────────────────────────────────

def _safe(val):
    """Devuelve None si el valor es NaN, None o inf."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val

def format_financial_value(val):
    v = _safe(val)
    if v is None:
        return "N/A"
    if abs(v) >= 1e12: return f"${v/1e12:.2f}T"
    if abs(v) >= 1e9:  return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6:  return f"${v/1e6:.2f}M"
    if abs(v) >= 1e3:  return f"${v/1e3:.2f}K"
    return f"${v:.2f}"

def fmt_x(val):
    """Formatea múltiplo: '27.63×' o 'N/A'."""
    v = _safe(val)
    return f"{v:.2f}×" if v is not None else "N/A"

def fmt_pct(val, mult=1):
    """Formatea porcentaje."""
    v = _safe(val)
    return f"{v * mult:.2f}%" if v is not None else "N/A"

def ts_to_date(ts):
    """Convierte timestamp Unix a fecha legible."""
    try:
        return datetime.datetime.fromtimestamp(int(ts)).strftime('%d %b %Y')
    except Exception:
        return str(ts)

# ────────────────────────────────────────────────
# FUNCIONES DE DATOS — CON CACHÉ (ttl=300s)
# ────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(ticker):
    """Descarga todos los datos del ticker en una sola llamada y los agrupa."""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        # Validar que hay datos reales
        if not info or not (info.get('currentPrice') or info.get('regularMarketPrice') or info.get('regularMarketOpen')):
            return None

        # ── Recomendaciones actuales ──
        recommendations = None
        try:
            recs = stock.recommendations
            if recs is not None and not recs.empty:
                latest = recs.iloc[0]
                sb = int(_safe(latest.get('strongBuy')) or 0)
                b  = int(_safe(latest.get('buy'))       or 0)
                h  = int(_safe(latest.get('hold'))      or 0)
                s  = int(_safe(latest.get('sell'))      or 0)
                ss = int(_safe(latest.get('strongSell'))or 0)
                recommendations = {
                    'strong_buy': sb, 'buy': b, 'hold': h,
                    'sell': s, 'strong_sell': ss,
                    'total': sb + b + h + s + ss
                }
        except Exception:
            pass

        # ── Histórico de recomendaciones ──
        rec_summary = None
        try:
            rs = stock.recommendations_summary
            if rs is not None and not rs.empty:
                rec_summary = rs.head(6)
        except Exception:
            pass

        # ── Precio objetivo ──
        target_mean   = _safe(info.get('targetMeanPrice'))
        target_high   = _safe(info.get('targetHighPrice'))
        target_low    = _safe(info.get('targetLowPrice'))
        target_median = _safe(info.get('targetMedianPrice'))
        current_price = _safe(info.get('currentPrice')) or _safe(info.get('regularMarketPrice'))
        upside = ((target_mean - current_price) / current_price * 100) if (target_mean and current_price) else None
        target_data = {
            'mean': target_mean, 'high': target_high, 'low': target_low,
            'median': target_median, 'current': current_price, 'upside': upside
        }

        # ── Métricas de valoración ──
        metrics = {
            'trailing_pe':    _safe(info.get('trailingPE')),
            'forward_pe':     _safe(info.get('forwardPE')),
            'price_to_sales': _safe(info.get('priceToSalesTrailing12Months')),
            'ev_ebitda':      _safe(info.get('enterpriseToEbitda')),
            'peg_ratio':      _safe(info.get('pegRatio')),
        }

        # ── Métricas de rentabilidad ──
        profitability = {
            'roe':             _safe(info.get('returnOnEquity')),
            'roa':             _safe(info.get('returnOnAssets')),
            'net_margin':      _safe(info.get('profitMargins')),
            'op_margin':       _safe(info.get('operatingMargins')),
            'gross_margin':    _safe(info.get('grossMargins')),
            'revenue_growth':  _safe(info.get('revenueGrowth')),
            'earnings_growth': _safe(info.get('earningsGrowth')),
            'debt_to_equity':  _safe(info.get('debtToEquity')),
            'current_ratio':   _safe(info.get('currentRatio')),
            'free_cashflow':   _safe(info.get('freeCashflow')),
        }

        # ── Eventos corporativos ──
        events = {}
        try:
            cal = stock.calendar
            if cal is not None:
                events = cal if isinstance(cal, dict) else cal.to_dict()
        except Exception:
            pass
        # Añadir desde info
        for k in ['exDividendDate', 'dividendDate']:
            v = _safe(info.get(k))
            if v and k not in events:
                events[k] = v

        # ── Estados financieros ──
        financials = None
        try:
            fin = stock.financials
            if fin is not None and not fin.empty:
                financials = fin
        except Exception:
            pass

        # ── Sparkline (precio 3 meses) ──
        sparkline = None
        try:
            hist = yf.download(ticker, period="3mo", interval="1d", progress=False, auto_adjust=True)
            if not hist.empty:
                close_col = 'Close'
                if isinstance(hist.columns, pd.MultiIndex):
                    close_col = ('Close', ticker)
                sparkline = [_safe(p) for p in hist[close_col].dropna().tolist()]
                sparkline = [p for p in sparkline if p is not None]
        except Exception:
            pass

        return {
            'info': info,
            'recommendations': recommendations,
            'rec_summary': rec_summary,
            'target_data': target_data,
            'metrics': metrics,
            'profitability': profitability,
            'events': events,
            'financials': financials,
            'sparkline': sparkline,
        }
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def translate_text_cached(text, ticker):
    """Traduce texto con caché de 1h por ticker."""
    if not text:
        return 'Descripción no disponible.'
    try:
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        translated = []
        for chunk in chunks:
            url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(chunk)}&langpair=en|es"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('responseStatus') == 200:
                    translated.append(d['responseData']['translatedText'])
                    continue
            translated.append(chunk)
            time.sleep(0.05)
        return ' '.join(translated)
    except Exception:
        return text


def get_suggestions(info, recommendations, target_data, profitability):
    suggestions = []
    pe         = _safe(info.get('trailingPE'))
    forward_pe = _safe(info.get('forwardPE'))

    if pe and forward_pe:
        if forward_pe < pe:
            suggestions.append(f"📈 Forward P/E ({forward_pe:.2f}×) inferior al P/E actual ({pe:.2f}×) — crecimiento de beneficios esperado.")
        else:
            suggestions.append(f"⚠️ Forward P/E ({forward_pe:.2f}×) superior al P/E actual ({pe:.2f}×) — posible contracción de márgenes.")

    if recommendations and recommendations['total'] > 0:
        buy_pct = ((recommendations['strong_buy'] + recommendations['buy']) / recommendations['total']) * 100
        if buy_pct >= 70:
            suggestions.append(f"✅ Fuerte consenso alcista entre analistas ({buy_pct:.0f}% recomiendan comprar).")
        elif buy_pct <= 30:
            suggestions.append(f"🔴 Débil consenso entre analistas ({buy_pct:.0f}% recomiendan comprar). Precaución.")
        else:
            suggestions.append(f"⚖️ Consenso neutral entre analistas ({buy_pct:.0f}% recomiendan comprar).")

    if target_data and target_data.get('mean') and target_data.get('current'):
        upside = target_data['upside']
        if upside and upside > 20:
            suggestions.append(f"🎯 Potencial alcista significativo: +{upside:.1f}% hasta precio objetivo (${target_data['mean']:.2f}).")
        elif upside and upside < -10:
            suggestions.append(f"⚠️ Precio actual supera el objetivo medio en {abs(upside):.1f}%. Posible sobrevaloración.")
        elif upside is not None:
            suggestions.append(f"📊 Precio alineado con consenso de analistas (diferencia: {upside:.1f}%).")

    rg = profitability.get('revenue_growth')
    if rg:
        if rg > 0.15:
            suggestions.append(f"🚀 Crecimiento de ingresos sólido: +{rg*100:.1f}% (trimestral).")
        elif rg < 0:
            suggestions.append(f"📉 Crecimiento de ingresos negativo: {rg*100:.1f}%. Revisar tendencia.")

    roe = profitability.get('roe')
    if roe:
        if roe > 0.20:
            suggestions.append(f"💎 ROE elevado ({roe*100:.1f}%) — alta eficiencia en uso del capital.")
        elif roe < 0.05:
            suggestions.append(f"⚠️ ROE bajo ({roe*100:.1f}%) — baja rentabilidad sobre el capital.")

    nm = profitability.get('net_margin')
    if nm:
        if nm > 0.20:
            suggestions.append(f"💰 Margen neto excelente ({nm*100:.1f}%) — negocio muy rentable.")
        elif nm < 0:
            suggestions.append(f"🔴 Margen neto negativo ({nm*100:.1f}%) — empresa en pérdidas.")

    de = profitability.get('debt_to_equity')
    if de:
        if de > 100:
            suggestions.append(f"💳 Ratio deuda/capital elevado ({de:.1f}). Considerar riesgo financiero.")
        elif de < 50:
            suggestions.append(f"💪 Estructura de capital conservadora (deuda/capital: {de:.1f}).")

    div_yield = _safe(info.get('dividendYield'))
    if div_yield and div_yield > 0:
        suggestions.append(f"💰 La empresa paga dividendos con yield del {div_yield*100:.2f}%.")

    return suggestions if suggestions else ["ℹ️ Datos insuficientes para generar sugerencias específicas."]


# ────────────────────────────────────────────────
# SPARKLINE SVG INLINE
# ────────────────────────────────────────────────

def build_sparkline_svg(prices, width=240, height=48):
    """Genera SVG de sparkline con área de gradiente."""
    if not prices or len(prices) < 2:
        return ""
    mn, mx = min(prices), max(prices)
    rng = mx - mn if mx != mn else 1
    xs = [round(i / (len(prices) - 1) * width, 2) for i in range(len(prices))]
    ys = [round(height - (p - mn) / rng * (height - 4) - 2, 2) for p in prices]
    pts = " ".join(f"{x},{y}" for x, y in zip(xs, ys))
    color = "#00ffad" if prices[-1] >= prices[0] else "#f23645"
    fill_pts = f"0,{height} " + pts + f" {width},{height}"
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.25"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<polygon points="{fill_pts}" fill="url(#sg)"/>'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>'
        f'</svg>'
    )


# ────────────────────────────────────────────────
# CSS GLOBAL
# ────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp { background: #0c0e12; }
        .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 100%; }

        /* ── VT323 ── */
        .vt-label { font-family: 'VT323', monospace; color: #666; font-size: 0.9rem; letter-spacing: 2px; }
        .landing-title {
            font-family: 'VT323', monospace; font-size: 5rem; color: #00ffad;
            text-shadow: 0 0 30px #00ffad55; border-bottom: 2px solid #00ffad33;
            padding-bottom: 10px; margin-bottom: 8px;
            text-transform: uppercase; letter-spacing: 4px; display: inline-block;
        }
        .landing-desc { font-family: 'VT323', monospace; font-size: 1.2rem; color: #00d9ff; letter-spacing: 3px; }

        /* ── INPUT ── */
        .stTextInput > div > div > input {
            background: #0c0e12 !important; border: 1px solid #00ffad33 !important;
            border-radius: 6px !important; color: #00ffad !important;
            font-family: 'VT323', monospace !important; font-size: 1.6rem !important;
            text-align: center; letter-spacing: 4px; padding: 12px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #00ffad !important; box-shadow: 0 0 10px #00ffad22 !important;
        }
        .stTextInput label {
            font-family: 'VT323', monospace !important; color: #888 !important;
            font-size: 1rem !important; letter-spacing: 2px; text-transform: uppercase;
        }

        /* ── BOTONES ── */
        .stButton > button {
            background: linear-gradient(90deg, #00ffad, #00cc8a) !important;
            color: #000 !important; border: none !important; border-radius: 6px !important;
            font-family: 'VT323', monospace !important; font-size: 1.4rem !important;
            letter-spacing: 3px !important; padding: 14px 40px !important;
            width: 100% !important; text-transform: uppercase !important;
            transition: box-shadow 0.2s !important;
        }
        .stButton > button:hover { box-shadow: 0 0 20px #00ffad44 !important; }
        .stDownloadButton > button {
            background: #0c0e12 !important; color: #00ffad !important;
            border: 1px solid #00ffad33 !important; border-radius: 6px !important;
            font-family: 'VT323', monospace !important; font-size: 1rem !important;
            letter-spacing: 2px !important; padding: 8px 20px !important;
            text-transform: uppercase !important; width: auto !important;
        }
        .stDownloadButton > button:hover { border-color: #00ffad88 !important; }

        /* ── MÓDULOS ── */
        .mod-box {
            background: linear-gradient(135deg, #0c0e12 0%, #111520 100%);
            border: 1px solid #00ffad1a; border-radius: 8px;
            overflow: hidden; margin-bottom: 18px; box-shadow: 0 2px 20px #00000040;
        }
        .mod-header {
            background: #0a0c10; padding: 12px 18px; border-bottom: 1px solid #00ffad1a;
            display: flex; justify-content: space-between; align-items: center;
        }
        .mod-title {
            font-family: 'VT323', monospace; color: #00ffad; font-size: 1.2rem;
            letter-spacing: 2px; text-transform: uppercase; margin: 0;
        }
        .mod-body { padding: 18px; }

        /* ── TICKER HEADER ── */
        .ticker-box {
            background: linear-gradient(135deg, #0a0c10 0%, #111520 100%);
            border: 1px solid #00ffad22; border-radius: 8px;
            padding: 18px 24px; margin-bottom: 18px;
            display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 0 30px #00ffad08;
        }
        .ticker-name  { font-family: 'VT323', monospace; font-size: 2.4rem; color: #00ffad; letter-spacing: 3px; text-shadow: 0 0 10px #00ffad33; }
        .ticker-meta  { font-family: 'Courier New', monospace; font-size: 11px; color: #555; margin-top: 4px; }
        .ticker-price { font-family: 'VT323', monospace; font-size: 2.6rem; color: #fff; text-align: right; }
        .ticker-change { font-family: 'VT323', monospace; font-size: 1.2rem; text-align: right; }

        /* ── MÉTRICAS DE VALORACIÓN ── */
        .metric-box {
            background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px;
            padding: 16px; position: relative; height: 100%;
        }
        .metric-tag {
            position: absolute; top: 10px; right: 10px; background: #0f1e35;
            color: #00d9ff; padding: 2px 8px; border-radius: 4px;
            font-family: 'VT323', monospace; font-size: 0.82rem; letter-spacing: 1px;
        }
        .metric-label { font-family: 'VT323', monospace; color: #777; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; margin-top: 4px; }
        .metric-value { font-family: 'VT323', monospace; color: #fff; font-size: 2rem; letter-spacing: 1px; }
        .metric-desc  { font-family: 'Courier New', monospace; color: #444; font-size: 10px; margin-top: 3px; }

        /* ── RENTABILIDAD ── */
        .profit-box {
            background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px;
            padding: 14px 16px;
        }
        .profit-label { font-family: 'VT323', monospace; color: #777; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
        .profit-value { font-family: 'VT323', monospace; font-size: 1.6rem; }

        /* ── RATINGS ── */
        .rating-item  { margin-bottom: 14px; }
        .rating-top   { display: flex; justify-content: space-between; margin-bottom: 5px; }
        .rating-name  { font-family: 'VT323', monospace; color: #ccc; font-size: 1.05rem; letter-spacing: 1px; }
        .rating-count { font-family: 'VT323', monospace; font-size: 1.05rem; font-weight: bold; }
        .rating-bar   { background: #0a0c10; height: 7px; border-radius: 4px; overflow: hidden; }
        .rating-fill  { height: 100%; border-radius: 4px; transition: width 0.6s ease; }

        /* ── PRECIO OBJETIVO ── */
        .target-box   { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 24px; text-align: center; height: 100%; }
        .target-label { font-family: 'VT323', monospace; color: #777; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
        .target-price { font-family: 'VT323', monospace; font-size: 3.2rem; color: #00ffad; text-shadow: 0 0 12px #00ffad33; }

        /* ── CONSENSO ── */
        .consensus-box { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 24px; text-align: center; height: 100%; }

        /* ── EVENTOS ── */
        .event-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #111520; }
        .event-row:last-child { border-bottom: none; }
        .event-label { font-family: 'VT323', monospace; color: #777; font-size: 1rem; letter-spacing: 1px; }
        .event-value { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.05rem; }

        /* ── RSU BOX ── */
        .rsu-box {
            background: linear-gradient(135deg, #0a0c10 0%, #111520 100%);
            border: 1px solid #00ffad33; border-radius: 8px;
            padding: 24px; margin: 18px 0; box-shadow: 0 0 20px #00ffad08;
        }
        .rsu-title { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.5rem; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 10px; }

        /* ── SUGERENCIAS ── */
        .suggestion-item {
            background: #0a0c10; border-left: 2px solid #00ffad;
            padding: 12px 16px; margin-bottom: 8px; border-radius: 0 6px 6px 0;
            font-family: 'Courier New', monospace; color: #ccc; font-size: 13px; line-height: 1.5;
        }

        /* ── ABOUT ── */
        .about-text { font-family: 'Courier New', monospace; color: #aaa; line-height: 1.8; font-size: 0.88rem; }

        /* ── TABS ── */
        .stTabs [data-baseweb="tab-list"]  { gap: 4px; background: #0a0c10; padding: 8px; border-radius: 8px; border: 1px solid #00ffad1a; margin-bottom: 16px; }
        .stTabs [data-baseweb="tab"]        { background: transparent; color: #555; border-radius: 6px; padding: 8px 16px; font-family: 'VT323', monospace; font-size: 0.95rem; letter-spacing: 1px; text-transform: uppercase; }
        .stTabs [aria-selected="true"]      { background: #00ffad !important; color: #000 !important; }

        /* ── TOOLTIP ── */
        .tip-box  { position: relative; cursor: help; }
        .tip-icon { width: 20px; height: 20px; border-radius: 50%; background: #1a1e26; border: 1px solid #333; display: flex; align-items: center; justify-content: center; color: #666; font-size: 11px; font-weight: bold; }
        .tip-text { visibility: hidden; width: 240px; background: #111520; color: #bbb; text-align: left; padding: 10px; border-radius: 6px; position: absolute; z-index: 1000; top: 26px; right: 0; opacity: 0; transition: opacity 0.2s; font-size: 11px; border: 1px solid #1a1e26; font-family: 'Courier New', monospace; box-shadow: 0 4px 20px #00000060; }
        .tip-box:hover .tip-text { visibility: visible; opacity: 1; }

        /* ── MISC ── */
        hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00ffad33, transparent); margin: 24px 0; }
        .hq { background: #00ffad0a; border: 1px solid #00ffad22; border-radius: 8px; padding: 16px 20px; font-family: 'VT323', monospace; font-size: 1.2rem; color: #00ffad99; text-align: center; letter-spacing: 1px; }

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

    # ── TÍTULO CENTRADO ──
    st.markdown("""
    <div style="text-align:center; margin-bottom:24px;">
        <div class="vt-label" style="margin-bottom:10px;">[SECURE CONNECTION ESTABLISHED // RSU ANALYTICS v3.0]</div>
        <div class="landing-title">📊 RSU AI REPORT</div><br>
        <div class="landing-desc">ANÁLISIS FUNDAMENTAL · TÉCNICO · ANALISTAS</div>
    </div>
    """, unsafe_allow_html=True)

    # ── SESSION STATE: recordar último ticker ──
    if 'last_ticker' not in st.session_state:
        st.session_state['last_ticker'] = ''
    if 'last_report' not in st.session_state:
        st.session_state['last_report'] = ''
    if 'last_report_ticker' not in st.session_state:
        st.session_state['last_report_ticker'] = ''

    # ── INPUT CENTRADO ──
    _, col_c, _ = st.columns([1.5, 2, 1.5])
    with col_c:
        t_in = st.text_input(
            "Ticker",
            value=st.session_state['last_ticker'],
            placeholder="NVDA, AAPL, META, IBE.MC…",
            label_visibility="collapsed"
        ).upper().strip()

    if not t_in:
        st.markdown("""
        <div style="text-align:center; margin-top:24px;">
            <div class="hq">▸ Introduce un ticker para iniciar el análisis ◂</div>
            <div style="margin-top:28px; font-family:'Courier New',monospace; color:#333; font-size:11px; letter-spacing:1px;">
                Powered by Yahoo Finance · TradingView · Gemini AI
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Guardar ticker en session_state
    st.session_state['last_ticker'] = t_in

    # ── CARGA DE DATOS (cacheada) ──
    with st.spinner(f"[ CARGANDO {t_in} ... ]"):
        data = get_stock_data(t_in)

    if not data:
        st.error(f"❌ No se pudieron obtener datos para **'{t_in}'**. Verifica que el ticker sea válido (ej: AAPL, NVDA, IBE.MC).")
        return

    info            = data['info']
    recommendations = data['recommendations']
    rec_summary     = data['rec_summary']
    target_data     = data['target_data']
    metrics         = data['metrics']
    profitability   = data['profitability']
    events          = data['events']
    financials      = data['financials']
    sparkline       = data['sparkline']

    # ── TRADUCCIÓN (cacheada por ticker) ──
    business_summary   = info.get('longBusinessSummary', '')
    translated_summary = translate_text_cached(business_summary, t_in)

    # ── CÁLCULOS HEADER ──
    current_price = target_data.get('current') or 0
    prev_close    = _safe(info.get('previousClose')) or current_price
    price_change  = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
    change_color  = "#00ffad" if price_change >= 0 else "#f23645"
    change_arrow  = "▲" if price_change >= 0 else "▼"
    market_cap    = _safe(info.get('marketCap')) or 0
    spark_svg     = build_sparkline_svg(sparkline)

    st.markdown(f"""
    <div class="ticker-box">
        <div>
            <div class="ticker-name">{info.get('shortName', t_in)}</div>
            <div class="ticker-meta">
                {info.get('sector', 'N/A')} &nbsp;·&nbsp; {info.get('industry', 'N/A')}
                &nbsp;·&nbsp; Cap: {format_financial_value(market_cap)}
                &nbsp;·&nbsp; {info.get('exchange', 'N/A')}
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:20px;">
            <div>{spark_svg}</div>
            <div>
                <div class="ticker-price">${current_price:,.2f}</div>
                <div class="ticker-change" style="color:{change_color};">{change_arrow} {abs(price_change):.2f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── GRÁFICO TRADINGVIEW ──
    chart_html = f"""<!DOCTYPE html><html><head>
    <style>body{{margin:0;padding:0;background:#0a0c10;}}</style></head><body>
    <div id="tv_chart" style="width:100%;height:460px;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{
        "autosize":true,"symbol":"{t_in}","interval":"D",
        "timezone":"Europe/Madrid","theme":"dark","style":"1","locale":"es",
        "toolbar_bg":"#0a0c10","enable_publishing":false,"hide_side_toolbar":false,
        "allow_symbol_change":true,"container_id":"tv_chart",
        "studies":["RSI@tv-basicstudies","MASimple@tv-basicstudies"]
    }});
    </script></body></html>"""

    st.markdown(f"""
    <div class="mod-box" style="margin-bottom:0;">
        <div class="mod-header">
            <span class="mod-title">📈 Gráfico Avanzado — {t_in}</span>
            <div class="tip-box">
                <div class="tip-icon">?</div>
                <div class="tip-text">Gráfico interactivo TradingView con datos en tiempo real. Incluye RSI y Media Móvil.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="border:1px solid #00ffad1a;border-top:none;border-radius:0 0 8px 8px;overflow:hidden;margin-bottom:18px;">', unsafe_allow_html=True)
        components.html(chart_html, height=462)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── SOBRE LA EMPRESA ──
    st.markdown(f"""
    <div class="mod-box">
        <div class="mod-header">
            <span class="mod-title">ℹ️ Sobre {info.get('shortName', t_in)}</span>
            <div class="tip-box">
                <div class="tip-icon">?</div>
                <div class="tip-text">Descripción oficial de la empresa traducida al español.</div>
            </div>
        </div>
        <div class="mod-body">
            <p class="about-text">{translated_summary}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════
    # PESTAÑAS PRINCIPALES
    # ════════════════════════════════════════════════
    tabs = st.tabs(["📊 Valoración", "📈 Rentabilidad", "💰 Precio Objetivo", "📋 Recomendaciones", "📅 Eventos", "📑 Financieros"])

    # ══════════════════════
    # TAB 1: VALORACIÓN
    # ══════════════════════
    with tabs[0]:
        valuation_data = [
            ("P/E",         metrics['trailing_pe'],    "Trailing",          "Precio / Beneficio"),
            ("P/S",         metrics['price_to_sales'], "TTM",               "Precio / Ventas"),
            ("EV/EBITDA",   metrics['ev_ebitda'],      "TTM",               "Valor Empresa / EBITDA"),
            ("Forward P/E", metrics['forward_pe'],     "Próx. 12M",         "Precio / BPA Futuro"),
            ("PEG Ratio",   metrics['peg_ratio'],      "P/E ÷ Crec.",       "Valoración ajustada al crecimiento"),
        ]
        row1 = "".join(
            f'<div style="flex:1;min-width:0;">'
            f'<div class="metric-box"><span class="metric-tag">{tag}</span>'
            f'<div class="metric-label">{label}</div>'
            f'<div class="metric-value">{fmt_x(val)}</div>'
            f'<div class="metric-desc">{desc}</div>'
            f'</div></div>'
            for label, val, tag, desc in valuation_data[:3]
        )
        row2 = "".join(
            f'<div style="flex:1;min-width:0;max-width:34%;">'
            f'<div class="metric-box"><span class="metric-tag">{tag}</span>'
            f'<div class="metric-label">{label}</div>'
            f'<div class="metric-value">{fmt_x(val)}</div>'
            f'<div class="metric-desc">{desc}</div>'
            f'</div></div>'
            for label, val, tag, desc in valuation_data[3:]
        )
        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">💵 Múltiplos de Valoración</span>
                <div class="tip-box"><div class="tip-icon">?</div>
                    <div class="tip-text">Métricas para evaluar si la empresa cotiza cara o barata respecto a sus fundamentales.</div>
                </div>
            </div>
            <div class="mod-body">
                <div style="display:flex;gap:10px;margin-bottom:10px;">{row1}</div>
                <div style="display:flex;gap:10px;">{row2}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════
    # TAB 2: RENTABILIDAD
    # ══════════════════════
    with tabs[1]:
        def pc(v, hi=0.15, lo=0.0):
            if v is None: return "#666"
            return "#00ffad" if v >= hi else ("#f23645" if v < lo else "#ff9800")

        roe = profitability.get('roe')
        roa = profitability.get('roa')
        nm  = profitability.get('net_margin')
        om  = profitability.get('op_margin')
        gm  = profitability.get('gross_margin')
        rg  = profitability.get('revenue_growth')
        eg  = profitability.get('earnings_growth')
        de  = profitability.get('debt_to_equity')
        cr  = profitability.get('current_ratio')
        fcf = profitability.get('free_cashflow')

        profit_items = [
            ("ROE",              fmt_pct(roe, 100),  pc(roe, 0.20, 0.05), "Rentabilidad s/ Fondos Propios"),
            ("ROA",              fmt_pct(roa, 100),  pc(roa, 0.10, 0.02), "Rentabilidad s/ Activos"),
            ("Margen Neto",      fmt_pct(nm, 100),   pc(nm, 0.15, 0.0),   "Beneficio Neto / Ingresos"),
            ("Margen Operativo", fmt_pct(om, 100),   pc(om, 0.15, 0.0),   "EBIT / Ingresos"),
            ("Margen Bruto",     fmt_pct(gm, 100),   pc(gm, 0.40, 0.20),  "Beneficio Bruto / Ingresos"),
            ("Crec. Ingresos",   fmt_pct(rg, 100),   pc(rg, 0.10, 0.0),   "Crecimiento YoY"),
            ("Crec. Beneficios", fmt_pct(eg, 100),   pc(eg, 0.10, 0.0),   "Crecimiento YoY EPS"),
            ("Deuda/Capital",
                f"{de:.1f}" if de is not None else "N/A",
                "#f23645" if de and de > 100 else ("#00ffad" if de and de < 50 else "#ff9800"),
                "Ratio de Apalancamiento"),
            ("Ratio Corriente",
                f"{cr:.2f}×" if cr is not None else "N/A",
                "#00ffad" if cr and cr >= 1.5 else ("#f23645" if cr and cr < 1.0 else "#ff9800"),
                "Activo Cte / Pasivo Cte"),
            ("Free Cash Flow",   format_financial_value(fcf),
                "#00ffad" if fcf and fcf > 0 else "#f23645",
                "Flujo de Caja Libre"),
        ]

        rows_html = ""
        for i in range(0, len(profit_items), 2):
            pair = profit_items[i:i+2]
            cells = "".join(
                f'<div style="flex:1;min-width:180px;">'
                f'<div class="profit-box">'
                f'<div class="profit-label">{lb}</div>'
                f'<div class="profit-value" style="color:{col};">{vl}</div>'
                f'<div class="metric-desc">{ds}</div>'
                f'</div></div>'
                for lb, vl, col, ds in pair
            )
            rows_html += f'<div style="display:flex;gap:10px;margin-bottom:10px;">{cells}</div>'

        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">📈 Rentabilidad y Salud Financiera</span>
                <div class="tip-box"><div class="tip-icon">?</div>
                    <div class="tip-text">Verde = bueno · Naranja = neutral · Rojo = precaución. Basado en umbrales estándar de análisis fundamental.</div>
                </div>
            </div>
            <div class="mod-body">{rows_html}</div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════
    # TAB 3: PRECIO OBJETIVO
    # ══════════════════════
    with tabs[2]:
        if target_data and target_data.get('mean'):
            upside      = target_data.get('upside') or 0
            u_arrow     = "▲" if upside >= 0 else "▼"
            b_color     = "#00ffad" if upside >= 0 else "#f23645"
            b_bg        = "rgba(0,255,173,0.10)" if upside >= 0 else "rgba(242,54,69,0.10)"
            n_analysts  = _safe(info.get('numberOfAnalystOpinions')) or 'N/D'

            ranges = [
                ("Objetivo Mínimo",  target_data.get('low'),    "#f23645"),
                ("Objetivo Mediana", target_data.get('median'), "#ff9800"),
                ("Objetivo Máximo",  target_data.get('high'),   "#00ffad"),
            ]
            rng_html = "".join(
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">'
                f'<span style="font-family:Courier New,monospace;color:#777;font-size:12px;">{rl}</span>'
                f'<span style="font-family:VT323,monospace;color:{rc};font-size:1.7rem;">${rv:,.2f}</span>'
                f'</div>'
                for rl, rv, rc in ranges if rv
            )
            st.markdown(f"""
            <div class="mod-box">
                <div class="mod-header"><span class="mod-title">🎯 Precio Objetivo de Analistas</span></div>
                <div class="mod-body">
                    <div style="display:flex;gap:14px;flex-wrap:wrap;">
                        <div style="flex:1;min-width:200px;">
                            <div class="target-box">
                                <div class="target-label">Precio Objetivo Medio</div>
                                <div class="target-price">${target_data['mean']:,.2f}</div>
                                <div style="display:inline-block;margin:8px 0;padding:4px 12px;border-radius:20px;
                                    font-family:VT323,monospace;font-size:1rem;
                                    background:{b_bg};color:{b_color};border:1px solid {b_color}33;">
                                    {u_arrow} {abs(upside):.1f}% vs ${target_data['current']:,.2f}
                                </div>
                                <div style="font-family:Courier New,monospace;color:#444;font-size:11px;margin-top:10px;">
                                    Basado en {n_analysts} analistas
                                </div>
                            </div>
                        </div>
                        <div style="flex:1;min-width:200px;">
                            <div class="target-box" style="text-align:left;">
                                <div style="font-family:VT323,monospace;color:#aaa;font-size:1rem;letter-spacing:2px;
                                    text-align:center;margin-bottom:18px;text-transform:uppercase;">
                                    Rango de Precios Objetivo
                                </div>
                                {rng_html}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No hay datos de precio objetivo disponibles para este ticker.")

    # ══════════════════════
    # TAB 4: RECOMENDACIONES
    # ══════════════════════
    with tabs[3]:
        if recommendations and recommendations['total'] > 0:
            buy_c  = recommendations['strong_buy'] + recommendations['buy']
            hold_c = recommendations['hold']
            sell_c = recommendations['sell'] + recommendations['strong_sell']
            tot    = recommendations['total']

            if buy_c > sell_c and buy_c > hold_c:
                consensus, c_color, c_pct = "ALCISTA", "#00ffad", buy_c / tot * 100
            elif sell_c > buy_c:
                consensus, c_color, c_pct = "BAJISTA", "#f23645", sell_c / tot * 100
            else:
                consensus, c_color, c_pct = "NEUTRAL", "#ff9800", hold_c / tot * 100

            pos_pct = buy_c / tot * 100

            bars_html = "".join(
                f'<div class="rating-item">'
                f'<div class="rating-top">'
                f'<span class="rating-name">{rl}</span>'
                f'<span class="rating-count" style="color:{rc};">{cnt}</span>'
                f'</div>'
                f'<div class="rating-bar"><div class="rating-fill" style="width:{cnt/tot*100:.1f}%;background:{rc};"></div></div>'
                f'</div>'
                for rl, cnt, rc in [
                    ("Compra Fuerte", recommendations['strong_buy'],  "#00ffad"),
                    ("Comprar",       recommendations['buy'],          "#4caf50"),
                    ("Mantener",      recommendations['hold'],         "#ff9800"),
                    ("Vender",        recommendations['sell'],         "#f57c00"),
                    ("Venta Fuerte",  recommendations['strong_sell'],  "#f23645"),
                ]
            )

            st.markdown(f"""
            <div class="mod-box">
                <div class="mod-header"><span class="mod-title">📋 Recomendaciones de Analistas</span></div>
                <div class="mod-body">
                    <div style="display:flex;gap:20px;flex-wrap:wrap;">
                        <div style="flex:3;min-width:240px;">
                            <div style="font-family:VT323,monospace;color:#00ffad;font-size:1rem;
                                letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;">
                                Distribución de Ratings
                                <span style="color:#555;font-size:0.82rem;"> ({tot} analistas)</span>
                            </div>
                            {bars_html}
                        </div>
                        <div style="flex:2;min-width:160px;">
                            <div class="consensus-box">
                                <div style="font-family:VT323,monospace;color:#666;font-size:0.85rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">Consenso</div>
                                <div style="font-family:VT323,monospace;font-size:2.4rem;color:{c_color};text-shadow:0 0 10px {c_color}33;margin-bottom:4px;">{consensus}</div>
                                <div style="font-family:Courier New,monospace;color:#777;font-size:12px;margin-bottom:16px;">{c_pct:.0f}% de acuerdo</div>
                                <div style="border-top:1px solid #1a1e26;padding-top:14px;">
                                    <div style="font-family:VT323,monospace;color:#444;font-size:0.82rem;letter-spacing:1px;">POSITIVOS</div>
                                    <div style="font-family:VT323,monospace;color:#00ffad;font-size:1.8rem;">{pos_pct:.0f}%</div>
                                </div>
                                <div style="border-top:1px solid #1a1e26;padding-top:14px;margin-top:8px;">
                                    <div style="font-family:VT323,monospace;color:#444;font-size:0.82rem;letter-spacing:1px;">TOTAL</div>
                                    <div style="font-family:VT323,monospace;color:#fff;font-size:1.8rem;">{tot}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Histórico de recomendaciones
            if rec_summary is not None and not rec_summary.empty:
                cols_map = {
                    'strongBuy': 'C.Fuerte', 'buy': 'Comprar',
                    'hold': 'Mantener', 'sell': 'Vender', 'strongSell': 'V.Fuerte'
                }
                rs_display = rec_summary.rename(columns=cols_map)
                st.markdown("""
                <div class="mod-box">
                    <div class="mod-header"><span class="mod-title">📆 Histórico de Recomendaciones (últimos 6 meses)</span></div>
                    <div class="mod-body">
                """, unsafe_allow_html=True)
                st.dataframe(rs_display, use_container_width=True)
                st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.info("No hay recomendaciones de analistas disponibles para este ticker.")

    # ══════════════════════
    # TAB 5: EVENTOS
    # ══════════════════════
    with tabs[4]:
        event_map = {
            'Earnings Date':    ('📅', 'Próximos Resultados'),
            'Ex-Dividend Date': ('💵', 'Fecha Ex-Dividendo'),
            'Dividend Date':    ('💰', 'Fecha Pago Dividendo'),
            'exDividendDate':   ('💵', 'Fecha Ex-Dividendo'),
            'dividendDate':     ('💰', 'Fecha Pago Dividendo'),
        }
        rows_html = ""
        for key, val in events.items():
            icon, label = event_map.get(key, ('📌', key.replace('_', ' ').title()))
            if isinstance(val, (int, float)) and val > 1e8:
                val = ts_to_date(val)
            elif isinstance(val, list):
                val = ', '.join(str(v) for v in val if v)
            if val:
                rows_html += (
                    f'<div class="event-row">'
                    f'<span class="event-label">{icon} {label}</span>'
                    f'<span class="event-value">{val}</span>'
                    f'</div>'
                )

        # Dividendo desde info
        dy  = _safe(info.get('dividendYield'))
        dr  = _safe(info.get('dividendRate'))
        eps = _safe(info.get('trailingEps'))
        nfye = _safe(info.get('nextFiscalYearEnd'))

        if dy:
            rows_html += f'<div class="event-row"><span class="event-label">💹 Dividend Yield</span><span class="event-value">{dy*100:.2f}%</span></div>'
        if dr:
            rows_html += f'<div class="event-row"><span class="event-label">💳 Dividendo Anual/Acción</span><span class="event-value">${dr:.2f}</span></div>'
        if eps:
            rows_html += f'<div class="event-row"><span class="event-label">📊 EPS (Trailing)</span><span class="event-value">${eps:.2f}</span></div>'
        if nfye:
            rows_html += f'<div class="event-row"><span class="event-label">📆 Fin Año Fiscal</span><span class="event-value">{ts_to_date(nfye)}</span></div>'

        if not rows_html:
            rows_html = '<div style="font-family:Courier New,monospace;color:#444;font-size:13px;">No hay eventos próximos disponibles para este ticker.</div>'

        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">📅 Eventos Corporativos y Dividendos</span>
                <div class="tip-box"><div class="tip-icon">?</div>
                    <div class="tip-text">Fechas clave: resultados trimestrales, dividendos y ejercicio fiscal.</div>
                </div>
            </div>
            <div class="mod-body">{rows_html}</div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════
    # TAB 6: FINANCIEROS
    # ══════════════════════
    with tabs[5]:
        if financials is not None:
            index_mapping = {
                'Total Revenue': 'Ingresos Totales', 'Net Income': 'Beneficio Neto',
                'Operating Income': 'Benef. Operativo', 'EBITDA': 'EBITDA',
                'Gross Profit': 'Benef. Bruto', 'Research Development': 'I+D',
                'Selling General Administrative': 'Gastos SG&A',
                'Total Operating Expenses': 'Gastos Operativos',
                'Income Before Tax': 'Benef. antes Imptos.',
                'Income Tax Expense': 'Impuesto s/ Benef.',
                'Interest Expense': 'Gastos Intereses',
            }
            financials.index = [index_mapping.get(str(i), str(i)) for i in financials.index]
            st.markdown("""
            <div class="mod-box">
                <div class="mod-header"><span class="mod-title">📑 Estado de Resultados</span></div>
                <div class="mod-body">
            """, unsafe_allow_html=True)
            st.dataframe(financials, use_container_width=True)
            st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.info("Estados financieros no disponibles.")

    # ════════════════════════════════════════════════
    # SECCIÓN RSU AI
    # ════════════════════════════════════════════════
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("""
    <div class="rsu-box">
        <div class="rsu-title">🤖 RSU Artificial Intelligence</div>
        <p style="font-family:'Courier New',monospace;color:#666;font-size:13px;line-height:1.6;margin-bottom:16px;">
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

Datos cuantitativos para enriquecer el análisis:
- Precio actual: ${current_price:.2f}
- P/E Trailing: {fmt_x(metrics['trailing_pe'])} | Forward P/E: {fmt_x(metrics['forward_pe'])} | PEG: {fmt_x(metrics['peg_ratio'])}
- EV/EBITDA: {fmt_x(metrics['ev_ebitda'])} | P/S: {fmt_x(metrics['price_to_sales'])}
- ROE: {fmt_pct(profitability.get('roe'), 100)} | ROA: {fmt_pct(profitability.get('roa'), 100)}
- Margen Neto: {fmt_pct(profitability.get('net_margin'), 100)} | Margen Operativo: {fmt_pct(profitability.get('op_margin'), 100)}
- Precio objetivo medio: {f"${target_data['mean']:.2f} (+{target_data['upside']:.1f}%)" if target_data.get('mean') and target_data.get('upside') else 'N/A'}
- Sector: {info.get('sector', 'N/A')} | Market Cap: {format_financial_value(market_cap)}
- Crecimiento ingresos: {fmt_pct(profitability.get('revenue_growth'), 100)} | Crecimiento beneficios: {fmt_pct(profitability.get('earnings_growth'), 100)}
- Free Cash Flow: {format_financial_value(profitability.get('free_cashflow'))}

Proporciona recomendaciones claras con niveles de entrada, stop-loss y objetivos de precio."""

                    res = model_ia.generate_content(prompt_final)
                    report_text = res.text

                    st.session_state['last_report']        = report_text
                    st.session_state['last_report_ticker'] = t_in

                    st.markdown(f"""
                    <div class="mod-box" style="margin-top:14px;">
                        <div class="mod-header"><span class="mod-title">📋 Informe RSU: {t_in}</span></div>
                        <div class="mod-body" style="background:#0a0c10;border-left:2px solid #00ffad;">
                            <div style="font-family:'Courier New',monospace;color:#ddd;line-height:1.8;font-size:13px;white-space:pre-wrap;">{report_text}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption(f"🤖 Generado con: {modelo_nombre} | RSU AI Analysis")

                except Exception as e:
                    st.error(f"❌ Error en la generación del informe: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── EXPORTAR INFORME ──
    if st.session_state.get('last_report') and st.session_state.get('last_report_ticker') == t_in:
        st.download_button(
            label="⬇️ DESCARGAR INFORME (.txt)",
            data=st.session_state['last_report'].encode('utf-8'),
            file_name=f"RSU_AI_Report_{t_in}.txt",
            mime="text/plain",
            key="download_report"
        )

    # ════════════════════════════════════════════════
    # SUGERENCIAS DE INVERSIÓN
    # ════════════════════════════════════════════════
    suggestions = get_suggestions(info, recommendations, target_data, profitability)
    sug_html    = "".join(
        f'<div class="suggestion-item"><strong style="color:#00ffad;">{i}.</strong> {s}</div>'
        for i, s in enumerate(suggestions, 1)
    )
    st.markdown(f"""
    <div class="mod-box">
        <div class="mod-header">
            <span class="mod-title">💡 Sugerencias de Inversión</span>
            <div class="tip-box"><div class="tip-icon">?</div>
                <div class="tip-text">Análisis automatizado basado en métricas fundamentales. No constituye asesoramiento financiero.</div>
            </div>
        </div>
        <div class="mod-body">{sug_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── FOOTER ──
    st.markdown("""
    <div style="text-align:center;margin-top:40px;padding:20px;border-top:1px solid #0f1218;">
        <div style="font-family:'VT323',monospace;color:#222;font-size:0.82rem;letter-spacing:2px;">
            [END OF REPORT // RSU_AI_REPORT_v3.0]<br>
            [DATA SOURCE: YAHOO FINANCE · TRADINGVIEW · GEMINI AI]<br>
            [STATUS: ACTIVE]
        </div>
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────
if __name__ == "__main__":
    render()



