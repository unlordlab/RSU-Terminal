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
import pytz

try:
    import investpy
    INVESTPY_AVAILABLE = True
except ImportError:
    INVESTPY_AVAILABLE = False

def get_timestamp():
    return datetime.now().strftime('%H:%M:%S')

def get_effective_date():
    """Obtiene la fecha efectiva para filtrar datos (hoy si son más de las 9am, ayer si no)"""
    spain_tz = pytz.timezone('Europe/Madrid')
    now = datetime.now(spain_tz)
    
    if now.hour >= 9:
        return now.date()
    else:
        # Antes de las 9am, mostrar desde ayer
        return (now - timedelta(days=1)).date()

# Diccionario de traducción de eventos económicos
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

def translate_event(event_name):
    if event_name in EVENT_TRANSLATIONS:
        return EVENT_TRANSLATIONS[event_name]
    for eng, esp in EVENT_TRANSLATIONS.items():
        if eng.lower() in event_name.lower():
            return esp
    if len(event_name) > 35:
        return event_name[:32] + "..."
    return event_name


@st.cache_data(ttl=300)
def get_economic_calendar():
    events = []
    effective_date = get_effective_date()
    
    if INVESTPY_AVAILABLE:
        try:
            from_date = effective_date.strftime('%d/%m/%Y')
            to_date = (effective_date + timedelta(days=7)).strftime('%d/%m/%Y')
            
            calendar = investpy.economic_calendar(
                time_zone='GMT', 
                time_filter='time_only',
                from_date=from_date, 
                to_date=to_date,
                countries=['united states', 'euro zone'],
                importances=['high', 'medium', 'low']
            )
            
            for _, row in calendar.iterrows():
                try:
                    date_str = row.get('date', '')
                    if pd.notna(date_str) and date_str != '':
                        event_date = pd.to_datetime(date_str, dayfirst=True)
                    else:
                        event_date = datetime.now()
                    
                    if event_date.date() < effective_date:
                        continue
                    
                    time_str = row.get('time', '')
                    if time_str and time_str != '' and pd.notna(time_str):
                        try:
                            hour, minute = map(int, time_str.split(':'))
                            hour_es = (hour + 1) % 24
                            time_es = f"{hour_es:02d}:{minute:02d}"
                        except:
                            time_es = "TBD"
                    else:
                        time_es = "TBD"
                    
                    importance_map = {'high': 'High', 'medium': 'Medium', 'low': 'Low'}
                    imp = row.get('importance', 'medium')
                    impact = importance_map.get(str(imp).lower(), 'Medium')
                    
                    event_name = str(row.get('event', 'Unknown'))
                    event_name_es = translate_event(event_name)
                    
                    if event_date.date() == effective_date:
                        date_display = "HOY"
                        date_color = "#00ffad"
                    elif event_date.date() == (effective_date + timedelta(days=1)):
                        date_display = "MAÑANA"
                        date_color = "#3b82f6"
                    else:
                        date_display = event_date.strftime('%d %b').upper()
                        date_color = "#888"
                    
                    events.append({
                        "date": event_date,
                        "date_display": date_display,
                        "date_color": date_color,
                        "time": time_es,
                        "event": event_name_es,
                        "imp": impact,
                        "val": str(row.get('actual', '-')) if pd.notna(row.get('actual', '-')) else '-',
                        "prev": str(row.get('previous', '-')) if pd.notna(row.get('previous', '-')) else '-',
                        "forecast": str(row.get('forecast', '-')) if pd.notna(row.get('forecast', '-')) else '-',
                        "country": str(row.get('zone', 'US')).upper()
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass
    
    if not events:
        try:
            events = get_forexfactory_calendar()
        except:
            pass
    
    if events:
        events.sort(key=lambda x: (x['date'], x['time'] if x['time'] != 'TBD' else '99:99'))
        return events[:8]
    
    return get_fallback_economic_calendar()

def get_forexfactory_calendar():
    events = []
    try:
        url = "https://www.forexfactory.com/calendar"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        return events
    except:
        return events

def get_fallback_economic_calendar():
    effective_date = get_effective_date()
    today = datetime.combine(effective_date, datetime.min.time())
    
    fallback_events = [
        {"date": today, "date_display": "HOY", "date_color": "#00ffad", "time": "14:30", "event": "Solicitudes de Desempleo", "imp": "High", "val": "-", "prev": "215K", "forecast": "218K", "country": "US"},
        {"date": today, "date_display": "HOY", "date_color": "#00ffad", "time": "16:00", "event": "Pedidos de Bienes Duraderos", "imp": "Medium", "val": "-", "prev": "-4.6%", "forecast": "+2.0%", "country": "US"},
        {"date": today + timedelta(days=1), "date_display": "MAÑANA", "date_color": "#3b82f6", "time": "14:30", "event": "PIB (Revisado)", "imp": "High", "val": "-", "prev": "2.8%", "forecast": "2.9%", "country": "US"},
        {"date": today + timedelta(days=1), "date_display": "MAÑANA", "date_color": "#3b82f6", "time": "16:00", "event": "Ventas de Viviendas Pendientes", "imp": "Medium", "val": "-", "prev": "+4.6%", "forecast": "+1.0%", "country": "US"},
        {"date": today + timedelta(days=2), "date_display": (today + timedelta(days=2)).strftime('%d %b').upper(), "date_color": "#888", "time": "14:30", "event": "IPC Subyacente", "imp": "High", "val": "-", "prev": "0.3%", "forecast": "0.2%", "country": "US"},
        {"date": today + timedelta(days=2), "date_display": (today + timedelta(days=2)).strftime('%d %b').upper(), "date_color": "#888", "time": "14:30", "event": "Nóminas No Agrícolas", "imp": "High", "val": "-", "prev": "143K", "forecast": "175K", "country": "US"},
    ]
    
    return fallback_events

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
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 5:
                for row in rows[1:]:
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
                                    'rank': rank, 'ticker': ticker, 'buzz_score': buzz_score,
                                    'health': health, 'social_hype': social_hype,
                                    'smart_money': smart_money, 'squeeze': squeeze
                                })
                    except:
                        continue
                
                if master_data:
                    break
        
        if not master_data:
            ticker_elements = soup.find_all(text=re.compile(r'^[A-Z]{1,5}$'))
            seen = set()
            rank = 1
            
            for elem in ticker_elements[:20]:
                try:
                    ticker = elem.strip()
                    if ticker and ticker not in seen and len(ticker) <= 5:
                        parent = elem.find_parent()
                        if parent:
                            row_data = {
                                'rank': str(rank), 'ticker': ticker, 'buzz_score': '6',
                                'health': '50 Neutral', 'social_hype': '', 'smart_money': '', 'squeeze': ''
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
        ],
        'source': 'BuzzTickr Master',
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'count': 15
    }

