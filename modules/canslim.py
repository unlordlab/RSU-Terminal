# -*- coding: utf-8 -*-
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from io import BytesIO
import base64
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURACIÓN DE PÁGINA Y CSS
# ============================================================

def get_timestamp():
    return datetime.now().strftime('%H:%M:%S')

def hex_to_rgba(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

# ============================================================
# OBTENER COMPONENTES DE ÍNDICES (EXPANDIDO)
# ============================================================

@st.cache_data(ttl=3600)
def get_sp500_tickers():
    """Obtiene los tickers del S&P 500 desde Wikipedia"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url)
        df = tables[0]
        return df['Symbol'].tolist()
    except:
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'AVGO', 'WMT']

@st.cache_data(ttl=3600)
def get_nasdaq100_tickers():
    """Obtiene los tickers del NASDAQ 100"""
    try:
        url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
        tables = pd.read_html(url)
        for table in tables:
            if 'Ticker' in table.columns:
                return table['Ticker'].tolist()
    except:
        pass
    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'PEP', 'COST']

@st.cache_data(ttl=3600)
def get_russell2000_tickers():
    """Obtiene Russell 2000 desde ETF (IWM) holdings"""
    try:
        # Usar los holdings del ETF IWM como proxy
        iwm = yf.Ticker("IWM")
        holdings = iwm.institutional_holders
        if holdings is not None:
            return holdings.index.tolist()[:1000]
    except:
        pass

    # Fallback: lista diversificada de small-caps
    return ['IWM', 'TNA', 'TZA', 'UWM', 'SRTY', 'VTWO', 'IWO', 'IWN', 'AMC', 'GME', 
            'BB', 'NOK', 'PLTR', 'SOFI', 'LCID', 'RIVN', 'SPCE', 'NKLA', 'MULN', 'HOOD',
            'AFRM', 'UPST', 'RBLX', 'U', 'DOCN', 'ASAN', 'MDB', 'NET', 'CRWD', 'OKTA',
            'ZS', 'S', 'PANW', 'FTNT', 'CYBR', 'QLYS', 'VRNS', 'TENB', 'SPLK', 'DDOG',
            'ESTC', 'FSLY', 'CLOV', 'WISH', 'CONTEXT', 'ROOT', 'METC', 'HUT', 'RIOT', 
            'MARA', 'BITF', 'CLSK', 'ARBK', 'CORZ', 'BTBT', 'SDIG', 'WULF', 'IREN', 
            'DMGI', 'HIVE', 'GLXY', 'COIN', 'LMND', 'HIPO', 'OSCR', 'PLTK', 'PLAY', 
            'CHUY', 'BOJA', 'TAST', 'FRGI', 'GTIM', 'PBPB', 'LOCO', 'SHAK', 'CMG', 
            'MCD', 'YUM', 'DRI', 'TXRH', 'CBRL', 'EAT', 'BJRI', 'WING', 'DENN', 'BRI',
            'ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX', 'ICLN', 'QCLN', 'PBW', 'TAN',
            'LIT', 'BATT', 'URA', 'NLR', 'CGW', 'PHO', 'FIW', 'CGW', 'EGLE', 'GASS',
            'GLBS', 'GNK', 'GOGL', 'NMM', 'SBLK', 'SHIP', 'TNP', 'ASC', 'NAT', 'OSG',
            'TK', 'TNK', 'TRMD', 'INSW', 'DSSI', 'STNG', 'LPG', 'PXS', 'PXSAP', 'PXSAW']

@st.cache_data(ttl=3600)
def get_additional_universe():
    """Stocks adicionales de alto crecimiento"""
    growth_etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ICLN', 'QCLN']
    meme_stocks = ['AMC', 'GME', 'BB', 'NOK', 'PLTR', 'SOFI', 'HOOD', 'AFRM', 'UPST']
    crypto_stocks = ['COIN', 'MSTR', 'RIOT', 'MARA', 'HUT', 'BITF', 'CLSK', 'ARBK']
    ev_stocks = ['TSLA', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'FSR', 'GOEV', 'WKHS']

    return growth_etfs + meme_stocks + crypto_stocks + ev_stocks

@st.cache_data(ttl=3600)
def get_all_universe_tickers():
    """Combina todos los universos - Expandido a ~1500 stocks"""
    sp500 = get_sp500_tickers()
    nasdaq = get_nasdaq100_tickers()
    russell = get_russell2000_tickers()
    additional = get_additional_universe()

    # Combinar y eliminar duplicados manteniendo orden de prioridad
    all_tickers = []
    seen = set()

    for ticker in sp500 + nasdaq + russell + additional:
        if ticker not in seen and len(ticker) <= 5:  # Filtrar tickers válidos
            all_tickers.append(ticker)
            seen.add(ticker)

    return all_tickers[:1500]  # Limitar a 1500 para rendimiento

# ============================================================
# ANÁLISIS DE MERCADO (M - MARKET DIRECTION)
# ============================================================

def analyze_market_direction():
    """Analiza la dirección del mercado usando múltiples índices"""
    try:
        indices = {
            'SPY': 'S&P 500',
            'QQQ': 'NASDAQ 100', 
            'IWM': 'Russell 2000',
            'VIX': 'Volatilidad',
            'DIA': 'Dow Jones'
        }

        market_data = {}
        bullish_count = 0
        bearish_count = 0

        for ticker, name in indices.items():
            try:
                if ticker == 'VIX':
                    data = yf.Ticker(ticker).history(period="20d")
                    current = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-5]
                    change = ((current - prev) / prev) * 100
                    # VIX inverso: subida = miedo (bearish)
                    signal = 'BEARISH' if change > 10 else 'BULLISH' if change < -10 else 'NEUTRAL'
                else:
                    data = yf.Ticker(ticker).history(period="20d")
                    current = data['Close'].iloc[-1]
                    sma20 = data['Close'].rolling(20).mean().iloc[-1]
                    sma50 = data['Close'].rolling(50).mean().iloc[-1] if len(data) >= 50 else sma20

                    price_vs_sma20 = (current / sma20 - 1) * 100
                    price_vs_sma50 = (current / sma50 - 1) * 100

                    if price_vs_sma20 > 2 and price_vs_sma50 > 0:
                        signal = 'BULLISH'
                        bullish_count += 1
                    elif price_vs_sma20 < -2 and price_vs_sma50 < 0:
                        signal = 'BEARISH'
                        bearish_count += 1
                    else:
                        signal = 'NEUTRAL'

                market_data[ticker] = {
                    'name': name,
                    'signal': signal,
                    'price': current,
                    'change': change if ticker == 'VIX' else price_vs_sma20
                }
            except:
                continue

        # Determinar dirección general
        if bullish_count >= 3:
            overall = 'BULLISH'
            color = '#00ffad'
        elif bearish_count >= 3:
            overall = 'BEARISH'
            color = '#f23645'
        else:
            overall = 'MIXED/CAUTION'
            color = '#ff9800'

        return {
            'overall': overall,
            'color': color,
            'indices': market_data,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count
        }
    except:
        return {
            'overall': 'UNKNOWN',
            'color': '#888',
            'indices': {},
            'bullish_count': 0,
            'bearish_count': 0
        }

# ============================================================
# CÁLCULOS CAN SLIM MEJORADOS
# ============================================================

def calculate_can_slim_metrics(ticker):
    """Calcula métricas CAN SLIM con análisis técnico avanzado"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="2y")

        if len(hist) < 100:
            return None

        # Datos básicos
        market_cap = info.get('marketCap', 0) / 1e9
        current_price = hist['Close'].iloc[-1]

        # C - Current Quarterly Earnings
        earnings_growth = info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0
        revenue_growth = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0

        # A - Annual Earnings Growth (3-5 años)
        eps_growth = info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0

        # N - New Highs + Análisis Técnico
        high_52w = hist['High'].max()
        low_52w = hist['Low'].min()
        pct_from_high = ((current_price - high_52w) / high_52w) * 100
        pct_from_low = ((current_price - low_52w) / low_52w) * 100

        # Detectar nuevos máximos
        is_new_high = pct_from_high > -5

        # S - Supply and Demand
        avg_volume_20 = hist['Volume'].rolling(20).mean().iloc[-1]
        avg_volume_50 = hist['Volume'].rolling(50).mean().iloc[-1]
        current_volume = hist['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1
        volume_trend = avg_volume_20 / avg_volume_50 if avg_volume_50 > 0 else 1

        # Análisis de float
        float_shares = info.get('floatShares', 0) / 1e6

        # L - Leader (RS Rating vs SPY)
        try:
            spy = yf.Ticker("SPY").history(period="1y")
            stock_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[-60] - 1) * 100
            spy_return = (spy['Close'].iloc[-1] / spy['Close'].iloc[-60] - 1) * 100
            rs_rating = 50 + (stock_return - spy_return) * 2
            rs_rating = max(0, min(100, rs_rating))

            # RS líder del sector
            sector = info.get('sector', '')
        except:
            rs_rating = 50

        # I - Institutional Sponsorship
        inst_ownership = info.get('heldPercentInstitutions', 0) * 100 if info.get('heldPercentInstitutions') else 0
        insider_ownership = info.get('heldPercentInsiders', 0) * 100 if info.get('heldPercentInsiders') else 0

        # M - Market Direction (se evalúa globalmente)
        market_data = analyze_market_direction()
        m_score = 15 if market_data['overall'] == 'BULLISH' else 5 if market_data['overall'] == 'BEARISH' else 10
        m_grade = 'A' if market_data['overall'] == 'BULLISH' else 'C' if market_data['overall'] == 'BEARISH' else 'B'

        # Calcular Score CAN SLIM (0-100)
        score = 0
        grades = {}
        scores = {}

        # C - Current Earnings (15 pts)
        if earnings_growth > 100: score += 15; grades['C'] = 'A'; scores['C'] = 15
        elif earnings_growth > 50: score += 13; grades['C'] = 'A'; scores['C'] = 13
        elif earnings_growth > 25: score += 10; grades['C'] = 'A'; scores['C'] = 10
        elif earnings_growth > 15: score += 7; grades['C'] = 'B'; scores['C'] = 7
        elif earnings_growth > 0: score += 4; grades['C'] = 'C'; scores['C'] = 4
        else: score += 0; grades['C'] = 'D'; scores['C'] = 0

        # A - Annual Growth (15 pts)
        if eps_growth > 100: score += 15; grades['A'] = 'A'; scores['A'] = 15
        elif eps_growth > 50: score += 12; grades['A'] = 'A'; scores['A'] = 12
        elif eps_growth > 25: score += 9; grades['A'] = 'B'; scores['A'] = 9
        elif eps_growth > 15: score += 6; grades['A'] = 'C'; scores['A'] = 6
        elif eps_growth > 0: score += 3; grades['A'] = 'D'; scores['A'] = 3
        else: score += 0; grades['A'] = 'F'; scores['A'] = 0

        # N - New Products/Highs (15 pts)
        if pct_from_high > -2: score += 15; grades['N'] = 'A'; scores['N'] = 15
        elif pct_from_high > -8: score += 12; grades['N'] = 'A'; scores['N'] = 12
        elif pct_from_high > -15: score += 9; grades['N'] = 'B'; scores['N'] = 9
        elif pct_from_high > -25: score += 5; grades['N'] = 'C'; scores['N'] = 5
        else: score += 0; grades['N'] = 'D'; scores['N'] = 0

        # S - Supply/Demand (15 pts)
        if volume_ratio > 3.0: score += 15; grades['S'] = 'A'; scores['S'] = 15
        elif volume_ratio > 2.0: score += 12; grades['S'] = 'A'; scores['S'] = 12
        elif volume_ratio > 1.5: score += 9; grades['S'] = 'B'; scores['S'] = 9
        elif volume_ratio > 1.0: score += 5; grades['S'] = 'C'; scores['S'] = 5
        else: score += 2; grades['S'] = 'D'; scores['S'] = 2

        # L - Leader (15 pts)
        if rs_rating > 95: score += 15; grades['L'] = 'A'; scores['L'] = 15
        elif rs_rating > 85: score += 12; grades['L'] = 'A'; scores['L'] = 12
        elif rs_rating > 75: score += 9; grades['L'] = 'B'; scores['L'] = 9
        elif rs_rating > 65: score += 5; grades['L'] = 'C'; scores['L'] = 5
        else: score += 0; grades['L'] = 'D'; scores['L'] = 0

        # I - Institutional (10 pts)
        if inst_ownership > 90: score += 10; grades['I'] = 'A'; scores['I'] = 10
        elif inst_ownership > 70: score += 8; grades['I'] = 'A'; scores['I'] = 8
        elif inst_ownership > 50: score += 6; grades['I'] = 'B'; scores['I'] = 6
        elif inst_ownership > 30: score += 3; grades['I'] = 'C'; scores['I'] = 3
        else: score += 0; grades['I'] = 'D'; scores['I'] = 0

        # M - Market Direction (15 pts)
        score += m_score
        grades['M'] = m_grade
        scores['M'] = m_score

        return {
            'ticker': ticker,
            'name': info.get('shortName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': market_cap,
            'price': current_price,
            'score': score,
            'grades': grades,
            'scores': scores,
            'metrics': {
                'earnings_growth': earnings_growth,
                'revenue_growth': revenue_growth,
                'eps_growth': eps_growth,
                'pct_from_high': pct_from_high,
                'pct_from_low': pct_from_low,
                'volume_ratio': volume_ratio,
                'volume_trend': volume_trend,
                'rs_rating': rs_rating,
                'inst_ownership': inst_ownership,
                'insider_ownership': insider_ownership,
                'float_shares': float_shares,
                'is_new_high': is_new_high,
                'market_direction': market_data['overall']
            }
        }
    except Exception as e:
        return None

# ============================================================
# VISUALIZACIONES AVANZADAS
# ============================================================

def create_price_chart(ticker, period="6mo"):
    """Crea gráfico de precios con volumen y medias móviles"""
    try:
        data = yf.Ticker(ticker).history(period=period)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, row_heights=[0.7, 0.3])

        # Precio y medias móviles
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Precio', 
                                line=dict(color='#00ffad', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(20).mean(), 
                                name='SMA 20', line=dict(color='#ff9800', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(50).mean(), 
                                name='SMA 50', line=dict(color='#2962ff', width=1)), row=1, col=1)

        # Volumen
        colors = ['#00ffad' if data['Close'].iloc[i] >= data['Open'].iloc[i] else '#f23645' 
                  for i in range(len(data))]
        fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volumen', 
                            marker_color=colors), row=2, col=1)

        fig.update_layout(
            title=f'{ticker} - Análisis Técnico',
            paper_bgcolor='#0c0e12',
            plot_bgcolor='#0c0e12',
            font=dict(color='white'),
            xaxis_rangeslider_visible=False,
            height=500,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#1a1e26', color='white')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#1a1e26', color='white')

        return fig
    except:
        return None

def create_score_gauge(score):
    """Gauge circular para el score"""
    color = "#00ffad" if score >= 80 else "#ff9800" if score >= 60 else "#f23645"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "CAN SLIM Score", 'font': {'size': 14, 'color': 'white'}},
        number={'font': {'size': 36, 'color': color, 'family': 'Arial Black'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "#0c0e12",
            'borderwidth': 2,
            'bordercolor': "#1a1e26",
            'steps': [
                {'range': [0, 60], 'color': hex_to_rgba("#f23645", 0.2)},
                {'range': [60, 80], 'color': hex_to_rgba("#ff9800", 0.2)},
                {'range': [80, 100], 'color': hex_to_rgba("#00ffad", 0.2)}
            ],
            'threshold': {'line': {'color': "white", 'width': 3}, 'thickness': 0.8, 'value': score}
        }
    ))

    fig.update_layout(paper_bgcolor="#0c0e12", font={'color': "white"}, height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def create_grades_radar(grades_dict):
    """Radar chart para calificaciones"""
    categories = ['C', 'A', 'N', 'S', 'L', 'I', 'M']
    values = []

    grade_map = {'A': 100, 'B': 75, 'C': 50, 'D': 25, 'F': 0}
    for cat in categories:
        values.append(grade_map.get(grades_dict.get(cat, 'F'), 0))

    values.append(values[0])
    categories.append(categories[0])

    fig = go.Figure(data=go.Scatterpolar(
        r=values, theta=categories, fill='toself', fillcolor='rgba(0, 255, 173, 0.3)',
        line=dict(color='#00ffad', width=2), marker=dict(size=8, color='#00ffad')
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], color='white', gridcolor='#1a1e26'),
                   angularaxis=dict(color='white', gridcolor='#1a1e26'), bgcolor='#0c0e12'),
        paper_bgcolor='#0c0e12', font=dict(color='white'), height=300,
        title=dict(text="Calificaciones CAN SLIM", font=dict(color='white', size=14)),
        margin=dict(l=60, r=60, t=50, b=40)
    )
    return fig

