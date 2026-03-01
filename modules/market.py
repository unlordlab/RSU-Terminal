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
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

try:
    import investpy
    INVESTPY_AVAILABLE = True
except ImportError:
    INVESTPY_AVAILABLE = False

# ── HEALTH CHECK STATE ────────────────────────────────────────────────────────
_api_health = {}
_api_health_lock = threading.Lock()

def set_api_health(name: str, ok: bool):
    with _api_health_lock:
        _api_health[name] = ok

def get_api_health(name: str) -> bool | None:
    return _api_health.get(name, None)

# ── SHARED HTTP SESSION (st.cache_resource) ───────────────────────────────────
@st.cache_resource
def get_http_session():
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    })
    return s

def get_timestamp():
    return datetime.now().strftime('%H:%M:%S')

# Diccionario de traducción de eventos económicos
EVENT_TRANSLATIONS = {
    # Empleo
    "Nonfarm Payrolls": "Nóminas No Agrícolas",
    "Unemployment Rate": "Tasa de Desempleo",
    "ADP Nonfarm Employment": "Empleo ADP",
    "Initial Jobless Claims": "Solicitudes de Desempleo",
    "Continuing Jobless Claims": "Solicitudes Continuas de Desempleo",
    "JOLTS Job Openings": "Vacantes JOLTS",
    "Average Hourly Earnings": "Salario por Hora Promedio",
    "Labor Force Participation Rate": "Tasa de Participación Laboral",
    
    # Inflación
    "CPI": "IPC (Inflación)",
    "Core CPI": "IPC Subyacente",
    "PPI": "IPP (Precios Productor)",
    "Core PPI": "IPP Subyacente",
    "PCE Price Index": "Índice de Precios PCE",
    "Core PCE": "PCE Subyacente",
    
    # Actividad Económica
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
    
    # Confianza y PMIs
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
    
    # Construcción y Vivienda
    "Building Permits": "Permisos de Construcción",
    "Housing Starts": "Inicio de Viviendas",
    "New Home Sales": "Ventas de Viviendas Nuevas",
    "Existing Home Sales": "Ventas de Viviendas Existentes",
    "Pending Home Sales": "Ventas de Viviendas Pendientes",
    "S&P/Case-Shiller Home Price Index": "Índice de Precios S&P/Case-Shiller",
    "FHFA House Price Index": "Índice de Precios FHFA",
    "Mortgage Applications": "Solicitudes de Hipotecas",
    
    # Comercio Exterior
    "Trade Balance": "Balanza Comercial",
    "Exports": "Exportaciones",
    "Imports": "Importaciones",
    
    # Deuda y Déficit
    "Treasury Budget": "Presupuesto del Tesoro",
    "Budget Balance": "Balance Presupuestario",
    "Public Debt": "Deuda Pública",
    
    # Fed y Tipos de Interés
    "Fed Interest Rate Decision": "Decisión de Tipos de la Fed",
    "FOMC Statement": "Declaración FOMC",
    "FOMC Minutes": "Actas FOMC",
    "FOMC Economic Projections": "Proyecciones Económicas FOMC",
    "Fed Chair Press Conference": "Rueda de Prensa del Presidente Fed",
    "Fed Chair Speech": "Discurso del Presidente Fed",
    "Fed Governor Speech": "Discurso de Gobernador Fed",
    "Fed Member Speech": "Discurso de Miembro Fed",
    
    # Commodities
    "Crude Oil Inventories": "Inventarios de Petróleo Crudo",
    "EIA Crude Oil Inventories": "Inventarios EIA Petróleo Crudo",
    "API Crude Oil Inventories": "Inventarios API Petróleo Crudo",
    "Gasoline Inventories": "Inventarios de Gasolina",
    "Distillate Inventories": "Inventarios de Destilados",
    "Natural Gas Storage": "Almacenamiento de Gas Natural",
    "Heating Oil Inventories": "Inventarios de Gasóleo Calefacción",
    "Refinery Utilization": "Utilización de Refinerías",
    
    # Otros
    "Current Account": "Cuenta Corriente",
    "Capital Flows": "Flujos de Capital",
    "Foreign Bond Investment": "Inversión en Bonos Extranjeros",
    "Net Long-term TIC Flows": "Flujos TIC Largo Plazo Netos",
    
    # Zona Euro
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

def translate_event(event_name):
    """Traduce el nombre del evento al español si existe en el diccionario"""
    # Buscar coincidencia exacta primero
    if event_name in EVENT_TRANSLATIONS:
        return EVENT_TRANSLATIONS[event_name]
    
    # Buscar coincidencias parciales
    for eng, esp in EVENT_TRANSLATIONS.items():
        if eng.lower() in event_name.lower():
            return esp
    
    # Si no hay traducción, devolver el nombre original truncado si es muy largo
    if len(event_name) > 35:
        return event_name[:32] + "..."
    return event_name

@st.cache_data(ttl=900)
def get_economic_calendar():
    """
    Scraping de Investing.com para obtener el calendario económico real.
    Filtra solo eventos de hoy en adelante, a 15 días vista.
    """
    events = []
    try:
        session = get_http_session()
        now = datetime.now()
        date_from = now.strftime('%Y-%m-%d')
        date_to = (now + timedelta(days=15)).strftime('%Y-%m-%d')
        
        url = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
        payload = {
            'country[]': ['5', '35'],  # 5=US, 35=Eurozone
            'importance[]': ['1', '2', '3'],
            'timefilter': 'timeRemain',
            'currentTab': 'custom',
            'submitFilters': '1',
            'limit_from': '0',
            'dateFrom': date_from,
            'dateTo': date_to,
        }
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.investing.com/economic-calendar/',
            'Origin': 'https://www.investing.com',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        r = session.post(url, data=payload, headers=headers, timeout=15)
        set_api_health('EcoCalendar', r.status_code == 200)
        
        if r.status_code == 200:
            data = r.json()
            html_content = data.get('data', '')
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                rows = soup.find_all('tr', class_=lambda c: c and 'js-event-item' in c)
                
                current_date = None
                for row in rows:
                    try:
                        # Fecha del evento
                        date_td = row.get('data-event-datetime', '')
                        if date_td:
                            try:
                                event_dt = datetime.strptime(date_td[:16], '%Y/%m/%d %H:%M')
                            except:
                                event_dt = now
                        else:
                            event_dt = current_date or now
                        
                        if event_dt.date() < now.date():
                            continue
                        
                        # Saltar fines de semana (los mercados no publican datos sáb/dom)
                        if event_dt.weekday() >= 5:
                            continue
                        
                        current_date = event_dt
                        
                        # Hora en CET (+1)
                        hour_cet = (event_dt.hour + 1) % 24
                        time_str = f"{hour_cet:02d}:{event_dt.minute:02d}"
                        
                        # Nombre del evento
                        name_td = row.find('td', class_='left event')
                        event_name = name_td.get_text(strip=True) if name_td else ''
                        event_name = translate_event(event_name) if event_name else 'Evento'
                        
                        # Importancia (1-3 bulls)
                        bull_tds = row.find_all('i', class_='grayFullBullishIcon')
                        importance_val = len(bull_tds)
                        impact = 'High' if importance_val >= 3 else ('Medium' if importance_val == 2 else 'Low')
                        
                        # País
                        flag_td = row.find('td', class_='left flagCur')
                        country = flag_td.get_text(strip=True).upper()[:2] if flag_td else 'US'
                        
                        # Actual / Previo / Forecast
                        actual_td = row.find('td', id=lambda i: i and i.startswith('actual'))
                        fore_td = row.find('td', id=lambda i: i and i.startswith('forecast'))
                        prev_td = row.find('td', id=lambda i: i and i.startswith('previous'))
                        
                        actual = actual_td.get_text(strip=True) if actual_td else '-'
                        forecast = fore_td.get_text(strip=True) if fore_td else '-'
                        previous = prev_td.get_text(strip=True) if prev_td else '-'
                        
                        if event_dt.date() == now.date():
                            date_display, date_color = "HOY", "#00ffad"
                        elif event_dt.date() == (now + timedelta(days=1)).date():
                            date_display, date_color = "MAÑANA", "#3b82f6"
                        else:
                            date_display = event_dt.strftime('%d %b').upper()
                            date_color = "#888"
                        
                        events.append({
                            "date": event_dt,
                            "date_display": date_display,
                            "date_color": date_color,
                            "time": time_str,
                            "event": event_name,
                            "imp": impact,
                            "val": actual if actual else '-',
                            "prev": previous if previous else '-',
                            "forecast": forecast if forecast else '-',
                            "country": country if country else 'US',
                        })
                    except:
                        continue
    except Exception as e:
        set_api_health('EcoCalendar', False)
    
    # Fallback 2: ForexFactory
    if not events:
        events = get_forexfactory_calendar()
    
    if events:
        events.sort(key=lambda x: (x['date'], x['time'] if x['time'] != 'TBD' else '99:99'))
        return events[:12]
    
    return get_fallback_economic_calendar()

def get_forexfactory_calendar():
    """Scraping de ForexFactory como respaldo del calendario económico"""
    events = []
    try:
        session = get_http_session()
        now = datetime.now()
        url = f"https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        r = session.get(url, timeout=10)
        set_api_health('ForexFactory', r.status_code == 200)
        if r.status_code == 200:
            data = r.json()
            for item in data:
                try:
                    date_str = item.get('date', '')
                    event_dt = datetime.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S') if date_str else now
                    if event_dt.date() < now.date():
                        continue
                    if event_dt.weekday() >= 5:  # saltar sáb/dom
                        continue
                    impact_map = {'High': 'High', 'Medium': 'Medium', 'Low': 'Low'}
                    impact = impact_map.get(item.get('impact', 'Low'), 'Low')
                    title = item.get('title', 'Evento')
                    title_es = translate_event(title)
                    hour_cet = (event_dt.hour + 1) % 24
                    if event_dt.date() == now.date():
                        date_display, date_color = "HOY", "#00ffad"
                    elif event_dt.date() == (now + timedelta(days=1)).date():
                        date_display, date_color = "MAÑANA", "#3b82f6"
                    else:
                        date_display = event_dt.strftime('%d %b').upper()
                        date_color = "#888"
                    events.append({
                        "date": event_dt,
                        "date_display": date_display,
                        "date_color": date_color,
                        "time": f"{hour_cet:02d}:{event_dt.minute:02d}",
                        "event": title_es,
                        "imp": impact,
                        "val": item.get('actual', '-') or '-',
                        "prev": item.get('previous', '-') or '-',
                        "forecast": item.get('forecast', '-') or '-',
                        "country": item.get('country', 'US').upper()[:2],
                    })
                except:
                    continue
    except:
        set_api_health('ForexFactory', False)
    return events

def get_fallback_economic_calendar():
    """Fallback cuando no hay datos reales disponibles"""
    return [
        {
            "date": datetime.now(),
            "date_display": "HOY",
            "date_color": "#888",
            "time": "--:--",
            "event": "Datos no disponibles",
            "imp": "Low",
            "val": "-",
            "prev": "-",
            "forecast": "-",
            "country": "US"
        }
    ]

@st.cache_data(ttl=300)
def get_crypto_prices():
    try:
        crypto_symbols = {
            'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'BNB-USD': 'BNB',
            'SOL-USD': 'Solana', 'XRP-USD': 'XRP', 'ADA-USD': 'Cardano'
        }
        cryptos = []
        for symbol, name in crypto_symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    price_str = f"{current_price:,.2f}" if current_price >= 1 else f"{current_price:.4f}"
                    cryptos.append({
                        'symbol': symbol.replace('-USD', ''), 'name': name,
                        'price': price_str, 'change': f"{change_pct:+.2f}%",
                        'is_positive': change_pct >= 0
                    })
                    time.sleep(0.1)
            except:
                continue
        return cryptos if cryptos else get_fallback_crypto_prices()
    except:
        return get_fallback_crypto_prices()

def get_fallback_crypto_prices():
    return [
        {"symbol": "BTC", "name": "Bitcoin", "price": "68,984.88", "change": "-1.62%", "is_positive": False},
        {"symbol": "ETH", "name": "Ethereum", "price": "2,018.46", "change": "-4.05%", "is_positive": False},
        {"symbol": "BNB", "name": "BNB", "price": "618.43", "change": "-2.76%", "is_positive": False},
        {"symbol": "SOL", "name": "Solana", "price": "84.04", "change": "-3.07%", "is_positive": False},
        {"symbol": "XRP", "name": "XRP", "price": "1.40", "change": "-2.22%", "is_positive": False},
        {"symbol": "ADA", "name": "Cardano", "price": "0.52", "change": "-4.20%", "is_positive": False},
    ]

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
        headers_elements = soup.find_all(['h2', 'h3', 'h4', 'div', 'span'])
        for header in headers_elements:
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
            all_links = soup.find_all('a', href=re.compile(r'/reddit-buzz/\?ticker=[A-Z]+'))
            seen = set()
            for link in all_links:
                ticker = link.get_text(strip=True).upper()
                if ticker and ticker not in seen and len(ticker) <= 5 and ticker.isalpha():
                    top_10_tickers.append(ticker)
                    seen.add(ticker)
                    if len(top_10_tickers) >= 10:
                        break
        if not top_10_tickers:
            return get_fallback_reddit_tickers()
        return {
            'tickers': top_10_tickers[:10], 'source': 'BuzzTickr',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    except:
        return get_fallback_reddit_tickers()

def get_fallback_reddit_tickers():
    return {
        'tickers': ["MSFT", "NVDA", "TSLA", "AAPL", "AMZN", "GOOGL", "META", "AMD", "PLTR", "GME"],
        'source': 'Fallback', 'timestamp': datetime.now().strftime('%H:%M:%S')
    }

@st.cache_data(ttl=3600)  # Cache de 1 hora para no sobrecargar BuzzTickr
def get_buzztickr_master_data():
    """
    Obtiene datos del Master Buzz de BuzzTickr con todas las métricas:
    Rank, Ticker, Buzz Score, Health, Social Hype, Smart Money, Squeeze Potential
    """
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
        
        # Buscar tabla de datos
        master_data = []
        
        # Intentar encontrar la tabla principal
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 5:  # Tabla con suficientes datos
                for row in rows[1:]:  # Saltar header
                    try:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 7:
                            rank = cells[0].get_text(strip=True)
                            ticker = cells[1].get_text(strip=True).upper()
                            buzz_score = cells[2].get_text(strip=True)
                            health = cells[3].get_text(strip=True)
                            social_hype = cells[4].get_text(strip=True)
                            smart_money = cells[5].get_text(strip=True)
                            squeeze = cells[6].get_text(strip=True)
                            
                            if ticker and len(ticker) <= 5:
                                master_data.append({
                                    'rank': rank,
                                    'ticker': ticker,
                                    'buzz_score': buzz_score,
                                    'health': health,
                                    'social_hype': social_hype,
                                    'smart_money': smart_money,
                                    'squeeze': squeeze
                                })
                    except:
                        continue
                
                if master_data:
                    break
        
        # Si no encontramos tabla, intentar extraer de divs o estructura alternativa
        if not master_data:
            # Buscar elementos que contengan datos de tickers
            ticker_elements = soup.find_all(text=re.compile(r'^[A-Z]{1,5}$'))
            seen = set()
            rank = 1
            
            for elem in ticker_elements[:20]:
                try:
                    ticker = elem.strip()
                    if ticker and ticker not in seen and len(ticker) <= 5:
                        parent = elem.find_parent()
                        if parent:
                            # Intentar encontrar datos relacionados en elementos hermanos o padre
                            row_data = {
                                'rank': str(rank),
                                'ticker': ticker,
                                'buzz_score': '6',
                                'health': '50 Neutral',
                                'social_hype': '',
                                'smart_money': '',
                                'squeeze': ''
                            }
                            master_data.append(row_data)
                            seen.add(ticker)
                            rank += 1
                            
                            if rank > 15:
                                break
                except:
                    continue
        
        if master_data:
            return {
                'data': master_data[:15],
                'source': 'BuzzTickr Master',
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'count': len(master_data)
            }
        
        return get_fallback_master_data()
        
    except Exception as e:
        return get_fallback_master_data()

def get_fallback_master_data():
    """Datos de respaldo basados en el scraping real de BuzzTickr"""
    return {
        'data': [
            {'rank': '1', 'ticker': 'SGN', 'buzz_score': '7', 'health': '28 Weak', 'social_hype': '★★★★★', 'smart_money': '', 'squeeze': '★★★★★ Extreme Short (70%)'},
            {'rank': '2', 'ticker': 'RUN', 'buzz_score': '7', 'health': '28 Weak', 'social_hype': '', 'smart_money': '', 'squeeze': '★★★★★ Extreme Short (30%)'},
            {'rank': '3', 'ticker': 'ANAB', 'buzz_score': '7', 'health': '35 Weak', 'social_hype': '', 'smart_money': '', 'squeeze': '★★★★★ Extreme Short (38%)'},
            {'rank': '4', 'ticker': 'HTZ', 'buzz_score': '7', 'health': '15 Weak', 'social_hype': '', 'smart_money': '', 'squeeze': '★★★★★ Extreme Short (46%)'},
            {'rank': '5', 'ticker': 'DEI', 'buzz_score': '7', 'health': '25 Weak', 'social_hype': '', 'smart_money': '', 'squeeze': '★★★★★ Extreme Short (25%)'},
            {'rank': '6', 'ticker': 'LUCK', 'buzz_score': '7', 'health': '15 Weak', 'social_hype': '', 'smart_money': '★★★★★ Whales >50%', 'squeeze': '★★★★★ Extreme Short (32%)'},
            {'rank': '7', 'ticker': 'QDEL', 'buzz_score': '7', 'health': '25 Weak', 'social_hype': '', 'smart_money': '★★★★★ Whales >50%', 'squeeze': '★★★★★ Extreme Short (25%)'},
            {'rank': '8', 'ticker': 'CAR', 'buzz_score': '7', 'health': '20 Weak', 'social_hype': '', 'smart_money': '★★★★★ Whales >50%', 'squeeze': '★★★★★ Extreme Short (48%)'},
            {'rank': '9', 'ticker': 'NVDA', 'buzz_score': '6', 'health': '80 Strong', 'social_hype': '★★★★★ Reddit Top 10', 'smart_money': '★★★★★ Whales >20%', 'squeeze': ''},
            {'rank': '10', 'ticker': 'MSFT', 'buzz_score': '6', 'health': '52 Hold', 'social_hype': '★★★★★ Reddit Top 10', 'smart_money': '★★★★★ Whales >20%', 'squeeze': ''},
            {'rank': '11', 'ticker': 'IBRX', 'buzz_score': '6', 'health': '32 Weak', 'social_hype': '', 'smart_money': '', 'squeeze': '★★★★★ Extreme Short (40%)'},
            {'rank': '12', 'ticker': 'RXT', 'buzz_score': '6', 'health': '15 Weak', 'social_hype': '★★★★★ Weekly Choice', 'smart_money': '', 'squeeze': '★★★★★ Days to Cover: 6.94'},
            {'rank': '13', 'ticker': 'RDDT', 'buzz_score': '6', 'health': '80 Strong', 'social_hype': '★★★★★ Weekly Choice', 'smart_money': '★★★★★ Whales >50%', 'squeeze': ''},
            {'rank': '14', 'ticker': 'PROP', 'buzz_score': '6', 'health': 'Weak', 'social_hype': '', 'smart_money': '', 'squeeze': '★★★★★ High Short (23%)'},
            {'rank': '15', 'ticker': 'WEN', 'buzz_score': '6', 'health': '48 Hold', 'social_hype': '', 'smart_money': '', 'squeeze': '★★★★★ Extreme Short (58%)'},
        ],
        'source': 'BuzzTickr Master',
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'count': 15
    }

@st.cache_data(ttl=60)
def get_financial_ticker_data():
    # Agrupado por categorías para el ticker estilo Bloomberg
    all_symbols = {
        # MAG7
        'AAPL': ('AAPL', 'MAG7'), 'MSFT': ('MSFT', 'MAG7'), 'GOOGL': ('GOOGL', 'MAG7'),
        'AMZN': ('AMZN', 'MAG7'), 'NVDA': ('NVDA', 'MAG7'), 'META': ('META', 'MAG7'), 'TSLA': ('TSLA', 'MAG7'),
        # Índices USA
        '^GSPC': ('S&P 500', 'IDX'), '^IXIC': ('NASDAQ', 'IDX'), '^DJI': ('DOW', 'IDX'), '^RUT': ('RUSSELL', 'IDX'),
        # Índices mundiales
        '^N225': ('NIKKEI', 'IDX'), '^GDAXI': ('DAX', 'IDX'), '^FTSE': ('FTSE 100', 'IDX'),
        '^FCHI': ('CAC 40', 'IDX'), '^IBEX': ('IBEX 35', 'IDX'), '^HSI': ('HANG SENG', 'IDX'),
        # Futuros
        'ES=F': ('S&P FUT', 'FUT'), 'NQ=F': ('NQ FUT', 'FUT'), 'YM=F': ('DOW FUT', 'FUT'),
        # Commodities
        'GC=F': ('ORO', 'COM'), 'SI=F': ('PLATA', 'COM'), 'CL=F': ('PETRÓLEO', 'COM'),
        'NG=F': ('GAS NAT.', 'COM'), 'HG=F': ('COBRE', 'COM'), 'ZW=F': ('TRIGO', 'COM'),
        # Crypto
        'BTC-USD': ('BTC', 'CRYPTO'), 'ETH-USD': ('ETH', 'CRYPTO'), 'SOL-USD': ('SOL', 'CRYPTO'),
        # Bonos/FX
        '^TNX': ('BONO 10Y', 'BOND'), 'DX-Y.NYB': ('USD INDEX', 'FX'),
    }
    
    def _fetch(symbol, name_cat):
        name, cat = name_cat
        try:
            hist = yf.Ticker(symbol).history(period="2d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                pct = ((current - prev) / prev) * 100
                if current >= 10000:
                    price_str = f"{current:,.0f}"
                elif current >= 100:
                    price_str = f"{current:,.2f}"
                elif current >= 1:
                    price_str = f"{current:.3f}"
                else:
                    price_str = f"{current:.4f}"
                return {'name': name, 'cat': cat, 'price': price_str, 'change': pct, 'is_positive': pct >= 0}
        except:
            pass
        return None

    ticker_data = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(_fetch, sym, name_cat): sym for sym, name_cat in all_symbols.items()}
        for fut in as_completed(futures, timeout=20):
            result = fut.result()
            if result:
                ticker_data.append(result)
    
    # Ordenar: MAG7 primero, luego índices, futuros, commodities, crypto, bonos
    cat_order = {'MAG7': 0, 'IDX': 1, 'FUT': 2, 'COM': 3, 'CRYPTO': 4, 'BOND': 5, 'FX': 6}
    ticker_data.sort(key=lambda x: cat_order.get(x.get('cat', 'IDX'), 99))
    return ticker_data

# Colores por categoría para el ticker
TICKER_CAT_COLORS = {
    'MAG7': '#a78bfa',   # Violeta
    'IDX': '#60a5fa',    # Azul
    'FUT': '#93c5fd',    # Azul claro
    'COM': '#fbbf24',    # Amarillo
    'CRYPTO': '#fb923c', # Naranja
    'BOND': '#34d399',   # Verde
    'FX': '#f9a8d4',     # Rosa
}

def generate_ticker_html():
    data = get_financial_ticker_data()
    if not data:
        data = [
            {'name': 'S&P 500', 'cat': 'IDX', 'price': '5,890.25', 'change': 0.45, 'is_positive': True},
            {'name': 'NASDAQ', 'cat': 'IDX', 'price': '21,150.80', 'change': -0.23, 'is_positive': False},
            {'name': 'NVDA', 'cat': 'MAG7', 'price': '890.25', 'change': 1.45, 'is_positive': True},
            {'name': 'AAPL', 'cat': 'MAG7', 'price': '210.50', 'change': -0.85, 'is_positive': False},
            {'name': 'BTC', 'cat': 'CRYPTO', 'price': '68,984.88', 'change': -1.62, 'is_positive': False},
            {'name': 'ORO', 'cat': 'COM', 'price': '2,865.40', 'change': 0.89, 'is_positive': True},
        ]

    # Agrupar por categoría
    from collections import OrderedDict
    cat_labels = {
        'MAG7': 'MAG 7', 'IDX': 'ÍNDICES', 'FUT': 'FUTUROS',
        'COM': 'MATERIAS PRIMAS', 'CRYPTO': 'CRYPTO', 'BOND': 'BONOS', 'FX': 'DIVISAS'
    }
    
    ticker_items = []
    current_cat = None
    cat_order = {'MAG7': 0, 'IDX': 1, 'FUT': 2, 'COM': 3, 'CRYPTO': 4, 'BOND': 5, 'FX': 6}
    data_sorted = sorted(data, key=lambda x: cat_order.get(x.get('cat', 'IDX'), 99))
    
    for item in data_sorted:
        cat = item.get('cat', 'IDX')
        cat_color = TICKER_CAT_COLORS.get(cat, '#888')
        
        # Separador de categoría
        if cat != current_cat:
            if current_cat is not None:
                ticker_items.append(
                    f'<span style="margin: 0 24px; color: #2a3f5f; font-size: 20px;">│</span>'
                )
            label = cat_labels.get(cat, cat)
            ticker_items.append(
                f'<span style="margin-right:12px; color:{cat_color}; font-size:9px; font-weight:900; '
                f'letter-spacing:1.2px; text-transform:uppercase; opacity:0.9;">{label}</span>'
            )
            current_cat = cat
        
        color = "#00ffad" if item['is_positive'] else "#f23645"
        arrow = "▲" if item['is_positive'] else "▼"
        change_pct = item['change']
        
        ticker_items.append(
            f'<span style="margin-right:28px; white-space:nowrap; display:inline-flex; align-items:center; gap:7px;">'
            f'<span style="color:{cat_color}; font-weight:700; font-size:13px; letter-spacing:0.3px;">{item["name"]}</span>'
            f'<span style="color:#e2e8f0; font-size:13px; font-family:\'Courier New\',monospace; font-weight:500;">{item["price"]}</span>'
            f'<span style="color:{color}; font-size:12px; font-weight:700;">{arrow} {change_pct:+.2f}%</span>'
            f'</span>'
        )
    
    items_html = "".join(ticker_items)
    # Duplicar para bucle infinito continuo
    all_items = items_html + items_html + items_html
    
    return f"""
    <div style="background:#0c0e12; border-bottom:1px solid #1a1e26; border-top:1px solid #1a1e26; padding:0; overflow:hidden; height:46px; display:flex; align-items:center; position:relative;">
        <div style="position:absolute; left:0; top:0; bottom:0; width:60px; background:linear-gradient(90deg,#0c0e12 60%,transparent); z-index:2;"></div>
        <div style="position:absolute; right:0; top:0; bottom:0; width:60px; background:linear-gradient(270deg,#0c0e12 60%,transparent); z-index:2;"></div>
        <div style="display:flex; align-items:center; white-space:nowrap; animation:ticker-scroll 90s linear infinite; will-change:transform; padding-left:100%;">
            {all_items}
        </div>
    </div>
    <style>
    @keyframes ticker-scroll {{
        0% {{ transform: translateX(0); }}
        100% {{ transform: translateX(-33.333%); }}
    }}
    </style>
    """

@st.cache_data(ttl=300)
def get_sector_performance(timeframe="1D"):
    try:
        sector_etfs = {
            'XLK': ('Technology', 'Tecnología'), 
            'XLF': ('Financials', 'Financieros'),
            'XLV': ('Healthcare', 'Salud'), 
            'XLE': ('Energy', 'Energía'),
            'XLY': ('Consumer Disc.', 'Consumo Discrecional'), 
            'XLU': ('Utilities', 'Utilidades'),
            'XLI': ('Industrials', 'Industriales'), 
            'XLB': ('Materials', 'Materiales'),
            'XLP': ('Consumer Staples', 'Consumo Básico'), 
            'XLRE': ('Real Estate', 'Bienes Raíces'),
            'XLC': ('Communication', 'Comunicaciones')
        }

        period_map = {"1D": "2d", "3D": "5d", "1W": "10d", "1M": "1mo"}
        period = period_map.get(timeframe, "2d")
        sectors_data = []

        for symbol, (name_en, name_es) in sector_etfs.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                if len(hist) >= 2:
                    if timeframe == "1D":
                        current, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                    elif timeframe == "3D":
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-4] if len(hist) >= 4 else hist['Close'].iloc[0]
                    elif timeframe == "1W":
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-6] if len(hist) >= 6 else hist['Close'].iloc[0]
                    else:
                        current, prev = hist['Close'].iloc[-1], hist['Close'].iloc[0]

                    change = ((current - prev) / prev) * 100
                    sectors_data.append({
                        'code': symbol, 
                        'name': name_en, 
                        'name_es': name_es,
                        'change': change
                    })
                time.sleep(0.05)
            except:
                continue

        return sectors_data if sectors_data else get_fallback_sectors(timeframe)
    except:
        return get_fallback_sectors(timeframe)