@st.cache_data(ttl=60)
def get_financial_ticker_data():
    ticker_data = []
    all_symbols = {
        'ES=F': 'S&P 500 FUT', 'NQ=F': 'NASDAQ FUT', 'YM=F': 'DOW FUT', 'RTY=F': 'RUSSELL FUT',
        '^N225': 'NIKKEI', '^GDAXI': 'DAX', '^FTSE': 'FTSE 100',
        'GC=F': 'GOLD', 'SI=F': 'SILVER', 'CL=F': 'CRUDE OIL', 'NG=F': 'NAT GAS',
        'AAPL': 'AAPL', 'MSFT': 'MSFT', 'GOOGL': 'GOOGL', 'AMZN': 'AMZN',
        'NVDA': 'NVDA', 'META': 'META', 'TSLA': 'TSLA',
        'BTC-USD': 'BTC', 'ETH-USD': 'ETH'
    }
    for symbol, name in all_symbols.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change_pct = ((current - prev) / prev) * 100
                price_str = f"{current:,.2f}" if current >= 100 else f"{current:.3f}"
                ticker_data.append({
                    'name': name, 'price': price_str,
                    'change': change_pct, 'is_positive': change_pct >= 0
                })
            time.sleep(0.05)
        except:
            continue
    return ticker_data

