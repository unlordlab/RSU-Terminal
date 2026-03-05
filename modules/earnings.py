# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from config import get_ia_model
import time
import requests
import math
import html
import traceback

# ────────────────────────────────────────────────
# API KEYS
# ────────────────────────────────────────────────

def get_api_keys():
    return {
        'alpha_vantage': st.secrets.get("ALPHA_VANTAGE_API_KEY", ""),
        'finnhub':       st.secrets.get("FINNHUB_API_KEY", ""),
    }

# ────────────────────────────────────────────────
# HELPERS NUMÉRICOS
# ────────────────────────────────────────────────

def _safe(val):
    if val is None: return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)): return None
    return val

def safe_float(value):
    if value is None or value == '' or value == 'None' or value == 'N/A': return 0.0
    try: return float(value)
    except: return 0.0

def safe_int(value):
    if value is None or value == '' or value == 'None' or value == 'N/A': return 0
    try: return int(float(value))
    except: return 0

def format_value(value, prefix="", suffix="", decimals=2):
    if value is None or value == 0 or (isinstance(value, float) and pd.isna(value)):
        return "N/D"
    try:
        val = float(value)
        if abs(val) >= 1e12: return f"{prefix}{val/1e12:.{decimals}f}T{suffix}"
        elif abs(val) >= 1e9: return f"{prefix}{val/1e9:.{decimals}f}B{suffix}"
        elif abs(val) >= 1e6: return f"{prefix}{val/1e6:.{decimals}f}M{suffix}"
        elif abs(val) >= 1e3: return f"{prefix}{val/1e3:.{decimals}f}K{suffix}"
        return f"{prefix}{val:.{decimals}f}{suffix}"
    except: return str(value)

def fmt_x(val):
    v = _safe(val)
    return f"{v:.2f}×" if v is not None else "N/D"

def fmt_pct(val, mult=1):
    v = _safe(val)
    return f"{v * mult:.2f}%" if v is not None else "N/D"

def ts_to_date(ts):
    try: return datetime.fromtimestamp(int(ts)).strftime('%d %b %Y')
    except: return str(ts)

def format_pct(value, decimals=2):
    if value is None or (isinstance(value, float) and pd.isna(value)): return "N/D", "#888"
    try:
        val = float(value) * 100 if abs(float(value)) < 1 else float(value)
        color = "#00ffad" if val >= 0 else "#f23645"
        return f"{val:.{decimals}f}%", color
    except: return "N/D", "#888"

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
# TRADUCCIÓN AUTOMÁTICA (castellano)
# ────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner=False)  # 24h — la descripción no cambia a diario
def translate_text_cached(text, ticker):
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
    except:
        return text

# ────────────────────────────────────────────────
# YFINANCE — DATOS PRINCIPALES (cacheado)
# ────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_yfinance_full(ticker):
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info
        cp_check = (
            _safe(info.get('currentPrice')) or
            _safe(info.get('regularMarketPrice')) or
            _safe(info.get('regularMarketOpen')) or
            _safe(info.get('ask')) or
            _safe(info.get('bid')) or
            _safe(info.get('navPrice'))
        )
        if not info or not cp_check:
            return None

        # Recomendaciones
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
                recommendations = {'strong_buy': sb, 'buy': b, 'hold': h,
                                   'sell': s, 'strong_sell': ss, 'total': sb+b+h+s+ss}
        except: pass

        rec_summary = None
        try:
            rs = stock.recommendations_summary
            if rs is not None and not rs.empty:
                rec_summary = rs.head(6)
        except: pass

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
            'price_to_book':  _safe(info.get('priceToBook')),
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
            'operating_cashflow': _safe(info.get('operatingCashflow')),
            'revenue_ttm':     _safe(info.get('totalRevenue')),
            'ebitda':          _safe(info.get('ebitda')),
            'total_cash':      _safe(info.get('totalCash')),
            'total_debt':      _safe(info.get('totalDebt')),
        }

        # Datos de mercado
        market = {
            'price':           cp,
            'prev_close':      _safe(info.get('previousClose')),
            'market_cap':      _safe(info.get('marketCap')),
            'volume':          _safe(info.get('volume')),
            'avg_volume':      _safe(info.get('averageVolume')),
            'beta':            _safe(info.get('beta')),
            '52w_high':        _safe(info.get('fiftyTwoWeekHigh')),
            '52w_low':         _safe(info.get('fiftyTwoWeekLow')),
            'eps':             _safe(info.get('trailingEps')),
            'eps_forward':     _safe(info.get('forwardEps')),
            'dividend_yield':  _safe(info.get('dividendYield')),
            'dividend_rate':   _safe(info.get('dividendRate')),
            'payout_ratio':    _safe(info.get('payoutRatio')),
            'sma_50':          _safe(info.get('fiftyDayAverage')),
            'sma_200':         _safe(info.get('twoHundredDayAverage')),
            'short_ratio':     _safe(info.get('shortRatio')),
            'insider_pct':     _safe(info.get('heldPercentInsiders')),
            'inst_pct':        _safe(info.get('heldPercentInstitutions')),
            'n_analysts':      _safe(info.get('numberOfAnalystOpinions')),
            'book_value':      _safe(info.get('bookValue')),
            'employees':       _safe(info.get('fullTimeEmployees')),
        }

        # Eventos calendario + estimaciones — una sola llamada
        events = {}
        analyst_estimates = {}
        try:
            cal = stock.calendar
            if cal is not None:
                raw = cal if isinstance(cal, dict) else cal.to_dict()
                useful_events = {'Earnings Date', 'Ex-Dividend Date', 'Dividend Date'}
                estimate_keys = {'Earnings High', 'Earnings Low', 'Earnings Average',
                                 'Revenue High',  'Revenue Low',  'Revenue Average'}
                for k, v in raw.items():
                    if v is None: continue
                    if k in useful_events:   events[k]            = v
                    elif k in estimate_keys: analyst_estimates[k] = v
        except: pass

        # Complementar fechas dividendo desde info si calendar no las devuelve
        for k_info, label in [
            ('exDividendDate', 'Fecha Ex-Dividendo'),
            ('dividendDate',   'Fecha Pago Dividendo')
        ]:
            if label not in events and 'Ex-Dividend Date' not in events:
                v = _safe(info.get(k_info))
                if v: events[label] = v

        # Sparkline 3 meses — reutiliza la sesión stock, sin llamada extra
        sparkline = None
        try:
            hist = stock.history(period="3mo", interval="1d", auto_adjust=True)
            if hist is not None and not hist.empty and 'Close' in hist.columns:
                sparkline = [p for p in [_safe(x) for x in hist['Close'].dropna().tolist()] if p is not None]
        except: pass

        # Histórico 1 año para gráfico
        hist_1y = None
        try:
            h = stock.history(period="1y", auto_adjust=True)
            if not h.empty:
                hist_1y = h
        except: pass

        # Earnings surprises
        earnings_surprises = []
        try:
            eq = stock.earnings_history
            if eq is not None and not eq.empty:
                for _, row in eq.head(8).iterrows():
                    eps_actual   = _safe(row.get('epsActual'))
                    eps_estimate = _safe(row.get('epsEstimate'))
                    if eps_actual is None and eps_estimate is None:
                        continue
                    surprise = (eps_actual - eps_estimate) if (eps_actual and eps_estimate) else None
                    surprise_pct = (surprise / abs(eps_estimate) * 100) if (surprise and eps_estimate and eps_estimate != 0) else None
                    date_val = row.name if hasattr(row, 'name') else ''
                    earnings_surprises.append({
                        'date': str(date_val)[:10] if date_val else 'N/D',
                        'eps_actual':   eps_actual   or 0,
                        'eps_estimate': eps_estimate or 0,
                        'surprise':     surprise     or 0,
                        'surprise_pct': surprise_pct or 0,
                    })
        except: pass

        # Institutional holders — same session, no extra call
        inst_data = {}
        try:
            inst_data['institutional'] = stock.institutional_holders
            inst_data['major']         = stock.major_holders
            inst_data['mutual_funds']  = stock.mutualfund_holders
        except: pass

        return {
            'info': info, 'recommendations': recommendations, 'rec_summary': rec_summary,
            'target_data': target_data, 'metrics': metrics, 'profitability': profitability,
            'market': market, 'events': events, 'analyst_estimates': analyst_estimates,
            'sparkline': sparkline, 'hist_1y': hist_1y,
            'earnings_surprises': earnings_surprises,
            'inst_data': inst_data,
        }
    except Exception as e:
        return None

