# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
from config import get_market_index, get_cnn_fear_greed
import requests
import streamlit.components.v1 as components
import time
import yfinance as yf
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ─── investpy opcional ───────────────────────────────────────────────────────
try:
    import investpy
    INVESTPY_AVAILABLE = True
except ImportError:
    INVESTPY_AVAILABLE = False

# ─── Helpers generales ───────────────────────────────────────────────────────
def get_timestamp() -> str:
    return datetime.now().strftime('%H:%M:%S')


# ─── CSS compartido ──────────────────────────────────────────────────────────
BASE_STYLES = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.container {
    border: 1px solid #1a1e26; border-radius: 10px; overflow: hidden;
    background: #11141a; width: 100%; height: 480px;
    display: flex; flex-direction: column;
}
.header {
    background: #0c0e12; padding: 10px 12px;
    border-bottom: 1px solid #1a1e26;
    display: flex; justify-content: space-between; align-items: center;
    flex-shrink: 0; position: relative;
}
.title { color: white; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
.tooltip-wrapper { position: static; display: inline-block; }
.tooltip-btn {
    width: 24px; height: 24px; border-radius: 50%;
    background: #1a1e26; border: 2px solid #555;
    display: flex; align-items: center; justify-content: center;
    color: #aaa; font-size: 14px; font-weight: bold; cursor: help;
}
.tooltip-content {
    display: none; position: fixed; width: 300px;
    background-color: #1e222d; color: #eee; text-align: left;
    padding: 15px; border-radius: 10px; z-index: 99999;
    font-size: 12px; border: 2px solid #3b82f6;
    box-shadow: 0 15px 40px rgba(0,0,0,0.9); line-height: 1.5;
    left: 50%; top: 50%; transform: translate(-50%, -50%);
    white-space: normal; word-wrap: break-word;
}
.tooltip-wrapper:hover .tooltip-content { display: block; }
.content { background: #11141a; flex: 1; overflow-y: auto; padding: 10px; }
.content::-webkit-scrollbar { width: 6px; }
.content::-webkit-scrollbar-track { background: #0c0e12; }
.content::-webkit-scrollbar-thumb { background: #2a3f5f; border-radius: 3px; }
.update-timestamp {
    text-align: center; color: #555; font-size: 10px; padding: 6px 0;
    font-family: 'Courier New', monospace;
    border-top: 1px solid #1a1e26; background: #0c0e12; flex-shrink: 0;
}
"""

def wrap_module_html(title: str, content: str, timestamp: str,
                     tooltip: str = "", badge: str = "",
                     extra_header: str = "") -> str:
    """
    Genera el HTML completo de un módulo con header, contenido y footer.
    Evita repetir ~50 líneas de estructura en cada módulo.
    """
    tooltip_html = ""
    if tooltip:
        tooltip_html = f"""
        <div class="tooltip-wrapper">
            <div class="tooltip-btn">?</div>
            <div class="tooltip-content">{tooltip}</div>
        </div>"""

    badge_html = f'<span style="background:#2a3f5f;color:#00ffad;padding:2px 6px;border-radius:3px;font-size:9px;font-weight:bold;">{badge}</span>' if badge else ""

    right_side = ""
    if badge_html or extra_header or tooltip_html:
        right_side = f'<div style="display:flex;align-items:center;gap:6px;">{badge_html}{extra_header}{tooltip_html}</div>'

    return f"""<!DOCTYPE html><html><head>
    <meta charset="UTF-8">
    <style>{BASE_STYLES}</style>
    </head><body>
    <div class="container">
        <div class="header">
            <div class="title">{title}</div>
            {right_side}
        </div>
        <div class="content">{content}</div>
        <div class="update-timestamp">Updated: {timestamp}</div>
    </div>
    </body></html>"""


# ─────────────────────────────────────────────────────────────────────────────
# DICCIONARIO DE TRADUCCIONES
# ─────────────────────────────────────────────────────────────────────────────
EVENT_TRANSLATIONS = {
    "Nonfarm Payrolls": "Nóminas No Agrícolas",
    "Unemployment Rate": "Tasa de Desempleo",
    "ADP Nonfarm Employment": "Empleo ADP",
    "Initial Jobless Claims": "Solicitudes de Desempleo",
    "Continuing Jobless Claims": "Solicitudes Continuas de Desempleo",
    "JOLTS Job Openings": "Vacantes JOLTS",
    "Average Hourly Earnings": "Salario por Hora Promedio",
    "Labor Force Participation Rate": "Tasa de Participación Laboral",
    "CPI": "IPC (Inflación)",
    "Core CPI": "IPC Subyacente",
    "PPI": "IPP (Precios Productor)",
    "Core PPI": "IPP Subyacente",
    "PCE Price Index": "Índice de Precios PCE",
    "Core PCE": "PCE Subyacente",
    "GDP": "PIB",
    "GDP Growth Rate": "Crecimiento del PIB",
    "Retail Sales": "Ventas al Por Menor",
    "Core Retail Sales": "Ventas al Por Menor Subyacentes",
    "Industrial Production": "Producción Industrial",
    "Manufacturing Production": "Producción Manufacturera",
    "Durable Goods Orders": "Pedidos de Bienes Duraderos",
    "Core Durable Goods Orders": "Pedidos Bienes Duraderos Subyacentes",
    "Factory Orders": "Órdenes de Fábrica",
    "Business Inventories": "Inventarios Empresariales",
    "ISM Manufacturing PMI": "PMI Manufacturero ISM",
    "ISM Services PMI": "PMI Servicios ISM",
    "S&P Global Manufacturing PMI": "PMI Manufacturero S&P Global",
    "S&P Global Services PMI": "PMI Servicios S&P Global",
    "S&P Global Composite PMI": "PMI Compuesto S&P Global",
    "Chicago PMI": "PMI de Chicago",
    "Philadelphia Fed Manufacturing Index": "Índice Manufacturero Fed Filadelfia",
    "Empire State Manufacturing Index": "Índice Manufacturero Empire State",
    "Dallas Fed Manufacturing Index": "Índice Manufacturero Fed Dallas",
    "Richmond Fed Manufacturing Index": "Índice Manufacturero Fed Richmond",
    "Kansas Fed Manufacturing Index": "Índice Manufacturero Fed Kansas",
    "CB Consumer Confidence": "Confianza del Consumidor CB",
    "Michigan Consumer Sentiment": "Sentimiento del Consumidor Michigan",
    "Michigan Consumer Expectations": "Expectativas del Consumidor Michigan",
    "Michigan Current Conditions": "Condiciones Actuales Michigan",
    "Conference Board Leading Index": "Índice Adelantado Conference Board",
    "Building Permits": "Permisos de Construcción",
    "Housing Starts": "Inicio de Viviendas",
    "New Home Sales": "Ventas de Viviendas Nuevas",
    "Existing Home Sales": "Ventas de Viviendas Existentes",
    "Pending Home Sales": "Ventas de Viviendas Pendientes",
    "S&P/Case-Shiller Home Price Index": "Índice de Precios S&P/Case-Shiller",
    "FHFA House Price Index": "Índice de Precios FHFA",
    "Mortgage Applications": "Solicitudes de Hipotecas",
    "Trade Balance": "Balanza Comercial",
    "Exports": "Exportaciones",
    "Imports": "Importaciones",
    "Treasury Budget": "Presupuesto del Tesoro",
    "Budget Balance": "Balance Presupuestario",
    "Public Debt": "Deuda Pública",
    "Fed Interest Rate Decision": "Decisión de Tipos de la Fed",
    "FOMC Statement": "Declaración FOMC",
    "FOMC Minutes": "Actas FOMC",
    "FOMC Economic Projections": "Proyecciones Económicas FOMC",
    "Fed Chair Press Conference": "Rueda de Prensa del Presidente Fed",
    "Fed Chair Speech": "Discurso del Presidente Fed",
    "Fed Governor Speech": "Discurso de Gobernador Fed",
    "Fed Member Speech": "Discurso de Miembro Fed",
    "Crude Oil Inventories": "Inventarios de Petróleo Crudo",
    "EIA Crude Oil Inventories": "Inventarios EIA Petróleo Crudo",
    "API Crude Oil Inventories": "Inventarios API Petróleo Crudo",
    "Gasoline Inventories": "Inventarios de Gasolina",
    "Distillate Inventories": "Inventarios de Destilados",
    "Natural Gas Storage": "Almacenamiento de Gas Natural",
    "Heating Oil Inventories": "Inventarios de Gasóleo Calefacción",
    "Refinery Utilization": "Utilización de Refinerías",
    "Current Account": "Cuenta Corriente",
    "Capital Flows": "Flujos de Capital",
    "Foreign Bond Investment": "Inversión en Bonos Extranjeros",
    "Net Long-term TIC Flows": "Flujos TIC Largo Plazo Netos",
    "ECB Interest Rate Decision": "Decisión de Tipos del BCE",
    "ECB Deposit Facility Rate": "Tasa de Depósito BCE",
    "ECB Marginal Lending Facility": "Facilidad de Préstamo Marginal BCE",
    "ECB Main Refinancing Operations Rate": "Tasa de Refinanciación Principal BCE",
    "ECB Press Conference": "Rueda de Prensa BCE",
    "ECB President Speech": "Discurso del Presidente BCE",
    "ECB Monetary Policy Statement": "Declaración de Política Monetaria BCE",
    "ECB Account of the Monetary Policy Meeting": "Acta de la Reunión de Política Monetaria BCE",
    "Eurozone CPI": "IPC Zona Euro",
    "Eurozone Core CPI": "IPC Subyacente Zona Euro",
    "Eurozone GDP": "PIB Zona Euro",
    "Eurozone Unemployment Rate": "Tasa de Desempleo Zona Euro",
    "Eurozone Retail Sales": "Ventas al Por Menor Zona Euro",
    "Eurozone Industrial Production": "Producción Industrial Zona Euro",
    "Eurozone ZEW Economic Sentiment": "Sentimiento Económico ZEW Zona Euro",
    "Germany ZEW Economic Sentiment": "Sentimiento Económico ZEW Alemania",
    "Germany Ifo Business Climate": "Clima Empresarial Ifo Alemania",
    "Germany Ifo Current Assessment": "Evaluación Actual Ifo Alemania",
    "Germany Ifo Expectations": "Expectativas Ifo Alemania",
    "France CPI": "IPC Francia",
    "France GDP": "PIB Francia",
    "Italy CPI": "IPC Italia",
    "Spain CPI": "IPC España",
}

def translate_event(event_name: str) -> str:
    if event_name in EVENT_TRANSLATIONS:
        return EVENT_TRANSLATIONS[event_name]
    for eng, esp in EVENT_TRANSLATIONS.items():
        if eng.lower() in event_name.lower():
            return esp
    return event_name[:32] + "..." if len(event_name) > 35 else event_name


# ─────────────────────────────────────────────────────────────────────────────
# CALENDARIO ECONÓMICO
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_economic_calendar():
    """
    Devuelve eventos económicos desde HOY en adelante.
    Compara solo la FECHA (sin hora) para evitar que eventos de hoy
    aparezcan como pasados por diferencia de zona horaria.
    """
    events = []
    today_date    = datetime.now().date()
    tomorrow_date = today_date + timedelta(days=1)

    if INVESTPY_AVAILABLE:
        try:
            from_date = datetime.now().strftime('%d/%m/%Y')
            to_date   = (datetime.now() + timedelta(days=7)).strftime('%d/%m/%Y')
            calendar  = investpy.economic_calendar(
                time_zone='GMT', time_filter='time_only',
                from_date=from_date, to_date=to_date,
                countries=['united states', 'euro zone'],
                importances=['high', 'medium', 'low']
            )
            importance_map = {'high': 'High', 'medium': 'Medium', 'low': 'Low'}

            for _, row in calendar.iterrows():
                try:
                    date_str = row.get('date', '')
                    if pd.notna(date_str) and date_str != '':
                        event_date = pd.to_datetime(date_str, dayfirst=True)
                    else:
                        event_date = pd.Timestamp.now()

                    # ⬇ Comparar solo la fecha, no el timestamp completo
                    event_date_only = event_date.date()
                    if event_date_only < today_date:
                        continue

                    time_str = row.get('time', '')
                    if time_str and pd.notna(time_str):
                        try:
                            hour, minute = map(int, str(time_str).split(':'))
                            time_es = f"{(hour + 1) % 24:02d}:{minute:02d}"
                        except Exception:
                            time_es = "TBD"
                    else:
                        time_es = "TBD"

                    imp = importance_map.get(str(row.get('importance', 'medium')).lower(), 'Medium')
                    event_name_es = translate_event(str(row.get('event', 'Unknown')))

                    if event_date_only == today_date:
                        date_display, date_color = "HOY", "#00ffad"
                    elif event_date_only == tomorrow_date:
                        date_display, date_color = "MAÑANA", "#3b82f6"
                    else:
                        date_display = event_date.strftime('%d %b').upper()
                        date_color   = "#888"

                    def _safe_str(val):
                        return str(val) if pd.notna(val) else '-'

                    events.append({
                        "date": event_date, "date_display": date_display,
                        "date_color": date_color, "time": time_es,
                        "event": event_name_es, "imp": imp,
                        "val": _safe_str(row.get('actual', '-')),
                        "prev": _safe_str(row.get('previous', '-')),
                        "forecast": _safe_str(row.get('forecast', '-')),
                        "country": str(row.get('zone', 'US')).upper()
                    })
                except Exception as e:
                    logger.debug("Economic calendar row error: %s", e)
                    continue
        except Exception as e:
            logger.warning("investpy error: %s", e)

    if not events:
        return get_fallback_economic_calendar()

    events.sort(key=lambda x: (x['date'], x['time'] if x['time'] != 'TBD' else '99:99'))
    return events[:8]


def get_fallback_economic_calendar():
    today = datetime.now()
    return [
        {"date": today, "date_display": "HOY", "date_color": "#00ffad", "time": "14:30",
         "event": "Solicitudes de Desempleo", "imp": "High", "val": "-", "prev": "215K", "forecast": "218K", "country": "US"},
        {"date": today, "date_display": "HOY", "date_color": "#00ffad", "time": "16:00",
         "event": "Pedidos de Bienes Duraderos", "imp": "Medium", "val": "-", "prev": "-4.6%", "forecast": "+2.0%", "country": "US"},
        {"date": today + timedelta(days=1), "date_display": "MAÑANA", "date_color": "#3b82f6", "time": "14:30",
         "event": "PIB (Revisado)", "imp": "High", "val": "-", "prev": "2.8%", "forecast": "2.9%", "country": "US"},
        {"date": today + timedelta(days=1), "date_display": "MAÑANA", "date_color": "#3b82f6", "time": "16:00",
         "event": "Ventas de Viviendas Pendientes", "imp": "Medium", "val": "-", "prev": "+4.6%", "forecast": "+1.0%", "country": "US"},
        {"date": today + timedelta(days=2), "date_display": (today + timedelta(days=2)).strftime('%d %b').upper(),
         "date_color": "#888", "time": "14:30", "event": "IPC Subyacente", "imp": "High", "val": "-", "prev": "0.3%", "forecast": "0.2%", "country": "US"},
        {"date": today + timedelta(days=2), "date_display": (today + timedelta(days=2)).strftime('%d %b').upper(),
         "date_color": "#888", "time": "14:30", "event": "Nóminas No Agrícolas", "imp": "High", "val": "-", "prev": "143K", "forecast": "175K", "country": "US"},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# PRECIOS CRYPTO  –  paralelizado
# ─────────────────────────────────────────────────────────────────────────────
def _fetch_single_crypto(symbol_name: tuple) -> dict | None:
    """Descarga datos de un solo crypto symbol. Usado en ThreadPoolExecutor."""
    symbol, name = symbol_name
    try:
        hist = yf.Ticker(symbol).history(period="2d")
        if len(hist) >= 2:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            change_pct = ((current - prev) / prev) * 100
            price_str = f"{current:,.2f}" if current >= 1 else f"{current:.4f}"
            return {
                'symbol': symbol.replace('-USD', ''), 'name': name,
                'price': price_str, 'change': f"{change_pct:+.2f}%",
                'is_positive': change_pct >= 0
            }
    except Exception as e:
        logger.debug("Crypto fetch error %s: %s", symbol, e)
    return None


@st.cache_data(ttl=300)
def get_crypto_prices():
    crypto_symbols = {
        'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'BNB-USD': 'BNB',
        'SOL-USD': 'Solana', 'XRP-USD': 'XRP', 'ADA-USD': 'Cardano'
    }
    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(_fetch_single_crypto, item): item for item in crypto_symbols.items()}
        for future in as_completed(futures):
            data = future.result()
            if data:
                results.append(data)

    # Mantener el orden original
    order = list(crypto_symbols.keys())
    results.sort(key=lambda x: order.index(x['symbol'] + '-USD') if x['symbol'] + '-USD' in order else 99)
    return results if results else get_fallback_crypto_prices()


def get_fallback_crypto_prices():
    return [
        {"symbol": "BTC", "name": "Bitcoin",  "price": "68,984.88", "change": "-1.62%", "is_positive": False},
        {"symbol": "ETH", "name": "Ethereum", "price": "2,018.46",  "change": "-4.05%", "is_positive": False},
        {"symbol": "BNB", "name": "BNB",       "price": "618.43",    "change": "-2.76%", "is_positive": False},
        {"symbol": "SOL", "name": "Solana",    "price": "84.04",     "change": "-3.07%", "is_positive": False},
        {"symbol": "XRP", "name": "XRP",       "price": "1.40",      "change": "-2.22%", "is_positive": False},
        {"symbol": "ADA", "name": "Cardano",   "price": "0.52",      "change": "-4.20%", "is_positive": False},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# REDDIT BUZZ
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_reddit_buzz():
    try:
        url = "https://www.buzztickr.com/reddit-buzz/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        top_10_tickers = []

        for header in soup.find_all(['h2', 'h3', 'h4', 'div', 'span']):
            header_text = header.get_text(strip=True).lower()
            if 'overall' in header_text and 'top' in header_text:
                parent = header.find_parent()
                if parent:
                    links = parent.find_all('a', href=re.compile(r'/reddit-buzz/\?ticker='))
                    for link in links[:10]:
                        ticker = link.get_text(strip=True).upper()
                        if ticker and ticker not in top_10_tickers and len(ticker) <= 5:
                            top_10_tickers.append(ticker)

        if not top_10_tickers:
            seen = set()
            for link in soup.find_all('a', href=re.compile(r'/reddit-buzz/\?ticker=[A-Z]+')):
                ticker = link.get_text(strip=True).upper()
                if ticker and ticker not in seen and len(ticker) <= 5 and ticker.isalpha():
                    top_10_tickers.append(ticker)
                    seen.add(ticker)
                    if len(top_10_tickers) >= 10:
                        break

        if not top_10_tickers:
            return get_fallback_reddit_tickers()

        return {'tickers': top_10_tickers[:10], 'source': 'BuzzTickr', 'timestamp': get_timestamp()}
    except Exception as e:
        logger.warning("Reddit buzz error: %s", e)
        return get_fallback_reddit_tickers()


def get_fallback_reddit_tickers():
    return {
        'tickers': ["MSFT", "NVDA", "TSLA", "AAPL", "AMZN", "GOOGL", "META", "AMD", "PLTR", "GME"],
        'source': 'Fallback', 'timestamp': get_timestamp()
    }


@st.cache_data(ttl=3600)
def get_buzztickr_master_data():
    try:
        url = "https://www.buzztickr.com/master-buzz/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        master_data = []

        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if len(rows) > 5:
                for row in rows[1:]:
                    try:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 7:
                            ticker = cells[1].get_text(strip=True).upper()
                            if ticker and len(ticker) <= 5:
                                master_data.append({
                                    'rank':        cells[0].get_text(strip=True),
                                    'ticker':      ticker,
                                    'buzz_score':  cells[2].get_text(strip=True),
                                    'health':      cells[3].get_text(strip=True),
                                    'social_hype': cells[4].get_text(strip=True),
                                    'smart_money': cells[5].get_text(strip=True),
                                    'squeeze':     cells[6].get_text(strip=True),
                                })
                    except Exception as e:
                        logger.debug("Master buzz row error: %s", e)
                if master_data:
                    break

        if master_data:
            return {'data': master_data[:15], 'source': 'BuzzTickr Master',
                    'timestamp': get_timestamp(), 'count': len(master_data)}

        return get_fallback_master_data()
    except Exception as e:
        logger.warning("BuzzTickr master error: %s", e)
        return get_fallback_master_data()


def get_fallback_master_data():
    return {
        'data': [
            {'rank': '1', 'ticker': 'SGN',  'buzz_score': '7', 'health': '28 Weak',   'social_hype': '★★★★★', 'smart_money': '',                   'squeeze': '★★★★★ Extreme Short (70%)'},
            {'rank': '2', 'ticker': 'RUN',  'buzz_score': '7', 'health': '28 Weak',   'social_hype': '',       'smart_money': '',                   'squeeze': '★★★★★ Extreme Short (30%)'},
            {'rank': '3', 'ticker': 'ANAB', 'buzz_score': '7', 'health': '35 Weak',   'social_hype': '',       'smart_money': '',                   'squeeze': '★★★★★ Extreme Short (38%)'},
            {'rank': '4', 'ticker': 'HTZ',  'buzz_score': '7', 'health': '15 Weak',   'social_hype': '',       'smart_money': '',                   'squeeze': '★★★★★ Extreme Short (46%)'},
            {'rank': '5', 'ticker': 'DEI',  'buzz_score': '7', 'health': '25 Weak',   'social_hype': '',       'smart_money': '',                   'squeeze': '★★★★★ Extreme Short (25%)'},
            {'rank': '6', 'ticker': 'LUCK', 'buzz_score': '7', 'health': '15 Weak',   'social_hype': '',       'smart_money': '★★★★★ Whales >50%', 'squeeze': '★★★★★ Extreme Short (32%)'},
            {'rank': '7', 'ticker': 'QDEL', 'buzz_score': '7', 'health': '25 Weak',   'social_hype': '',       'smart_money': '★★★★★ Whales >50%', 'squeeze': '★★★★★ Extreme Short (25%)'},
            {'rank': '8', 'ticker': 'CAR',  'buzz_score': '7', 'health': '20 Weak',   'social_hype': '',       'smart_money': '★★★★★ Whales >50%', 'squeeze': '★★★★★ Extreme Short (48%)'},
            {'rank': '9', 'ticker': 'NVDA', 'buzz_score': '6', 'health': '80 Strong', 'social_hype': '★★★★★ Reddit Top 10', 'smart_money': '★★★★★ Whales >20%', 'squeeze': ''},
            {'rank': '10','ticker': 'MSFT', 'buzz_score': '6', 'health': '52 Hold',   'social_hype': '★★★★★ Reddit Top 10', 'smart_money': '★★★★★ Whales >20%', 'squeeze': ''},
        ],
        'source': 'BuzzTickr Master', 'timestamp': get_timestamp(), 'count': 15
    }


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL TICKER  –  paralelizado
# ─────────────────────────────────────────────────────────────────────────────
def _fetch_single_ticker(symbol_name: tuple) -> dict | None:
    symbol, name = symbol_name
    try:
        hist = yf.Ticker(symbol).history(period="2d")
        if len(hist) >= 2:
            current = hist['Close'].iloc[-1]
            prev    = hist['Close'].iloc[-2]
            change_pct = ((current - prev) / prev) * 100
            price_str = f"{current:,.2f}" if current >= 100 else f"{current:.3f}"
            return {'name': name, 'price': price_str,
                    'change': change_pct, 'is_positive': change_pct >= 0}
    except Exception as e:
        logger.debug("Ticker fetch error %s: %s", symbol, e)
    return None


@st.cache_data(ttl=60)
def get_financial_ticker_data():
    all_symbols = {
        'ES=F': 'S&P 500 FUT', 'NQ=F': 'NASDAQ FUT', 'YM=F': 'DOW FUT', 'RTY=F': 'RUSSELL FUT',
        '^N225': 'NIKKEI', '^GDAXI': 'DAX', '^FTSE': 'FTSE 100',
        'GC=F': 'GOLD', 'SI=F': 'SILVER', 'CL=F': 'CRUDE OIL', 'NG=F': 'NAT GAS',
        'AAPL': 'AAPL', 'MSFT': 'MSFT', 'GOOGL': 'GOOGL', 'AMZN': 'AMZN',
        'NVDA': 'NVDA', 'META': 'META', 'TSLA': 'TSLA',
        'BTC-USD': 'BTC', 'ETH-USD': 'ETH'
    }
    ticker_data = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_fetch_single_ticker, item): item for item in all_symbols.items()}
        for future in as_completed(futures):
            result = future.result()
            if result:
                ticker_data.append(result)
    return ticker_data


def generate_ticker_html() -> str:
    data = get_financial_ticker_data()
    if not data:
        data = [
            {'name': 'S&P 500 FUT', 'price': '5,890.25',  'change':  0.45, 'is_positive': True},
            {'name': 'NASDAQ FUT',  'price': '21,150.80', 'change': -0.23, 'is_positive': False},
            {'name': 'DOW FUT',     'price': '42,890.15', 'change':  0.67, 'is_positive': True},
            {'name': 'NIKKEI',      'price': '38,750.50', 'change':  1.24, 'is_positive': True},
            {'name': 'DAX',         'price': '21,340.75', 'change': -0.15, 'is_positive': False},
            {'name': 'GOLD',        'price': '2,865.40',  'change':  0.89, 'is_positive': True},
            {'name': 'CRUDE OIL',   'price': '73.85',     'change': -1.23, 'is_positive': False},
            {'name': 'BTC',         'price': '68,984.88', 'change': -1.62, 'is_positive': False},
        ]

    items_html = "".join(
        f'<span style="margin-right:40px;white-space:nowrap;">'
        f'<span style="color:#fff;font-weight:bold;">{d["name"]}</span> '
        f'<span style="color:#ccc;">{d["price"]}</span> '
        f'<span style="color:{"#00ffad" if d["is_positive"] else "#f23645"};">'
        f'{"▲" if d["is_positive"] else "▼"} {d["change"]:+.2f}%</span></span>'
        for d in data
    )
    all_items = items_html * 2  # duplicar para loop continuo

    return f"""
    <div style="background:linear-gradient(90deg,#0c0e12 0%,#1a1e26 50%,#0c0e12 100%);
                border-bottom:2px solid #2a3f5f;padding:12px 0;overflow:hidden;">
        <div style="display:inline-block;white-space:nowrap;
                    animation:ticker-scroll 30s linear infinite;padding-left:100%;">
            {all_items}
        </div>
    </div>
    <style>
    @keyframes ticker-scroll {{ 0% {{ transform:translateX(0); }} 100% {{ transform:translateX(-50%); }} }}
    </style>"""


# ─────────────────────────────────────────────────────────────────────────────
# SECTOR PERFORMANCE  –  paralelizado
# ─────────────────────────────────────────────────────────────────────────────
SECTOR_ETFS = {
    'XLK':  ('Technology',      'Tecnología'),
    'XLF':  ('Financials',      'Financieros'),
    'XLV':  ('Healthcare',      'Salud'),
    'XLE':  ('Energy',          'Energía'),
    'XLY':  ('Consumer Disc.',  'Consumo Discrecional'),
    'XLU':  ('Utilities',       'Utilidades'),
    'XLI':  ('Industrials',     'Industriales'),
    'XLB':  ('Materials',       'Materiales'),
    'XLP':  ('Consumer Staples','Consumo Básico'),
    'XLRE': ('Real Estate',     'Bienes Raíces'),
    'XLC':  ('Communication',   'Comunicaciones'),
}
PERIOD_MAP = {"1D": "2d", "3D": "5d", "1W": "10d", "1M": "1mo"}


def _fetch_sector(args: tuple) -> dict | None:
    symbol, names, period, timeframe = args
    name_en, name_es = names
    try:
        hist = yf.Ticker(symbol).history(period=period)
        if len(hist) < 2:
            return None
        current = hist['Close'].iloc[-1]
        if   timeframe == "1D": prev = hist['Close'].iloc[-2]
        elif timeframe == "3D": prev = hist['Close'].iloc[-4] if len(hist) >= 4 else hist['Close'].iloc[0]
        elif timeframe == "1W": prev = hist['Close'].iloc[-6] if len(hist) >= 6 else hist['Close'].iloc[0]
        else:                   prev = hist['Close'].iloc[0]
        return {
            'code': symbol, 'name': name_en, 'name_es': name_es,
            'change': ((current - prev) / prev) * 100
        }
    except Exception as e:
        logger.debug("Sector fetch error %s: %s", symbol, e)
    return None


@st.cache_data(ttl=300)
def get_sector_performance(timeframe: str = "1D"):
    period = PERIOD_MAP.get(timeframe, "2d")
    args = [(sym, names, period, timeframe) for sym, names in SECTOR_ETFS.items()]
    results = []
    with ThreadPoolExecutor(max_workers=11) as ex:
        futures = {ex.submit(_fetch_sector, a): a for a in args}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    return results if results else get_fallback_sectors(timeframe)


def get_fallback_sectors(timeframe: str = "1D"):
    base = [
        ("XLK","Technology",+6.02), ("XLF","Financials",+0.99),
        ("XLV","Healthcare",+1.01), ("XLE","Energy",+2.30),
        ("XLY","Consumer Disc.",+1.13), ("XLU","Utilities",+1.68),
        ("XLI","Industrials",+3.26), ("XLB","Materials",+3.91),
        ("XLP","Consumer Staples",+0.20), ("XLRE","Real Estate",+3.33),
        ("XLC","Communication",+1.08)
    ]
    mult = {"1D": 1, "3D": 2.5, "1W": 4, "1M": 8}.get(timeframe, 1)
    return [{'code': c, 'name': n, 'name_es': n, 'change': v * mult} for c, n, v in base]


# ─────────────────────────────────────────────────────────────────────────────
# VIX TERM STRUCTURE
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_vix_term_structure():
    try:
        try:
            vix_hist = yf.Ticker("^VIX").history(period="5d")
            if len(vix_hist) >= 3:
                current_spot = vix_hist['Close'].iloc[-1]
                prev_spot    = vix_hist['Close'].iloc[-2]
                spot_2days   = vix_hist['Close'].iloc[-3]
            else:
                raise ValueError("Insufficient VIX history")
        except Exception:
            current_spot, prev_spot, spot_2days = 17.45, 17.36, 20.37

        # Generar curva dinámica
        base_year = datetime.now().year
        months_labels = []
        for i in range(9):
            dt = datetime.now() + timedelta(days=30 * i)
            months_labels.append(dt.strftime('%b'))

        is_contango = current_spot < 20

        def build_curve(spot):
            curve = [spot]
            for i in range(1, 9):
                if is_contango:
                    curve.append(spot + (i * 0.9) + (i * i * 0.08))
                else:
                    curve.append(spot - (i * 0.3))
            return curve

        current_curve  = build_curve(current_spot)
        prev_curve     = build_curve(prev_spot)
        two_days_curve = build_curve(spot_2days)

        vix_data_pts = [
            {'month': months_labels[i],
             'current':  round(current_curve[i], 2),
             'previous': round(prev_curve[i], 2),
             'two_days': round(two_days_curve[i], 2)}
            for i in range(9)
        ]

        if current_curve[-1] > current_curve[0]:
            state, state_desc, state_color = "Contango", "Typical in calm markets - Conducive to dip buying", "#00ffad"
            explanation = ("<b>Contango:</b> Futures price &gt; Spot price. "
                          "The market expects volatility to decrease over time.")
        else:
            state, state_desc, state_color = "Backwardation", "Market stress detected - Caution advised", "#f23645"
            explanation = ("<b>Backwardation:</b> Futures price &lt; Spot price. "
                          "The market expects increased near-term volatility.")

        return {
            'data': vix_data_pts, 'current_spot': current_spot,
            'prev_spot': prev_spot, 'spot_2days': spot_2days,
            'state': state, 'state_desc': state_desc,
            'state_color': state_color, 'explanation': explanation,
            'is_contango': is_contango
        }
    except Exception as e:
        logger.warning("VIX term structure error: %s", e)
        return get_fallback_vix_structure()


def get_fallback_vix_structure():
    today = datetime.now()
    months = [(today + timedelta(days=30 * i)).strftime('%b') for i in range(8)]
    data = [
        {'month': months[i], 'current': round(17.45 + i * 0.9, 2),
         'previous': round(17.36 + i * 0.85, 2), 'two_days': round(20.37 + i * 0.5, 2)}
        for i in range(8)
    ]
    return {
        'data': data, 'current_spot': 17.45, 'prev_spot': 17.36, 'spot_2days': 20.37,
        'state': 'Contango', 'state_desc': 'Typical in calm markets - Conducive to dip buying',
        'state_color': '#00ffad',
        'explanation': 'Futures price > Spot. Market expects lower volatility ahead.',
        'is_contango': True
    }


def generate_vix_chart_html(vix_data: dict) -> str:
    data = vix_data['data']
    months = [d['month'] for d in data]
    current_levels  = [d['current']  for d in data]
    prev_levels     = [d['previous'] for d in data]
    two_days_levels = [d['two_days'] for d in data]

    chart_width, chart_height, padding = 340, 180, 35
    all_values = current_levels + prev_levels + two_days_levels
    min_level  = min(all_values) - 0.5
    max_level  = max(all_values) + 0.5
    level_range = max_level - min_level

    def build_line(values, color, dashed=False):
        pts = []
        for i, v in enumerate(values):
            x = padding + (i / (len(values) - 1)) * (chart_width - 2 * padding)
            y = chart_height - padding - ((v - min_level) / level_range) * (chart_height - 2 * padding)
            pts.append((x, y, v))
        pts_str = " ".join(f"{x},{y}" for x, y, _ in pts)
        dash = 'stroke-dasharray="4,3"' if dashed else ''
        circles = "".join(
            f'<circle cx="{x}" cy="{y}" r="3" fill="{color}" stroke="white" stroke-width="1"/>'
            for x, y, _ in pts
        )
        return f'<polyline points="{pts_str}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {dash}/>{circles}'

    y_axis = "".join(
        f'<text x="{padding-8}" y="{chart_height-padding-(i/4)*(chart_height-2*padding)+3}" '
        f'text-anchor="end" fill="#666" font-size="9">{min_level + level_range*i/4:.1f}</text>'
        f'<line x1="{padding}" y1="{chart_height-padding-(i/4)*(chart_height-2*padding)}" '
        f'x2="{chart_width-padding}" y2="{chart_height-padding-(i/4)*(chart_height-2*padding)}" stroke="#1a1e26" stroke-width="1"/>'
        for i in range(5)
    )
    x_labels = "".join(
        f'<text x="{padding + (i/(len(months)-1))*(chart_width-2*padding)}" y="{chart_height-8}" '
        f'text-anchor="middle" fill="#666" font-size="8">{m}</text>'
        for i, m in enumerate(months)
    )
    lx = chart_width - 175
    legend = f"""
    <rect x="{lx}" y="5" width="170" height="50" fill="#0c0e12" stroke="#1a1e26" rx="4"/>
    <line x1="{lx+5}" y1="20" x2="{lx+20}" y2="20" stroke="#3b82f6" stroke-width="2"/>
    <text x="{lx+25}" y="23" fill="#888" font-size="8">Current: {vix_data['current_spot']:.2f}</text>
    <line x1="{lx+5}" y1="35" x2="{lx+20}" y2="35" stroke="#f97316" stroke-width="2" stroke-dasharray="4,3"/>
    <text x="{lx+25}" y="38" fill="#888" font-size="8">Previous: {vix_data['prev_spot']:.2f}</text>
    <line x1="{lx+5}" y1="50" x2="{lx+20}" y2="50" stroke="#6b7280" stroke-width="2" stroke-dasharray="4,3"/>
    <text x="{lx+25}" y="53" fill="#888" font-size="8">2 Days Ago: {vix_data['spot_2days']:.2f}</text>"""

    return f"""
    <div style="width:100%;height:200px;background:#0c0e12;border-radius:8px;padding:8px;">
        <svg width="100%" height="100%" viewBox="0 0 {chart_width} {chart_height}" preserveAspectRatio="xMidYMid meet">
            {y_axis}
            {build_line(two_days_levels, "#6b7280", True)}
            {build_line(prev_levels,     "#f97316", True)}
            {build_line(current_levels,  "#3b82f6", False)}
            {x_labels}
            {legend}
        </svg>
    </div>"""


# ─────────────────────────────────────────────────────────────────────────────
# CRYPTO FEAR & GREED
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_crypto_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1",
                         headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.status_code == 200:
            item = r.json()['data'][0]
            return {
                'value': int(item['value']),
                'classification': item['value_classification'],
                'timestamp': datetime.now().strftime('%H:%M'),
                'source': 'alternative.me'
            }
    except Exception as e:
        logger.warning("Crypto F&G error: %s", e)
    return {'value': 50, 'classification': 'Neutral', 'timestamp': get_timestamp(), 'source': 'alternative.me'}


# ─────────────────────────────────────────────────────────────────────────────
# EARNINGS CALENDAR
# ─────────────────────────────────────────────────────────────────────────────
MEGA_CAPS = [
    'AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','BRK-B','AVGO','WMT',
    'JPM','V','MA','UNH','HD','PG','JNJ','BAC','LLY','MRK','KO','PEP','ABBV',
    'COST','TMO','ADBE','NFLX','AMD','CRM','ACN','LIN','DIS','VZ','WFC',
    'DHR','NKE','TXN','PM','RTX','HON'
]

AFTER_MARKET_TICKERS = {'NVDA','AAPL','AMZN','META','NFLX','AMD'}


@st.cache_data(ttl=600)
def get_earnings_calendar():
    """
    Devuelve earnings desde HOY en adelante.
    La comparación se hace por fecha de calendario (date), no por diferencia
    de horas/minutos, para evitar que eventos de hoy aparezcan como "ayer".
    """
    api_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", None)
    earnings_list = []
    today_date = datetime.now().date()  # solo la fecha, sin hora

    if api_key:
        try:
            from io import StringIO
            url = f"https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey={api_key}"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                df = pd.read_csv(StringIO(r.text))
                df_filtered = df[df['symbol'].isin(MEGA_CAPS)].copy()
                for _, row in df_filtered.iterrows():
                    try:
                        report_date = pd.to_datetime(row['reportDate']).date()
                        # Estricto: solo hoy o futuro
                        if report_date < today_date:
                            continue
                        days_until = (report_date - today_date).days
                        symbol = row['symbol']
                        earnings_list.append({
                            'ticker':    symbol,
                            'date':      report_date.strftime('%b %d'),
                            'full_date': pd.Timestamp(report_date),
                            'time':      "After Market" if symbol in AFTER_MARKET_TICKERS else "Before Bell",
                            'impact':    'High',
                            'estimate':  row.get('estimate', '-'),
                            'days':      days_until,
                            'source':    'AlphaVantage'
                        })
                    except Exception as e:
                        logger.debug("Earnings row error: %s", e)
                earnings_list.sort(key=lambda x: x['full_date'])
                if len(earnings_list) >= 4:
                    return earnings_list[:6]
        except Exception as e:
            logger.warning("Alpha Vantage earnings error: %s", e)

    # Fallback: yfinance paralelo
    def fetch_earn(ticker):
        try:
            stock = yf.Ticker(ticker)
            cal = stock.calendar
            if cal is not None and not cal.empty:
                next_e = cal.index[0]
                # Normalizar a solo fecha para comparar correctamente
                next_date = pd.Timestamp(next_e).date()
                if next_date < today_date:
                    return None
                days_until = (next_date - today_date).days
                if days_until > 60:
                    return None
                info = stock.info
                cap = info.get('marketCap', 0) / 1e9
                if cap >= 50:
                    hour = pd.Timestamp(next_e).hour if pd.Timestamp(next_e).hour != 0 else 16
                    return {
                        'ticker':     ticker,
                        'date':       next_date.strftime('%b %d'),
                        'full_date':  pd.Timestamp(next_date),
                        'time':       "Before Bell" if hour < 12 else "After Market",
                        'impact':     'High',
                        'market_cap': f"${cap:.0f}B",
                        'days':       days_until,
                        'source':     'yfinance'
                    }
        except Exception as e:
            logger.debug("yfinance earnings error %s: %s", ticker, e)
        return None

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_earn, t): t for t in MEGA_CAPS[:15]}
        for future in as_completed(futures):
            result = future.result()
            if result:
                earnings_list.append(result)

    earnings_list.sort(key=lambda x: x['full_date'])
    return earnings_list[:6] if earnings_list else get_fallback_earnings_realistic()


def get_fallback_earnings_realistic():
    today = datetime.now()
    items = [
        ("NVDA",  2, "After Market", "$3.2T"),
        ("AAPL",  5, "After Market", "$3.4T"),
        ("MSFT",  7, "After Market", "$3.1T"),
        ("AMZN",  8, "After Market", "$2.1T"),
        ("GOOGL", 10,"After Market", "$2.3T"),
        ("META",  12,"After Market", "$1.8T"),
    ]
    return [
        {'ticker': t, 'date': (today+timedelta(days=d)).strftime('%b %d'),
         'full_date': today+timedelta(days=d), 'time': ti,
         'impact': 'High', 'market_cap': mc, 'days': d, 'source': 'Fallback'}
        for t, d, ti, mc in items
    ]


# ─────────────────────────────────────────────────────────────────────────────
# INSIDER TRADING
# ─────────────────────────────────────────────────────────────────────────────
def _parse_amount(amount_str: str) -> float:
    """Convierte strings como '$12.5M', '$400K', '$1.2B' a float."""
    try:
        s = amount_str.replace('$', '').replace(',', '').strip()
        if s.endswith('B'):   return float(s[:-1]) * 1e9
        elif s.endswith('M'): return float(s[:-1]) * 1e6
        elif s.endswith('K'): return float(s[:-1]) * 1e3
        return float(s)
    except (ValueError, AttributeError):
        return 0.0


@st.cache_data(ttl=600)
def get_insider_trading():
    api_key = st.secrets.get("FMP_API_KEY", None)
    if not api_key:
        return get_fallback_insider()

    symbols = ['AAPL','MSFT','NVDA','TSLA','META','GOOGL','AMZN','NFLX','AMD','CRM']
    all_trades = []

    def fetch_insider(symbol):
        trades = []
        try:
            url = f"https://financialmodelingprep.com/api/v4/insider-trading?symbol={symbol}&limit=3&apikey={api_key}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for trade in r.json():
                    t_type = trade.get('transactionType', '')
                    if   'P' in t_type: trans = "BUY"
                    elif 'S' in t_type: trans = "SELL"
                    else: continue

                    shares = trade.get('securitiesTransacted', 0) or 0
                    price  = trade.get('price', 0) or 0
                    amount = shares * price
                    if amount > 50_000:
                        amount_str = f"${amount/1e6:.1f}M" if amount >= 1e6 else f"${amount/1e3:.0f}K"
                        trades.append({
                            'ticker':   symbol,
                            'insider':  str(trade.get('reportingName', 'Executive'))[:20],
                            'position': str(trade.get('typeOfOwner', 'Officer'))[:15],
                            'type':     trans,
                            'amount':   amount_str,
                            'date':     trade.get('transactionDate', 'Recent')
                        })
        except Exception as e:
            logger.debug("Insider fetch error %s: %s", symbol, e)
        return trades

    with ThreadPoolExecutor(max_workers=6) as ex:
        for result in ex.map(fetch_insider, symbols):
            all_trades.extend(result)

    if all_trades:
        all_trades.sort(key=lambda x: _parse_amount(x['amount']), reverse=True)
        return all_trades[:6]

    return get_fallback_insider()


def get_fallback_insider():
    return [
        {"ticker": "NVDA", "insider": "Jensen Huang",     "position": "CEO", "type": "SELL", "amount": "$12.5M"},
        {"ticker": "TSLA", "insider": "Elon Musk",        "position": "CEO", "type": "SELL", "amount": "$45.1M"},
        {"ticker": "META", "insider": "Mark Zuckerberg",  "position": "CEO", "type": "SELL", "amount": "$28.3M"},
        {"ticker": "MSFT", "insider": "Satya Nadella",    "position": "CEO", "type": "SELL", "amount": "$8.2M"},
        {"ticker": "AAPL", "insider": "Tim Cook",         "position": "CEO", "type": "SELL", "amount": "$5.4M"},
        {"ticker": "AMZN", "insider": "Andy Jassy",       "position": "CEO", "type": "SELL", "amount": "$3.1M"},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# MARKET BREADTH
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_market_breadth():
    try:
        hist = yf.Ticker("SPY").history(period="6mo")
        if len(hist) > 50:
            current = hist['Close'].iloc[-1]
            sma50   = hist['Close'].rolling(50).mean().iloc[-1]
            sma200  = hist['Close'].rolling(200).mean().iloc[-1]
            deltas  = hist['Close'].diff()
            gains   = deltas.where(deltas > 0, 0).rolling(14).mean()
            losses  = (-deltas.where(deltas < 0, 0)).rolling(14).mean()
            rs  = gains / losses
            rsi = 100 - (100 / (1 + rs.iloc[-1])) if not pd.isna(rs.iloc[-1]) else 50
            return {
                'price': current, 'sma50': sma50, 'sma200': sma200,
                'above_sma50': current > sma50, 'above_sma200': current > sma200,
                'golden_cross': sma50 > sma200, 'rsi': rsi,
                'trend':    'ALCISTA' if sma50 > sma200 else 'BAJISTA',
                'strength': 'FUERTE'  if (current > sma50 and current > sma200) else 'DÉBIL'
            }
    except Exception as e:
        logger.warning("Market breadth error: %s", e)
    return get_fallback_market_breadth()


def get_fallback_market_breadth():
    return {
        'price': 695.50, 'sma50': 686.61, 'sma200': float('nan'),
        'above_sma50': True, 'above_sma200': False, 'golden_cross': False,
        'rsi': 59.2, 'trend': 'BAJISTA', 'strength': 'DÉBIL'
    }


# ─────────────────────────────────────────────────────────────────────────────
# NOTICIAS  –  caché de traducción
# ─────────────────────────────────────────────────────────────────────────────
HIGH_IMPACT_KEYWORDS = {"earnings","profit","revenue","gdp","fed","fomc","inflation","rate","outlook"}

@st.cache_data(ttl=900)   # caché más agresivo que las llamadas de render
def _translate_cached(text: str) -> str:
    """Traducción con caché para evitar llamadas repetidas por rerender."""
    try:
        if len(text.encode('utf-8')) > 450:
            text = text[:200] + "..."
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=en|es"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get('responseStatus') == 200:
                translated = data.get('responseData', {}).get('translatedText', text)
                if translated != text and "MYMEMORY" not in translated:
                    return translated
    except Exception as e:
        logger.debug("Translation error: %s", e)
    return text


@st.cache_data(ttl=300)
def fetch_finnhub_news():
    api_key = st.secrets.get("FINNHUB_API_KEY", None)
    if not api_key:
        return get_fallback_news()
    try:
        r = requests.get(f"https://finnhub.io/api/v1/news?category=general&token={api_key}", timeout=12)
        news_list = []
        for item in r.json()[:8]:
            title_en = item.get("headline", "Sin título")
            title_es = _translate_cached(title_en)
            timestamp = item.get("datetime", 0)
            time_str  = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "N/A"
            lower = title_en.lower()
            impact, color = ("Alto", "#f23645") if any(k in lower for k in HIGH_IMPACT_KEYWORDS) else ("Moderado", "#ff9800")
            news_list.append({"time": time_str, "title": title_es, "impact": impact, "color": color, "link": item.get("url", "#")})
        return news_list if news_list else get_fallback_news()
    except Exception as e:
        logger.warning("Finnhub error: %s", e)
        return get_fallback_news()


def get_fallback_news():
    return [
        {"time": "19:45", "title": "Tesla supera expectativas de beneficios",         "impact": "Alto",    "color": "#f23645", "link": "#"},
        {"time": "18:30", "title": "El PIB de EEUU crece un 2,3% en el último trimestre","impact": "Alto","color": "#f23645", "link": "#"},
        {"time": "16:15", "title": "Apple presenta resultados récord gracias al iPhone","impact": "Alto",   "color": "#f23645", "link": "#"},
        {"time": "14:00", "title": "La inflación subyacente se modera al 3,2%",        "impact": "Moderado","color": "#ff9800","link": "#"},
        {"time": "12:30", "title": "Microsoft Cloud supera los 30.000M en ingresos",   "impact": "Alto",    "color": "#f23645", "link": "#"},
        {"time": "11:15", "title": "La Fed mantiene los tipos de interés sin cambios",  "impact": "Alto",    "color": "#f23645", "link": "#"},
        {"time": "10:00", "title": "Amazon anuncia nueva división de inteligencia artificial","impact":"Moderado","color":"#ff9800","link":"#"},
        {"time": "09:30", "title": "NVIDIA presenta nuevos chips para centros de datos","impact": "Alto",   "color": "#f23645", "link": "#"},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# FED LIQUIDITY
# ─────────────────────────────────────────────────────────────────────────────
def get_fed_liquidity():
    api_key = st.secrets.get("FRED_API_KEY", None)
    if not api_key:
        return "STABLE", "#ff9800", "API Key no configurada", "N/A", "N/A"
    try:
        url = (f"https://api.stlouisfed.org/fred/series/observations"
               f"?series_id=WALCL&api_key={api_key}&file_type=json&limit=10&sort_order=desc")
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            obs = r.json().get('observations', [])
            if len(obs) >= 2:
                latest = float(obs[0]['value'])
                prev   = float(obs[1]['value'])
                change = latest - prev
                if   change < -100: return "QT",     "#f23645", "Quantitative Tightening", f"{latest/1000:.1f}T", obs[0]['date']
                elif change >  100: return "QE",     "#00ffad", "Quantitative Easing",     f"{latest/1000:.1f}T", obs[0]['date']
                else:               return "STABLE", "#ff9800", "Balance sheet stable",    f"{latest/1000:.1f}T", obs[0]['date']
    except Exception as e:
        logger.warning("FRED error: %s", e)
    return "N/A", "#888", "Sin conexión", "N/A", "N/A"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE RENDER
# ─────────────────────────────────────────────────────────────────────────────
def _fng_label_color(val: int):
    if   val <= 24: return "EXTREME FEAR",  "#d32f2f"
    elif val <= 44: return "FEAR",          "#f57c00"
    elif val <= 55: return "NEUTRAL",       "#ff9800"
    elif val <= 75: return "GREED",         "#4caf50"
    else:           return "EXTREME GREED", "#00ffad"

FNG_LEGEND_HTML = """
<div class="fng-legend">
    <div class="fng-legend-item"><div class="fng-color-box" style="background:#d32f2f;"></div><div>Extreme<br>Fear</div></div>
    <div class="fng-legend-item"><div class="fng-color-box" style="background:#f57c00;"></div><div>Fear</div></div>
    <div class="fng-legend-item"><div class="fng-color-box" style="background:#ff9800;"></div><div>Neutral</div></div>
    <div class="fng-legend-item"><div class="fng-color-box" style="background:#4caf50;"></div><div>Greed</div></div>
    <div class="fng-legend-item"><div class="fng-color-box" style="background:#00ffad;"></div><div>Extreme<br>Greed</div></div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# RENDER PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def render():
    # ── CSS global de Streamlit ──────────────────────────────────────────────
    st.markdown("""
    <style>
    /* ── Sidebar: recuperar estilo de botones/páginas ── */
    [data-testid="stSidebarNav"] ul { padding: 0; list-style: none; }
    [data-testid="stSidebarNav"] li { margin: 4px 0; }
    [data-testid="stSidebarNav"] a {
        display: flex; align-items: center; gap: 10px;
        padding: 10px 14px; border-radius: 8px;
        background: #11141a; border: 1px solid #1a1e26;
        color: #ccc !important; font-size: 13px; font-weight: 600;
        text-decoration: none !important; transition: all 0.15s;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: #1a2035; border-color: #2a3f5f; color: white !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: #0d2137; border-color: #00ffad;
        color: #00ffad !important;
    }
    /* ── Resto de CSS del dashboard ── */
    .tooltip-wrapper { position: static; display: inline-block; }
    .tooltip-btn {
        width: 24px; height: 24px; border-radius: 50%;
        background: #1a1e26; border: 2px solid #555;
        display: flex; align-items: center; justify-content: center;
        color: #aaa; font-size: 14px; font-weight: bold; cursor: help;
    }
    .tooltip-content {
        display: none; position: fixed; width: 300px;
        background-color: #1e222d; color: #eee; text-align: left;
        padding: 15px; border-radius: 10px; z-index: 99999;
        font-size: 12px; border: 2px solid #3b82f6;
        box-shadow: 0 15px 40px rgba(0,0,0,0.9); line-height: 1.5;
        left: 50%; top: 50%; transform: translate(-50%, -50%);
        white-space: normal; word-wrap: break-word;
    }
    .tooltip-wrapper:hover .tooltip-content { display: block; }
    .update-timestamp {
        text-align: center; color: #555; font-size: 10px; padding: 6px 0;
        font-family: 'Courier New', monospace;
        border-top: 1px solid #1a1e26; background: #0c0e12; flex-shrink: 0;
    }
    .module-container {
        border: 1px solid #1a1e26; border-radius: 10px; overflow: hidden;
        background: #11141a; height: 480px;
        display: flex; flex-direction: column; margin-bottom: 0;
    }
    .module-header {
        background: #0c0e12; padding: 10px 12px;
        border-bottom: 1px solid #1a1e26;
        display: flex; justify-content: space-between; align-items: center;
        flex-shrink: 0;
    }
    .module-title {
        margin: 0; color: white; font-size: 13px; font-weight: bold;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .module-content { flex: 1; overflow-y: auto; padding: 10px; }
    .sector-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 6px; height: 100%; }
    .sector-item {
        background: #0c0e12; border: 1px solid #1a1e26; border-radius: 6px;
        padding: 8px 4px; text-align: center;
        display: flex; flex-direction: column; justify-content: center;
    }
    .sector-code  { color: #666; font-size: 9px; font-weight: bold; margin-bottom: 2px; }
    .sector-name  { color: white; font-size: 10px; font-weight: 600; margin-bottom: 4px; line-height: 1.2; }
    .sector-change { font-size: 11px; font-weight: bold; }
    .fng-legend { display: flex; justify-content: space-between; width: 100%; margin-top: 10px; font-size: 0.6rem; color: #888; text-align: center; }
    .fng-legend-item { flex: 1; padding: 0 2px; }
    .fng-color-box { width: 100%; height: 4px; margin-bottom: 3px; border-radius: 2px; }
    .eco-date-badge { display:inline-flex; align-items:center; justify-content:center; padding:2px 6px; border-radius:4px; font-size:9px; font-weight:bold; margin-right:6px; min-width:45px; text-align:center; }
    .eco-time { font-family:'Courier New',monospace; font-size:10px; color:#888; min-width:35px; }
    div[data-testid="stWidgetLabel"] { display: none !important; }
    div[role="radiogroup"] { display:flex; gap:4px; background:#0c0e12; padding:2px; border-radius:6px; border:1px solid #1a1e26; margin:0 !important; }
    div[role="radiogroup"] > label { margin:0 !important; padding:0 !important; }
    div[role="radiogroup"] > label > div { display:none !important; }
    div[role="radiogroup"] > label > div[data-testid="stMarkdownContainer"] { display:block !important; }
    div[role="radiogroup"] > label > div[data-testid="stMarkdownContainer"] p { margin:0; padding:4px 10px; font-size:10px; font-weight:600; color:#888; border-radius:4px; cursor:pointer; }
    div[role="radiogroup"] > label:hover > div[data-testid="stMarkdownContainer"] p { color:white; }
    div[role="radiogroup"] > label[data-checked="true"] > div[data-testid="stMarkdownContainer"] p { background:#2a3f5f; color:#00ffad; }
    </style>
    """, unsafe_allow_html=True)

    # ── Ticker ───────────────────────────────────────────────────────────────
    components.html(generate_ticker_html(), height=50, scrolling=False)
    st.markdown('<h1 style="margin-top:15px;text-align:center;margin-bottom:15px;font-size:1.5rem;">Market Dashboard</h1>',
                unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # FILA 1
    # ════════════════════════════════════════════════════════════════════════
    col1, col2, col3 = st.columns(3)

    # ── Índices ──────────────────────────────────────────────────────────────
    with col1:
        indices_html = ""
        for t, n in [
            ("^GSPC","S&P 500"), ("^IXIC","NASDAQ 100"),
            ("^DJI","DOW JONES"), ("^RUT","RUSSELL 2000"),
            ("VUG","VUG – Growth"), ("MEME","MEME ETF"), ("RSP","RSP – Equal Weight"),
        ]:
            val, chg = get_market_index(t)
            c = "#00ffad" if chg >= 0 else "#f23645"
            indices_html += (
                f'<div style="background:#0c0e12;padding:10px 12px;border-radius:8px;margin-bottom:8px;'
                f'border:1px solid #1a1e26;display:flex;justify-content:space-between;align-items:center;">'
                f'<div><div style="font-weight:bold;color:white;font-size:12px;">{n}</div>'
                f'<div style="color:#555;font-size:9px;">INDEX</div></div>'
                f'<div style="text-align:right;">'
                f'<div style="color:white;font-weight:bold;font-size:12px;">{val:,.2f}</div>'
                f'<div style="color:{c};font-size:10px;font-weight:bold;">{chg:+.2f}%</div>'
                f'</div></div>'
            )
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Market Indices</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Rendimiento en tiempo real de los principales índices bursátiles de EEUU.</div>
                </div>
            </div>
            <div class="module-content" style="padding:12px;">{indices_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>''', unsafe_allow_html=True)

    # ── Calendario Económico ─────────────────────────────────────────────────
    with col2:
        events = get_economic_calendar()
        impact_colors = {'High': '#f23645', 'Medium': '#ff9800', 'Low': '#4caf50'}
        country_flags = {'US':'🇺🇸','EU':'🇪🇺','EZ':'🇪🇺','DE':'🇩🇪','FR':'🇫🇷','ES':'🇪🇸','IT':'🇮🇹'}
        events_html = ""
        for ev in events[:6]:
            imp_color    = impact_colors.get(ev['imp'], '#888')
            date_color   = ev.get('date_color', '#888')
            flag         = country_flags.get(ev.get('country','US'), '🇺🇸')
            display_val  = ev['val']
            if display_val in ('-','nan'):
                fc = ev.get('forecast', '-')
                display_val = f"Est: {fc}" if fc not in ('-','nan') else '-'
            events_html += (
                f'<div style="padding:8px;border-bottom:1px solid #1a1e26;display:flex;align-items:center;">'
                f'<div class="eco-date-badge" style="background:{date_color}22;color:{date_color};border:1px solid {date_color}44;">{ev["date_display"]}</div>'
                f'<div class="eco-time">{ev["time"]}</div>'
                f'<div style="flex-grow:1;margin-left:8px;min-width:0;">'
                f'<div style="color:white;font-size:10px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
                f'{flag} {ev["event"]}</div>'
                f'<div style="color:{imp_color};font-size:7px;font-weight:bold;text-transform:uppercase;margin-top:2px;">● {ev["imp"]}</div>'
                f'</div>'
                f'<div style="text-align:right;min-width:50px;margin-left:6px;">'
                f'<div style="color:white;font-size:10px;font-weight:bold;">{display_val}</div>'
                f'</div></div>'
            )
        badge = '<span style="background:#2a3f5f;color:#00ffad;padding:2px 6px;border-radius:3px;font-size:9px;font-weight:bold;">CET</span>'
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Calendario Económico</div>
                <div style="display:flex;align-items:center;gap:6px;">
                    {badge}
                    <div class="tooltip-wrapper">
                        <div class="tooltip-btn">?</div>
                        <div class="tooltip-content">Calendario económico en tiempo real. Hora española (CET/CEST). Eventos traducidos.</div>
                    </div>
                </div>
            </div>
            <div class="module-content" style="padding:0;">{events_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>''', unsafe_allow_html=True)

    # ── Reddit Social Pulse ───────────────────────────────────────────────────
    with col3:
        master_data = get_buzztickr_master_data()
        buzz_items  = master_data.get('data', [])
        cards_html  = ""

        for item in buzz_items[:10]:
            rank       = str(item.get('rank', '-'))
            ticker     = str(item.get('ticker', '-'))
            buzz_score = str(item.get('buzz_score', '-'))
            health     = str(item.get('health', '-'))
            smart_money= str(item.get('smart_money', ''))
            squeeze    = str(item.get('squeeze', ''))

            try:
                rank_bg, rank_color, glow = ("#f23645","white","box-shadow:0 0 10px rgba(242,54,69,0.3);") if int(rank) <= 3 else ("#1a1e26","#888","")
            except ValueError:
                rank_bg, rank_color, glow = "#1a1e26", "#888", ""

            h_parts    = health.split()
            h_num      = h_parts[0] if h_parts else "50"
            h_text     = h_parts[1].upper() if len(h_parts) > 1 else "NEUTRAL"
            h_color    = "#00ffad" if 'strong' in health.lower() else ("#f23645" if 'weak' in health.lower() else "#ff9800")
            h_bg       = h_color + "15"

            has_smart    = 'whales' in smart_money.lower()
            smart_icon   = "🐋" if has_smart else "○"
            smart_color  = "#00ffad" if has_smart else "#333"
            smart_text   = "SMART $" if has_smart else "—"

            has_squeeze  = 'short' in squeeze.lower() or 'squeeze' in squeeze.lower()
            squeeze_icon = "🧨" if has_squeeze else "○"
            squeeze_color= "#f23645" if has_squeeze else "#333"
            pct_match    = re.search(r'(\d+\.?\d*)%', squeeze) if has_squeeze else None
            squeeze_pct  = pct_match.group(1) + "%" if pct_match else ""

            try:
                score_width = (int(buzz_score) / 10) * 100
            except ValueError:
                score_width = 50

            cards_html += f"""
            <div style="background:#0c0e12;border:1px solid #1a1e26;border-radius:8px;padding:10px;margin-bottom:8px;{glow}">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <div style="width:26px;height:26px;border-radius:50%;background:{rank_bg};color:{rank_color};display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:11px;flex-shrink:0;">{rank}</div>
                    <div style="flex:1;">
                        <div style="color:#00ffad;font-weight:bold;font-size:14px;letter-spacing:0.5px;">${ticker}</div>
                        <div style="display:flex;align-items:center;gap:6px;margin-top:2px;">
                            <div style="flex:1;height:4px;background:#1a1e26;border-radius:2px;overflow:hidden;">
                                <div style="width:{score_width}%;height:100%;background:linear-gradient(90deg,#00ffad,#00cc8a);"></div>
                            </div>
                            <span style="color:#888;font-size:10px;font-weight:bold;">{buzz_score}/10</span>
                        </div>
                    </div>
                </div>
                <div style="display:flex;gap:8px;">
                    <div style="flex:1;background:{h_bg};border:1px solid {h_color}30;border-radius:6px;padding:6px;text-align:center;">
                        <div style="font-size:8px;color:#666;text-transform:uppercase;margin-bottom:2px;">Health</div>
                        <div style="color:{h_color};font-weight:bold;font-size:11px;">{h_num}</div>
                        <div style="color:{h_color};font-size:8px;opacity:0.8;">{h_text}</div>
                    </div>
                    <div style="flex:1;background:#0f1218;border:1px solid {smart_color}30;border-radius:6px;padding:6px;text-align:center;">
                        <div style="font-size:8px;color:#666;text-transform:uppercase;margin-bottom:2px;">Smart $</div>
                        <div style="color:{smart_color};font-size:14px;">{smart_icon}</div>
                        <div style="color:{smart_color};font-size:8px;margin-top:1px;">{smart_text}</div>
                    </div>
                    <div style="flex:1;background:#0f1218;border:1px solid {squeeze_color}30;border-radius:6px;padding:6px;text-align:center;">
                        <div style="font-size:8px;color:#666;text-transform:uppercase;margin-bottom:2px;">Squeeze</div>
                        <div style="color:{squeeze_color};font-size:14px;">{squeeze_icon}</div>
                        <div style="color:{squeeze_color};font-size:8px;margin-top:1px;">{squeeze_pct or '—'}</div>
                    </div>
                </div>
            </div>"""

        components.html(wrap_module_html(
            title="Reddit Social Pulse",
            content=cards_html,
            timestamp=f"{master_data.get('timestamp', get_timestamp())} • {master_data.get('source','API')} • Top {master_data.get('count',0)}",
            tooltip="Top 10 activos más mencionados en Reddit según BuzzTickr. Incluye Health Score, Smart Money tracking y Squeeze Potential.",
            badge="LIVE",
        ).replace(
            # Añadir animación LIVE y scrollbar
            "</style>",
            """@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.7; } }
            .live-badge-inner { animation:pulse 2s infinite; }
            .content::-webkit-scrollbar { width:6px; }
            .content::-webkit-scrollbar-track { background:#0c0e12; }
            .content::-webkit-scrollbar-thumb { background:#2a3f5f; border-radius:3px; }
            </style>"""
        ).replace(
            f'>{badge}</span>' if (badge := "LIVE") else "",
            f' class="live-badge-inner">{badge}</span>'
        ), height=480, scrolling=False)

    # ════════════════════════════════════════════════════════════════════════
    # FILA 2
    # ════════════════════════════════════════════════════════════════════════
    st.write("")
    c1, c2, c3 = st.columns(3)

    # ── CNN Fear & Greed ──────────────────────────────────────────────────────
    with c1:
        val = get_cnn_fear_greed()
        if val is None:
            val, label, col = 50, "NEUTRAL", "#ff9800"
        else:
            label, col = _fng_label_color(val)
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Fear & Greed Index</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Índice CNN Fear & Greed – mide el sentimiento del mercado.</div>
                </div>
            </div>
            <div class="module-content" style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:15px;">
                <div style="font-size:3.5rem;font-weight:bold;color:{col};">{val}</div>
                <div style="color:white;font-size:1rem;letter-spacing:1px;font-weight:bold;margin:8px 0;">{label}</div>
                <div style="width:90%;background:#0c0e12;height:12px;border-radius:6px;margin:10px 0;border:1px solid #1a1e26;overflow:hidden;">
                    <div style="width:{val}%;background:{col};height:100%;"></div>
                </div>
                {FNG_LEGEND_HTML}
            </div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>''', unsafe_allow_html=True)

    # ── Sector Rotation ───────────────────────────────────────────────────────
    with c2:
        if 'sector_tf' not in st.session_state:
            st.session_state.sector_tf = "1 Day"
        tf_options = ["1 Day", "3 Days", "1 Week", "1 Month"]
        tf_map     = {"1 Day": "1D", "3 Days": "3D", "1 Week": "1W", "1 Month": "1M"}
        current_tf = st.session_state.sector_tf
        sectors    = get_sector_performance(tf_map.get(current_tf, "1D"))

        sectors_html = ""
        for s in sectors:
            chg = s['change']
            if   chg >= 2:    bg, tc = "#00ffad22", "#00ffad"
            elif chg >= 0.5:  bg, tc = "#00ffad18", "#00ffad"
            elif chg >= 0:    bg, tc = "#00ffad10", "#00ffad"
            elif chg >= -0.5: bg, tc = "#f2364510", "#f23645"
            elif chg >= -2:   bg, tc = "#f2364518", "#f23645"
            else:             bg, tc = "#f2364522", "#f23645"
            sectors_html += (
                f'<div class="sector-item" style="background:{bg};">'
                f'<div class="sector-code">{s["code"]}</div>'
                f'<div class="sector-name">{s["name"]}</div>'
                f'<div class="sector-change" style="color:{tc};">{chg:+.2f}%</div>'
                f'</div>'
            )

        hcol1, _, hcol3 = st.columns([2, 1, 1])
        with hcol1:
            st.markdown('''
            <div style="display:flex;align-items:center;gap:10px;">
                <div class="module-title" style="color:white;font-size:13px;font-weight:bold;text-transform:uppercase;letter-spacing:0.5px;">Sector Rotation</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Rendimiento de los sectores vía ETFs sectoriales.</div>
                </div>
            </div>''', unsafe_allow_html=True)
        with hcol3:
            selected_tf = st.radio("", tf_options, index=tf_options.index(current_tf),
                                   key="sector_tf_radio", horizontal=True, label_visibility="collapsed")
            if selected_tf != current_tf:
                st.session_state.sector_tf = selected_tf
                st.rerun()

        st.markdown(f'''
        <div style="border:1px solid #1a1e26;border-radius:10px;overflow:hidden;background:#11141a;height:430px;display:flex;flex-direction:column;margin-top:-10px;">
            <div style="flex:1;overflow-y:auto;padding:8px;">
                <div class="sector-grid">{sectors_html}</div>
            </div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>''', unsafe_allow_html=True)

    # ── Crypto Fear & Greed ───────────────────────────────────────────────────
    with c3:
        cfg = get_crypto_fear_greed()
        label, col = _fng_label_color(cfg['value'])
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Crypto Fear & Greed</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Crypto Fear & Greed Index – mide el sentimiento del mercado de criptomonedas.</div>
                </div>
            </div>
            <div class="module-content" style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:15px;">
                <div style="font-size:3.5rem;font-weight:bold;color:{col};">{cfg['value']}</div>
                <div style="color:white;font-size:1rem;letter-spacing:1px;font-weight:bold;margin:8px 0;">{label}</div>
                <div style="width:90%;background:#0c0e12;height:12px;border-radius:6px;margin:10px 0;border:1px solid #1a1e26;overflow:hidden;">
                    <div style="width:{cfg['value']}%;background:{col};height:100%;"></div>
                </div>
                {FNG_LEGEND_HTML}
            </div>
            <div class="update-timestamp">Updated: {cfg['timestamp']} • {cfg['source']}</div>
        </div>''', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # FILA 3
    # ════════════════════════════════════════════════════════════════════════
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)

    # ── Earnings Calendar ─────────────────────────────────────────────────────
    with f3c1:
        earnings = get_earnings_calendar()
        earn_html = ""
        for item in earnings:
            days       = item.get('days', 0)
            imp_color  = "#f23645" if item['impact'] == "High" else "#888"
            if   days == 0: d_text, d_color, d_bg = "HOY",    "#f23645", "#f2364522"
            elif days == 1: d_text, d_color, d_bg = "MAÑANA", "#ff9800", "#ff980022"
            elif days <= 3: d_text, d_color, d_bg = f"{days}d","#00ffad", "#00ffad22"
            else:           d_text, d_color, d_bg = f"{days}d","#888",    "#1a1e26"

            # Market cap en tiempo de render (sin llamada yfinance extra — ya lo tenemos)
            market_cap = item.get('market_cap', 'Large Cap')

            earn_html += (
                f'<div style="background:#0c0e12;padding:10px;border-radius:6px;margin-bottom:8px;'
                f'border:1px solid #1a1e26;display:flex;justify-content:space-between;align-items:center;position:relative;overflow:hidden;">'
                f'<div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:{imp_color};"></div>'
                f'<div style="margin-left:8px;">'
                f'<div style="color:#00ffad;font-weight:bold;font-size:12px;letter-spacing:0.5px;">{item["ticker"]}</div>'
                f'<div style="color:#555;font-size:8px;margin-top:2px;">{market_cap}</div>'
                f'</div>'
                f'<div style="text-align:center;flex:1;margin:0 10px;">'
                f'<div style="color:white;font-weight:bold;font-size:11px;">{item["date"]}</div>'
                f'<div style="color:#666;font-size:8px;text-transform:uppercase;letter-spacing:0.3px;">{item["time"]}</div>'
                f'</div>'
                f'<div style="text-align:right;">'
                f'<div style="background:{d_bg};color:{d_color};padding:3px 8px;border-radius:4px;font-size:9px;font-weight:bold;border:1px solid {d_color}33;">{d_text}</div>'
                f'<div style="color:{imp_color};font-size:8px;font-weight:bold;margin-top:4px;text-transform:uppercase;">● {item["impact"]}</div>'
                f'</div></div>'
            )
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Earnings Calendar</div>
                <div style="display:flex;align-items:center;gap:6px;">
                    <span style="background:#2a3f5f;color:#00ffad;padding:2px 6px;border-radius:3px;font-size:9px;font-weight:bold;">MEGA-CAP</span>
                    <div class="tooltip-wrapper">
                        <div class="tooltip-btn">?</div>
                        <div class="tooltip-content">Próximos earnings de mega-cap companies (>$50B). Datos vía Alpha Vantage/yfinance.</div>
                    </div>
                </div>
            </div>
            <div class="module-content" style="padding:10px;">{earn_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>''', unsafe_allow_html=True)

    # ── Insider Tracker ───────────────────────────────────────────────────────
    with f3c2:
        insiders = get_insider_trading()
        insider_html = ""
        for item in insiders:
            tc = "#00ffad" if item['type'] == "BUY" else "#f23645"
            insider_html += (
                f'<div style="background:#0c0e12;padding:8px;border-radius:6px;margin-bottom:6px;'
                f'border:1px solid #1a1e26;display:flex;justify-content:space-between;">'
                f'<div><div style="color:white;font-weight:bold;font-size:10px;">{item["ticker"]}</div>'
                f'<div style="color:#555;font-size:8px;">{item["position"]}</div></div>'
                f'<div style="text-align:right;">'
                f'<div style="color:{tc};font-weight:bold;font-size:9px;">{item["type"]}</div>'
                f'<div style="color:#888;font-size:8px;">{item["amount"]}</div>'
                f'</div></div>'
            )
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Insider Tracker</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Insider trading activity (> $50k) via SEC Form 4.</div>
                </div>
            </div>
            <div class="module-content" style="padding:10px;">{insider_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>''', unsafe_allow_html=True)

    # ── Noticias ──────────────────────────────────────────────────────────────
    with f3c3:
        news = fetch_finnhub_news()
        news_html = "".join(
            f'<div style="padding:8px 12px;border-bottom:1px solid #1a1e26;">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:3px;">'
            f'<span style="color:#888;font-size:0.7rem;font-family:monospace;">{n["time"]}</span>'
            f'<span style="padding:1px 6px;border-radius:8px;font-size:0.65rem;font-weight:bold;'
            f'background:{n["color"]}22;color:{n["color"]};">{n["impact"]}</span>'
            f'</div>'
            f'<div style="color:white;font-size:0.8rem;line-height:1.2;margin-bottom:4px;">'
            f'{n["title"].replace(chr(34),"&quot;").replace(chr(39),"&#39;")}</div>'
            f'<a href="{n["link"]}" target="_blank" style="color:#00ffad;text-decoration:none;font-size:0.75rem;">→ Leer más</a>'
            f'</div>'
            for n in news[:8]
        )
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Noticias de Alto Impacto</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Noticias de alto impacto traducidas al español vía Finnhub API.</div>
                </div>
            </div>
            <div class="module-content" style="padding:0;overflow-y:auto;">{news_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>''', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # FILA 4
    # ════════════════════════════════════════════════════════════════════════
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)

    # ── VIX Index ─────────────────────────────────────────────────────────────
    with f4c1:
        vix_val, vix_chg = get_market_index("^VIX")
        vix_color = "#00ffad" if vix_chg >= 0 else "#f23645"
        vix_content = (
            f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;">'
            f'<div style="font-size:3rem;font-weight:bold;color:white;">{vix_val:.2f}</div>'
            f'<div style="color:#f23645;font-size:1rem;font-weight:bold;margin-top:5px;">VIX INDEX</div>'
            f'<div style="color:{vix_color};font-size:0.9rem;font-weight:bold;">{vix_chg:+.2f}%</div>'
            f'<div style="color:#555;font-size:0.75rem;margin-top:10px;">Volatility Index</div>'
            f'</div>'
        )
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">VIX Index</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Índice de volatilidad CBOE (VIX).</div>
                </div>
            </div>
            <div class="module-content" style="padding:15px;">{vix_content}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>''', unsafe_allow_html=True)

    # ── FED Liquidity ─────────────────────────────────────────────────────────
    with f4c2:
        status, color, desc, assets, date = get_fed_liquidity()
        fed_content = (
            f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;">'
            f'<div style="font-size:3.5rem;font-weight:bold;color:{color};">{status}</div>'
            f'<div style="color:white;font-size:1rem;font-weight:bold;margin:8px 0;">{desc}</div>'
            f'<div style="background:#0c0e12;padding:10px 16px;border-radius:6px;border:1px solid #1a1e26;">'
            f'<div style="font-size:1.4rem;color:white;">{assets}</div>'
            f'<div style="color:#888;font-size:0.75rem;">Total Assets</div>'
            f'</div></div>'
        )
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">FED Liquidity Policy</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Política de liquidez de la FED vía FRED.</div>
                </div>
            </div>
            <div class="module-content" style="padding:15px;">{fed_content}</div>
            <div class="update-timestamp">Updated: {date}</div>
        </div>''', unsafe_allow_html=True)

    # ── 10Y Treasury ─────────────────────────────────────────────────────────
    with f4c3:
        tnx_val, tnx_chg = get_market_index("^TNX")
        tnx_color = "#00ffad" if tnx_chg >= 0 else "#f23645"
        tnx_content = (
            f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;">'
            f'<div style="font-size:3rem;font-weight:bold;color:white;">{tnx_val:.2f}%</div>'
            f'<div style="color:white;font-size:1rem;font-weight:bold;margin-top:5px;">10Y TREASURY</div>'
            f'<div style="color:{tnx_color};font-size:0.9rem;font-weight:bold;">{tnx_chg:+.2f}%</div>'
            f'<div style="color:#555;font-size:0.75rem;margin-top:10px;">US 10-Year Yield</div>'
            f'</div>'
        )
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">10Y Treasury Yield</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Rendimiento del bono del Tesoro de EEUU a 10 años.</div>
                </div>
            </div>
            <div class="module-content" style="padding:15px;">{tnx_content}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>''', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # FILA 5
    # ════════════════════════════════════════════════════════════════════════
    st.write("")
    f5c1, f5c2, f5c3 = st.columns(3)

    # ── Market Breadth ────────────────────────────────────────────────────────
    with f5c1:
        breadth = get_market_breadth()
        sma50_c   = "#00ffad" if breadth['above_sma50']   else "#f23645"
        sma200_c  = "#00ffad" if breadth['above_sma200']  else "#f23645"
        golden_c  = "#00ffad" if breadth['golden_cross']  else "#f23645"
        trend_c   = "#00ffad" if breadth['trend']   == 'ALCISTA' else "#f23645"
        strength_c= "#00ffad" if breadth['strength'] == 'FUERTE' else "#ff9800"
        golden_t  = "GOLDEN CROSS ✓" if breadth['golden_cross'] else "DEATH CROSS ✗"
        rsi = breadth['rsi']
        rsi_color = "#f23645" if rsi > 70 else ("#00ffad" if rsi < 30 else "#ff9800")
        rsi_text  = "OVERBOUGHT" if rsi > 70 else ("OVERSOLD" if rsi < 30 else "NEUTRAL")

        breadth_content = f"""
        <div class="metric-box">
            <span class="metric-label">SPY Price</span>
            <span class="metric-value" style="color:white;">${breadth['price']:.2f}</span>
        </div>
        <div class="metric-box">
            <span class="metric-label">SMA 50</span>
            <span class="metric-value" style="color:{sma50_c};">${breadth['sma50']:.2f}</span>
        </div>
        <div class="metric-box">
            <span class="metric-label">SMA 200</span>
            <span class="metric-value" style="color:{sma200_c};">${breadth['sma200']:.2f}</span>
        </div>
        <div class="metric-box" style="border-color:{golden_c}44;background:{golden_c}11;">
            <span class="metric-label">Signal</span>
            <span class="metric-value" style="color:{golden_c};">{golden_t}</span>
        </div>
        <div style="margin-top:8px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                <span class="metric-label">RSI (14)</span>
                <span style="color:{rsi_color};font-size:11px;font-weight:bold;">{rsi:.1f} - {rsi_text}</span>
            </div>
            <div style="width:100%;height:14px;background:linear-gradient(to right,#00ffad 0%,#ff9800 50%,#f23645 100%);border-radius:7px;position:relative;margin:6px 0;">
                <div style="position:absolute;top:-3px;left:{min(rsi,100)}%;width:3px;height:20px;background:white;border-radius:2px;transform:translateX(-50%);"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:8px;color:#555;margin-top:2px;">
                <span>0</span><span>30</span><span>50</span><span>70</span><span>100</span>
            </div>
        </div>
        <div style="margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:6px;">
            <div class="metric-box" style="text-align:center;margin-bottom:0;padding:6px;">
                <div class="metric-label">Trend</div>
                <div style="color:{trend_c};font-size:11px;font-weight:bold;">{breadth['trend']}</div>
            </div>
            <div class="metric-box" style="text-align:center;margin-bottom:0;padding:6px;">
                <div class="metric-label">Strength</div>
                <div style="color:{strength_c};font-size:11px;font-weight:bold;">{breadth['strength']}</div>
            </div>
        </div>"""

        breadth_extra_css = """
        .metric-box { background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:8px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center; }
        .metric-label { color:#888; font-size:10px; }
        .metric-value { font-size:13px; font-weight:bold; }
        """

        html_full = wrap_module_html(
            title="Market Breadth",
            content=breadth_content,
            timestamp=get_timestamp(),
            tooltip="Market Breadth: SMA50/200, Golden/Death Cross, RSI(14)"
        ).replace("</style>", breadth_extra_css + "</style>")

        components.html(html_full, height=480, scrolling=False)

    # ── VIX Term Structure ────────────────────────────────────────────────────
    with f5c2:
        vix_data   = get_vix_term_structure()
        sc         = vix_data['state_color']
        data_pts   = vix_data['data']
        slope_pct  = ((data_pts[-1]['current'] - data_pts[0]['current']) / data_pts[0]['current']) * 100 if len(data_pts) >= 2 else 0
        chart_html = generate_vix_chart_html(vix_data)

        vix_content = f"""
        <div class="spot-box">
            <div>
                <div style="color:#888;font-size:10px;font-weight:500;">VIX Spot</div>
                <div style="color:{sc};font-size:10px;font-weight:bold;">{slope_pct:+.1f}% vs Far Month</div>
            </div>
            <div style="color:white;font-size:20px;font-weight:bold;">{vix_data['current_spot']:.2f}</div>
        </div>
        <div class="chart-wrapper">{chart_html}</div>
        <div style="background:{sc}15;border:1px solid {sc}22;border-radius:6px;padding:8px 10px;">
            <div style="color:{sc};font-weight:bold;font-size:11px;margin-bottom:2px;">● {vix_data['state']}</div>
            <div style="color:#aaa;font-size:10px;line-height:1.3;">{vix_data['state_desc']}</div>
        </div>"""

        vix_extra_css = f"""
        .spot-box {{ display:flex; justify-content:space-between; align-items:center; background:linear-gradient(90deg,#0c0e12,#1a1e26); border:1px solid #2a3f5f; border-radius:6px; padding:10px 14px; margin-bottom:10px; }}
        .chart-wrapper {{ background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:8px; margin-bottom:8px; }}
        .state-badge {{ background:{sc}15; color:{sc}; padding:4px 10px; border-radius:10px; font-size:10px; font-weight:bold; border:1px solid {sc}33; }}
        """

        state_badge_html = f'<span class="state-badge">{vix_data["state"]}</span>'

        html_full = wrap_module_html(
            title="VIX Term Structure",
            content=vix_content,
            timestamp=get_timestamp(),
            tooltip=vix_data['explanation'],
            extra_header=state_badge_html
        ).replace("</style>", vix_extra_css + "</style>")

        components.html(html_full, height=480, scrolling=False)

    # ── Crypto Pulse ──────────────────────────────────────────────────────────
    with f5c3:
        try:
            cryptos = get_crypto_prices()
        except Exception:
            cryptos = get_fallback_crypto_prices()

        crypto_content = "".join(
            f'<div style="background:#0c0e12;border:1px solid #1a1e26;border-radius:6px;padding:8px;margin-bottom:5px;'
            f'display:flex;justify-content:space-between;align-items:center;">'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="color:#00ffad;font-weight:bold;font-size:12px;">{c["symbol"]}</div>'
            f'<div style="color:#555;font-size:9px;">{c["name"]}</div>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<div style="color:white;font-size:12px;font-weight:bold;">${c["price"]}</div>'
            f'<div style="color:{"#00ffad" if c["is_positive"] else "#f23645"};font-size:10px;font-weight:bold;">{c["change"]}</div>'
            f'</div></div>'
            for c in cryptos[:6]
        )

        components.html(wrap_module_html(
            title="Crypto Pulse",
            content=crypto_content,
            timestamp=get_timestamp(),
            tooltip="Precios reales de criptomonedas vía Yahoo Finance."
        ), height=480, scrolling=False)

    # ════════════════════════════════════════════════════════════════════════
    # FILA 6  –  Módulos vacíos (reservados para futura funcionalidad)
    # ════════════════════════════════════════════════════════════════════════
    st.write("")
    f6c1, f6c2, f6c3 = st.columns(3)

    _empty_placeholder = """
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                height:100%;text-align:center;gap:12px;">
        <div style="font-size:2rem;opacity:0.15;">⬜</div>
        <div style="color:#333;font-size:11px;letter-spacing:1px;text-transform:uppercase;">
            Próximamente
        </div>
    </div>"""

    with f6c1:
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Módulo 1</div>
            </div>
            <div class="module-content">{_empty_placeholder}</div>
            <div class="update-timestamp">—</div>
        </div>''', unsafe_allow_html=True)

    with f6c2:
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Módulo 2</div>
            </div>
            <div class="module-content">{_empty_placeholder}</div>
            <div class="update-timestamp">—</div>
        </div>''', unsafe_allow_html=True)

    with f6c3:
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Módulo 3</div>
            </div>
            <div class="module-content">{_empty_placeholder}</div>
            <div class="update-timestamp">—</div>
        </div>''', unsafe_allow_html=True)


if __name__ == "__main__":
    render()

