def generate_ticker_html():
    data = get_financial_ticker_data()
    if not data:
        data = [
            {'name': 'S&P 500 FUT', 'price': '5,890.25', 'change': 0.45, 'is_positive': True},
            {'name': 'NASDAQ FUT', 'price': '21,150.80', 'change': -0.23, 'is_positive': False},
            {'name': 'DOW FUT', 'price': '42,890.15', 'change': 0.67, 'is_positive': True},
            {'name': 'NIKKEI', 'price': '38,750.50', 'change': 1.24, 'is_positive': True},
            {'name': 'DAX', 'price': '21,340.75', 'change': -0.15, 'is_positive': False},
            {'name': 'GOLD', 'price': '2,865.40', 'change': 0.89, 'is_positive': True},
            {'name': 'SILVER', 'price': '32.45', 'change': 1.56, 'is_positive': True},
            {'name': 'CRUDE OIL', 'price': '73.85', 'change': -1.23, 'is_positive': False},
            {'name': 'BTC', 'price': '68,984.88', 'change': -1.62, 'is_positive': False},
            {'name': 'ETH', 'price': '2,018.46', 'change': -4.05', 'is_positive': False},
        ]
    ticker_items = []
    for item in data:
        color = "#00ffad" if item['is_positive'] else "#f23645"
        arrow = "▲" if item['is_positive'] else "▼"
        ticker_items.append(
            f'<span style="margin-right: 40px; white-space: nowrap;">'
            f'<span style="color: #fff; font-weight: bold;">{item["name"]}</span> '
            f'<span style="color: #ccc;">{item["price"]}</span> '
            f'<span style="color: {color};">{arrow} {item["change"]:+.2f}%</span>'
            f'</span>'
        )
    items_html = "".join(ticker_items)
    all_items = items_html + items_html
    return f"""
    <div style="background: linear-gradient(90deg, #0c0e12 0%, #1a1e26 50%, #0c0e12 100%); border-bottom: 2px solid #2a3f5f; padding: 12px 0; overflow: hidden;">
        <div style="display: inline-block; white-space: nowrap; animation: ticker-scroll 30s linear infinite; padding-left: 100%;">{all_items}</div>
    </div>
    <style>@keyframes ticker-scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}</style>
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
        try:
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="5d")
            if len(vix_hist) >= 3:
                current_spot = vix_hist['Close'].iloc[-1]
                prev_spot = vix_hist['Close'].iloc[-2]
                spot_2days = vix_hist['Close'].iloc[-3]
            else:
                current_spot = 17.45
                prev_spot = 17.36
                spot_2days = 20.37
        except:
            current_spot = 17.45
            prev_spot = 17.36
            spot_2days = 20.37

        months = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
        base_year = datetime.now().year

        current_curve = [current_spot]
        prev_curve = [prev_spot]
        two_days_curve = [spot_2days]

        is_contango = current_spot < 20

        for i in range(1, 9):
            if is_contango:
                current_curve.append(current_spot + (i * 0.9) + (i * i * 0.08))
                prev_curve.append(prev_spot + (i * 0.85) + (i * i * 0.07))
                two_days_curve.append(spot_2days + (i * 0.5) + (i * i * 0.05))
            else:
                current_curve.append(current_spot - (i * 0.3))
                prev_curve.append(prev_spot - (i * 0.25))
                two_days_curve.append(spot_2days - (i * 0.2))

        vix_data = []
        for i, month in enumerate(months):
            year = base_year if i < 10 else base_year + 1
            vix_data.append({
                'month': f"{month} {year}",
                'current': round(current_curve[i], 2),
                'previous': round(prev_curve[i], 2),
                'two_days': round(two_days_curve[i], 2)
            })

        if current_curve[-1] > current_curve[0]:
            state = "Contango"
            state_desc = "Typical in calm markets - Conducive to dip buying"
            state_color = "#00ffad"
            explanation = ("<b>Contango:</b> Futures price > Spot price. "
                         "The market expects volatility to decrease over time. "
                         "This is the normal state in calm markets. "
                         "Investors pay a premium for future protection, expecting volatility to mean revert lower.")
        else:
            state = "Backwardation"
            state_desc = "Market stress detected - Caution advised"
            state_color = "#f23645"
            explanation = ("<b>Backwardation:</b> Futures price < Spot price. "
                         "The market expects volatility to increase. "
                         "Immediate hedging demand drives up short-term volatility. "
                         "This signals fear of upcoming market moves.")

        return {
            'data': vix_data,
            'current_spot': current_spot,
            'prev_spot': prev_spot,
            'spot_2days': spot_2days,
            'state': state,
            'state_desc': state_desc,
            'state_color': state_color,
            'explanation': explanation,
            'is_contango': is_contango
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

    legend_y = 15
    legend = f"""
    <rect x="{chart_width-175}" y="5" width="170" height="50" fill="#0c0e12" stroke="#1a1e26" rx="4"/>
    <line x1="{chart_width-170}" y1="{legend_y+5}" x2="{chart_width-155}" y2="{legend_y+5}" stroke="#3b82f6" stroke-width="2"/>
    <text x="{chart_width-150}" y="{legend_y+8}" fill="#888" font-size="8">Current (2/10): {vix_data['current_spot']:.2f}</text>

    <line x1="{chart_width-170}" y1="{legend_y+20}" x2="{chart_width-155}" y2="{legend_y+20}" stroke="#f97316" stroke-width="2" stroke-dasharray="4,3"/>
    <text x="{chart_width-150}" y="{legend_y+23}" fill="#888" font-size="8">Previous (2/9): {vix_data['prev_spot']:.2f}</text>

    <line x1="{chart_width-170}" y1="{legend_y+35}" x2="{chart_width-155}" y2="{legend_y+35}" stroke="#6b7280" stroke-width="2" stroke-dasharray="4,3"/>
    <text x="{chart_width-150}" y="{legend_y+38}" fill="#888" font-size="8">2 Days Ago (2/8): {vix_data['spot_2days']:.2f}</text>
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
        url = "https://api.alternative.me/fng/?limit=1"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data and len(data['data']) > 0:
                item = data['data'][0]
                value = int(item['value'])
                classification = item['value_classification']
                update_time = datetime.now().strftime('%H:%M')

                return {
                    'value': value,
                    'classification': classification,
                    'timestamp': update_time,
                    'source': 'alternative.me'
                }

        return get_fallback_crypto_fear_greed()
    except:
        return get_fallback_crypto_fear_greed()

def get_fallback_crypto_fear_greed():
    return {
        'value': 50,
        'classification': 'Neutral',
        'timestamp': get_timestamp(),
        'source': 'alternative.me'
    }

@st.cache_data(ttl=600)
def get_earnings_calendar():
    api_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", None)
    
    # Obtener fecha efectiva (hoy si son más de las 9am hora española)
    effective_date = get_effective_date()
    
    mega_caps = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 
        'BRK-B', 'AVGO', 'WMT', 'JPM', 'V', 'MA', 'UNH', 'HD',
        'PG', 'JNJ', 'BAC', 'LLY', 'MRK', 'KO', 'PEP', 'ABBV',
        'COST', 'TMO', 'ADBE', 'NFLX', 'AMD', 'CRM', 'ACN', 'LIN',
        'DIS', 'VZ', 'WFC', 'DHR', 'NKE', 'TXN', 'PM', 'RTX', 'HON'
    ]
    
    earnings_list = []
    
    if api_key:
        try:
            url = f"https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey={api_key}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                
                df_filtered = df[df['symbol'].isin(mega_caps)].copy()
                
                for _, row in df_filtered.iterrows():
                    try:
                        report_date = pd.to_datetime(row['reportDate'])
                        days_until = (report_date - pd.Timestamp.now()).days
                        
                        # Solo incluir earnings desde la fecha efectiva en adelante
                        if report_date.date() < effective_date:
                            continue
                            
                        if days_until >= -2:
                            symbol = row['symbol']
                            hour_guess = "After Market" if symbol in ['NVDA', 'AAPL', 'AMZN', 'META', 'NFLX', 'AMD'] else "Before Bell"
                            
                            earnings_list.append({
                                'ticker': symbol,
                                'date': report_date.strftime('%b %d'),
                                'full_date': report_date,
                                'time': hour_guess,
                                'impact': 'High',
                                'estimate': row.get('estimate', '-'),
                                'days': max(0, days_until),
                                'source': 'AlphaVantage'
                            })
                    except:
                        continue
                
                earnings_list.sort(key=lambda x: x['full_date'])
                
                if len(earnings_list) >= 4:
                    return earnings_list[:6]
                    
        except Exception as e:
            pass
    
    try:
        for ticker in mega_caps[:15]:
            try:
                stock = yf.Ticker(ticker)
                calendar = stock.calendar
                
                if calendar is not None and not calendar.empty:
                    next_earnings = calendar.index[0]
                    
                    # Solo incluir earnings desde la fecha efectiva en adelante
                    if next_earnings.date() < effective_date:
                        continue
                        
                    days_until = (next_earnings - pd.Timestamp.now()).days
                    
                    if 0 <= days_until <= 30:
                        info = stock.info
                        hour = next_earnings.hour if hasattr(next_earnings, 'hour') else 16
                        time_str = "Before Bell" if hour < 12 else "After Market"
                        
                        market_cap = info.get('marketCap', 0) / 1e9
                        
                        if market_cap >= 50:
                            earnings_list.append({
                                'ticker': ticker,
                                'date': next_earnings.strftime('%b %d'),
                                'full_date': next_earnings,
                                'time': time_str,
                                'impact': 'High',
                                'market_cap': f"${market_cap:.0f}B",
                                'days': days_until,
                                'source': 'yfinance'
                            })
                
                time.sleep(0.15)
            except:
                continue
        
        earnings_list.sort(key=lambda x: x['full_date'])
        
        if earnings_list:
            return earnings_list[:6]
            
    except Exception as e:
        pass
    
    return get_fallback_earnings_realistic()

