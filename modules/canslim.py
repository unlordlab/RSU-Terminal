
# -*- coding: utf-8 -*-
"""
CAN SLIM Scanner Pro - v4.0.0
Sistema de selección de acciones con Ratings IBD + Trend Template Minervini + ML
Optimizado para comunidades de trading: batch downloads, caché agresivo, pre-filtros.
Universo: S&P 500 completo (~503 acciones) vía Wikipedia.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import warnings
import os
import json
import re as re_module
import time
import random
import logging
warnings.filterwarnings('ignore')

# ── Logging (reemplaza print() en producción) ──────────────────────────────────
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("canslim")

# ── Imports opcionales ─────────────────────────────────────────────────────────
try:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from zipline.api import order_target_percent, record, symbol, set_benchmark
    from zipline import run_algorithm
    ZIPLINE_AVAILABLE = True
except ImportError:
    ZIPLINE_AVAILABLE = False

# ==============================================================================
# CONSTANTES Y COLORES
# ==============================================================================

CACHE_TTL_SECONDS  = 3600   # 1 hora de caché para resultados de scan
BATCH_SIZE         = 50     # acciones por lote en yf.download()
MIN_MARKET_CAP_B   = 0.5    # filtro previo: market cap mínimo en $B
MIN_PRICE          = 10.0   # filtro previo: precio mínimo
MIN_AVG_VOLUME     = 500_000  # filtro previo: volumen diario mínimo

COLORS = {
    'primary'        : '#00ffad',
    'warning'        : '#ff9800',
    'danger'         : '#f23645',
    'neutral'        : '#888888',
    'bg_dark'        : '#0c0e12',
    'bg_card'        : '#1a1e26',
    'border'         : '#2a2e36',
    'text'           : '#ffffff',
    'text_secondary' : '#aaaaaa',
    'ibd_blue'       : '#2196F3',
    'ibd_green'      : '#4CAF50',
}

def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# ==============================================================================
# UNIVERSO S&P 500 (vía Wikipedia + fallback hardcoded)
# ==============================================================================

# Lista completa S&P 500 hardcoded (actualizada 2025) como fuente primaria confiable.
# Wikipedia se usa como fuente secundaria para actualizaciones. 
SP500_TICKERS = [
    "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","ABNB",
    "AKAM","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL","GOOG","MO","AMZN",
    "AMCR","AEE","AAL","AEP","AXP","AIG","AMT","AWK","AMP","AME","AMGN",
    "APH","ADI","ANSS","AON","APA","AAPL","AMAT","APTV","ACGL","ADM","ANET",
    "AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON","BKR","BALL",
    "BAC","BK","BBWI","BAX","BDX","BRK-B","BBY","TECH","BIIB","BLK","BX",
    "BA","BKNG","BWA","BSX","BMY","AVGO","BR","BRO","BF-B","BLDR","BG","CDNS",
    "CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR","CTLT","CAT","CBOE","CBRE",
    "CDW","CE","COR","CNC","CNX","CDAY","CF","CRL","SCHW","CHTR","CVX","CMG",
    "CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO",
    "CTSH","CL","CMCSA","CAG","COP","ED","STZ","CEG","COO","CPRT","GLW","CPAY",
    "CTVA","CSGP","COST","CTRA","CRWD","CCI","CSX","CMI","CVS","DHR","DRI",
    "DVA","DAY","DE","DAL","XRAY","DVN","DXCM","FANG","DLR","DFS","DG","DLTR",
    "D","DPZ","DOV","DOW","DHI","DTE","DUK","DD","EMN","ETN","EBAY","ECL",
    "EIX","EW","EA","ELV","LLY","EMR","ENPH","ETR","EOG","EPAM","EQT","EFX",
    "EQIX","EQR","ESS","EL","ETSY","EG","EVRST","EXAS","EXPD","EXPE","EXR",
    "XOM","FFIV","FDS","FICO","FAST","FRT","FDX","FIS","FITB","FSLR","FE",
    "FI","FMC","F","FTIV","FOXA","FOX","BEN","FCX","GRMN","IT","GE","GEHC",
    "GEV","GEN","GNRC","GD","GIS","GM","GPC","GILD","GS","HAL","HIG","HAS",
    "HCA","DOC","HSIC","HSY","HES","HPE","HLT","HOLX","HD","HON","HRL","HST",
    "HWM","HPQ","HUBB","HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY",
    "IR","PODD","INTC","ICE","IFF","IP","IPG","INTU","ISRG","IVZ","INVH",
    "IQV","IRM","JBHT","JBL","JKHY","J","JNJ","JCI","JPM","JNPR","K","KVUE",
    "KDP","KEY","KEYS","KMB","KIM","KMI","KLAC","KHC","KR","LHX","LH","LRCX",
    "LW","LVS","LDOS","LEN","LIN","LYV","LKQ","LMT","L","LOW","LULU","LYB",
    "MTB","MRO","MPC","MKTX","MAR","MMC","MLM","MAS","MA","MTCH","MKC","MCD",
    "MCK","MDT","MRK","META","MET","MTD","MGM","MCHP","MU","MSFT","MAA","MRNA",
    "MHK","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS","MSI","MSCI",
    "NDAQ","NTAP","NFLX","NEM","NWSA","NWS","NEE","NKE","NI","NDSN","NSC",
    "NTRS","NOC","NCLH","NRG","NUE","NVDA","NVR","NXPI","ORLY","OXY","ODFL",
    "OMC","ON","OKE","ORCL","OTIS","PCAR","PKG","PANW","PH","PAYX","PAYC",
    "PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNW","PNC","POOL","PPG","PPL",
    "PFG","PG","PGR","PLD","PRU","PEG","PTC","PSA","PHM","QRVO","PWR","QCOM",
    "DGX","RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY","ROK",
    "ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB","STX","SRE","NOW",
    "SHW","SPG","SWKS","SJM","SNA","SOLV","SO","LUV","SWK","SBUX","STT","STLD",
    "STE","SYK","SMCI","SYF","SNPS","SYY","TMUS","TROW","TTWO","TPR","TRGP",
    "TGT","TEL","TDY","TFX","TER","TSLA","TXN","TXT","TMO","TJX","TSCO","TT",
    "TDG","TRV","TRMB","TFC","TYL","TSN","USB","UBER","UDR","ULTA","UNP","UAL",
    "UPS","URI","UNH","UHS","VLO","VTR","VLTO","VRSN","VRSK","VZ","VRTX","VTRS",
    "VICI","V","VST","VMC","WRB","GWW","WAB","WBA","WMT","DIS","WBD","WM",
    "WAT","WEC","WFC","WELL","WST","WDC","WY","WHR","WMB","WTW","WYNN","XEL",
    "XYL","YUM","ZBRA","ZBH","ZTS",
]

@st.cache_data(ttl=86400)
def get_sp500_tickers() -> list[str]:
    """
    Devuelve la lista S&P 500 completa (~503 tickers).
    Fuente primaria: lista hardcoded actualizada (siempre disponible, sin red).
    Fuente secundaria: Wikipedia (para incorporar cambios recientes al índice).
    Fusiona ambas y devuelve el conjunto más completo.
    """
    # Base siempre disponible
    base = list(dict.fromkeys(SP500_TICKERS))   # deduplicar preservando orden

    # Intentar enriquecer desde Wikipedia
    try:
        tables = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", header=0
        )
        df  = tables[0]
        col = "Symbol" if "Symbol" in df.columns else df.columns[0]
        wiki_raw = df[col].str.replace(".", "-", regex=False).tolist()

        seen = set(base)
        for t in wiki_raw:
            t = str(t).strip().upper()
            # Regex permisiva: letras, números, guion — hasta 6 chars
            if t and t not in seen and re_module.match(r'^[A-Z][A-Z0-9\-]{0,5}$', t):
                seen.add(t)
                base.append(t)
        logger.info(f"SP500: {len(base)} tickers (hardcoded + Wikipedia)")
    except Exception as e:
        logger.warning(f"Wikipedia SP500 no disponible ({e}), usando sólo lista hardcoded")

    return base

# ==============================================================================
# SISTEMA DE CACHÉ JSON (resultados pre-calculados por job nocturno)
# ==============================================================================

# FIX RUTAS: Streamlit Cloud usa CWD = raíz del repo (diferente a __file__).
# Buscamos en todas las ubicaciones posibles en orden de probabilidad.
# NO usar constante global — recalcular en cada llamada para mayor robustez.

CACHE_MAX_AGE_H = 20   # horas máximas de validez del caché

def _find_cache_path() -> str:
    """
    Busca scan_cache.json en múltiples rutas posibles.
    Streamlit Cloud pone CWD = raíz del repo; __file__ puede apuntar a otra parte.
    """
    candidates = [
        os.path.join(os.getcwd(), "data", "scan_cache.json"),                          # CWD/data/ — Streamlit Cloud
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "scan_cache.json"),  # junto al .py
        "data/scan_cache.json",                                                          # relativa directa
        os.path.join(os.path.expanduser("~"), "data", "scan_cache.json"),               # home dir
        "scan_cache.json",                                                               # raíz sin carpeta
    ]
    for p in candidates:
        if os.path.exists(p):
            logger.info(f"scan_cache.json encontrado en: {p}")
            return p
    # Si no existe en ningún lado, devolver la preferida (CWD) para que save funcione
    preferred = os.path.join(os.getcwd(), "data", "scan_cache.json")
    logger.warning(f"scan_cache.json no encontrado. Rutas buscadas: {candidates}")
    return preferred


def load_cached_scan() -> dict | None:
    """
    Carga los resultados del job nocturno si existen y son frescos.
    Retorna None si no hay caché o está obsoleto.
    FIX v4.0.2: recalcula la ruta en cada llamada para Streamlit Cloud.
    """
    try:
        path = _find_cache_path()
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        generated_at = datetime.fromisoformat(data.get("generated_at", "2000-01-01"))
        age_hours = (datetime.utcnow() - generated_at).total_seconds() / 3600
        if age_hours > CACHE_MAX_AGE_H:
            logger.info(f"Caché JSON obsoleto ({age_hours:.1f}h > {CACHE_MAX_AGE_H}h)")
            return None
        logger.info(f"Caché JSON válido ({age_hours:.1f}h de antigüedad) — {path}")
        return data
    except Exception as e:
        logger.warning(f"Error leyendo caché JSON: {e}")
        return None


def save_scan_to_cache(candidates: list, market_status: dict, sp500_count: int):
    """
    Guarda los resultados del scan en JSON para ser leídos por la app.
    Llamado por el job nocturno (nightly_scan.py).
    """
    try:
        save_path = _find_cache_path()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        payload = {
            "generated_at" : datetime.utcnow().isoformat(),
            "sp500_count"  : sp500_count,
            "candidates"   : candidates,
            "market_status": {
                "score" : market_status.get("score", 50),
                "phase" : market_status.get("phase", "N/A"),
                "color" : market_status.get("color", "#888888"),
                "signals": market_status.get("signals", []),
            },
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"Caché JSON guardado: {len(candidates)} candidatos → {save_path}")
    except Exception as e:
        logger.error(f"Error guardando caché JSON: {e}")



def init_session_state():
    defaults = {
        'scan_candidates'   : [],
        'scan_timestamp'    : None,
        'last_scan_params'  : {},
        'market_status'     : None,
        'spy_data_cache'    : None,
        'bulk_hist_cache'   : None,
        'bulk_info_cache'   : None,
        'sp500_tickers'     : None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ==============================================================================
# DESCARGA MASIVA OPTIMIZADA (evita rate limits con batch downloads)
# ==============================================================================

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def download_batch_history(tickers_tuple: tuple, period: str = "1y") -> dict[str, pd.DataFrame]:
    """
    Descarga histórico de precio/volumen.
    - 1 ticker  → yf.Ticker().history() (más robusto, evita problemas MultiIndex)
    - N tickers → yf.download() en batch (eficiente)
    Retorna dict {ticker: DataFrame con OHLCV}.
    """
    tickers = list(tickers_tuple)
    if not tickers:
        return {}

    # ── Caso 1 ticker: usar Ticker().history() — más fiable que download() ──
    if len(tickers) == 1:
        t = tickers[0]
        try:
            df = yf.Ticker(t).history(period=period, auto_adjust=True)
            if df is None or df.empty:
                logger.warning(f"Ticker().history() vacío para {t}")
                return {}
            # history() devuelve columnas simples: Open, High, Low, Close, Volume...
            # Normalizar nombres por si acaso
            df.columns = [c.capitalize() if c.lower() in
                          {'open','high','low','close','volume'} else c
                          for c in df.columns]
            # Quitar timezone del índice para consistencia con el resto
            if hasattr(df.index, 'tz') and df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            required = {'Close', 'Open', 'High', 'Low', 'Volume'}
            if not required.issubset(set(df.columns)):
                logger.warning(f"Columnas insuficientes para {t}: {list(df.columns)}")
                return {}
            df = df.dropna(subset=['Close'])
            if len(df) < 30:
                logger.warning(f"Muy pocas filas para {t}: {len(df)}")
                return {}
            return {t: df}
        except Exception as e:
            logger.error(f"Error Ticker().history() para {t}: {e}")
            return {}

    # ── Caso N tickers: batch download ──────────────────────────────────────
    try:
        raw = yf.download(
            tickers,
            period=period,
            auto_adjust=True,
            progress=False,
            group_by='ticker',
            threads=True,
        )
        result = {}
        for t in tickers:
            try:
                df = raw[t].dropna(how='all')
                if len(df) > 30:
                    result[t] = df
            except Exception:
                pass
        return result
    except Exception as e:
        logger.error(f"Error en batch download: {e}")
        return {}


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def download_batch_info(tickers_tuple: tuple) -> dict[str, dict]:
    """
    Descarga info fundamental ticker a ticker pero con retry inteligente y
    caché agresivo. El info de yfinance no soporta batch nativo.
    Se hace de forma compacta con rate limiting gentil.
    """
    tickers = list(tickers_tuple)
    result  = {}
    for i, t in enumerate(tickers):
        try:
            info = yf.Ticker(t).info
            if info and len(info) > 5:
                result[t] = info
            # delay suave: 0.3s base + jitter para evitar 429
            time.sleep(0.3 + random.uniform(0.05, 0.2))
        except Exception as e:
            logger.warning(f"Info error {t}: {e}")
            time.sleep(0.5)
        # pausa adicional cada 50 tickers
        if (i + 1) % 50 == 0:
            time.sleep(2)
    return result


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_single_ticker_info(ticker: str) -> dict:
    """
    Obtiene el .info de un ticker individual con retry + backoff.
    Cacheado 1h — si el usuario vuelve a analizar el mismo ticker no hace nueva llamada HTTP.
    Nota: yfinance ≥0.2.x puede devolver .info con pocas claves — se complementa con fast_info.
    """
    last_err = None
    for attempt in range(3):
        try:
            if attempt > 0:
                wait = 15 * attempt + random.uniform(1, 5)
                logger.info(f"Retry {attempt}/2 para {ticker} — esperando {wait:.1f}s")
                time.sleep(wait)
            tkr  = yf.Ticker(ticker)
            info = tkr.info or {}

            # yfinance ≥0.2.x: .info puede devolver dict mínimo sin fundamentales.
            # Completar con fast_info si faltan campos clave.
            if len(info) < 10:
                try:
                    fi = tkr.fast_info
                    info.setdefault('marketCap',             getattr(fi, 'market_cap', None))
                    info.setdefault('previousClose',         getattr(fi, 'previous_close', None))
                    info.setdefault('fiftyTwoWeekHigh',      getattr(fi, 'year_high', None))
                    info.setdefault('fiftyTwoWeekLow',       getattr(fi, 'year_low', None))
                    info.setdefault('regularMarketVolume',   getattr(fi, 'last_volume', None))
                    info.setdefault('shortName', ticker)
                except Exception:
                    pass

            if info and len(info) > 5:
                return info
        except Exception as e:
            last_err = e
            logger.warning(f"get_single_ticker_info {ticker} intento {attempt+1}: {e}")
    logger.error(f"No se pudo obtener info de {ticker} tras 3 intentos: {last_err}")
    return {}  # dict vacío — calculate_can_slim_metrics maneja fundamentales en 0
    logger.error(f"No se pudo obtener info de {ticker} tras 3 intentos: {last_err}")
    return {}  # dict vacío — calculate_can_slim_metrics maneja fundamentales en 0


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_spy_history() -> pd.DataFrame:
    """SPY histórico con caché de 1h."""
    try:
        data = yf.download("SPY", period="2y", auto_adjust=True, progress=False)
        # yfinance ≥0.2 devuelve MultiIndex incluso con 1 ticker — aplanar
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data.dropna(how='all')
    except Exception as e:
        logger.error(f"Error SPY: {e}")
        return pd.DataFrame()


# ==============================================================================
# PRE-FILTROS (Market Cap, Precio, Volumen) — aplica ANTES de análisis pesado
# ==============================================================================

def pre_filter_tickers(tickers: list, hist_data: dict, info_data: dict) -> list:
    """
    Filtra tickers por:
      - Precio > MIN_PRICE
      - Volumen promedio 20d > MIN_AVG_VOLUME
      - Market cap > MIN_MARKET_CAP_B (si disponible en info)
    Reduce universo ~30-40% antes del análisis técnico pesado.
    """
    filtered = []
    for t in tickers:
        hist = hist_data.get(t)
        info = info_data.get(t, {})
        if hist is None or hist.empty or len(hist) < 50:
            continue
        try:
            price = hist['Close'].iloc[-1]
            if isinstance(price, pd.Series): price = float(price.iloc[0])
            else: price = float(price)
        except Exception:
            continue
        if price < MIN_PRICE:
            continue
        avg_vol = hist['Volume'].rolling(20).mean().iloc[-1]
        if avg_vol < MIN_AVG_VOLUME:
            continue
        mkt_cap = info.get('marketCap', None)
        if mkt_cap is not None and mkt_cap < MIN_MARKET_CAP_B * 1e9:
            continue
        filtered.append(t)
    return filtered

# ==============================================================================
# RS RATING — percentil real sobre universo (corrige escalado arbitrario)
# ==============================================================================

def compute_rs_scores_universe(tickers: list, hist_data: dict, spy_hist: pd.DataFrame) -> dict[str, float]:
    """
    Calcula RS Rating real para todos los tickers en un solo pase:
    1. Calcula retorno ponderado 40/20/20/20 (4 trimestres) relativo a SPY
    2. Asigna percentil 1-99 dentro del universo
    Esto da un RS Rating comparable con la metodología IBD.
    """
    if spy_hist.empty:
        return {t: 50 for t in tickers}

    # Normalizar índice SPY
    spy_close = spy_hist['Close'].copy()
    if hasattr(spy_close.index, 'tz') and spy_close.index.tz is not None:
        spy_close.index = spy_close.index.tz_localize(None)

    raw_scores = {}
    days_per_q = 63

    for t in tickers:
        hist = hist_data.get(t)
        if hist is None or len(hist) < 130:
            continue
        try:
            close = hist['Close'].copy()
            if hasattr(close.index, 'tz') and close.index.tz is not None:
                close.index = close.index.tz_localize(None)

            # Alinear con SPY
            merged = pd.merge(
                close.rename('stock'),
                spy_close.rename('spy'),
                left_index=True, right_index=True, how='inner'
            )
            if len(merged) < 100:
                continue

            weights = [0.40, 0.20, 0.20, 0.20]
            period_scores = []
            for i in range(4):
                end   = len(merged) - 1 if i == 0 else len(merged) - 1 - i * days_per_q
                start = end - days_per_q
                if start < 0:
                    period_scores.append(0.0)
                    continue
                s_ret = merged['stock'].iloc[end] / merged['stock'].iloc[start] - 1
                m_ret = merged['spy'].iloc[end]   / merged['spy'].iloc[start]   - 1
                rel   = (1 + s_ret) / (1 + m_ret) - 1 if abs(m_ret) > 0.001 else s_ret
                period_scores.append(rel)

            weighted = sum(w * s for w, s in zip(weights, period_scores))
            raw_scores[t] = weighted
        except Exception:
            pass

    if not raw_scores:
        return {t: 50 for t in tickers}

    # Convertir a percentil 1-99
    values = list(raw_scores.values())
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    percentile_map = {}
    for t, v in raw_scores.items():
        rank = sorted_vals.index(v)
        pct  = round(1 + (rank / max(n - 1, 1)) * 98)
        percentile_map[t] = min(99, max(1, pct))

    # Tickers sin datos → 50
    for t in tickers:
        if t not in percentile_map:
            percentile_map[t] = 50
    return percentile_map

# ==============================================================================
# CLASES DE RATINGS IBD
# ==============================================================================

class IBDRatingsCalculator:
    """Ratings IBD: EPS, Composite, SMR, Accumulation/Distribution, ATR."""

    def calculate_eps_rating(self, quarterly_eps_growth: float) -> int:
        g = quarterly_eps_growth
        if g is None: return 50
        if g >= 100: return 99
        if g >= 50:  return 90 + min(9, int((g - 50) / 5))
        if g >= 25:  return 80 + min(9, int((g - 25) / 2.5))
        if g >= 15:  return 60 + min(19, int(g - 15))
        if g > 0:    return 40 + min(19, int(g * 2))
        return max(1, 40 + int(g))

    def calculate_composite_rating(self, rs: int, eps: int, sales_g: float, roe: float, perf_12m: float) -> int:
        eps_s   = eps
        rs_s    = rs
        sales_s = min(99, max(1, 50 + (sales_g or 0)))
        roe_s   = min(99, max(1, (roe or 0) * 2))
        perf_s  = min(99, max(1, 50 + (perf_12m or 0)))
        comp = eps_s*0.30 + rs_s*0.30 + sales_s*0.15 + roe_s*0.15 + perf_s*0.10
        return min(99, max(1, round(comp)))

    def calculate_smr_rating(self, sales_g: float, roe: float, margins: float) -> str:
        score = 0
        if sales_g >= 25: score += 40
        elif sales_g >= 15: score += 30
        elif sales_g >= 10: score += 20
        elif sales_g > 0:  score += 10
        if roe >= 25: score += 40
        elif roe >= 17: score += 30
        elif roe >= 10: score += 20
        elif roe > 0:  score += 10
        if margins and margins > 0.20: score += 20
        elif margins and margins > 0.10: score += 15
        elif margins and margins > 0:   score += 10
        if score >= 80: return 'A'
        if score >= 60: return 'B'
        if score >= 40: return 'C'
        return 'D'

    def calculate_acc_dis_rating(self, hist: pd.DataFrame, period: int = 50) -> str:
        if hist is None or len(hist) < period:
            return 'C'
        try:
            recent = hist.tail(period).copy()
            recent['chg'] = recent['Close'].pct_change()
            vol_up   = recent[recent['chg'] > 0]['Volume'].sum()
            total_v  = recent['Volume'].sum()
            if total_v == 0: return 'C'
            acc_ratio = (vol_up / total_v) * 100
            perf = (recent['Close'].iloc[-1] / recent['Close'].iloc[0] - 1) * 100
            if acc_ratio >= 65 and perf > 5: return 'A'
            if acc_ratio >= 58: return 'B'
            if acc_ratio >= 42: return 'C'
            if acc_ratio >= 35: return 'D'
            return 'E'
        except Exception:
            return 'C'

    def calculate_atr_percent(self, hist: pd.DataFrame, period: int = 14) -> float:
        if hist is None or len(hist) < period:
            return 0.0
        try:
            h, l, c = hist['High'], hist['Low'], hist['Close']
            tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
            atr = tr.rolling(period).mean().iloc[-1]
            return round((atr / c.iloc[-1]) * 100, 2)
        except Exception:
            return 0.0


# ==============================================================================
# TREND TEMPLATE MINERVINI (8 criterios Stage 2)
# ==============================================================================

class MinerviniTrendTemplate:
    CRITERIA = [
        "Precio > SMA 50",
        "Precio > SMA 150",
        "Precio > SMA 200",
        "SMA 50 > SMA 150",
        "SMA 150 > SMA 200",
        "SMA 200 Tendencia Alcista",
        "Precio > 30% del mínimo 52s",
        "Precio dentro 25% del máximo 52s",
    ]

    def check_all_criteria(self, hist: pd.DataFrame, price: float) -> dict:
        empty = {'all_pass': False, 'score': 0,
                 'criteria': {n: False for n in self.CRITERIA}, 'stage': 'Insufficient Data'}
        if hist is None or len(hist) < 200:
            return empty
        try:
            close  = hist['Close']
            sma50  = close.rolling(50).mean().iloc[-1]
            sma150 = close.rolling(150).mean().iloc[-1]
            sma200 = close.rolling(200).mean().iloc[-1]
            sma200_20d = close.rolling(200).mean().iloc[-20]
            high52 = hist['High'].tail(252).max()
            low52  = hist['Low'].tail(252).min()

            criteria = {
                "Precio > SMA 50"             : price > sma50,
                "Precio > SMA 150"            : price > sma150,
                "Precio > SMA 200"            : price > sma200,
                "SMA 50 > SMA 150"            : sma50 > sma150,
                "SMA 150 > SMA 200"           : sma150 > sma200,
                "SMA 200 Tendencia Alcista"   : sma200 > sma200_20d,
                "Precio > 30% del mínimo 52s" : price >= low52 * 1.30,
                "Precio dentro 25% del máximo 52s": price >= high52 * 0.75,
            }
            score    = sum(criteria.values())
            all_pass = score == 8

            if all_pass:                                        stage = "Stage 2 (Advancing)"
            elif price > sma200 and sma200 > sma200_20d:       stage = "Stage 1/2 Transition"
            elif price < sma200 and not (sma200 > sma200_20d): stage = "Stage 4 (Declining)"
            else:                                               stage = "Stage 3 (Distribution)"

            return {
                'all_pass': all_pass, 'score': score,
                'criteria': criteria, 'stage': stage,
                'values'  : {
                    'sma_50': sma50, 'sma_150': sma150, 'sma_200': sma200,
                    'high_52w': high52, 'low_52w': low52,
                    'distance_from_high': ((price / high52) - 1) * 100,
                    'distance_from_low' : ((price / low52)  - 1) * 100,
                }
            }
        except Exception as e:
            return {**empty, 'stage': f'Error: {e}'}


# ==============================================================================
# ANÁLISIS DE MERCADO (criterio M)
# ==============================================================================

class MarketAnalyzer:
    INDICES = {'SPY': 'S&P 500', 'QQQ': 'NASDAQ 100', 'IWM': 'Russell 2000', '^VIX': 'VIX'}

    @st.cache_data(ttl=300, show_spinner=False)
    def get_market_data(_self) -> dict:
        result = {}
        tickers_to_dl = ['SPY', 'QQQ', 'IWM', '^VIX']
        try:
            raw = yf.download(tickers_to_dl, period="6mo", auto_adjust=True,
                              progress=False, group_by='ticker', threads=True)
            for t in tickers_to_dl:
                try:
                    df = raw[t].dropna(how='all') if len(tickers_to_dl) > 1 else raw.dropna(how='all')
                    if df.empty: continue
                    result[t] = {
                        'name'    : _self.INDICES[t],
                        'data'    : df,
                        'current' : df['Close'].iloc[-1],
                        'sma_50'  : df['Close'].rolling(50).mean().iloc[-1],
                        'sma_200' : df['Close'].rolling(200).mean().iloc[-1],
                        'trend_20d': (df['Close'].iloc[-1] / df['Close'].iloc[-20] - 1) * 100,
                    }
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Market data error: {e}")
        return result

    def calculate_market_score(self) -> dict:
        data   = self.get_market_data()
        score  = 50
        signals = []

        if 'SPY' in data:
            s = data['SPY']
            if s['current'] > s['sma_50'] > s['sma_200']:
                score += 20; signals.append("SPY: Golden Cross (Alcista)")
            elif s['current'] > s['sma_50']:
                score += 10; signals.append("SPY: Sobre SMA50")
            elif s['current'] < s['sma_50'] < s['sma_200']:
                score -= 20; signals.append("SPY: Death Cross (Bajista)")
            else:
                score -= 10
            if s['trend_20d'] > 5:  score += 10
            elif s['trend_20d'] < -5: score -= 10

        if 'QQQ' in data:
            q = data['QQQ']
            if q['current'] > q['sma_50']: score += 10; signals.append("QQQ: Tendencia positiva")
            else: score -= 5

        if 'IWM' in data:
            i = data['IWM']
            if i['current'] > i['sma_50']: score += 10; signals.append("Small Caps: Participación amplia")
            else: score -= 5

        if '^VIX' in data:
            v = data['^VIX']
            if v['current'] < 20:   score += 10; signals.append("VIX: Bajo (estabilidad)")
            elif v['current'] > 30: score -= 15; signals.append("VIX: Alto (miedo extremo)")

        score = max(0, min(100, score))

        if   score >= 80: phase, color = "CONFIRMED UPTREND",        COLORS['primary']
        elif score >= 60: phase, color = "UPTREND UNDER PRESSURE",   COLORS['warning']
        elif score >= 40: phase, color = "MARKET IN TRANSITION",     COLORS['neutral']
        elif score >= 20: phase, color = "DOWNTREND UNDER PRESSURE", COLORS['warning']
        else:             phase, color = "CONFIRMED DOWNTREND",      COLORS['danger']

        return {'score': score, 'phase': phase, 'color': color, 'signals': signals, 'data': data}


# ==============================================================================
# ML PREDICTOR (GradientBoosting)
# ==============================================================================

class CANSlimMLPredictor:
    FEATURES = [
        'earnings_growth', 'revenue_growth', 'eps_growth',
        'rs_rating', 'volume_ratio', 'inst_ownership',
        'pct_from_high', 'volatility', 'price_momentum',
    ]

    def __init__(self):
        self.model  = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canslim_ml_model.pkl")

    def _feature_vector(self, m: dict) -> np.ndarray:
        return np.array([
            m.get('earnings_growth', 0), m.get('revenue_growth', 0),
            m.get('eps_growth', 0),       m.get('rs_rating', 50),
            m.get('volume_ratio', 1),     m.get('inst_ownership', 0),
            abs(m.get('pct_from_high', 0)), m.get('volatility', 0.2),
            m.get('price_momentum', 0),
        ]).reshape(1, -1)

    def predict(self, metrics: dict) -> float:
        if not SKLEARN_AVAILABLE:
            return 0.5
        try:
            if self.model is None and os.path.exists(self.model_path):
                self.model, self.scaler = joblib.load(self.model_path)
            if self.model is None:
                return 0.5
            X = self.scaler.transform(self._feature_vector(metrics))
            return float(self.model.predict_proba(X)[0][1])
        except Exception:
            return 0.5

    def get_feature_importance(self) -> dict:
        if not SKLEARN_AVAILABLE or self.model is None:
            return {f: 1/len(self.FEATURES) for f in self.FEATURES}
        return dict(zip(self.FEATURES, self.model.feature_importances_))

    def train(self, historical_data: list) -> float:
        if not SKLEARN_AVAILABLE or len(historical_data) < 10:
            return 0.0
        X = np.array([self._feature_vector(d['metrics'])[0] for d in historical_data])
        y = np.array([1 if d.get('future_return', 0) > d.get('market_return', 0) else 0 for d in historical_data])
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        self.scaler.fit(X_tr)
        X_tr = self.scaler.transform(X_tr)
        X_te = self.scaler.transform(X_te)
        self.model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42)
        self.model.fit(X_tr, y_tr)
        joblib.dump((self.model, self.scaler), self.model_path)
        return self.model.score(X_te, y_te)


# ==============================================================================
# CÁLCULO INDIVIDUAL CAN SLIM (usa datos pre-descargados)
# ==============================================================================

def calculate_can_slim_metrics(
    ticker:       str,
    hist:         pd.DataFrame,
    info:         dict,
    spy_hist:     pd.DataFrame,
    rs_universe:  dict,
    market_score: dict,
    ibd_calc:     IBDRatingsCalculator,
    trend_engine: MinerviniTrendTemplate,
    ml:           CANSlimMLPredictor,
) -> dict | None:
    """
    Calcula métricas CAN SLIM completas usando datos ya descargados en batch.
    No hace ninguna llamada HTTP por sí misma.
    """
    try:
        if hist is None or hist.empty or len(hist) < 50:
            return None

        # Seguridad: aplanar MultiIndex si llegara hasta aquí (yfinance ≥0.2)
        if isinstance(hist.columns, pd.MultiIndex):
            hist = hist.copy()
            hist.columns = [col[0] for col in hist.columns]

        # Seguridad: eliminar columnas duplicadas (puede ocurrir tras flatten)
        if hist.columns.duplicated().any():
            hist = hist.loc[:, ~hist.columns.duplicated()]

        # Extrae escalar seguro — evita que .iloc[-1] devuelva Series
        def _s(val):
            if isinstance(val, pd.Series): return float(val.iloc[0])
            if hasattr(val, 'item'): return float(val.item())
            return float(val)

        price       = _s(hist['Close'].iloc[-1])
        market_cap  = info.get('marketCap', 0) / 1e9
        earn_g      = (info.get('earningsGrowth', 0) or 0) * 100
        rev_g       = (info.get('revenueGrowth', 0) or 0) * 100
        eps_g       = (info.get('earningsQuarterlyGrowth', 0) or 0) * 100
        # SANITIZE: Yahoo Finance devuelve valores absurdos (>10000%) cuando
        # el año anterior tuvo pérdidas (base effect). Cap en 999% para no distorsionar.
        earn_g = max(-100.0, min(999.0, earn_g))
        rev_g  = max(-100.0, min(999.0, rev_g))
        eps_g  = max(-100.0, min(999.0, eps_g))
        roe         = (info.get('returnOnEquity', 0) or 0) * 100
        margins     = info.get('profitMargins', 0) or 0
        inst_own    = (info.get('heldPercentInstitutions', 0) or 0) * 100
        high52      = _s(hist['High'].max())
        pct_from_hi = ((price - high52) / high52) * 100 if high52 > 0 else -100
        avg_vol     = _s(hist['Volume'].rolling(20).mean().iloc[-1])
        cur_vol     = _s(hist['Volume'].iloc[-1])
        vol_ratio   = cur_vol / avg_vol if avg_vol > 0 else 1.0

        # RS percentil real sobre universo
        rs_rating = rs_universe.get(ticker, 50)

        # IBD Ratings
        eps_rating = ibd_calc.calculate_eps_rating(eps_g)
        if len(hist) >= 252:
            price_252 = _s(hist['Close'].iloc[-252])
            perf_12m  = (price / price_252 - 1) * 100 if price_252 > 0 else 0.0
        else:
            price_0  = _s(hist['Close'].iloc[0])
            perf_12m = (price / price_0 - 1) * 100 if price_0 > 0 else 0.0
        composite  = ibd_calc.calculate_composite_rating(rs_rating, eps_rating, rev_g, roe, perf_12m)
        smr        = ibd_calc.calculate_smr_rating(rev_g, roe, margins)
        acc_dis    = ibd_calc.calculate_acc_dis_rating(hist)
        atr_pct    = ibd_calc.calculate_atr_percent(hist)

        # Trend Template
        trend_result = trend_engine.check_all_criteria(hist, price)

        # Score CAN SLIM (C, A, N, S, L, I, M)
        score = 0
        c_grade, c_sc = ('A', 20) if earn_g > 50 else ('A', 15) if earn_g > 25 else \
                         ('B', 10) if earn_g > 15 else ('C', 5) if earn_g > 0 else ('D', 0)
        score += c_sc

        a_grade, a_sc = ('A', 15) if eps_g > 50 else ('A', 12) if eps_g > 25 else \
                         ('B', 8)  if eps_g > 15 else ('C', 4) if eps_g > 0 else ('D', 0)
        score += a_sc

        n_grade, n_sc = ('A', 15) if pct_from_hi > -3  else ('A', 12) if pct_from_hi > -10 else \
                         ('B', 8)  if pct_from_hi > -20 else ('C', 4) if pct_from_hi > -30 else ('D', 0)
        score += n_sc

        s_grade, s_sc = ('A', 10) if vol_ratio > 2.0 else ('A', 8) if vol_ratio > 1.5 else \
                         ('B', 5)  if vol_ratio > 1.0 else ('C', 2)
        score += s_sc

        l_grade, l_sc = ('A', 15) if rs_rating > 90 else ('A', 12) if rs_rating > 80 else \
                         ('B', 8)  if rs_rating > 70 else ('C', 4) if rs_rating > 60 else ('D', 0)
        score += l_sc

        i_grade, i_sc = ('A', 10) if inst_own > 80 else ('A', 8) if inst_own > 60 else \
                         ('B', 5)  if inst_own > 40 else ('C', 3) if inst_own > 20 else ('D', 0)
        score += i_sc

        ms = market_score.get('score', 50)
        # M — Market Direction (15 pts)
        # O'Neil: el mercado arrastra el 75% de las acciones.
        # Con market score <60 (no confirmed uptrend) = 0 pts.
        # Esto explica por qué scores altos en mercado débil son raros.
        m_grade, m_sc = ('A', 15) if ms >= 80 else \
                         ('B', 10) if ms >= 70 else \
                         ('C', 5)  if ms >= 60 else \
                         ('D', 0)   # <60 = UPTREND UNDER PRESSURE o peor → 0 pts
        score += m_sc

        # Normalizar score a escala 0-100 real según máximo posible con mercado actual
        # Max absoluto = 100 (20+15+15+10+15+10+15). Sin M = 85.
        # Escalar para que el gauge siempre refleje la calidad relativa al mercado:
        # score_display = round(score / 85 * 100) si m_sc==0, sino score (ya es /100)
        max_possible = 85 + m_sc  # 85 sin M, 90/95/100 con M parcial/total
        score_display = round(min(100, score / max_possible * 100)) if max_possible > 0 else score

        # ML
        volatility    = hist['Close'].pct_change().std() * np.sqrt(252) * 100
        if isinstance(volatility, pd.Series): volatility = float(volatility.iloc[0])
        price_mom_20d = (_s(hist['Close'].iloc[-1]) / _s(hist['Close'].iloc[-20]) - 1) * 100 \
                        if len(hist) >= 20 else 0.0
        ml_prob = ml.predict({
            'earnings_growth': earn_g, 'revenue_growth': rev_g, 'eps_growth': eps_g,
            'rs_rating': rs_rating,   'volume_ratio': vol_ratio, 'inst_ownership': inst_own,
            'pct_from_high': pct_from_hi, 'volatility': volatility / 100, 'price_momentum': price_mom_20d,
        })

        return {
            'ticker'      : ticker,
            'name'        : info.get('shortName', ticker),
            'sector'      : info.get('sector', 'N/A'),
            'industry'    : info.get('industry', 'N/A'),
            'market_cap'  : market_cap,
            'price'       : price,
            'score'       : score_display,
            'ml_probability': ml_prob,
            'grades'      : {'C': c_grade, 'A': a_grade, 'N': n_grade,
                             'S': s_grade, 'L': l_grade, 'I': i_grade, 'M': m_grade},
            'scores'      : {'C': c_sc, 'A': a_sc, 'N': n_sc,
                             'S': s_sc, 'L': l_sc, 'I': i_sc, 'M': m_sc},
            'metrics'     : {
                'earnings_growth': earn_g, 'revenue_growth': rev_g, 'eps_growth': eps_g,
                'pct_from_high': pct_from_hi, 'volume_ratio': vol_ratio, 'rs_rating': rs_rating,
                'inst_ownership': inst_own, 'market_score': ms,
                'market_phase': market_score.get('phase', 'N/A'),
                'volatility': volatility, 'price_momentum': price_mom_20d,
            },
            'ibd_ratings' : {
                'composite': composite, 'rs': rs_rating, 'eps': eps_rating,
                'smr': smr, 'acc_dis': acc_dis, 'atr_percent': atr_pct,
                'pe_ratio': info.get('trailingPE', 0) or 0,
                'roe': roe, 'sales_growth': rev_g,
            },
            'trend_template': trend_result,
            'week_52_range' : {
                'high': trend_result.get('values', {}).get('high_52w', high52),
                'low' : trend_result.get('values', {}).get('low_52w', hist['Low'].min()),
                'current_position': (price / high52 * 100) if high52 else 0,
            },
        }
    except Exception as e:
        import traceback
        logger.warning(f"Error calculando {ticker}: {e}\n{traceback.format_exc()}")
        return None


# ==============================================================================
# SCAN PRINCIPAL (batch optimizado, caché, pre-filtros)
# ==============================================================================

def scan_sp500(min_score: int = 60, min_composite: int = 0,
               require_stage2: bool = False, max_results: int = 30) -> list:
    """
    Escanea el S&P 500 completo con arquitectura optimizada:
      1. Descarga histórico en lotes batch (una llamada HTTP por lote de 50)
      2. Descarga info fundamental con rate limiting gentil
      3. Pre-filtra por precio/volumen/market cap
      4. Calcula RS percentil sobre universo completo
      5. Analiza cada acción sin llamadas HTTP adicionales
    """
    sp500 = get_sp500_tickers()
    spy_hist = get_spy_history()

    # ── Progress UI ──────────────────────────────────────────────────────────
    progress = st.progress(0)
    status   = st.empty()

    # ── PASO 1: Batch download histórico (lotes de BATCH_SIZE) ───────────────
    status.markdown(f"""
    <div class="phase-box">
        <span style="font-family:'VT323',monospace;color:{COLORS['primary']};font-size:1.1rem;">
        [1/4] DESCARGANDO HISTÓRICO EN BATCH — {len(sp500)} acciones
        </span>
    </div>""", unsafe_allow_html=True)
    progress.progress(0.05)

    hist_data: dict[str, pd.DataFrame] = {}
    batches = [sp500[i:i+BATCH_SIZE] for i in range(0, len(sp500), BATCH_SIZE)]
    for idx, batch in enumerate(batches):
        batch_result = download_batch_history(tuple(batch), period="1y")
        hist_data.update(batch_result)
        progress.progress(0.05 + 0.25 * (idx + 1) / len(batches))

    # ── PASO 2: Info fundamental ─────────────────────────────────────────────
    status.markdown(f"""
    <div class="phase-box">
        <span style="font-family:'VT323',monospace;color:{COLORS['primary']};font-size:1.1rem;">
        [2/4] DESCARGANDO DATOS FUNDAMENTALES
        </span>
    </div>""", unsafe_allow_html=True)
    progress.progress(0.30)
    info_data = download_batch_info(tuple(sp500))

    # ── PASO 3: Pre-filtro ───────────────────────────────────────────────────
    status.markdown(f"""
    <div class="phase-box">
        <span style="font-family:'VT323',monospace;color:{COLORS['primary']};font-size:1.1rem;">
        [3/4] PRE-FILTRANDO UNIVERSO
        </span>
    </div>""", unsafe_allow_html=True)
    progress.progress(0.55)
    filtered = pre_filter_tickers(sp500, hist_data, info_data)

    # ── PASO 4: RS percentil sobre universo completo ─────────────────────────
    rs_universe = compute_rs_scores_universe(filtered, hist_data, spy_hist)

    # ── PASO 5: Análisis CAN SLIM ────────────────────────────────────────────
    status.markdown(f"""
    <div class="phase-box">
        <span style="font-family:'VT323',monospace;color:{COLORS['primary']};font-size:1.1rem;">
        [4/4] CALCULANDO SCORES CAN SLIM — {len(filtered)} acciones pre-filtradas
        </span>
    </div>""", unsafe_allow_html=True)
    progress.progress(0.60)

    ibd_calc     = IBDRatingsCalculator()
    trend_engine = MinerviniTrendTemplate()
    ml           = CANSlimMLPredictor()
    market_score = MarketAnalyzer().calculate_market_score()

    candidates = []
    for i, t in enumerate(filtered):
        result = calculate_can_slim_metrics(
            ticker=t,
            hist=hist_data.get(t),
            info=info_data.get(t, {}),
            spy_hist=spy_hist,
            rs_universe=rs_universe,
            market_score=market_score,
            ibd_calc=ibd_calc,
            trend_engine=trend_engine,
            ml=ml,
        )
        if result is None:
            continue
        # Filtros adicionales configurables
        if result['score'] < min_score:
            continue
        if min_composite > 0 and result['ibd_ratings']['composite'] < min_composite:
            continue
        if require_stage2 and not result['trend_template']['all_pass']:
            continue
        candidates.append(result)
        progress.progress(0.60 + 0.38 * (i + 1) / max(len(filtered), 1))

    progress.progress(1.0)
    status.empty()
    progress.empty()

    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:max_results]


# ==============================================================================
# VISUALIZACIONES
# ==============================================================================

def create_score_gauge(score: int, title: str = "CAN SLIM Score") -> go.Figure:
    color = COLORS['primary'] if score >= 80 else COLORS['warning'] if score >= 60 else COLORS['danger']
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 13, 'color': 'white'}},
        number={'font': {'size': 34, 'color': color}},
        gauge={
            'axis'       : {'range': [0, 100], 'tickcolor': 'white'},
            'bar'        : {'color': color, 'thickness': 0.75},
            'bgcolor'    : COLORS['bg_dark'],
            'borderwidth': 2, 'bordercolor': COLORS['bg_card'],
            'steps'      : [
                {'range': [0, 60],  'color': hex_to_rgba(COLORS['danger'],  0.2)},
                {'range': [60, 80], 'color': hex_to_rgba(COLORS['warning'], 0.2)},
                {'range': [80,100], 'color': hex_to_rgba(COLORS['primary'], 0.2)},
            ],
            'threshold'  : {'line': {'color': 'white', 'width': 3}, 'thickness': 0.8, 'value': score},
        }
    ))
    fig.update_layout(paper_bgcolor=COLORS['bg_dark'], font={'color': 'white'},
                      height=240, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_grades_radar(grades: dict) -> go.Figure:
    cats   = ['C', 'A', 'N', 'S', 'L', 'I', 'M']
    g_map  = {'A': 100, 'B': 75, 'C': 50, 'D': 25, 'F': 0}
    values = [g_map.get(grades.get(c, 'F'), 0) for c in cats]
    values.append(values[0]); cats.append(cats[0])
    fig = go.Figure(go.Scatterpolar(
        r=values, theta=cats, fill='toself',
        fillcolor=hex_to_rgba(COLORS['primary'], 0.3),
        line=dict(color=COLORS['primary'], width=2),
        marker=dict(size=7, color=COLORS['primary'])
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color='white', gridcolor=COLORS['bg_card']),
            angularaxis=dict(color='white', gridcolor=COLORS['bg_card']),
            bgcolor=COLORS['bg_dark']
        ),
        paper_bgcolor=COLORS['bg_dark'], font=dict(color='white'),
        title=dict(text="Calificaciones CAN SLIM", font=dict(color='white', size=13)),
        height=320, margin=dict(l=50, r=50, t=50, b=30)
    )
    return fig


def create_ibd_radar(ibd: dict) -> go.Figure:
    cats   = ['Composite', 'RS', 'EPS', 'Sales', 'ROE']
    values = [
        ibd.get('composite', 50), ibd.get('rs', 50), ibd.get('eps', 50),
        min(100, max(0, 50 + (ibd.get('sales_growth', 0) or 0))),
        min(100, (ibd.get('roe', 0) or 0) * 2),
    ]
    values.append(values[0]); cats.append(cats[0])
    fig = go.Figure(go.Scatterpolar(
        r=values, theta=cats, fill='toself',
        fillcolor=hex_to_rgba(COLORS['ibd_blue'], 0.3),
        line=dict(color=COLORS['ibd_blue'], width=2),
        marker=dict(size=7, color=COLORS['ibd_blue'])
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color='white', gridcolor=COLORS['border']),
            angularaxis=dict(color='white', gridcolor=COLORS['border']),
            bgcolor=COLORS['bg_dark']
        ),
        paper_bgcolor=COLORS['bg_dark'], font=dict(color='white'),
        title=dict(text="Perfil IBD", font=dict(color='white', size=13)),
        height=290, margin=dict(l=40, r=40, t=40, b=30)
    )
    return fig


def create_market_dashboard(market_data: dict) -> go.Figure:
    """
    Panel simplificado: solo SPY con precio, SMA50, SMA200.
    El dashboard de 4 gráficos (SPY/QQQ/IWM/VIX) era visualmente ruido sin valor accionable.
    Lo que importa es: ¿está el SPY sobre sus medias? Eso lo muestra este único gráfico.
    """
    if not market_data or 'data' not in market_data:
        return go.Figure()

    score  = market_data.get('score', 50)
    phase  = market_data.get('phase', 'N/A')
    color  = market_data.get('color', '#888888')
    data   = market_data.get('data', {})
    signals = market_data.get('signals', [])

    fig = go.Figure()

    if 'SPY' in data:
        spy = data['SPY']['data']
        cl  = spy['Close']
        idx = spy.index

        sma200 = cl.rolling(200).mean()
        sma50  = cl.rolling(50).mean()

        # SMA 200 (rojo)
        fig.add_trace(go.Scatter(x=idx, y=sma200, name='SMA 200',
                                  line=dict(color='#f23645', width=1.5, dash='dash'),
                                  hovertemplate='SMA200: $%{y:.2f}'))
        # SMA 50 (naranja)
        fig.add_trace(go.Scatter(x=idx, y=sma50, name='SMA 50',
                                  line=dict(color='#ff9800', width=1.5, dash='dot'),
                                  hovertemplate='SMA50: $%{y:.2f}'))
        # Precio SPY
        fig.add_trace(go.Scatter(x=idx, y=cl, name='SPY',
                                  line=dict(color=COLORS['primary'], width=2.5),
                                  hovertemplate='SPY: $%{y:.2f}<br>%{x}'))

    signal_text = '  ·  '.join(signals[:3]) if signals else 'Sin señales'
    fig.update_layout(
        title=dict(
            text=f"S&P 500 (SPY)  ·  Market Score: <b>{score}/100</b>  ·  {phase}",
            font=dict(family='VT323, monospace', size=17, color=color), x=0.5
        ),
        paper_bgcolor=COLORS['bg_dark'], plot_bgcolor=COLORS['bg_dark'],
        font=dict(color='#888', family='Courier New, monospace', size=11),
        height=300, margin=dict(l=50, r=20, t=50, b=40),
        xaxis=dict(gridcolor=COLORS['bg_card'], showgrid=True, zeroline=False, color='#666'),
        yaxis=dict(gridcolor=COLORS['bg_card'], showgrid=True, zeroline=False,
                   tickprefix='$', color='#666'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02,
                    xanchor='right', x=1, bgcolor='rgba(0,0,0,0)'),
        hovermode='x unified',
    )
    fig.add_annotation(
        text=f"Señales: {signal_text}",
        xref="paper", yref="paper", x=0.01, y=0.02,
        showarrow=False, font=dict(size=10, color='#555', family='Courier New'), align='left'
    )
    return fig


def create_ml_feature_importance(ml: CANSlimMLPredictor) -> go.Figure:
    imp = ml.get_feature_importance()
    fig = go.Figure(go.Bar(
        x=list(imp.keys()), y=list(imp.values()),
        marker_color=COLORS['primary'],
        text=[f'{v:.1%}' for v in imp.values()], textposition='auto'
    ))
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'], plot_bgcolor=COLORS['bg_dark'],
        font=dict(color='white'),
        title=dict(text="Importancia de Factores ML", font=dict(color='white')),
        xaxis=dict(color='white', gridcolor=COLORS['bg_card']),
        yaxis=dict(color='white', gridcolor=COLORS['bg_card']),
        height=290
    )
    return fig


# ==============================================================================
# COMPONENTES UI: IBD PANEL & TREND TEMPLATE
# ==============================================================================

def render_ibd_panel(ibd: dict):
    composite = ibd.get('composite', 0)
    rs        = ibd.get('rs', 0)
    eps       = ibd.get('eps', 0)
    smr       = ibd.get('smr', 'C')
    acc_dis   = ibd.get('acc_dis', 'C')
    atr       = ibd.get('atr_percent', 0)
    pe        = ibd.get('pe_ratio', 0)
    roe       = ibd.get('roe', 0)

    c_color = COLORS['primary'] if composite >= 80 else COLORS['warning'] if composite >= 60 else COLORS['danger']

    hc1, hc2 = st.columns([2, 1])
    with hc1:
        st.markdown('<h3>📊 RATINGS IBD</h3>', unsafe_allow_html=True)
    with hc2:
        st.markdown(f"<div style='font-family:VT323,monospace;color:{c_color};text-align:right;"
                    f"font-size:1.5rem;letter-spacing:2px;margin-top:10px;'>COMPOSITE: {composite}</div>",
                    unsafe_allow_html=True)
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div style='text-align:center;padding:15px;background:rgba(33,150,243,.1);
        border-radius:10px;border:1px solid rgba(33,150,243,.3);'>
        <div style='color:#aaa;font-size:.8rem;margin-bottom:5px;font-family:Courier New,monospace;'>RS RATING</div>
        <div style='color:#2196F3;font-size:2rem;font-family:VT323,monospace;'>{rs}</div>
        <div style='color:#666;font-size:.7rem;font-family:Courier New,monospace;'>vs S&P 500</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style='text-align:center;padding:15px;background:rgba(76,175,80,.1);
        border-radius:10px;border:1px solid rgba(76,175,80,.3);'>
        <div style='color:#aaa;font-size:.8rem;margin-bottom:5px;font-family:Courier New,monospace;'>EPS RATING</div>
        <div style='color:#4CAF50;font-size:2rem;font-family:VT323,monospace;'>{eps}</div>
        <div style='color:#666;font-size:.7rem;font-family:Courier New,monospace;'>Growth YoY</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        smr_c = COLORS['primary'] if smr == 'A' else COLORS['warning'] if smr == 'B' else \
                COLORS['danger'] if smr == 'D' else COLORS['neutral']
        st.markdown(f"""
        <div style='text-align:center;padding:15px;background:rgba(255,152,0,.1);
        border-radius:10px;border:1px solid rgba(255,152,0,.3);'>
        <div style='color:#aaa;font-size:.8rem;margin-bottom:5px;font-family:Courier New,monospace;'>SMR GRADE</div>
        <div style='color:{smr_c};font-size:2rem;font-family:VT323,monospace;'>{smr}</div>
        <div style='color:#666;font-size:.7rem;font-family:Courier New,monospace;'>Sales/Margins/ROE</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c4, c5, c6, c7 = st.columns(4)
    with c4: st.metric("A/D Rating", acc_dis, help="Accumulation/Distribution 50d")
    with c5: st.metric("ATR %",      f"{atr}%", help="Volatilidad promedio")
    with c6: st.metric("P/E Ratio",  f"{pe:.1f}" if pe else "N/A")
    with c7: st.metric("ROE",        f"{roe:.1f}%", help="Return on Equity")


