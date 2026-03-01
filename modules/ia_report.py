# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import math
import datetime
import requests
import time
from config import get_ia_model

# ────────────────────────────────────────────────
# PROMPT RSU — INYECTADO DIRECTAMENTE
# ────────────────────────────────────────────────
PROMPT_RSU = """Por favor, analiza {t} para mí y proporciona lo siguiente, de forma concisa, estructurada y claramente organizada en **formato markdown**:

---

## 1. Explica a qué se dedica la empresa con lenguaje sencillo.

* Tres puntos breves sobre lo que hace.
* Incluye ejemplos o analogías sencillas con las que pueda identificarme.

---

## 2. Resumen profesional (máximo 10 frases)

Incluye:

* Sector.
* Productos/servicios principales.
* Competidores primarios (lista los tickers).
* Métricas o hitos destacables.
* Ventaja competitiva/foso (moat).
* Por qué es única dentro de su industria.
* Si es biotecnológica, especifica si tiene producto comercial o está en fase clínica.

---

## 3. Tabla estratégica: Narrativa y Catalizadores

Incluye en una tabla:

* Temas candentes, narrativa o historia actual de la acción.
* Catalizadores recientes o potenciales (resultados, noticias, macro, sectoriales).
* Datos fundamentales significativos (gran crecimiento en ingresos o beneficios, moat sólido, producto diferencial, liderazgo en gestión, patentes, etc.).

---

## 4. Principales noticias/eventos de los últimos 3 meses

Usa una tabla con:

* Fecha (AAAA-MM-DD).
* Tipo de evento (Resultados, Lanzamiento de producto, Mejora/Degradación de analistas, M&A, etc.).
* Resumen breve (1-2 frases).
* Enlace directo a la fuente.
* Marca claramente cualquier evento que haya movido significativamente el precio.

---

## 5. Fundamentales (Último Trimestre)

Resume:

* Ingresos reportados vs expectativas.
* EPS reportado vs expectativas.
* Márgenes (bruto, operativo, neto si disponible).
* Comentarios relevantes del guidance.
* Reacción del mercado tras resultados.

---

## 6. Análisis Técnico

Incluye:

* Tendencia actual (corto, medio y largo plazo).
* Ondas de Elliott si aplica.
* Niveles clave de soporte y resistencia.
* Zonas de acumulación/distribución si son evidentes.
* Estructura de mercado (máximos/mínimos crecientes o decrecientes).
* Volumen relevante en rupturas o zonas clave.

---

## 7. Smart Money

Analiza:

* Actividad destacada en opciones (volumen inusual, calls/puts agresivas, strikes relevantes).
* Movimientos institucionales recientes.
* Compras/ventas de insiders (especialmente CEO, fundador o equipo ejecutivo).
* Presentaciones institucionales si están disponibles.

---

## 8. Comparativa sectorial (Último mes)

Resume:

* Cómo se ha comportado la acción frente a sus principales competidores.
* Tendencia general del sector (alcista/bajista/lateral).
* Flujos hacia el sector si son visibles.

---

## 9. Próximos catalizadores (próximos 30 días)

Enumera:

* Próximos resultados.
* Lanzamientos de producto.
* Eventos regulatorios.
* Conferencias o presentaciones relevantes.
* Cualquier evento macro que pueda impactar directamente al negocio.

---

## 10. Cambios en precios objetivo de analistas

Resume en formato claro:

* Banco/casa de análisis.
* Precio objetivo anterior vs nuevo.
* Fecha.
* Razonamiento clave del cambio.

---

## 11. Perspectivas

Responde de forma clara y directa:

* ¿Cuál es el sentimiento general actual (bullish, bearish, mixto)?
* ¿Está en fase de acumulación, distribución o continuación?
* ¿Cuáles son los próximos niveles técnicos clave a vigilar?
* ¿Qué tendría que pasar para provocar un gran movimiento?

---

### Enfoque General

Céntrate especialmente en las razones por las cuales la acción podría realizar un gran movimiento en el futuro:

* Beneficios y ventas.
* Cambios en guidance.
* Lanzamientos de productos.
* Mejoras/degradaciones de analistas.
* Compras de insiders (especialmente CEO/Fundador).
* Actividad relevante en opciones.
* Asociaciones estratégicas.
* Catalizadores sectoriales o macro.

Mantén el estilo claro, profesional, directo y orientado a la toma de decisiones de inversión. Responde siempre en castellano."""


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
    if val is None: return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)): return None
    return val

def format_financial_value(val):
    v = _safe(val)
    if v is None: return "N/A"
    if abs(v) >= 1e12: return f"${v/1e12:.2f}T"
    if abs(v) >= 1e9:  return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6:  return f"${v/1e6:.2f}M"
    if abs(v) >= 1e3:  return f"${v/1e3:.2f}K"
    return f"${v:.2f}"

def fmt_x(val):
    v = _safe(val)
    return f"{v:.2f}×" if v is not None else "N/A"

def fmt_pct(val, mult=1):
    v = _safe(val)
    return f"{v * mult:.2f}%" if v is not None else "N/A"

def ts_to_date(ts):
    try:
        return datetime.datetime.fromtimestamp(int(ts)).strftime('%d %b %Y')
    except Exception:
        return str(ts)


