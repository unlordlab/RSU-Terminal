# -*- coding: utf-8 -*-
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURACIÓN DE PÁGINA
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
# OBTENER COMPONENTES DE ÍNDICES
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
        # Fallback: top 100 S&P 500
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'AVGO', 'WMT',
                'JPM', 'V', 'MA', 'UNH', 'HD', 'PG', 'JNJ', 'BAC', 'LLY', 'MRK', 'KO', 'PEP',
                'ABBV', 'COST', 'TMO', 'ADBE', 'NFLX', 'AMD', 'CRM', 'ACN', 'LIN', 'PM', 'DIS',
                'ABT', 'VZ', 'NKE', 'TXN', 'RTX', 'NEE', 'BMY', 'QCOM', 'CVX', 'PFE', 'T',
                'SBUX', 'LOW', 'GS', 'UPS', 'HON', 'MS', 'UNP', 'BA', 'CAT', 'IBM', 'GE',
                'LMT', 'DE', 'SPGI', 'MDT', 'GILD', 'CVS', 'AMGN', 'C', 'BLK', 'AXP', 'MO',
                'BKNG', 'SYK', 'COP', 'ADI', 'USB', 'MMC', 'EL', 'LRCX', 'SO', 'BDX', 'CI',
                'PNC', 'TJX', 'ITW', 'APD', 'NOC', 'ETN', 'CME', 'CSX', 'DUK', 'FDX', 'CL',
                'GM', 'AON', 'TGT', 'NSC', 'WM', 'SLB', 'EOG', 'PXD', 'HUM', 'MET']

@st.cache_data(ttl=3600)
def get_nasdaq100_tickers():
    """Obtiene los tickers del NASDAQ 100"""
    try:
        url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
        tables = pd.read_html(url)
        for table in tables:
            if 'Ticker' in table.columns or 'Symbol' in table.columns:
                col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                return table[col].tolist()
    except:
        pass

    # Fallback: top NASDAQ 100
    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'PEP', 'COST',
            'NFLX', 'AMD', 'ADBE', 'TMUS', 'INTC', 'QCOM', 'INTU', 'AMAT', 'BKNG', 'ISRG',
            'VRTX', 'MU', 'LRCX', 'REGN', 'PANW', 'SNOW', 'CSX', 'ADP', 'KLAC', 'ABNB',
            'MELI', 'NXPI', 'MAR', 'FTNT', 'WDAY', 'JD', 'ORLY', 'CTAS', 'MRVL', 'DXCM',
            'CPRT', 'CEG', 'AZN', 'TEAM', 'CHTR', 'KDP', 'MRNA', 'PAYX', 'ROST', 'ODFL',
            'PCAR', 'MNST', 'KHC', 'AEP', 'EXC', 'IDXX', 'DDOG', 'FAST', 'VRSK', 'CSGP',
            'EA', 'XEL', 'LULU', 'ILMN', 'DLTR', 'CTSH', 'BIIB', 'WBD', 'GFS', 'TTD',
            'ON', 'ANSS', 'MCHP', 'CDNS', 'TTWO', 'FTV', 'WBA', 'SIRI', 'SPLK', 'ZM',
            'DOCU', 'OKTA', 'CRWD', 'ZS', 'NET', 'DDOG', 'PLTR', 'SOFI', 'LCID', 'RIVN']

@st.cache_data(ttl=3600)
def get_russell2000_tickers():
    """Obtiene una muestra representativa del Russell 2000"""
    # Russell 2000 son 2000 stocks pequeños, usamos una muestra diversificada
    return ['IWM', 'RUT', 'TNA', 'TZA', 'UWM', 'SRTY', 'VTWO', 'IWO', 'IWN', 'RTY',
            'AMC', 'GME', 'BB', 'NOK', 'PLTR', 'SOFI', 'LCID', 'RIVN', 'SPCE', 'NKLA',
            'MULN', 'HOOD', 'AFRM', 'UPST', 'RBLX', 'U', 'DOCN', 'ASAN', 'MDB', 'NET',
            'CRWD', 'OKTA', 'ZS', 'S', 'PANW', 'FTNT', 'CYBR', 'QLYS', 'VRNS', 'TENB',
            'SPLK', 'DDOG', 'ESTC', 'FSLY', 'NET', 'CLOV', 'WISH', 'CONTEXT', 'ROOT', 'METC',
            'HUT', 'RIOT', 'MARA', 'BITF', 'CLSK', 'ARBK', 'CORZ', 'BTBT', 'SDIG', 'WULF',
            'IREN', 'DMGI', 'HIVE', 'BITF', 'GLXY', 'COIN', 'HOOD', 'SOFI', 'AFRM', 'UPST',
            'LMND', 'ROOT', 'HIPO', 'OSCR', 'CLOV', 'WISH', 'PLTK', 'PLAY', 'CHUY', 'BOJA',
            'TAST', 'FRGI', 'GTIM', 'PBPB', 'LOCO', 'SHAK', 'CMG', 'MCD', 'YUM', 'DRI',
            'TXRH', 'CBRL', 'EAT', 'BJRI', 'CHUY', 'PLAY', 'GTIM', 'PBPB', 'BOJA', 'FRGI']