def create_comparison_chart(candidates):
    """Comparación lado a lado de múltiples stocks"""
    fig = go.Figure()

    colors = ['#00ffad', '#ff9800', '#2962ff', '#f23645', '#9c27b0']

    for i, c in enumerate(candidates[:5]):
        try:
            data = yf.Ticker(c['ticker']).history(period="6mo")
            normalized = (data['Close'] / data['Close'].iloc[0] - 1) * 100

            fig.add_trace(go.Scatter(
                x=data.index, y=normalized, name=f"{c['ticker']} ({c['score']})",
                line=dict(color=colors[i % len(colors)], width=2)
            ))
        except:
            continue

    fig.update_layout(
        title="Comparación de Rendimiento (Normalizado)",
        paper_bgcolor='#0c0e12', plot_bgcolor='#0c0e12',
        font=dict(color='white'), height=400,
        xaxes=dict(showgrid=True, gridcolor='#1a1e26'),
        yaxes=dict(showgrid=True, gridcolor='#1a1e26', title='Retorno %'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    return fig

# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================

def export_to_csv(candidates):
    """Exporta resultados a CSV"""
    if not candidates:
        return None

    data = []
    for c in candidates:
        data.append({
            'Ticker': c['ticker'],
            'Nombre': c['name'],
            'Sector': c['sector'],
            'Score': c['score'],
            'Grado_C': c['grades']['C'],
            'Grado_A': c['grades']['A'],
            'Grado_N': c['grades']['N'],
            'Grado_S': c['grades']['S'],
            'Grado_L': c['grades']['L'],
            'Grado_I': c['grades']['I'],
            'Grado_M': c['grades']['M'],
            'EPS_Growth': c['metrics']['earnings_growth'],
            'Revenue_Growth': c['metrics']['revenue_growth'],
            'RS_Rating': c['metrics']['rs_rating'],
            'From_High': c['metrics']['pct_from_high'],
            'Volume_Ratio': c['metrics']['volume_ratio'],
            'Inst_Ownership': c['metrics']['inst_ownership'],
            'Market_Cap_B': c['market_cap'],
            'Precio': c['price']
        })

    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')

def get_download_link(csv_data, filename="can_slim_results.csv"):
    """Genera link de descarga"""
    if csv_data is None:
        return ""
    b64 = base64.b64encode(csv_data).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}" style="text-decoration:none;"><button style="background:#00ffad;color:#0c0e12;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;font-weight:bold;">📥 Descargar CSV</button></a>'

# ============================================================
# RENDER PRINCIPAL
# ============================================================

def render():
    # CSS Global
    st.markdown("""
    <style>
    .main { background: #0c0e12; color: white; }
    .stApp { background: #0c0e12; }
    h1, h2, h3 { color: white !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background: #0c0e12; color: #888; border: 1px solid #1a1e26; border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { background: #1a1e26; color: #00ffad; border-bottom: 2px solid #00ffad; }
    .metric-card { background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 15px; text-align: center; }
    .grade-badge { display: inline-block; width: 30px; height: 30px; border-radius: 6px; text-align: center; line-height: 30px; font-weight: bold; font-size: 14px; margin: 2px; }
    .grade-A { background: rgba(0, 255, 173, 0.2); color: #00ffad; border: 1px solid #00ffad; }
    .grade-B { background: rgba(255, 152, 0, 0.2); color: #ff9800; border: 1px solid #ff9800; }
    .grade-C { background: rgba(242, 54, 69, 0.2); color: #f23645; border: 1px solid #f23645; }
    .grade-D { background: rgba(136, 136, 136, 0.2); color: #888; border: 1px solid #888; }
    .stProgress > div > div > div > div { background-color: #00ffad; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="font-size: 2.5rem; margin-bottom: 10px; color: #00ffad;">🎯 CAN SLIM Scanner Pro</h1>
        <p style="color: #888; font-size: 1.1rem;">Sistema de Selección de Acciones de William O'Neil</p>
        <p style="color: #555; font-size: 0.9rem;">S&P 500 • NASDAQ 100 • Russell 2000 • Growth Stocks • Crypto • EV</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar para filtros
    with st.sidebar:
        st.header("⚙️ Filtros")

        min_score = st.slider("Score Mínimo", 0, 100, 50)
        min_rs = st.slider("RS Rating Mínimo", 0, 100, 60)

        sectors = st.multiselect("Sectores", 
            ['Technology', 'Healthcare', 'Financial', 'Consumer Cyclical', 'Industrials', 
             'Communication', 'Energy', 'Basic Materials', 'Real Estate', 'Utilities'],
            default=['Technology', 'Healthcare'])

        min_volume = st.slider("Volume Ratio Mín", 0.5, 5.0, 1.0)

        st.header("📊 Opciones")
        max_results = st.number_input("Máx Resultados", 5, 100, 20)
        chart_period = st.selectbox("Período Gráficos", ["3mo", "6mo", "1y", "2y"])

        st.header("🔍 Universos")
        scan_sp500 = st.checkbox("S&P 500", value=True)
        scan_nasdaq = st.checkbox("NASDAQ 100", value=True)
        scan_russell = st.checkbox("Russell 2000", value=True)
        scan_growth = st.checkbox("Growth + Crypto + EV", value=True)

    # Tabs principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Scanner", "📈 Gráficos", "📊 Comparador", "📚 Metodología", "⚙️ Configuración"])

    # Variables de estado
    if 'candidates' not in st.session_state:
        st.session_state.candidates = []
    if 'selected_stock' not in st.session_state:
        st.session_state.selected_stock = None

    with tab1:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**Última actualización:** {get_timestamp()}")
        with col3:
            if st.button("🔍 ESCANEAR UNIVERSO COMPLETO", use_container_width=True, type="primary"):
                with st.spinner("Cargando universo de activos..."):
                    all_tickers = []
                    if scan_sp500:
                        all_tickers.extend(get_sp500_tickers())
                    if scan_nasdaq:
                        all_tickers.extend(get_nasdaq100_tickers())
                    if scan_russell:
                        all_tickers.extend(get_russell2000_tickers())
                    if scan_growth:
                        all_tickers.extend(get_additional_universe())

                    # Eliminar duplicados
                    all_tickers = list(set(all_tickers))
                    st.info(f"Universo total: {len(all_tickers)} activos")

                progress_bar = st.progress(0)
                status_text = st.empty()

                candidates = []
                for i, ticker in enumerate(all_tickers[:1500]):  # Limitar a 1500
                    progress = (i + 1) / min(len(all_tickers), 1500)
                    progress_bar.progress(progress)
                    status_text.text(f"Analizando {ticker}... ({i+1}/{min(len(all_tickers), 1500)})")

                    result = calculate_can_slim_metrics(ticker)
                    if result and result['score'] >= min_score:
                        # Aplicar filtros adicionales
                        if result['metrics']['rs_rating'] >= min_rs and result['sector'] in sectors:
                            if result['metrics']['volume_ratio'] >= min_volume:
                                candidates.append(result)

                progress_bar.empty()
                status_text.empty()

                st.session_state.candidates = candidates

                if candidates:
                    st.success(f"🎯 Se encontraron {len(candidates)} candidatos CAN SLIM")
                else:
                    st.warning("No se encontraron candidatos con los criterios seleccionados")

        if st.session_state.candidates:
            candidates = st.session_state.candidates

            # Top 3 destacados
            st.subheader("🏆 Top Candidatos CAN SLIM")
            cols = st.columns(min(3, len(candidates)))
            for i, col in enumerate(cols):
                if i < len(candidates):
                    c = candidates[i]
                    with col:
                        st.plotly_chart(create_score_gauge(c['score']), use_container_width=True, key=f"gauge_{i}")
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <h3 style="color: #00ffad; margin: 0;">{c['ticker']}</h3>
                            <p style="color: #888; font-size: 12px; margin: 5px 0;">{c['name'][:30]}</p>
                            <div style="margin: 10px 0;">
                                <span class="grade-badge grade-{c['grades']['C']}">C</span>
                                <span class="grade-badge grade-{c['grades']['A']}">A</span>
                                <span class="grade-badge grade-{c['grades']['N']}">N</span>
                                <span class="grade-badge grade-{c['grades']['S']}">S</span>
                                <span class="grade-badge grade-{c['grades']['L']}">L</span>
                                <span class="grade-badge grade-{c['grades']['I']}">I</span>
                                <span class="grade-badge grade-{c['grades']['M']}">M</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Ver {c['ticker']}", key=f"btn_{i}"):
                            st.session_state.selected_stock = c

            # Tabla completa con selección
            st.subheader("📋 Resultados Detallados")

            # Preparar datos
            table_data = []
            for c in candidates[:max_results]:
                table_data.append({
                    'Ticker': c['ticker'],
                    'Nombre': c['name'][:25],
                    'Score': c['score'],
                    'C': c['grades']['C'],
                    'A': c['grades']['A'],
                    'N': c['grades']['N'],
                    'S': c['grades']['S'],
                    'L': c['grades']['L'],
                    'I': c['grades']['I'],
                    'M': c['grades']['M'],
                    'EPS Growth': f"{c['metrics']['earnings_growth']:.1f}%",
                    'RS Rating': f"{c['metrics']['rs_rating']:.0f}",
                    'From High': f"{c['metrics']['pct_from_high']:.1f}%",
                    'Volume': f"{c['metrics']['volume_ratio']:.1f}x",
                    'Sector': c['sector']
                })

            df = pd.DataFrame(table_data)

            # Color coding
            def color_score(val):
                try:
                    score = int(val)
                    color = '#00ffad' if score >= 80 else '#ff9800' if score >= 60 else '#f23645'
                    return f'color: {color}; font-weight: bold'
                except:
                    return ''

            styled_df = df.style.applymap(color_score, subset=['Score'])
            st.dataframe(styled_df, use_container_width=True, height=400)

            # Exportar
            csv_data = export_to_csv(candidates)
            st.markdown(get_download_link(csv_data), unsafe_allow_html=True)

    with tab2:
        if st.session_state.selected_stock:
            c = st.session_state.selected_stock
            st.subheader(f"📈 Análisis Detallado: {c['ticker']} - {c['name']}")

            col1, col2 = st.columns([2, 1])

            with col1:
                fig = create_price_chart(c['ticker'], chart_period)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

                # Métricas detalladas
                st.markdown("### 📊 Métricas CAN SLIM")
                cols = st.columns(3)
                metrics = [
                    ("EPS Growth", f"{c['metrics']['earnings_growth']:.1f}%", c['grades']['C']),
                    ("Revenue Growth", f"{c['metrics']['revenue_growth']:.1f}%", c['grades']['A']),
                    ("RS Rating", f"{c['metrics']['rs_rating']:.0f}", c['grades']['L']),
                    ("From 52W High", f"{c['metrics']['pct_from_high']:.1f}%", c['grades']['N']),
                    ("Volume Ratio", f"{c['metrics']['volume_ratio']:.1f}x", c['grades']['S']),
                    ("Inst. Ownership", f"{c['metrics']['inst_ownership']:.1f}%", c['grades']['I']),
                ]

                for i, (label, value, grade) in enumerate(metrics):
                    with cols[i % 3]:
                        color = '#00ffad' if grade == 'A' else '#ff9800' if grade == 'B' else '#f23645'
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="color: #888; font-size: 12px;">{label}</div>
                            <div style="color: {color}; font-size: 24px; font-weight: bold;">{value}</div>
                            <div style="color: {color}; font-size: 12px;">Grade: {grade}</div>
                        </div>
                        """, unsafe_allow_html=True)

            with col2:
                st.plotly_chart(create_grades_radar(c['grades']), use_container_width=True)

                st.markdown("### 🎯 Signal")
                if c['score'] >= 80:
                    st.success("🟢 COMPRA FUERTE - Cumple todos los criterios CAN SLIM")
                elif c['score'] >= 60:
                    st.warning("🟡 COMPRA - Cumple la mayoría de criterios")
                else:
                    st.error("🔴 ESPERAR - No cumple criterios suficientes")

                if c['metrics']['is_new_high']:
                    st.info("🔥 BREAKOUT: Nuevo máximo histórico con volumen")
        else:
            st.info("Selecciona un stock en el tab Scanner para ver el análisis detallado")

    with tab3:
        if len(st.session_state.candidates) > 1:
            st.subheader("📊 Comparador de Candidatos")

            selected = st.multiselect("Seleccionar stocks para comparar", 
                                     [c['ticker'] for c in st.session_state.candidates],
                                     default=[c['ticker'] for c in st.session_state.candidates[:3]])

            if selected:
                selected_candidates = [c for c in st.session_state.candidates if c['ticker'] in selected]
                fig = create_comparison_chart(selected_candidates)
                st.plotly_chart(fig, use_container_width=True)

                # Tabla comparativa
                comp_data = []
                for c in selected_candidates:
                    comp_data.append({
                        'Ticker': c['ticker'],
                        'Score': c['score'],
                        'C': c['grades']['C'],
                        'A': c['grades']['A'],
                        'N': c['grades']['N'],
                        'S': c['grades']['S'],
                        'L': c['grades']['L'],
                        'I': c['grades']['I'],
                        'M': c['grades']['M'],
                        'EPS': f"{c['metrics']['earnings_growth']:.1f}%",
                        'RS': f"{c['metrics']['rs_rating']:.0f}",
                        'Price': f"${c['price']:.2f}"
                    })

                st.table(pd.DataFrame(comp_data))
        else:
            st.info("Necesitas al menos 2 candidatos para comparar")

    with tab4:
        st.markdown("""
        ## 📚 Guía Completa CAN SLIM

        ### Introducción
        CAN SLIM es un sistema de selección de acciones desarrollado por William O'Neil, fundador de Investor's Business Daily. 
        Es una estrategia de **growth investing** que identifica acciones con alto potencial de crecimiento antes de que 
        experimenten grandes movimientos al alza.

        ### Los 7 Criterios

        #### **C - Current Quarterly Earnings per Share** (15% del score)
        - **Qué buscar:** Crecimiento >25% vs mismo trimestre año anterior
        - **Ideal:** >50% de crecimiento
        - **Por qué importa:** Muestra aceleración reciente en beneficios
        - **Señal de alerta:** Crecimiento <15% o desaceleración

        #### **A - Annual Earnings Growth** (15% del score)
        - **Qué buscar:** Crecimiento anual compuesto >25% últimos 3-5 años
        - **Ideal:** Consistencia año tras año
        - **Por qué importa:** Demuestra sostenibilidad del crecimiento
        - **ROE:** Buscar >17%

        #### **N - New Products, New Management, New Highs** (15% del score)
        - **New Products:** Innovaciones que generan nuevos ingresos
        - **New Management:** Cambios positivos en dirección
        - **New Highs:** Precio cerca de máximos históricos (>95%)
        - **Por qué importa:** El momento óptimo de compra es en nuevos máximos

        #### **S - Supply and Demand** (15% del score)
        - **Volume:** 1.5x-2x volumen promedio en días de subida
        - **Float:** Preferiblemente <100M acciones (menos supply)
        - **Price:** Acciones >$15 (instituciones evitan penny stocks)
        - **Por qué importa:** Volumen confirma interés institucional

        #### **L - Leader or Laggard** (15% del score)
        - **RS Rating:** >80 (mejor que 80% del mercado)
        - **Sector Leader:** Top 2-3 del sector
        - **Evitar:** Últimos del sector (laggards)
        - **Por qué importa:** Los líderes siguen liderando

        #### **I - Institutional Sponsorship** (10% del score)
        - **Ownership:** 40-70% institucional (no demasiado alto)
        - **Trend:** Aumento reciente en tenencia
        - **Quality:** Fondos de calidad (Fidelity, T. Rowe Price)
        - **Por qué importa:** Los "smart money" valida la historia

        #### **M - Market Direction** (15% del score) ⭐ CRÍTICO
        - **Confirmación:** Índices principales en tendencia alcista
        - **Follow-Through Day:** Día 4-7 después de mínimo con volumen
        - **Distribution:** Evitar días de distribución (venta institucional)
        - **Por qué importa:** 3 de 4 acciones siguen la tendencia del mercado

        ### Reglas de Operación

        1. **Solo comprar en mercados alcistas confirmados (M)**
        2. **Comprar en puntos de compra (breakouts)**
        3. **Usar stop-loss del 7-8%**
        4. **Vender cuando caiga debajo de la SMA 50-day**
        5. **Nunca promediar a la baja**
        6. **Dejar correr las ganancias (pyramiding)**

        ### Señales de Venta
        - Climax run (subida parabólica + volumen máximo)
        - Cajón de distribución (rango lateral con volumen)
        - Cruce bajista de medias móviles
        - Pérdida de soporte clave
        - Cambio en fundamentales

        ### Errores Comunes a Evitar
        ❌ Comprar en mercados bajistas  
        ❌ Ignorar el volumen  
        ❌ Promediar pérdidas  
        ❌ Comprar stocks con bajo RS  
        ❌ No usar stop-loss  
        ❌ Vender ganadores demasiado pronto  

        ### Recursos Adicionales
        - Libro: "How to Make Money in Stocks" - William O'Neil
        - Periódico: Investor's Business Daily
        - Herramienta: MarketSmith (IBD)
        """)

    with tab5:
        st.markdown("""
        ### ⚙️ Configuración Técnica

        **Universo de Análisis:**
        - S&P 500: 500 grandes capitalizaciones
        - NASDAQ 100: 100 líderes tecnológicos
        - Russell 2000: ~1000 small-caps de alto crecimiento
        - Growth/Crypto/EV: Stocks temáticos adicionales

        **Total:** Hasta 1,500 stocks analizados en cada escaneo

        **Fuentes de Datos:**
        - Precios y volumen: Yahoo Finance (yfinance)
        - Fundamentales: Yahoo Finance
        - Componentes índices: Wikipedia + ETFs

        **Frecuencia de Actualización:**
        - Datos de precio: Tiempo real (15 min delay)
        - Fundamentales: Trimestral
        - Lista de componentes: Diario (cache)

        **Cálculo del Score:**
        - C: 15 pts (Current Earnings)
        - A: 15 pts (Annual Growth)
        - N: 15 pts (New Highs)
        - S: 15 pts (Supply/Demand)
        - L: 15 pts (Leader)
        - I: 10 pts (Institutional)
        - M: 15 pts (Market Direction)

        **Total: 100 puntos**

        ### Mejoras Técnicas Sugeridas
        1. **Base de datos local** (SQLite/PostgreSQL) para histórico
        2. **WebSocket** para datos en tiempo real
        3. **Machine Learning** para scoring predictivo
        4. **Backtesting engine** con Zipline/Backtrader
        5. **Alertas** vía email/Telegram
        6. **API propia** para datos fundamentales
        """)

if __name__ == "__main__":
    render()