# ────────────────────────────────────────────────
# DATOS — CACHÉ
# ────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info
        if not info or not (_safe(info.get('currentPrice')) or _safe(info.get('regularMarketPrice')) or _safe(info.get('regularMarketOpen'))):
            return None

        # Recomendaciones actuales
        recommendations = None
        try:
            recs = stock.recommendations
            if recs is not None and not recs.empty:
                latest = recs.iloc[0]
                sb = int(_safe(latest.get('strongBuy'))  or 0)
                b  = int(_safe(latest.get('buy'))        or 0)
                h  = int(_safe(latest.get('hold'))       or 0)
                s  = int(_safe(latest.get('sell'))       or 0)
                ss = int(_safe(latest.get('strongSell')) or 0)
                recommendations = {'strong_buy': sb, 'buy': b, 'hold': h, 'sell': s, 'strong_sell': ss, 'total': sb+b+h+s+ss}
        except Exception: pass

        # Histórico recomendaciones
        rec_summary = None
        try:
            rs = stock.recommendations_summary
            if rs is not None and not rs.empty:
                rec_summary = rs.head(6)
        except Exception: pass

        # Precio objetivo
        tm = _safe(info.get('targetMeanPrice'))
        cp = _safe(info.get('currentPrice')) or _safe(info.get('regularMarketPrice'))
        target_data = {
            'mean': tm, 'high': _safe(info.get('targetHighPrice')),
            'low': _safe(info.get('targetLowPrice')), 'median': _safe(info.get('targetMedianPrice')),
            'current': cp, 'upside': ((tm - cp) / cp * 100) if (tm and cp) else None
        }

        # Métricas valoración
        metrics = {
            'trailing_pe':    _safe(info.get('trailingPE')),
            'forward_pe':     _safe(info.get('forwardPE')),
            'price_to_sales': _safe(info.get('priceToSalesTrailing12Months')),
            'ev_ebitda':      _safe(info.get('enterpriseToEbitda')),
            'peg_ratio':      _safe(info.get('pegRatio')),
        }

        # Rentabilidad
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

        # Eventos calendario — sólo los relevantes
        events = {}
        try:
            cal = stock.calendar
            if cal is not None:
                raw = cal if isinstance(cal, dict) else cal.to_dict()
                # Filtrar sólo claves conocidas y útiles
                useful_keys = {'Earnings Date', 'Ex-Dividend Date', 'Dividend Date'}
                for k, v in raw.items():
                    if k in useful_keys:
                        events[k] = v
        except Exception: pass
        # Complementar desde info
        for k, label in [('exDividendDate', 'Fecha Ex-Dividendo'), ('dividendDate', 'Fecha Pago Dividendo')]:
            v = _safe(info.get(k))
            if v and 'Ex-Dividend Date' not in events and 'Dividend Date' not in events:
                events[label] = v

        # Estimaciones analistas para próximos earnings
        analyst_estimates = {}
        try:
            cal_raw = stock.calendar
            if cal_raw is not None:
                raw = cal_raw if isinstance(cal_raw, dict) else cal_raw.to_dict()
                for k in ['Earnings High', 'Earnings Low', 'Earnings Average',
                          'Revenue High', 'Revenue Low', 'Revenue Average']:
                    if k in raw and raw[k] is not None:
                        analyst_estimates[k] = raw[k]
        except Exception: pass

        # Sparkline
        sparkline = None
        try:
            hist = yf.download(ticker, period="3mo", interval="1d", progress=False, auto_adjust=True)
            if not hist.empty:
                close_col = ('Close', ticker) if isinstance(hist.columns, pd.MultiIndex) else 'Close'
                sparkline = [p for p in [_safe(x) for x in hist[close_col].dropna().tolist()] if p is not None]
        except Exception: pass

        return {
            'info': info, 'recommendations': recommendations, 'rec_summary': rec_summary,
            'target_data': target_data, 'metrics': metrics, 'profitability': profitability,
            'events': events, 'analyst_estimates': analyst_estimates, 'sparkline': sparkline,
        }
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def translate_text_cached(text, ticker):
    """Traduce descripción de empresa al castellano con caché 1h."""
    if not text: return 'Descripción no disponible.'
    try:
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        translated = []
        for chunk in chunks:
            url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(chunk)}&langpair=en|es"
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('responseStatus') == 200:
                    translated.append(d['responseData']['translatedText'])
                    time.sleep(0.05)
                    continue
            translated.append(chunk)
            time.sleep(0.05)
        return ' '.join(translated)
    except Exception:
        return text


@st.cache_data(ttl=1800, show_spinner=False)
def get_institutional_holders_sec(ticker):
    """
    Obtiene los 13F holders (fondos institucionales) desde yfinance.
    Datos reales de declaraciones 13F a la SEC.
    """
    try:
        stock = yf.Ticker(ticker)
        # institutional_holders: top tenedores institucionales
        inst = stock.institutional_holders
        # major_holders: resumen de % institucional vs retail
        major = stock.major_holders
        # mutual_fund_holders: fondos de inversión
        mutual = stock.mutualfund_holders
        return {
            'institutional': inst,
            'major': major,
            'mutual_funds': mutual,
        }
    except Exception:
        return None