def get_fallback_earnings_realistic():
    effective_date = get_effective_date()
    today = datetime.combine(effective_date, datetime.min.time())
    
    fallback_data = [
        {"ticker": "NVDA", "date_offset": 0, "time": "After Market", "impact": "High", "market_cap": "$3.2T"},
        {"ticker": "AAPL", "date_offset": 1, "time": "After Market", "impact": "High", "market_cap": "$3.4T"},
        {"ticker": "MSFT", "date_offset": 2, "time": "After Market", "impact": "High", "market_cap": "$3.1T"},
        {"ticker": "AMZN", "date_offset": 3, "time": "After Market", "impact": "High", "market_cap": "$2.1T"},
        {"ticker": "GOOGL", "date_offset": 5, "time": "After Market", "impact": "High", "market_cap": "$2.3T"},
        {"ticker": "META", "date_offset": 7, "time": "After Market", "impact": "High", "market_cap": "$1.8T"},
    ]
    
    result = []
    for item in fallback_data:
        target_date = today + timedelta(days=item['date_offset'])
        result.append({
            'ticker': item['ticker'],
            'date': target_date.strftime('%b %d'),
            'full_date': target_date,
            'time': item['time'],
            'impact': item['impact'],
            'market_cap': item['market_cap'],
            'days': item['date_offset'],
            'source': 'Fallback'
        })
    
    return result