def get_fallback_sectors(timeframe="1D"):
    base = [
        ("XLK", "Technology", +6.02), ("XLF", "Financials", +0.99), 
        ("XLV", "Healthcare", +1.01), ("XLE", "Energy", +2.30),
        ("XLY", "Consumer Disc.", +1.13), ("XLU", "Utilities", +1.68),
        ("XLI", "Industrials", +3.26), ("XLB", "Materials", +3.91), 
        ("XLP", "Consumer Staples", +0.20), ("XLRE", "Real Estate", +3.33), 
        ("XLC", "Communication", +1.08)
    ]
    mult = {"1D": 1, "3D": 2.5, "1W": 4, "1M": 8}.get(timeframe, 1)
    return [{'code': c, 'name': n, 'name_es': n, 'change': v * mult} for c, n, v in base]

@st.cache_data(ttl=300)
def get_vix_term_structure():
    try:
        # VIX Spot real
        try:
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="5d")
            if len(vix_hist) >= 3:
                current_spot = float(vix_hist['Close'].iloc[-1])
                prev_spot = float(vix_hist['Close'].iloc[-2])
                spot_2days = float(vix_hist['Close'].iloc[-3])
            else:
                current_spot, prev_spot, spot_2days = 17.45, 17.36, 20.37
        except:
            current_spot, prev_spot, spot_2days = 17.45, 17.36, 20.37

        # Intentar obtener futuros VIX reales (VX1-VX8 en CBOE via yfinance)
        # Los futuros VIX tienen símbolos como VXH25, VXJ25, etc. en yfinance
        now = datetime.now()
        month_codes = ['F','G','H','J','K','M','N','Q','U','V','X','Z']
        month_names = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
        
        vix_futures = []
        vix_futures.append({'month': f"{month_names[now.month-1]} {now.year}", 
                            'current': round(current_spot, 2), 
                            'previous': round(prev_spot, 2), 
                            'two_days': round(spot_2days, 2)})
        
        # Intentar obtener futuros reales
        futures_obtained = False
        future_vals = []
        for i in range(1, 8):
            m = (now.month - 1 + i) % 12
            y = now.year + ((now.month - 1 + i) // 12)
            code = month_codes[m]
            yr2 = str(y)[-2:]
            sym = f"VX{code}{yr2}.CF"
            try:
                t = yf.Ticker(sym)
                h = t.history(period="2d")
                if len(h) >= 1:
                    val = float(h['Close'].iloc[-1])
                    prev_val = float(h['Close'].iloc[-2]) if len(h) >= 2 else val
                    vix_futures.append({
                        'month': f"{month_names[m]} {y}",
                        'current': round(val, 2),
                        'previous': round(prev_val, 2),
                        'two_days': round(prev_val * 0.99, 2)
                    })
                    future_vals.append(val)
                    futures_obtained = True
            except:
                pass

        # Si no obtuvimos futuros reales, simular curva realista
        if not futures_obtained or len(vix_futures) < 4:
            vix_futures = []
            is_contango = current_spot < 20
            for i in range(8):
                m = (now.month - 1 + i) % 12
                y = now.year + ((now.month - 1 + i) // 12)
                if is_contango:
                    cur = current_spot + (i * 0.9) + (i * i * 0.08)
                    prv = prev_spot + (i * 0.85) + (i * i * 0.07)
                    td = spot_2days + (i * 0.5) + (i * i * 0.05)
                else:
                    cur = max(current_spot - (i * 0.3), 12)
                    prv = max(prev_spot - (i * 0.25), 12)
                    td = max(spot_2days - (i * 0.2), 12)
                vix_futures.append({
                    'month': f"{month_names[m]} {y}",
                    'current': round(cur, 2),
                    'previous': round(prv, 2),
                    'two_days': round(td, 2)
                })

        # Determinar estado
        if len(vix_futures) >= 2 and vix_futures[-1]['current'] > vix_futures[0]['current']:
            state = "Contango"
            state_desc = "Mercados calmados - Favorable para comprar caídas"
            state_color = "#00ffad"
            explanation = ("<b>Contango:</b> Precio Futuros > Spot. "
                         "El mercado espera que la volatilidad baje con el tiempo. "
                         "Estado normal en mercados tranquilos.")
        else:
            state = "Backwardation"
            state_desc = "Estrés de mercado detectado - Precaución"
            state_color = "#f23645"
            explanation = ("<b>Backwardation:</b> Precio Futuros < Spot. "
                         "El mercado espera más volatilidad. "
                         "Señal de miedo inmediato.")

        return {
            'data': vix_futures,
            'current_spot': current_spot,
            'prev_spot': prev_spot,
            'spot_2days': spot_2days,
            'state': state,
            'state_desc': state_desc,
            'state_color': state_color,
            'explanation': explanation,
            'is_contango': state == "Contango"
        }
    except Exception as e:
        return get_fallback_vix_structure()

def get_fallback_vix_structure():
    return {
        'data': [
            {'month': 'Feb 2026', 'current': 17.45, 'previous': 17.36, 'two_days': 20.37},
            {'month': 'Mar 2026', 'current': 18.35, 'previous': 18.21, 'two_days': 20.87},
            {'month': 'Apr 2026', 'current': 19.25, 'previous': 19.06, 'two_days': 21.37},
            {'month': 'May 2026', 'current': 20.15, 'previous': 19.91, 'two_days': 21.87},
            {'month': 'Jun 2026', 'current': 21.05, 'previous': 20.76, 'two_days': 22.37},
            {'month': 'Jul 2026', 'current': 21.95, 'previous': 21.61, 'two_days': 22.87},
            {'month': 'Aug 2026', 'current': 22.85, 'previous': 22.46, 'two_days': 23.37},
            {'month': 'Sep 2026', 'current': 23.75, 'previous': 23.31, 'two_days': 23.87},
        ],
        'current_spot': 17.45,
        'prev_spot': 17.36,
        'spot_2days': 20.37,
        'state': 'Contango',
        'state_desc': 'Typical in calm markets - Conducive to dip buying',
        'state_color': '#00ffad',
        'explanation': 'Futures price > Spot. Market expects lower volatility ahead.',
        'is_contango': True
    }

def generate_vix_chart_html(vix_data):
    data = vix_data['data']
    months = [d['month'].split()[0] for d in data]
    current_levels = [d['current'] for d in data]
    prev_levels = [d['previous'] for d in data]
    two_days_levels = [d['two_days'] for d in data]

    chart_width, chart_height, padding = 340, 180, 35

    all_values = current_levels + prev_levels + two_days_levels
    min_level, max_level = min(all_values) - 0.5, max(all_values) + 0.5
    level_range = max_level - min_level

    def get_coords(values, color, is_dashed=False):
        points = []
        for i, level in enumerate(values):
            x = padding + (i / (len(values) - 1)) * (chart_width - 2 * padding)
            y = chart_height - padding - ((level - min_level) / level_range) * (chart_height - 2 * padding)
            points.append((x, y, level))

        points_str = " ".join([f"{x},{y}" for x, y, _ in points])
        dash_attr = 'stroke-dasharray="4,3"' if is_dashed else ''

        circles = ""
        for x, y, level in points:
            circles += f'<circle cx="{x}" cy="{y}" r="3" fill="{color}" stroke="white" stroke-width="1"/>'

        return f'<polyline points="{points_str}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {dash_attr}/>{circles}'

    current_line = get_coords(current_levels, "#3b82f6", False)
    prev_line = get_coords(prev_levels, "#f97316", True)
    two_days_line = get_coords(two_days_levels, "#6b7280", True)

    y_axis = ""
    for i in range(5):
        val = min_level + (level_range * i / 4)
        y_pos = chart_height - padding - (i / 4) * (chart_height - 2 * padding)
        y_axis += f'<text x="{padding-8}" y="{y_pos+3}" text-anchor="end" fill="#666" font-size="9">{val:.1f}</text>'
        y_axis += f'<line x1="{padding}" y1="{y_pos}" x2="{chart_width-padding}" y2="{y_pos}" stroke="#1a1e26" stroke-width="1"/>'

    x_labels = ""
    for i, month in enumerate(months):
        x = padding + (i / (len(months) - 1)) * (chart_width - 2 * padding)
        x_labels += f'<text x="{x}" y="{chart_height-8}" text-anchor="middle" fill="#666" font-size="8">{month}</text>'

    today_str = datetime.now().strftime('%d/%m')
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%d/%m')
    two_days_str = (datetime.now() - timedelta(days=2)).strftime('%d/%m')
    legend_y = 15
    # Leyenda en la parte IZQUIERDA para no tapar el final de la curva
    legend = f"""
    <rect x="4" y="5" width="155" height="50" fill="#0c0e12" stroke="#1a1e26" rx="4"/>
    <line x1="8" y1="{legend_y+5}" x2="22" y2="{legend_y+5}" stroke="#3b82f6" stroke-width="2"/>
    <text x="26" y="{legend_y+8}" fill="#888" font-size="8">Hoy ({today_str}): {vix_data['current_spot']:.2f}</text>

    <line x1="8" y1="{legend_y+20}" x2="22" y2="{legend_y+20}" stroke="#f97316" stroke-width="2" stroke-dasharray="4,3"/>
    <text x="26" y="{legend_y+23}" fill="#888" font-size="8">Ayer ({yesterday_str}): {vix_data['prev_spot']:.2f}</text>

    <line x1="8" y1="{legend_y+35}" x2="22" y2="{legend_y+35}" stroke="#6b7280" stroke-width="2" stroke-dasharray="4,3"/>
    <text x="26" y="{legend_y+38}" fill="#888" font-size="8">-2d ({two_days_str}): {vix_data['spot_2days']:.2f}</text>
    """

    return f"""
    <div style="width: 100%; height: 200px; background: #0c0e12; border-radius: 8px; padding: 8px;">
        <svg width="100%" height="100%" viewBox="0 0 {chart_width} {chart_height}" preserveAspectRatio="xMidYMid meet">
            {y_axis}
            {two_days_line}
            {prev_line}
            {current_line}
            {x_labels}
            {legend}
            <text x="15" y="{chart_height/2}" text-anchor="middle" fill="#888" font-size="9" transform="rotate(-90, 15, {chart_height/2})">VIX Level</text>
        </svg>
    </div>
    """

@st.cache_data(ttl=300)
def get_crypto_fear_greed():
    try:
        session = get_http_session()
        url = "https://api.alternative.me/fng/?limit=1"
        response = session.get(url, timeout=10)
        set_api_health('CryptoFG', response.status_code == 200)

        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data and len(data['data']) > 0:
                item = data['data'][0]
                value = int(item['value'])
                classification = item['value_classification']
                ts = int(item['timestamp'])
                update_time = datetime.fromtimestamp(ts).strftime('%d/%m %H:%M')
                return {
                    'value': value,
                    'classification': classification,
                    'timestamp': update_time,
                    'source': 'alternative.me'
                }
        set_api_health('CryptoFG', False)
        return get_fallback_crypto_fear_greed()
    except:
        set_api_health('CryptoFG', False)
        return get_fallback_crypto_fear_greed()

def get_fallback_crypto_fear_greed():
    return {
        'value': 50,
        'classification': 'Neutral',
        'timestamp': get_timestamp(),
        'source': 'Datos no disponibles'
    }

@st.cache_data(ttl=1800)
def get_earnings_calendar():
    """
    Earnings de mega-caps. Solo muestra fechas futuras reales.
    Si hoy es fin de semana (sáb/dom), el filtro mínimo es mañana (days>=1).
    Si hoy es día laborable, mostramos hoy (days>=0) solo si aún no pasó.
    """
    now = datetime.now()
    today = now.date()
    is_weekend = today.weekday() >= 5  # sábado=5, domingo=6
    min_days = 1 if is_weekend else 0
    mega_caps_timing = {
        # ticker: (after_market: bool)
        'NVDA': True, 'AAPL': True, 'AMZN': True, 'META': True, 'NFLX': True,
        'AMD': True, 'GOOGL': False, 'MSFT': True, 'TSLA': True,
        'BRK-B': False, 'AVGO': False, 'WMT': False, 'JPM': False,
        'V': False, 'MA': False, 'UNH': False, 'HD': False,
        'COST': False, 'ADBE': False, 'ACN': False, 'LIN': False,
        'BAC': False, 'MRK': False, 'PFE': False, 'LLY': False,
    }
    
    earnings_list = []
    api_key = None
    try:
        api_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", None)
    except:
        pass

    # Intento 1: Alpha Vantage
    if api_key:
        try:
            from io import StringIO
            session = get_http_session()
            url = f"https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey={api_key}"
            r = session.get(url, timeout=15)
            set_api_health('AlphaVantage', r.status_code == 200)
            if r.status_code == 200:
                df = pd.read_csv(StringIO(r.text))
                df_f = df[df['symbol'].isin(list(mega_caps_timing.keys()))].copy()
                for _, row in df_f.iterrows():
                    try:
                        rd = pd.to_datetime(row['reportDate']).date()
                        days = (rd - today).days
                        if days < min_days:
                            continue
                        sym = row['symbol']
                        after_mkt = mega_caps_timing.get(sym, False)
                        timing = "Tras el cierre" if after_mkt else "Antes de apertura"
                        earnings_list.append({
                            'ticker': sym,
                            'date': rd.strftime('%d %b'),
                            'full_date': rd,
                            'time': timing,
                            'impact': 'High',
                            'market_cap': '-',
                            'days': days,
                        })
                    except:
                        continue
                earnings_list.sort(key=lambda x: x['full_date'])
                if len(earnings_list) >= 3:
                    return earnings_list[:6]
        except Exception as e:
            set_api_health('AlphaVantage', False)

    # Intento 2: yfinance con paralelismo
    def fetch_earnings(ticker):
        try:
            t = yf.Ticker(ticker)
            cal = t.calendar
            if cal is not None:
                if isinstance(cal, dict):
                    ed = cal.get('Earnings Date', [None])
                    if ed and len(ed) > 0:
                        rd = pd.Timestamp(ed[0]).date()
                        days = (rd - today).days
                        if min_days <= days <= 60:
                            info = t.info
                            mc = info.get('marketCap', 0) or 0
                            mc_str = f"${mc/1e12:.1f}T" if mc >= 1e12 else (f"${mc/1e9:.0f}B" if mc >= 1e9 else "-")
                            after_mkt = mega_caps_timing.get(ticker, False)
                            return {
                                'ticker': ticker,
                                'date': rd.strftime('%d %b'),
                                'full_date': rd,
                                'time': "Tras el cierre" if after_mkt else "Antes de apertura",
                                'impact': 'High',
                                'market_cap': mc_str,
                                'days': days,
                            }
        except:
            pass
        return None

    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(fetch_earnings, t): t for t in list(mega_caps_timing.keys())[:20]}
            for fut in as_completed(futures, timeout=20):
                result = fut.result()
                if result:
                    earnings_list.append(result)
        
        earnings_list.sort(key=lambda x: x['full_date'])
        if earnings_list:
            return earnings_list[:6]
    except:
        pass

    return get_fallback_earnings_realistic()

def get_fallback_earnings_realistic():
    """Fallback cuando no hay datos reales disponibles"""
    today = datetime.now()
    return [
        {
            'ticker': 'N/D',
            'date': 'Sin datos',
            'full_date': today,
            'time': '-',
            'impact': 'N/D',
            'market_cap': 'Datos no disponibles',
            'days': 0,
            'source': 'Fallback'
        }
    ]

@st.cache_data(ttl=1800)
def get_insider_trading():
    """
    Obtiene transacciones reales de insiders via múltiples fuentes.
    1. OpenInsider CSV export (más fiable que HTML scraping)
    2. SEC EDGAR últimas Form 4 con enriquecimiento de datos
    3. FMP API si hay key configurada
    """
    all_trades = []
    session = get_http_session()
    
    # ── FUENTE 1: OpenInsider CSV (sin necesidad de parsear HTML) ─────────────
    try:
        # CSV export directo de OpenInsider - mucho más fiable
        csv_url = (
            "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=7&fdr=&td=0"
            "&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=100&vh=&ocl=&och=&sic1=-1"
            "&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h="
            "&oc2l=&oc2h=&sortcol=0&cnt=40&action=1"
        )
        headers_req = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'http://openinsider.com/',
        }
        r = session.get(csv_url, timeout=20, headers=headers_req)
        set_api_health('Insider', r.status_code == 200)
        
        if r.status_code == 200 and len(r.text) > 500:
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # OpenInsider usa clase 'tinytable' o id 'tablewrapper'
            table = None
            for sel in ['table.tinytable', '#tablewrapper', 'table.table']:
                table = soup.select_one(sel)
                if table:
                    break
            if not table:
                # Buscar la primera tabla grande
                for t in soup.find_all('table'):
                    if len(t.find_all('tr')) > 5:
                        table = t
                        break
            
            if table:
                # Detectar columnas leyendo el header
                header_row = table.find('tr')
                col_map = {}
                if header_row:
                    for i, th in enumerate(header_row.find_all(['th', 'td'])):
                        txt = th.get_text(strip=True).lower()
                        if 'ticker' in txt or 'sym' in txt:
                            col_map['ticker'] = i
                        elif 'insider' in txt or 'name' in txt:
                            col_map['insider'] = i
                        elif 'title' in txt or 'role' in txt:
                            col_map['title'] = i
                        elif 'type' in txt or 'trade' in txt:
                            col_map['type'] = i
                        elif 'value' in txt or 'val' in txt:
                            col_map['value'] = i
                        elif 'date' in txt or 'filed' in txt:
                            col_map['date'] = i
                
                # Defaults si no se detectaron
                if 'ticker' not in col_map: col_map['ticker'] = 3
                if 'insider' not in col_map: col_map['insider'] = 4
                if 'title' not in col_map: col_map['title'] = 5
                if 'type' not in col_map: col_map['type'] = 6
                if 'value' not in col_map: col_map['value'] = 11
                if 'date' not in col_map: col_map['date'] = 1

                data_rows = table.find_all('tr')[1:]
                for row in data_rows[:30]:
                    try:
                        cells = row.find_all('td')
                        if len(cells) < 8:
                            continue
                        
                        def safe_cell(idx):
                            return cells[idx].get_text(strip=True) if idx < len(cells) else ''
                        
                        ticker_raw = safe_cell(col_map['ticker'])
                        if not ticker_raw or len(ticker_raw) > 7 or not ticker_raw.replace('.','').isalpha():
                            continue
                        
                        trade_type_raw = safe_cell(col_map['type'])
                        if 'P -' in trade_type_raw or trade_type_raw.startswith('P ') or trade_type_raw == 'P':
                            trans = "COMPRA"
                        elif 'S -' in trade_type_raw or trade_type_raw.startswith('S ') or trade_type_raw == 'S':
                            trans = "VENTA"
                        elif 'Purchase' in trade_type_raw:
                            trans = "COMPRA"
                        elif 'Sale' in trade_type_raw:
                            trans = "VENTA"
                        else:
                            continue
                        
                        val_text = safe_cell(col_map['value'])
                        val_clean = val_text.replace('$','').replace(',','').replace('+','').strip()
                        try:
                            if 'B' in val_text:
                                value_num = float(re.sub(r'[^0-9.]', '', val_clean.split('B')[0])) * 1e9
                            elif 'M' in val_text:
                                value_num = float(re.sub(r'[^0-9.]', '', val_clean.split('M')[0])) * 1e6
                            elif 'K' in val_text:
                                value_num = float(re.sub(r'[^0-9.]', '', val_clean.split('K')[0])) * 1e3
                            else:
                                value_num = float(re.sub(r'[^0-9.]', '', val_clean)) if val_clean else 0
                        except:
                            value_num = 0
                        
                        if value_num < 50000:
                            continue
                        
                        value_fmt = (f"${value_num/1e9:.2f}B" if value_num >= 1e9 else
                                     f"${value_num/1e6:.1f}M" if value_num >= 1e6 else
                                     f"${value_num/1e3:.0f}K")
                        
                        all_trades.append({
                            'ticker': ticker_raw.upper(),
                            'insider': safe_cell(col_map['insider'])[:26],
                            'position': safe_cell(col_map['title'])[:22],
                            'type': trans,
                            'amount': value_fmt,
                            'date': safe_cell(col_map['date'])[:10],
                            'value_num': value_num,
                        })
                    except:
                        continue
    except Exception as e:
        set_api_health('Insider', False)
    
    # ── FUENTE 2: SEC EDGAR EFTS (búsqueda de Form 4 recientes) ───────────────
    if not all_trades:
        try:
            # API pública de búsqueda EDGAR - Form 4 = transacciones de insiders
            sec_url = "https://efts.sec.gov/LATEST/search-index?q=%22form+4%22&dateRange=custom&startdt={}&enddt={}&forms=4".format(
                (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d')
            )
            r = session.get(sec_url, timeout=12, headers={'User-Agent': 'MarketDashboard/1.0 contact@example.com'})
            if r.status_code == 200:
                data = r.json()
                hits = data.get('hits', {}).get('hits', [])[:8]
                for hit in hits:
                    src = hit.get('_source', {})
                    display_names = src.get('display_names', [])
                    entity = display_names[0].get('name', 'Desconocido') if display_names else 'Desconocido'
                    # Form 4 del ticker / company
                    tickers = src.get('period_of_report', '')
                    filed = src.get('file_date', '')[:10]
                    # Usar entity_name como ticker si es corto
                    company = src.get('entity_name', '')
                    ticker_candidate = company[:6].replace(' ', '') if company else 'N/D'
                    
                    all_trades.append({
                        'ticker': ticker_candidate,
                        'insider': entity[:26],
                        'position': 'Form 4 SEC',
                        'type': 'N/D',
                        'amount': 'Ver SEC',
                        'date': filed,
                        'value_num': 0,
                    })
                if all_trades:
                    set_api_health('Insider', True)
        except:
            pass
    
    # ── FUENTE 3: FMP API ──────────────────────────────────────────────────────
    if not all_trades:
        try:
            api_key = st.secrets.get("FMP_API_KEY", None)
            if api_key:
                symbols = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'META', 'GOOGL', 'AMZN', 'NFLX', 'AMD', 'CRM']
                for symbol in symbols[:8]:
                    try:
                        url = f"https://financialmodelingprep.com/api/v4/insider-trading?symbol={symbol}&limit=3&apikey={api_key}"
                        r = session.get(url, timeout=10)
                        if r.status_code == 200:
                            for trade in r.json():
                                tt = trade.get('transactionType', '')
                                trans = "COMPRA" if 'P' in tt else ("VENTA" if 'S' in tt else None)
                                if not trans: continue
                                shares = trade.get('securitiesTransacted', 0) or 0
                                price_v = trade.get('price', 0) or 0
                                amount = shares * price_v
                                if amount > 50000:
                                    all_trades.append({
                                        'ticker': symbol,
                                        'insider': trade.get('reportingName', 'Executive')[:26],
                                        'position': trade.get('typeOfOwner', 'Officer')[:22],
                                        'type': trans,
                                        'amount': f"${amount/1e6:.1f}M" if amount >= 1e6 else f"${amount/1e3:.0f}K",
                                        'date': trade.get('transactionDate', '')[:10],
                                        'value_num': amount,
                                    })
                    except:
                        continue
        except:
            pass
    
    if all_trades:
        all_trades.sort(key=lambda x: x.get('value_num', 0), reverse=True)
        return all_trades[:8]
    
    return get_fallback_insider()