def get_suggestions(info, recommendations, target_data, profitability):
    """Genera sugerencias de inversión basadas en datos reales de la API."""
    suggestions = []
    pe         = _safe(info.get('trailingPE'))
    forward_pe = _safe(info.get('forwardPE'))
    current_p  = target_data.get('current', 0) or 0
    n_analysts = _safe(info.get('numberOfAnalystOpinions')) or 0

    # 1. P/E vs Forward P/E
    if pe and forward_pe and pe > 0 and forward_pe > 0:
        if forward_pe < pe * 0.85:
            suggestions.append(f"📈 Forward P/E ({forward_pe:.2f}×) significativamente inferior al P/E actual ({pe:.2f}×) — fuerte crecimiento de beneficios esperado.")
        elif forward_pe < pe:
            suggestions.append(f"📈 Forward P/E ({forward_pe:.2f}×) inferior al P/E actual ({pe:.2f}×) — crecimiento de beneficios esperado.")
        else:
            suggestions.append(f"⚠️ Forward P/E ({forward_pe:.2f}×) superior al P/E actual ({pe:.2f}×) — posible contracción de márgenes.")

    # 2. Consenso analistas con número real
    if recommendations and recommendations['total'] > 0:
        buy_pct = ((recommendations['strong_buy'] + recommendations['buy']) / recommendations['total']) * 100
        n_buy   = recommendations['strong_buy'] + recommendations['buy']
        if buy_pct >= 75:
            suggestions.append(f"✅ Fuerte consenso alcista: {n_buy} de {recommendations['total']} analistas recomiendan comprar ({buy_pct:.0f}%).")
        elif buy_pct >= 50:
            suggestions.append(f"⚖️ Consenso mayoritariamente alcista: {buy_pct:.0f}% de {recommendations['total']} analistas recomiendan comprar.")
        elif buy_pct <= 30:
            suggestions.append(f"🔴 Consenso débil: sólo {buy_pct:.0f}% de {recommendations['total']} analistas recomiendan comprar.")
        else:
            suggestions.append(f"⚖️ Consenso neutral entre {recommendations['total']} analistas ({buy_pct:.0f}% favorables).")

    # 3. Potencial al precio objetivo con datos reales
    if target_data.get('mean') and current_p:
        upside = target_data['upside']
        mean_p = target_data['mean']
        na_str = f" (consenso de {int(n_analysts)} analistas)" if n_analysts else ""
        if upside and upside > 25:
            suggestions.append(f"🎯 Alto potencial alcista: +{upside:.1f}% hasta objetivo medio ${mean_p:.2f}{na_str}.")
        elif upside and upside > 10:
            suggestions.append(f"📊 Potencial alcista moderado: +{upside:.1f}% hasta precio objetivo ${mean_p:.2f}{na_str}.")
        elif upside and upside < -10:
            suggestions.append(f"⚠️ Cotización {abs(upside):.1f}% por encima del objetivo medio (${mean_p:.2f}). Posible sobrevaloración.")
        elif upside is not None:
            suggestions.append(f"📊 Precio alineado con consenso de analistas (±{abs(upside):.1f}% del objetivo ${mean_p:.2f}).")

    # 4. Crecimiento ingresos
    rg = profitability.get('revenue_growth')
    if rg is not None:
        if rg > 0.25:
            suggestions.append(f"🚀 Crecimiento de ingresos excepcional: +{rg*100:.1f}% interanual.")
        elif rg > 0.10:
            suggestions.append(f"📈 Crecimiento de ingresos sólido: +{rg*100:.1f}% interanual.")
        elif rg > 0:
            suggestions.append(f"📊 Crecimiento de ingresos modesto: +{rg*100:.1f}% interanual.")
        else:
            suggestions.append(f"📉 Ingresos en contracción: {rg*100:.1f}% interanual. Revisar tendencia.")

    # 5. ROE con benchmark
    roe = profitability.get('roe')
    if roe is not None:
        if roe > 0.30:
            suggestions.append(f"💎 ROE excepcional ({roe*100:.1f}%) — empresa muy eficiente en generar beneficios con el capital.")
        elif roe > 0.15:
            suggestions.append(f"💚 ROE sólido ({roe*100:.1f}%) — buena rentabilidad sobre fondos propios.")
        elif roe < 0:
            suggestions.append(f"🔴 ROE negativo ({roe*100:.1f}%) — empresa destruyendo valor actualmente.")

    # 6. Margen neto
    nm = profitability.get('net_margin')
    if nm is not None:
        if nm > 0.25:
            suggestions.append(f"💰 Margen neto excepcional ({nm*100:.1f}%) — negocio altamente rentable.")
        elif nm > 0.10:
            suggestions.append(f"✅ Margen neto sólido ({nm*100:.1f}%).")
        elif nm < 0:
            suggestions.append(f"🔴 Margen neto negativo ({nm*100:.1f}%) — empresa en pérdidas. Verificar si es estructural o transitorio.")

    # 7. Deuda
    de = profitability.get('debt_to_equity')
    if de is not None:
        if de > 150:
            suggestions.append(f"💳 Endeudamiento muy elevado (D/E: {de:.0f}%) — riesgo financiero alto en entorno de tipos altos.")
        elif de > 80:
            suggestions.append(f"⚠️ Endeudamiento moderado-alto (D/E: {de:.0f}%). Vigilar cobertura de intereses.")
        elif de < 30:
            suggestions.append(f"💪 Balance conservador (D/E: {de:.0f}%) — solidez financiera, flexibilidad para invertir o recomprar.")

    # 8. Free Cash Flow
    fcf = profitability.get('free_cashflow')
    if fcf is not None:
        if fcf > 0:
            suggestions.append(f"💵 Free Cash Flow positivo ({format_financial_value(fcf)}) — empresa genera caja real, puede recomprar acciones o pagar dividendos.")
        else:
            suggestions.append(f"⚠️ Free Cash Flow negativo ({format_financial_value(fcf)}) — empresa consume caja. Evaluar si es inversión de crecimiento o señal de alerta.")

    # 9. Dividendo
    dy = _safe(info.get('dividendYield'))
    dr = _safe(info.get('dividendRate'))
    if dy and dy > 0 and dr:
        suggestions.append(f"💰 Dividendo anual: ${dr:.2f}/acción (yield {dy*100:.2f}%) — fuente de rentabilidad adicional.")

    # 10. PEG
    peg = _safe(info.get('pegRatio'))
    if peg and peg > 0:
        if peg < 1:
            suggestions.append(f"🟢 PEG Ratio {peg:.2f} — potencialmente infravalorada respecto a su crecimiento (PEG < 1 es señal positiva).")
        elif peg > 3:
            suggestions.append(f"🔴 PEG Ratio {peg:.2f} — valoración muy exigente respecto al crecimiento esperado.")

    return suggestions if suggestions else ["ℹ️ Datos insuficientes para generar sugerencias específicas."]


# ────────────────────────────────────────────────
# SPARKLINE SVG
# ────────────────────────────────────────────────