# ────────────────────────────────────────────────
# ALPHA VANTAGE — EARNINGS HISTORY (complementario)
# ────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_alpha_vantage_earnings(ticker, api_key):
    if not api_key: return None
    try:
        resp = requests.get(
            "https://www.alphavantage.co/query",
            params={'function': 'EARNINGS', 'symbol': ticker, 'apikey': api_key},
            timeout=20
        )
        if resp.status_code == 200:
            data = resp.json()
            if 'Note' in data or 'Information' in data or not data.get('quarterlyEarnings'):
                return None
            surprises = []
            for r in data['quarterlyEarnings'][:8]:
                ea  = safe_float(r.get('reportedEPS'))
                ee  = safe_float(r.get('estimatedEPS'))
                sur = safe_float(r.get('surprise'))
                pct = safe_float(r.get('surprisePercentage'))
                if ea != 0 or ee != 0:
                    surprises.append({
                        'date': r.get('fiscalDateEnding', 'N/D'),
                        'eps_actual': ea, 'eps_estimate': ee,
                        'surprise': sur, 'surprise_pct': pct,
                    })
            return surprises if surprises else None
    except:
        return None

# ────────────────────────────────────────────────
# FINNHUB — SEGMENTOS Y SENTIMIENTO
# ────────────────────────────────────────────────

@st.cache_data(ttl=900, show_spinner=False)
def get_finnhub_data(ticker, api_key):
    if not api_key: return None
    base_url = "https://finnhub.io/api/v1"
    headers  = {"X-Finnhub-Token": api_key}
    result   = {}
    try:
        for key, params in [
            ('revenue_breakdown', {'symbol': ticker}),
            ('geographic_revenue', {'symbol': ticker, 'breakdown': 'geographic'}),
        ]:
            r = requests.get(f"{base_url}/stock/revenue-breakdown",
                             params=params, headers=headers, timeout=10)
            result[key] = r.json() if r.status_code == 200 else {}
            time.sleep(0.3)

        to_date   = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        r = requests.get(f"{base_url}/company-news",
                         params={'symbol': ticker, 'from': from_date, 'to': to_date},
                         headers=headers, timeout=10)
        result['news'] = r.json() if r.status_code == 200 else []

        result['source'] = 'finnhub'
        return result
    except:
        return None

def process_finnhub_segments(finnhub_data):
    if not finnhub_data: return None
    segments = {}
    for key in ['revenue_breakdown', 'geographic_revenue']:
        bd = finnhub_data.get(key, {})
        if bd and 'data' in bd:
            for item in bd['data']:
                name = item.get('segment') or item.get('region', 'Desconocido')
                rev  = item.get('revenue', 0)
                if rev > 0: segments[name] = rev
            if segments: break
    return segments if segments else None

def calculate_news_sentiment(finnhub_data):
    if not finnhub_data or 'news' not in finnhub_data: return None
    news = finnhub_data['news']
    if not news: return None

    bullish_words = ['beat','strong','growth','profit','gain','rise','surge','upgrade',
                     'buy','outperform','exceeds','beats','record','soar','rally','deal','expansion']
    bearish_words = ['miss','weak','loss','decline','fall','drop','downgrade','sell',
                     'cut','underperform','misses','plunge','crash','concern','risk',
                     'investigation','lawsuit','layoff','recession','bankruptcy','fraud']

    bullish_count = bearish_count = total = 0
    for article in news[:30]:
        title = article.get('headline', '').lower()
        if not title: continue
        total += 1
        if any(w in title for w in bullish_words): bullish_count += 1
        if any(w in title for w in bearish_words): bearish_count += 1

    ts = bullish_count + bearish_count
    if ts == 0:
        return {'overall_sentiment': 'neutral', 'sentiment_score': 0,
                'news_count': len(news), 'bullish_pct': 0, 'bearish_pct': 0,
                'analyzed_count': total, 'source': 'finnhub'}

    bullish_pct = bullish_count / ts * 100
    bearish_pct = bearish_count / ts * 100

    if bullish_pct > 60:
        sentiment, score = 'alcista', 0.5 + (bullish_pct - 60) / 80
    elif bearish_pct > 60:
        sentiment, score = 'bajista', -0.5 - (bearish_pct - 60) / 80
    else:
        sentiment, score = 'neutral', (bullish_pct - bearish_pct) / 100

    return {
        'overall_sentiment': sentiment, 'sentiment_score': max(-1, min(1, score)),
        'news_count': len(news), 'bullish_pct': round(bullish_pct, 1),
        'bearish_pct': round(bearish_pct, 1), 'analyzed_count': total, 'source': 'finnhub'
    }

# ────────────────────────────────────────────────
# TENEDORES INSTITUCIONALES (13F)
# ────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def get_institutional_holders(ticker):
    try:
        stock = yf.Ticker(ticker)
        return {
            'institutional': stock.institutional_holders,
            'major':         stock.major_holders,
            'mutual_funds':  stock.mutualfund_holders,
        }
    except:
        return None

# ────────────────────────────────────────────────
# SUGERENCIAS AUTOMÁTICAS
# ────────────────────────────────────────────────

def get_suggestions(info, recommendations, target_data, profitability):
    suggestions = []

    pe         = _safe(info.get('trailingPE'))
    forward_pe = _safe(info.get('forwardPE'))
    cp         = target_data.get('current', 0) or 0
    n_analysts = _safe(info.get('numberOfAnalystOpinions')) or 0

    if pe and forward_pe and pe > 0 and forward_pe > 0:
        if forward_pe < pe * 0.85:
            suggestions.append(f"📈 Forward P/E ({forward_pe:.2f}×) muy inferior al P/E actual ({pe:.2f}×) — fuerte crecimiento de beneficios esperado.")
        elif forward_pe < pe:
            suggestions.append(f"📈 Forward P/E ({forward_pe:.2f}×) inferior al P/E actual ({pe:.2f}×) — crecimiento de beneficios esperado.")
        else:
            suggestions.append(f"⚠️ Forward P/E ({forward_pe:.2f}×) superior al P/E actual ({pe:.2f}×) — posible contracción de márgenes.")

    if recommendations and recommendations['total'] > 0:
        tot     = recommendations['total']
        buy_pct = ((recommendations['strong_buy'] + recommendations['buy']) / tot) * 100
        n_buy   = recommendations['strong_buy'] + recommendations['buy']
        if buy_pct >= 75:
            suggestions.append(f"✅ Fuerte consenso alcista: {n_buy} de {tot} analistas recomiendan comprar ({buy_pct:.0f}%).")
        elif buy_pct >= 50:
            suggestions.append(f"⚖️ Consenso mayoritariamente alcista: {buy_pct:.0f}% de {tot} analistas recomiendan comprar.")
        elif buy_pct <= 30:
            suggestions.append(f"🔴 Consenso débil: solo {buy_pct:.0f}% de {tot} analistas recomiendan comprar.")
        else:
            suggestions.append(f"⚖️ Consenso neutral entre {tot} analistas ({buy_pct:.0f}% favorables).")

    if target_data.get('mean') and cp:
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

    rg = profitability.get('revenue_growth')
    if rg is not None:
        if rg > 0.25:   suggestions.append(f"🚀 Crecimiento de ingresos excepcional: +{rg*100:.1f}% interanual.")
        elif rg > 0.10: suggestions.append(f"📈 Crecimiento de ingresos sólido: +{rg*100:.1f}% interanual.")
        elif rg > 0:    suggestions.append(f"📊 Crecimiento de ingresos modesto: +{rg*100:.1f}% interanual.")
        else:           suggestions.append(f"📉 Ingresos en contracción: {rg*100:.1f}% interanual.")

    roe = profitability.get('roe')
    if roe is not None:
        if roe > 0.30:  suggestions.append(f"💎 ROE excepcional ({roe*100:.1f}%) — empresa muy eficiente en generar beneficios con el capital.")
        elif roe > 0.15: suggestions.append(f"💚 ROE sólido ({roe*100:.1f}%) — buena rentabilidad sobre fondos propios.")
        elif roe < 0:   suggestions.append(f"🔴 ROE negativo ({roe*100:.1f}%) — empresa destruyendo valor actualmente.")

    nm = profitability.get('net_margin')
    if nm is not None:
        if nm > 0.25:   suggestions.append(f"💰 Margen neto excepcional ({nm*100:.1f}%) — negocio altamente rentable.")
        elif nm > 0.10: suggestions.append(f"✅ Margen neto sólido ({nm*100:.1f}%).")
        elif nm < 0:    suggestions.append(f"🔴 Margen neto negativo ({nm*100:.1f}%) — empresa en pérdidas.")

    de = profitability.get('debt_to_equity')
    if de is not None:
        if de > 150:   suggestions.append(f"💳 Endeudamiento muy elevado (D/E: {de:.0f}%) — riesgo financiero alto.")
        elif de > 80:  suggestions.append(f"⚠️ Endeudamiento moderado-alto (D/E: {de:.0f}%). Vigilar cobertura de intereses.")
        elif de < 30:  suggestions.append(f"💪 Balance conservador (D/E: {de:.0f}%) — solidez financiera.")

    fcf = profitability.get('free_cashflow')
    if fcf is not None:
        if fcf > 0: suggestions.append(f"💵 Free Cash Flow positivo ({format_value(fcf, '$')}) — empresa genera caja real.")
        else:       suggestions.append(f"⚠️ Free Cash Flow negativo ({format_value(fcf, '$')}) — empresa consume caja.")

    dy = _safe(info.get('dividendYield'))
    dr = _safe(info.get('dividendRate'))
    if dy and dy > 0 and dr:
        suggestions.append(f"💰 Dividendo anual: ${dr:.2f}/acción (yield {dy*100:.2f}%) — fuente de rentabilidad adicional.")

    peg = _safe(info.get('pegRatio'))
    if peg and peg > 0:
        if peg < 1:    suggestions.append(f"🟢 PEG Ratio {peg:.2f} — potencialmente infravalorada respecto a su crecimiento.")
        elif peg > 3:  suggestions.append(f"🔴 PEG Ratio {peg:.2f} — valoración muy exigente respecto al crecimiento esperado.")

    return suggestions if suggestions else ["ℹ️ Datos insuficientes para generar sugerencias específicas."]