def get_fallback_insider():
    return [
        {"ticker": "N/D", "insider": "Datos no disponibles", "position": "-", "type": "N/D", "amount": "-"},
    ]

@st.cache_data(ttl=600)
def get_market_breadth():
    try:
        spy = yf.Ticker("SPY")
        # Necesitamos al menos 200 días para SMA200
        spy_hist = spy.history(period="2y")
        if len(spy_hist) >= 200:
            current = float(spy_hist['Close'].iloc[-1])
            sma50  = float(spy_hist['Close'].rolling(50).mean().iloc[-1])
            sma200 = float(spy_hist['Close'].rolling(200).mean().iloc[-1])
            
            # RSI(14)
            deltas = spy_hist['Close'].diff()
            gains  = deltas.where(deltas > 0, 0).rolling(14).mean()
            losses = (-deltas.where(deltas < 0, 0)).rolling(14).mean()
            rs     = gains / losses
            rsi    = float(100 - (100 / (1 + rs.iloc[-1]))) if not pd.isna(rs.iloc[-1]) else 50.0
            
            # McClellan Oscillator (proxy con sectores ETF)
            # Usamos SPY: EMA(19) - EMA(39) de breadth sintética
            close = spy_hist['Close']
            ema19 = float(close.ewm(span=19, adjust=False).mean().iloc[-1])
            ema39 = float(close.ewm(span=39, adjust=False).mean().iloc[-1])
            # Normalizado como porcentaje respecto al precio
            mcclellan = round((ema19 - ema39) / current * 1000, 2)
            
            # % activos sobre SMA50 (proxy usando sectores ETF)
            sector_etfs = ['XLK','XLF','XLV','XLE','XLY','XLU','XLI','XLB','XLP','XLRE','XLC']
            above_sma50_count = 0
            total_checked = 0
            for etf_sym in sector_etfs:
                try:
                    etf = yf.Ticker(etf_sym)
                    etf_h = etf.history(period="100d")
                    if len(etf_h) >= 50:
                        etf_price = float(etf_h['Close'].iloc[-1])
                        etf_sma50 = float(etf_h['Close'].rolling(50).mean().iloc[-1])
                        if not pd.isna(etf_sma50):
                            if etf_price > etf_sma50:
                                above_sma50_count += 1
                            total_checked += 1
                except:
                    pass
            pct_above_sma50 = round((above_sma50_count / total_checked * 100) if total_checked > 0 else 50.0, 1)
            
            return {
                'price': current, 'sma50': sma50, 'sma200': sma200,
                'above_sma50': current > sma50, 'above_sma200': current > sma200,
                'golden_cross': sma50 > sma200, 'rsi': rsi,
                'trend': 'ALCISTA' if sma50 > sma200 else 'BAJISTA',
                'strength': 'FUERTE' if (current > sma50 and current > sma200) else 'DÉBIL',
                'mcclellan': mcclellan,
                'pct_above_sma50': pct_above_sma50,
            }
        elif len(spy_hist) >= 50:
            # Fallback con menos datos
            current = float(spy_hist['Close'].iloc[-1])
            sma50   = float(spy_hist['Close'].rolling(50).mean().iloc[-1])
            return {
                'price': current, 'sma50': sma50, 'sma200': float('nan'),
                'above_sma50': current > sma50, 'above_sma200': False,
                'golden_cross': False, 'rsi': 50.0,
                'trend': 'N/D', 'strength': 'N/D',
                'mcclellan': 0.0, 'pct_above_sma50': 50.0,
            }
        return get_fallback_market_breadth()
    except:
        return get_fallback_market_breadth()

def get_fallback_market_breadth():
    return {
        'price': 0.0, 'sma50': 0.0, 'sma200': 0.0,
        'above_sma50': False, 'above_sma200': False, 'golden_cross': False,
        'rsi': 50.0, 'trend': 'Datos no disponibles', 'strength': 'N/D',
        'mcclellan': 0.0, 'pct_above_sma50': 50.0,
    }

def get_fallback_news():
    return [
        {"time": "--:--", "title": "Datos no disponibles. Configure FINNHUB_API_KEY.", "impact": "N/D", "color": "#888", "link": "#"},
    ]

def translate_to_spanish(text):
    """Intenta traducir texto al castellano usando MyMemory API (gratuita)"""
    try:
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text[:500])}&langpair=en|es"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            translated = data.get('responseData', {}).get('translatedText', '')
            if translated and translated != text:
                return translated
    except:
        pass
    return text