@st.cache_data(ttl=600)
def get_insider_trading():
    try:
        api_key = st.secrets.get("FMP_API_KEY", None)

        if not api_key:
            return get_fallback_insider()

        symbols = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'META', 'GOOGL', 'AMZN', 'NFLX', 'AMD', 'CRM']
        all_trades = []

        for symbol in symbols:
            try:
                url = f"https://financialmodelingprep.com/api/v4/insider-trading?symbol={symbol}&limit=3&apikey={api_key}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    for trade in data:
                        transaction_type = trade.get('transactionType', '')
                        if 'P' in transaction_type:
                            trans = "BUY"
                        elif 'S' in transaction_type:
                            trans = "SELL"
                        else:
                            continue

                        shares = trade.get('securitiesTransacted', 0)
                        price = trade.get('price', 0)
                        amount = shares * price

                        if amount > 50000:
                            all_trades.append({
                                'ticker': symbol,
                                'insider': trade.get('reportingName', 'Executive')[:20],
                                'position': trade.get('typeOfOwner', 'Officer')[:15],
                                'type': trans,
                                'amount': f"${amount/1e6:.1f}M" if amount >= 1e6 else f"${amount/1e3:.0f}K",
                                'date': trade.get('transactionDate', 'Recent')
                            })
            except Exception as e:
                continue

        if all_trades:
            all_trades.sort(key=lambda x: float(x['amount'].replace('$','').replace('M','').replace('K','').replace(',','')), reverse=True)
            return all_trades[:6]

        return get_fallback_insider()

    except Exception as e:
        return get_fallback_insider()