# ────────────────────────────────────────────────
# PROMPT IA
# ────────────────────────────────────────────────

PROMPT_RSU_COMPLETO = """Por favor, analiza {t} para mí y proporciona lo siguiente, de forma concisa, estructurada y claramente organizada en **formato markdown**:

---

## 1. Explica a qué se dedica la empresa como si tuviera 12 años

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

---
**DATOS CUANTITATIVOS ACTUALES (Yahoo Finance):**
{datos_cuantitativos}

Mantén el estilo claro, profesional, directo y orientado a la toma de decisiones de inversión. Responde siempre en castellano."""

PROMPT_RSU_RAPIDO = """Analiza {t} y proporciona en castellano:

1. **SNAPSHOT**: Qué hace, precio actual, capitalización
2. **VALORACIÓN**: P/E, PEG, P/S — ¿cara o barata?
3. **CALIDAD**: Márgenes, ROE, FCF — ¿negocio de calidad?
4. **CATALIZADORES**: 3 razones para subir, 3 riesgos
5. **VEREDICTO**: Score /10, recomendación (comprar/mantener/vender), target price

**DATOS:**
{datos_cuantitativos}

Responde en castellano. Breve y directo."""

# ────────────────────────────────────────────────
# CSS GLOBAL
# ────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp { background: #0c0e12; }
        .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 100%; }

        /* VT323 headings */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            color: #00ffad !important;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        h1 { font-size: 3.5rem !important; text-shadow: 0 0 20px #00ffad66; border-bottom: 2px solid #00ffad; padding-bottom: 15px; }
        h2 { font-size: 2.2rem !important; color: #00d9ff !important; border-left: 4px solid #00ffad; padding-left: 15px; margin-top: 30px !important; }
        h3 { font-size: 1.8rem !important; color: #ff9800 !important; }

        /* Body */
        p, li { font-family: 'Courier New', monospace; color: #ccc !important; line-height: 1.8; font-size: 0.92rem; }
        strong { color: #00ffad; }

        /* VT labels */
        .vt-label { font-family: 'VT323', monospace; color: #666; font-size: 0.9rem; letter-spacing: 2px; }
        .landing-title { font-family: 'VT323', monospace; font-size: 5rem; color: #00ffad; text-shadow: 0 0 30px #00ffad55; border-bottom: 2px solid #00ffad33; padding-bottom: 10px; letter-spacing: 4px; }
        .landing-desc  { font-family: 'VT323', monospace; font-size: 1.2rem; color: #00d9ff; letter-spacing: 3px; }

        /* INPUT */
        .stTextInput > div > div > input {
            background: #0c0e12 !important; border: 1px solid #00ffad33 !important;
            border-radius: 6px !important; color: #00ffad !important;
            font-family: 'VT323', monospace !important; font-size: 1.6rem !important;
            text-align: center; letter-spacing: 4px; padding: 12px !important;
        }
        .stTextInput > div > div > input:focus { border-color: #00ffad !important; box-shadow: 0 0 10px #00ffad22 !important; }
        .stTextInput label { font-family: 'VT323', monospace !important; color: #888 !important; font-size: 1rem !important; letter-spacing: 2px; }

        /* BOTONES */
        .stButton > button {
            background: linear-gradient(90deg, #00ffad, #00cc8a) !important;
            color: #000 !important; border: none !important; border-radius: 6px !important;
            font-family: 'VT323', monospace !important; font-size: 1.4rem !important;
            letter-spacing: 3px !important; padding: 12px 28px !important;
            text-transform: uppercase !important; width: 100% !important;
        }
        .stButton > button:hover { box-shadow: 0 0 20px #00ffad44 !important; }
        .stDownloadButton > button {
            background: #0c0e12 !important; color: #00ffad !important;
            border: 1px solid #00ffad33 !important; border-radius: 6px !important;
            font-family: 'VT323', monospace !important; font-size: 1rem !important;
            letter-spacing: 2px !important; padding: 8px 20px !important;
            text-transform: uppercase !important; width: auto !important;
        }

        /* MÓDULOS */
        .mod-box     { background: linear-gradient(135deg, #0c0e12 0%, #111520 100%); border: 1px solid #00ffad1a; border-radius: 8px; overflow: hidden; margin-bottom: 18px; box-shadow: 0 2px 20px #00000040; }
        .mod-header  { background: #0a0c10; padding: 12px 18px; border-bottom: 1px solid #00ffad1a; display: flex; justify-content: space-between; align-items: center; }
        .mod-title   { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.2rem; letter-spacing: 2px; text-transform: uppercase; margin: 0; }
        .mod-body    { padding: 18px; }

        /* TICKER HEADER */
        .ticker-box    { background: linear-gradient(135deg, #0a0c10 0%, #111520 100%); border: 1px solid #00ffad22; border-radius: 8px; padding: 18px 24px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 30px #00ffad08; }
        .ticker-name   { font-family: 'VT323', monospace; font-size: 2.4rem; color: #00ffad; letter-spacing: 3px; text-shadow: 0 0 10px #00ffad33; }
        .ticker-meta   { font-family: 'Courier New', monospace; font-size: 11px; color: #555; margin-top: 4px; }
        .ticker-price  { font-family: 'VT323', monospace; font-size: 2.6rem; color: #fff; text-align: right; }
        .ticker-change { font-family: 'VT323', monospace; font-size: 1.2rem; text-align: right; }

        /* MÉTRICAS */
        .metric-box   { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 16px; position: relative; height: 120px; box-sizing: border-box; }
        .metric-tag   { position: absolute; top: 8px; right: 8px; background: #0f1e35; color: #00d9ff; padding: 1px 6px; border-radius: 4px; font-family: 'VT323', monospace; font-size: 0.8rem; letter-spacing: 1px; }
        .metric-label { font-family: 'VT323', monospace; color: #777; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .metric-value { font-family: 'VT323', monospace; font-size: 1.8rem; letter-spacing: 1px; }
        .metric-desc  { font-family: 'Courier New', monospace; color: #444; font-size: 10px; margin-top: 2px; }

        /* PROFIT BOX */
        .profit-box   { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 14px 16px; }
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
        .target-price { font-family: 'VT323', monospace; font-size: 3.2rem; color: #00ffad; text-shadow: 0 0 12px #00ffad33; }
        .target-label { font-family: 'VT323', monospace; color: #777; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }

        /* CONSENSUS */
        .consensus-box { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 24px; text-align: center; height: 100%; }

        /* EVENTOS */
        .event-row        { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #111520; }
        .event-row:last-child { border-bottom: none; }
        .event-label      { font-family: 'VT323', monospace; color: #888; font-size: 1rem; letter-spacing: 1px; }
        .event-value      { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.05rem; }

        /* FONDOS */
        .fund-card        { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 16px 18px; margin-bottom: 10px; }
        .fund-card:hover  { border-color: #00ffad44; }
        .fund-name        { font-family: 'VT323', monospace; color: #fff; font-size: 1.1rem; letter-spacing: 1px; }

        /* SUGERENCIAS */
        .suggestion-item { background: #0a0c10; border-left: 2px solid #00ffad; padding: 12px 16px; margin-bottom: 8px; border-radius: 0 6px 6px 0; font-family: 'Courier New', monospace; color: #ccc; font-size: 13px; line-height: 1.5; }

        /* RSU BOX */
        .rsu-box  { background: linear-gradient(135deg, #0a0c10 0%, #111520 100%); border: 1px solid #00ffad33; border-radius: 8px; padding: 24px; margin: 18px 0; }
        .rsu-title { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.5rem; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 10px; }

        /* ABOUT */
        .about-text { font-family: 'Courier New', monospace; color: #aaa; line-height: 1.8; font-size: 0.88rem; }

        /* HIGHLIGHT */
        .highlight-quote { background: #00ffad0a; border: 1px solid #00ffad22; border-radius: 8px; padding: 16px 20px; font-family: 'VT323', monospace; font-size: 1.2rem; color: #00ffad99; text-align: center; letter-spacing: 1px; margin: 16px 0; }

        /* TOOLTIP */
        .tip-box  { position: relative; cursor: help; z-index: 10; }
        .tip-icon { width: 20px; height: 20px; border-radius: 50%; background: #1a1e26; border: 1px solid #333; display: flex; align-items: center; justify-content: center; color: #666; font-size: 11px; font-weight: bold; }
        .tip-text { visibility: hidden; width: 260px; background: #111520; color: #bbb; text-align: left; padding: 12px; border-radius: 6px; position: fixed; z-index: 9999; opacity: 0; transition: opacity 0.2s; font-size: 11px; border: 1px solid #00ffad22; font-family: 'Courier New', monospace; box-shadow: 0 4px 24px #00000080; pointer-events: none; }
        .tip-box:hover .tip-text { visibility: visible; opacity: 1; }

        /* TABS */
        .stTabs [data-baseweb="tab-list"]  { gap: 4px; background: #0a0c10; padding: 8px; border-radius: 8px; border: 1px solid #00ffad1a; margin-bottom: 16px; }
        .stTabs [data-baseweb="tab"]        { background: transparent; color: #555; border-radius: 6px; padding: 8px 14px; font-family: 'VT323', monospace; font-size: 0.9rem; letter-spacing: 1px; text-transform: uppercase; }
        .stTabs [aria-selected="true"]      { background: #00ffad !important; color: #000 !important; }

        /* MISC */
        hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00ffad33, transparent); margin: 24px 0; }
        .hq { background: #00ffad0a; border: 1px solid #00ffad22; border-radius: 8px; padding: 16px 20px; font-family: 'VT323', monospace; font-size: 1.2rem; color: #00ffad99; text-align: center; letter-spacing: 1px; }

        /* Streamlit cleanups */
        [data-testid="stMetricValue"] { font-family: 'VT323', monospace; color: #00ffad; }
        div[data-testid="stVerticalBlock"] > div { margin-bottom: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    st.set_page_config(page_title="RSU Earnings", page_icon="📅", layout="wide",
                       initial_sidebar_state="collapsed")
    inject_css()

    # Session state
    for k, v in [('last_ticker', ''), ('last_report', ''), ('last_report_ticker', '')]:
        if k not in st.session_state:
            st.session_state[k] = v

    # HEADER
    st.markdown("""
    <div style="text-align:center; margin-bottom:28px;">
        <div class="vt-label" style="margin-bottom:10px;">[CONEXIÓN SEGURA ESTABLECIDA // RSU ANALYTICS v4.0]</div>
        <div class="landing-title">📅 RSU EARNINGS</div><br>
        <div class="landing-desc">ANÁLISIS DE RESULTADOS · FUNDAMENTALES · SORPRESAS · IA</div>
    </div>
    """, unsafe_allow_html=True)

    api_keys = get_api_keys()

    # INPUT
    _, col_c, _ = st.columns([1.5, 2, 1.5])
    with col_c:
        t_in = st.text_input(
            "Ticker",
            value=st.session_state['last_ticker'],
            placeholder="AAPL, NVDA, MSFT, IBE.MC…",
            label_visibility="collapsed"
        ).upper().strip()

    if not t_in:
        st.markdown("""
        <div style="text-align:center; margin-top:24px;">
            <div class="hq">▸ Introduce un ticker para iniciar el análisis de earnings ◂</div>
            <div style="margin-top:28px; font-family:'Courier New',monospace; color:#333; font-size:11px; letter-spacing:1px;">
                Datos: Yahoo Finance · Alpha Vantage · Finnhub · Gemini AI
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.session_state['last_ticker'] = t_in

    # CARGA DE DATOS
    with st.spinner(f"[ CARGANDO {t_in} ... ]"):
        yf_data      = get_yfinance_full(t_in)
        av_surprises = get_alpha_vantage_earnings(t_in, api_keys['alpha_vantage']) if api_keys['alpha_vantage'] else None
        finnhub_data = get_finnhub_data(t_in, api_keys['finnhub']) if api_keys['finnhub'] else None

    if not yf_data:
        st.error(f"❌ No se encontraron datos para **'{t_in}'**. Verifica que el ticker sea válido.")
        return

    info              = yf_data['info']
    recommendations   = yf_data['recommendations']
    rec_summary       = yf_data['rec_summary']
    target_data       = yf_data['target_data']
    metrics           = yf_data['metrics']
    profitability     = yf_data['profitability']
    market            = yf_data['market']
    events            = yf_data['events']
    analyst_estimates = yf_data['analyst_estimates']
    sparkline         = yf_data['sparkline']
    hist_1y           = yf_data['hist_1y']
    yf_surprises      = yf_data['earnings_surprises']
    inst_data_preload = yf_data.get('inst_data', {})

    # Usar sorpresas de AV si disponibles (más precisas), si no las de yfinance
    earnings_surprises = av_surprises if av_surprises else yf_surprises

    # Traduccción descripción
    translated_summary = translate_text_cached(info.get('longBusinessSummary', ''), t_in)

    # Segmentos y sentimiento de Finnhub
    segments  = process_finnhub_segments(finnhub_data) if finnhub_data else None
    sentiment = calculate_news_sentiment(finnhub_data) if finnhub_data else None

    # Cálculos header
    cp           = market.get('price') or 0
    prev_close   = market.get('prev_close') or cp
    price_change = ((cp - prev_close) / prev_close * 100) if prev_close else 0
    change_color = "#00ffad" if price_change >= 0 else "#f23645"
    change_arrow = "▲" if price_change >= 0 else "▼"
    market_cap   = market.get('market_cap') or 0
    spark_svg    = build_sparkline_svg(sparkline)

    # ── TICKER HEADER ──
    st.markdown(f"""
    <div class="ticker-box">
        <div>
            <div class="ticker-name">{info.get('shortName', t_in)}</div>
            <div class="ticker-meta">
                {info.get('sector', 'N/A')} &nbsp;·&nbsp; {info.get('industry', 'N/A')}
                &nbsp;·&nbsp; Cap: {format_value(market_cap, '$')}
                &nbsp;·&nbsp; {info.get('exchange', 'N/A')}
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:20px;">
            <div>{spark_svg}</div>
            <div>
                <div class="ticker-price">${cp:,.2f}</div>
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
        "studies":["RSI@tv-basicstudies","MASimple@tv-basicstudies","MACD@tv-basicstudies"]
    }});
    </script></body></html>"""

    st.markdown(f"""
    <div class="mod-box" style="margin-bottom:0;">
        <div class="mod-header">
            <span class="mod-title">📈 Gráfico Avanzado — {t_in}</span>
            <div class="tip-box">
                <div class="tip-icon">?</div>
                <div class="tip-text">Gráfico TradingView interactivo con RSI, Media Móvil y MACD. Puedes cambiar timeframe y añadir indicadores.</div>
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
        </div>
        <div class="mod-body"><p class="about-text">{html.escape(translated_summary)}</p></div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════
    # PESTAÑAS PRINCIPALES
    # ══════════════════════════════════════════════
    tabs = st.tabs([
        "📊 Valoración",
        "📈 Rentabilidad",
        "💰 Precio Objetivo",
        "📋 Recomendaciones",
        "🎯 Earnings Surprises",
        "📅 Eventos & Calendario",
        "🏦 Fondos Institucionales",
        "📰 Segmentos & Sentimiento",
    ])

    # ══ TAB 1: VALORACIÓN ══
    with tabs[0]:
        def valuation_color(name, val):
            v = _safe(val)
            if v is None: return "#888"
            if v < 0: return "#f23645"
            thresholds = {
                "P/E": (15, 30), "P/S": (2, 8), "EV/EBITDA": (10, 20),
                "Forward P/E": (12, 25), "PEG Ratio": (1, 2), "P/B": (1, 4),
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
            ("P/B",         metrics['price_to_book'],  "Actual",      "Precio / Valor en Libros"),
        ]

        rows_html = ""
        for i in range(0, len(valuation_data), 3):
            chunk = valuation_data[i:i+3]
            cells = "".join(
                f'<div style="flex:1;min-width:0;">'
                f'<div class="metric-box"><span class="metric-tag">{tag}</span>'
                f'<div class="metric-label">{label}</div>'
                f'<div class="metric-value" style="color:{valuation_color(label, val)};">{fmt_x(val)}</div>'
                f'<div class="metric-desc">{desc}</div>'
                f'</div></div>'
                for label, val, tag, desc in chunk
            )
            # Pad if fewer than 3
            while len(chunk) < 3:
                cells += '<div style="flex:1;min-width:0;"></div>'
                chunk.append(None)
            rows_html += f'<div style="display:flex;gap:10px;margin-bottom:10px;">{cells}</div>'

        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">💵 Múltiplos de Valoración</span>
                <div class="tip-box"><div class="tip-icon">?</div>
                    <div class="tip-text">Verde = barato · Naranja = valoración media · Rojo = caro. Umbrales estándar de análisis fundamental.</div>
                </div>
            </div>
            <div class="mod-body">{rows_html}</div>
        </div>
        """, unsafe_allow_html=True)

        # Métricas adicionales
        eps        = market.get('eps') or 0
        eps_fwd    = market.get('eps_forward') or 0
        beta       = market.get('beta') or 0
        book       = market.get('book_value') or 0
        hi52       = market.get('52w_high') or 0
        lo52       = market.get('52w_low') or 0
        sma50      = market.get('sma_50') or 0
        sma200     = market.get('sma_200') or 0

        extra_html = f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
            <div style="flex:1;min-width:120px;">
                <div class="profit-box">
                    <div class="profit-label">EPS (TTM)</div>
                    <div class="profit-value" style="color:#00ffad;">${eps:.2f}</div>
                </div>
            </div>
            <div style="flex:1;min-width:120px;">
                <div class="profit-box">
                    <div class="profit-label">EPS Forward</div>
                    <div class="profit-value" style="color:#00d9ff;">${eps_fwd:.2f}</div>
                </div>
            </div>
            <div style="flex:1;min-width:120px;">
                <div class="profit-box">
                    <div class="profit-label">Beta</div>
                    <div class="profit-value" style="color:{'#ff9800' if beta > 1.5 else '#00ffad'}">{beta:.2f}</div>
                </div>
            </div>
            <div style="flex:1;min-width:120px;">
                <div class="profit-box">
                    <div class="profit-label">Máx. 52 Semanas</div>
                    <div class="profit-value" style="color:#00ffad;">${hi52:.2f}</div>
                </div>
            </div>
            <div style="flex:1;min-width:120px;">
                <div class="profit-box">
                    <div class="profit-label">Mín. 52 Semanas</div>
                    <div class="profit-value" style="color:#f23645;">${lo52:.2f}</div>
                </div>
            </div>
            <div style="flex:1;min-width:120px;">
                <div class="profit-box">
                    <div class="profit-label">SMA 50</div>
                    <div class="profit-value" style="color:#ff9800;">${sma50:.2f}</div>
                </div>
            </div>
            <div style="flex:1;min-width:120px;">
                <div class="profit-box">
                    <div class="profit-label">SMA 200</div>
                    <div class="profit-value" style="color:#5b8ff9;">${sma200:.2f}</div>
                </div>
            </div>
        </div>
        """
        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header"><span class="mod-title">📌 Datos de Mercado Adicionales</span></div>
            <div class="mod-body">{extra_html}</div>
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
        ocf = profitability.get('operating_cashflow')
        rev = profitability.get('revenue_ttm')
        ebt = profitability.get('ebitda')
        cash= profitability.get('total_cash')
        dbt = profitability.get('total_debt')

        profit_items = [
            ("ROE",              fmt_pct(roe, 100),  pc(roe, 0.20, 0.05), "Rentabilidad s/ Fondos Propios"),
            ("ROA",              fmt_pct(roa, 100),  pc(roa, 0.10, 0.02), "Rentabilidad s/ Activos"),
            ("Margen Neto",      fmt_pct(nm, 100),   pc(nm, 0.15, 0.0),   "Beneficio Neto / Ingresos"),
            ("Margen Operativo", fmt_pct(om, 100),   pc(om, 0.15, 0.0),   "EBIT / Ingresos"),
            ("Margen Bruto",     fmt_pct(gm, 100),   pc(gm, 0.40, 0.20),  "Beneficio Bruto / Ingresos"),
            ("Crec. Ingresos",   fmt_pct(rg, 100),   pc(rg, 0.10, 0.0),   "Crecimiento YoY"),
            ("Crec. Beneficios", fmt_pct(eg, 100),   pc(eg, 0.10, 0.0),   "Crecimiento YoY EPS"),
            ("Deuda/Capital",    f"{de:.1f}%" if de is not None else "N/D",
                "#f23645" if de and de > 100 else ("#00ffad" if de and de < 50 else "#ff9800"), "Ratio Apalancamiento"),
            ("Ratio Corriente",  f"{cr:.2f}×" if cr is not None else "N/D",
                "#00ffad" if cr and cr >= 1.5 else ("#f23645" if cr and cr < 1.0 else "#ff9800"), "Activo Cte / Pasivo Cte"),
            ("Free Cash Flow",   format_value(fcf, '$'), "#00ffad" if fcf and fcf > 0 else "#f23645", "Flujo de Caja Libre"),
            ("Op. Cash Flow",    format_value(ocf, '$'), "#00ffad" if ocf and ocf > 0 else "#f23645", "Flujo Operativo"),
            ("Ingresos TTM",     format_value(rev, '$'), "#00ffad", "Ingresos totales últimos 12M"),
            ("EBITDA",           format_value(ebt, '$'), "#00ffad" if ebt and ebt > 0 else "#f23645", "Earnings Before Interest, Tax, D&A"),
            ("Caja Total",       format_value(cash,'$'), "#00ffad", "Efectivo y equivalentes"),
            ("Deuda Total",      format_value(dbt, '$'), "#f23645" if dbt and dbt > 0 else "#00ffad", "Deuda financiera total"),
        ]

        rows_html = ""
        for i in range(0, len(profit_items), 3):
            chunk = profit_items[i:i+3]
            cells = "".join(
                f'<div style="flex:1;min-width:160px;">'
                f'<div class="profit-box">'
                f'<div class="profit-label">{lb}</div>'
                f'<div class="profit-value" style="color:{col};">{vl}</div>'
                f'<div class="metric-desc">{ds}</div>'
                f'</div></div>'
                for lb, vl, col, ds in chunk
            )
            rows_html += f'<div style="display:flex;gap:10px;margin-bottom:10px;">{cells}</div>'

        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">📈 Rentabilidad y Salud Financiera</span>
                <div class="tip-box"><div class="tip-icon">?</div>
                    <div class="tip-text">Verde = bueno · Naranja = neutral · Rojo = precaución. Umbrales de análisis fundamental estándar.</div>
                </div>
            </div>
            <div class="mod-body">{rows_html}</div>
        </div>
        """, unsafe_allow_html=True)

    # ══ TAB 3: PRECIO OBJETIVO ══
    with tabs[2]:
        if target_data and target_data.get('mean'):
            upside  = target_data.get('upside') or 0
            u_arrow = "▲" if upside >= 0 else "▼"
            b_color = "#00ffad" if upside >= 0 else "#f23645"
            b_bg    = "rgba(0,255,173,0.10)" if upside >= 0 else "rgba(242,54,69,0.10)"
            na_str  = _safe(info.get('numberOfAnalystOpinions')) or 'N/D'

            rng_html = "".join(
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
                                    Consenso de {na_str} analistas
                                </div>
                            </div>
                        </div>
                        <div style="flex:1;min-width:200px;">
                            <div class="target-box" style="text-align:left;">
                                <div style="font-family:VT323,monospace;color:#aaa;font-size:1rem;letter-spacing:2px;text-align:center;margin-bottom:18px;">RANGO DE PRECIOS OBJETIVO</div>
                                {rng_html}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Gauge potencial alcista
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=upside,
                delta={'reference': 0, 'increasing': {'color': "#00ffad"}, 'decreasing': {'color': "#f23645"}},
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Potencial Alcista vs Precio Actual", 'font': {'color': 'white', 'size': 14}},
                gauge={
                    'axis': {'range': [-50, 100], 'tickcolor': 'white'},
                    'bar': {'color': b_color, 'thickness': 0.75},
                    'bgcolor': '#1a1e26',
                    'steps': [
                        {'range': [-50, -10], 'color': '#3d1f1f'},
                        {'range': [-10, 10],  'color': '#3d3520'},
                        {'range': [10, 100],  'color': '#1f3d2e'},
                    ],
                    'threshold': {'line': {'color': 'white', 'width': 3}, 'thickness': 0.8, 'value': upside}
                }
            ))
            fig_gauge.update_layout(template="plotly_dark", paper_bgcolor='#11141a',
                                    font=dict(color='white'), height=280,
                                    margin=dict(l=30, r=30, t=50, b=30))
            st.plotly_chart(fig_gauge, use_container_width=True)
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
            st.info("No hay recomendaciones de analistas disponibles.")

    # ══ TAB 5: EARNINGS SURPRISES ══
    with tabs[4]:
        if earnings_surprises and len(earnings_surprises) > 0:
            source_label = "Alpha Vantage" if av_surprises else "Yahoo Finance"
            st.markdown(f"""
            <div class="mod-box">
                <div class="mod-header">
                    <span class="mod-title">🎯 Historial de Earnings Surprises</span>
                    <span style="font-family:'Courier New',monospace;color:#555;font-size:11px;">Fuente: {source_label}</span>
                </div>
                <div class="mod-body">
            """, unsafe_allow_html=True)

            dates        = [s['date'] for s in reversed(earnings_surprises)]
            surprises_v  = [s['surprise_pct'] for s in reversed(earnings_surprises)]
            eps_actual   = [s['eps_actual']   for s in reversed(earnings_surprises)]
            eps_estimate = [s['eps_estimate'] for s in reversed(earnings_surprises)]
            bar_colors   = ['#00ffad' if s >= 0 else '#f23645' for s in surprises_v]

            fig_surp = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                     vertical_spacing=0.08, row_heights=[0.5, 0.5])

            fig_surp.add_trace(go.Bar(
                x=dates, y=surprises_v, marker_color=bar_colors,
                text=[f"{s:+.1f}%" for s in surprises_v],
                textposition='outside', textfont=dict(color='white', size=10),
                name="Sorpresa %"
            ), row=1, col=1)

            fig_surp.add_trace(go.Scatter(
                x=dates, y=eps_actual, mode='lines+markers',
                line=dict(color='#00ffad', width=2), marker=dict(size=8),
                name="EPS Real"
            ), row=2, col=1)
            fig_surp.add_trace(go.Scatter(
                x=dates, y=eps_estimate, mode='lines+markers',
                line=dict(color='#5b8ff9', width=2, dash='dash'), marker=dict(size=8),
                name="EPS Estimado"
            ), row=2, col=1)

            beat_rate = sum(1 for s in earnings_surprises if s['surprise'] >= 0) / len(earnings_surprises) * 100
            avg_surp  = sum(s['surprise_pct'] for s in earnings_surprises) / len(earnings_surprises)

            fig_surp.add_hline(y=0, line_dash="dash", line_color="#666", opacity=0.5, row=1, col=1)
            fig_surp.update_layout(
                title=dict(text=f"Beat Rate: {beat_rate:.0f}%  |  Sorpresa Media: {avg_surp:+.1f}%",
                           font=dict(color='white', size=14)),
                template="plotly_dark", plot_bgcolor='#0c0e12', paper_bgcolor='#11141a',
                font=dict(color='white'), height=450,
                margin=dict(l=50, r=50, t=60, b=50),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_surp.update_xaxes(gridcolor='#1a1e26', tickangle=-45)
            fig_surp.update_yaxes(gridcolor='#1a1e26')
            st.plotly_chart(fig_surp, use_container_width=True)

            # KPIs de sorpresas
            beats = sum(1 for s in earnings_surprises if s['surprise'] >= 0)
            st.markdown(f"""
            <div style="display:flex;gap:12px;margin-top:8px;">
                <div style="flex:1;background:#0a0c10;border:1px solid #1a1e26;border-radius:8px;padding:16px;text-align:center;">
                    <div style="font-family:VT323,monospace;color:#777;font-size:0.85rem;letter-spacing:1px;text-transform:uppercase;">Beat Rate</div>
                    <div style="font-family:VT323,monospace;color:#00ffad;font-size:2.2rem;">{beat_rate:.0f}%</div>
                    <div style="font-family:Courier New,monospace;color:#555;font-size:11px;">{beats} de {len(earnings_surprises)} trimestres</div>
                </div>
                <div style="flex:1;background:#0a0c10;border:1px solid #1a1e26;border-radius:8px;padding:16px;text-align:center;">
                    <div style="font-family:VT323,monospace;color:#777;font-size:0.85rem;letter-spacing:1px;text-transform:uppercase;">Sorpresa Media</div>
                    <div style="font-family:VT323,monospace;color:{'#00ffad' if avg_surp >= 0 else '#f23645'};font-size:2.2rem;">{avg_surp:+.1f}%</div>
                    <div style="font-family:Courier New,monospace;color:#555;font-size:11px;">últimos {len(earnings_surprises)} trimestres</div>
                </div>
                <div style="flex:1;background:#0a0c10;border:1px solid #1a1e26;border-radius:8px;padding:16px;text-align:center;">
                    <div style="font-family:VT323,monospace;color:#777;font-size:0.85rem;letter-spacing:1px;text-transform:uppercase;">Fuente</div>
                    <div style="font-family:VT323,monospace;color:#00d9ff;font-size:1.4rem;">{'🟢 ' + source_label}</div>
                    <div style="font-family:Courier New,monospace;color:#555;font-size:11px;">datos reales</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            if not api_keys['alpha_vantage']:
                st.warning("⚠️ Configura **ALPHA_VANTAGE_API_KEY** para obtener datos precisos de earnings surprises.")
            st.info("No hay datos de earnings surprises disponibles para este ticker.")

    # ══ TAB 6: EVENTOS & CALENDARIO ══
    with tabs[5]:
        event_map = {
            'Earnings Date':        ('📅', 'Próximos Resultados Trimestrales'),
            'Ex-Dividend Date':     ('💵', 'Fecha Ex-Dividendo'),
            'Dividend Date':        ('💰', 'Fecha de Pago del Dividendo'),
            'Fecha Ex-Dividendo':   ('💵', 'Fecha Ex-Dividendo'),
            'Fecha Pago Dividendo': ('💰', 'Fecha de Pago del Dividendo'),
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

        dy  = _safe(info.get('dividendYield'))
        dr  = _safe(info.get('dividendRate'))
        eps = _safe(info.get('trailingEps'))
        nfy = _safe(info.get('nextFiscalYearEnd'))
        emps= market.get('employees')

        if dy:   fechas_html += f'<div class="event-row"><span class="event-label">💹 Dividend Yield</span><span class="event-value">{dy*100:.2f}%</span></div>'
        if dr:   fechas_html += f'<div class="event-row"><span class="event-label">💳 Dividendo Anual / Acción</span><span class="event-value">${dr:.2f}</span></div>'
        if eps:  fechas_html += f'<div class="event-row"><span class="event-label">📊 BPA (Trailing)</span><span class="event-value">${eps:.2f}</span></div>'
        if nfy:  fechas_html += f'<div class="event-row"><span class="event-label">📆 Fin Año Fiscal</span><span class="event-value">{ts_to_date(nfy)}</span></div>'
        if emps: fechas_html += f'<div class="event-row"><span class="event-label">👥 Empleados</span><span class="event-value">{int(emps):,}</span></div>'

        if not fechas_html:
            fechas_html = '<div style="font-family:Courier New,monospace;color:#444;font-size:13px;">No hay eventos disponibles.</div>'

        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header"><span class="mod-title">📅 Calendario Corporativo</span></div>
            <div class="mod-body">{fechas_html}</div>
        </div>
        """, unsafe_allow_html=True)

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
                <div style="font-family:VT323,monospace;color:#00ffad;font-size:1rem;letter-spacing:2px;margin-bottom:12px;">ESTIMACIONES DE BPA — PRÓXIMO TRIMESTRE</div>
                <div style="font-family:Courier New,monospace;color:#555;font-size:11px;margin-bottom:10px;">Consenso de analistas de Wall Street</div>
                """
                for lbl, val in [("Estimación Alta", eps_hi), ("Estimación Media (consenso)", eps_avg), ("Estimación Baja", eps_lo)]:
                    if val is not None:
                        color = "#00ffad" if lbl == "Estimación Media (consenso)" else "#aaa"
                        est_html += f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #111520;"><span style="font-family:Courier New,monospace;color:#666;font-size:11px;">{lbl}</span><span style="font-family:VT323,monospace;color:{color};font-size:1.1rem;">${val:.2f}</span></div>'

            if any([rev_hi, rev_lo, rev_avg]):
                est_html += """
                <div style="font-family:VT323,monospace;color:#00d9ff;font-size:1rem;letter-spacing:2px;margin:16px 0 10px;">ESTIMACIONES DE INGRESOS — PRÓXIMO TRIMESTRE</div>
                """
                for lbl, val in [("Estimación Alta", rev_hi), ("Estimación Media (consenso)", rev_avg), ("Estimación Baja", rev_lo)]:
                    if val is not None:
                        color = "#00ffad" if lbl == "Estimación Media (consenso)" else "#aaa"
                        est_html += f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #111520;"><span style="font-family:Courier New,monospace;color:#666;font-size:11px;">{lbl}</span><span style="font-family:VT323,monospace;color:{color};font-size:1.1rem;">{format_value(val, "$")}</span></div>'

            if est_html:
                st.markdown(f"""
                <div class="mod-box">
                    <div class="mod-header"><span class="mod-title">🔮 Estimaciones de Analistas — Próximos Resultados</span></div>
                    <div class="mod-body">{est_html}</div>
                </div>
                """, unsafe_allow_html=True)

    # ══ TAB 7: FONDOS INSTITUCIONALES ══
    with tabs[6]:
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

        # Usar datos ya cargados en get_yfinance_full — sin llamada extra a Yahoo Finance
        holders_data = inst_data_preload if inst_data_preload else get_institutional_holders(t_in)

        if holders_data:
            major = holders_data.get('major')
            inst  = holders_data.get('institutional')
            mf    = holders_data.get('mutual_funds')

            if major is not None and not major.empty:
                try:
                    pct_inst   = major.iloc[2, 0] if len(major) > 2 else "N/D"
                    pct_retail = major.iloc[3, 0] if len(major) > 3 else "N/D"
                    if isinstance(pct_inst,   float): pct_inst   = f"{pct_inst*100:.1f}%"
                    if isinstance(pct_retail, float): pct_retail = f"{pct_retail*100:.1f}%"
                    st.markdown(f"""
                    <div style="display:flex;gap:12px;margin-bottom:18px;">
                        <div style="flex:1;background:#0a0c10;border:1px solid #1a1e26;border-radius:8px;padding:16px;text-align:center;">
                            <div style="font-family:VT323,monospace;color:#777;font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">% Institucional</div>
                            <div style="font-family:VT323,monospace;color:#00ffad;font-size:2rem;">{pct_inst}</div>
                        </div>
                        <div style="flex:1;background:#0a0c10;border:1px solid #1a1e26;border-radius:8px;padding:16px;text-align:center;">
                            <div style="font-family:VT323,monospace;color:#777;font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">% Retail</div>
                            <div style="font-family:VT323,monospace;color:#00d9ff;font-size:2rem;">{pct_retail}</div>
                        </div>
                        <div style="flex:1;background:#0a0c10;border:1px solid #1a1e26;border-radius:8px;padding:16px;text-align:center;">
                            <div style="font-family:VT323,monospace;color:#777;font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">% Insiders</div>
                            <div style="font-family:VT323,monospace;color:#ff9800;font-size:2rem;">{fmt_pct(market.get('insider_pct'), 100) if market.get('insider_pct') else 'N/D'}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                except: pass

            if inst is not None and not inst.empty:
                st.markdown("""
                <div style="font-family:VT323,monospace;color:#00ffad;font-size:1rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;">
                    🏛 Top Tenedores Institucionales (Fondos, ETFs, Gestoras)
                </div>
                """, unsafe_allow_html=True)
                col_map = {'Holder': 'Institución', 'Shares': 'Acciones',
                           'Date Reported': 'Fecha', '% Out': '% del Float', 'Value': 'Valor (USD)'}
                inst_display = inst.rename(columns=col_map).head(15)
                if 'Valor (USD)' in inst_display.columns:
                    inst_display['Valor (USD)'] = inst_display['Valor (USD)'].apply(
                        lambda x: format_value(x, '$') if _safe(x) else "N/D")
                if 'Acciones' in inst_display.columns:
                    inst_display['Acciones'] = inst_display['Acciones'].apply(
                        lambda x: f"{int(x):,}" if _safe(x) else "N/D")
                st.dataframe(inst_display, use_container_width=True, hide_index=True)

            if mf is not None and not mf.empty:
                st.markdown("""
                <div style="font-family:VT323,monospace;color:#00d9ff;font-size:1rem;letter-spacing:2px;text-transform:uppercase;margin:16px 0 10px;">
                    📦 Top Fondos de Inversión (Mutual Funds)
                </div>
                """, unsafe_allow_html=True)
                mf_col_map = {'Holder': 'Fondo', 'Shares': 'Acciones',
                              'Date Reported': 'Fecha', '% Out': '% del Float', 'Value': 'Valor (USD)'}
                mf_display = mf.rename(columns=mf_col_map).head(10)
                if 'Valor (USD)' in mf_display.columns:
                    mf_display['Valor (USD)'] = mf_display['Valor (USD)'].apply(
                        lambda x: format_value(x, '$') if _safe(x) else "N/D")
                if 'Acciones' in mf_display.columns:
                    mf_display['Acciones'] = mf_display['Acciones'].apply(
                        lambda x: f"{int(x):,}" if _safe(x) else "N/D")
                st.dataframe(mf_display, use_container_width=True, hide_index=True)

            if (inst is None or inst.empty) and (mf is None or mf.empty):
                st.info("No se encontraron datos de tenedores institucionales.")
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

    # ══ TAB 8: SEGMENTOS & SENTIMIENTO ══
    with tabs[7]:
        col_seg, col_sent = st.columns(2)

        with col_seg:
            st.markdown("""
            <div class="mod-box">
                <div class="mod-header"><span class="mod-title">🍕 Ingresos por Segmento</span></div>
                <div class="mod-body">
            """, unsafe_allow_html=True)

            if segments:
                labels = list(segments.keys())
                values = list(segments.values())
                colors = ['#5b8ff9', '#00ffad', '#f5a623', '#f23645', '#9b59b6', '#1abc9c']

                fig_seg = go.Figure(data=[go.Pie(
                    labels=labels, values=values, hole=0.4,
                    marker_colors=colors[:len(labels)],
                    textinfo='label+percent', textfont=dict(size=12, color='white')
                )])
                fig_seg.update_layout(
                    template="plotly_dark", plot_bgcolor='#0c0e12', paper_bgcolor='#0c0e12',
                    font=dict(color='white'), height=320,
                    margin=dict(l=20, r=20, t=20, b=20), showlegend=False
                )
                st.plotly_chart(fig_seg, use_container_width=True)
                st.markdown('<div style="font-family:Courier New,monospace;color:#555;font-size:11px;">✅ Datos reales de Finnhub</div>', unsafe_allow_html=True)
            else:
                if not api_keys['finnhub']:
                    st.markdown('<div style="font-family:Courier New,monospace;color:#555;font-size:12px;padding:20px;">Configura FINNHUB_API_KEY para ver datos de segmentos reales.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="font-family:Courier New,monospace;color:#555;font-size:12px;padding:20px;">Datos de segmentos no disponibles para este ticker.</div>', unsafe_allow_html=True)

            st.markdown("</div></div>", unsafe_allow_html=True)

        with col_sent:
            st.markdown("""
            <div class="mod-box">
                <div class="mod-header"><span class="mod-title">📰 Sentimiento de Noticias</span></div>
                <div class="mod-body">
            """, unsafe_allow_html=True)

            if sentiment:
                sent_val   = sentiment.get('overall_sentiment', 'neutral')
                score      = sentiment.get('sentiment_score', 0)
                bull_pct   = sentiment.get('bullish_pct', 0)
                bear_pct   = sentiment.get('bearish_pct', 0)
                news_count = sentiment.get('news_count', 0)
                analyzed   = sentiment.get('analyzed_count', 0)

                sent_colors = {'alcista': '#00ffad', 'bajista': '#f23645', 'neutral': '#ff9800'}
                sent_color  = sent_colors.get(sent_val, '#888')

                fig_gauge2 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=score * 100,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Score de Sentimiento", 'font': {'color': 'white', 'size': 13}},
                    gauge={
                        'axis': {'range': [-100, 100], 'tickcolor': 'white'},
                        'bar': {'color': sent_color, 'thickness': 0.75},
                        'bgcolor': '#1a1e26',
                        'steps': [
                            {'range': [-100, -33], 'color': '#3d1f1f'},
                            {'range': [-33, 33],   'color': '#3d3520'},
                            {'range': [33, 100],   'color': '#1f3d2e'},
                        ],
                    }
                ))
                fig_gauge2.update_layout(template="plotly_dark", paper_bgcolor='#0c0e12',
                                         font=dict(color='white'), height=220,
                                         margin=dict(l=20, r=20, t=40, b=10))
                st.plotly_chart(fig_gauge2, use_container_width=True)

                st.markdown(f"""
                <div style="display:flex;gap:8px;margin-top:8px;">
                    <div style="flex:1;text-align:center;background:#0a0c10;border:1px solid #1a1e26;border-radius:6px;padding:10px;">
                        <div style="font-family:VT323,monospace;color:#777;font-size:0.8rem;">SENTIMIENTO</div>
                        <div style="font-family:VT323,monospace;color:{sent_color};font-size:1.3rem;">{sent_val.upper()}</div>
                    </div>
                    <div style="flex:1;text-align:center;background:#0a0c10;border:1px solid #1a1e26;border-radius:6px;padding:10px;">
                        <div style="font-family:VT323,monospace;color:#777;font-size:0.8rem;">ALCISTAS</div>
                        <div style="font-family:VT323,monospace;color:#00ffad;font-size:1.3rem;">{bull_pct:.0f}%</div>
                    </div>
                    <div style="flex:1;text-align:center;background:#0a0c10;border:1px solid #1a1e26;border-radius:6px;padding:10px;">
                        <div style="font-family:VT323,monospace;color:#777;font-size:0.8rem;">BAJISTAS</div>
                        <div style="font-family:VT323,monospace;color:#f23645;font-size:1.3rem;">{bear_pct:.0f}%</div>
                    </div>
                </div>
                <div style="font-family:Courier New,monospace;color:#444;font-size:11px;margin-top:8px;">
                    📊 {analyzed} noticias analizadas de {news_count} disponibles (últimos 30 días)
                </div>
                """, unsafe_allow_html=True)
            else:
                if not api_keys['finnhub']:
                    st.markdown('<div style="font-family:Courier New,monospace;color:#555;font-size:12px;padding:20px;">Configura FINNHUB_API_KEY para ver el análisis de sentimiento de noticias reales.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="font-family:Courier New,monospace;color:#555;font-size:12px;padding:20px;">Sentimiento no disponible para este ticker.</div>', unsafe_allow_html=True)

            st.markdown("</div></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════
    # SUGERENCIAS AUTOMÁTICAS
    # ══════════════════════════════════════════════
    st.markdown("<hr>", unsafe_allow_html=True)
    suggestions = get_suggestions(info, recommendations, target_data, profitability)
    sug_html = "".join(
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
    # RSU IA — ANÁLISIS COMPLETO O RÁPIDO
    # ══════════════════════════════════════════════
    st.markdown("<hr>", unsafe_allow_html=True)

    datos_cuantitativos = f"""
| Métrica | Valor |
|---|---|
| Precio actual | ${cp:,.2f} |
| Market Cap | {format_value(market_cap, '$')} |
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
| Free Cash Flow | {format_value(profitability.get('free_cashflow'), '$')} |
| Precio objetivo medio | {"$"+str(round(target_data['mean'],2)) if target_data.get('mean') else 'N/A'} |
| Potencial alcista | {(str(round(target_data['upside'],1))+"%") if target_data.get('upside') else 'N/A'} |
| Sector | {info.get('sector', 'N/A')} |
| País | {info.get('country', 'N/A')} |
"""

    st.markdown("""
    <div class="rsu-box">
        <div class="rsu-title">🤖 RSU Artificial Intelligence</div>
        <p style="font-family:'Courier New',monospace;color:#666;font-size:13px;line-height:1.6;margin-bottom:16px;">
            Dos modos de análisis: <strong style="color:#00ffad;">Rápido</strong> (snapshot ejecutivo en segundos) 
            o <strong style="color:#00d9ff;">Completo</strong> (informe de 11 secciones con técnico, smart money y catalizadores).
        </p>
    """, unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        btn_rapido = st.button("⚡ ANÁLISIS RÁPIDO", key="btn_rapido")
    with col_btn2:
        btn_completo = st.button("📋 INFORME COMPLETO (11 SECCIONES)", key="btn_completo")

    st.markdown("</div>", unsafe_allow_html=True)

    model_ia, modelo_nombre, error_ia = get_ia_model()

    if btn_rapido or btn_completo:
        if error_ia:
            st.error(f"❌ Error al conectar con el modelo IA: {error_ia}")
        else:
            prompt_template = PROMPT_RSU_RAPIDO if btn_rapido else PROMPT_RSU_COMPLETO
            prompt_final = (prompt_template
                            .replace("{t}", t_in)
                            .replace("{datos_cuantitativos}", datos_cuantitativos))

            label_spinner = "ANÁLISIS RÁPIDO" if btn_rapido else "GENERANDO INFORME COMPLETO"
            with st.spinner(f"[ {label_spinner} {t_in} ... ]"):
                try:
                    res = model_ia.generate_content(
                        prompt_final,
                        generation_config={"temperature": 0.2, "max_output_tokens": 8192}
                    )
                    st.session_state['last_report']        = res.text
                    st.session_state['last_report_ticker'] = t_in
                except Exception as e:
                    st.error(f"❌ Error generando el informe: {e}")

    if st.session_state.get('last_report') and st.session_state.get('last_report_ticker') == t_in:
        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">📋 Informe RSU IA — {t_in}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.container():
            st.markdown(
                '<div style="border:1px solid #00ffad1a;border-top:none;border-radius:0 0 8px 8px;'
                'padding:24px;background:#0a0c10;margin-bottom:18px;">',
                unsafe_allow_html=True
            )
            st.markdown(st.session_state['last_report'])
            st.markdown('</div>', unsafe_allow_html=True)

        col_dl, _ = st.columns([1, 3])
        with col_dl:
            st.download_button(
                label="⬇️ DESCARGAR INFORME (.md)",
                data=st.session_state['last_report'].encode('utf-8'),
                file_name=f"RSU_Earnings_{t_in}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                key="download_report"
            )

    # ══ FOOTER ══
    st.markdown("""
    <div style="text-align:center;margin-top:50px;padding:20px;border-top:1px solid #0f1218;">
        <div style="font-family:'VT323',monospace;color:#222;font-size:0.82rem;letter-spacing:2px;">
            [END OF REPORT // RSU_EARNINGS_v4.0]<br>
            [DATA SOURCE: YAHOO FINANCE · ALPHA VANTAGE · FINNHUB · TRADINGVIEW · GEMINI AI]<br>
            [STATUS: ACTIVE // {year}]
        </div>
    </div>
    """.replace("{year}", str(datetime.now().year)), unsafe_allow_html=True)


if __name__ == "__main__":
    render()