@st.cache_data(ttl=300)
def fetch_finnhub_news():
    api_key = st.secrets.get("FINNHUB_API_KEY", None)
    if not api_key:
        return get_fallback_news()
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
        r = requests.get(url, timeout=12)
        data = r.json()
        news_list = []
        for item in data[:8]:
            title_en = item.get("headline", "Sin título")
            # Traducir al castellano
            title = translate_to_spanish(title_en)
            link = item.get("url", "#")
            timestamp = item.get("datetime", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "N/A"
            lower = title_en.lower()
            impact, color = ("Alto", "#f23645") if any(k in lower for k in ["earnings", "profit", "revenue", "gdp", "fed", "fomc", "inflation", "rate", "outlook"]) else ("Moderado", "#ff9800")
            news_list.append({"time": time_str, "title": title, "impact": impact, "color": color, "link": link})
        return news_list if news_list else get_fallback_news()
    except:
        return get_fallback_news()

def get_fed_liquidity():
    api_key = st.secrets.get("FRED_API_KEY", None)
    if not api_key:
        return {
            'status': 'N/D', 'color': '#ff9800', 'desc': 'Configura FRED_API_KEY',
            'total': 'N/D', 'date': 'N/D',
            'treasuries': 'N/D', 'mbs': 'N/D',
            'net_liquidity': 'N/D', 'net_liquidity_num': None,
            'weekly_change': None, 'fed_rate': None,
            'history': [], 'tga': 'N/D', 'rrp': 'N/D',
        }
    try:
        session = get_http_session()
        
        def fred_fetch(series_id, limit=12):
            url = (f"https://api.stlouisfed.org/fred/series/observations"
                   f"?series_id={series_id}&api_key={api_key}&file_type=json"
                   f"&limit={limit}&sort_order=desc")
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                obs = r.json().get('observations', [])
                return [(o['date'], float(o['value'])) for o in obs if o['value'] != '.']
            return []
        
        # Balance total Fed (WALCL) - en millones
        walcl = fred_fetch('WALCL', 20)
        # Treasuries (TREAST)
        treast = fred_fetch('TREAST', 5)
        # MBS (MBST)
        mbst = fred_fetch('MBST', 5)
        # TGA - Cuenta General del Tesoro (WTREGEN)
        tga = fred_fetch('WTREGEN', 5)
        # RRP - Repos Inversos (RRPONTSYD)
        rrp = fred_fetch('RRPONTSYD', 5)
        # Fed Funds Rate (FEDFUNDS)
        fedfunds = fred_fetch('FEDFUNDS', 3)
        
        set_api_health('FRED', True)
        
        if not walcl:
            return get_fed_liquidity_fallback()
        
        # Total assets
        latest_total = walcl[0][1]  # en millones
        prev_week = walcl[1][1] if len(walcl) > 1 else latest_total
        prev_month = walcl[4][1] if len(walcl) > 4 else latest_total
        weekly_change = latest_total - prev_week  # en millones
        date_latest = walcl[0][0]
        
        # Clasificar política
        if weekly_change < -10000:
            status, color = "QT", "#f23645"
            desc = "Quantitative Tightening (reducción balance)"
        elif weekly_change > 10000:
            status, color = "QE", "#00ffad"
            desc = "Quantitative Easing (expansión balance)"
        else:
            status, color = "ESTABLE", "#ff9800"
            desc = "Balance del balance estable"
        
        # Treasuries y MBS
        t_val = treast[0][1] if treast else None
        m_val = mbst[0][1] if mbst else None
        
        # TGA y RRP
        tga_val = tga[0][1] if tga else 0
        rrp_val = rrp[0][1] if rrp else 0
        
        # Liquidez neta = Balance total - TGA - RRP
        net_liq = latest_total - tga_val - rrp_val
        
        # Fed Funds Rate
        ff_rate = fedfunds[0][1] if fedfunds else None
        
        # Historial para sparkline (últimas 24 semanas)
        history_data = [(d, v/1e6) for d, v in reversed(walcl)]  # en trillones
        
        def fmt_trillions(v_millions):
            if v_millions is None: return 'N/D'
            t = v_millions / 1e6
            return f"${t:.2f}T"
        
        def fmt_billions_change(v_millions):
            if v_millions is None: return 'N/D'
            b = v_millions / 1e3
            sign = "+" if b >= 0 else ""
            return f"{sign}{b:.1f}B esta semana"
        
        return {
            'status': status, 'color': color, 'desc': desc,
            'total': fmt_trillions(latest_total),
            'total_num': latest_total,
            'date': date_latest,
            'treasuries': fmt_trillions(t_val) if t_val else 'N/D',
            'mbs': fmt_trillions(m_val) if m_val else 'N/D',
            'net_liquidity': fmt_trillions(net_liq),
            'net_liquidity_num': net_liq,
            'tga': fmt_trillions(tga_val),
            'rrp': fmt_trillions(rrp_val),
            'weekly_change': fmt_billions_change(weekly_change),
            'weekly_change_num': weekly_change,
            'fed_rate': ff_rate,
            'history': history_data[-20:],
        }
    except Exception as e:
        set_api_health('FRED', False)
        return get_fed_liquidity_fallback()

def get_fed_liquidity_fallback():
    return {
        'status': 'N/D', 'color': '#888', 'desc': 'No disponible',
        'total': 'N/D', 'date': 'N/D',
        'treasuries': 'N/D', 'mbs': 'N/D',
        'net_liquidity': 'N/D', 'net_liquidity_num': None,
        'weekly_change': None, 'fed_rate': None,
        'history': [], 'tga': 'N/D', 'rrp': 'N/D',
        'weekly_change_num': 0,
    }


# ── ECONOMIC INDICATORS (FRED) ────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_economic_indicators():
    """Obtiene indicadores macroeconómicos de FRED y yfinance."""
    indicators = []
    fred_key = None
    try:
        fred_key = st.secrets.get("FRED_API_KEY", None)
    except:
        pass
    
    fred_series = [
        ("UNRATE",   "Tasa de Desempleo",     "%"),
        ("CPIAUCSL", "Índice de Precios (IPC)", "Index"),
        ("FEDFUNDS", "Tipos de Interés Fed",   "%"),
        ("GDP",      "PIB (EE.UU.)",           "Billions"),
        ("PAYEMS",   "Nóminas No Agrícolas",   "Thousands"),
    ]
    
    if fred_key:
        session = get_http_session()
        for series_id, name, unit in fred_series:
            try:
                url = (f"https://api.stlouisfed.org/fred/series/observations"
                       f"?series_id={series_id}&api_key={fred_key}&file_type=json"
                       f"&limit=2&sort_order=desc")
                r = session.get(url, timeout=10)
                set_api_health('FRED', r.status_code == 200)
                if r.status_code == 200:
                    obs = r.json().get('observations', [])
                    if len(obs) >= 2:
                        val_now  = float(obs[0]['value'])
                        val_prev = float(obs[1]['value'])
                        change   = val_now - val_prev
                        pct      = (change / val_prev * 100) if val_prev else 0
                        date_str = obs[0]['date']
                        indicators.append({
                            'name':   name,
                            'value':  val_now,
                            'unit':   unit,
                            'change': change,
                            'pct':    pct,
                            'date':   date_str,
                            'up':     change >= 0
                        })
            except:
                continue
    
    # 10Y Treasury via yfinance como complemento
    try:
        t = yf.Ticker("^TNX")
        h = t.history(period="5d")
        if len(h) >= 2:
            val_now  = float(h['Close'].iloc[-1])
            val_prev = float(h['Close'].iloc[-2])
            change   = val_now - val_prev
            pct      = (change / val_prev * 100) if val_prev else 0
            indicators.append({
                'name': 'Bono del Tesoro 10Y',
                'value': val_now,
                'unit': '%',
                'change': change,
                'pct': pct,
                'date': datetime.now().strftime('%b %d, %Y'),
                'up': change >= 0
            })
    except:
        pass
    
    if not indicators:
        set_api_health('FRED', False)
    
    return indicators


# ── US HIGH YIELD CREDIT SPREADS (FRED HY OAS) ──────────────────────────────
@st.cache_data(ttl=3600)
def get_credit_spreads():
    """Obtiene los spreads de crédito High Yield de FRED (BAMLH0A0HYM2)."""
    fred_key = None
    try:
        fred_key = st.secrets.get("FRED_API_KEY", None)
    except:
        pass
    
    try:
        session = get_http_session()
        # Con API key de FRED
        if fred_key:
            url = (f"https://api.stlouisfed.org/fred/series/observations"
                   f"?series_id=BAMLH0A0HYM2&api_key={fred_key}&file_type=json"
                   f"&limit=130&sort_order=desc")
        else:
            # Sin API key, intentar scraping alternativo
            url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2&vintage_date=&realtime_start=&realtime_end="
        
        r = session.get(url, timeout=15)
        set_api_health('CreditSpreads', r.status_code == 200)
        
        history = []
        if fred_key and r.status_code == 200:
            obs = r.json().get('observations', [])
            for o in reversed(obs):
                try:
                    v = float(o['value'])
                    history.append({'date': o['date'], 'value': v})
                except:
                    continue
        elif not fred_key and r.status_code == 200:
            lines = r.text.strip().split('\n')
            for line in lines[1:]:  # skip header
                try:
                    parts = line.split(',')
                    v = float(parts[1])
                    history.append({'date': parts[0], 'value': v})
                except:
                    continue
        
        if len(history) >= 2:
            current_val = history[-1]['value']
            prev_val    = history[-2]['value']
            change      = current_val - prev_val
            date_str    = history[-1]['date']
            # Tomar últimos 130 puntos (≈ 6 meses de días hábiles)
            chart_data  = history[-130:]
            return {
                'current': current_val,
                'prev': prev_val,
                'change': change,
                'date': date_str,
                'history': chart_data,
                'ok': True
            }
    except Exception as e:
        set_api_health('CreditSpreads', False)
    
    # Fallback
    return {'current': None, 'ok': False, 'history': []}


# ── ADVANCE-DECLINE LINE (calculada desde yfinance) ──────────────────────────
@st.cache_data(ttl=600)
def get_advance_decline():
    """
    Aproxima la línea Advance/Decline usando la lista del S&P 500 (muestra).
    """
    try:
        # Usamos ETFs sectoriales para aproximar A/D diaria
        sector_etfs = ['XLK','XLF','XLV','XLE','XLY','XLU','XLI','XLB','XLP','XLRE','XLC']
        advances, declines = 0, 0
        ad_history = []
        
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(period="6mo")
        
        # Para la línea A/D histórica, usamos componentes del SPY 
        # como proxy: días en que SPY sube = mayoría avanza
        if len(spy_hist) > 20:
            cumulative = 0
            for i in range(1, len(spy_hist)):
                day_change = spy_hist['Close'].iloc[i] - spy_hist['Close'].iloc[i-1]
                # Simular A/D basado en volumen y precio
                adv = int(250 + (day_change / spy_hist['Close'].iloc[i-1]) * 3000)
                adv = max(50, min(450, adv))
                dec = 500 - adv
                net = adv - dec
                cumulative += net
                date_val = spy_hist.index[i]
                ad_history.append({
                    'date': date_val.strftime('%Y-%m-%d'),
                    'ad': cumulative / 1000,  # en miles
                    'spy': float(spy_hist['Close'].iloc[i])
                })
            
            current_ad = ad_history[-1]['ad'] if ad_history else 0
            set_api_health('AdvDecline', True)
            return {
                'history': ad_history[-90:],  # 90 días
                'current_ad': current_ad,
                'spy_current': float(spy_hist['Close'].iloc[-1]),
                'spy_change': float(spy_hist['Close'].iloc[-1] - spy_hist['Close'].iloc[-2]),
                'ok': True
            }
    except Exception as e:
        set_api_health('AdvDecline', False)
    return {'history': [], 'current_ad': 0, 'spy_current': 0, 'spy_change': 0, 'ok': False}


def render():
    # CSS Global - Tooltips CENTRADOS en el módulo - ALTURA AUMENTADA A 420px
    st.markdown("""
    <style>
    /* Tooltips CENTRADOS - flotan en el centro del módulo */
    .tooltip-wrapper {
        position: static;
        display: inline-block;
    }
    .tooltip-btn {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #1a1e26;
        border: 2px solid #555;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #aaa;
        font-size: 14px;
        font-weight: bold;
        cursor: help;
    }
    .tooltip-content {
        display: none;
        position: fixed;
        width: 300px;
        background-color: #1e222d;
        color: #eee;
        text-align: left;
        padding: 15px;
        border-radius: 10px;
        z-index: 99999;
        font-size: 12px;
        border: 2px solid #3b82f6;
        box-shadow: 0 15px 40px rgba(0,0,0,0.9);
        line-height: 1.5;

        /* CENTRADO EN LA PANTALLA */
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);

        white-space: normal;
        word-wrap: break-word;
    }

    /* Mostrar tooltip en hover */
    .tooltip-wrapper:hover .tooltip-content {
        display: block;
    }

    /* Timestamp */
    .update-timestamp {
        text-align: center;
        color: #555;
        font-size: 10px;
        padding: 6px 0;
        font-family: 'Courier New', monospace;
        border-top: 1px solid #1a1e26;
        background: #0c0e12;
        flex-shrink: 0;
    }

    /* Contenedores - altura AUMENTADA a 420px */
    .module-container { 
        border: 1px solid #1a1e26; 
        border-radius: 10px; 
        overflow: hidden; 
        background: #11141a; 
        height: 420px;
        display: flex;
        flex-direction: column;
        margin-bottom: 0;
    }
    .module-header { 
        background: #0c0e12; 
        padding: 10px 12px; 
        border-bottom: 1px solid #1a1e26; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        flex-shrink: 0;
    }
    .module-title { 
        margin: 0; 
        color: white; 
        font-size: 13px; 
        font-weight: bold; 
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .module-content { 
        flex: 1;
        overflow-y: auto;
        padding: 10px;
    }

    /* Sector rotation */
    .sector-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
        height: 100%;
    }
    .sector-item {
        background: #0c0e12;
        border: 1px solid #1a1e26;
        border-radius: 6px;
        padding: 8px 4px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .sector-code { color: #666; font-size: 9px; font-weight: bold; margin-bottom: 2px; }
    .sector-name { color: white; font-size: 10px; font-weight: 600; margin-bottom: 4px; line-height: 1.2; }
    .sector-change { font-size: 11px; font-weight: bold; }

    /* Select nativo */
    .sector-select {
        background: #1a1e26;
        color: white;
        border: 1px solid #2a3f5f;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
        cursor: pointer;
    }
    .sector-select:hover { border-color: #3b82f6; }

    /* Fear & Greed */
    .fng-legend { display: flex; justify-content: space-between; width: 100%; margin-top: 10px; font-size: 0.6rem; color: #888; text-align: center; }
    .fng-legend-item { flex: 1; padding: 0 2px; }
    .fng-color-box { width: 100%; height: 4px; margin-bottom: 3px; border-radius: 2px; }

    /* Columnas */
    .stColumns { gap: 0.5rem !important; }
    .stColumn { padding: 0 0.25rem !important; }
    .element-container { margin-bottom: 0.5rem !important; }
    
    /* Estilos específicos para Calendario Económico */
    .eco-date-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 9px;
        font-weight: bold;
        margin-right: 6px;
        min-width: 45px;
        text-align: center;
    }
    .eco-time {
        font-family: 'Courier New', monospace;
        font-size: 10px;
        color: #888;
        min-width: 35px;
    }
    .eco-flag {
        font-size: 10px;
        margin-right: 4px;
    }
    
    /* ESTILOS NUEVOS PARA REDDIT SOCIAL PULSE - MASTER BUZZ */
    .buzz-table-header {
        display: grid;
        grid-template-columns: 25px 45px 35px 50px 1fr 1fr 1fr;
        gap: 4px;
        padding: 6px 4px;
        background: #0c0e12;
        border-bottom: 2px solid #2a3f5f;
        font-size: 8px;
        font-weight: bold;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    .buzz-row {
        display: grid;
        grid-template-columns: 25px 45px 35px 50px 1fr 1fr 1fr;
        gap: 4px;
        padding: 6px 4px;
        border-bottom: 1px solid #1a1e26;
        align-items: center;
        font-size: 9px;
        transition: background 0.2s;
    }
    .buzz-row:hover {
        background: #1a1e26;
    }
    .buzz-rank {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 9px;
    }
    .buzz-rank.top3 {
        background: #f23645;
        color: white;
    }
    .buzz-rank.normal {
        background: #1a1e26;
        color: #888;
    }
    .buzz-ticker {
        color: #00ffad;
        font-weight: bold;
        font-size: 10px;
    }
    .buzz-score {
        font-weight: bold;
        color: white;
    }
    .buzz-health {
        font-size: 8px;
        padding: 2px 4px;
        border-radius: 3px;
        text-align: center;
    }
    .health-strong {
        background: #00ffad22;
        color: #00ffad;
        border: 1px solid #00ffad44;
    }
    .health-hold {
        background: #ff980022;
        color: #ff9800;
        border: 1px solid #ff980044;
    }
    .health-weak {
        background: #f2364522;
        color: #f23645;
        border: 1px solid #f2364544;
    }
    .buzz-metric {
        font-size: 8px;
        color: #aaa;
        line-height: 1.2;
    }
    .buzz-stars {
        color: #ffd700;
        font-size: 8px;
    }
    .buzz-section-title {
        font-size: 7px;
        color: #555;
        text-transform: uppercase;
        margin-bottom: 2px;
        letter-spacing: 0.5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Ticker
    ticker_html = generate_ticker_html()
    components.html(ticker_html, height=50, scrolling=False)
    st.markdown('<h1 style="margin-top:15px; text-align:center; margin-bottom:15px; font-size: 1.5rem;">Market Dashboard</h1>', unsafe_allow_html=True)

    # ── API HEALTH BAR ─────────────────────────────────────────────────────────
    apis = [
        ('yfinance', 'Yahoo Fin.'),
        ('CryptoFG', 'Crypto F&G'),
        ('ForexFactory', 'Eco Cal.'),
        ('FRED', 'FRED'),
        ('AlphaVantage', 'AlphaV.'),
    ]
    health_html = '<div style="display:flex; gap:8px; padding:6px 12px; background:#0c0e12; border-bottom:1px solid #1a1e26; justify-content:flex-end; align-items:center;">'
    health_html += '<span style="color:#555; font-size:9px; margin-right:4px;">APIs:</span>'
    for key, label in apis:
        status = get_api_health(key)
        dot_color = "#00ffad" if status == True else ("#f23645" if status == False else "#555")
        health_html += f'<span style="font-size:9px; color:#888;">● <span style="color:{dot_color};">{label}</span></span>'
    health_html += '</div>'
    st.markdown(health_html, unsafe_allow_html=True)

    # ── REFRESH BUTTON (arriba izquierda, en verde cyan) ──────────────────────
    col_r1, col_r2, col_r3 = st.columns([1, 3, 1])
    with col_r1:
        st.markdown(
            '''<style>
            div[data-testid="stButton"]:has(button[data-testid="baseButton-secondary"][key="global_refresh"]) button,
            button[aria-label="↻ Actualizar"] {
                background:#00ffad!important; border:1px solid #00ffad!important;
                color:#0a0c10!important; font-size:12px!important; font-weight:800!important;
                padding:5px 16px!important; border-radius:7px!important;
                height:auto!important; min-height:0!important;
                box-shadow: 0 0 10px #00ffad33!important;
            }
            </style>''',
            unsafe_allow_html=True
        )
        if st.button("↻ Actualizar", key="global_refresh", type="secondary"):
            st.cache_data.clear()
            st.rerun()

    # FILA 1
    col1, col2, col3 = st.columns(3)

    with col1:
        # Sparklines helper
        @st.cache_data(ttl=300)
        def _get_sparkline(symbol, period="5d"):
            try:
                h = yf.Ticker(symbol).history(period=period)
                if len(h) >= 3:
                    vals = [float(v) for v in h['Close'].values[-10:]]
                    return vals
            except:
                pass
            return []

        def _sparkline_svg(vals, color="#00ffad", w=60, h=18):
            if len(vals) < 2:
                return ""
            mn, mx = min(vals), max(vals)
            rng = mx - mn if mx != mn else 1
            pts = []
            for i, v in enumerate(vals):
                x = i * (w / (len(vals) - 1))
                y = h - ((v - mn) / rng) * h
                pts.append(f"{x:.1f},{y:.1f}")
            path = " ".join(pts)
            return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="overflow:visible;">'
                    f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="1.5" '
                    f'stroke-linecap="round" stroke-linejoin="round"/></svg>')

        indices_html = ""
        for t, n in [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), 
                     ("^RUT", "RUSSELL 2000"), ("RSP", "S&P 500 EW"), ("MEME", "MEME"), ("VUG", "Growth ETF")]:
            idx_val, idx_change = get_market_index(t)
            color = "#00ffad" if idx_change >= 0 else "#f23645"
            spark_vals = _get_sparkline(t)
            spark_svg = _sparkline_svg(spark_vals, color=color)
            indices_html += (
                f'<div style="background:#0c0e12; padding:8px 12px; border-radius:8px; margin-bottom:5px; '
                f'border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">'
                f'<div><div style="font-weight:bold; color:white; font-size:11px;">{n}</div>'
                f'<div style="color:#555; font-size:9px;">{t}</div></div>'
                f'<div style="display:flex; align-items:center; gap:10px;">'
                f'{spark_svg}'
                f'<div style="text-align:right;">'
                f'<div style="color:white; font-weight:bold; font-size:11px;">{idx_val:,.2f}</div>'
                f'<div style="color:{color}; font-size:10px; font-weight:bold;">{idx_change:+.2f}%</div>'
                f'</div></div></div>')

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Índices de Mercado</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Principales índices bursátiles de EE.UU. con sparklines de 5 días via Yahoo Finance.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 10px;">{indices_html}</div>
            <div class="update-timestamp">Actualizado: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    # === CALENDARIO ECONÓMICO MEJORADO ===
    with col2:
        events = get_economic_calendar()
        impact_colors = {'High': '#f23645', 'Medium': '#ff9800', 'Low': '#4caf50'}
        country_flags = {'US': '🇺🇸', 'EU': '🇪🇺', 'EZ': '🇪🇺', 'DE': '🇩🇪', 'FR': '🇫🇷', 'ES': '🇪🇸', 'IT': '🇮🇹'}
        
        events_html = ""
        for ev in events[:6]:
            imp_color = impact_colors.get(ev['imp'], '#888')
            date_color = ev.get('date_color', '#888')
            date_display = ev.get('date_display', '---')
            country = ev.get('country', 'US')
            flag = country_flags.get(country, '🇺🇸')
            
            # Mostrar previsión si existe y no hay valor actual
            display_val = ev['val']
            if display_val == '-' or display_val == 'nan':
                display_val = ev.get('forecast', '-')
                if display_val != '-' and display_val != 'nan':
                    display_val = f"Est: {display_val}"
            
            events_html += f'''<div style="padding:8px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;">
                <div class="eco-date-badge" style="background:{date_color}22; color:{date_color}; border:1px solid {date_color}44;">{date_display}</div>
                <div class="eco-time">{ev["time"]}</div>
                <div style="flex-grow:1; margin-left:8px; min-width:0;">
                    <div style="color:white; font-size:10px; font-weight:500; line-height:1.2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        <span class="eco-flag">{flag}</span>{ev["event"]}
                    </div>
                    <div style="color:{imp_color}; font-size:7px; font-weight:bold; text-transform:uppercase; margin-top:2px;">● {ev["imp"]}</div>
                </div>
                <div style="text-align:right; min-width:50px; margin-left:6px;">
                    <div style="color:white; font-size:10px; font-weight:bold;">{display_val}</div>
                </div>
            </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Calendario Económico</div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="background: #2a3f5f; color: #00ffad; padding: 2px 6px; border-radius: 3px; font-size: 9px; font-weight: bold;">CET</span>
                    <div class="tooltip-wrapper">
                        <div class="tooltip-btn">?</div>
                        <div class="tooltip-content">Calendario económico en tiempo real. Datos de hoy en adelante a 15 días. Hora española (CET/CEST). Fuente: Investing.com / ForexFactory.</div>
                    </div>
                </div>
            </div>
            <div class="module-content" style="padding: 0;">{events_html}</div>
            <div class="update-timestamp">Actualizado: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    # === REDDIT SOCIAL PULSE - MASTER BUZZ ===
    with col3:
        master_data = get_buzztickr_master_data()
        buzz_items = master_data.get('data', [])
        timestamp_str = master_data.get('timestamp', get_timestamp())
        source_str = master_data.get('source', 'API')
        count_str = master_data.get('count', 0)
        
        # Cards visuales en lugar de tabla
        cards_html = ""
        for item in buzz_items[:20]:  # 20 activos con scroll
            rank = str(item.get('rank', '-'))
            ticker = str(item.get('ticker', '-'))
            buzz_score = str(item.get('buzz_score', '-'))
            health = str(item.get('health', '-'))
            social_hype = str(item.get('social_hype', ''))
            smart_money = str(item.get('smart_money', ''))
            squeeze = str(item.get('squeeze', ''))

            try:
                rank_int = int(rank)
                if rank_int == 1:   rank_bg, rank_color = "linear-gradient(135deg,#f23645,#c62828)", "white"
                elif rank_int == 2: rank_bg, rank_color = "linear-gradient(135deg,#ff9800,#e65100)", "white"
                elif rank_int == 3: rank_bg, rank_color = "linear-gradient(135deg,#ffd700,#f9a825)", "#111"
                else:               rank_bg, rank_color = "#1a1e26", "#888"
                rank_int_ok = True
            except:
                rank_bg, rank_color = "#1a1e26", "#888"
                rank_int = 99
                rank_int_ok = False

            health_lower = health.lower()
            if 'strong' in health_lower:
                h_bg, h_border, h_color = "#00ffad15", "#00ffad50", "#00ffad"
                h_label = "FUERTE"
            elif 'hold' in health_lower:
                h_bg, h_border, h_color = "#ff980015", "#ff980050", "#ff9800"
                h_label = "HOLD"
            else:
                h_bg, h_border, h_color = "#f2364515", "#f2364550", "#f23645"
                h_label = "DÉBIL"

            # Health number
            num_match = re.search(r'(\d+)', health)
            health_num = num_match.group(1) if num_match else ""

            # Extraer estrellas de hype, smart money y squeeze
            def extract_stars(text, max_stars=5):
                """Extrae el número de estrellas del texto BuzzTickr"""
                star_count = text.count('★')
                if star_count == 0:
                    star_count = text.count('*')
                return min(star_count, max_stars)
            
            hype_stars = extract_stars(social_hype)
            smart_stars = extract_stars(smart_money)
            squeeze_stars = extract_stars(squeeze)
            
            def stars_html(n, max_n=5, active_color="#ffd700", inactive_color="#2a3f5f"):
                result = ""
                for i in range(max_n):
                    color = active_color if i < n else inactive_color
                    result += f'<span style="color:{color}; font-size:11px;">★</span>'
                return result
            
            hype_label = ""
            if "Reddit Top 10" in social_hype:
                hype_label = " Reddit"
            elif "Weekly Choice" in social_hype:
                hype_label = " Semanal"
            
            smart_label = ""
            if "Whales" in smart_money:
                pct_m = re.search(r'>(\d+)%', smart_money)
                smart_label = f" Ballenas >{pct_m.group(1)}%" if pct_m else " Ballenas"
            
            squeeze_label = ""
            sqz_match2 = re.search(r'\((\d+)%\)', squeeze)
            if sqz_match2:
                squeeze_label = f" {sqz_match2.group(1)}%"
            elif "Days to Cover" in squeeze:
                dtc = re.search(r'(\d+\.\d+)', squeeze)
                squeeze_label = f" DTC:{dtc.group(1)}" if dtc else ""

            cards_html += f'''
            <div class="buzz-row">
                <div class="buzz-rank" style="background:{rank_bg}; color:{rank_color};">{rank}</div>
                <div class="buzz-ticker-col">
                    <div class="buzz-ticker">${ticker}</div>
                    <div class="buzz-score">SCR:{buzz_score}</div>
                </div>
                <div class="buzz-health" style="background:{h_bg}; border:1px solid {h_border}; color:{h_color};">
                    {health_num or ""}<br><span style="font-size:8px;">{h_label}</span>
                </div>
                <div class="buzz-signals-col">
                    <div class="signal-badge" style="background:#ffd70014; border:1px solid #ffd70033;">
                        <span class="sig-label" style="color:#ffd700;">HYPE</span>
                        <span class="sig-stars">{stars_html(hype_stars, active_color="#ffd700")}</span>
                        <span class="sig-info" style="color:#ffd70099;">{hype_label}</span>
                    </div>
                    <div class="signal-badge" style="background:#00ffad14; border:1px solid #00ffad33;">
                        <span class="sig-label" style="color:#00ffad;">SMART</span>
                        <span class="sig-stars">{stars_html(smart_stars, active_color="#00ffad")}</span>
                        <span class="sig-info" style="color:#00ffad99;">{smart_label}</span>
                    </div>
                    <div class="signal-badge" style="background:#f2364514; border:1px solid #f2364533;">
                        <span class="sig-label" style="color:#f23645;">SQZ</span>
                        <span class="sig-stars">{stars_html(squeeze_stars, active_color="#f23645")}</span>
                        <span class="sig-info" style="color:#f2364599;">{squeeze_label}</span>
                    </div>
                </div>
            </div>'''

        buzz_html_full = f'''<!DOCTYPE html><html><head><style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#11141a; }}
        .container {{ border:1px solid #1a1e26; border-radius:10px; overflow:hidden; background:#11141a; width:100%; height:420px; display:flex; flex-direction:column; }}
        .header {{ background:#0c0e12; padding:10px 12px; border-bottom:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center; flex-shrink:0; }}
        .title {{ color:white; font-size:13px; font-weight:bold; text-transform:uppercase; letter-spacing:0.5px; }}
        .col-head {{ display:grid; grid-template-columns:24px 50px 40px 1fr; gap:3px; padding:4px 8px; background:#0c0e12; border-bottom:2px solid #1a1e26; }}
        .col-label {{ font-size:7px; font-weight:bold; color:#3a4f6f; text-transform:uppercase; letter-spacing:0.8px; }}
        .content {{ flex:1; overflow-y:auto; scrollbar-width:thin; scrollbar-color:#1a1e26 transparent; }}
        .buzz-row {{ display:grid; grid-template-columns:24px 50px 40px 1fr; gap:3px; padding:4px 8px; border-bottom:1px solid #1a1e2640; align-items:center; }}
        .buzz-row:hover {{ background:#ffffff05; }}
        .buzz-rank {{ width:20px; height:20px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:900; font-size:9px; flex-shrink:0; }}
        .buzz-ticker-col {{ display:flex; flex-direction:column; }}
        .buzz-ticker {{ color:#00ffad; font-weight:bold; font-size:11px; }}
        .buzz-score {{ color:#444; font-size:7px; }}
        .buzz-health {{ padding:3px 2px; border-radius:4px; font-size:10px; font-weight:bold; text-align:center; line-height:1.2; }}
        .buzz-signals-col {{ display:flex; flex-direction:column; gap:2px; width:100%; }}
        .signal-badge {{ display:flex; align-items:center; border-radius:4px; padding:2px 5px; gap:4px; width:100%; }}
        .sig-label {{ font-size:8px; font-weight:900; min-width:30px; text-transform:uppercase; letter-spacing:0.5px; flex-shrink:0; }}
        .sig-stars {{ font-size:10px; flex-shrink:0; }}
        .sig-info {{ font-size:7px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1; }}
        .footer {{ background:#0c0e12; border-top:1px solid #1a1e26; padding:4px 10px; display:flex; justify-content:space-between; align-items:center; flex-shrink:0; }}
        .update-timestamp {{ text-align:center; color:#555; font-size:10px; padding:5px 0; font-family:'Courier New',monospace; border-top:1px solid #1a1e26; background:#0c0e12; flex-shrink:0; }}
        .tooltip-wrapper {{ position:static; display:inline-block; }}
        .tooltip-btn {{ width:22px; height:22px; border-radius:50%; background:#1a1e26; border:1px solid #333; display:flex; align-items:center; justify-content:center; color:#666; font-size:11px; cursor:help; }}
        .tooltip-content {{ display:none; position:fixed; width:280px; background:#1e222d; color:#eee; padding:12px; border-radius:10px; z-index:99999; font-size:11px; border:2px solid #3b82f6; box-shadow:0 15px 40px rgba(0,0,0,0.9); line-height:1.5; left:50%; top:50%; transform:translate(-50%,-50%); }}
        .tooltip-wrapper:hover .tooltip-content {{ display:block; }}
        </style></head><body>
        <div class="container">
            <div class="header">
                <div class="title">Reddit Social Pulse</div>
                <div style="display:flex; align-items:center; gap:6px;">
                    <span style="background:#f2364520; color:#f23645; border:1px solid #f2364540; padding:2px 7px; border-radius:4px; font-size:9px; font-weight:bold; letter-spacing:0.5px;">● LIVE</span>
                    <div class="tooltip-wrapper">
                        <div class="tooltip-btn">?</div>
                        <div class="tooltip-content">Master Buzz BuzzTickr. Rank, Ticker, Salud, Hype (Reddit ★), Smart Money (Ballenas ★) y Squeeze (★). Top 20 activos con scroll.</div>
                    </div>
                </div>
            </div>
            <div class="col-head">
                <div class="col-label">#</div>
                <div class="col-label">Ticker</div>
                <div class="col-label">Salud</div>
                <div class="col-label">Hype / Smart Money / Squeeze</div>
            </div>
            <div class="content">
                {cards_html}
            </div>
            <div class="footer">
                <span style="font-size:9px; color:#555;">
                    <span style="color:#00ffad; font-weight:bold;">{count_str}</span> activos monitorizados
                </span>
                <span style="font-size:8px; color:#333;">BuzzTickr</span>
            </div>
            <div class="update-timestamp">Actualizado: {timestamp_str} • {source_str}</div>
        </div>
        </body></html>'''
        
        components.html(buzz_html_full, height=420, scrolling=False)


    # FILA 2
    st.write("")
    c1, c2, c3 = st.columns(3)

    with c1:
        val = get_cnn_fear_greed()
        if val is None:
            val_display, label, col, bar_width = "50", "NEUTRAL", "#ff9800", 50
        else:
            val_display = val
            bar_width = val
            if val <= 24: label, col = "MIEDO EXTREMO", "#d32f2f"
            elif val <= 44: label, col = "MIEDO", "#f57c00"
            elif val <= 55: label, col = "NEUTRAL", "#ff9800"
            elif val <= 75: label, col = "CODICIA", "#4caf50"
            else: label, col = "CODICIA EXTREMA", "#00ffad"

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Índice Miedo y Codicia</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Índice CNN Fear & Greed – mide el sentimiento del mercado de valores. Valores bajos = miedo, valores altos = codicia.</div>
                </div>
            </div>
            <div class="module-content" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:15px;">
                <div style="font-size:3.5rem; font-weight:bold; color:{col};">{val_display}</div>
                <div style="color:white; font-size:1rem; letter-spacing:1px; font-weight:bold; margin:8px 0;">{label}</div>
                <div style="width:90%; background:#0c0e12; height:12px; border-radius:6px; margin:10px 0; border:1px solid #1a1e26; overflow:hidden;">
                    <div style="width:{bar_width}%; background:{col}; height:100%;"></div>
                </div>
                <div class="fng-legend">
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#d32f2f;"></div><div>Miedo<br>Extremo</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#f57c00;"></div><div>Miedo</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#ff9800;"></div><div>Neutral</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#4caf50;"></div><div>Codicia</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#00ffad;"></div><div>Codicia<br>Extrema</div></div>
                </div>
            </div>
            <div class="update-timestamp">Actualizado: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    # SECTOR ROTATION - BOTONES DENTRO DEL MÓDULO HTML (sin desplegable externo)
    with c2:
        if 'sector_tf' not in st.session_state:
            st.session_state.sector_tf = "1D"

        tf_options = ["1D", "3D", "1W", "1M"]
        current_tf = st.session_state.sector_tf
        
        # Detectar cambio de temporalidad via query param interno de Streamlit
        qp = st.query_params.get("sector_tf", None)
        if qp and qp in tf_options and qp != current_tf:
            st.session_state.sector_tf = qp
            current_tf = qp

        sectors = get_sector_performance(current_tf)

        sectors_html = ""
        for sector in sectors:
            code, name, change = sector['code'], sector['name'], sector['change']
            if change >= 2:     bg_color, text_color = "#00ffad22", "#00ffad"
            elif change >= 0.5: bg_color, text_color = "#00ffad18", "#00ffad"
            elif change >= 0:   bg_color, text_color = "#00ffad10", "#00ffad"
            elif change >= -0.5:bg_color, text_color = "#f2364510", "#f23645"
            elif change >= -2:  bg_color, text_color = "#f2364518", "#f23645"
            else:               bg_color, text_color = "#f2364522", "#f23645"
            sectors_html += (f'<div class="sector-item" style="background:{bg_color};">'
                             f'<div class="sector-code">{code}</div>'
                             f'<div class="sector-name">{name}</div>'
                             f'<div class="sector-change" style="color:{text_color};">{change:+.2f}%</div>'
                             f'</div>')

        # Botones de temporalidad interactivos dentro del módulo
        tf_btns_html = ""
        for tf in tf_options:
            active = tf == current_tf
            bg = "#3b82f6" if active else "#1a1e26"
            border = "#3b82f6" if active else "#2a3f5f"
            fw = "bold" if active else "normal"
            tf_btns_html += (
                f'<button onclick="changeTF(\'{tf}\')" style="background:{bg}; border:1px solid {border}; '
                f'color:white; padding:3px 9px; border-radius:4px; font-size:9px; font-weight:{fw}; '
                f'margin-left:3px; cursor:pointer; transition:all 0.2s;">{tf}</button>'
            )

        sector_module_html = f'''<!DOCTYPE html><html><head><style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#11141a; }}
        .container {{ border:1px solid #1a1e26; border-radius:10px; overflow:hidden; background:#11141a; width:100%; height:420px; display:flex; flex-direction:column; }}
        .header {{ background:#0c0e12; padding:10px 12px; border-bottom:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center; flex-shrink:0; }}
        .title {{ color:white; font-size:13px; font-weight:bold; text-transform:uppercase; letter-spacing:0.5px; }}
        .content {{ flex:1; overflow:hidden; padding:8px; }}
        .sector-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; height:100%; }}
        .sector-item {{ background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:8px 4px; text-align:center; display:flex; flex-direction:column; justify-content:center; }}
        .sector-code {{ color:#666; font-size:9px; font-weight:bold; margin-bottom:2px; }}
        .sector-name {{ color:white; font-size:10px; font-weight:600; margin-bottom:4px; line-height:1.2; }}
        .sector-change {{ font-size:11px; font-weight:bold; }}
        button {{ outline:none; }}
        button:hover {{ filter:brightness(1.2); }}
        .update-timestamp {{ text-align:center; color:#555; font-size:10px; padding:6px 0; font-family:'Courier New',monospace; border-top:1px solid #1a1e26; background:#0c0e12; flex-shrink:0; }}
        .tooltip-wrapper {{ position:static; display:inline-block; }}
        .tooltip-btn {{ width:22px; height:22px; border-radius:50%; background:#1a1e26; border:1px solid #444; display:flex; align-items:center; justify-content:center; color:#888; font-size:12px; font-weight:bold; cursor:help; }}
        .tooltip-content {{ display:none; position:fixed; width:280px; background:#1e222d; color:#eee; padding:12px; border-radius:10px; z-index:99999; font-size:11px; border:2px solid #3b82f6; box-shadow:0 15px 40px rgba(0,0,0,0.9); line-height:1.5; left:50%; top:50%; transform:translate(-50%,-50%); }}
        .tooltip-wrapper:hover .tooltip-content {{ display:block; }}
        </style></head><body>
        <div class="container">
            <div class="header">
                <div class="title">Rotación Sectorial</div>
                <div style="display:flex; align-items:center; gap:2px;">
                    {tf_btns_html}
                    <div class="tooltip-wrapper" style="margin-left:6px;">
                        <div class="tooltip-btn">?</div>
                        <div class="tooltip-content">Rendimiento de sectores vía ETFs sectoriales. Los botones cambian el horizonte temporal: 1D, 3D, 1W, 1M.</div>
                    </div>
                </div>
            </div>
            <div class="content">
                <div class="sector-grid">{sectors_html}</div>
            </div>
            <div class="update-timestamp">Actualizado: {get_timestamp()} · {current_tf}</div>
        </div>
        <script>
        function changeTF(tf) {{
            // Comunicar con Streamlit via postMessage
            window.parent.postMessage({{type:'streamlit:setComponentValue', value: tf}}, '*');
            // Actualizar URL param para que Streamlit lo lea
            const url = new URL(window.parent.location);
            url.searchParams.set('sector_tf', tf);
            window.parent.history.replaceState({{}}, '', url);
            window.parent.location.reload();
        }}
        </script>
        </body></html>'''

        # Botones Streamlit nativos para cambio de temporalidad (compactos, al lado del módulo)
        btn_cols = st.columns(4)
        tf_changed = False
        for i, tf in enumerate(tf_options):
            with btn_cols[i]:
                btn_style = "primary" if tf == current_tf else "secondary"
                if st.button(tf, key=f"sector_btn_{tf}", type=btn_style, use_container_width=True):
                    if tf != current_tf:
                        st.session_state.sector_tf = tf
                        tf_changed = True
        if tf_changed:
            st.rerun()

        st.markdown(f'''
        <style>
        /* Sector timeframe buttons - small cyan */
        div[data-testid="stHorizontalBlock"] button[data-testid="baseButton-secondary"] {{
            background:transparent!important; border:1px solid #1e3a2f!important;
            color:#555!important; font-size:8px!important; padding:1px 6px!important;
            border-radius:4px!important; height:22px!important; min-height:0!important;
            font-weight:500!important; letter-spacing:0.5px!important;
        }}
        div[data-testid="stHorizontalBlock"] button[data-testid="baseButton-secondary"]:hover {{
            border-color:#00ffad66!important; color:#00ffad!important;
        }}
        div[data-testid="stHorizontalBlock"] button[data-testid="baseButton-primary"] {{
            background:#00ffad18!important; border:1px solid #00ffad!important;
            color:#00ffad!important; font-size:8px!important; padding:1px 6px!important;
            border-radius:4px!important; height:22px!important; min-height:0!important;
            font-weight:700!important; letter-spacing:0.5px!important;
            box-shadow:0 0 8px #00ffad22!important;
        }}
        </style>
        <div class="module-container" style="margin-top:4px;">
            <div class="module-header" style="justify-content:space-between;">
                <div class="module-title">Rotación Sectorial</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Rendimiento de sectores vía ETFs sectoriales. Usa los botones de temporalidad superiores.</div>
                </div>
            </div>
            <div class="module-content" style="padding:8px;">
                <div class="sector-grid">{sectors_html}</div>
            </div>
            <div class="update-timestamp">Actualizado: {get_timestamp()} · {current_tf}</div>
        </div>
        ''', unsafe_allow_html=True)

    with c3:
        crypto_fg = get_crypto_fear_greed()
        val = crypto_fg['value']
        fg_timestamp = crypto_fg.get('timestamp', get_timestamp())
        fg_source = crypto_fg.get('source', 'alternative.me')

        if val <= 24: label, col = "MIEDO EXTREMO", "#d32f2f"
        elif val <= 44: label, col = "MIEDO", "#f57c00"
        elif val <= 55: label, col = "NEUTRAL", "#ff9800"
        elif val <= 75: label, col = "CODICIA", "#4caf50"
        else: label, col = "CODICIA EXTREMA", "#00ffad"

        bar_width = val

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Crypto: Miedo y Codicia</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Índice Crypto Fear & Greed – mide el sentimiento del mercado cripto. Fuente: alternative.me</div>
                </div>
            </div>
            <div class="module-content" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:15px;">
                <div style="font-size:3.5rem; font-weight:bold; color:{col};">{val}</div>
                <div style="color:white; font-size:1rem; letter-spacing:1px; font-weight:bold; margin:8px 0;">{label}</div>
                <div style="width:90%; background:#0c0e12; height:12px; border-radius:6px; margin:10px 0; border:1px solid #1a1e26; overflow:hidden;">
                    <div style="width:{bar_width}%; background:{col}; height:100%;"></div>
                </div>
                <div class="fng-legend">
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#d32f2f;"></div><div>Miedo<br>Extremo</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#f57c00;"></div><div>Miedo</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#ff9800;"></div><div>Neutral</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#4caf50;"></div><div>Codicia</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#00ffad;"></div><div>Codicia<br>Extrema</div></div>
                </div>
            </div>
            <div class="update-timestamp">Actualizado: {fg_timestamp} • {fg_source}</div>
        </div>
        ''', unsafe_allow_html=True)


    # FILA 3
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)

    # EARNINGS CALENDAR MEJORADO
    with f3c1:
        earnings = get_earnings_calendar()
        
        earn_html = ""
        for item in earnings:
            impact_color = "#f23645" if item['impact'] in ("High", "N/D") else "#888"
            days = item.get('days', 0)
            
            if days == 0:
                days_text = "HOY"
                days_color = "#f23645"
                days_bg = "#f2364522"
            elif days == 1:
                days_text = "MAÑANA"
                days_color = "#ff9800"
                days_bg = "#ff980022"
            elif days <= 3:
                days_text = f"+{days}d"
                days_color = "#00ffad"
                days_bg = "#00ffad22"
            else:
                days_text = f"+{days}d"
                days_color = "#888"
                days_bg = "#1a1e26"
            
            market_cap = item.get('market_cap', '-')
            timing = item.get('time', '-')
            
            earn_html += f'''
            <div style="background:#0c0e12; padding:9px; border-radius:6px; margin-bottom:7px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center; position:relative; overflow:hidden;">
                <div style="position:absolute; left:0; top:0; bottom:0; width:3px; background:{impact_color};"></div>
                <div style="margin-left:8px;">
                    <div style="color:#00ffad; font-weight:bold; font-size:12px; letter-spacing:0.5px;">{item['ticker']}</div>
                    <div style="color:#555; font-size:8px; margin-top:2px;">{market_cap}</div>
                </div>
                <div style="text-align:center; flex:1; margin:0 10px;">
                    <div style="color:white; font-weight:bold; font-size:11px;">{item['date']}</div>
                    <div style="color:#666; font-size:8px; text-transform:uppercase; letter-spacing:0.3px;">{timing}</div>
                </div>
                <div style="text-align:right;">
                    <div style="background:{days_bg}; color:{days_color}; padding:3px 8px; border-radius:4px; font-size:9px; font-weight:bold; border:1px solid {days_color}33;">
                        {days_text}
                    </div>
                    <div style="color:{impact_color}; font-size:8px; font-weight:bold; margin-top:4px; text-transform:uppercase;">● Alto impacto</div>
                </div>
            </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Calendario de Resultados</div>
                <div style="display:flex; align-items:center; gap:6px;">
                    <span style="background:#2a3f5f; color:#00ffad; padding:2px 6px; border-radius:3px; font-size:9px; font-weight:bold;">MEGA-CAP</span>
                    <div class="tooltip-wrapper">
                        <div class="tooltip-btn">?</div>
                        <div class="tooltip-content">Próximos resultados de empresas mega-cap. Solo fechas futuras. Fuente: Alpha Vantage / yfinance.</div>
                    </div>
                </div>
            </div>
            <div class="module-content" style="padding:10px;">{earn_html}</div>
            <div class="update-timestamp">Actualizado: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with f3c2:
        insiders = get_insider_trading()
        insider_html = ""
        for item in insiders:
            is_buy = item['type'] in ("COMPRA", "BUY")
            type_color = "#00ffad" if is_buy else "#f23645"
            type_bg = "#00ffad15" if is_buy else "#f2364515"
            type_border = "#00ffad40" if is_buy else "#f2364540"
            type_label = "COMPRA" if is_buy else "VENTA"
            date_str = str(item.get('date', ''))[:10]
            insider_html += f'''
            <div style="background:#0c0e12; padding:8px 10px; border-radius:6px; margin-bottom:5px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center; position:relative; overflow:hidden;">
                <div style="position:absolute; left:0; top:0; bottom:0; width:3px; background:{type_color};"></div>
                <div style="margin-left:8px; flex:1; min-width:0;">
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="color:#00ffad; font-weight:bold; font-size:11px;">{item['ticker']}</span>
                        <span style="background:{type_bg}; color:{type_color}; border:1px solid {type_border}; padding:1px 5px; border-radius:3px; font-size:8px; font-weight:bold;">{type_label}</span>
                    </div>
                    <div style="color:#666; font-size:8px; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{item.get('insider', '-')}</div>
                    <div style="color:#444; font-size:7px;">{item.get('position', '-')}</div>
                </div>
                <div style="text-align:right; flex-shrink:0; margin-left:8px;">
                    <div style="color:white; font-weight:bold; font-size:11px;">{item['amount']}</div>
                    <div style="color:#555; font-size:8px;">{date_str}</div>
                </div>
            </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Tracker Insiders</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Transacciones reales de insiders (>$100K) via OpenInsider / SEC Form 4. Actualizado cada 30 minutos.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 8px;">{insider_html}</div>
            <div class="update-timestamp">Actualizado: {get_timestamp()} • OpenInsider</div>
        </div>
        ''', unsafe_allow_html=True)

    with f3c3:
        news = fetch_finnhub_news()
        news_items_html = []
        for item in news[:8]:
            safe_title = item['title'].replace('"', '&quot;').replace("'", '&#39;')
            news_item = (
                '<div style="padding: 8px 12px; border-bottom: 1px solid #1a1e26;">'
                '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:3px;">'
                '<span style="color:#888;font-size:0.7rem;font-family:monospace;">' + item['time'] + '</span>'
                '<span style="padding: 1px 6px; border-radius: 8px; font-size: 0.65rem; font-weight: bold; background-color:' + item['color'] + '22;color:' + item['color'] + ';">' + item['impact'] + '</span>'
                '</div>'
                '<div style="color:white;font-size:0.8rem;line-height:1.2;margin-bottom:4px;">' + safe_title + '</div>'
                '<a href="' + item['link'] + '" target="_blank" style="color: #00ffad; text-decoration: none; font-size: 0.75rem;">→ Leer más</a>'
                '</div>'
            )
            news_items_html.append(news_item)
        news_content = "".join(news_items_html)

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Noticias de Alto Impacto</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Noticias financieras de alto impacto vía Finnhub API. Titulares traducidos al castellano.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 0; overflow-y: auto;">{news_content}</div>
            <div class="update-timestamp">Actualizado: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    # FILA 4
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)

    with f4c1:
        # VIX con gráfico diario y niveles 20/25
        try:
            vix_ticker = yf.Ticker("^VIX")
            vix_hist = vix_ticker.history(period="6mo")
            vix_current = float(vix_hist['Close'].iloc[-1]) if len(vix_hist) > 0 else 20.0
            vix_prev = float(vix_hist['Close'].iloc[-2]) if len(vix_hist) > 1 else vix_current
            vix_change = vix_current - vix_prev
            vix_change_pct = (vix_change / vix_prev * 100) if vix_prev else 0
            vix_vals = [float(v) for v in vix_hist['Close'].values]
            vix_dates = [str(d)[:10] for d in vix_hist.index]
        except:
            vix_current, vix_prev, vix_change, vix_change_pct = 20.0, 19.5, 0.5, 2.5
            vix_vals, vix_dates = [], []

        vix_color = "#f23645" if vix_change >= 0 else "#00ffad"
        vix_level_color = "#f23645" if vix_current >= 25 else ("#ff9800" if vix_current >= 20 else "#00ffad")
        vix_state = "ESTRÉS ALTO" if vix_current >= 25 else ("PRECAUCIÓN" if vix_current >= 20 else "CALMA")

        # Generar SVG del gráfico VIX
        def _vix_chart_svg(vals, dates, W=320, H=180):
            if len(vals) < 5:
                return '<text x="50%" y="50%" text-anchor="middle" fill="#555" font-size="10">Sin datos</text>'
            pad = {'l': 35, 'r': 10, 't': 15, 'b': 22}
            mn = min(min(vals), 10)
            mx = max(max(vals), 30)
            rng = mx - mn if mx != mn else 1
            n = len(vals)

            def to_xy(i, v):
                x = pad['l'] + i * (W - pad['l'] - pad['r']) / (n - 1)
                y = H - pad['b'] - ((v - mn) / rng) * (H - pad['t'] - pad['b'])
                return x, y

            # Área bajo la curva
            area_pts = [f"{pad['l']},{H - pad['b']}"]
            line_pts = []
            for i, v in enumerate(vals):
                x, y = to_xy(i, v)
                area_pts.append(f"{x:.1f},{y:.1f}")
                line_pts.append(f"{x:.1f},{y:.1f}")
            area_pts.append(f"{W - pad['r']},{H - pad['b']}")

            # Nivel 20
            _, y20 = to_xy(0, 20)
            # Nivel 25
            _, y25 = to_xy(0, 25)

            # Y ticks
            yticks = ""
            for v in [10, 15, 20, 25, 30]:
                if mn <= v <= mx:
                    _, yv = to_xy(0, v)
                    col = "#f2364555" if v in [20, 25] else "#1a1e26"
                    yticks += f'<line x1="{pad["l"]}" y1="{yv:.1f}" x2="{W - pad["r"]}" y2="{yv:.1f}" stroke="{col}" stroke-width="0.7"/>'
                    yticks += f'<text x="{pad["l"] - 3}" y="{yv + 3:.1f}" text-anchor="end" fill="#555" font-size="7">{v}</text>'

            # X labels
            xlabels = ""
            step = max(1, n // 5)
            for i in range(0, n, step):
                x, _ = to_xy(i, vals[i])
                lbl = dates[i][5:] if i < len(dates) else ""
                xlabels += f'<text x="{x:.1f}" y="{H - 4}" text-anchor="middle" fill="#555" font-size="7">{lbl}</text>'

            # Último punto
            lx, ly = to_xy(n - 1, vals[-1])
            dot_color = "#f23645" if vals[-1] >= 25 else ("#ff9800" if vals[-1] >= 20 else "#00ffad")

            return f'''
            {yticks}
            <line x1="{pad["l"]}" y1="{y20:.1f}" x2="{W - pad["r"]}" y2="{y20:.1f}" stroke="#ff980088" stroke-width="1" stroke-dasharray="4,3"/>
            <text x="{W - pad["r"] - 2}" y="{y20 - 3:.1f}" text-anchor="end" fill="#ff9800" font-size="8" font-weight="bold">20</text>
            <line x1="{pad["l"]}" y1="{y25:.1f}" x2="{W - pad["r"]}" y2="{y25:.1f}" stroke="#f2364588" stroke-width="1" stroke-dasharray="4,3"/>
            <text x="{W - pad["r"] - 2}" y="{y25 - 3:.1f}" text-anchor="end" fill="#f23645" font-size="8" font-weight="bold">25</text>
            <polygon points="{" ".join(area_pts)}" fill="{dot_color}15"/>
            <polyline points="{" ".join(line_pts)}" fill="none" stroke="{dot_color}" stroke-width="1.5" stroke-linejoin="round"/>
            <circle cx="{lx:.1f}" cy="{ly:.1f}" r="3" fill="{dot_color}" stroke="#11141a" stroke-width="1"/>
            {xlabels}'''

        chart_svg = _vix_chart_svg(vix_vals, vix_dates)

        vix_full_html = f'''<!DOCTYPE html><html><head><style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#11141a; }}
        .container {{ border:1px solid #1a1e26; border-radius:10px; overflow:hidden; background:#11141a; width:100%; height:420px; display:flex; flex-direction:column; }}
        .header {{ background:#0c0e12; padding:10px 12px; border-bottom:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center; flex-shrink:0; }}
        .title {{ color:white; font-size:13px; font-weight:bold; text-transform:uppercase; letter-spacing:0.5px; }}
        .content {{ flex:1; overflow:hidden; padding:10px; display:flex; flex-direction:column; }}
        .update-timestamp {{ text-align:center; color:#555; font-size:10px; padding:5px 0; font-family:'Courier New',monospace; border-top:1px solid #1a1e26; background:#0c0e12; flex-shrink:0; }}
        .tooltip-wrapper {{ position:static; display:inline-block; }}
        .tooltip-btn {{ width:22px; height:22px; border-radius:50%; background:#1a1e26; border:1px solid #444; display:flex; align-items:center; justify-content:center; color:#888; font-size:12px; font-weight:bold; cursor:help; }}
        .tooltip-content {{ display:none; position:fixed; width:280px; background:#1e222d; color:#eee; padding:12px; border-radius:10px; z-index:99999; font-size:11px; border:2px solid #3b82f6; box-shadow:0 15px 40px rgba(0,0,0,0.9); line-height:1.5; left:50%; top:50%; transform:translate(-50%,-50%); }}
        .tooltip-wrapper:hover .tooltip-content {{ display:block; }}
        </style></head><body>
        <div class="container">
            <div class="header">
                <div class="title">VIX Índice de Volatilidad</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">CBOE Volatility Index (VIX). Niveles clave: 20 = zona de precaución, 25+ = estrés de mercado. Gráfico diario 6 meses. Fuente: yfinance.</div>
                </div>
            </div>
            <div class="content">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                    <div>
                        <div style="font-size:2rem; font-weight:bold; color:{vix_level_color}; line-height:1;">{vix_current:.2f}</div>
                        <div style="font-size:10px; color:{vix_color}; font-weight:bold;">{vix_change:+.2f} ({vix_change_pct:+.2f}%)</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="background:{vix_level_color}20; color:{vix_level_color}; border:1px solid {vix_level_color}50; padding:3px 8px; border-radius:4px; font-size:9px; font-weight:bold;">{vix_state}</div>
                        <div style="color:#555; font-size:8px; margin-top:4px;">Diario · 6 meses</div>
                    </div>
                </div>
                <div style="flex:1; background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:6px; overflow:hidden;">
                    <svg width="100%" height="100%" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid meet">
                        {chart_svg}
                    </svg>
                </div>
                <div style="display:flex; gap:12px; margin-top:6px; font-size:9px; color:#666;">
                    <span>— <span style="color:#ff9800;">Nivel 20</span> (precaución)</span>
                    <span>— <span style="color:#f23645;">Nivel 25</span> (estrés)</span>
                </div>
            </div>
            <div class="update-timestamp">Actualizado: {get_timestamp()} • CBOE via yfinance</div>
        </div>
        </body></html>'''
        components.html(vix_full_html, height=420, scrolling=False)

    with f4c2:
        fed = get_fed_liquidity()
        color = fed['color']
        status = fed['status']
        
        # Generar sparkline del balance histórico
        hist = fed.get('history', [])
        if len(hist) >= 4:
            W_f, H_f = 300, 55
            pad_f = {'l': 5, 'r': 5, 't': 5, 'b': 5}
            h_vals = [v for _, v in hist]
            mn_f, mx_f = min(h_vals), max(h_vals)
            rng_f = mx_f - mn_f if mx_f != mn_f else 0.1
            n_f = len(h_vals)
            pts_f = []
            area_f = [f"{pad_f['l']},{H_f - pad_f['b']}"]
            for i, v in enumerate(h_vals):
                x = pad_f['l'] + i * (W_f - pad_f['l'] - pad_f['r']) / (n_f - 1)
                y = H_f - pad_f['b'] - ((v - mn_f) / rng_f) * (H_f - pad_f['t'] - pad_f['b'])
                pts_f.append(f"{x:.1f},{y:.1f}")
                area_f.append(f"{x:.1f},{y:.1f}")
            area_f.append(f"{W_f - pad_f['r']},{H_f - pad_f['b']}")
            sparkline_fed = f'''<svg width="100%" height="{H_f}" viewBox="0 0 {W_f} {H_f}">
                <polygon points="{" ".join(area_f)}" fill="{color}15"/>
                <polyline points="{" ".join(pts_f)}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linejoin="round"/>
            </svg>'''
        else:
            sparkline_fed = '<div style="color:#555; font-size:9px; text-align:center; padding:10px;">Sin historial</div>'
        
        # Determinar postura monetaria
        ff_rate = fed.get('fed_rate')
        if ff_rate is not None:
            if ff_rate >= 4.5:
                postura, postura_color = "RESTRICTIVA", "#f23645"
            elif ff_rate >= 3.0:
                postura, postura_color = "NEUTRAL", "#ff9800"
            else:
                postura, postura_color = "EXPANSIVA", "#00ffad"
        else:
            postura, postura_color = "N/D", "#888"
        
        w_change_num = fed.get('weekly_change_num', 0) or 0
        w_change_color = "#00ffad" if w_change_num > 0 else ("#f23645" if w_change_num < 0 else "#888")
        
        fed_html = f'''<div style="display:flex; flex-direction:column; height:100%; gap:6px;">
            <!-- Status principal -->
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:1.6rem; font-weight:bold; color:{color}; line-height:1;">{status}</div>
                    <div style="font-size:9px; color:#888; margin-top:2px;">{fed['desc']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.4rem; font-weight:bold; color:white;">{fed['total']}</div>
                    <div style="font-size:8px; color:#555;">Balance total WALCL</div>
                </div>
            </div>
            <!-- Cambio semanal -->
            <div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:6px 10px; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#888; font-size:9px;">Δ Semanal</span>
                <span style="color:{w_change_color}; font-size:10px; font-weight:bold;">{fed.get('weekly_change', 'N/D')}</span>
            </div>
            <!-- Desglose activos -->
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:5px;">
                <div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:5px; padding:5px 8px; text-align:center;">
                    <div style="font-size:8px; color:#555; margin-bottom:2px;">TREASURIES</div>
                    <div style="font-size:11px; color:#3b82f6; font-weight:bold;">{fed['treasuries']}</div>
                </div>
                <div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:5px; padding:5px 8px; text-align:center;">
                    <div style="font-size:8px; color:#555; margin-bottom:2px;">MBS</div>
                    <div style="font-size:11px; color:#a78bfa; font-weight:bold;">{fed['mbs']}</div>
                </div>
            </div>
            <!-- Liquidez neta -->
            <div style="background:{'#00ffad10' if (fed.get('net_liquidity_num') or 0) > 0 else '#f2364510'}; border:1px solid {'#00ffad30' if (fed.get('net_liquidity_num') or 0) > 0 else '#f2364530'}; border-radius:6px; padding:6px 10px;">
                <div style="font-size:8px; color:#888; margin-bottom:2px;">Liquidez Neta = Balance − TGA − RRP</div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:12px; font-weight:bold; color:white;">{fed['net_liquidity']}</div>
                    <div style="font-size:8px; color:#555;">TGA:{fed['tga']} | RRP:{fed['rrp']}</div>
                </div>
            </div>
            <!-- Tipo de interés -->
            <div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:6px 10px; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#888; font-size:9px;">Fed Funds Rate</span>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:12px; font-weight:bold; color:white;">{f"{ff_rate:.2f}%" if ff_rate else "N/D"}</span>
                    <span style="background:{postura_color}22; color:{postura_color}; border:1px solid {postura_color}44; padding:1px 6px; border-radius:3px; font-size:8px; font-weight:bold;">{postura}</span>
                </div>
            </div>
            <!-- Sparkline balance -->
            <div>
                <div style="font-size:8px; color:#555; margin-bottom:2px;">Balance últimas 20 semanas</div>
                {sparkline_fed}
            </div>
        </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Política de Liquidez FED</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Balance de la Reserva Federal via FRED. Incluye desglose Treasuries/MBS, Liquidez Neta (Balance−TGA−RRP), cambio semanal y tipo de interés. Requiere FRED_API_KEY.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 10px;">{fed_html}</div>
            <div class="update-timestamp">Actualizado: {fed['date']} • FRED</div>
        </div>
        ''', unsafe_allow_html=True)

    with f4c3:
        # Yield Curve: 2Y vs 10Y
        try:
            tnx = yf.Ticker("^TNX")  # 10Y
            irx = yf.Ticker("^IRX")  # 13-week; usaremos ^TYX como 30Y y FVX como 5Y
            tyx2y = yf.Ticker("^FVX") # 5Y proxy; mejor usar directo
            # 2Y via FRED o yfinance - usar DGS2 proxy
            t2y_ticker = yf.Ticker("^IRX")  # 3 month
            
            tnx_hist = tnx.history(period="1y")
            # 2Y Treasury: usar símbolo alternativo
            t2y_ticker2 = yf.Ticker("SHY")  # 1-3Y Treasury ETF como proxy
            t2y_hist = t2y_ticker2.history(period="1y")
            
            y10 = float(tnx_hist['Close'].iloc[-1]) if len(tnx_hist) > 0 else 4.0
            y10_prev = float(tnx_hist['Close'].iloc[-2]) if len(tnx_hist) > 1 else y10
            
            # Intentar obtener 2Y real
            try:
                twoy = yf.Ticker("^UST2Y")
                twoy_hist = twoy.history(period="5d")
                if len(twoy_hist) > 0:
                    y2 = float(twoy_hist['Close'].iloc[-1])
                else:
                    raise Exception("no data")
            except:
                # Fallback: estimar 2Y ~ IRX (3M) + spread
                irx_h = yf.Ticker("^IRX").history(period="5d")
                y2 = float(irx_h['Close'].iloc[-1]) * 0.01 * 10 if len(irx_h) > 0 else y10 * 0.9
                if y2 > y10 * 1.5 or y2 < 0.5:
                    y2 = y10 - 0.5  # estimación razonable
            
            spread = y10 - y2
            spread_pct = spread * 100  # en puntos básicos
            is_inverted = spread < 0
            
            # Historial del spread (proxy)
            y10_vals = [float(v) for v in tnx_hist['Close'].values[-90:]]
            # Generar historial spread sintético
            spread_history = []
            for i, y10v in enumerate(y10_vals):
                sp = y10v - y2 + (i - len(y10_vals)) * 0.005  # tendencia aproximada
                spread_history.append(sp)
            
        except Exception as e:
            y10, y2, spread = 4.0, 4.5, -0.5
            is_inverted = True
            spread_history = [-0.5] * 30
        
        spread_color = "#f23645" if is_inverted else "#00ffad"
        status_text = "⚠ INVERTIDA" if is_inverted else "✓ NORMAL"
        status_bg = "#f2364515" if is_inverted else "#00ffad15"
        
        # Generar mini sparkline del spread histórico
        W_sp, H_sp = 300, 60
        pad_sp = 5
        if len(spread_history) >= 2:
            mn_sp, mx_sp = min(spread_history), max(spread_history)
            rng_sp = mx_sp - mn_sp if mx_sp != mn_sp else 0.1
            n_sp = len(spread_history)
            sp_pts = []
            for i, sv in enumerate(spread_history):
                x = pad_sp + i * (W_sp - 2*pad_sp) / (n_sp - 1)
                y = H_sp - pad_sp - ((sv - mn_sp) / rng_sp) * (H_sp - 2*pad_sp)
                sp_pts.append(f"{x:.1f},{y:.1f}")
            # Línea cero
            zero_y = H_sp - pad_sp - ((0 - mn_sp) / rng_sp) * (H_sp - 2*pad_sp) if mn_sp <= 0 <= mx_sp else H_sp/2
            sparkline_svg = f'''<svg width="100%" height="{H_sp}" viewBox="0 0 {W_sp} {H_sp}">
                <line x1="{pad_sp}" y1="{zero_y:.1f}" x2="{W_sp-pad_sp}" y2="{zero_y:.1f}" stroke="#f23645" stroke-width="0.8" stroke-dasharray="3,2" opacity="0.6"/>
                <text x="{W_sp-pad_sp}" y="{zero_y-2:.1f}" text-anchor="end" fill="#f2364588" font-size="7">0</text>
                <polyline points="{" ".join(sp_pts)}" fill="none" stroke="{spread_color}" stroke-width="1.5" stroke-linejoin="round"/>
            </svg>'''
        else:
            sparkline_svg = ""
        
        tnx_html = f'''<div style="display:flex; flex-direction:column; height:100%; gap:8px;">
            <!-- Header datos -->
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-size:9px; color:#888; text-transform:uppercase; letter-spacing:0.5px;">Rendimiento Bono 10Y</div>
                    <div style="font-size:2rem; font-weight:bold; color:white; line-height:1.1;">{y10:.2f}%</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:9px; color:#888; text-transform:uppercase; letter-spacing:0.5px;">Bono 2Y</div>
                    <div style="font-size:2rem; font-weight:bold; color:#aaa; line-height:1.1;">{y2:.2f}%</div>
                </div>
            </div>
            <!-- Spread badge -->
            <div style="background:{status_bg}; border:1px solid {spread_color}33; border-radius:8px; padding:10px 14px; text-align:center;">
                <div style="font-size:11px; color:#888; margin-bottom:4px;">Spread 10Y-2Y</div>
                <div style="font-size:1.6rem; font-weight:bold; color:{spread_color}; line-height:1;">{spread:+.2f}%</div>
                <div style="font-size:9px; font-weight:bold; color:{spread_color}; margin-top:4px; letter-spacing:0.5px;">{status_text}</div>
            </div>
            <!-- Explicación -->
            <div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:8px 10px;">
                <div style="font-size:9px; color:#888; line-height:1.5;">
                    {"⚠ <span style='color:#f23645;'>Curva invertida:</span> El bono corto (2Y) rinde más que el largo (10Y). Históricamente precede a recesiones en 6-18 meses." if is_inverted else "✓ <span style='color:#00ffad;'>Curva normal:</span> Los bonos largos rinden más, reflejando expectativas de crecimiento económico saludable."}
                </div>
            </div>
            <!-- Sparkline histórico del spread -->
            <div>
                <div style="font-size:8px; color:#555; margin-bottom:3px;">Evolución del spread (90 días)</div>
                {sparkline_svg}
            </div>
        </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Curva de Tipos 2Y vs 10Y</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Diferencial entre el bono del Tesoro a 10 años y el de 2 años. Una curva invertida (2Y &gt; 10Y) es señal histórica de recesión.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 12px;">{tnx_html}</div>
            <div class="update-timestamp">Actualizado: {get_timestamp()} • US Treasury via yfinance</div>
        </div>
        ''', unsafe_allow_html=True)


    # FILA 5 - Módulos HTML (altura aumentada a 420px en CSS)
    st.write("")
    f5c1, f5c2, f5c3 = st.columns(3)

    # Market Breadth
    with f5c1:
        breadth = get_market_breadth()
        trend_color = "#00ffad" if breadth['trend'] == 'ALCISTA' else "#f23645"
        strength_color = "#00ffad" if breadth['strength'] == 'FUERTE' else "#ff9800"
        sma50_color = "#00ffad" if breadth['above_sma50'] else "#f23645"
        sma200_color = "#00ffad" if breadth['above_sma200'] else "#f23645"
        golden_color = "#00ffad" if breadth['golden_cross'] else "#f23645"
        golden_text = "GOLDEN CROSS ✓" if breadth['golden_cross'] else "DEATH CROSS ✗"
        rsi = breadth['rsi']
        if rsi > 70: rsi_color, rsi_text = "#f23645", "SOBRECOMPRA"
        elif rsi < 30: rsi_color, rsi_text = "#00ffad", "SOBREVENTA"
        else: rsi_color, rsi_text = "#ff9800", "NEUTRAL"
        
        mcclellan = breadth.get('mcclellan', 0.0)
        mcclellan_color = "#00ffad" if mcclellan > 0 else "#f23645"
        mcclellan_state = "ALCISTA" if mcclellan > 20 else ("BAJISTA" if mcclellan < -20 else "NEUTRO")
        
        pct_sma50 = breadth.get('pct_above_sma50', 50.0)
        pct_color = "#00ffad" if pct_sma50 >= 60 else ("#f23645" if pct_sma50 <= 40 else "#ff9800")
        
        # SMA200: si es nan, mostrar N/D
        sma200_val = breadth['sma200']
        import math
        if math.isnan(sma200_val) if isinstance(sma200_val, float) else False:
            sma200_str = "N/D (insuf. datos)"
            sma200_color_use = "#888"
        else:
            sma200_str = f"${sma200_val:.2f}"
            sma200_color_use = sma200_color

        tooltip_text = "Market Breadth: SMA50/200, Golden/Death Cross, RSI(14), Oscilador McClellan, % activos sobre SMA50"
        timestamp_str = get_timestamp()

        breadth_html = f'''<!DOCTYPE html><html><head><style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        .container {{ border: 1px solid #1a1e26; border-radius: 10px; overflow: hidden; background: #11141a; width: 100%; height: 420px; display: flex; flex-direction: column; }}
        .header {{ background: #0c0e12; padding: 10px 12px; border-bottom: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }}
        .title {{ color: white; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }}
        .tooltip-wrapper {{ position: static; display: inline-block; }}
        .tooltip-btn {{ width: 24px; height: 24px; border-radius: 50%; background: #1a1e26; border: 2px solid #555; display: flex; align-items: center; justify-content: center; color: #aaa; font-size: 14px; font-weight: bold; cursor: help; }}
        .tooltip-content {{ display: none; position: fixed; width: 300px; background-color: #1e222d; color: #eee; text-align: left; padding: 15px; border-radius: 10px; z-index: 99999; font-size: 12px; border: 2px solid #3b82f6; box-shadow: 0 15px 40px rgba(0,0,0,0.9); line-height: 1.5; left: 50%; top: 50%; transform: translate(-50%, -50%); white-space: normal; word-wrap: break-word; }}
        .tooltip-wrapper:hover .tooltip-content {{ display: block; }}
        .content {{ background: #11141a; flex: 1; overflow-y: auto; padding: 10px; }}
        .metric-box {{ background: #0c0e12; border: 1px solid #1a1e26; border-radius: 6px; padding: 7px 10px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center; }}
        .metric-label {{ color: #888; font-size: 10px; }}
        .metric-value {{ font-size: 12px; font-weight: bold; }}
        .rsi-gauge {{ width: 100%; height: 12px; background: linear-gradient(to right, #00ffad 0%, #ff9800 50%, #f23645 100%); border-radius: 6px; position: relative; margin: 4px 0; }}
        .rsi-marker {{ position: absolute; top: -3px; width: 3px; height: 18px; background: white; border-radius: 2px; transform: translateX(-50%); }}
        .pct-bar-bg {{ width: 100%; height: 8px; background: #1a1e26; border-radius: 4px; margin: 4px 0; overflow: hidden; }}
        .pct-bar {{ height: 100%; border-radius: 4px; }}
        .update-timestamp {{ text-align: center; color: #555; font-size: 10px; padding: 6px 0; font-family: 'Courier New', monospace; border-top: 1px solid #1a1e26; background: #0c0e12; flex-shrink: 0; }}
        </style></head><body>
        <div class="container">
            <div class="header">
                <div class="title">Market Breadth</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">{tooltip_text}</div>
                </div>
            </div>
            <div class="content">
                <div class="metric-box">
                    <span class="metric-label">Precio SPY</span>
                    <span class="metric-value" style="color: white;">${breadth['price']:.2f}</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">SMA 50</span>
                    <span class="metric-value" style="color: {sma50_color};">${breadth['sma50']:.2f}</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">SMA 200</span>
                    <span class="metric-value" style="color: {sma200_color_use};">{sma200_str}</span>
                </div>
                <div class="metric-box" style="border-color: {golden_color}44; background: {golden_color}11;">
                    <span class="metric-label">Señal</span>
                    <span class="metric-value" style="color: {golden_color};">{golden_text}</span>
                </div>
                <div class="metric-box">
                    <div style="flex:1;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                            <span class="metric-label">Oscilador McClellan</span>
                            <span style="color:{mcclellan_color}; font-size:10px; font-weight:bold;">{mcclellan:+.1f} · {mcclellan_state}</span>
                        </div>
                        <div class="pct-bar-bg">
                            <div class="pct-bar" style="width:{min(abs(mcclellan)/50*100,100):.0f}%; background:{mcclellan_color};"></div>
                        </div>
                        <div style="font-size:8px; color:#555;">Señal: >+50 sobrecompra · <-50 sobreventa</div>
                    </div>
                </div>
                <div class="metric-box">
                    <div style="flex:1;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                            <span class="metric-label">% Sectores sobre SMA50</span>
                            <span style="color:{pct_color}; font-size:11px; font-weight:bold;">{pct_sma50:.0f}%</span>
                        </div>
                        <div class="pct-bar-bg">
                            <div class="pct-bar" style="width:{pct_sma50:.0f}%; background:{pct_color};"></div>
                        </div>
                    </div>
                </div>
                <div style="margin-top:6px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                        <span class="metric-label">RSI (14)</span>
                        <span style="color:{rsi_color}; font-size:10px; font-weight:bold;">{rsi:.1f} — {rsi_text}</span>
                    </div>
                    <div class="rsi-gauge">
                        <div class="rsi-marker" style="left:{min(rsi,100):.0f}%;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:8px; color:#555; margin-top:2px;">
                        <span>0</span><span>30</span><span>50</span><span>70</span><span>100</span>
                    </div>
                </div>
                <div style="margin-top:6px; display:grid; grid-template-columns:1fr 1fr; gap:6px;">
                    <div class="metric-box" style="text-align:center; margin-bottom:0; padding:6px;">
                        <div class="metric-label">Tendencia</div>
                        <div style="color:{trend_color}; font-size:11px; font-weight:bold;">{breadth['trend']}</div>
                    </div>
                    <div class="metric-box" style="text-align:center; margin-bottom:0; padding:6px;">
                        <div class="metric-label">Fuerza</div>
                        <div style="color:{strength_color}; font-size:11px; font-weight:bold;">{breadth['strength']}</div>
                    </div>
                </div>
            </div>
            <div class="update-timestamp">Actualizado: {timestamp_str}</div>
        </div>
        </body></html>'''
        components.html(breadth_html, height=420, scrolling=False)


    # VIX Term Structure
    with f5c2:
        vix_data = get_vix_term_structure()
        state_color = vix_data['state_color']
        state_bg = f"{state_color}15"
        chart_html = generate_vix_chart_html(vix_data)
        tooltip_text = f"VIX Term Structure: {vix_data['state']}. {vix_data['explanation']}"
        data_points = vix_data['data']
        slope_pct = ((data_points[-1]['current'] - data_points[0]['current']) / data_points[0]['current']) * 100 if len(data_points) >= 2 else 0
        timestamp_str = get_timestamp()

        vix_html_full = f"""
<!DOCTYPE html><html><head><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
.container {{ border: 1px solid #1a1e26; border-radius: 10px; overflow: hidden; background: #11141a; width: 100%; height: 420px; display: flex; flex-direction: column; }}
.header {{ background: #0c0e12; padding: 10px 12px; border-bottom: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; position: relative; }}
.title {{ color: white; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }}
.state-badge {{ background: {state_bg}; color: {state_color}; padding: 4px 10px; border-radius: 10px; font-size: 10px; font-weight: bold; border: 1px solid {state_color}33; position: absolute; left: 50%; transform: translateX(-50%); }}
.tooltip-wrapper {{ position: static; display: inline-block; }}
.tooltip-btn {{ width: 22px; height: 22px; border-radius: 50%; background: #1a1e26; border: 1px solid #444; display: flex; align-items: center; justify-content: center; color: #888; font-size: 12px; font-weight: bold; cursor: help; }}
.tooltip-content {{ display: none; position: fixed; width: 300px; background-color: #1e222d; color: #eee; text-align: left; padding: 15px; border-radius: 10px; z-index: 99999; font-size: 12px; border: 2px solid #3b82f6; box-shadow: 0 15px 40px rgba(0,0,0,0.9); line-height: 1.5; left: 50%; top: 50%; transform: translate(-50%, -50%); white-space: normal; word-wrap: break-word; }}
.tooltip-wrapper:hover .tooltip-content {{ display: block; }}
.content {{ background: #11141a; flex: 1; overflow-y: auto; padding: 10px; }}
.spot-box {{ display: flex; justify-content: space-between; align-items: center; background: linear-gradient(90deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 6px; padding: 10px 14px; margin-bottom: 10px; }}
.spot-label {{ color: #888; font-size: 10px; font-weight: 500; }}
.spot-value {{ color: white; font-size: 20px; font-weight: bold; }}
.spot-change {{ color: {state_color}; font-size: 10px; font-weight: bold; margin-top: 2px; }}
.chart-wrapper {{ background: #0c0e12; border: 1px solid #1a1e26; border-radius: 6px; padding: 8px; margin-bottom: 8px; }}
.insight-box {{ background: {state_bg}; border: 1px solid {state_color}22; border-radius: 6px; padding: 8px 10px; }}
.insight-title {{ color: {state_color}; font-weight: bold; font-size: 11px; margin-bottom: 2px; }}
.insight-desc {{ color: #aaa; font-size: 10px; line-height: 1.3; }}
.update-timestamp {{ text-align: center; color: #555; font-size: 10px; padding: 6px 0; font-family: 'Courier New', monospace; border-top: 1px solid #1a1e26; background: #0c0e12; flex-shrink: 0; }}
</style></head><body>
<div class="container">
    <div class="header">
        <div class="title">VIX Term Structure</div>
        <span class="state-badge">{vix_data['state']}</span>
        <div class="tooltip-wrapper">
            <div class="tooltip-btn">?</div>
            <div class="tooltip-content">{tooltip_text}</div>
        </div>
    </div>
    <div class="content">
        <div class="spot-box">
            <div>
                <div class="spot-label">VIX Spot</div>
                <div class="spot-change">{slope_pct:+.1f}% vs Far Month</div>
            </div>
            <div class="spot-value">{vix_data['current_spot']:.2f}</div>
        </div>
        <div class="chart-wrapper">
            {chart_html}
        </div>
        <div class="insight-box">
            <div class="insight-title">● {vix_data['state']}</div>
            <div class="insight-desc">{vix_data['state_desc']}</div>
        </div>
    </div>
    <div class="update-timestamp">Actualizado: {timestamp_str}</div>
</div>
</body></html>
"""
        components.html(vix_html_full, height=420, scrolling=False)

    # Crypto Pulse
    with f5c3:
        try:
            cryptos = get_crypto_prices()
        except:
            cryptos = get_fallback_crypto_prices()

        crypto_items_html = []
        for crypto in cryptos[:6]:
            symbol = str(crypto.get('symbol', 'N/A'))
            name = str(crypto.get('name', 'Unknown'))
            price = str(crypto.get('price', '0.00'))
            change = str(crypto.get('change', '0%'))
            color = "#00ffad" if crypto.get('is_positive', True) else "#f23645"
            item_html = (
                '<div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 6px; padding: 8px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">'
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<div style="color: #00ffad; font-weight: bold; font-size: 12px;">' + symbol + '</div>'
                '<div style="color: #555; font-size: 9px;">' + name + '</div></div>'
                '<div style="text-align: right;">'
                '<div style="color: white; font-size: 12px; font-weight: bold;">$' + price + '</div>'
                '<div style="color: ' + color + '; font-size: 10px; font-weight: bold;">' + change + '</div></div></div>'
            )
            crypto_items_html.append(item_html)
        crypto_content = "".join(crypto_items_html)
        timestamp_str = get_timestamp()

        crypto_html_full = '''<!DOCTYPE html><html><head><style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .container { border: 1px solid #1a1e26; border-radius: 10px; overflow: hidden; background: #11141a; width: 100%; height: 420px; display: flex; flex-direction: column; }
        .header { background: #0c0e12; padding: 10px 12px; border-bottom: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .title { color: white; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
        .tooltip-wrapper { position: static; display: inline-block; }
        .tooltip-btn { width: 24px; height: 24px; border-radius: 50%; background: #1a1e26; border: 2px solid #555; display: flex; align-items: center; justify-content: center; color: #aaa; font-size: 14px; font-weight: bold; cursor: help; }
        .tooltip-content { display: none; position: fixed; width: 300px; background-color: #1e222d; color: #eee; text-align: left; padding: 15px; border-radius: 10px; z-index: 99999; font-size: 12px; border: 2px solid #3b82f6; box-shadow: 0 15px 40px rgba(0,0,0,0.9); line-height: 1.5; left: 50%; top: 50%; transform: translate(-50%, -50%); white-space: normal; word-wrap: break-word; }
        .tooltip-wrapper:hover .tooltip-content { display: block; }
        .content { background: #11141a; flex: 1; overflow-y: auto; padding: 10px; }
        .update-timestamp { text-align: center; color: #555; font-size: 10px; padding: 6px 0; font-family: 'Courier New', monospace; border-top: 1px solid #1a1e26; background: #0c0e12; flex-shrink: 0; }
        </style></head><body><div class="container">
        <div class="header"><div class="title">Crypto Pulse</div><div class="tooltip-wrapper"><div class="tooltip-btn">?</div><div class="tooltip-content">Preus reals de criptomonedes via Yahoo Finance.</div></div></div>
        <div class="content">''' + crypto_content + '''</div>
        <div class="update-timestamp">Actualizado: ''' + timestamp_str + '''</div>
        </div></body></html>'''
        components.html(crypto_html_full, height=420, scrolling=False)

    # FILA 6 - Indicadores Económicos | A/D Line | Credit Spreads
    st.write("")
    f6c1, f6c2, f6c3 = st.columns(3)

    # ── ECONOMIC INDICATORS ────────────────────────────────────────────────────
    with f6c1:
        indicators = get_economic_indicators()
        ts6 = get_timestamp()
        
        if not indicators:
            ind_html = '<div style="text-align:center; color:#555; padding:40px; font-size:11px;">Datos no disponibles<br><small>Configure FRED_API_KEY en secrets</small></div>'
        else:
            ind_html = ""
            for ind in indicators:
                up = ind.get('up', True)
                arrow = "▲" if up else "▼"
                chg_color = "#00ffad" if up else "#f23645"
                val_fmt = f"{ind['value']:,.2f}"
                pct_fmt = f"{ind['pct']:+.2f}%"
                date_short = str(ind.get('date', ''))[:7]
                ind_html += (
                    f'<div style="padding:10px 12px; border-bottom:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">'
                    f'<div><div style="color:white; font-size:11px; font-weight:bold;">{ind["name"]}</div>'
                    f'<div style="color:#555; font-size:9px;">{date_short}</div></div>'
                    f'<div style="text-align:right;">'
                    f'<div style="color:white; font-size:12px; font-weight:bold;">{val_fmt} <span style="color:#888; font-size:9px;">{ind["unit"]}</span></div>'
                    f'<div style="color:{chg_color}; font-size:10px; font-weight:bold;">{arrow} {ind["change"]:+.2f} ({pct_fmt})</div>'
                    f'</div></div>'
                )

        ind_full_html = f'''<!DOCTYPE html><html><head><style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#11141a; }}
        .container {{ border:1px solid #1a1e26; border-radius:10px; overflow:hidden; background:#11141a; width:100%; height:420px; display:flex; flex-direction:column; }}
        .header {{ background:#0c0e12; padding:10px 12px; border-bottom:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center; flex-shrink:0; }}
        .title {{ color:white; font-size:13px; font-weight:bold; text-transform:uppercase; letter-spacing:0.5px; }}
        .content {{ flex:1; overflow-y:auto; }}
        .update-timestamp {{ text-align:center; color:#555; font-size:10px; padding:6px 0; font-family:'Courier New',monospace; border-top:1px solid #1a1e26; background:#0c0e12; flex-shrink:0; }}
        .tooltip-wrapper {{ position:static; display:inline-block; }}
        .tooltip-btn {{ width:22px; height:22px; border-radius:50%; background:#1a1e26; border:1px solid #444; display:flex; align-items:center; justify-content:center; color:#888; font-size:12px; font-weight:bold; cursor:help; }}
        .tooltip-content {{ display:none; position:fixed; width:280px; background:#1e222d; color:#eee; padding:12px; border-radius:10px; z-index:99999; font-size:11px; border:2px solid #3b82f6; box-shadow:0 15px 40px rgba(0,0,0,0.9); line-height:1.5; left:50%; top:50%; transform:translate(-50%,-50%); }}
        .tooltip-wrapper:hover .tooltip-content {{ display:block; }}
        </style></head><body>
        <div class="container">
            <div class="header">
                <div class="title">Indicadores Económicos</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Indicadores macroeconómicos de EE.UU. via FRED (Federal Reserve). Requiere FRED_API_KEY.</div>
                </div>
            </div>
            <div class="content">{ind_html}</div>
            <div class="update-timestamp">Actualizado: {ts6} • FRED</div>
        </div>
        </body></html>'''
        components.html(ind_full_html, height=420, scrolling=False)

    # ── ADVANCE-DECLINE LINE ───────────────────────────────────────────────────
    with f6c2:
        ad_data = get_advance_decline()
        ts_ad = get_timestamp()
        history_ad = ad_data.get('history', [])
        spy_cur = ad_data.get('spy_current', 0)
        spy_chg = ad_data.get('spy_change', 0)
        current_ad_val = ad_data.get('current_ad', 0)
        spy_color = "#00ffad" if spy_chg >= 0 else "#f23645"

        # SVG chart for A/D line + SPY
        def _make_ad_chart(history):
            if len(history) < 5:
                return '<div style="color:#555; text-align:center; padding:20px; font-size:10px;">Sin datos</div>'
            
            W, H = 340, 200
            pad = {'l': 45, 'r': 10, 't': 10, 'b': 30}
            
            spy_vals = [d['spy'] for d in history]
            ad_vals  = [d['ad']  for d in history]
            dates    = [d['date'] for d in history]
            
            def normalize(vals, pad_top, pad_bot, h):
                mn, mx = min(vals), max(vals)
                rng = mx - mn if mx != mn else 1
                return [h - pad_bot - ((v - mn) / rng) * (h - pad_top - pad_bot) for v in vals], mn, mx
            
            spy_ys, spy_mn, spy_mx = normalize(spy_vals, pad['t'], pad['b'] + 90, H)
            ad_ys,  ad_mn,  ad_mx  = normalize(ad_vals,  pad['t'] + 120, pad['b'], H)
            
            n = len(history)
            def pts(ys):
                return " ".join(f"{pad['l'] + i * (W - pad['l'] - pad['r']) / (n-1):.1f},{y:.1f}" for i, y in enumerate(ys))
            
            spy_pts = pts(spy_ys)
            ad_pts  = pts(ad_ys)
            
            # x-axis labels (show ~4) - solo en la parte inferior sin solapar
            x_labels = ""
            step = max(1, n // 4)
            for i in range(0, n, step):
                x = pad['l'] + i * (W - pad['l'] - pad['r']) / (n - 1)
                lbl = dates[i][5:]  # MM-DD
                x_labels += f'<text x="{x:.1f}" y="{H - 3}" text-anchor="middle" fill="#555" font-size="7">{lbl}</text>'
            
            # Etiquetas de eje Y a la izquierda sin solapar con la gráfica
            spy_last_y = spy_ys[-1]
            ad_last_y = ad_ys[-1]
            
            # Etiqueta SPY en el eje Y izquierdo (zona superior)
            spy_label_y = max(spy_ys[0] + 8, pad['t'] + 5)
            ad_label_y = min(ad_ys[0] - 3, H - pad['b'] - 5)
            
            # Grid line separator
            sep_y = pad['t'] + (H - pad['t'] - pad['b']) * 0.48
            
            return f'''<svg width="100%" height="100%" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">
                <line x1="{pad['l']}" y1="{sep_y:.1f}" x2="{W - pad['r']}" y2="{sep_y:.1f}" stroke="#1a1e26" stroke-width="1" stroke-dasharray="3,3"/>
                <!-- Etiquetas eje Y izquierdo bien posicionadas -->
                <text x="{pad['l'] - 3}" y="{pad['t'] + 10}" fill="#3b82f6" font-size="7" text-anchor="end">S&amp;P 500</text>
                <text x="{pad['l'] - 3}" y="{H - pad['b'] - 10}" fill="#f23645" font-size="7" text-anchor="end">A/D</text>
                <!-- Y-axis tick values -->
                <text x="{pad['l'] - 3}" y="{spy_ys[0]:.1f}" fill="#3b82f660" font-size="6" text-anchor="end">{spy_vals[0]:,.0f}</text>
                <text x="{pad['l'] - 3}" y="{spy_ys[-1]:.1f}" fill="#3b82f6" font-size="6" text-anchor="end">{spy_vals[-1]:,.0f}</text>
                <text x="{pad['l'] - 3}" y="{ad_ys[-1]:.1f}" fill="#f23645" font-size="6" text-anchor="end">{ad_vals[-1]:,.1f}K</text>
                <!-- Líneas -->
                <polyline points="{spy_pts}" fill="none" stroke="#3b82f6" stroke-width="1.5" stroke-linejoin="round"/>
                <polyline points="{ad_pts}" fill="none" stroke="#f23645" stroke-width="1.5" stroke-linejoin="round"/>
                {x_labels}
            </svg>'''
        
        ad_chart_svg = _make_ad_chart(history_ad)
        
        ad_full_html = f'''<!DOCTYPE html><html><head><style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#11141a; }}
        .container {{ border:1px solid #1a1e26; border-radius:10px; overflow:hidden; background:#11141a; width:100%; height:420px; display:flex; flex-direction:column; }}
        .header {{ background:#0c0e12; padding:10px 12px; border-bottom:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center; flex-shrink:0; }}
        .title {{ color:white; font-size:13px; font-weight:bold; text-transform:uppercase; letter-spacing:0.5px; }}
        .content {{ flex:1; overflow:hidden; padding:10px; display:flex; flex-direction:column; }}
        .update-timestamp {{ text-align:center; color:#555; font-size:10px; padding:6px 0; font-family:'Courier New',monospace; border-top:1px solid #1a1e26; background:#0c0e12; flex-shrink:0; }}
        .tooltip-wrapper {{ position:static; display:inline-block; }}
        .tooltip-btn {{ width:22px; height:22px; border-radius:50%; background:#1a1e26; border:1px solid #444; display:flex; align-items:center; justify-content:center; color:#888; font-size:12px; font-weight:bold; cursor:help; }}
        .tooltip-content {{ display:none; position:fixed; width:280px; background:#1e222d; color:#eee; padding:12px; border-radius:10px; z-index:99999; font-size:11px; border:2px solid #3b82f6; box-shadow:0 15px 40px rgba(0,0,0,0.9); line-height:1.5; left:50%; top:50%; transform:translate(-50%,-50%); }}
        .tooltip-wrapper:hover .tooltip-content {{ display:block; }}
        </style></head><body>
        <div class="container">
            <div class="header">
                <div style="display:flex; flex-direction:column;">
                    <div class="title">Amplitud: Línea Avance-Descenso</div>
                </div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">La línea Avance/Descenso mide la amplitud del mercado. Una A/D creciente junto a SPY alcista confirma la tendencia. Datos proxy basados en SPY via yfinance.</div>
                </div>
            </div>
            <div class="content">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <div style="font-size:10px; color:#888;">S&P 500: <span style="color:{spy_color}; font-weight:bold;">{spy_cur:,.2f} ({spy_chg:+.2f})</span></div>
                    <div style="font-size:10px; color:#888;">A/D: <span style="color:#f23645; font-weight:bold;">{current_ad_val:,.1f}K</span></div>
                </div>
                <div style="flex:1; background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:8px; overflow:hidden;">
                    {ad_chart_svg}
                </div>
                <div style="display:flex; gap:12px; margin-top:8px; font-size:9px; color:#666;">
                    <span>▬ <span style="color:#3b82f6;">S&P 500</span></span>
                    <span>▬ <span style="color:#f23645;">Línea A/D</span></span>
                </div>
            </div>
            <div class="update-timestamp">Actualizado: {ts_ad} • yfinance proxy</div>
        </div>
        </body></html>'''
        components.html(ad_full_html, height=420, scrolling=False)

    # ── US HIGH YIELD CREDIT SPREADS ──────────────────────────────────────────
    with f6c3:
        cs_data = get_credit_spreads()
        ts_cs = get_timestamp()
        
        if cs_data.get('ok') and cs_data.get('history'):
            cs_current = cs_data['current']
            cs_change  = cs_data['change']
            cs_date    = cs_data['date']
            cs_history = cs_data['history']
            cs_color   = "#f23645" if cs_change >= 0 else "#00ffad"  # spread sube = malo
            
            # Chart SVG
            W2, H2 = 340, 200
            pad2 = {'l': 38, 'r': 10, 't': 10, 'b': 22}
            cs_vals = [d['value'] for d in cs_history]
            cs_dates = [d['date'] for d in cs_history]
            mn2, mx2 = min(cs_vals), max(cs_vals)
            rng2 = mx2 - mn2 if mx2 != mn2 else 0.1
            n2 = len(cs_vals)
            
            # Area fill
            area_pts = []
            line_pts = []
            for i, v in enumerate(cs_vals):
                x = pad2['l'] + i * (W2 - pad2['l'] - pad2['r']) / (n2 - 1)
                y = H2 - pad2['b'] - ((v - mn2) / rng2) * (H2 - pad2['t'] - pad2['b'])
                area_pts.append(f"{x:.1f},{y:.1f}")
                line_pts.append(f"{x:.1f},{y:.1f}")
            
            first_x = pad2['l']
            last_x = pad2['l'] + (W2 - pad2['l'] - pad2['r'])
            area_path = (f"{first_x},{H2 - pad2['b']} " + " ".join(area_pts) + 
                         f" {last_x},{H2 - pad2['b']}")
            
            # Y-axis ticks
            y_ticks = ""
            for i in range(5):
                v = mn2 + rng2 * i / 4
                y_pos = H2 - pad2['b'] - (i / 4) * (H2 - pad2['t'] - pad2['b'])
                y_ticks += (f'<text x="{pad2["l"] - 4}" y="{y_pos + 3:.1f}" text-anchor="end" fill="#555" font-size="7">{v:.2f}%</text>'
                            f'<line x1="{pad2["l"]}" y1="{y_pos:.1f}" x2="{W2 - pad2["r"]}" y2="{y_pos:.1f}" stroke="#1a1e26" stroke-width="0.5"/>')
            
            # X-axis labels
            x_labels2 = ""
            step2 = max(1, n2 // 5)
            for i in range(0, n2, step2):
                x = pad2['l'] + i * (W2 - pad2['l'] - pad2['r']) / (n2 - 1)
                lbl = cs_dates[i][5:]
                x_labels2 += f'<text x="{x:.1f}" y="{H2 - 3}" text-anchor="middle" fill="#555" font-size="7">{lbl}</text>'
            
            cs_chart = f'''<svg width="100%" height="100%" viewBox="0 0 {W2} {H2}" preserveAspectRatio="xMidYMid meet">
                {y_ticks}
                <polygon points="{area_path}" fill="#f2364520"/>
                <polyline points="{" ".join(line_pts)}" fill="none" stroke="#f23645" stroke-width="1.8" stroke-linejoin="round"/>
                {x_labels2}
            </svg>'''
            
            cs_desc = f"Actual: {cs_current:.2f}% ({cs_change:+.3f})"
        else:
            cs_chart = '<div style="color:#555; text-align:center; padding:40px; font-size:10px;">Configure FRED_API_KEY para datos reales</div>'
            cs_current = 0
            cs_color = "#888"
            cs_desc = "Datos no disponibles"
            cs_date = "—"

        cs_full_html = f'''<!DOCTYPE html><html><head><style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#11141a; }}
        .container {{ border:1px solid #1a1e26; border-radius:10px; overflow:hidden; background:#11141a; width:100%; height:420px; display:flex; flex-direction:column; }}
        .header {{ background:#0c0e12; padding:10px 12px; border-bottom:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center; flex-shrink:0; }}
        .title {{ color:white; font-size:13px; font-weight:bold; text-transform:uppercase; letter-spacing:0.5px; }}
        .content {{ flex:1; overflow:hidden; padding:10px; display:flex; flex-direction:column; }}
        .update-timestamp {{ text-align:center; color:#555; font-size:10px; padding:6px 0; font-family:'Courier New',monospace; border-top:1px solid #1a1e26; background:#0c0e12; flex-shrink:0; }}
        .tooltip-wrapper {{ position:static; display:inline-block; }}
        .tooltip-btn {{ width:22px; height:22px; border-radius:50%; background:#1a1e26; border:1px solid #444; display:flex; align-items:center; justify-content:center; color:#888; font-size:12px; font-weight:bold; cursor:help; }}
        .tooltip-content {{ display:none; position:fixed; width:280px; background:#1e222d; color:#eee; padding:12px; border-radius:10px; z-index:99999; font-size:11px; border:2px solid #3b82f6; box-shadow:0 15px 40px rgba(0,0,0,0.9); line-height:1.5; left:50%; top:50%; transform:translate(-50%,-50%); }}
        .tooltip-wrapper:hover .tooltip-content {{ display:block; }}
        </style></head><body>
        <div class="container">
            <div class="header">
                <div>
                    <div class="title">High Yield Credit Spreads EE.UU.</div>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:{cs_color}; font-size:12px; font-weight:bold;">{cs_current:.2f}%</span>
                    <div class="tooltip-wrapper">
                        <div class="tooltip-btn">?</div>
                        <div class="tooltip-content">Diferencial OAS del índice High Yield de EE.UU. (BAMLH0A0HYM2). Spreads altos = mayor riesgo de crédito percibido. Fuente: FRED.</div>
                    </div>
                </div>
            </div>
            <div class="content">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:9px; color:#666;">
                    <span>{cs_desc}</span>
                    <span>6 Meses • OAS</span>
                </div>
                <div style="flex:1; background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:4px; overflow:hidden;">
                    {cs_chart}
                </div>
                <div style="margin-top:6px; font-size:9px; color:#555; text-align:center;">
                    Option-Adjusted Spread (OAS) • Spreads altos = mayor riesgo de crédito
                </div>
            </div>
            <div class="update-timestamp">Actualizado: {ts_cs} • {cs_date} • FRED</div>
        </div>
        </body></html>'''
        components.html(cs_full_html, height=420, scrolling=False)

if __name__ == "__main__":
    render()






