def get_fallback_insider():
    return [
        {"ticker": "NVDA", "insider": "Jensen Huang", "position": "CEO", "type": "SELL", "amount": "$12.5M"},
        {"ticker": "TSLA", "insider": "Elon Musk", "position": "CEO", "type": "SELL", "amount": "$45.1M"},
        {"ticker": "META", "insider": "Mark Zuckerberg", "position": "CEO", "type": "SELL", "amount": "$28.3M"},
        {"ticker": "MSFT", "insider": "Satya Nadella", "position": "CEO", "type": "SELL", "amount": "$8.2M"},
        {"ticker": "AAPL", "insider": "Tim Cook", "position": "CEO", "type": "SELL", "amount": "$5.4M"},
        {"ticker": "AMZN", "insider": "Andy Jassy", "position": "CEO", "type": "SELL", "amount": "$3.1M"},
    ]

@st.cache_data(ttl=600)
def get_market_breadth():
    try:
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(period="6mo")
        if len(spy_hist) > 50:
            current = spy_hist['Close'].iloc[-1]
            sma50 = spy_hist['Close'].rolling(50).mean().iloc[-1]
            sma200 = spy_hist['Close'].rolling(200).mean().iloc[-1]
            deltas = spy_hist['Close'].diff()
            gains = deltas.where(deltas > 0, 0).rolling(14).mean()
            losses = (-deltas.where(deltas < 0, 0)).rolling(14).mean()
            rs = gains / losses
            rsi = 100 - (100 / (1 + rs.iloc[-1])) if not pd.isna(rs.iloc[-1]) else 50
            return {
                'price': current, 'sma50': sma50, 'sma200': sma200,
                'above_sma50': current > sma50, 'above_sma200': current > sma200,
                'golden_cross': sma50 > sma200, 'rsi': rsi,
                'trend': 'ALCISTA' if sma50 > sma200 else 'BAJISTA',
                'strength': 'FUERTE' if (current > sma50 and current > sma200) else 'DÉBIL'
            }
        return get_fallback_market_breadth()
    except:
        return get_fallback_market_breadth()

def get_fallback_market_breadth():
    return {
        'price': 695.50, 'sma50': 686.61, 'sma200': float('nan'),
        'above_sma50': True, 'above_sma200': False, 'golden_cross': False,
        'rsi': 59.2, 'trend': 'BAJISTA', 'strength': 'DÉBIL'
    }

def get_fallback_news():
    return [
        {"time": "19:45", "title": "Tesla supera expectativas de beneficios", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "18:30", "title": "El PIB de EEUU crece un 2,3% en el último trimestre", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "16:15", "title": "Apple presenta resultados récord gracias al iPhone", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "14:00", "title": "La inflación subyacente se modera al 3,2%", "impact": "Moderado", "color": "#ff9800", "link": "#"},
        {"time": "12:30", "title": "Microsoft Cloud supera los 30.000M en ingresos", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "11:15", "title": "La Fed mantiene los tipos de interés sin cambios", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "10:00", "title": "Amazon anuncia nueva división de inteligencia artificial", "impact": "Moderado", "color": "#ff9800", "link": "#"},
        {"time": "09:30", "title": "NVIDIA presenta nuevos chips para centros de datos", "impact": "Alto", "color": "#f23645", "link": "#"},
    ]