def build_sparkline_svg(prices, width=240, height=48):
    if not prices or len(prices) < 2: return ""
    mn, mx = min(prices), max(prices)
    rng = mx - mn if mx != mn else 1
    xs = [round(i / (len(prices) - 1) * width, 2) for i in range(len(prices))]
    ys = [round(height - (p - mn) / rng * (height - 4) - 2, 2) for p in prices]
    pts  = " ".join(f"{x},{y}" for x, y in zip(xs, ys))
    color = "#00ffad" if prices[-1] >= prices[0] else "#f23645"
    fill  = f"0,{height} " + pts + f" {width},{height}"
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.25"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<polygon points="{fill}" fill="url(#sg)"/>'
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

        .vt-label { font-family: 'VT323', monospace; color: #666; font-size: 0.9rem; letter-spacing: 2px; }
        .landing-title {
            font-family: 'VT323', monospace; font-size: 5rem; color: #00ffad;
            text-shadow: 0 0 30px #00ffad55; border-bottom: 2px solid #00ffad33;
            padding-bottom: 10px; margin-bottom: 8px;
            text-transform: uppercase; letter-spacing: 4px; display: inline-block;
        }
        .landing-desc { font-family: 'VT323', monospace; font-size: 1.2rem; color: #00d9ff; letter-spacing: 3px; }

        /* INPUT */
        .stTextInput > div > div > input {
            background: #0c0e12 !important; border: 1px solid #00ffad33 !important;
            border-radius: 6px !important; color: #00ffad !important;
            font-family: 'VT323', monospace !important; font-size: 1.6rem !important;
            text-align: center; letter-spacing: 4px; padding: 12px !important;
        }
        .stTextInput > div > div > input:focus { border-color: #00ffad !important; box-shadow: 0 0 10px #00ffad22 !important; }
        .stTextInput label { font-family: 'VT323', monospace !important; color: #888 !important; font-size: 1rem !important; letter-spacing: 2px; text-transform: uppercase; }

        /* BOTONES */
        .stButton > button {
            background: linear-gradient(90deg, #00ffad, #00cc8a) !important;
            color: #000 !important; border: none !important; border-radius: 6px !important;
            font-family: 'VT323', monospace !important; font-size: 1.4rem !important;
            letter-spacing: 3px !important; padding: 14px 40px !important;
            width: 100% !important; text-transform: uppercase !important;
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

        /* MÓDULOS */
        .mod-box { background: linear-gradient(135deg, #0c0e12 0%, #111520 100%); border: 1px solid #00ffad1a; border-radius: 8px; overflow: hidden; margin-bottom: 18px; box-shadow: 0 2px 20px #00000040; }
        .mod-header { background: #0a0c10; padding: 12px 18px; border-bottom: 1px solid #00ffad1a; display: flex; justify-content: space-between; align-items: center; }
        .mod-title { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.2rem; letter-spacing: 2px; text-transform: uppercase; margin: 0; }
        .mod-body { padding: 18px; }

        /* TICKER HEADER */
        .ticker-box { background: linear-gradient(135deg, #0a0c10 0%, #111520 100%); border: 1px solid #00ffad22; border-radius: 8px; padding: 18px 24px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 30px #00ffad08; }
        .ticker-name  { font-family: 'VT323', monospace; font-size: 2.4rem; color: #00ffad; letter-spacing: 3px; text-shadow: 0 0 10px #00ffad33; }
        .ticker-meta  { font-family: 'Courier New', monospace; font-size: 11px; color: #555; margin-top: 4px; }
        .ticker-price  { font-family: 'VT323', monospace; font-size: 2.6rem; color: #fff; text-align: right; }
        .ticker-change { font-family: 'VT323', monospace; font-size: 1.2rem; text-align: right; }

        /* MÉTRICAS VALORACIÓN — tamaño igual forzado */
        .metric-box { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 16px; position: relative; height: 130px; box-sizing: border-box; }
        .metric-tag { position: absolute; top: 10px; right: 10px; background: #0f1e35; color: #00d9ff; padding: 2px 8px; border-radius: 4px; font-family: 'VT323', monospace; font-size: 0.82rem; letter-spacing: 1px; }
        .metric-label { font-family: 'VT323', monospace; color: #777; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; margin-top: 4px; }
        .metric-value { font-family: 'VT323', monospace; font-size: 2rem; letter-spacing: 1px; }
        .metric-desc  { font-family: 'Courier New', monospace; color: #444; font-size: 10px; margin-top: 3px; }

        /* RENTABILIDAD */
        .profit-box { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 14px 16px; }
        .profit-label { font-family: 'VT323', monospace; color: #777; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
        .profit-value { font-family: 'VT323', monospace; font-size: 1.6rem; }

        /* RATINGS */
        .rating-item  { margin-bottom: 14px; }
        .rating-top   { display: flex; justify-content: space-between; margin-bottom: 5px; }
        .rating-name  { font-family: 'VT323', monospace; color: #ccc; font-size: 1.05rem; letter-spacing: 1px; }
        .rating-count { font-family: 'VT323', monospace; font-size: 1.05rem; font-weight: bold; }
        .rating-bar   { background: #0a0c10; height: 7px; border-radius: 4px; overflow: hidden; }
        .rating-fill  { height: 100%; border-radius: 4px; }

        /* PRECIO OBJETIVO */
        .target-box   { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 24px; text-align: center; height: 100%; }
        .target-label { font-family: 'VT323', monospace; color: #777; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
        .target-price { font-family: 'VT323', monospace; font-size: 3.2rem; color: #00ffad; text-shadow: 0 0 12px #00ffad33; }

        /* CONSENSO */
        .consensus-box { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 24px; text-align: center; height: 100%; }

        /* EVENTOS */
        .event-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #111520; }
        .event-row:last-child { border-bottom: none; }
        .event-label { font-family: 'VT323', monospace; color: #888; font-size: 1rem; letter-spacing: 1px; }
        .event-value { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.05rem; }

        /* ESTIMACIONES ANALISTAS */
        .estimate-box { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px; }
        .estimate-label { font-family: 'VT323', monospace; color: #777; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
        .estimate-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; }
        .estimate-key { font-family: 'Courier New', monospace; color: #666; font-size: 11px; }
        .estimate-val { font-family: 'VT323', monospace; color: #00ffad; font-size: 1rem; }

        /* FONDOS — HEDGE FUND CARDS */
        .fund-card { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 16px 18px; margin-bottom: 10px; transition: border-color 0.2s; }
        .fund-card:hover { border-color: #00ffad44; }
        .fund-name { font-family: 'VT323', monospace; color: #fff; font-size: 1.15rem; letter-spacing: 1px; }
        .fund-meta { font-family: 'Courier New', monospace; color: #555; font-size: 11px; margin-top: 2px; }
        .fund-shares { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.3rem; }
        .fund-change-up   { font-family: 'VT323', monospace; color: #00ffad; font-size: 0.9rem; }
        .fund-change-down { font-family: 'VT323', monospace; color: #f23645; font-size: 0.9rem; }
        .fund-change-new  { font-family: 'VT323', monospace; color: #00d9ff; font-size: 0.9rem; }

        /* RSU BOX */
        .rsu-box { background: linear-gradient(135deg, #0a0c10 0%, #111520 100%); border: 1px solid #00ffad33; border-radius: 8px; padding: 24px; margin: 18px 0; box-shadow: 0 0 20px #00ffad08; }
        .rsu-title { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.5rem; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 10px; }

        /* INFORME IA MARKDOWN — estilos dentro del contenedor */
        .ia-report-body { font-family: 'Courier New', monospace; color: #ccc; line-height: 1.8; font-size: 13px; }
        .ia-report-body h1,h2 { font-family: 'VT323', monospace; color: #00ffad; letter-spacing: 2px; }
        .ia-report-body h3 { font-family: 'VT323', monospace; color: #00d9ff; }
        .ia-report-body table { border-collapse: collapse; width: 100%; margin: 12px 0; }
        .ia-report-body th { background: #0f1e35; color: #00d9ff; font-family: 'VT323', monospace; padding: 8px 12px; letter-spacing: 1px; }
        .ia-report-body td { border-bottom: 1px solid #1a1e26; padding: 8px 12px; color: #bbb; font-size: 12px; }
        .ia-report-body strong { color: #00ffad; }
        .ia-report-body code { background: #0f1218; color: #00d9ff; padding: 1px 5px; border-radius: 3px; font-size: 11px; }
        .ia-report-body hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00ffad33, transparent); margin: 16px 0; }

        /* SUGERENCIAS */
        .suggestion-item { background: #0a0c10; border-left: 2px solid #00ffad; padding: 12px 16px; margin-bottom: 8px; border-radius: 0 6px 6px 0; font-family: 'Courier New', monospace; color: #ccc; font-size: 13px; line-height: 1.5; }

        /* ABOUT */
        .about-text { font-family: 'Courier New', monospace; color: #aaa; line-height: 1.8; font-size: 0.88rem; }

        /* TABS */
        .stTabs [data-baseweb="tab-list"]  { gap: 4px; background: #0a0c10; padding: 8px; border-radius: 8px; border: 1px solid #00ffad1a; margin-bottom: 16px; }
        .stTabs [data-baseweb="tab"]        { background: transparent; color: #555; border-radius: 6px; padding: 8px 14px; font-family: 'VT323', monospace; font-size: 0.9rem; letter-spacing: 1px; text-transform: uppercase; }
        .stTabs [aria-selected="true"]      { background: #00ffad !important; color: #000 !important; }

        /* TOOLTIP — z-index elevado para que no quede tapado */
        .tip-box  { position: relative; cursor: help; z-index: 10; }
        .tip-icon { width: 20px; height: 20px; border-radius: 50%; background: #1a1e26; border: 1px solid #333; display: flex; align-items: center; justify-content: center; color: #666; font-size: 11px; font-weight: bold; }
        .tip-text {
            visibility: hidden; width: 260px; background: #111520; color: #bbb;
            text-align: left; padding: 12px; border-radius: 6px;
            position: fixed;   /* fixed en vez de absolute para evitar overflow del contenedor */
            z-index: 9999;
            opacity: 0; transition: opacity 0.2s;
            font-size: 11px; border: 1px solid #00ffad22; font-family: 'Courier New', monospace;
            box-shadow: 0 4px 24px #00000080;
            pointer-events: none;
        }
        .tip-box:hover .tip-text { visibility: visible; opacity: 1; }

        /* MISC */
        hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00ffad33, transparent); margin: 24px 0; }
        .hq { background: #00ffad0a; border: 1px solid #00ffad22; border-radius: 8px; padding: 16px 20px; font-family: 'VT323', monospace; font-size: 1.2rem; color: #00ffad99; text-align: center; letter-spacing: 1px; }

        /* streamlit cleanups */
        div[data-testid="stVerticalBlock"] > div { margin-bottom: 0 !important; }
        .element-container { margin-bottom: 0 !important; }
        .stTextInput > div { margin-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────
# RENDER
# ────────────────────────────────────────────────

def render():
    inject_css()

    # TÍTULO CENTRADO
    st.markdown("""
    <div style="text-align:center; margin-bottom:24px;">
        <div class="vt-label" style="margin-bottom:10px;">[CONEXIÓN SEGURA ESTABLECIDA // RSU ANALYTICS v3.0]</div>
        <div class="landing-title">📊 RSU AI REPORT</div><br>
        <div class="landing-desc">ANÁLISIS FUNDAMENTAL · TÉCNICO · ANALISTAS</div>
    </div>
    """, unsafe_allow_html=True)

    # SESSION STATE
    for k, v in [('last_ticker', ''), ('last_report', ''), ('last_report_ticker', '')]:
        if k not in st.session_state:
            st.session_state[k] = v

    # INPUT CENTRADO
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

    st.session_state['last_ticker'] = t_in

    # CARGA DE DATOS
    with st.spinner(f"[ CARGANDO {t_in} ... ]"):
        data = get_stock_data(t_in)

    if not data:
        st.error(f"❌ No se encontraron datos para **'{t_in}'**. Verifica que el ticker sea válido.")
        return

    info              = data['info']
    recommendations   = data['recommendations']
    rec_summary       = data['rec_summary']
    target_data       = data['target_data']
    metrics           = data['metrics']
    profitability     = data['profitability']
    events            = data['events']
    analyst_estimates = data['analyst_estimates']
    sparkline         = data['sparkline']

    # TRADUCCIÓN (castellano, cacheada)
    translated_summary = translate_text_cached(info.get('longBusinessSummary', ''), t_in)

    # CÁLCULOS HEADER
    current_price = target_data.get('current') or 0
    prev_close    = _safe(info.get('previousClose')) or current_price
    price_change  = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
    change_color  = "#00ffad" if price_change >= 0 else "#f23645"
    change_arrow  = "▲" if price_change >= 0 else "▼"
    market_cap    = _safe(info.get('marketCap')) or 0
    spark_svg     = build_sparkline_svg(sparkline)

    # TICKER HEADER
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

    # GRÁFICO TRADINGVIEW
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
                <div class="tip-text">Gráfico TradingView interactivo en tiempo real. Incluye RSI (fuerza relativa) y Media Móvil de 9 sesiones. Puedes cambiar timeframe y añadir indicadores.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="border:1px solid #00ffad1a;border-top:none;border-radius:0 0 8px 8px;overflow:hidden;margin-bottom:18px;">', unsafe_allow_html=True)
        components.html(chart_html, height=462)
        st.markdown('</div>', unsafe_allow_html=True)

    # SOBRE LA EMPRESA
    st.markdown(f"""
    <div class="mod-box">
        <div class="mod-header">
            <span class="mod-title">ℹ️ Sobre {info.get('shortName', t_in)}</span>
            <div class="tip-box"><div class="tip-icon">?</div>
                <div class="tip-text">Descripción oficial de la empresa traducida al castellano desde Yahoo Finance.</div>
            </div>
        </div>
        <div class="mod-body"><p class="about-text">{translated_summary}</p></div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════
    # PESTAÑAS
    # ══════════════════════════════════════════════
    tabs = st.tabs(["📊 Valoración", "📈 Rentabilidad", "💰 Precio Objetivo", "📋 Recomendaciones", "📅 Eventos", "🏦 Fondos Institucionales"])

    # ══ TAB 1: VALORACIÓN ══
    with tabs[0]:
        def valuation_color(name, val):
            v = _safe(val)
            if v is None: return "#888"
            if v < 0: return "#f23645"
            thresholds = {
                "P/E":         (15, 30),
                "P/S":         (2,  8),
                "EV/EBITDA":   (10, 20),
                "Forward P/E": (12, 25),
                "PEG Ratio":   (1,  2),
            }
            lo, hi = thresholds.get(name, (0, 9999))
            if v <= lo: return "#00ffad"
            if v >= hi: return "#f23645"
            return "#ff9800"

        valuation_data = [
            ("P/E",         metrics['trailing_pe'],    "Trailing",    "Precio / Beneficio"),
            ("P/S",         metrics['price_to_sales'], "TTM",         "Precio / Ventas"),
            ("EV/EBITDA",   metrics['ev_ebitda'],      "TTM",         "Valor Empresa / EBITDA"),
            ("Forward P/E", metrics['forward_pe'],     "Próx. 12M",   "Precio / BPA Futuro"),
            ("PEG Ratio",   metrics['peg_ratio'],      "P/E ÷ Crec.", "Valoración ajustada al crecimiento"),
        ]
        row1 = "".join(
            f'<div style="flex:1;min-width:0;">'
            f'<div class="metric-box"><span class="metric-tag">{tag}</span>'
            f'<div class="metric-label">{label}</div>'
            f'<div class="metric-value" style="color:{valuation_color(label, val)};">{fmt_x(val)}</div>'
            f'<div class="metric-desc">{desc}</div>'
            f'</div></div>'
            for label, val, tag, desc in valuation_data[:3]
        )
        row2 = "".join(
            f'<div style="flex:1;min-width:0;">'
            f'<div class="metric-box"><span class="metric-tag">{tag}</span>'
            f'<div class="metric-label">{label}</div>'
            f'<div class="metric-value" style="color:{valuation_color(label, val)};">{fmt_x(val)}</div>'
            f'<div class="metric-desc">{desc}</div>'
            f'</div></div>'
            for label, val, tag, desc in valuation_data[3:]
        )
        # Placeholder vacío para alinear la fila 2 a 3 columnas
        row2 += '<div style="flex:1;min-width:0;"></div>'

        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">💵 Múltiplos de Valoración</span>
                <div class="tip-box"><div class="tip-icon">?</div>
                    <div class="tip-text">Verde = barato · Naranja = valoración media · Rojo = caro. Umbrales estándar de análisis fundamental.</div>
                </div>
            </div>
            <div class="mod-body">
                <div style="display:flex;gap:10px;margin-bottom:10px;">{row1}</div>
                <div style="display:flex;gap:10px;">{row2}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══ TAB 2: RENTABILIDAD ══
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
                f"{de:.1f}%" if de is not None else "N/A",
                "#f23645" if de and de > 100 else ("#00ffad" if de and de < 50 else "#ff9800"),
                "Ratio de Apalancamiento"),
            ("Ratio Corriente",
                f"{cr:.2f}×" if cr is not None else "N/A",
                "#00ffad" if cr and cr >= 1.5 else ("#f23645" if cr and cr < 1.0 else "#ff9800"),
                "Activo Cte / Pasivo Cte"),
            ("Free Cash Flow", format_financial_value(fcf),
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
                    <div class="tip-text">Verde = bueno · Naranja = neutral · Rojo = precaución. Umbrales estándar de análisis fundamental.</div>
                </div>
            </div>
            <div class="mod-body">{rows_html}</div>
        </div>
        """, unsafe_allow_html=True)

    # ══ TAB 3: PRECIO OBJETIVO ══
    with tabs[2]:
        if target_data and target_data.get('mean'):
            upside     = target_data.get('upside') or 0
            u_arrow    = "▲" if upside >= 0 else "▼"
            b_color    = "#00ffad" if upside >= 0 else "#f23645"
            b_bg       = "rgba(0,255,173,0.10)" if upside >= 0 else "rgba(242,54,69,0.10)"
            n_analysts = _safe(info.get('numberOfAnalystOpinions')) or 'N/D'
            rng_html   = "".join(
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">'
                f'<span style="font-family:Courier New,monospace;color:#777;font-size:12px;">{rl}</span>'
                f'<span style="font-family:VT323,monospace;color:{rc};font-size:1.7rem;">${rv:,.2f}</span>'
                f'</div>'
                for rl, rv, rc in [
                    ("Objetivo Mínimo",  target_data.get('low'),    "#f23645"),
                    ("Objetivo Mediana", target_data.get('median'), "#ff9800"),
                    ("Objetivo Máximo",  target_data.get('high'),   "#00ffad"),
                ] if rv
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
                                    Consenso de {n_analysts} analistas
                                </div>
                            </div>
                        </div>
                        <div style="flex:1;min-width:200px;">
                            <div class="target-box" style="text-align:left;">
                                <div style="font-family:VT323,monospace;color:#aaa;font-size:1rem;letter-spacing:2px;text-align:center;margin-bottom:18px;text-transform:uppercase;">Rango de Precios Objetivo</div>
                                {rng_html}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No hay datos de precio objetivo disponibles para este ticker.")

    # ══ TAB 4: RECOMENDACIONES ══
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
                            <div style="font-family:VT323,monospace;color:#00ffad;font-size:1rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;">
                                Distribución de Ratings <span style="color:#555;font-size:0.82rem;">({tot} analistas)</span>
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
                                    <div style="font-family:VT323,monospace;color:#444;font-size:0.82rem;letter-spacing:1px;">TOTAL ANALISTAS</div>
                                    <div style="font-family:VT323,monospace;color:#fff;font-size:1.8rem;">{tot}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if rec_summary is not None and not rec_summary.empty:
                cols_map = {'strongBuy': 'C.Fuerte', 'buy': 'Comprar', 'hold': 'Mantener', 'sell': 'Vender', 'strongSell': 'V.Fuerte'}
                st.markdown("""<div class="mod-box"><div class="mod-header"><span class="mod-title">📆 Histórico de Recomendaciones (últimos 6 meses)</span></div><div class="mod-body">""", unsafe_allow_html=True)
                st.dataframe(rec_summary.rename(columns=cols_map), use_container_width=True)
                st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.info("No hay recomendaciones de analistas disponibles para este ticker.")

    # ══ TAB 5: EVENTOS ══
    with tabs[4]:
        # ── Fechas clave ──
        event_map = {
            'Earnings Date':       ('📅', 'Próximos Resultados Trimestrales'),
            'Ex-Dividend Date':    ('💵', 'Fecha Ex-Dividendo'),
            'Dividend Date':       ('💰', 'Fecha de Pago del Dividendo'),
            'Fecha Ex-Dividendo':  ('💵', 'Fecha Ex-Dividendo'),
            'Fecha Pago Dividendo':('💰', 'Fecha de Pago del Dividendo'),
        }
        fechas_html = ""
        for key, val in events.items():
            icon, label = event_map.get(key, ('📌', key))
            if isinstance(val, (int, float)) and val > 1e8:
                val = ts_to_date(val)
            elif isinstance(val, list):
                val = ', '.join(str(v) for v in val if v)
            if val:
                fechas_html += (
                    f'<div class="event-row">'
                    f'<span class="event-label">{icon} {label}</span>'
                    f'<span class="event-value">{val}</span>'
                    f'</div>'
                )

        # ── Datos extra desde info ──
        dy   = _safe(info.get('dividendYield'))
        dr   = _safe(info.get('dividendRate'))
        eps  = _safe(info.get('trailingEps'))
        nfye = _safe(info.get('nextFiscalYearEnd'))
        if dy:   fechas_html += f'<div class="event-row"><span class="event-label">💹 Dividend Yield</span><span class="event-value">{dy*100:.2f}%</span></div>'
        if dr:   fechas_html += f'<div class="event-row"><span class="event-label">💳 Dividendo Anual por Acción</span><span class="event-value">${dr:.2f}</span></div>'
        if eps:  fechas_html += f'<div class="event-row"><span class="event-label">📊 BPA (Trailing)</span><span class="event-value">${eps:.2f}</span></div>'
        if nfye: fechas_html += f'<div class="event-row"><span class="event-label">📆 Fin Año Fiscal</span><span class="event-value">{ts_to_date(nfye)}</span></div>'

        if not fechas_html:
            fechas_html = '<div style="font-family:Courier New,monospace;color:#444;font-size:13px;">No hay eventos disponibles para este ticker.</div>'

        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">📅 Calendario Corporativo</span>
                <div class="tip-box"><div class="tip-icon">?</div>
                    <div class="tip-text">Fechas clave obtenidas de Yahoo Finance: próxima presentación de resultados, dividendos y cierre de ejercicio fiscal.</div>
                </div>
            </div>
            <div class="mod-body">{fechas_html}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Estimaciones de analistas para próximos resultados ──
        if analyst_estimates:
            eps_hi  = analyst_estimates.get('Earnings High')
            eps_lo  = analyst_estimates.get('Earnings Low')
            eps_avg = analyst_estimates.get('Earnings Average')
            rev_hi  = analyst_estimates.get('Revenue High')
            rev_lo  = analyst_estimates.get('Revenue Low')
            rev_avg = analyst_estimates.get('Revenue Average')

            est_html = ""
            if any([eps_hi, eps_lo, eps_avg]):
                est_html += """
                <div class="estimate-box">
                    <div class="estimate-label">📊 Estimaciones de BPA (Beneficio por Acción) — próximo trimestre</div>
                    <div style="font-family:Courier New,monospace;color:#666;font-size:11px;margin-bottom:10px;">
                        Rango de estimaciones que los analistas esperan que reporte la empresa (consenso de Wall Street)
                    </div>
                """
                for lbl, val in [("Estimación Alta (optimista)", eps_hi), ("Estimación Media (consenso)", eps_avg), ("Estimación Baja (pesimista)", eps_lo)]:
                    if val is not None:
                        color = "#00ffad" if lbl == "Estimación Media (consenso)" else "#aaa"
                        est_html += f'<div class="estimate-row"><span class="estimate-key">{lbl}</span><span class="estimate-val" style="color:{color};">${val:.2f}</span></div>'
                est_html += "</div>"

            if any([rev_hi, rev_lo, rev_avg]):
                est_html += """
                <div class="estimate-box">
                    <div class="estimate-label">💰 Estimaciones de Ingresos — próximo trimestre</div>
                    <div style="font-family:Courier New,monospace;color:#666;font-size:11px;margin-bottom:10px;">
                        Rango de estimaciones de facturación esperada (en millones de dólares)
                    </div>
                """
                for lbl, val in [("Estimación Alta (optimista)", rev_hi), ("Estimación Media (consenso)", rev_avg), ("Estimación Baja (pesimista)", rev_lo)]:
                    if val is not None:
                        color = "#00ffad" if lbl == "Estimación Media (consenso)" else "#aaa"
                        est_html += f'<div class="estimate-row"><span class="estimate-key">{lbl}</span><span class="estimate-val" style="color:{color};">{format_financial_value(val)}</span></div>'
                est_html += "</div>"

            if est_html:
                st.markdown(f"""
                <div class="mod-box">
                    <div class="mod-header">
                        <span class="mod-title">🔮 Estimaciones de Analistas — Próximos Resultados</span>
                        <div class="tip-box"><div class="tip-icon">?</div>
                            <div class="tip-text">Consenso de analistas de Wall Street sobre BPA e ingresos esperados para el próximo trimestre. Si la empresa supera la estimación media es una "earnings surprise" positiva y suele mover el precio al alza.</div>
                        </div>
                    </div>
                    <div class="mod-body">{est_html}</div>
                </div>
                """, unsafe_allow_html=True)

    # ══ TAB 6: FONDOS INSTITUCIONALES (13F) ══
    with tabs[5]:
        st.markdown("""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">🏦 Fondos Institucionales — Declaraciones 13F (SEC)</span>
                <div class="tip-box"><div class="tip-icon">?</div>
                    <div class="tip-text">Datos reales de declaraciones trimestrales obligatorias a la SEC (formulario 13F). Muestra qué fondos institucionales tienen posición en esta empresa y cuántas acciones declararon. Fuente: Yahoo Finance / SEC EDGAR.</div>
                </div>
            </div>
            <div class="mod-body">
        """, unsafe_allow_html=True)

        with st.spinner("[ CARGANDO DATOS 13F ... ]"):
            holders_data = get_institutional_holders_sec(t_in)

        if holders_data:
            major = holders_data.get('major')
            inst  = holders_data.get('institutional')
            mf    = holders_data.get('mutual_funds')

            # Major holders resumen
            if major is not None and not major.empty:
                try:
                    pct_inst   = major.iloc[2, 0] if len(major) > 2 else "N/D"
                    pct_retail = major.iloc[3, 0] if len(major) > 3 else "N/D"
                    if isinstance(pct_inst, float):   pct_inst   = f"{pct_inst*100:.1f}%"
                    if isinstance(pct_retail, float): pct_retail = f"{pct_retail*100:.1f}%"
                    st.markdown(f"""
                    <div style="display:flex;gap:12px;margin-bottom:18px;">
                        <div style="flex:1;background:#0a0c10;border:1px solid #1a1e26;border-radius:8px;padding:16px;text-align:center;">
                            <div style="font-family:VT323,monospace;color:#777;font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">% en manos institucionales</div>
                            <div style="font-family:VT323,monospace;color:#00ffad;font-size:2rem;">{pct_inst}</div>
                        </div>
                        <div style="flex:1;background:#0a0c10;border:1px solid #1a1e26;border-radius:8px;padding:16px;text-align:center;">
                            <div style="font-family:VT323,monospace;color:#777;font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">% en manos retail</div>
                            <div style="font-family:VT323,monospace;color:#00d9ff;font-size:2rem;">{pct_retail}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception:
                    pass

            # Top holders institucionales
            if inst is not None and not inst.empty:
                st.markdown("""
                <div style="font-family:VT323,monospace;color:#00ffad;font-size:1rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;">
                    🏛 Top Tenedores Institucionales (Fondos, ETFs, Gestoras)
                </div>
                <div style="font-family:Courier New,monospace;color:#555;font-size:11px;margin-bottom:14px;">
                    Declaraciones 13F presentadas a la SEC. Datos del último trimestre disponible.
                </div>
                """, unsafe_allow_html=True)

                # Renombrar columnas al castellano
                col_map = {
                    'Holder': 'Institución', 'Shares': 'Acciones',
                    'Date Reported': 'Fecha Declarada', '% Out': '% del Float',
                    'Value': 'Valor (USD)'
                }
                inst_display = inst.rename(columns=col_map).head(15)

                # Formatear columna de valor
                if 'Valor (USD)' in inst_display.columns:
                    inst_display['Valor (USD)'] = inst_display['Valor (USD)'].apply(
                        lambda x: format_financial_value(x) if _safe(x) else "N/A"
                    )
                if 'Acciones' in inst_display.columns:
                    inst_display['Acciones'] = inst_display['Acciones'].apply(
                        lambda x: f"{int(x):,}" if _safe(x) else "N/A"
                    )

                st.markdown('<div style="border:1px solid #00ffad1a;border-radius:8px;overflow:hidden;padding:12px;background:#0a0c10;margin-bottom:18px;">', unsafe_allow_html=True)
                st.dataframe(inst_display, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Fondos de inversión
            if mf is not None and not mf.empty:
                st.markdown("""
                <div style="font-family:VT323,monospace;color:#00d9ff;font-size:1rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;">
                    📦 Top Fondos de Inversión (Mutual Funds)
                </div>
                """, unsafe_allow_html=True)
                mf_col_map = {
                    'Holder': 'Fondo', 'Shares': 'Acciones',
                    'Date Reported': 'Fecha', '% Out': '% del Float', 'Value': 'Valor (USD)'
                }
                mf_display = mf.rename(columns=mf_col_map).head(10)
                if 'Valor (USD)' in mf_display.columns:
                    mf_display['Valor (USD)'] = mf_display['Valor (USD)'].apply(
                        lambda x: format_financial_value(x) if _safe(x) else "N/A"
                    )
                if 'Acciones' in mf_display.columns:
                    mf_display['Acciones'] = mf_display['Acciones'].apply(
                        lambda x: f"{int(x):,}" if _safe(x) else "N/A"
                    )
                st.markdown('<div style="border:1px solid #00ffad1a;border-radius:8px;overflow:hidden;padding:12px;background:#0a0c10;margin-bottom:18px;">', unsafe_allow_html=True)
                st.dataframe(mf_display, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

            if (inst is None or inst.empty) and (mf is None or mf.empty):
                st.info("No se encontraron datos de tenedores institucionales para este ticker.")

        else:
            st.info("No se pudieron obtener datos 13F para este ticker.")

        st.markdown("""
        <div style="font-family:Courier New,monospace;color:#333;font-size:11px;margin-top:12px;padding-top:12px;border-top:1px solid #111520;">
            ⚠️ Fuente: SEC EDGAR vía Yahoo Finance. Los datos 13F son declaraciones trimestrales con rezago de hasta 45 días.
            No reflejan posiciones actuales en tiempo real. Para pitches narrativos de hedge funds consultar plataformas
            de pago como WhaleWisdom, Tikr o publicaciones directas de los fondos.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════
    # SUGERENCIAS DE INVERSIÓN
    # ══════════════════════════════════════════════
    st.markdown("<hr>", unsafe_allow_html=True)

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
                <div class="tip-text">Análisis automatizado con datos reales de Yahoo Finance. No constituye asesoramiento financiero.</div>
            </div>
        </div>
        <div class="mod-body">{sug_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════
    # RSU AI — PROMPT INYECTADO + SALIDA MARKDOWN
    # ══════════════════════════════════════════════
    st.markdown("""
    <div class="rsu-box">
        <div class="rsu-title">🤖 RSU Artificial Intelligence</div>
        <p style="font-family:'Courier New',monospace;color:#666;font-size:13px;line-height:1.6;margin-bottom:16px;">
            Análisis completo de 11 secciones: empresa, fundamentales, técnico, smart money, catalizadores y perspectivas.
            Datos en tiempo real. Respuesta estructurada en markdown.
        </p>
    """, unsafe_allow_html=True)

    if st.button("✨ GENERAR INFORME IA (PROMPT RSU)", key="rsu_button"):
        model_ia, modelo_nombre, error_ia = get_ia_model()
        if error_ia:
            st.error(f"❌ Error al conectar con el modelo IA: {error_ia}")
        else:
            with st.spinner(f"[ ANALIZANDO {t_in} CON IA ... ]"):
                try:
                    # Inyectar ticker y datos cuantitativos en el prompt
                    prompt_con_ticker = PROMPT_RSU.replace("{t}", t_in)
                    prompt_final = prompt_con_ticker + f"""

---
**INSTRUCCIÓN ADICIONAL: Responde siempre en castellano.**

**Datos cuantitativos actuales para contextualizar el análisis** (fuente: Yahoo Finance, tiempo real):

| Métrica | Valor |
|---|---|
| Precio actual | ${current_price:,.2f} |
| Market Cap | {format_financial_value(market_cap)} |
| P/E Trailing | {fmt_x(metrics['trailing_pe'])} |
| Forward P/E | {fmt_x(metrics['forward_pe'])} |
| PEG Ratio | {fmt_x(metrics['peg_ratio'])} |
| EV/EBITDA | {fmt_x(metrics['ev_ebitda'])} |
| P/S (TTM) | {fmt_x(metrics['price_to_sales'])} |
| ROE | {fmt_pct(profitability.get('roe'), 100)} |
| ROA | {fmt_pct(profitability.get('roa'), 100)} |
| Margen Neto | {fmt_pct(profitability.get('net_margin'), 100)} |
| Margen Operativo | {fmt_pct(profitability.get('op_margin'), 100)} |
| Crec. Ingresos YoY | {fmt_pct(profitability.get('revenue_growth'), 100)} |
| Crec. Beneficios YoY | {fmt_pct(profitability.get('earnings_growth'), 100)} |
| Deuda/Capital | {fmt_pct(profitability.get('debt_to_equity'), 1)} |
| Free Cash Flow | {format_financial_value(profitability.get('free_cashflow'))} |
| Precio objetivo medio | {"$"+str(round(target_data['mean'],2)) if target_data.get('mean') else 'N/A'} |
| Potencial alcista | {(str(round(target_data['upside'],1))+"%") if target_data.get('upside') else 'N/A'} |
| Sector | {info.get('sector', 'N/A')} |
| País | {info.get('country', 'N/A')} |
"""
                    res = model_ia.generate_content(prompt_final)
                    report_text = res.text

                    st.session_state['last_report']        = report_text
                    st.session_state['last_report_ticker'] = t_in

                except Exception as e:
                    st.error(f"❌ Error generando el informe: {e}")
                    report_text = None

    st.markdown("</div>", unsafe_allow_html=True)

    # Mostrar el informe en markdown nativo de Streamlit (con estilos RSU)
    if st.session_state.get('last_report') and st.session_state.get('last_report_ticker') == t_in:
        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">📋 Informe RSU — {t_in}</span>
                <div class="tip-box"><div class="tip-icon">?</div>
                    <div class="tip-text">Informe generado por IA con 11 secciones de análisis. Basado en datos reales y análisis en tiempo real del modelo Gemini.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.container():
            st.markdown(
                '<div style="border:1px solid #00ffad1a;border-top:none;border-radius:0 0 8px 8px;'
                'padding:24px;background:#0a0c10;margin-bottom:18px;">',
                unsafe_allow_html=True
            )
            # Renderizado markdown nativo — tablas, headers, bold, etc.
            st.markdown(st.session_state['last_report'])
            st.markdown('</div>', unsafe_allow_html=True)

        # Descarga
        col_dl, col_empty = st.columns([1, 3])
        with col_dl:
            st.download_button(
                label="⬇️ DESCARGAR INFORME (.md)",
                data=st.session_state['last_report'].encode('utf-8'),
                file_name=f"RSU_AI_Report_{t_in}.md",
                mime="text/markdown",
                key="download_report"
            )

    # FOOTER
    st.markdown("""
    <div style="text-align:center;margin-top:40px;padding:20px;border-top:1px solid #0f1218;">
        <div style="font-family:'VT323',monospace;color:#222;font-size:0.82rem;letter-spacing:2px;">
            [END OF REPORT // RSU_AI_REPORT_v4.0]<br>
            [DATA SOURCE: YAHOO FINANCE · SEC EDGAR · TRADINGVIEW · GEMINI AI]<br>
            [STATUS: ACTIVE]
        </div>
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────
if __name__ == "__main__":
    render()