def render_trend_template(trend: dict):
    criteria = trend.get('criteria', {})
    score    = trend.get('score', 0)
    stage    = trend.get('stage', '')
    all_pass = trend.get('all_pass', False)

    sc_color = COLORS['primary'] if all_pass else COLORS['warning']
    hc1, hc2 = st.columns([2, 1])
    with hc1:
        st.markdown('<h3>🎯 TREND TEMPLATE MINERVINI</h3>', unsafe_allow_html=True)
    with hc2:
        st.markdown(f"<div style='font-family:VT323,monospace;color:{sc_color};text-align:right;"
                    f"font-size:1.5rem;letter-spacing:2px;margin-top:10px;'>{score}/8</div>",
                    unsafe_allow_html=True)

    stage_c = COLORS['primary'] if 'Stage 2' in stage else \
              COLORS['danger'] if 'Stage 4' in stage else COLORS['warning']
    st.markdown(f"<div style='font-family:VT323,monospace;color:{stage_c};font-size:1.1rem;"
                f"text-align:right;letter-spacing:1px;margin-top:-10px;'>▸ {stage.upper()}</div>",
                unsafe_allow_html=True)
    st.markdown("---")

    items = list(criteria.items())
    mid   = len(items) // 2
    col1, col2 = st.columns(2)
    for i, (criterion, passed) in enumerate(items):
        with col1 if i < mid else col2:
            if passed: st.success(f"✓ {criterion}")
            else:      st.error(f"✗ {criterion}")

    st.markdown("---")
    if all_pass:
        st.success("✅ **TODOS LOS CRITERIOS CUMPLIDOS** — Stage 2 Confirmado")
    else:
        st.warning(f"⚠️ **{score}/8 criterios cumplidos** — Revisar condiciones técnicas")