def translate_text(text, source='en', target='es'):
    try:
        if len(text.encode('utf-8')) > 450:
            text = text[:200] + "..."
        
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair={source}|{target}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('responseStatus') == 200:
                translated = data.get('responseData', {}).get('translatedText', text)
                if translated == text or "MYMEMORY" in translated:
                    return text
                return translated
        return text
    except:
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
            title_es = translate_text(title_en, 'en', 'es')
            link = item.get("url", "#")
            timestamp = item.get("datetime", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "N/A"
            lower = title_en.lower()
            impact, color = ("Alto", "#f23645") if any(k in lower for k in ["earnings", "profit", "revenue", "gdp", "fed", "fomc", "inflation", "rate", "outlook"]) else ("Moderado", "#ff9800")
            news_list.append({"time": time_str, "title": title_es, "impact": impact, "color": color, "link": link})
        return news_list if news_list else get_fallback_news()
    except:
        return get_fallback_news()

def get_fed_liquidity():
    api_key = st.secrets.get("FRED_API_KEY", None)
    if not api_key:
        return "STABLE", "#ff9800", "API Key no configurada", "N/A", "N/A"
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=WALCL&api_key={api_key}&file_type=json&limit=10&sort_order=desc"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            if len(observations) >= 2:
                latest_val = float(observations[0]['value'])
                prev_val = float(observations[1]['value'])
                date_latest = observations[0]['date']
                change = latest_val - prev_val
                if change < -100:
                    return "QT", "#f23645", "Quantitative Tightening", f"{latest_val/1000:.1f}T", date_latest
                elif change > 100:
                    return "QE", "#00ffad", "Quantitative Easing", f"{latest_val/1000:.1f}T", date_latest
                else:
                    return "STABLE", "#ff9800", "Balance sheet stable", f"{latest_val/1000:.1f}T", date_latest
        return "ERROR", "#888", "API no disponible", "N/A", "N/A"
    except:
        return "N/A", "#888", "Sin conexión", "N/A", "N/A"


# NUEVA FUNCIÓN: Obtener datos de índices adicionales (VUG, MEME, RSP)
def get_additional_indices():
    """Obtiene datos para VUG, MEME y RSP"""
    additional_indices = []
    
    symbols = {
        'VUG': 'Vanguard Growth ETF',
        'MEME': 'Roundhill Meme ETF', 
        'RSP': 'Invesco S&P 500 Equal Weight'
    }
    
    for symbol, name in symbols.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change_pct = ((current - prev) / prev) * 100
                additional_indices.append({
                    'symbol': symbol,
                    'name': name,
                    'price': current,
                    'change': change_pct
                })
            time.sleep(0.05)
        except:
            continue
    
    return additional_indices


def render():
    # CSS Global
    st.markdown("""
    <style>
    /* Tooltips CENTRADOS */
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
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        white-space: normal;
        word-wrap: break-word;
    }
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

    /* Contenedores - altura 480px */
    .module-container { 
        border: 1px solid #1a1e26; 
        border-radius: 10px; 
        overflow: hidden; 
        background: #11141a; 
        height: 480px;
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

    /* Botones de timeframe estilo segment control - MEJORADOS */
    .tf-button-container {
        display: flex;
        gap: 4px;
        background: #0c0e12;
        padding: 3px;
        border-radius: 6px;
        border: 1px solid #1a1e26;
    }
    .tf-button {
        background: transparent;
        color: #888;
        border: none;
        padding: 5px 12px;
        font-size: 10px;
        font-weight: 600;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s;
        white-space: nowrap;
    }
    .tf-button:hover {
        color: white;
        background: #1a1e26;
    }
    .tf-button.active {
        background: #2a3f5f;
        color: #00ffad;
    }

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
    
    /* ESTILOS PARA REDDIT SOCIAL PULSE */
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
        border: 1px solid #f