@st.cache_data(ttl=3600)
def get_all_universe_tickers():
    """Combina todos los universos y elimina duplicados"""
    sp500 = get_sp500_tickers()
    nasdaq = get_nasdaq100_tickers()
    russell = get_russell2000_tickers()

    # Combinar y eliminar duplicados
    all_tickers = list(set(sp500 + nasdaq + russell))

    # Priorizar por capitalización (filtrar solo los más líquidos)
    # Limitar a 500 para rendimiento
    return all_tickers[:500]

# ============================================================
# CÁLCULOS CAN SLIM
# ============================================================

def calculate_can_slim_metrics(ticker):
    """Calcula todas las métricas CAN SLIM para un ticker"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")

        if len(hist) < 50:
            return None

        # Datos básicos
        market_cap = info.get('marketCap', 0) / 1e9
        current_price = hist['Close'].iloc[-1]

        # C - Current Quarterly Earnings
        earnings_growth = info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0
        revenue_growth = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0

        # A - Annual Earnings Growth
        eps_growth = info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0

        # N - New Highs
        high_52w = hist['High'].max()
        pct_from_high = ((current_price - high_52w) / high_52w) * 100

        # S - Supply and Demand (Volume)
        avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
        current_volume = hist['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

        # L - Leader (RS Rating vs SPY)
        try:
            spy = yf.Ticker("SPY").history(period="1y")
            stock_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
            spy_return = (spy['Close'].iloc[-1] / spy['Close'].iloc[0] - 1) * 100
            rs_rating = 50 + (stock_return - spy_return) * 2
            rs_rating = max(0, min(100, rs_rating))
        except:
            rs_rating = 50

        # I - Institutional Sponsorship
        inst_ownership = info.get('heldPercentInstitutions', 0) * 100 if info.get('heldPercentInstitutions') else 0

        # Calcular Score CAN SLIM (0-100)
        score = 0
        details = {}

        # C - Current Earnings (20 pts)
        if earnings_growth > 50: 
            score += 20; c_grade = 'A'; c_score = 20
        elif earnings_growth > 25: 
            score += 15; c_grade = 'A'; c_score = 15
        elif earnings_growth > 15: 
            score += 10; c_grade = 'B'; c_score = 10
        elif earnings_growth > 0: 
            score += 5; c_grade = 'C'; c_score = 5
        else: 
            score += 0; c_grade = 'D'; c_score = 0

        # A - Annual Growth (15 pts)
        if eps_growth > 50: 
            score += 15; a_grade = 'A'; a_score = 15
        elif eps_growth > 25: 
            score += 12; a_grade = 'A'; a_score = 12
        elif eps_growth > 15: 
            score += 8; a_grade = 'B'; a_score = 8
        elif eps_growth > 0: 
            score += 4; a_grade = 'C'; a_score = 4
        else: 
            score += 0; a_grade = 'D'; a_score = 0

        # N - New Products/Highs (15 pts)
        if pct_from_high > -3: 
            score += 15; n_grade = 'A'; n_score = 15
        elif pct_from_high > -10: 
            score += 12; n_grade = 'A'; n_score = 12
        elif pct_from_high > -20: 
            score += 8; n_grade = 'B'; n_score = 8
        elif pct_from_high > -30: 
            score += 4; n_grade = 'C'; n_score = 4
        else: 
            score += 0; n_grade = 'D'; n_score = 0

        # S - Supply/Demand (10 pts)
        if volume_ratio > 2.0: 
            score += 10; s_grade = 'A'; s_score = 10
        elif volume_ratio > 1.5: 
            score += 8; s_grade = 'A'; s_score = 8
        elif volume_ratio > 1.0: 
            score += 5; s_grade = 'B'; s_score = 5
        else: 
            score += 2; s_grade = 'C'; s_score = 2

        # L - Leader (15 pts)
        if rs_rating > 90: 
            score += 15; l_grade = 'A'; l_score = 15
        elif rs_rating > 80: 
            score += 12; l_grade = 'A'; l_score = 12
        elif rs_rating > 70: 
            score += 8; l_grade = 'B'; l_score = 8
        elif rs_rating > 60: 
            score += 4; l_grade = 'C'; l_score = 4
        else: 
            score += 0; l_grade = 'D'; l_score = 0

        # I - Institutional (10 pts)
        if inst_ownership > 80: 
            score += 10; i_grade = 'A'; i_score = 10
        elif inst_ownership > 60: 
            score += 8; i_grade = 'A'; i_score = 8
        elif inst_ownership > 40: 
            score += 5; i_grade = 'B'; i_score = 5
        elif inst_ownership > 20: 
            score += 3; i_grade = 'C'; i_score = 3
        else: 
            score += 0; i_grade = 'D'; i_score = 0

        # M - Market Direction (se evalúa globalmente)
        m_grade = 'A'  # Se actualiza con datos de mercado

        return {
            'ticker': ticker,
            'name': info.get('shortName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': market_cap,
            'price': current_price,
            'score': score,
            'grades': {'C': c_grade, 'A': a_grade, 'N': n_grade, 'S': s_grade, 'L': l_grade, 'I': i_grade, 'M': m_grade},
            'scores': {'C': c_score, 'A': a_score, 'N': n_score, 'S': s_score, 'L': l_score, 'I': i_score, 'M': 0},
            'metrics': {
                'earnings_growth': earnings_growth,
                'revenue_growth': revenue_growth,
                'eps_growth': eps_growth,
                'pct_from_high': pct_from_high,
                'volume_ratio': volume_ratio,
                'rs_rating': rs_rating,
                'inst_ownership': inst_ownership
            }
        }
    except Exception as e:
        return None

@st.cache_data(ttl=600)
def scan_universe(tickers, min_score=40):
    """Escanea el universo de tickers y devuelve candidatos CAN SLIM"""
    candidates = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, ticker in enumerate(tickers):
        progress = (i + 1) / len(tickers)
        progress_bar.progress(progress)
        status_text.text(f"Analizando {ticker}... ({i+1}/{len(tickers)})")

        result = calculate_can_slim_metrics(ticker)
        if result and result['score'] >= min_score:
            candidates.append(result)

    progress_bar.empty()
    status_text.empty()

    # Ordenar por score descendente
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates

# ============================================================
# VISUALIZACIONES
# ============================================================

def create_score_gauge(score):
    """Crea un gauge circular para el score CAN SLIM"""
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

    fig.update_layout(
        paper_bgcolor="#0c0e12",
        font={'color': "white"},
        height=250,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def create_grades_radar(grades_dict):
    """Crea un radar chart para las calificaciones"""
    categories = ['C', 'A', 'N', 'S', 'L', 'I', 'M']
    values = []

    grade_map = {'A': 100, 'B': 75, 'C': 50, 'D': 25, 'F': 0}
    for cat in categories:
        values.append(grade_map.get(grades_dict.get(cat, 'F'), 0))

    values.append(values[0])  # Cerrar el polígono
    categories.append(categories[0])

    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(0, 255, 173, 0.3)',
        line=dict(color='#00ffad', width=2),
        marker=dict(size=8, color='#00ffad')
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color='white', gridcolor='#1a1e26'),
            angularaxis=dict(color='white', gridcolor='#1a1e26'),
            bgcolor='#0c0e12'
        ),
        paper_bgcolor='#0c0e12',
        font=dict(color='white'),
        title=dict(text="Calificaciones CAN SLIM", font=dict(color='white', size=14)),
        height=300,
        margin=dict(l=60, r=60, t=50, b=40)
    )
    return fig

# ============================================================
# RENDER PRINCIPAL
# ============================================================

def render():
    # CSS Global
    st.markdown("""
    <style>
    .main {
        background: #0c0e12;
        color: white;
    }
    .stApp {
        background: #0c0e12;
    }
    h1, h2, h3 {
        color: white !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #0c0e12;
        color: #888;
        border: 1px solid #1a1e26;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background: #1a1e26;
        color: #00ffad;
        border-bottom: 2px solid #00ffad;
    }
    .metric-card {
        background: #0c0e12;
        border: 1px solid #1a1e26;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .grade-badge {
        display: inline-block;
        width: 30px;
        height: 30px;
        border-radius: 6px;
        text-align: center;
        line-height: 30px;
        font-weight: bold;
        font-size: 14px;
        margin: 2px;
    }
    .grade-A { background: rgba(0, 255, 173, 0.2); color: #00ffad; border: 1px solid #00ffad; }
    .grade-B { background: rgba(255, 152, 0, 0.2); color: #ff9800; border: 1px solid #ff9800; }
    .grade-C { background: rgba(242, 54, 69, 0.2); color: #f23645; border: 1px solid #f23645; }
    .grade-D { background: rgba(136, 136, 136, 0.2); color: #888; border: 1px solid #888; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="font-size: 2.5rem; margin-bottom: 10px; color: #00ffad;">🎯 CAN SLIM Scanner Pro</h1>
        <p style="color: #888; font-size: 1.1rem;">Sistema de Selección de Acciones de William O'Neil</p>
        <p style="color: #555; font-size: 0.9rem;">Datos en tiempo real • S&P 500 • NASDAQ 100 • Russell 2000</p>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Scanner", "📊 Análisis", "📚 Metodología", "⚙️ Configuración"])

    with tab1:
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            min_score = st.slider("Score Mínimo", 0, 100, 50, help="Filtrar acciones con score igual o mayor")
        with col2:
            max_results = st.number_input("Máx Resultados", 5, 50, 15)
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            scan_button = st.button("🔍 ESCANEAR UNIVERSO", use_container_width=True, type="primary")

        if scan_button:
            tickers = get_all_universe_tickers()
            candidates = scan_universe(tickers, min_score)

            if candidates:
                st.success(f"Se encontraron {len(candidates)} candidatos CAN SLIM")

                # Top 3 destacados
                st.subheader("🏆 Top Candidatos")
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
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                # Tabla completa
                st.subheader("📋 Resultados Detallados")

                # Preparar datos para tabla
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
                        'EPS Growth': f"{c['metrics']['earnings_growth']:.1f}%",
                        'RS Rating': f"{c['metrics']['rs_rating']:.0f}",
                        'From High': f"{c['metrics']['pct_from_high']:.1f}%",
                        'Sector': c['sector']
                    })

                df = pd.DataFrame(table_data)

                # Aplicar color al score
                def color_score(val):
                    color = '#00ffad' if val >= 80 else '#ff9800' if val >= 60 else '#f23645'
                    return f'color: {color}; font-weight: bold'

                styled_df = df.style.applymap(color_score, subset=['Score'])
                st.dataframe(styled_df, use_container_width=True, height=400)

            else:
                st.warning("No se encontraron candidatos con los criterios seleccionados")

    with tab2:
        st.info("Análisis detallado en desarrollo...")

    with tab3:
        st.markdown("""
        ### Los 7 Criterios CAN SLIM

        **C - Current Quarterly Earnings** (>25%)
        Crecimiento trimestral de beneficios. Buscar >25%, idealmente >50%.

        **A - Annual Earnings Growth** (>25%)
        Crecimiento anual consistente durante los últimos 3-5 años.

        **N - New Products/Management/Highs**
        Nuevos productos, cambio de management o nuevos máximos históricos.

        **S - Supply and Demand**
        Volumen elevado indica interés institucional. Buscar 1.5x-2x el promedio.

        **L - Leader or Laggard**
        Solo comprar líderes del sector. RS Rating >80.

        **I - Institutional Sponsorship**
        Patrocinio de fondos institucionales creciente. >40% ownership.

        **M - Market Direction**
        Solo operar en mercados alcistas confirmados. El factor más importante.
        """)

    with tab4:
        st.markdown("""
        ### Configuración del Scanner

        **Universo de Análisis:**
        - S&P 500: 500 grandes capitalizaciones
        - NASDAQ 100: 100 tecnológicas/líderes
        - Russell 2000: 2000 pequeñas capitalizaciones

        **Total analizado:** ~500-600 stocks (eliminando duplicados)

        **Frecuencia de actualización:** Datos en tiempo real vía Yahoo Finance
        """)

if __name__ == "__main__":
    render()