# ==============================================================================
# DISPLAY RESULTADOS GUARDADOS
# ==============================================================================

def display_saved_results():
    if not st.session_state.scan_candidates:
        return False

    candidates = st.session_state.scan_candidates
    scan_time  = st.session_state.scan_timestamp

    st.markdown(f"""
    <div class="terminal-box">
        <div style="font-family:'VT323',monospace;color:{COLORS['primary']};font-size:1.1rem;">
            [SCAN COMPLETE // {scan_time}]
        </div>
        <div style="font-family:'VT323',monospace;font-size:1.5rem;margin-top:5px;">
            ▸ {len(candidates)} CANDIDATOS CAN SLIM DETECTADOS — UNIVERSO: S&P 500
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<h2>🏆 TOP CANDIDATOS CAN SLIM</h2>', unsafe_allow_html=True)
    cols = st.columns(min(3, len(candidates)))
    for i, col in enumerate(cols):
        if i < len(candidates):
            c = candidates[i]
            with col:
                st.plotly_chart(create_score_gauge(c['score']), use_container_width=True, key=f"gauge_{i}")
                grades_html = ''.join(
                    f'<span class="grade-badge grade-{c["grades"][g]}">{g}</span>'
                    for g in ['C', 'A', 'N', 'S', 'L', 'I', 'M']
                )
                stage_pass = "✅" if c['trend_template']['all_pass'] else f"{c['trend_template']['score']}/8"
                st.markdown(f"""
                <div class="terminal-box" style="text-align:center;padding:15px;">
                    <div style="font-family:'VT323',monospace;color:{COLORS['primary']};font-size:1.8rem;">{c['ticker']}</div>
                    <div style="font-family:'Courier New',monospace;color:#888;font-size:11px;margin:4px 0;">{c['name'][:32]}</div>
                    <div style="margin:8px 0;">{grades_html}</div>
                    <div style="font-family:'VT323',monospace;color:{COLORS['ibd_blue']};font-size:1rem;">
                        IBD Composite: {c['ibd_ratings']['composite']}
                    </div>
                    <div style="font-family:'VT323',monospace;color:{COLORS['primary']};font-size:1rem;">
                        ML: {c['ml_probability']:.1%} | Stage: {stage_pass}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<h2>📋 RESULTADOS DETALLADOS</h2>', unsafe_allow_html=True)
    max_r  = st.session_state.last_scan_params.get('max_results', 30)
    rows   = []
    for c in candidates[:max_r]:
        rows.append({
            'Ticker'    : c['ticker'],
            'Nombre'    : c['name'][:28],
            'Sector'    : c['sector'],
            'Score'     : c['score'],
            'Composite' : c['ibd_ratings']['composite'],
            'RS'        : c['ibd_ratings']['rs'],
            'EPS'       : c['ibd_ratings']['eps'],
            'SMR'       : c['ibd_ratings']['smr'],
            'A/D'       : c['ibd_ratings']['acc_dis'],
            'Stage'     : f"{c['trend_template']['score']}/8",
            'ML Prob'   : f"{c['ml_probability']:.0%}",
            'C':c['grades']['C'],'A':c['grades']['A'],'N':c['grades']['N'],
            'S':c['grades']['S'],'L':c['grades']['L'],'I':c['grades']['I'],'M':c['grades']['M'],
            'EPS G%'    : f"{min(999.0, c['metrics']['earnings_growth']):.1f}%",
            'Del High'  : f"{c['metrics']['pct_from_high']:.1f}%",
            'VolRatio'  : f"{c['metrics']['volume_ratio']:.2f}x",
            'MktCap$B'  : f"${c['market_cap']:.1f}B",
        })
    df = pd.DataFrame(rows)

    def c_score(val):
        try:
            s = int(val)
            col = COLORS['primary'] if s >= 80 else COLORS['warning'] if s >= 60 else COLORS['danger']
            return f'color:{col};font-weight:bold'
        except: return ''

    def c_grade(val):
        grade_colors = {'A': COLORS['primary'], 'B': COLORS['warning'], 'C': COLORS['danger']}
        color = grade_colors.get(str(val), COLORS['neutral'])
        return f"color:{color};font-weight:bold"

    styled = df.style \
        .applymap(c_score, subset=['Score', 'Composite', 'RS', 'EPS']) \
        .applymap(c_grade, subset=['C','A','N','S','L','I','M'])
    st.dataframe(styled, use_container_width=True, height=580)

    csv = df.to_csv(index=False)
    st.download_button("📥 DESCARGAR CSV", data=csv,
                       file_name=f"canslim_sp500_{scan_time.replace(':','-')}.csv",
                       mime="text/csv")
    if st.button("🗑️ LIMPIAR RESULTADOS", type="secondary"):
        st.session_state.scan_candidates  = []
        st.session_state.scan_timestamp   = None
        st.session_state.last_scan_params = {}
        st.rerun()
    return True


# ==============================================================================
# CONTENIDO EDUCATIVO
# ==============================================================================

EDUCATIONAL_CONTENT = {
    "guia_completa": """
### 📚 Los 7 Criterios CAN SLIM + Ratings IBD

**C — Current Quarterly Earnings**
Buscar crecimiento >25% vs mismo trimestre año anterior. Idealmente >50% con aceleración.
EPS Rating IBD normaliza el crecimiento en escala percentil 1-99.

**A — Annual Earnings Growth**
Crecimiento EPS 3-5 años >25% anual con consistencia. ROE >17%.
SMR Rating (A-D) evalúa Sales, Margins y ROE de forma compuesta.

**N — New Products / New Highs**
Nuevos productos, gestión innovadora o breakouts desde máximos históricos.
El precio debe estar cerca de máximos (dentro del -5% al +5%).

**S — Supply and Demand**
Volumen superior al promedio (1.5x-3x) en días alcistas.
Accumulation/Distribution Rating (A-E) mide presión compradora 50 días.

**L — Leader or Laggard**
RS Rating >80: top 20% del mercado. Ponderación IBD 40/20/20/20.
Evitar stocks débiles "porque están baratos".

**I — Institutional Sponsorship**
Fondos institucionales >40% del float, número de fondos creciendo.
Presencia de gestores de calidad (Fidelity, BlackRock, Vanguard).

**M — Market Direction**
Factor más importante. No operar contra la tendencia.
Índices sobre SMA 50/200, VIX bajo, confirmación de uptrend.
""",

    "ibd_ratings_guide": """
### 📊 Ratings IBD

**Composite Rating (0-99)**: 30% EPS + 30% RS + 40% fundamentales. 99 = mejor 1%.

**RS Rating (0-99)**: Performance relativa vs S&P 500. Ponderación 40/20/20/20 (4 trimestres).
En esta herramienta se calcula como percentil real sobre el universo S&P 500.

**EPS Rating (0-99)**: Crecimiento de ganancias trimestrales YoY normalizado a percentil.

**SMR Rating (A-D)**: Sales (40%) + Margins (30%) + ROE (30%).

**Accumulation/Distribution (A-E)**: Ratio volumen días up/down en ventana 50 días.
A = compra institucional fuerte. E = distribución institucional.
""",

    "trend_template_minervini": """
### 🎯 Trend Template de Mark Minervini (Stage 2)

8 criterios para confirmar Stage 2 (Advancing Phase) según Weinstein-Minervini:

1. Precio > SMA 50
2. Precio > SMA 150
3. Precio > SMA 200
4. SMA 50 > SMA 150
5. SMA 150 > SMA 200
6. SMA 200 en tendencia alcista (vs hace 20 días)
7. Precio > 30% del mínimo de 52 semanas
8. Precio dentro del 25% del máximo de 52 semanas

Stage 2 confirmado = 8/8. Operar solo en Stage 2.
""",

    "reglas_operacion": """
### 📋 Reglas de Operación

**Entradas**: Breakout desde base de consolidación con volumen superior al promedio.
Piramidación solo cuando la primera posición sube 2-3%.
Máximo 10-12% del portafolio por posición. 5-10 stocks diversificados.

**Filtros IBD recomendados**: Composite >80, RS >80, EPS >80, SMR A/B, A/D A/B, Stage 2 (8/8).

**Gestión de Riesgo**: Stop loss 7-8% desde compra. Trailing stop a breakeven en +8-10%.
Tomar ganancias parciales en +20-25%. Cash es posición válida en downtrend.
""",

    "senales_venta": """
### 🚨 Señales de Venta

**Técnicas**: Climax top (parabólico + volumen extremo), pérdida de SMA 50 con volumen,
key reversal day, volumen alto sin progreso de precio.

**Ratings IBD**: Composite <60, RS <70, A/D cambia a D/E, Trend Template <6/8.

**Fundamentales**: 2 trimestres consecutivos de desaceleración de earnings,
recorte de estimaciones, rotación sectorial visible.

**Reglas fijas**: Stop 7-8%, trailing stop, profit taking en +20-25%.
""",

    "errores_comunes": """
### ⚠️ Errores Comunes

**Psicológicos**: Negar pérdidas, promediar a la baja, miedo a comprar en máximos, overtrading.

**Análisis**: Ignorar el M (mercado), focalizarse en precio bajo, descuidar el volumen,
comprar antes del breakout, ignorar ratings IBD.

**Ejecución**: Órdenes de mercado en apertura, posiciones >20%, no definir stop antes de entrar.

**Timing**: Comprar antes de earnings (riesgo de gap -20/-30%), forzar operaciones sin setup válido.

**Disciplina**: Cambiar reglas a mitad de la operación, dejar que resultados recientes sesguen el juicio.
"""
}


# ==============================================================================
# CSS GLOBAL (terminal aesthetic)
# ==============================================================================

def get_global_css() -> str:
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp {{ background: {COLORS['bg_dark']}; }}

        h1,h2,h3,h4,h5,h6 {{
            font-family: 'VT323', monospace !important;
            color: {COLORS['primary']} !important;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        h1 {{
            font-size: 3.5rem !important;
            text-shadow: 0 0 20px {hex_to_rgba(COLORS['primary'], 0.4)};
            border-bottom: 2px solid {COLORS['primary']};
            padding-bottom: 15px;
            margin-bottom: 30px !important;
        }}
        h2 {{
            font-size: 2.2rem !important;
            color: #00d9ff !important;
            border-left: 4px solid {COLORS['primary']};
            padding-left: 15px;
            margin-top: 40px !important;
        }}
        h3 {{
            font-size: 1.8rem !important;
            color: {COLORS['warning']} !important;
            margin-top: 30px !important;
        }}
        h4 {{
            font-size: 1.5rem !important;
            color: #9c27b0 !important;
        }}
        p, li {{
            font-family: 'Courier New', monospace;
            color: #ccc !important;
            line-height: 1.8;
            font-size: 0.95rem;
        }}
        strong {{ color: {COLORS['primary']}; font-weight: bold; }}
        blockquote {{
            border-left: 3px solid {COLORS['warning']};
            margin: 20px 0; padding-left: 20px;
            color: {COLORS['warning']}; font-style: italic;
        }}
        hr {{
            border: none; height: 1px;
            background: linear-gradient(90deg, transparent, {COLORS['primary']}, transparent);
            margin: 40px 0;
        }}
        ul {{ list-style: none; padding-left: 0; }}
        ul li::before {{ content: "▸ "; color: {COLORS['primary']}; margin-right: 8px; }}

        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
        .stTabs [data-baseweb="tab"] {{
            font-family: 'VT323', monospace !important;
            font-size: 1.1rem !important; letter-spacing: 1px;
            background: {COLORS['bg_dark']}; color: #888;
            border: 1px solid {COLORS['bg_card']};
            border-radius: 8px 8px 0 0;
        }}
        .stTabs [aria-selected="true"] {{
            background: {COLORS['bg_card']}; color: {COLORS['primary']};
            border-bottom: 2px solid {COLORS['primary']};
        }}

        .terminal-box {{
            background: linear-gradient(135deg, {COLORS['bg_dark']} 0%, {COLORS['bg_card']} 100%);
            border: 1px solid {hex_to_rgba(COLORS['primary'], 0.27)};
            border-radius: 8px; padding: 25px; margin: 20px 0;
            box-shadow: 0 0 15px {hex_to_rgba(COLORS['primary'], 0.07)};
        }}
        .phase-box {{
            background: {COLORS['bg_dark']};
            border-left: 3px solid {COLORS['primary']};
            padding: 20px; margin: 15px 0; border-radius: 0 8px 8px 0;
        }}
        .highlight-quote {{
            background: {hex_to_rgba(COLORS['primary'], 0.07)};
            border: 1px solid {hex_to_rgba(COLORS['primary'], 0.2)};
            border-radius: 8px; padding: 20px; margin: 20px 0;
            font-family: 'VT323', monospace; font-size: 1.2rem;
            color: {COLORS['primary']}; text-align: center;
        }}
        .risk-box {{
            background: linear-gradient(135deg, #1a0f0f 0%, #261a1a 100%);
            border: 1px solid {hex_to_rgba(COLORS['danger'], 0.27)};
            border-radius: 8px; padding: 20px; margin: 15px 0;
        }}
        .strategy-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr));
            gap: 15px; margin: 20px 0;
        }}
        .strategy-card {{
            background: {COLORS['bg_dark']}; border: 1px solid #2a3f5f;
            border-radius: 8px; padding: 15px;
        }}
        .strategy-card h4 {{ color: {COLORS['primary']} !important; font-size: 1.1rem !important; }}

        .metric-card {{
            background: {COLORS['bg_dark']}; border: 1px solid {COLORS['bg_card']};
            border-radius: 10px; padding: 15px; text-align: center;
        }}
        .grade-badge {{
            display: inline-block; width: 30px; height: 30px;
            border-radius: 6px; text-align: center; line-height: 30px;
            font-weight: bold; font-size: 14px; margin: 2px;
            font-family: 'VT323', monospace;
        }}
        .grade-A {{ background:rgba(0,255,173,.2); color:{COLORS['primary']}; border:1px solid {COLORS['primary']}; }}
        .grade-B {{ background:rgba(255,152,0,.2); color:{COLORS['warning']}; border:1px solid {COLORS['warning']}; }}
        .grade-C {{ background:rgba(242,54,69,.2);  color:{COLORS['danger']};  border:1px solid {COLORS['danger']}; }}
        .grade-D {{ background:rgba(136,136,136,.2);color:#888;               border:1px solid #888; }}

        .market-badge {{
            display:inline-block; padding:5px 15px; border-radius:20px;
            font-family:'VT323',monospace; letter-spacing:1px; font-size:1rem;
        }}
        .saved-results-banner {{
            background: linear-gradient(90deg, {hex_to_rgba(COLORS['primary'], 0.2)}, transparent);
            border-left: 4px solid {COLORS['primary']};
            padding: 10px 15px; border-radius: 0 8px 8px 0; margin: 10px 0;
        }}
        .methodology-section h3 {{
            color: {COLORS['primary']} !important;
            border-bottom: 2px solid {COLORS['bg_card']}; padding-bottom: 10px;
        }}
        .methodology-section h4 {{ color: {COLORS['warning']} !important; }}
    </style>
    """


# ==============================================================================
# RENDER PRINCIPAL
# ==============================================================================

def render():
    init_session_state()
    st.markdown(get_global_css(), unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    market_analyzer = MarketAnalyzer()
    market_status   = market_analyzer.calculate_market_score()

    st.markdown(f"""
    <div style="text-align:center;margin-bottom:40px;">
        <div style="font-family:'VT323',monospace;font-size:1rem;color:#666;margin-bottom:10px;">
            [SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]
        </div>
        <h1>🎯 CAN SLIM SCANNER PRO</h1>
        <div style="font-family:'VT323',monospace;color:#00d9ff;font-size:1.2rem;letter-spacing:3px;margin-bottom:15px;">
            IBD RATINGS // MINERVINI TREND TEMPLATE // ML PREDICTIVO // S&P 500
        </div>
        <div>
            <span class="market-badge" style="background:{hex_to_rgba(market_status['color'],.2)};
            color:{market_status['color']};border:1px solid {market_status['color']};">
                ▸ M-MARKET: {market_status['phase']} ({market_status['score']}/100)
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚀 SCANNER S&P 500",
        "📊 ANÁLISIS DETALLADO",
        "📚 METODOLOGÍA",
        "🤖 ML PREDICTIVO",
        "📈 BACKTESTING",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — SCANNER S&P 500
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        sp500_list = get_sp500_tickers()

        # ── Detectar caché nocturno ───────────────────────────────────────────
        cached = load_cached_scan()

        if cached:
            gen_at    = datetime.fromisoformat(cached["generated_at"])
            age_min   = int((datetime.utcnow() - gen_at).total_seconds() / 60)
            age_str   = f"{age_min // 60}h {age_min % 60}m" if age_min >= 60 else f"{age_min}m"
            cache_n   = len(cached.get("candidates", []))
            cache_sp  = cached.get("sp500_count", len(sp500_list))
            st.markdown(f"""
            <div class="terminal-box" style="border-color:{hex_to_rgba(COLORS['primary'],.5)};">
                <div style="font-family:'VT323',monospace;color:{COLORS['primary']};font-size:1.5rem;letter-spacing:2px;">
                    ✅ SCANNER DISPONIBLE — S&P 500 ANALIZADO HOY
                </div>
                <div style="font-family:'Courier New',monospace;color:#aaa;font-size:.88rem;margin-top:10px;line-height:2;">
                    🕐 &nbsp;Última actualización: <strong style="color:{COLORS['primary']};">{gen_at.strftime('%d/%m/%Y a las %H:%M')}</strong>
                    &nbsp;(hace {age_str})
                    <br>
                    📊 &nbsp;Activos analizados: <strong style="color:{COLORS['primary']};">{cache_sp} acciones</strong>
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    🏆 &nbsp;Candidatos encontrados: <strong style="color:{COLORS['primary']};">{cache_n}</strong>
                </div>
                <div style="font-family:'Courier New',monospace;color:#555;font-size:.78rem;margin-top:6px;">
                    Análisis completo · Pre-filtros aplicados · RS percentil real · IBD Ratings · Trend Template · Actualización diaria automática
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="terminal-box" style="border-color:{hex_to_rgba(COLORS['warning'],.4)};">
                <div style="font-family:'VT323',monospace;color:{COLORS['warning']};font-size:1.5rem;letter-spacing:2px;">
                    🔄 SCANNER ACTUALIZÁNDOSE — USA EL SCAN EN VIVO
                </div>
                <div style="font-family:'Courier New',monospace;color:#aaa;font-size:.88rem;margin-top:10px;line-height:2;">
                    El análisis diario automático estará disponible a partir de las <strong>05:00 hora española</strong>.<br>
                    Puedes lanzar un análisis en vivo ahora — tardará unos <strong>5-10 minutos</strong>.
                </div>
                <div style="font-family:'Courier New',monospace;color:#555;font-size:.78rem;margin-top:6px;">
                    Análisis diario · S&P 500 completo · Pre-filtros automáticos · IBD Ratings · Trend Template
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Controles de filtro ───────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            min_score = st.slider("Score Mínimo CAN SLIM", 0, 100, 60,
                                  help="Filtrar acciones con score igual o mayor")
        with col2:
            min_composite = st.number_input("IBD Composite Mín.", 0, 99, 70,
                                            help="Composite Rating IBD mínimo")
        with col3:
            max_results   = st.number_input("Máx Resultados", 5, 100, 30)
        with col4:
            require_stage2 = st.checkbox("Solo Stage 2 (8/8)", value=False,
                                          help="Solo acciones con Trend Template completo")

        # ── Botones de acción ─────────────────────────────────────────────────
        btn_col1, btn_col2 = st.columns([3, 1])
        with btn_col1:
            if cached:
                load_cache_btn = st.button(
                    f"⚡ CARGAR ANÁLISIS DE HOY — {cache_n} CANDIDATOS",
                    use_container_width=True, type="primary"
                )
                scan_live_btn = False
            else:
                load_cache_btn = False
                scan_live_btn = st.button(
                    "🔍 ESCANEAR S&P 500 EN VIVO",
                    use_container_width=True, type="primary"
                )
        with btn_col2:
            force_live = st.button("🔄 Forzar Scan en Vivo", use_container_width=True,
                                   help="Ignora el caché y escanea en tiempo real")

        # ── Expanders informativos ────────────────────────────────────────────
        with st.expander("📊 VER CONDICIONES DE MERCADO"):
            st.plotly_chart(create_market_dashboard(market_status), use_container_width=True)
            st.markdown('<div class="phase-box"><strong>SEÑALES TÉCNICAS:</strong></div>',
                        unsafe_allow_html=True)
            for sig in market_status['signals']:
                st.markdown(f"- {sig}")

        with st.expander("⚙️ CONFIGURACIÓN DE PRE-FILTROS (scan en vivo)"):
            c1, c2, c3 = st.columns(3)
            with c1: st.number_input("Precio mínimo ($)",     0.0,  500.0, float(MIN_PRICE))
            with c2: st.number_input("Volumen mín. (miles)", 100,  10000, int(MIN_AVG_VOLUME/1000))
            with c3: st.number_input("Market Cap mín. ($B)", 0.0,  50.0,  float(MIN_MARKET_CAP_B))

        # ── Mostrar resultados guardados en session_state ─────────────────────
        display_saved_results()

        # ── Acción: cargar caché nocturno ─────────────────────────────────────
        if load_cache_btn and cached:
            raw = cached.get("candidates", [])
            # Aplicar filtros locales al caché (instantáneo, sin red)
            filtered_cache = [
                c for c in raw
                if c.get("score", 0) >= min_score
                and c.get("ibd_ratings", {}).get("composite", 0) >= min_composite
                and (not require_stage2 or c.get("trend_template", {}).get("all_pass", False))
            ][:max_results]

            if filtered_cache:
                st.session_state.scan_candidates  = filtered_cache
                ts = datetime.fromisoformat(cached["generated_at"])
                st.session_state.scan_timestamp   = f"análisis del {ts.strftime('%d/%m/%Y %H:%M')}"
                st.session_state.last_scan_params = {
                    "min_score": min_score, "max_results": max_results,
                    "min_composite": min_composite, "require_stage2": require_stage2,
                }
                st.rerun()
            else:
                st.markdown(f"""
                <div class="risk-box">
                    <div style="font-family:'VT323',monospace;color:{COLORS['warning']};font-size:1.2rem;">
                        ⚠️ SIN CANDIDATOS CON ESTOS FILTROS
                    </div>
                    <p>El caché tiene {len(raw)} candidatos pero ninguno cumple los filtros actuales.
                    Prueba reduciendo Score Mínimo o IBD Composite.</p>
                </div>""", unsafe_allow_html=True)

        # ── Acción: scan en vivo (botón principal o forzado) ──────────────────
        if scan_live_btn or force_live:
            st.session_state.scan_candidates = []
            st.session_state.scan_timestamp  = None

            st.markdown(f"""
            <div class="highlight-quote">
                INICIANDO SCAN EN VIVO — S&P 500 ({len(sp500_list)} ACCIONES)<br>
                <span style="font-size:.9rem;color:#888;">
                Arquitectura batch: ~{len(sp500_list)//BATCH_SIZE + 1} lotes de {BATCH_SIZE} acciones
                </span>
            </div>""", unsafe_allow_html=True)

            candidates = scan_sp500(
                min_score=min_score,
                min_composite=min_composite,
                require_stage2=require_stage2,
                max_results=max_results,
            )

            if candidates:
                st.session_state.scan_candidates  = candidates
                st.session_state.scan_timestamp   = datetime.now().strftime('%H:%M:%S') + " (en vivo)"
                st.session_state.last_scan_params = {
                    "min_score": min_score, "max_results": max_results,
                    "min_composite": min_composite, "require_stage2": require_stage2,
                }
                st.rerun()
            else:
                st.markdown(f"""
                <div class="risk-box">
                    <div style="font-family:'VT323',monospace;color:{COLORS['warning']};font-size:1.2rem;">
                        ⚠️ SIN CANDIDATOS
                    </div>
                    <p>No se encontraron acciones con los criterios seleccionados.
                    Considera reducir el Score Mínimo o el IBD Composite.</p>
                </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — ANÁLISIS DETALLADO
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        if st.session_state.scan_candidates:
            st.markdown(f"""
            <div class="saved-results-banner">
                📊 <strong>{len(st.session_state.scan_candidates)} candidatos guardados</strong>
                del scan de las {st.session_state.scan_timestamp}
            </div>""", unsafe_allow_html=True)

        ticker_input = st.text_input("Ingresar Ticker para Análisis Detallado", "AAPL").upper()

        if st.button("ANALIZAR", type="primary"):
            with st.spinner(f"Descargando datos de {ticker_input}..."):
                try:
                    hist_single = download_batch_history((ticker_input,), period="1y").get(ticker_input)
                    # CACHE + RETRY: evita YFRateLimitError en análisis individual
                    info_single = get_single_ticker_info(ticker_input)
                    spy_hist    = get_spy_history()
                    rs_univ     = {ticker_input: 50}  # RS puntual (no universo completo)

                    # RS aproximado vs SPY para análisis individual
                    if hist_single is not None and not spy_hist.empty:
                        # RS individual: calcular retorno relativo vs SPY y mapear a escala 1-99
                        # No usar compute_rs_scores_universe con 1 ticker (daría percentil trivial)
                        try:
                            close = hist_single['Close'].copy()
                            if hasattr(close.index, 'tz') and close.index.tz is not None:
                                close.index = close.index.tz_localize(None)
                            spy_close = spy_hist['Close'].copy()
                            if hasattr(spy_close.index, 'tz') and spy_close.index.tz is not None:
                                spy_close.index = spy_close.index.tz_localize(None)
                            merged = pd.merge(close.rename('stock'), spy_close.rename('spy'),
                                              left_index=True, right_index=True, how='inner')
                            if len(merged) >= 100:
                                days_per_q = 63
                                weights = [0.40, 0.20, 0.20, 0.20]
                                period_scores = []
                                for i in range(4):
                                    end   = len(merged) - 1 if i == 0 else len(merged) - 1 - i * days_per_q
                                    start = end - days_per_q
                                    if start < 0:
                                        period_scores.append(0.0)
                                        continue
                                    s_ret = merged['stock'].iloc[end] / merged['stock'].iloc[start] - 1
                                    m_ret = merged['spy'].iloc[end]   / merged['spy'].iloc[start]   - 1
                                    rel   = (1 + s_ret) / (1 + m_ret) - 1 if abs(m_ret) > 0.001 else s_ret
                                    period_scores.append(rel)
                                weighted = sum(w * s for w, s in zip(weights, period_scores))
                                # Mapear retorno relativo a escala 1-99 usando curva sigmoidea simple
                                # weighted > 0.30 → ~99, 0 → ~50, < -0.30 → ~1
                                import math
                                rs_val = round(50 + weighted * 100)
                                rs_val = max(1, min(99, rs_val))
                                rs_univ = {ticker_input: rs_val}
                            else:
                                rs_univ = {ticker_input: 50}
                        except Exception:
                            rs_univ = {ticker_input: 50}

                    result = calculate_can_slim_metrics(
                        ticker=ticker_input,
                        hist=hist_single,
                        info=info_single,
                        spy_hist=spy_hist,
                        rs_universe=rs_univ,
                        market_score=market_status,
                        ibd_calc=IBDRatingsCalculator(),
                        trend_engine=MinerviniTrendTemplate(),
                        ml=CANSlimMLPredictor(),
                    )

                    if result is None:
                        # Diagnóstico detallado para depuración
                        hist_ok   = hist_single is not None and not hist_single.empty
                        hist_rows = len(hist_single) if hist_ok else 0
                        hist_cols = list(hist_single.columns) if hist_ok else []
                        info_ok   = bool(info_single)
                        spy_ok    = not spy_hist.empty

                        st.markdown(f"""
                        <div class="risk-box">
                            <div style="font-family:'VT323',monospace;color:{COLORS['danger']};font-size:1.2rem;">
                                ❌ NO SE PUDO CALCULAR ANÁLISIS — {ticker_input}
                            </div>
                            <p style="font-family:'Courier New',monospace;font-size:.85rem;color:#ccc;margin-top:10px;">
                                Diagnóstico:<br>
                                • Histórico precio: {'✅ ' + str(hist_rows) + ' filas, cols: ' + str(hist_cols) if hist_ok else '❌ Sin datos'}<br>
                                • Info fundamental: {'✅ OK' if info_ok else '❌ Sin datos (yfinance bloqueado temporalmente)'}<br>
                                • SPY histórico: {'✅ OK' if spy_ok else '❌ Sin datos'}
                            </p>
                            {'<p style="font-family:Courier New,monospace;font-size:.82rem;color:#ff9800;">⚠️ El histórico tiene menos de 50 filas o columnas incorrectas — problema con yfinance/MultiIndex.</p>' if hist_ok and (hist_rows < 50 or not {"Close","High","Low","Open","Volume"}.issubset(set(hist_cols))) else ''}
                            {'<p style="font-family:Courier New,monospace;font-size:.82rem;color:#888;">ℹ️ Espera 30 segundos y vuelve a intentarlo (rate limit de Yahoo Finance).</p>' if not info_ok else ''}
                        </div>""", unsafe_allow_html=True)
                    else:
                        with st.expander("🔍 Debug Info"):
                            st.write(f"RS Rating (percentil): {result['ibd_ratings']['rs']}")
                            st.write(f"EPS Rating: {result['ibd_ratings']['eps']}")
                            st.write(f"Composite: {result['ibd_ratings']['composite']}")
                            st.write(f"ML Prob: {result['ml_probability']:.1%}")

                        col1, col2, col3 = st.columns([1, 1.2, 1])
                        with col1:
                            st.markdown('<h3>CAN SLIM SCORE</h3>', unsafe_allow_html=True)
                            st.plotly_chart(create_score_gauge(result['score']),
                                            use_container_width=True, key=f"cs_{ticker_input}")
                            st.plotly_chart(create_grades_radar(result['grades']),
                                            use_container_width=True, key=f"radar_{ticker_input}")
                            rs = result['ibd_ratings']['rs']
                            rs_c = COLORS['primary'] if rs > 80 else COLORS['warning'] if rs > 60 else COLORS['danger']
                            ml_p = result['ml_probability']
                            ml_c = COLORS['primary'] if ml_p > 0.7 else COLORS['warning'] if ml_p > 0.5 else COLORS['danger']
                            st.markdown(f"""
                            <div class="metric-card" style="margin-top:10px;">
                                <div style="font-family:'VT323',monospace;color:#888;font-size:.9rem;">RS RATING</div>
                                <div style="font-family:'VT323',monospace;color:{rs_c};font-size:2.5rem;">{rs}</div>
                            </div>
                            <div class="metric-card" style="margin-top:8px;">
                                <div style="font-family:'VT323',monospace;color:#888;font-size:.9rem;">ML PROBABILITY</div>
                                <div style="font-family:'VT323',monospace;color:{ml_c};font-size:2.5rem;">{ml_p:.1%}</div>
                            </div>""", unsafe_allow_html=True)
                        with col2:
                            render_ibd_panel(result['ibd_ratings'])
                            st.plotly_chart(create_ibd_radar(result['ibd_ratings']),
                                            use_container_width=True, key=f"ibd_{ticker_input}")
                        with col3:
                            render_trend_template(result['trend_template'])
                            with st.expander("📐 Niveles Técnicos"):
                                tv = result['trend_template'].get('values', {})
                                if tv:
                                    st.dataframe(pd.DataFrame({
                                        'Métrica': ['SMA 50','SMA 150','SMA 200','52W High','52W Low','Dist. High','Dist. Low'],
                                        'Valor'  : [
                                            f"${tv.get('sma_50',0):.2f}",    f"${tv.get('sma_150',0):.2f}",
                                            f"${tv.get('sma_200',0):.2f}",   f"${tv.get('high_52w',0):.2f}",
                                            f"${tv.get('low_52w',0):.2f}",   f"{tv.get('distance_from_high',0):.1f}%",
                                            f"{tv.get('distance_from_low',0):.1f}%",
                                        ]
                                    }), use_container_width=True, hide_index=True)

                        # Gráfico de precios
                        st.markdown("---")
                        if hist_single is not None and len(hist_single) > 0:
                            fig = go.Figure()
                            fig.add_trace(go.Candlestick(
                                x=hist_single.index,
                                open=hist_single['Open'], high=hist_single['High'],
                                low=hist_single['Low'],   close=hist_single['Close'], name='Price'
                            ))
                            for period, color, dash in [(50, COLORS['warning'], 'solid'),
                                                         (150, '#FF9800', 'dash'),
                                                         (200, COLORS['primary'], 'solid')]:
                                if len(hist_single) >= period:
                                    fig.add_trace(go.Scatter(
                                        x=hist_single.index,
                                        y=hist_single['Close'].rolling(period).mean(),
                                        name=f'SMA {period}',
                                        line=dict(color=color, width=1+(period==200), dash=dash)
                                    ))
                            fig.update_layout(
                                title=f"{result['name']} ({ticker_input}) — ${result['price']:.2f}",
                                paper_bgcolor=COLORS['bg_dark'], plot_bgcolor=COLORS['bg_dark'],
                                font=dict(color='white'),
                                xaxis=dict(gridcolor=COLORS['bg_card']),
                                yaxis=dict(gridcolor=COLORS['bg_card']),
                                height=500, showlegend=True,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        with st.expander("📋 Métricas Completas"):
                            st.table(pd.DataFrame({
                                'Métrica': ['Market Cap','EPS Growth','Rev Growth','Inst. Own','Vol Ratio',
                                            'From High','Volatility','Price Mom','Market Score',
                                            'IBD Composite','IBD RS','IBD EPS','IBD SMR','A/D','ATR%','P/E','ROE'],
                                'Valor'  : [
                                    f"${result['market_cap']:.1f}B",
                                    f"{result['metrics']['earnings_growth']:.1f}%",
                                    f"{result['metrics']['revenue_growth']:.1f}%",
                                    f"{result['metrics']['inst_ownership']:.1f}%",
                                    f"{result['metrics']['volume_ratio']:.2f}x",
                                    f"{result['metrics']['pct_from_high']:.1f}%",
                                    f"{result['metrics']['volatility']:.1f}%",
                                    f"{result['metrics']['price_momentum']:.1f}%",
                                    f"{result['metrics']['market_score']:.0f}/100",
                                    f"{result['ibd_ratings']['composite']}/99",
                                    f"{result['ibd_ratings']['rs']}/99",
                                    f"{result['ibd_ratings']['eps']}/99",
                                    result['ibd_ratings']['smr'],
                                    result['ibd_ratings']['acc_dis'],
                                    f"{result['ibd_ratings']['atr_percent']:.2f}%",
                                    f"{result['ibd_ratings']['pe_ratio']:.1f}",
                                    f"{result['ibd_ratings']['roe']:.1f}%",
                                ]
                            }))
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")
                    import traceback; st.code(traceback.format_exc())

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — METODOLOGÍA
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        if st.session_state.scan_candidates:
            st.markdown(f"""
            <div class="saved-results-banner">
                📊 <strong>{len(st.session_state.scan_candidates)} candidatos guardados</strong>
                del scan de las {st.session_state.scan_timestamp}
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="text-align:center;margin-bottom:30px;">
            <div style="font-family:'VT323',monospace;font-size:1rem;color:#666;margin-bottom:5px;">
                [KNOWLEDGE BASE // LOADED]
            </div>
            <h2 style="border-left:none;padding-left:0;text-align:center;">📚 METODOLOGÍA COMPLETA</h2>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="methodology-section">', unsafe_allow_html=True)
        for key in ['guia_completa','ibd_ratings_guide','trend_template_minervini',
                    'reglas_operacion','senales_venta','errores_comunes']:
            st.markdown(EDUCATIONAL_CONTENT[key])
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — ML PREDICTIVO
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        if st.session_state.scan_candidates:
            st.markdown(f"""
            <div class="saved-results-banner">
                📊 <strong>{len(st.session_state.scan_candidates)} candidatos guardados</strong>
                del {st.session_state.scan_timestamp}
            </div>""", unsafe_allow_html=True)

        st.markdown('<h2>🤖 ML PREDICTIVO — ESTADO ACTUAL</h2>', unsafe_allow_html=True)

        # Estado honesto del ML
        ml_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canslim_ml_model.pkl")
        ml_trained = os.path.exists(ml_model_path)

        st.markdown(f"""
        <div class="terminal-box" style="border-color:{'rgba(0,255,173,.4)' if ml_trained else 'rgba(255,152,0,.4)'};">
            <div style="font-family:'VT323',monospace;color:{'#00ffad' if ml_trained else '#ff9800'};font-size:1.3rem;">
                {'✅ MODELO ENTRENADO — ACTIVO' if ml_trained else '⏳ MODELO EN FORMACIÓN — SIN DATOS HISTÓRICOS AÚN'}
            </div>
            <div style="font-family:'Courier New',monospace;color:#aaa;font-size:.85rem;margin-top:10px;line-height:1.8;">
                {'El archivo <code>canslim_ml_model.pkl</code> existe. El modelo usará predicciones reales cuando tenga suficientes datos.' if ml_trained else
                'El modelo está implementado (GradientBoostingClassifier) pero devuelve 50% porque aún no tiene datos históricos reales.<br>'
                'Las predicciones se activarán automáticamente cuando tengamos suficientes scans acumulados (~6 meses).'}
            </div>
            <div style="font-family:'Courier New',monospace;color:#555;font-size:.78rem;margin-top:8px;">
                Modelo guardado en: canslim_ml_model.pkl (mismo directorio que la app)
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<h3>HOJA DE RUTA</h3>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="terminal-box">
                <div style="font-family:'Courier New',monospace;color:#ccc;font-size:.85rem;line-height:1.9;">
                    <strong style="color:#00ffad;">Ahora:</strong> Cada análisis diario guarda métricas en histórico<br>
                    <strong style="color:#ff9800;">Mes 3:</strong> Calcular retorno real de candidatos del mes 1 vs SPY<br>
                    <strong style="color:#ff9800;">Mes 4-6:</strong> ~200 samples → primer entrenamiento real<br>
                    <strong style="color:#2196F3;">Mes 6-12:</strong> ~500 samples → validación temporal y despliegue<br>
                    <strong style="color:#4CAF50;">Mes 6+:</strong> Probabilidades reales en el scanner
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown('<h3>IMPORTANCIA DE FACTORES</h3>', unsafe_allow_html=True)
            ml_viz = CANSlimMLPredictor()
            st.plotly_chart(create_ml_feature_importance(ml_viz), use_container_width=True)

        st.markdown('<h3>PREDICCIÓN INDIVIDUAL</h3>', unsafe_allow_html=True)
        st.info("⚠️ Probabilidades actuales = 50% placeholder hasta tener datos históricos acumulados.")
        pred_ticker = st.text_input("Ticker para análisis ML", "NVDA").upper()
        if st.button("ANALIZAR", disabled=not SKLEARN_AVAILABLE):
            with st.spinner(f"Analizando {pred_ticker}..."):
                try:
                    h = download_batch_history((pred_ticker,), period="1y").get(pred_ticker)
                    i = get_single_ticker_info(pred_ticker)
                    spy = get_spy_history()
                    rs  = compute_rs_scores_universe([pred_ticker], {pred_ticker: h}, spy) if h is not None else {pred_ticker: 50}
                    res = calculate_can_slim_metrics(
                        pred_ticker, h, i, spy, rs, market_status,
                        IBDRatingsCalculator(), MinerviniTrendTemplate(), CANSlimMLPredictor()
                    )
                    if res:
                        prob  = res['ml_probability']
                        color = COLORS['primary'] if prob > 0.7 else COLORS['warning'] if prob > 0.5 else COLORS['danger']
                        st.markdown(f"""
                        <div class="terminal-box" style="text-align:center;">
                            <div style="font-family:'VT323',monospace;color:#888;font-size:1rem;letter-spacing:2px;">
                                PROBABILIDAD DE OUTPERFORMANCE vs SPY (3 meses)
                            </div>
                            <div style="font-family:'VT323',monospace;color:{color};font-size:5rem;
                            margin:10px 0;text-shadow:0 0 20px {color}66;">{prob:.1%}</div>
                            <div style="font-family:'Courier New',monospace;color:#555;font-size:.82rem;">
                                {'⚠️ Valor placeholder — modelo en formación' if not ml_trained else '✅ Predicción del modelo entrenado'}
                            </div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.error(f"No se pudo analizar {pred_ticker}")
                except Exception as e:
                    import traceback
                    st.error(f"Error inesperado analizando {ticker_input}: {e}")
                    with st.expander("🔍 Detalle del error (para debug)"):
                        st.code(traceback.format_exc())

    # TAB 5 — BACKTESTING
    # ══════════════════════════════════════════════════════════════════════════
    with tab5:
        if st.session_state.scan_candidates:
            st.markdown(f"""
            <div class="saved-results-banner">
                📊 <strong>{len(st.session_state.scan_candidates)} candidatos guardados</strong>
                del {st.session_state.scan_timestamp}
            </div>""", unsafe_allow_html=True)

        st.markdown('<h2>📈 BACKTESTING — ESTADO Y HOJA DE RUTA</h2>', unsafe_allow_html=True)

        # Honest state
        st.markdown(f"""
        <div class="risk-box">
            <div style="font-family:'VT323',monospace;color:{COLORS['warning']};font-size:1.3rem;">
                ⚠️ LOS RESULTADOS NUMÉRICOS ACTUALES SON DEMO — NO REALES
            </div>
            <div style="font-family:'Courier New',monospace;color:#ccc;font-size:.85rem;margin-top:10px;line-height:1.8;">
                Los datos que aparecen (+145.3%, Sharpe 1.85...) son <strong>valores hardcodeados de demostración</strong>.<br>
                Zipline es excesivamente complejo para Streamlit Cloud.<br>
                <strong style="color:#ff9800;">Recomendado: implementar con pandas (2-3 días) — funciona en cloud.</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<h3>ESTRATEGIA PROPUESTA (PANDAS)</h3>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="terminal-box">
                <div style="font-family:'Courier New',monospace;color:#ccc;font-size:.85rem;line-height:1.9;">
                    <strong style="color:#00ffad;">Entrada:</strong> Score &gt;80 AND Composite &gt;90 AND Stage2 AND Market &gt;70<br>
                    <strong style="color:#f23645;">Stop loss:</strong> -7% desde entrada<br>
                    <strong style="color:#00ffad;">Take profit:</strong> +20-25%<br>
                    <strong style="color:#ff9800;">Posición:</strong> Equal-weight, max 10% cartera<br>
                    <strong style="color:#2196F3;">Universo:</strong> S&P 500, 5 años histórico<br>
                    <strong style="color:#2196F3;">Benchmark:</strong> Buy&Hold SPY mismo período
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown('<h3>OPCIONES DE IMPLEMENTACIÓN</h3>', unsafe_allow_html=True)
            st.markdown("""
            | Librería | Tiempo | Cloud | Recomendación |
            |----------|--------|-------|---------------|
            | **pandas** | 2-3 días | ✅ | ⭐ Empezar aquí |
            | vectorbt | 1 semana | ✅ | Opción 2 |
            | backtrader | 1 semana | ✅ | Opción 3 |
            | zipline (actual) | 1-2 meses | ❌ | Descartar |
            """)

        st.markdown('<h3>DEMO (VALORES NO REALES)</h3>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1: start_date = st.date_input("Fecha Inicio", datetime(2020, 1, 1))
        with col2: end_date   = st.date_input("Fecha Fin",    datetime(2023, 12, 31))
        with col3: capital    = st.number_input("Capital ($)", 10_000, 1_000_000, 100_000)

        with st.expander("⚙️ Parámetros de Estrategia"):
            max_pos  = st.slider("Máximo Posiciones", 5, 20, 10)
            stop_l   = st.slider("Stop Loss %",       3, 15, 7)
            profit_t = st.slider("Profit Target %",  10, 50, 20)

        if st.button("▶️ VER DEMO (VALORES NO REALES)", type="secondary"):
            st.warning("⚠️ Recuerda: estos números son placeholders de demostración, no resultados reales.")
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("TOTAL RETURN", "+145.3%", "+45.2% vs SPY")
            mc2.metric("SHARPE RATIO", "1.85",    "vs 1.2 SPY")
            mc3.metric("MAX DRAWDOWN", "-12.4%",  "vs -20.1% SPY")
            mc4.metric("WIN RATE",     "68%",     "de operaciones")

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
    <hr>
    <div style="text-align:center;padding:20px;">
        <p style="font-family:'VT323',monospace;color:#444;font-size:.9rem;">
            [END OF TRANSMISSION // CANSLIM_SCANNER_PRO_v4.0.0]<br>
            [UNIVERSO: S&P 500 // IBD RATINGS // MINERVINI TREND TEMPLATE // ML]<br>
            [STATUS: ACTIVE // OPTIMIZADO PARA COMUNIDADES DE TRADING]
        </p>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# FASTAPI (condicional)
# ==============================================================================

if FASTAPI_AVAILABLE:
    app = FastAPI(title="CAN SLIM Pro API", version="4.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"],
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    class TickerRequest(BaseModel):
        ticker: str; include_ml: bool = True

    @app.get("/")
    async def root():
        return {"message": "CAN SLIM Pro API v4.0.0", "universe": "S&P 500"}

    @app.get("/market/status")
    async def market_status_endpoint():
        return MarketAnalyzer().calculate_market_score()

    @app.post("/analyze")
    async def analyze(req: TickerRequest):
        h    = download_batch_history((req.ticker,), "1y").get(req.ticker)
        info = get_single_ticker_info(req.ticker)
        spy  = get_spy_history()
        rs   = compute_rs_scores_universe([req.ticker], {req.ticker: h}, spy) if h is not None else {req.ticker: 50}
        ms   = MarketAnalyzer().calculate_market_score()
        res  = calculate_can_slim_metrics(req.ticker, h, info, spy, rs, ms,
                                          IBDRatingsCalculator(), MinerviniTrendTemplate(), CANSlimMLPredictor())
        if res is None:
            raise HTTPException(status_code=404, detail=f"No data for {req.ticker}")
        return res

    @app.get("/universe/sp500")
    async def get_universe():
        tickers = get_sp500_tickers()
        return {"count": len(tickers), "tickers": tickers}
else:
    app = None


if __name__ == "__main__":
    render()
