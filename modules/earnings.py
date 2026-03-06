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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import math
import html
import traceback
import logging

logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger("rsu_earnings")

# ────────────────────────────────────────────────
# HTTP SESSION COMPARTIDA (connection pooling)
# ────────────────────────────────────────────────

def _make_session():
    """Sesión requests con retry automático y connection pooling."""
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(
        pool_connections=8,
        pool_maxsize=16,
        max_retries=retry,
    )
    s.mount("https://", adapter)
    s.mount("http://",  adapter)
    s.headers.update({"User-Agent": "RSUEarnings/4.0"})
    return s

_HTTP = _make_session()

# ────────────────────────────────────────────────
# API KEYS
# ────────────────────────────────────────────────

def get_api_keys():
    return {
        'alpha_vantage': st.secrets.get("ALPHA_VANTAGE_API_KEY", ""),
        'finnhub':       st.secrets.get("FINNHUB_API_KEY", ""),
        'fmp':           st.secrets.get("FMP_API_KEY", ""),          # financialmodelingprep.com — plan free 250 req/día
    }

# ────────────────────────────────────────────────
# DECORADOR SAFE_CALL — reemplaza except: pass
# ────────────────────────────────────────────────

def safe_call(fn, *args, default=None, context="", **kwargs):
    """
    Ejecuta fn(*args, **kwargs). Si falla, loguea el error con contexto
    y devuelve `default`. Reemplaza los bloques except: pass silenciosos.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        label = context or getattr(fn, "__name__", "unknown")
        logger.warning("[safe_call] %s → %s: %s", label, type(exc).__name__, exc)
        return default

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

def get_yfinance_full(ticker):  # cache removed: debug log needs session_state
    """
    Carga datos de yfinance con 3 estrategias de precio y modo debug.
    Devuelve datos parciales si hay historial aunque info{} esté vacío.
    Nunca devuelve None si existe algún precio accesible.
    """
    debug_log = []   # acumulamos pasos — se expone en UI si falla
    try:
        stock = yf.Ticker(ticker)
        debug_log.append("✅ yf.Ticker() creado")

        try:
            info = stock.info or {}
            debug_log.append(f"✅ info dict: {len(info)} keys | quoteType={info.get('quoteType','?')} longName={info.get('longName','?')[:40]}")
        except Exception as e:
            info = {}
            debug_log.append(f"⚠️ info falló: {e}")

        # ── Estrategia 1: campos de precio en info{} ──
        cp_check = (
            _safe(info.get('currentPrice')) or
            _safe(info.get('regularMarketPrice')) or
            _safe(info.get('regularMarketOpen')) or
            _safe(info.get('ask')) or
            _safe(info.get('bid')) or
            _safe(info.get('navPrice')) or
            _safe(info.get('postMarketPrice')) or
            _safe(info.get('preMarketPrice'))
        )
        if cp_check:
            debug_log.append(f"✅ Precio desde info: {cp_check}")
        else:
            debug_log.append(f"⚠️ info no tiene precio. Keys disponibles: {list(info.keys())[:20]}")

        # ── Estrategia 2: historial reciente ──
        hist_data = None
        if not cp_check:
            try:
                hist_data = stock.history(period="5d", interval="1d", auto_adjust=True)
                if hist_data is not None and not hist_data.empty and 'Close' in hist_data.columns:
                    last_close = _safe(float(hist_data['Close'].dropna().iloc[-1]))
                    if last_close:
                        cp_check = last_close
                        info['currentPrice'] = last_close
                        info['regularMarketPrice'] = last_close
                        if len(hist_data) >= 2:
                            prev = _safe(float(hist_data['Close'].dropna().iloc[-2]))
                            if prev: info['previousClose'] = prev
                        debug_log.append(f"✅ Precio desde history(5d): {last_close}")
                    else:
                        debug_log.append(f"⚠️ history(5d) devolvió datos pero Close={last_close}")
                else:
                    debug_log.append(f"⚠️ history(5d) vacío o sin columna Close: {hist_data}")
            except Exception as e:
                debug_log.append(f"❌ history(5d) excepción: {e}")

        # ── Estrategia 3: fast_info ──
        if not cp_check:
            try:
                fi = stock.fast_info
                last = _safe(getattr(fi, 'last_price', None))
                debug_log.append(f"fast_info.last_price={last} | attrs={[a for a in dir(fi) if not a.startswith('_')][:8]}")
                if last:
                    cp_check = last
                    info['currentPrice'] = last
                    info['regularMarketPrice'] = last
                    prev = _safe(getattr(fi, 'previous_close', None))
                    if prev: info['previousClose'] = prev
                    mc = _safe(getattr(fi, 'market_cap', None))
                    if mc and not info.get('marketCap'): info['marketCap'] = mc
                    debug_log.append(f"✅ Precio desde fast_info: {last}")
                else:
                    debug_log.append(f"⚠️ fast_info.last_price es None o 0")
            except Exception as e:
                debug_log.append(f"❌ fast_info excepción: {e}")

        if not cp_check:
            debug_log.append(f"❌ FALLO TOTAL: sin precio para {ticker}")
            # Guardar log en session_state para mostrarlo en UI
            import streamlit as _st
            st.session_state['_debug_log'] = debug_log
            st.session_state['_debug_ticker'] = ticker
            logger.warning("[get_yfinance_full] Sin precio para %s | %s", ticker, " | ".join(debug_log))
            return None

        # Si llegamos aquí, tenemos precio. Guardar debug log de éxito también.
        st.session_state['_debug_log'] = debug_log
        st.session_state['_debug_ticker'] = ticker

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
        except Exception as e:
            logger.warning("[yf.recommendations] %s: %s", ticker, e)

        rec_summary = None
        try:
            rs = stock.recommendations_summary
            if rs is not None and not rs.empty:
                rec_summary = rs.head(6)
        except Exception as e:
            logger.warning("[yf.recommendations_summary] %s: %s", ticker, e)

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

        # ── Fallback fast_info para métricas frecuentemente N/D ──
        # fast_info es más estable que info{} para algunos campos
        try:
            fi = stock.fast_info
            if metrics['trailing_pe'] is None:
                fi_pe = _safe(getattr(fi, 'pe_forward', None) or getattr(fi, 'price_eps_ttm', None))
                if fi_pe: metrics['trailing_pe'] = fi_pe
            if not info.get('marketCap'):
                fi_mc = _safe(getattr(fi, 'market_cap', None))
                if fi_mc: info['marketCap'] = fi_mc
            if not info.get('fiftyTwoWeekHigh'):
                fi_hi = _safe(getattr(fi, 'year_high', None))
                fi_lo = _safe(getattr(fi, 'year_low', None))
                if fi_hi: info['fiftyTwoWeekHigh'] = fi_hi
                if fi_lo: info['fiftyTwoWeekLow']  = fi_lo
            if not info.get('fiftyDayAverage'):
                fi_sma = _safe(getattr(fi, 'fifty_day_average', None))
                if fi_sma: info['fiftyDayAverage'] = fi_sma
            if not info.get('twoHundredDayAverage'):
                fi_sma2 = _safe(getattr(fi, 'two_hundred_day_average', None))
                if fi_sma2: info['twoHundredDayAverage'] = fi_sma2
        except Exception as e:
            logger.warning("[yf.fast_info metrics] %s: %s", ticker, e)

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
        except Exception as e:
            logger.warning("[yf.calendar] %s: %s", ticker, e)

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
        except Exception as e:
            logger.warning("[yf.sparkline] %s: %s", ticker, e)

        # Histórico 1 año para gráfico
        hist_1y = None
        try:
            h = stock.history(period="1y", auto_adjust=True)
            if not h.empty:
                hist_1y = h
        except Exception as e:
            logger.warning("[yf.hist_1y] %s: %s", ticker, e)

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
        except Exception as e:
            logger.warning("[yf.earnings_history] %s: %s", ticker, e)

        # Institutional holders — same session, no extra call
        inst_data = {}
        try:
            inst_data['institutional'] = stock.institutional_holders
            inst_data['major']         = stock.major_holders
            inst_data['mutual_funds']  = stock.mutualfund_holders
        except Exception as e:
            logger.warning("[yf.inst_data] %s: %s", ticker, e)

        return {
            'info': info, 'recommendations': recommendations, 'rec_summary': rec_summary,
            'target_data': target_data, 'metrics': metrics, 'profitability': profitability,
            'market': market, 'events': events, 'analyst_estimates': analyst_estimates,
            'sparkline': sparkline, 'hist_1y': hist_1y,
            'earnings_surprises': earnings_surprises,
            'inst_data': inst_data,
        }
    except Exception as e:
        logger.error("[get_yfinance_full] %s: %s\n%s", ticker, e, traceback.format_exc())
        return None

# ────────────────────────────────────────────────
# ALPHA VANTAGE — EARNINGS HISTORY (complementario)
# ────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_alpha_vantage_earnings(ticker, api_key):
    if not api_key: return None
    try:
        resp = _HTTP.get(
            "https://www.alphavantage.co/query",
            params={'function': 'EARNINGS', 'symbol': ticker, 'apikey': api_key},
            timeout=20
        )
        if resp.status_code == 200:
            data = resp.json()
            if 'Note' in data or 'Information' in data or not data.get('quarterlyEarnings'):
                logger.warning("[AV] Rate limit or no data for %s: %s", ticker, list(data.keys()))
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
    except Exception as e:
        logger.warning("[get_alpha_vantage_earnings] %s: %s", ticker, e)
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
            try:
                r = _HTTP.get(f"{base_url}/stock/revenue-breakdown",
                              params=params, headers=headers, timeout=10)
                result[key] = r.json() if r.status_code == 200 else {}
            except Exception as e:
                logger.warning("[finnhub.%s] %s: %s", key, ticker, e)
                result[key] = {}
            time.sleep(0.2)

        try:
            to_date   = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            r = _HTTP.get(f"{base_url}/company-news",
                          params={'symbol': ticker, 'from': from_date, 'to': to_date},
                          headers=headers, timeout=10)
            result['news'] = r.json() if r.status_code == 200 else []
            if r.status_code == 429:
                logger.warning("[finnhub] Rate limit hit for %s news", ticker)
        except Exception as e:
            logger.warning("[finnhub.news] %s: %s", ticker, e)
            result['news'] = []

        result['source'] = 'finnhub'
        return result
    except Exception as e:
        logger.warning("[get_finnhub_data] %s: %s", ticker, e)
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
    """Análisis de sentimiento mejorado con negación y word-boundary matching."""
    if not finnhub_data or 'news' not in finnhub_data: return None
    news = finnhub_data['news']
    if not news: return None

    # Frases/patrones positivos (completos para evitar falsos positivos)
    bullish_phrases = [
        'beat', 'beats', 'strong earnings', 'strong revenue', 'revenue growth',
        'profit growth', 'record revenue', 'record earnings', 'raises guidance',
        'raised guidance', 'upgrade', 'upgraded', 'outperform', 'buy rating',
        'exceeds', 'exceeded', 'surges', 'soars', 'rallies', 'new high',
        'buyback', 'share repurchase', 'dividend increase', 'expands',
        'partnership', 'acquisition', 'market share', 'strong demand'
    ]
    bearish_phrases = [
        'misses', 'missed', 'miss', 'weak earnings', 'weak revenue', 'revenue decline',
        'lowers guidance', 'lowered guidance', 'cuts guidance', 'downgrade', 'downgraded',
        'underperform', 'sell rating', 'below expectations', 'plunges', 'crashes',
        'falls sharply', 'loses', 'layoffs', 'layoff', 'restructuring', 'recalls',
        'investigation', 'lawsuit', 'sec probe', 'bankruptcy', 'default', 'fraud',
        'data breach', 'fine', 'penalty', 'recall', 'safety concerns'
    ]
    # Negaciones que invierten el sentido
    negations = ['not ', 'no ', "doesn't ", "don't ", "won't ", "isn't ", "aren't ", "wasn't "]

    bullish_count = bearish_count = total = 0
    for article in news[:50]:
        title = (article.get('headline', '') + ' ' + article.get('summary', '')).lower()
        if not title.strip(): continue
        total += 1

        b_hit = any(ph in title for ph in bullish_phrases)
        bear_hit = any(ph in title for ph in bearish_phrases)

        # Detectar negaciones antes de una palabra clave positiva
        if b_hit:
            negated = any(
                neg + ph in title
                for neg in negations
                for ph in bullish_phrases
                if neg + ph in title
            )
            if negated: bear_hit = True
            else: bullish_count += 1

        if bear_hit:
            # Evitar doble conteo si ya fue contado arriba
            if not (b_hit and not any(neg + ph in title for neg in negations for ph in bullish_phrases if neg + ph in title)):
                bearish_count += 1

    ts = bullish_count + bearish_count
    if ts == 0:
        return {'overall_sentiment': 'neutral', 'sentiment_score': 0,
                'news_count': len(news), 'bullish_pct': 0, 'bearish_pct': 0,
                'analyzed_count': total, 'source': 'finnhub',
                'articles': news[:15]}

    bullish_pct = bullish_count / ts * 100
    bearish_pct = bearish_count / ts * 100

    if bullish_pct > 60:
        sentiment, score = 'alcista', min(1.0, 0.5 + (bullish_pct - 60) / 80)
    elif bearish_pct > 60:
        sentiment, score = 'bajista', max(-1.0, -0.5 - (bearish_pct - 60) / 80)
    else:
        sentiment, score = 'neutral', (bullish_pct - bearish_pct) / 100

    return {
        'overall_sentiment': sentiment, 'sentiment_score': score,
        'news_count': len(news), 'bullish_pct': round(bullish_pct, 1),
        'bearish_pct': round(bearish_pct, 1), 'analyzed_count': total,
        'source': 'finnhub', 'articles': news[:15]
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
    except Exception as e:
        logger.warning("[get_institutional_holders] %s: %s", ticker, e)
        return None

# ────────────────────────────────────────────────
# FMP — FINANCIAL MODELING PREP (fuente gratuita)
# API docs: https://site.financialmodelingprep.com/developer/docs
# Plan free: 250 req/día, sin WebSocket, datos fundamentales completos
# ────────────────────────────────────────────────

_FMP_BASE = "https://financialmodelingprep.com/api/v3"

def _fmp_get(endpoint, params, api_key, timeout=12):
    """Llamada a FMP con session compartida y logging de errores."""
    if not api_key:
        return None
    try:
        p = {"apikey": api_key, **params}
        resp = _HTTP.get(f"{_FMP_BASE}/{endpoint}", params=p, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            # FMP devuelve lista vacía o dict con error si el ticker no existe
            if isinstance(data, dict) and data.get("Error Message"):
                logger.warning("[FMP] %s → %s", endpoint, data["Error Message"])
                return None
            return data
        logger.warning("[FMP] HTTP %s for %s", resp.status_code, endpoint)
        return None
    except Exception as e:
        logger.warning("[FMP] %s: %s", endpoint, e)
        return None

@st.cache_data(ttl=900, show_spinner=False)
def get_fmp_data(ticker, api_key):
    """
    Obtiene de FMP:
    - Perfil completo (sector, industria, descripción, beta, empleados…)
    - Ratios financieros (PE, P/B, P/S, EV/EBITDA, ROE, márgenes…)
    - Income statement último trimestre (ingresos, EPS, márgenes)
    - Earnings surprises de los últimos 8 trimestres
    - Price target consenso de analistas
    - Insider trades recientes
    Devuelve dict con todas las secciones o None si FMP no está configurado.
    """
    if not api_key:
        return None

    result = {}

    # 1. Perfil
    profile = _fmp_get(f"profile/{ticker}", {}, api_key)
    if profile and isinstance(profile, list) and profile:
        result['profile'] = profile[0]

    # 2. Ratios TTM
    ratios = _fmp_get(f"ratios-ttm/{ticker}", {}, api_key)
    if ratios and isinstance(ratios, list) and ratios:
        result['ratios'] = ratios[0]

    # 3. Key metrics TTM (incluye EV/EBITDA, FCF yield, etc.)
    km = _fmp_get(f"key-metrics-ttm/{ticker}", {}, api_key)
    if km and isinstance(km, list) and km:
        result['key_metrics'] = km[0]

    # 4. Earnings surprises (últimos 8 trimestres)
    es = _fmp_get(f"earnings-surprises/{ticker}", {}, api_key)
    if es and isinstance(es, list):
        surprises = []
        for r in es[:8]:
            ea  = safe_float(r.get('actualEarningResult'))
            ee  = safe_float(r.get('estimatedEarning'))
            sur = ea - ee if (ea and ee) else 0
            pct = (sur / abs(ee) * 100) if (sur and ee and ee != 0) else 0
            surprises.append({
                'date':         r.get('date', 'N/D'),
                'eps_actual':   ea,
                'eps_estimate': ee,
                'surprise':     sur,
                'surprise_pct': pct,
            })
        result['earnings_surprises'] = surprises

    # 5. Analyst estimates (price target)
    pt = _fmp_get(f"price-target-consensus/{ticker}", {}, api_key)
    if pt and isinstance(pt, list) and pt:
        result['price_target'] = pt[0]

    # 6. Insider trades (últimos 10)
    it = _fmp_get(f"insider-trading", {"symbol": ticker, "limit": 10}, api_key)
    if it and isinstance(it, list):
        result['insider_trades'] = it[:10]

    # 7. Analyst recommendations
    rec = _fmp_get(f"analyst-stock-recommendations/{ticker}", {"limit": 1}, api_key)
    if rec and isinstance(rec, list) and rec:
        result['analyst_rec'] = rec[0]

    return result if result else None

def fmp_override_metrics(yf_data, fmp_data):
    """
    Combina datos yfinance (base) con FMP (override cuando disponible).
    FMP tiene endpoints estables y schema documentado — preferir sus valores.
    """
    if not fmp_data:
        return yf_data

    r = fmp_data.get('ratios', {})
    km = fmp_data.get('key_metrics', {})
    prof = fmp_data.get('profile', {})

    # Override métricas de valoración
    if r:
        m = yf_data.get('metrics', {})
        if r.get('peRatioTTM'):   m['trailing_pe']    = safe_float(r['peRatioTTM']) or m.get('trailing_pe')
        if r.get('priceToSalesRatioTTM'): m['price_to_sales'] = safe_float(r['priceToSalesRatioTTM']) or m.get('price_to_sales')
        if r.get('priceToBookRatioTTM'):  m['price_to_book']  = safe_float(r['priceToBookRatioTTM']) or m.get('price_to_book')
        if r.get('pegRatioTTM'):  m['peg_ratio']       = safe_float(r['pegRatioTTM']) or m.get('peg_ratio')
        if km.get('enterpriseValueOverEBITDATTM'): m['ev_ebitda'] = safe_float(km['enterpriseValueOverEBITDATTM']) or m.get('ev_ebitda')
        yf_data['metrics'] = m

    # Override rentabilidad
    if r:
        p = yf_data.get('profitability', {})
        if r.get('returnOnEquityTTM'):    p['roe']         = safe_float(r['returnOnEquityTTM']) or p.get('roe')
        if r.get('returnOnAssetsTTM'):    p['roa']         = safe_float(r['returnOnAssetsTTM']) or p.get('roa')
        if r.get('netProfitMarginTTM'):   p['net_margin']  = safe_float(r['netProfitMarginTTM']) or p.get('net_margin')
        if r.get('operatingProfitMarginTTM'): p['op_margin'] = safe_float(r['operatingProfitMarginTTM']) or p.get('op_margin')
        if r.get('grossProfitMarginTTM'): p['gross_margin']= safe_float(r['grossProfitMarginTTM']) or p.get('gross_margin')
        if r.get('debtEquityRatioTTM'):   p['debt_to_equity'] = safe_float(r['debtEquityRatioTTM']) * 100 or p.get('debt_to_equity')
        if r.get('currentRatioTTM'):      p['current_ratio']  = safe_float(r['currentRatioTTM']) or p.get('current_ratio')
        if km.get('freeCashFlowPerShareTTM') and yf_data['market'].get('market_cap'):
            # No hay FCF absoluto en TTM endpoint free — mantener yfinance
            pass
        yf_data['profitability'] = p

    # Precio objetivo desde FMP si mejor que YF
    pt = fmp_data.get('price_target', {})
    if pt:
        cp = yf_data['target_data'].get('current', 0) or 0
        mean = safe_float(pt.get('targetConsensus')) or yf_data['target_data'].get('mean')
        if mean and mean > 0:
            yf_data['target_data']['mean']   = mean
            yf_data['target_data']['high']   = safe_float(pt.get('targetHigh'))   or yf_data['target_data'].get('high')
            yf_data['target_data']['low']    = safe_float(pt.get('targetLow'))    or yf_data['target_data'].get('low')
            yf_data['target_data']['median'] = safe_float(pt.get('targetMedian')) or yf_data['target_data'].get('median')
            yf_data['target_data']['upside'] = ((mean - cp) / cp * 100) if (mean and cp) else yf_data['target_data'].get('upside')

    return yf_data

# ────────────────────────────────────────────────
# SUGERENCIAS AUTOMÁTICAS
# ────────────────────────────────────────────────

def get_suggestions(info, recommendations, target_data, profitability):
    suggestions = []

    sector = (info.get('sector') or '').lower()
    industry = (info.get('industry') or '').lower()

    # ── Umbrales ajustados por sector ──
    # PE razonable varía enormemente: utilities ~15, tech ~30, biotech no aplica
    def pe_label(pe_val):
        if not pe_val or pe_val <= 0: return None, None
        if 'technology' in sector or 'communication' in sector:
            lo, hi = 20, 50
        elif 'financial' in sector or 'bank' in industry:
            lo, hi = 8, 18
        elif 'utilities' in sector or 'real estate' in sector:
            lo, hi = 12, 22
        elif 'health' in sector or 'biotech' in industry:
            lo, hi = 15, 60  # biotech puede tener PE muy alto o N/A
        else:
            lo, hi = 15, 30
        if pe_val < lo:    return "barato vs sector", "#00ffad"
        elif pe_val > hi:  return "caro vs sector", "#f23645"
        else:              return "valoración razonable vs sector", "#ff9800"

    def roe_thresholds():
        """ROE esperado varía por sector."""
        if 'financial' in sector or 'bank' in industry:
            return 0.10, 0.05   # bancos con ROE >10% = bueno
        elif 'real estate' in sector:
            return 0.08, 0.03
        else:
            return 0.20, 0.05   # tech/consumer: >20% = bueno

    pe         = _safe(info.get('trailingPE'))
    forward_pe = _safe(info.get('forwardPE'))
    cp         = target_data.get('current', 0) or 0
    n_analysts = _safe(info.get('numberOfAnalystOpinions')) or 0

    # PE con contexto sectorial
    if pe and pe > 0:
        pe_desc, _ = pe_label(pe)
        if pe_desc:
            suggestions.append(f"📊 P/E Trailing {pe:.1f}× — {pe_desc} ({info.get('sector','sector desconocido')}).")

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
        roe_hi, roe_lo = roe_thresholds()
        if roe > roe_hi * 1.5:  suggestions.append(f"💎 ROE excepcional ({roe*100:.1f}%) para el sector {info.get('sector','N/A')} — empresa muy eficiente.")
        elif roe > roe_hi:       suggestions.append(f"💚 ROE sólido ({roe*100:.1f}%) — buena rentabilidad sobre fondos propios.")
        elif roe < 0:            suggestions.append(f"🔴 ROE negativo ({roe*100:.1f}%) — empresa destruyendo valor actualmente.")

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
# RSU PUNTUACIÓN — Score de salud 0-100
# ────────────────────────────────────────────────

def compute_rsu_score(info, metrics, profitability, market, recommendations, target_data):
    """
    Score compuesto 0-100 dividido en 4 pilares (25 pts cada uno):
    1. Calidad del negocio (márgenes, ROE, FCF)
    2. Valoración relativa al sector
    3. Momentum de precio (vs SMA50/200)
    4. Consenso analistas + upside
    Devuelve dict con score total y sub-scores.
    """
    sector   = (info.get('sector') or '').lower()
    industry = (info.get('industry') or '').lower()

    # Detectar empresa pre-revenue / early-stage (pérdidas > 3 años consecutivos)
    rev_ttm = profitability.get('revenue_ttm') or 0
    is_pre_revenue = rev_ttm < 50_000_000  # ingresos < 50M = empresa muy pequeña/pre-revenue

    # ── Pilar 1: Calidad (0-25) ──
    # Punto de partida neutral (12) para pre-revenue — no castigar por pérdidas esperadas
    q_score = 8 if is_pre_revenue else 0
    nm = profitability.get('net_margin')
    roe = profitability.get('roe')
    fcf = profitability.get('free_cashflow')
    op_m = profitability.get('op_margin')

    # Márgenes netos — contexto sectorial
    if nm is not None:
        if 'financial' in sector or 'bank' in industry:
            q_score += 5
        elif nm > 0.20:  q_score += 8
        elif nm > 0.10:  q_score += 6
        elif nm > 0.02:  q_score += 3
        elif nm < 0 and not is_pre_revenue:  q_score -= 3   # no penalizar si es pre-revenue

    if roe is not None:
        roe_hi = 0.10 if ('financial' in sector) else 0.15
        if roe > roe_hi * 2:   q_score += 8
        elif roe > roe_hi:     q_score += 5
        elif roe < 0 and not is_pre_revenue: q_score -= 4

    if fcf is not None:
        if fcf > 0:   q_score += 5
        elif fcf < 0 and not is_pre_revenue: q_score -= 2

    if op_m is not None and op_m > 0.15:
        q_score += 4

    q_score = max(0, min(25, q_score))

    # ── Pilar 2: Valoración (0-25) ──
    v_score = 12  # Neutral por defecto
    pe = metrics.get('trailing_pe')
    forward_pe = metrics.get('forward_pe')
    peg = metrics.get('peg_ratio')

    if 'technology' in sector or 'communication' in sector:
        pe_cheap, pe_fair, pe_exp = 20, 35, 55
    elif 'financial' in sector or 'bank' in industry:
        pe_cheap, pe_fair, pe_exp = 8, 15, 22
    elif 'utilities' in sector or 'real estate' in sector:
        pe_cheap, pe_fair, pe_exp = 10, 18, 28
    elif 'health' in sector or 'biotech' in industry:
        pe_cheap, pe_fair, pe_exp = 15, 40, 80
    else:
        pe_cheap, pe_fair, pe_exp = 12, 22, 35

    if pe and pe > 0:
        if pe < pe_cheap:       v_score += 8
        elif pe < pe_fair:      v_score += 4
        elif pe > pe_exp:       v_score -= 6
        elif pe > pe_fair:      v_score -= 3

    if peg and peg > 0:
        if peg < 1.0:   v_score += 5
        elif peg < 1.5: v_score += 2
        elif peg > 3.0: v_score -= 5

    if forward_pe and pe and forward_pe > 0 and pe > 0:
        if forward_pe < pe * 0.85: v_score += 3
        elif forward_pe > pe * 1.1: v_score -= 2

    v_score = max(0, min(25, v_score))

    # ── Pilar 3: Momentum (0-25) ──
    m_score = 12
    cp = market.get('price') or 0
    sma50  = market.get('sma_50')
    sma200 = market.get('sma_200')
    hi52   = market.get('52w_high')
    lo52   = market.get('52w_low')

    if cp and sma50:
        if cp > sma50 * 1.05:   m_score += 5
        elif cp > sma50:        m_score += 2
        elif cp < sma50 * 0.95: m_score -= 4
        else:                   m_score -= 1

    if cp and sma200:
        if cp > sma200 * 1.10:  m_score += 5
        elif cp > sma200:       m_score += 2
        elif cp < sma200 * 0.90: m_score -= 5
        else:                    m_score -= 1

    if cp and hi52 and lo52 and hi52 > lo52:
        pct_range = (cp - lo52) / (hi52 - lo52)
        if pct_range > 0.80:   m_score += 3   # cerca de máximos — momentum fuerte
        elif pct_range < 0.20: m_score -= 4   # cerca de mínimos

    m_score = max(0, min(25, m_score))

    # ── Pilar 4: Consenso (0-25) ──
    c_score = 12
    upside = target_data.get('upside')
    if recommendations and recommendations.get('total', 0) > 0:
        tot = recommendations['total']
        buy_pct = (recommendations.get('strong_buy', 0) + recommendations.get('buy', 0)) / tot * 100
        if buy_pct >= 75:   c_score += 8
        elif buy_pct >= 60: c_score += 5
        elif buy_pct >= 50: c_score += 2
        elif buy_pct <= 30: c_score -= 6
        else:               c_score -= 2

    if upside is not None:
        if upside > 30:    c_score += 5
        elif upside > 15:  c_score += 3
        elif upside > 5:   c_score += 1
        elif upside < -15: c_score -= 5
        elif upside < -5:  c_score -= 2

    c_score = max(0, min(25, c_score))

    total = q_score + v_score + m_score + c_score

    # Etiqueta y color del score total
    if total >= 75:      label, color = "EXCELENTE", "#00ffad"
    elif total >= 60:    label, color = "BUENO",     "#7fffad"
    elif total >= 45:    label, color = "NEUTRAL",   "#ff9800"
    elif total >= 30:    label, color = "DÉBIL",     "#ff5722"
    else:                label, color = "NEGATIVO",  "#f23645"

    return {
        'total': total,
        'calidad':    q_score,
        'valoracion': v_score,
        'momentum':   m_score,
        'consenso':   c_score,
        'label': label,
        'color': color,
    }

# ────────────────────────────────────────────────
# CONTEXTO SECTORIAL — colores por sector
# ────────────────────────────────────────────────

def sector_metric_color(metric_name, value, sector, industry):
    """Devuelve color (#hex) para una métrica considerando el sector."""
    v = _safe(value)
    if v is None: return "#888"

    s = (sector or '').lower()
    ind = (industry or '').lower()

    # Thresholds por tipo de métrica y sector
    THRESHOLDS = {
        'pe': {
            'tech':    (20, 50), 'comm': (18, 45), 'fin': (8, 18),
            'util':    (12, 22), 'real': (12, 25), 'health': (15, 60),
            'default': (12, 28),
        },
        'roe': {
            'fin':     (0.10, 0.05), 'real': (0.08, 0.03),
            'default': (0.20, 0.08),
        },
        'net_margin': {
            'fin':     (0.18, 0.08), 'real': (0.10, 0.02),
            'util':    (0.08, 0.03), 'health': (0.12, 0.00),
            'default': (0.15, 0.05),
        },
        'de': {
            'fin':     (300, 600),   # bancos: D/E muy alto es normal
            'util':    (100, 200),
            'real':    (80, 200),
            'default': (50, 150),
        },
    }

    def _sector_key(s, ind):
        if 'technology' in s or 'software' in ind: return 'tech'
        if 'communication' in s: return 'comm'
        if 'financial' in s or 'bank' in ind: return 'fin'
        if 'utilities' in s: return 'util'
        if 'real estate' in s: return 'real'
        if 'health' in s or 'biotech' in ind: return 'health'
        return 'default'

    sk = _sector_key(s, ind)

    if metric_name == 'pe':
        thr = THRESHOLDS['pe'].get(sk, THRESHOLDS['pe']['default'])
        if v < thr[0]: return "#00ffad"
        if v > thr[1]: return "#f23645"
        return "#ff9800"

    elif metric_name == 'roe':
        thr = THRESHOLDS['roe'].get(sk, THRESHOLDS['roe']['default'])
        if v > thr[0]:  return "#00ffad"
        if v < thr[1]:  return "#f23645"
        return "#ff9800"

    elif metric_name == 'net_margin':
        thr = THRESHOLDS['net_margin'].get(sk, THRESHOLDS['net_margin']['default'])
        if v > thr[0]:  return "#00ffad"
        if v < thr[1]:  return "#f23645"
        return "#ff9800"

    elif metric_name == 'de':
        thr = THRESHOLDS['de'].get(sk, THRESHOLDS['de']['default'])
        if v < thr[0]:  return "#00ffad"
        if v > thr[1]:  return "#f23645"
        return "#ff9800"

    # Fallback genérico
    return "#888"

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

**DATOS CUANTITATIVOS DISPONIBLES (úsalos como base, no los ignores):**
{datos_cuantitativos}

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
* Contextualiza los ratios de valoración vs la mediana del sector (no uses thresholds genéricos — P/E 15 "barato" no aplica igual a tech que a utilities).

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
Mantén el estilo claro, profesional, directo y orientado a la toma de decisiones de inversión. Responde siempre en castellano."""

PROMPT_RSU_RAPIDO = """Analiza {t} en castellano. Sé directo y breve.

**DATOS ACTUALES (Yahoo Finance / FMP):**
{datos_cuantitativos}

Proporciona exactamente esto, usando los datos anteriores como base:

1. **SNAPSHOT** — Qué hace en 2 frases. Precio actual, capitalización, sector.
2. **VALORACIÓN** — P/E, PEG, P/S vs sector (no uses thresholds genéricos — contextualiza al sector). ¿Cara, barata o razonable?
3. **CALIDAD** — Márgenes, ROE, FCF. ¿Negocio de calidad?
4. **CATALIZADORES** — 3 razones para subir / 3 riesgos clave.
5. **VEREDICTO** — Score /10, recomendación (comprar/mantener/vender con convicción), target price razonado.

Responde en castellano. Sin preámbulos."""

# ────────────────────────────────────────────────
# CSS GLOBAL
# ────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');

        /* ── BASE ── */
        .stApp { background: #0c0e12 !important; }
        .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 100% !important; }

        /* ── TIPOGRAFÍA — VT323 solo para labels/KPIs, Inter para texto largo ── */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            color: #00ffad !important;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        h1 { font-size: 3.5rem !important; text-shadow: 0 0 20px #00ffad66; border-bottom: 2px solid #00ffad; padding-bottom: 15px; }
        h2 { font-size: 2.2rem !important; color: #00d9ff !important; border-left: 4px solid #00ffad; padding-left: 15px; margin-top: 30px !important; }
        h3 { font-size: 1.8rem !important; color: #ff9800 !important; }

        /* Párrafos con Inter para legibilidad en texto largo */
        p, li { font-family: 'Inter', -apple-system, sans-serif !important; color: #bbb !important; line-height: 1.7; font-size: 0.9rem; }
        strong { color: #00ffad !important; }

        /* ── VT labels ── */
        .vt-label { font-family: 'VT323', monospace; color: #666; font-size: 0.9rem; letter-spacing: 2px; }
        .landing-title { font-family: 'VT323', monospace; font-size: 5rem; color: #00ffad; text-shadow: 0 0 30px #00ffad55; border-bottom: 2px solid #00ffad33; padding-bottom: 10px; letter-spacing: 4px; }
        .landing-desc  { font-family: 'Space Grotesk', sans-serif; font-size: 0.95rem; color: #00d9ff; letter-spacing: 3px; text-transform: uppercase; }

        /* ── INPUT ── */
        .stTextInput > div > div > input {
            background: #0c0e12 !important; border: 1px solid #00ffad33 !important;
            border-radius: 6px !important; color: #00ffad !important;
            font-family: 'VT323', monospace !important; font-size: 1.6rem !important;
            text-align: center; letter-spacing: 4px; padding: 12px !important;
            transition: border-color 0.2s, box-shadow 0.2s !important;
        }
        .stTextInput > div > div > input:focus { border-color: #00ffad !important; box-shadow: 0 0 12px #00ffad22 !important; }
        .stTextInput label { font-family: 'VT323', monospace !important; color: #888 !important; font-size: 1rem !important; letter-spacing: 2px; }

        /* ── BOTONES ── */
        .stButton > button {
            background: linear-gradient(90deg, #00ffad, #00cc8a) !important;
            color: #000 !important; border: none !important; border-radius: 6px !important;
            font-family: 'Space Grotesk', sans-serif !important; font-size: 0.88rem !important;
            font-weight: 700 !important; letter-spacing: 2px !important; padding: 12px 28px !important;
            text-transform: uppercase !important; width: 100% !important;
            transition: box-shadow 0.2s, transform 0.1s !important;
        }
        .stButton > button:hover { box-shadow: 0 0 20px #00ffad44 !important; transform: translateY(-1px) !important; }
        .stButton > button:active { transform: translateY(0) !important; }
        .stDownloadButton > button {
            background: #0c0e12 !important; color: #00ffad !important;
            border: 1px solid #00ffad33 !important; border-radius: 6px !important;
            font-family: 'Space Grotesk', sans-serif !important; font-size: 0.82rem !important;
            letter-spacing: 2px !important; padding: 8px 20px !important;
            text-transform: uppercase !important; width: auto !important;
        }

        /* ── ANIMACIÓN FADEUP — módulos de entrada ── */
        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(12px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .mod-box, .ticker-box, .rsu-box {
            animation: fadeUp 0.25s ease-out both;
        }
        /* Escalonar animación en hijos directos para efecto cascada */
        .mod-box:nth-child(1) { animation-delay: 0.00s; }
        .mod-box:nth-child(2) { animation-delay: 0.04s; }
        .mod-box:nth-child(3) { animation-delay: 0.08s; }
        .mod-box:nth-child(4) { animation-delay: 0.12s; }

        /* ── MÓDULOS ── */
        .mod-box     { background: linear-gradient(135deg, #0c0e12 0%, #111520 100%); border: 1px solid #00ffad1a; border-radius: 8px; overflow: hidden; margin-bottom: 18px; box-shadow: 0 2px 20px #00000040; }
        .mod-header  { background: #0a0c10; padding: 12px 18px; border-bottom: 1px solid #00ffad1a; display: flex; justify-content: space-between; align-items: center; }
        .mod-title   { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.2rem; letter-spacing: 2px; text-transform: uppercase; margin: 0; }
        .mod-body    { padding: 18px; }

        /* ── TICKER HEADER ── */
        .ticker-box    { background: linear-gradient(135deg, #0a0c10 0%, #111520 100%); border: 1px solid #00ffad22; border-radius: 8px; padding: 18px 24px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 30px #00ffad08; flex-wrap: wrap; gap: 12px; }
        .ticker-name   { font-family: 'VT323', monospace; font-size: 2.4rem; color: #00ffad; letter-spacing: 3px; text-shadow: 0 0 10px #00ffad33; }
        .ticker-meta   { font-family: 'Inter', sans-serif; font-size: 11px; color: #555; margin-top: 4px; }
        .ticker-price  { font-family: 'VT323', monospace; font-size: 2.6rem; color: #fff; text-align: right; }
        .ticker-change { font-family: 'Space Grotesk', sans-serif; font-size: 0.95rem; font-weight: 600; text-align: right; }

        /* ── PUNTUACIÓN RSU ── */
        .rsu-score-box { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 16px; text-align: center; }
        .rsu-score-num { font-family: 'VT323', monospace; font-size: 3.5rem; letter-spacing: 2px; line-height: 1; }
        .rsu-score-label { font-family: 'Space Grotesk', sans-serif; font-size: 0.78rem; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; margin-top: 4px; }
        .rsu-score-sub { font-family: 'Inter', sans-serif; font-size: 0.72rem; color: #555; margin-top: 2px; }
        .score-bar-track { background: #0a0c10; border-radius: 4px; height: 5px; margin: 4px 0; overflow: hidden; }
        .score-bar-fill  { height: 100%; border-radius: 4px; transition: width 0.6s ease; }

        /* ── MÉTRICAS ── */
        .metric-box   { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 16px; position: relative; min-height: 100px; box-sizing: border-box; }
        .metric-tag   { position: absolute; top: 8px; right: 8px; background: #0f1e35; color: #00d9ff; padding: 1px 6px; border-radius: 4px; font-family: 'Space Grotesk', sans-serif; font-size: 0.7rem; font-weight: 600; letter-spacing: 1px; }
        .metric-label { font-family: 'VT323', monospace; color: #777; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .metric-value { font-family: 'VT323', monospace; font-size: 1.8rem; letter-spacing: 1px; }
        .metric-desc  { font-family: 'Inter', sans-serif; color: #444; font-size: 10px; margin-top: 3px; }
        /* Tooltip de contexto sectorial bajo la métrica */
        .metric-sector-note { font-family: 'Inter', sans-serif; font-size: 9px; color: #336; margin-top: 4px; font-style: italic; }

        /* ── PROFIT BOX ── */
        .profit-box   { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 14px 16px; }
        .profit-label { font-family: 'VT323', monospace; color: #777; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
        .profit-value { font-family: 'VT323', monospace; font-size: 1.6rem; }

        /* ── RATINGS ── */
        .rating-item  { margin-bottom: 14px; }
        .rating-top   { display: flex; justify-content: space-between; margin-bottom: 5px; }
        .rating-name  { font-family: 'VT323', monospace; color: #ccc; font-size: 1.05rem; letter-spacing: 1px; }
        .rating-count { font-family: 'VT323', monospace; font-size: 1.05rem; font-weight: bold; }
        .rating-bar   { background: #0a0c10; height: 7px; border-radius: 4px; overflow: hidden; }
        .rating-fill  { height: 100%; border-radius: 4px; }

        /* ── PRECIO OBJETIVO ── */
        .target-box   { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 24px; text-align: center; height: 100%; }
        .target-price { font-family: 'VT323', monospace; font-size: 3.2rem; color: #00ffad; text-shadow: 0 0 12px #00ffad33; }
        .target-label { font-family: 'Space Grotesk', sans-serif; color: #777; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }

        /* ── CONSENSUS ── */
        .consensus-box { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 24px; text-align: center; height: 100%; }

        /* ── EVENTOS ── */
        .event-row        { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #111520; }
        .event-row:last-child { border-bottom: none; }
        .event-label      { font-family: 'Space Grotesk', sans-serif; color: #888; font-size: 0.8rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
        .event-value      { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.05rem; }

        /* ── FONDOS ── */
        .fund-card        { background: #0a0c10; border: 1px solid #1a1e26; border-radius: 8px; padding: 16px 18px; margin-bottom: 10px; transition: border-color 0.15s; }
        .fund-card:hover  { border-color: #00ffad44; }
        .fund-name        { font-family: 'Inter', sans-serif; color: #fff; font-size: 0.88rem; font-weight: 500; letter-spacing: 0.5px; }

        /* ── SUGERENCIAS ── */
        .suggestion-item { background: #0a0c10; border-left: 2px solid #00ffad; padding: 12px 16px; margin-bottom: 8px; border-radius: 0 6px 6px 0; font-family: 'Inter', sans-serif; color: #bbb; font-size: 0.86rem; line-height: 1.6; }

        /* ── RSU BOX ── */
        .rsu-box  { background: linear-gradient(135deg, #0a0c10 0%, #111520 100%); border: 1px solid #00ffad33; border-radius: 8px; padding: 24px; margin: 18px 0; }
        .rsu-title { font-family: 'VT323', monospace; color: #00ffad; font-size: 1.5rem; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 10px; }

        /* ── ABOUT — Inter para texto largo ── */
        .about-text { font-family: 'Inter', sans-serif; color: #999; line-height: 1.8; font-size: 0.88rem; }

        /* ── HIGHLIGHT ── */
        .highlight-quote { background: #00ffad0a; border: 1px solid #00ffad22; border-radius: 8px; padding: 16px 20px; font-family: 'VT323', monospace; font-size: 1.2rem; color: #00ffad99; text-align: center; letter-spacing: 1px; margin: 16px 0; }

        /* ── TOOLTIP ── */
        .tip-box  { position: relative; cursor: help; z-index: 10; }
        .tip-icon { width: 20px; height: 20px; border-radius: 50%; background: #1a1e26; border: 1px solid #333; display: flex; align-items: center; justify-content: center; color: #666; font-size: 11px; font-weight: bold; }
        .tip-text { visibility: hidden; width: 260px; background: #111520; color: #bbb; text-align: left; padding: 12px; border-radius: 6px; position: fixed; z-index: 9999; opacity: 0; transition: opacity 0.2s; font-size: 11px; border: 1px solid #00ffad22; font-family: 'Inter', sans-serif; box-shadow: 0 4px 24px #00000080; pointer-events: none; }
        .tip-box:hover .tip-text { visibility: visible; opacity: 1; }

        /* ── TABS ── */
        .stTabs [data-baseweb="tab-list"]  { gap: 4px; background: #0a0c10; padding: 8px; border-radius: 8px; border: 1px solid #00ffad1a; margin-bottom: 16px; flex-wrap: wrap; }
        .stTabs [data-baseweb="tab"]        { background: transparent; color: #555; border-radius: 6px; padding: 8px 14px; font-family: 'Space Grotesk', sans-serif; font-size: 0.78rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; transition: color 0.15s; }
        .stTabs [aria-selected="true"]      { background: #00ffad !important; color: #000 !important; }

        /* ── DARK MODE — Streamlit DataFrames ── */
        [data-testid="stDataFrame"] { border: 1px solid #1a1e26 !important; border-radius: 8px !important; overflow: hidden !important; }
        [data-testid="stDataFrame"] table { background: #0a0c10 !important; }
        [data-testid="stDataFrame"] th { background: #111520 !important; color: #00ffad !important; font-family: 'Space Grotesk', sans-serif !important; font-size: 0.78rem !important; font-weight: 600 !important; letter-spacing: 1px !important; text-transform: uppercase !important; border-bottom: 1px solid #1a1e26 !important; }
        [data-testid="stDataFrame"] td { color: #bbb !important; font-family: 'Inter', sans-serif !important; font-size: 0.83rem !important; border-bottom: 1px solid #0f1218 !important; background: transparent !important; }
        [data-testid="stDataFrame"] tr:hover td { background: #111520 !important; }

        /* ── DARK MODE — Plotly charts ── */
        .js-plotly-plot .plotly .bg { fill: #0c0e12 !important; }

        /* ── MISC ── */
        hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00ffad33, transparent); margin: 24px 0; }
        .hq { background: #00ffad0a; border: 1px solid #00ffad22; border-radius: 8px; padding: 16px 20px; font-family: 'VT323', monospace; font-size: 1.2rem; color: #00ffad99; text-align: center; letter-spacing: 1px; }

        /* ── STREAMLIT CLEANUPS ── */
        [data-testid="stMetricValue"] { font-family: 'VT323', monospace; color: #00ffad; }
        div[data-testid="stVerticalBlock"] > div { margin-bottom: 0 !important; }
        .stSpinner > div { border-color: #00ffad !important; border-right-color: transparent !important; }
        [data-testid="stExpander"] { border: 1px solid #1a1e26 !important; border-radius: 8px !important; background: #0a0c10 !important; }
        [data-testid="stExpander"] summary { font-family: 'Space Grotesk', sans-serif !important; color: #888 !important; font-size: 0.82rem !important; font-weight: 600 !important; letter-spacing: 1px !important; }

        /* ── MOBILE RESPONSIVE ── */
        @media (max-width: 768px) {
            .landing-title { font-size: 3rem !important; }
            .ticker-box { flex-direction: column; align-items: flex-start; }
            .ticker-price { font-size: 2rem; }
            .ticker-change { font-size: 0.85rem; }
            .stTabs [data-baseweb="tab"] { font-size: 0.7rem !important; padding: 6px 8px !important; }
            .metric-value { font-size: 1.5rem !important; }
            .rsu-score-num { font-size: 2.5rem !important; }
            .mod-body { padding: 12px !important; }
        }
        @media (max-width: 480px) {
            .landing-title { font-size: 2.2rem !important; letter-spacing: 2px; }
            .ticker-name { font-size: 1.8rem !important; }
            .metric-box { min-height: 80px !important; }
        }
    </style>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    st.set_page_config(page_title="RSU Research", page_icon="🔬", layout="wide",
                       initial_sidebar_state="collapsed")
    inject_css()

    # Session state
    for k, v in [('last_ticker', ''), ('last_report', ''), ('last_report_ticker', '')]:
        if k not in st.session_state:
            st.session_state[k] = v

    # HEADER
    st.markdown("""
    <div style="text-align:center; margin-bottom:28px;">
        <div class="vt-label" style="margin-bottom:10px;">[CONEXIÓN SEGURA ESTABLECIDA // RSU ANALYTICS v5.0]</div>
        <div class="landing-title">🔬 RSU RESEARCH</div><br>
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
        # FMP: fuente primaria de fundamentales/ratios cuando está configurada
        fmp_data     = get_fmp_data(t_in, api_keys['fmp']) if api_keys['fmp'] else None
        # Finnhub: solo si hay API key — lazy (los datos de noticias se cargan aquí pero la tab los usa)
        finnhub_data = get_finnhub_data(t_in, api_keys['finnhub']) if api_keys['finnhub'] else None

    if not yf_data:
        st.error(f"❌ No se pudieron obtener datos para **'{t_in}'**.")

        # ── Debug log detallado ──
        debug_log  = st.session_state.get('_debug_log', [])
        if debug_log:
            with st.expander("🔍 Debug — ¿qué falló exactamente?", expanded=True):
                for step in debug_log:
                    color = "#00ffad" if step.startswith("✅") else ("#ff9800" if step.startswith("⚠️") else "#f23645")
                    st.markdown(
                        f'<div style="font-family:monospace;font-size:0.78rem;color:{color};'
                        f'padding:3px 0;border-bottom:1px solid #111;">{step}</div>',
                        unsafe_allow_html=True
                    )

        st.markdown("""
        <div style="background:#0a0c10;border:1px solid #1a1e26;border-radius:8px;padding:16px;margin-top:8px;">
            <div style="font-family:'Space Grotesk',sans-serif;font-size:0.8rem;color:#666;letter-spacing:1px;text-transform:uppercase;margin-bottom:10px;">Posibles causas</div>
            <div style="font-family:'Inter',sans-serif;font-size:0.84rem;color:#888;line-height:1.8;">
                ▸ El ticker no existe o está mal escrito (ej: <strong style="color:#00ffad;">AAPL</strong> no <strong style="color:#f23645;">apple</strong>)<br>
                ▸ Bolsa europea — añade sufijo (ej: <strong style="color:#00ffad;">IBE.MC</strong> BME, <strong style="color:#00ffad;">AMS.AS</strong> Amsterdam)<br>
                ▸ Yahoo Finance con problemas temporales — espera 30s y recarga<br>
                ▸ yfinance desactualizado — puede requerir actualización en el servidor
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Aplicar overrides FMP sobre datos yfinance (FMP más fiable para ratios)
    if fmp_data:
        yf_data = fmp_override_metrics(yf_data, fmp_data)

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

    # Earnings surprises: prioridad FMP > AV > yfinance
    fmp_surprises = (fmp_data or {}).get('earnings_surprises')
    earnings_surprises = fmp_surprises or av_surprises or yf_surprises

    # Sector/industry para contexto de colores
    sector   = info.get('sector', '')
    industry = info.get('industry', '')

    # Traduccción descripción
    translated_summary = translate_text_cached(info.get('longBusinessSummary', ''), t_in)

    # Segmentos y sentimiento de Finnhub
    segments  = process_finnhub_segments(finnhub_data) if finnhub_data else None
    sentiment = calculate_news_sentiment(finnhub_data) if finnhub_data else None

    # RSU Score
    rsu_score = compute_rsu_score(info, metrics, profitability, market, recommendations, target_data)

    # Cálculos header
    cp           = market.get('price') or 0
    prev_close   = market.get('prev_close') or cp
    price_change = ((cp - prev_close) / prev_close * 100) if prev_close else 0
    change_color = "#00ffad" if price_change >= 0 else "#f23645"
    change_arrow = "▲" if price_change >= 0 else "▼"
    market_cap   = market.get('market_cap') or 0
    spark_svg    = build_sparkline_svg(sparkline)

    # Fuente de datos activa (para el footer)
    data_sources = ["Yahoo Finance"]
    if fmp_data:    data_sources.append("FMP")
    if av_surprises: data_sources.append("Alpha Vantage")
    if finnhub_data: data_sources.append("Finnhub")

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
        <div style="display:flex; align-items:center; gap:20px; flex-wrap:wrap;">
            <div>{spark_svg}</div>
            <div>
                <div class="ticker-price">${cp:,.2f}</div>
                <div class="ticker-change" style="color:{change_color};">{change_arrow} {abs(price_change):.2f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── RSU PUNTUACIÓN + KPIs RÁPIDOS (jerarquía: información crítica arriba) ──
    score_col, k1, k2, k3, k4 = st.columns([1.2, 1, 1, 1, 1])
    sc = rsu_score
    with score_col:
        # Barras de sub-score
        bars_html = ""
        for label_b, val_b, color_b, tooltip_b in [
            ("CAL",  sc['calidad'],    "#00ffad", "Calidad: márgenes, ROE y FCF"),
            ("VAL",  sc['valoracion'], "#00d9ff", "Valoración: P/E vs sector, PEG"),
            ("MOM",  sc['momentum'],   "#ff9800", "Momentum: precio vs SMA50/200"),
            ("CON",  sc['consenso'],   "#9b59b6", "Consenso: analistas y upside"),
        ]:
            pct = val_b / 25 * 100
            bars_html += (
                f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;" title="{tooltip_b} ({val_b}/25 pts)">'
                f'<div style="font-family:Space Grotesk,sans-serif;color:#556;font-size:0.65rem;'
                f'font-weight:700;letter-spacing:1px;text-transform:uppercase;width:32px;flex-shrink:0;'
                f'cursor:default;" title="{tooltip_b}">{label_b}</div>'
                '<div style="flex:1;background:#0f1218;border-radius:3px;height:5px;overflow:hidden;">'
                f'<div style="width:{pct:.0f}%;height:100%;border-radius:3px;background:{color_b};"></div>'
                '</div>'
                f'<div style="font-family:VT323,monospace;color:{color_b};font-size:0.9rem;'
                f'width:22px;text-align:right;flex-shrink:0;">{val_b}</div>'
                '</div>'
            )
        score_html = (
            '<div class="rsu-score-box">'
            '<div style="display:flex;align-items:center;gap:14px;margin-bottom:12px;">'
            '<div>'
            f'<div class="rsu-score-num" style="color:{sc["color"]};">{sc["total"]}</div>'
            '<div style="font-family:Space Grotesk,sans-serif;font-size:0.65rem;color:#444;letter-spacing:1px;">/100</div>'
            '</div>'
            '<div style="flex:1;">'
            f'<div class="rsu-score-label" style="color:{sc["color"]};">{sc["label"]}</div>'
            '<div style="font-family:Inter,sans-serif;font-size:0.68rem;color:#444;margin-top:2px;">RSU Score</div>'
            '</div>'
            '</div>'
            + bars_html +
            '</div>'
        )
        st.markdown(score_html, unsafe_allow_html=True)

    # KPIs rápidos top
    sma200 = market.get('sma_200')
    sma50  = market.get('sma_50')
    vs_sma200 = ((cp - sma200) / sma200 * 100) if (cp and sma200) else None
    vs_sma50  = ((cp - sma50)  / sma50  * 100) if (cp and sma50)  else None

    with k1:
        pe_val = metrics.get('trailing_pe')
        pe_color = sector_metric_color('pe', pe_val, sector, industry)
        pe_note = f"Sector: {sector.split(' ')[0].title()}" if sector else ""
        st.markdown(f"""
        <div class="metric-box" style="animation:fadeUp 0.2s ease-out 0.05s both;">
            <div class="metric-label">P/E Trailing</div>
            <div class="metric-value" style="color:{pe_color};">{fmt_x(pe_val) if pe_val else 'N/D'}</div>
            <div class="metric-sector-note">{pe_note}</div>
        </div>""", unsafe_allow_html=True)

    with k2:
        nm = profitability.get('net_margin')
        nm_color = sector_metric_color('net_margin', nm, sector, industry)
        st.markdown(f"""
        <div class="metric-box" style="animation:fadeUp 0.2s ease-out 0.08s both;">
            <div class="metric-label">Margen Neto</div>
            <div class="metric-value" style="color:{nm_color};">{fmt_pct(nm, 100) if nm is not None else 'N/D'}</div>
            <div class="metric-sector-note">Sector: {sector.split(' ')[0].title() if sector else 'N/A'}</div>
        </div>""", unsafe_allow_html=True)

    with k3:
        vs200_color = "#00ffad" if (vs_sma200 or 0) >= 0 else "#f23645"
        vs200_str   = f"{'+' if (vs_sma200 or 0) >= 0 else ''}{vs_sma200:.1f}%" if vs_sma200 is not None else "N/D"
        st.markdown(f"""
        <div class="metric-box" style="animation:fadeUp 0.2s ease-out 0.11s both;">
            <div class="metric-label">vs SMA 200</div>
            <div class="metric-value" style="color:{vs200_color};">{vs200_str}</div>
            <div class="metric-sector-note">Tendencia largo plazo</div>
        </div>""", unsafe_allow_html=True)

    with k4:
        upside = target_data.get('upside')
        up_color = "#00ffad" if (upside or 0) > 0 else "#f23645"
        up_str   = f"{'+' if (upside or 0) >= 0 else ''}{upside:.1f}%" if upside is not None else "N/D"
        st.markdown(f"""
        <div class="metric-box" style="animation:fadeUp 0.2s ease-out 0.14s both;">
            <div class="metric-label">Potencial</div>
            <div class="metric-value" style="color:{up_color};">{up_str}</div>
            <div class="metric-sector-note">vs. precio objetivo</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

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
            <div class="tip-box" style="display:inline-flex;margin-left:6px;"><div class="tip-icon">?</div><div class="tip-text">Gráfico TradingView interactivo con RSI, Media Móvil y MACD. Puedes cambiar timeframe y añadir indicadores.</div></div>
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
        "📉 Earnings Analysis",
        "🎯 Earnings Surprises",
        "📅 Eventos & Calendario",
        "🏦 Fondos Institucionales",
        "📰 Noticias & Sentimiento",
        "📅 Estacionalidad",
    ])

    # ══ TAB 1: VALORACIÓN ══
    with tabs[0]:
        def valuation_color(name, val):
            v = _safe(val)
            if v is None: return "#888"
            if v < 0: return "#f23645"
            # P/E — sector-aware via the global function
            if name == "P/E":        return sector_metric_color('pe', v, sector, industry)
            if name == "Forward P/E": return sector_metric_color('pe', v, sector, industry)
            # Other metrics: use fixed thresholds (no sectorial distortion for these)
            thresholds = {
                "P/S": (2, 8), "EV/EBITDA": (10, 20), "PEG Ratio": (1, 2), "P/B": (1, 4),
            }
            lo, hi = thresholds.get(name, (0, 9999))
            if v <= lo: return "#00ffad"
            if v >= hi: return "#f23645"
            return "#ff9800"

        # Nota de contexto sectorial bajo el tab de valoración
        sector_note = ""
        if sector:
            sector_note = f'<div style="font-family:Inter,sans-serif;font-size:0.76rem;color:#444;margin-bottom:12px;border-left:3px solid #1a2e40;padding-left:10px;">Umbrales P/E ajustados para sector <strong style="color:#00d9ff;">{sector}</strong>. Los colores reflejan si la valoración es barata, razonable o cara <em>para este sector</em>, no con thresholds genéricos.</div>'
        st.markdown(sector_note, unsafe_allow_html=True)

        def fmt_val_metric(val, name=""):
            """
            Formatea un múltiplo de valoración.
            - P/E negativo = empresa en pérdidas (válido, mostrar en naranja con nota)
            - EV/EBITDA negativo = EBITDA negativo (válido, mostrar en naranja)
            - None = dato no disponible (N/D gris)
            """
            v = _safe(val)
            if v is None:
                return "N/D", "#555"
            if v < 0:
                if name in ("P/E", "Forward P/E"):
                    return f"{v:.2f}×", "#ff9800"   # naranja: empresa en pérdidas
                if name == "EV/EBITDA":
                    return f"{v:.2f}×", "#ff9800"   # naranja: EBITDA negativo
                return f"{v:.2f}×", "#f23645"
            return f"{v:.2f}×", valuation_color(name, v)

        valuation_data = [
            ("P/E",         metrics['trailing_pe'],    "Trailing",    "N/D = empresa en pérdidas (EPS negativo)"),
            ("P/S",         metrics['price_to_sales'], "TTM",         "Precio / Ventas"),
            ("EV/EBITDA",   metrics['ev_ebitda'],      "TTM",         "Negativo = EBITDA negativo"),
            ("Forward P/E", metrics['forward_pe'],     "Próx. 12M",   "Precio / BPA estimado próximos 12M"),
            ("PEG Ratio",   metrics['peg_ratio'],      "P/E ÷ Crec.", "Valoración ajustada al crecimiento"),
            ("P/B",         metrics['price_to_book'],  "Actual",      "Precio / Valor en Libros"),
        ]

        rows_html = ""
        for i in range(0, len(valuation_data), 3):
            chunk = valuation_data[i:i+3]
            cells = ""
            for label, val, tag, desc in chunk:
                disp, color = fmt_val_metric(val, label)
                cells += (
                    '<div style="flex:1;min-width:0;">'
                    f'<div class="metric-box"><span class="metric-tag">{tag}</span>'
                    f'<div class="metric-label">{label}</div>'
                    f'<div class="metric-value" style="color:{color};">{disp}</div>'
                    f'<div class="metric-desc">{desc}</div>'
                    '</div></div>'
                )
            for _ in range(3 - len(chunk)):
                cells += '<div style="flex:1;min-width:0;"></div>'
            rows_html += f'<div style="display:flex;gap:10px;margin-bottom:10px;">{cells}</div>'

        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">💵 Múltiplos de Valoración</span>
                <div class="tip-box" style="display:inline-flex;margin-left:6px;"><div class="tip-icon">?</div><div class="tip-text">Verde = barato · Naranja = valoración media · Rojo = caro. Umbrales estándar de análisis fundamental.</div></div>
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

        # ROE threshold: sector-aware
        roe_color = sector_metric_color('roe', roe, sector, industry)
        nm_color  = sector_metric_color('net_margin', nm, sector, industry)
        de_color  = sector_metric_color('de', de, sector, industry)

        profit_items = [
            ("ROE",              fmt_pct(roe, 100),  roe_color,  "Rentabilidad s/ Fondos Propios — umbral por sector"),
            ("ROA",              fmt_pct(roa, 100),  pc(roa, 0.10, 0.02), "Rentabilidad s/ Activos"),
            ("Margen Neto",      fmt_pct(nm, 100),   nm_color,   "Beneficio Neto / Ingresos — umbral por sector"),
            ("Margen Operativo", fmt_pct(om, 100),   pc(om, 0.15, 0.0),   "EBIT / Ingresos"),
            ("Margen Bruto",     fmt_pct(gm, 100),   pc(gm, 0.40, 0.20),  "Beneficio Bruto / Ingresos"),
            ("Crec. Ingresos",   fmt_pct(rg, 100),   pc(rg, 0.10, 0.0),   "Crecimiento YoY"),
            ("Crec. Beneficios", fmt_pct(eg, 100),   pc(eg, 0.10, 0.0),   "Crecimiento YoY EPS"),
            ("Deuda/Capital",    f"{de:.1f}%" if de is not None else "N/D",
                de_color, "Ratio Apalancamiento — umbral por sector"),
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

        sector_rentab_note = f'<div style="font-family:Inter,sans-serif;font-size:0.76rem;color:#444;margin-bottom:12px;border-left:3px solid #1a2e40;padding-left:10px;">ROE, Margen Neto y D/E coloreados con umbrales de sector <strong style="color:#00d9ff;">{sector or "N/A"}</strong>. Otros ratios usan thresholds fundamentales estándar.</div>' if sector else ""

        st.markdown(f"""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">📈 Rentabilidad y Salud Financiera</span>
                <div class="tip-box" style="display:inline-flex;margin-left:6px;"><div class="tip-icon">?</div><div class="tip-text">Verde = bueno · Naranja = neutral · Rojo = precaución. ROE y Márgenes ajustados al sector: un ROE del 8% es excelente para un banco pero débil para tech.</div></div>
            </div>
            <div class="mod-body">{sector_rentab_note}{rows_html}</div>
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
            st.plotly_chart(fig_gauge, use_container_width=True, key="gauge_rsu_score")
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
                cols_map = {'strongBuy': 'C.Fuerte', 'buy': 'Comprar', 'hold': 'Mantener',
                            'sell': 'Vender', 'strongSell': 'V.Fuerte', 'period': 'Período'}
                df_r = rec_summary.rename(columns=cols_map)
                # Build pure HTML table to keep it inside mod-box
                th_style = 'padding:8px 14px;font-family:Space Grotesk,sans-serif;font-size:0.68rem;color:#555;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #1a1e26;text-align:right;'
                thead = '<tr>' + ''.join(f'<th style="{th_style}text-align:{"left" if i==0 else "right"}">{c}</th>' for i,c in enumerate(df_r.columns)) + '</tr>'
                rows_html = ''
                for _, row in df_r.iterrows():
                    cells = ''
                    for i,v in enumerate(row):
                        td = f'padding:7px 14px;font-family:{"Inter" if i==0 else "monospace"},sans-serif;font-size:{"0.8" if i==0 else "0.85"}rem;color:{"#888" if i==0 else "#ccc"};border-bottom:1px solid #0f1218;text-align:{"left" if i==0 else "right"};'
                        cells += f'<td style="{td}">{v}</td>'
                    rows_html += f'<tr>{cells}</tr>'
                rec_html = (
                    '<div class="mod-box">'
                    '<div class="mod-header"><span class="mod-title">📆 Histórico de Recomendaciones (últimos 6 meses)</span></div>'
                    '<div class="mod-body" style="overflow-x:auto;padding:0;">'
                    f'<table style="width:100%;border-collapse:collapse;">'
                    f'<thead>{thead}</thead><tbody>{rows_html}</tbody>'
                    '</table></div></div>'
                )
                st.markdown(rec_html, unsafe_allow_html=True)
        else:
            st.info("No hay recomendaciones de analistas disponibles.")

    # ══ TAB 4: EARNINGS ANALYSIS ══
    with tabs[4]:
        st.markdown("""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-icon">📉</span>
                <div>
                    <div class="mod-title">Earnings Analysis</div>
                    <div style="font-family:Inter,sans-serif;color:#555;font-size:0.75rem;">
                        Métricas de rendimiento y reacción histórica a earnings
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        ea_surprises = earnings_surprises or []
        next_earnings = events.get('Earnings Date') if events else None

        if not ea_surprises:
            st.info("No hay datos de earnings históricos disponibles para este ticker.")
        else:
            import numpy as np

            # ── Build reaction metrics from surprises ──
            n_q = min(len(ea_surprises), 8)
            recent = ea_surprises[:n_q]

            # EPS beats
            eps_beats = sum(1 for e in recent if (e.get('surprise_pct') or 0) > 0)

            # For gap/price reaction we use hist_1y if available
            reactions = []
            if hist_1y is not None and not hist_1y.empty:
                for surp in recent:
                    try:
                        rd = surp.get('report_date') or surp.get('date')
                        if not rd: continue
                        import pandas as pd
                        rd_ts = pd.Timestamp(str(rd))
                        idx = hist_1y.index.searchsorted(rd_ts)
                        if idx >= len(hist_1y) or idx == 0: continue
                        pre_close = float(hist_1y['Close'].iloc[idx-1])
                        open_price = float(hist_1y['Open'].iloc[idx]) if idx < len(hist_1y) else None
                        d3_close  = float(hist_1y['Close'].iloc[min(idx+2, len(hist_1y)-1)])
                        gap_pct   = (open_price - pre_close)/pre_close*100 if open_price else None
                        d3_pct    = (d3_close   - pre_close)/pre_close*100
                        high_pct  = (float(hist_1y['High'].iloc[idx]) - pre_close)/pre_close*100
                        low_pct   = (float(hist_1y['Low'].iloc[idx])  - pre_close)/pre_close*100
                        reactions.append({
                            'quarter': surp.get('quarter',''),
                            'date': str(rd)[:10],
                            'surprise': surp.get('surprise_pct',0) or 0,
                            'gap': gap_pct, 'high': high_pct,
                            'low': low_pct, 'd3': d3_pct,
                        })
                    except Exception:
                        pass

            avg_gap = np.mean([r['gap'] for r in reactions if r['gap'] is not None]) if reactions else None
            gap_vol = np.std( [r['gap'] for r in reactions if r['gap'] is not None]) if reactions and len(reactions)>1 else None
            avg_d3  = np.mean([r['d3'] for r in reactions]) if reactions else None

            # Scores (0-100)
            gup_score   = max(0,min(100, int((avg_gap or 0)*5 + 50)))
            eps_score   = int(eps_beats/n_q*100)
            fade_score  = max(0,min(100, int((avg_d3 or 0)*3 + 50))) if avg_d3 is not None else 50
            consistency = max(0,min(100, int(100 - (gap_vol or 5)*8))) if gap_vol is not None else 50
            overall     = int(consistency*0.3 + gup_score*0.3 + fade_score*0.2 + eps_score*0.2)

            # ── Snapshot header ──
            next_str = ""
            if next_earnings:
                try:
                    from datetime import datetime as _dt
                    ne = next_earnings[0] if isinstance(next_earnings, list) else next_earnings
                    next_str = str(ne)[:10]
                except Exception:
                    next_str = str(next_earnings)[:10]

            def _fc(v, pos_green=True):
                """Color for percentage value."""
                if v is None: return "#888"
                return "#00ffad" if (v > 0) == pos_green else "#f23645"

            def _fp(v, decimals=1):
                if v is None: return "N/D"
                return f"{v:+.{decimals}f}%"

            # ── Snapshot bar ──
            st.markdown(f"""
            <div style="background:#0c0e14;border:1px solid #1a1e26;border-radius:8px;
                        padding:16px 20px;margin-bottom:12px;display:flex;
                        flex-wrap:wrap;justify-content:space-between;align-items:center;gap:12px;">
                <div>
                    <div style="font-family:Space Grotesk,sans-serif;color:#555;font-size:0.7rem;
                                letter-spacing:1px;text-transform:uppercase;">Snapshot</div>
                    <div style="font-family:VT323,monospace;color:#00ffad;font-size:1.1rem;">
                        Reacción a earnings (últimos {n_q})
                    </div>
                    <div style="font-family:Inter,sans-serif;color:#444;font-size:0.72rem;">
                        Perfil sesgo alcista · KPIs basados en la ventana de análisis
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-family:Space Grotesk,sans-serif;color:#555;font-size:0.7rem;
                                letter-spacing:1px;text-transform:uppercase;">Next Earnings</div>
                    <div style="font-family:VT323,monospace;color:#00d9ff;font-size:1.3rem;">
                        {next_str if next_str else "N/D"}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── 4 KPI cards + radar ──
            col_radar, col_kpis = st.columns([3, 2])

            with col_radar:
                radar_vals = [gup_score, eps_score, consistency, fade_score,
                              max(0,min(100,int((avg_d3 or 0)*3+50)))]
                radar_labels = ["Gap-up","EPS Beats","Consistencia","Fade Resist.","+3D"]
                fig_radar = go.Figure(go.Scatterpolar(
                    r=radar_vals + [radar_vals[0]],
                    theta=radar_labels + [radar_labels[0]],
                    fill='toself',
                    fillcolor='rgba(0,255,173,0.07)',
                    line=dict(color='#00ffad', width=2),
                    marker=dict(color='#00ffad', size=6)
                ))
                fig_radar.update_layout(
                    polar=dict(
                        bgcolor='#0a0c10',
                        radialaxis=dict(range=[0,100], showticklabels=True,
                                        tickvals=[20,40,60,80,100],
                                        tickfont=dict(size=8,color='#444'),
                                        gridcolor='#1a1e26', linecolor='#1a1e26'),
                        angularaxis=dict(tickfont=dict(size=10,color='#888'),
                                         gridcolor='#1a1e26', linecolor='#1a1e26')
                    ),
                    paper_bgcolor='#0c0e12', plot_bgcolor='#0c0e12',
                    font=dict(color='white', family='Space Grotesk'),
                    showlegend=False,
                    margin=dict(l=70, r=70, t=50, b=50),
                    height=320
                )
                st.plotly_chart(fig_radar, use_container_width=True, key="radar_earnings")

            with col_kpis:
                def _kpi(label, value, sub="", color="#00ffad"):
                    return (
                        f'<div style="background:#0a0c10;border:1px solid #1a1e26;border-radius:8px;'
                        f'padding:14px 16px;margin-bottom:8px;">'
                        f'<div style="font-family:Space Grotesk,sans-serif;color:#555;font-size:0.65rem;'
                        f'letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">{label}</div>'
                        f'<div style="font-family:VT323,monospace;color:{color};font-size:1.9rem;line-height:1.1;">{value}</div>'
                        f'<div style="font-family:Inter,sans-serif;color:#444;font-size:0.72rem;margin-top:2px;">{sub}</div>'
                        f'</div>'
                    )
                ov_color = "#00ffad" if overall>=60 else ("#ff9800" if overall>=40 else "#f23645")
                st.markdown(
                    _kpi("Puntuación Total", f"{overall}/100", "Consistencia · Gap · Fade · EPS", ov_color) +
                    _kpi("Batidos EPS", f"{eps_beats} / {n_q}", "Batidos en el período",
                         "#00ffad" if eps_beats/n_q>=0.6 else "#ff9800") +
                    _kpi("Gap Medio (Apertura)", _fp(avg_gap), "Vs. cierre pre-publicación",
                         _fc(avg_gap)) +
                    _kpi("Volatilidad Gap (σ)", f"{gap_vol:.2f} pp" if gap_vol is not None else "N/D",
                         "Desv. est. del gap de apertura", "#00d9ff"),
                    unsafe_allow_html=True
                )

            # ── History table ──
            if reactions:
                _hist_header = (
                    '<div style="background:#0c0e14;border:1px solid #1a1e26;border-radius:8px;padding:14px 18px;margin-top:8px;">'
                    '<div style="font-family:Space Grotesk,sans-serif;color:#555;font-size:0.7rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Historial</div>'
                    '<div style="font-family:VT323,monospace;color:#ccc;font-size:1rem;margin-bottom:12px;">Tabla de reacciones a earnings</div>'
                )

                def _cell(v, green_if_pos=True):
                    if v is None: return '<td style="color:#444;text-align:right;padding:6px 10px;">—</td>'
                    c = "#00ffad" if (v>0)==green_if_pos else "#f23645"
                    bg = "rgba(0,255,173,0.06)" if v>0 else "rgba(242,54,69,0.06)"
                    return f'<td style="color:{c};background:{bg};text-align:right;padding:6px 10px;font-family:monospace;font-size:0.82rem;">{v:+.1f}%</td>'

                rows = ""
                for r in reactions:
                    rows += (
                        f'<tr style="border-bottom:1px solid #0f1218;">'
                        f'<td style="padding:6px 10px;font-family:Space Grotesk,sans-serif;color:#888;font-size:0.78rem;">{r["quarter"]}</td>'
                        f'<td style="padding:6px 10px;font-family:monospace;color:#555;font-size:0.75rem;">{r["date"]}</td>'
                        + _cell(r["gap"]) + _cell(r["high"]) + _cell(r["low"])
                        + _cell(r["d3"]) +
                        f'<td style="padding:6px 10px;text-align:right;font-family:monospace;font-size:0.8rem;'
                        f'color:{"#00ffad" if r["surprise"]>0 else "#f23645"};">{r["surprise"]:+.1f}%</td>'
                        f'</tr>'
                    )
                st.markdown(
                    _hist_header +
                    '<div style="overflow-x:auto;">'
                    '<table style="width:100%;border-collapse:collapse;">'
                    '<thead><tr style="border-bottom:1px solid #1a1e26;">'
                    '<th style="text-align:left;padding:6px 10px;font-family:Space Grotesk,sans-serif;color:#555;font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;">Trimestre</th>'
                    '<th style="text-align:left;padding:6px 10px;font-family:Space Grotesk,sans-serif;color:#555;font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;">Fecha</th>'
                    '<th style="text-align:right;padding:6px 10px;font-family:Space Grotesk,sans-serif;color:#555;font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;">Gap Apertura</th>'
                    '<th style="text-align:right;padding:6px 10px;font-family:Space Grotesk,sans-serif;color:#555;font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;">Alto</th>'
                    '<th style="text-align:right;padding:6px 10px;font-family:Space Grotesk,sans-serif;color:#555;font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;">Bajo</th>'
                    '<th style="text-align:right;padding:6px 10px;font-family:Space Grotesk,sans-serif;color:#555;font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;">+3D</th>'
                    '<th style="text-align:right;padding:6px 10px;font-family:Space Grotesk,sans-serif;color:#555;font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;">Sorpresa EPS</th>'
                    f'</tr></thead><tbody>{rows}</tbody>'
                    '</table></div></div>',
                    unsafe_allow_html=True)


    # ══ TAB 5: EARNINGS SURPRISES ══
    with tabs[5]:
        if earnings_surprises and len(earnings_surprises) > 0:
            source_label = "Alpha Vantage" if av_surprises else "Yahoo Finance"
            st.markdown(f"""
            <div class="mod-box">
                <div class="mod-header">
                    <span class="mod-title">🎯 Historial de Earnings Surprises</span>
                    <span style="font-family:'Courier New',monospace;color:#555;font-size:11px;">Fuente: {source_label}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div style="border:1px solid #1a1e26;border-top:none;border-radius:0 0 10px 10px;padding:16px 20px;background:#0a0c10;margin-bottom:12px;">', unsafe_allow_html=True)

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
            st.plotly_chart(fig_surp, use_container_width=True, key="surp_chart")

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

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            if not api_keys['alpha_vantage']:
                st.warning("⚠️ Configura **ALPHA_VANTAGE_API_KEY** para obtener datos precisos de earnings surprises.")
            st.info("No hay datos de earnings surprises disponibles para este ticker.")

    # ══ TAB 6: EVENTOS & CALENDARIO ══
    with tabs[6]:
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
    with tabs[7]:
        st.markdown("""
        <div class="mod-box">
            <div class="mod-header">
                <span class="mod-title">🏦 Fondos Institucionales — Declaraciones 13F (SEC)</span>
                <div class="tip-box" style="display:inline-flex;margin-left:6px;"><div class="tip-icon">?</div><div class="tip-text">Datos reales de declaraciones trimestrales obligatorias a la SEC (formulario 13F). Muestra qué fondos institucionales tienen posición en esta empresa y cuántas acciones declararon. Fuente: Yahoo Finance / SEC EDGAR.</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="border:1px solid #1a1e26;border-top:none;border-radius:0 0 10px 10px;padding:16px 20px;background:#0a0c10;margin-bottom:12px;">', unsafe_allow_html=True)

        # Usar datos ya cargados en get_yfinance_full — sin llamada extra a Yahoo Finance
        holders_data = inst_data_preload if inst_data_preload else get_institutional_holders(t_in)

        if holders_data:
            major = holders_data.get('major')
            inst  = holders_data.get('institutional')
            mf    = holders_data.get('mutual_funds')

            if major is not None and not major.empty:
                try:
                    def _fmt_pct_major(val):
                        if val is None: return "N/D"
                        try:
                            v = float(val)
                            if 0 <= v <= 1.5:   return f"{v*100:.1f}%"
                            elif 0 < v <= 100:  return f"{v:.1f}%"
                            return "N/D"
                        except:
                            return str(val)

                    def _lookup_major(df, *labels):
                        """
                        yfinance major_holders: col 0 = numeric value, col 1 = label text.
                        Searches col 1 for label keywords, returns col 0 value.
                        Falls back to positional index if label not found.
                        """
                        if df is None or df.empty: return None
                        # Col 1 contains the description, col 0 contains the value
                        label_col = 1 if len(df.columns) > 1 else 0
                        val_col   = 0
                        for lbl in labels:
                            try:
                                mask = df.iloc[:, label_col].astype(str).str.lower().str.contains(lbl.lower(), na=False)
                                if mask.any():
                                    return df.loc[mask].iloc[0, val_col]
                            except Exception:
                                pass
                        return None

                    # yfinance major_holders typical rows:
                    # 0: % insiders held, 1: % institutions held,
                    # 2: % float held by institutions, 3: # of institutions holding shares
                    raw_inst   = (_lookup_major(major, 'institution', 'institutions held')
                                  or (major.iloc[1, 0] if len(major) > 1 else None))
                    raw_retail = (_lookup_major(major, 'float', 'retail', 'insiders')
                                  or (major.iloc[0, 0] if len(major) > 0 else None))
                    pct_inst   = _fmt_pct_major(raw_inst)
                    pct_retail = _fmt_pct_major(raw_retail)
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
                           'Date Fecha': 'Fecha', '% Out': '% del Float', 'Value': 'Valor (USD)'}
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
                              'Date Fecha': 'Fecha', '% Out': '% del Float', 'Value': 'Valor (USD)'}
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
        st.markdown('</div>', unsafe_allow_html=True)

    # ══ TAB 8: NOTICIAS & SENTIMIENTO ══
    with tabs[8]:
        if not api_keys['finnhub']:
            st.markdown("""
            <div class="mod-box"><div class="mod-body">
                <div style="font-family:Inter,sans-serif;color:#555;font-size:0.84rem;padding:20px;text-align:center;">
                    ⚙️ Configura <strong style="color:#00ffad;">FINNHUB_API_KEY</strong> en los secrets para activar este módulo.<br>
                    <span style="color:#333;font-size:11px;margin-top:8px;display:block;">finnhub.io — plan gratuito con 60 req/min.</span>
                </div>
            </div></div>
            """, unsafe_allow_html=True)
        else:
            col_sent, col_news = st.columns([1, 2])

            # ── Sentimiento ──
            with col_sent:
                if sentiment:
                    import math as _math
                    sent_val   = sentiment.get('overall_sentiment', 'neutral')
                    score      = sentiment.get('sentiment_score', 0)
                    bull_pct   = sentiment.get('bullish_pct', 0)
                    bear_pct   = sentiment.get('bearish_pct', 0)
                    news_count = sentiment.get('news_count', 0)
                    analyzed   = sentiment.get('analyzed_count', 0)
                    sent_colors = {'alcista': '#00ffad', 'bajista': '#f23645', 'neutral': '#ff9800'}
                    sent_color  = sent_colors.get(sent_val, '#888')
                    gauge_val   = round(max(-1.0, min(1.0, score)) * 100, 1)

                    # ── Plotly Indicator gauge ──
                    fig_sent = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=gauge_val,
                        number={'font': {'size': 42, 'color': sent_color, 'family': 'VT323, monospace'},
                                'valueformat': '.0f'},
                        gauge={
                            'axis': {
                                'range': [-100, 100],
                                'tickvals': [-100, -50, 0, 50, 100],
                                'ticktext': ['-100', '-50', '0', '50', '100'],
                                'tickfont': {'size': 11, 'color': '#555'},
                                'tickcolor': '#333',
                            },
                            'bar': {'color': sent_color, 'thickness': 0.28},
                            'bgcolor': '#0a0c10',
                            'borderwidth': 0,
                            'steps': [
                                {'range': [-100, -35], 'color': '#2a0d0d'},
                                {'range': [-35,   35], 'color': '#141408'},
                                {'range': [35,   100], 'color': '#0a1e10'},
                            ],
                            'threshold': {
                                'line': {'color': sent_color, 'width': 4},
                                'thickness': 0.8,
                                'value': gauge_val,
                            },
                        },
                        domain={'x': [0, 1], 'y': [0, 1]},
                    ))
                    fig_sent.update_layout(
                        paper_bgcolor='#0d0f16',
                        font={'color': '#888', 'family': 'Space Grotesk, sans-serif'},
                        margin=dict(l=20, r=20, t=20, b=5),
                        height=190,
                    )
                    kpi_row = (
                        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:10px;">'
                        '<div style="text-align:center;background:#0a0c10;border:1px solid #1a1e26;border-radius:6px;padding:8px 4px;">'
                        '<div style="font-family:Space Grotesk,sans-serif;color:#555;font-size:0.6rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;">SEÑAL</div>'
                        '<div style="font-family:VT323,monospace;color:' + sent_color + ';font-size:1.2rem;">' + sent_val.upper() + '</div>'
                        '</div>'
                        '<div style="text-align:center;background:#0a0c10;border:1px solid #1a1e26;border-radius:6px;padding:8px 4px;">'
                        '<div style="font-family:Space Grotesk,sans-serif;color:#555;font-size:0.6rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;">ALCISTA</div>'
                        '<div style="font-family:VT323,monospace;color:#00ffad;font-size:1.2rem;">' + f"{bull_pct:.0f}%" + '</div>'
                        '</div>'
                        '<div style="text-align:center;background:#0a0c10;border:1px solid #1a1e26;border-radius:6px;padding:8px 4px;">'
                        '<div style="font-family:Space Grotesk,sans-serif;color:#555;font-size:0.6rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;">BAJISTA</div>'
                        '<div style="font-family:VT323,monospace;color:#f23645;font-size:1.2rem;">' + f"{bear_pct:.0f}%" + '</div>'
                        '</div></div>'
                        '<div style="font-family:Inter,sans-serif;color:#444;font-size:0.68rem;margin-top:8px;text-align:center;">'
                        + str(analyzed) + ' titulares de ' + str(news_count) + ' analizados'
                        '</div>'
                    )
                    st.markdown(
                        '<div class="mod-box">'
                        '<div class="mod-header"><span class="mod-title">📊 Sentimiento</span>'
                        '<div class="tip-box" style="display:inline-flex;margin-left:6px;"><div class="tip-icon">?</div><div class="tip-text">Análisis de titulares Finnhub (últimos 30 días). Score de -100 (muy bajista) a +100 (muy alcista).</div></div>'
                        '</div><div class="mod-body" style="padding:8px 12px 12px;">',
                        unsafe_allow_html=True)
                    st.plotly_chart(fig_sent, use_container_width=True,
                                    config={'displayModeBar': False}, key='gauge_sentiment')
                    st.markdown(kpi_row + '</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="mod-box"><div class="mod-body">
                        <div style="font-family:Inter,sans-serif;color:#555;font-size:0.84rem;padding:20px;text-align:center;">
                            Sin datos de sentimiento para este ticker.
                        </div>
                    </div></div>
                    """, unsafe_allow_html=True)

            # ── Noticias ──
            with col_news:
                articles = []
                if sentiment and sentiment.get('articles'):
                    articles = sentiment['articles']
                elif finnhub_data and finnhub_data.get('news'):
                    articles = finnhub_data['news'][:15]

                if articles:
                    news_items = ""
                    for art in articles[:12]:
                        headline = html.escape(art.get('headline', 'Sin título')[:110])
                        source   = html.escape(art.get('source', ''))
                        url      = art.get('url', '#')
                        ts_raw   = art.get('datetime', 0)
                        try:
                            from datetime import datetime as _dt
                            ts_str = _dt.fromtimestamp(int(ts_raw)).strftime('%d %b')
                        except Exception:
                            ts_str = ''
                        news_items += (
                            '<div style="padding:9px 0;border-bottom:1px solid #0f1218;">'
                            '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">'
                            f'<a href="{url}" target="_blank" '
                            'style="font-family:Courier New,monospace;color:#bbb;font-size:11.5px;'
                            'line-height:1.5;text-decoration:none;flex:1;">'
                            f'{headline}</a>'
                            '<div style="flex-shrink:0;text-align:right;min-width:52px;">'
                            f'<div style="font-family:VT323,monospace;color:#444;font-size:0.8rem;">{ts_str}</div>'
                            f'<div style="font-family:Inter,sans-serif;color:#333;font-size:9px;">{source}</div>'
                            '</div></div></div>'
                        )
                    st.markdown(f"""
                    <div class="mod-box">
                        <div class="mod-header">
                            <span class="mod-title">📰 Últimas Noticias (30 días)</span>
                            <div class="tip-box" style="display:inline-flex;margin-left:6px;"><div class="tip-icon">?</div><div class="tip-text">Noticias vía Finnhub. Clic en el titular para abrir la fuente original.</div></div>
                        </div>
                        <div class="mod-body" style="max-height:420px;overflow-y:auto;padding:12px 16px;">
                            {news_items}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="mod-box"><div class="mod-body">
                        <div style="font-family:Inter,sans-serif;color:#555;font-size:0.84rem;padding:20px;text-align:center;">
                            No hay noticias disponibles para este ticker en los últimos 30 días.
                        </div>
                    </div></div>
                    """, unsafe_allow_html=True)

    # ══ TAB 9: ESTACIONALIDAD ══
    with tabs[9]:
        if hist_1y is None or hist_1y.empty:
            st.info("Se necesitan datos históricos para calcular la estacionalidad.")
        else:
            import numpy as np
            from datetime import datetime as _dt
            import calendar as _cal

            # ── Load 5 years of history ──
            try:
                import yfinance as _yf2
                _tk = _yf2.Ticker(t_in)
                hist_5y = _tk.history(period="5y", interval="1mo", auto_adjust=True)
            except Exception:
                hist_5y = hist_1y  # fallback

            lookback_years = st.number_input("Ventana análisis (años)", min_value=1, max_value=10,
                                              value=5, step=1, key="seas_lookback")

            if hist_5y is not None and not hist_5y.empty:
                # Compute monthly returns
                try:
                    import yfinance as _yf3
                    _tkr = _yf3.Ticker(t_in)
                    h_full = _tkr.history(period=f"{lookback_years}y", interval="1mo", auto_adjust=True)
                except Exception:
                    h_full = hist_5y

                h_full = h_full[h_full['Close'] > 0].copy()
                h_full['ret'] = h_full['Close'].pct_change() * 100
                h_full['year']  = h_full.index.year
                h_full['month'] = h_full.index.month
                h_full = h_full.dropna(subset=['ret'])

                now_month = _dt.now().month
                months = list(range(1, 13))
                month_names = [_cal.month_name[m] for m in months]

                # ── Heatmap: year × month matrix ──
                years = sorted(h_full['year'].unique(), reverse=True)
                _hm_hdr = (
                    '<div style="background:#0c0e14;border:1px solid #1a1e26;border-radius:10px;padding:20px;margin-bottom:16px;">'
                    '<div style="font-family:VT323,monospace;color:#ccc;font-size:1.3rem;margin-bottom:4px;">Rentabilidad Mensual — Mapa de Calor</div>'
                    f'<div style="font-family:Inter,sans-serif;color:#444;font-size:0.75rem;margin-bottom:16px;">{lookback_years} años de rendimiento histórico mensual</div>'
                )

                def _cell_color(v):
                    if v is None: return "#1a1e26", "#444"
                    if v >= 10:  return "#0d4a2a", "#00ffad"
                    if v >= 3:   return "#0a2818", "#00cc88"
                    if v >= 0:   return "#111a14", "#559966"
                    if v >= -3:  return "#1a1510", "#886644"
                    if v >= -10: return "#2a1010", "#cc4444"
                    return "#3d0a0a", "#f23645"

                # Header row
                hdr = '<table style="width:100%;border-collapse:collapse;font-family:Space Grotesk,sans-serif;">'
                hdr += '<tr><th style="text-align:left;padding:6px 8px;color:#555;font-size:0.65rem;letter-spacing:1px;text-transform:uppercase;min-width:50px;">YEAR</th>'
                for mn in ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']:
                    hdr += f'<th style="text-align:center;padding:6px 4px;color:#555;font-size:0.65rem;letter-spacing:1px;text-transform:uppercase;min-width:60px;">{mn}</th>'
                hdr += '</tr>'

                rows_h = ''
                for yr in years:
                    yr_data = h_full[h_full['year'] == yr]
                    row = f'<tr><td style="padding:4px 8px;font-family:monospace;color:#888;font-size:0.8rem;">{yr}</td>'
                    for m in months:
                        m_data = yr_data[yr_data['month'] == m]['ret']
                        if len(m_data) > 0:
                            v = round(float(m_data.iloc[0]), 2)
                            bg, fg = _cell_color(v)
                            border = "border:1px solid #00d9ff44;" if yr == _dt.now().year and m == now_month else ""
                            row += (f'<td style="text-align:center;padding:5px 3px;{border}">'
                                    f'<div style="background:{bg};border-radius:4px;padding:5px 2px;'
                                    f'font-family:monospace;color:{fg};font-size:0.75rem;">'
                                    f'{"+" if v>=0 else ""}{v:.2f}%</div></td>')
                        else:
                            row += '<td style="text-align:center;padding:5px 3px;"><div style="background:#111;border-radius:4px;padding:5px 2px;color:#333;font-size:0.75rem;">—</div></td>'
                    row += '</tr>'
                    rows_h += row

                legend = (
                    '</table>'
                    '<div style="margin-top:12px;display:flex;gap:16px;flex-wrap:wrap;align-items:center;">'
                    '<span style="font-family:Inter,sans-serif;color:#555;font-size:0.72rem;font-weight:600;">Escala de Color:</span>'
                    '<span style="font-family:monospace;font-size:0.7rem;color:#f23645;">■ ≤ -10%</span>'
                    '<span style="font-family:monospace;font-size:0.7rem;color:#cc4444;">■ -3% a 0%</span>'
                    '<span style="font-family:monospace;font-size:0.7rem;color:#555;">■ ~0%</span>'
                    '<span style="font-family:monospace;font-size:0.7rem;color:#00cc88;">■ 0% a 3%</span>'
                    '<span style="font-family:monospace;font-size:0.7rem;color:#00ffad;">■ ≥ 10%</span>'
                    '</div></div>'
                )
                st.markdown(_hm_hdr + hdr + rows_h + legend, unsafe_allow_html=True)

                # ── Patrones de Estacionalidad table ──
                _pt_hdr = (
                    '<div style="background:#0c0e14;border:1px solid #1a1e26;border-radius:10px;padding:20px;margin-top:16px;">'
                    '<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">'
                    '<span style="font-size:1.1rem;">📅</span>'
                    '<div style="font-family:VT323,monospace;color:#ccc;font-size:1.3rem;">Patrones de Estacionalidad</div>'
                    '</div>'
                    '<div style="font-family:Inter,sans-serif;color:#444;font-size:0.75rem;margin-bottom:16px;">Patrones históricos de precio por período temporal</div>'
                )

                # Table header
                tbl = (
                    '<table style="width:100%;border-collapse:collapse;">'
                    '<thead><tr style="border-bottom:1px solid #1a1e26;">'
                )
                for col in ['MES','REND. MEDIO %','CONSISTENCIA %','DESV. EST. %','VOL. REL.','MÁXIMO DRAWDOWN %','PUNTUACIÓN']:
                    align = 'left' if col=='MES' else 'right'
                    tbl += f'<th style="text-align:{align};padding:8px 12px;font-family:Space Grotesk,sans-serif;color:#555;font-size:0.65rem;letter-spacing:1px;text-transform:uppercase;">{col}</th>'
                tbl += '</tr></thead><tbody>'

                # Per-month stats
                all_rets = {m: h_full[h_full['month']==m]['ret'].values for m in months}
                max_vol = max(np.std(v) for v in all_rets.values() if len(v)>0) or 1

                for i, m in enumerate(months):
                    rets = all_rets[m]
                    if len(rets) == 0:
                        continue
                    avg   = float(np.mean(rets))
                    cons  = float(np.mean(rets > 0) * 100)
                    std   = float(np.std(rets))
                    rel_v = round(std / max_vol * 10, 2) if max_vol else 0
                    mdd   = float(np.min(rets))
                    # Score: avg*3 + cons*0.4 - std*0.5
                    score = round(avg*3 + cons*0.4 - std*0.5, 1)
                    sc_color = "#00ffad" if score>=30 else ("#ff9800" if score>=10 else "#f23645")
                    avg_c = "#00ffad" if avg>=0 else "#f23645"
                    mdd_c = "#00ffad" if mdd>=0 else "#f23645"
                    cur_border = "border-left:2px solid #ff9800;" if m == now_month else ""

                    tbl += (
                        f'<tr style="border-bottom:1px solid #0f1218;{cur_border}">'
                        f'<td style="padding:8px 12px;font-family:Inter,sans-serif;color:#ccc;font-size:0.82rem;">{month_names[i]}</td>'
                        f'<td style="text-align:right;padding:8px 12px;">'
                        f'<span style="background:{"rgba(0,255,173,0.1)" if avg>=0 else "rgba(242,54,69,0.1)"};'
                        f'color:{avg_c};padding:2px 8px;border-radius:4px;font-family:monospace;font-size:0.78rem;">'
                        f'{"+" if avg>=0 else ""}{avg:.2f}%</span></td>'
                        f'<td style="text-align:right;padding:8px 12px;font-family:monospace;color:#888;font-size:0.78rem;">{cons:.0f}%</td>'
                        f'<td style="text-align:right;padding:8px 12px;font-family:monospace;color:#666;font-size:0.78rem;">{std:.2f}%</td>'
                        f'<td style="text-align:right;padding:8px 12px;font-family:monospace;color:#666;font-size:0.78rem;">{rel_v:.2f}</td>'
                        f'<td style="text-align:right;padding:8px 12px;font-family:monospace;color:{mdd_c};font-size:0.78rem;">{mdd:.2f}%</td>'
                        f'<td style="text-align:right;padding:8px 12px;">'
                        f'<span style="background:{sc_color}22;color:{sc_color};padding:2px 8px;'
                        f'border-radius:4px;font-family:monospace;font-size:0.78rem;">{score}</span></td>'
                        f'</tr>'
                    )

                tbl += '</tbody></table>'
                footnote = (
                    '<div style="margin-top:12px;font-family:Inter,sans-serif;color:#444;font-size:0.72rem;">'
                    'Chip Rend. Medio: verde=positivo, rojo=negativo. &nbsp;'
                    'Borde amarillo = mes actual del calendario. &nbsp;'
                    'Puntuación = media×3 + consistencia×0.4 − desv.est×0.5'
                    '</div></div>'
                )
                st.markdown(_pt_hdr + tbl + footnote, unsafe_allow_html=True)

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
            <div class="tip-box" style="display:inline-flex;margin-left:6px;"><div class="tip-icon">?</div><div class="tip-text">Análisis automatizado con datos reales de Yahoo Finance. No constituye asesoramiento financiero.</div></div>
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

    # ── IA Section ──
    st.markdown("""
    <div style="background:#0c0e14;border:1px solid #00ffad33;border-radius:10px;
                padding:20px 24px 16px;margin:20px 0 12px 0;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <span style="font-size:1.4rem;">🤖</span>
            <div style="font-family:VT323,monospace;color:#00ffad;font-size:1.6rem;
                        letter-spacing:3px;text-transform:uppercase;">RSU Artificial Intelligence</div>
            <span style="background:#00ffad22;color:#00ffad;font-family:monospace;font-size:0.65rem;
                         padding:2px 8px;border-radius:4px;border:1px solid #00ffad44;margin-left:auto;">
                AI POWERED
            </span>
        </div>
        <div style="font-family:Inter,sans-serif;color:#555;font-size:0.83rem;line-height:1.7;
                    border-top:1px solid #1a1e26;padding-top:10px;">
            <strong style="color:#00ffad;">⚡ Rápido</strong> — Snapshot ejecutivo: precio, valoración, catalizadores y riesgo en segundos.<br>
            <strong style="color:#00d9ff;">📋 Completo</strong> — Informe de 11 secciones: empresa, fundamentales, técnico, smart money y perspectivas.<br>
            <strong style="color:#ff9800;">🔍 Grok</strong> — Investigación en tiempo real: noticias, insiders, catalizadores y movimientos sectoriales vía xAI.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_ia1, col_ia2, col_ia3 = st.columns(3)
    btn_rapido   = col_ia1.button("▶  ANÁLISIS RÁPIDO",          key="btn_rapido",   use_container_width=True)
    btn_completo = col_ia2.button("▶  INFORME COMPLETO (11s)",   key="btn_completo", use_container_width=True)
    btn_grok     = col_ia3.button("🔍  INVESTIGACIÓN GROK (xAI)", key="btn_grok",     use_container_width=True)

    model_ia, modelo_nombre, error_ia = get_ia_model()

    if btn_rapido or btn_completo:
        if error_ia:
            st.error(f"❌ Error al conectar con el modelo IA: {error_ia}")
        else:
            prompt_template = PROMPT_RSU_RAPIDO if btn_rapido else PROMPT_RSU_COMPLETO

            # Enriquecer datos cuantitativos con contexto sectorial para el prompt
            sector_context = f"\n| Sector | {sector or 'N/A'} |\n| Industria | {industry or 'N/A'} |\n| RSU Score | {rsu_score['total']}/100 ({rsu_score['label']}) |"
            datos_enriquecidos = datos_cuantitativos + sector_context

            prompt_final = (prompt_template
                            .replace("{t}", t_in)
                            .replace("{datos_cuantitativos}", datos_enriquecidos))

            # Truncar si el prompt es demasiado largo (previene degradación del modelo)
            MAX_PROMPT_CHARS = 12000
            if len(prompt_final) > MAX_PROMPT_CHARS:
                prompt_final = prompt_final[:MAX_PROMPT_CHARS] + "\n\n[Datos truncados por longitud. Continúa el análisis con los datos disponibles.]"

            is_rapido = btn_rapido
            label_tipo = "ANÁLISIS RÁPIDO" if is_rapido else "INFORME COMPLETO"

            st.markdown(f"""
            <div style="font-family:'Space Grotesk',sans-serif;color:#00ffad;font-size:0.8rem;
                        letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">
                ⚡ Generando {label_tipo} para {t_in}...
            </div>
            """, unsafe_allow_html=True)

            report_placeholder = st.empty()
            full_text = ""

            try:
                # Streaming: muestra el informe mientras se genera token a token
                response = model_ia.generate_content(
                    prompt_final,
                    generation_config={
                        "temperature": 0.1,          # Análisis financiero: baja temperatura = más consistente
                        "max_output_tokens": 8192,
                    },
                    stream=True,
                )
                for chunk in response:
                    try:
                        if chunk.text:
                            full_text += chunk.text
                            report_placeholder.markdown(
                                f'<div style="border:1px solid #00ffad1a;border-radius:8px;'
                                f'padding:24px;background:#0a0c10;margin-bottom:12px;">{full_text}</div>',
                                unsafe_allow_html=True
                            )
                    except Exception as chunk_err:
                        logger.warning("[IA stream chunk] %s: %s", t_in, chunk_err)

                if full_text:
                    st.session_state['last_report']        = full_text
                    st.session_state['last_report_ticker'] = t_in
                else:
                    st.error("❌ El modelo no devolvió texto. Intenta de nuevo.")

            except Exception as e:
                logger.error("[IA generate_content] %s: %s", t_in, e)
                # Fallback: sin streaming si el modelo no lo soporta
                try:
                    res = model_ia.generate_content(
                        prompt_final,
                        generation_config={"temperature": 0.1, "max_output_tokens": 8192}
                    )
                    full_text = res.text
                    st.session_state['last_report']        = full_text
                    st.session_state['last_report_ticker'] = t_in
                    report_placeholder.markdown(full_text)
                except Exception as e2:
                    st.error(f"❌ Error generando el informe: {e2}")
                    logger.error("[IA fallback] %s: %s", t_in, e2)

    # ── GROK (xAI) ──
    if btn_grok:
        xai_key = st.secrets.get("XAI_API_KEY", "")
        if not xai_key:
            st.error("❌ Clave XAI_API_KEY no configurada en secrets.toml")
        else:
            prompt_grok_final = PROMPT_GROK.replace("{t}", t_in)
            st.markdown(f"""
            <div style="font-family:'Space Grotesk',sans-serif;color:#ff9800;font-size:0.8rem;
                        letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">
                🔍 Consultando Grok (xAI) para {t_in}...
            </div>
            """, unsafe_allow_html=True)
            try:
                import requests as _req
                resp_g = _req.post(
                    "https://api.x.ai/v1/chat/completions",
                    json={"model":"grok-3-latest","messages":[{"role":"user","content":prompt_grok_final}],
                          "temperature":0.2,"max_tokens":8192},
                    headers={"Authorization":f"Bearer {xai_key}","Content-Type":"application/json"},
                    timeout=120
                )
                resp_g.raise_for_status()
                grok_text = resp_g.json()["choices"][0]["message"]["content"]
                st.session_state['last_report']        = grok_text
                st.session_state['last_report_ticker'] = t_in
                st.markdown(
                    '<div style="border:1px solid #ff980033;border-radius:8px;'
                    'padding:24px;background:#0a0c10;margin-bottom:12px;">'
                    '<div style="font-family:Space Grotesk,sans-serif;color:#ff9800;'
                    'font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;">'
                    f'🔍 GROK (xAI) — {t_in}' + '</div>' + grok_text + '</div>',
                    unsafe_allow_html=True
                )
            except Exception as eg:
                st.error(f"❌ Error Grok: {eg}")

    if st.session_state.get('last_report') and st.session_state.get('last_report_ticker') == t_in:
        if not (btn_rapido or btn_completo or btn_grok):
            # Solo mostrar informe previo si no acabamos de generar uno nuevo
            st.markdown(f"""
            <div class="mod-box">
                <div class="mod-header">
                    <span class="mod-title">📋 Informe RSU IA — {t_in}</span>
                    <div style="font-family:'Space Grotesk',sans-serif;font-size:0.7rem;color:#444;letter-spacing:1px;">CACHÉ</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.container():
                st.markdown(
                    '<div style="border:1px solid #00ffad1a;border-radius:0 0 8px 8px;'
                    'padding:24px;background:#0a0c10;margin-bottom:18px;">'
                    + st.session_state['last_report'] +
                    '</div>',
                    unsafe_allow_html=True
                )

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
    sources_str = " · ".join(s.upper() for s in data_sources)
    st.markdown(f"""
    <div style="text-align:center;margin-top:50px;padding:20px;border-top:1px solid #0f1218;">
        <div style="font-family:'Space Grotesk',sans-serif;color:#222;font-size:0.72rem;letter-spacing:2px;text-transform:uppercase;">
            [END OF REPORT // RSU_EARNINGS_v5.0]<br>
            [DATA: {sources_str} · TRADINGVIEW · GEMINI AI]<br>
            [STATUS: ACTIVE // {datetime.now().year}]
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render()



