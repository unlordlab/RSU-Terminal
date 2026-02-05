import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from config import get_ia_model, get_cnn_fear_greed
import requests
from bs4 import BeautifulSoup
import time
import json

# ────────────────────────────────────────────────
# FUNCIONES DE DATOS REALES
# ────────────────────────────────────────────────

def get_comprehensive_earnings_data(ticker_symbol):
    """Obtiene datos completos y reales de earnings."""
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        hist = stock.history(period="1y")
        
        # Datos básicos
        data = {
            "ticker": ticker_symbol,
            "name": info.get('longName', ticker_symbol),
            "short_name": info.get('shortName', ticker_symbol),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "country": info.get('country', 'N/A'),
            "employees": info.get('fullTimeEmployees', 0),
            "website": info.get('website', '#'),
            "summary": info.get('longBusinessSummary', ''),
            
            # Precios
            "price": info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0),
            "prev_close": info.get('regularMarketPreviousClose', 0),
            "open": info.get('regularMarketOpen', 0),
            "day_high": info.get('regularMarketDayHigh', 0),
            "day_low": info.get('regularMarketDayLow', 0),
            "fifty_two_high": info.get('fiftyTwoWeekHigh', 0),
            "fifty_two_low": info.get('fiftyTwoWeekLow', 0),
            "volume": info.get('volume', 0),
            "avg_volume": info.get('averageVolume', 0),
            
            # Métricas clave
            "market_cap": info.get('marketCap', 0),
            "enterprise_value": info.get('enterpriseValue', 0),
            "rev_growth": info.get('revenueGrowth'),
            "ebitda_margin": info.get('ebitdaMargins'),
            "profit_margin": info.get('profitMargins'),
            "operating_margin": info.get('operatingMargins'),
            "gross_margin": info.get('grossMargins'),
            "pe_trailing": info.get('trailingPE'),
            "pe_forward": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio'),
            "price_to_sales": info.get('priceToSalesTrailing12Months'),
            "price_to_book": info.get('priceToBook'),
            "eps": info.get('trailingEps'),
            "eps_forward": info.get('forwardEps'),
            "eps_growth": info.get('earningsGrowth'),
            "revenue_per_share": info.get('revenuePerShare'),
            
            # Retornos
            "roe": info.get('returnOnEquity'),
            "roa": info.get('returnOnAssets'),
            "roic": info.get('returnOnCapitalEmployed'),
            
            # Balance
            "cash": info.get('totalCash', 0),
            "free_cashflow": info.get('freeCashflow', 0),
            "operating_cashflow": info.get('operatingCashflow', 0),
            "debt": info.get('totalDebt', 0),
            "debt_to_equity": info.get('debtToEquity'),
            "current_ratio": info.get('currentRatio'),
            "quick_ratio": info.get('quickRatio'),
            
            # Dividendos
            "dividend_rate": info.get('dividendRate', 0),
            "dividend_yield": info.get('dividendYield', 0) if info.get('dividendYield') else 0,
            "ex_div_date": info.get('exDividendDate'),
            "payout_ratio": info.get('payoutRatio', 0),
            
            # Targets
            "target_high": info.get('targetHighPrice', 0),
            "target_low": info.get('targetLowPrice', 0),
            "target_mean": info.get('targetMeanPrice', 0),
            "target_median": info.get('targetMedianPrice', 0),
            "recommendation": info.get('recommendationKey', 'none'),
            "num_analysts": info.get('numberOfAnalystOpinions', 0),
            
            # Histórico
            "hist": hist,
            "beta": info.get('beta', 0),
        }
        
        # Calcular cambio porcentual
        if data['price'] and data['prev_close']:
            data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
            data['change_abs'] = data['price'] - data['prev_close']
        else:
            data['change_pct'] = 0
            data['change_abs'] = 0
            
        # Calcular distancia a 52 semanas
        if data['fifty_two_high'] and data['price']:
            data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
        else:
            data['pct_from_high'] = 0
            
        return data, stock
        
    except Exception as e:
        st.error(f"Error obteniendo datos: {str(e)}")
        return None, None

def get_earnings_calendar_real(stock, ticker):
    """Obtiene fechas reales de earnings."""
    try:
        calendar = stock.calendar
        if calendar is not None and not calendar.empty:
            earnings_dates = []
            for idx, row in calendar.iterrows():
                date_str = idx.strftime('%d %b %Y') if isinstance(idx, datetime) else str(idx)
                eps_est = row.get('Earnings Estimate', 'N/A')
                revenue_est = row.get('Revenue Estimate', 'N/A')
                earnings_dates.append({
                    'date': date_str,
                    'eps_est': eps_est,
                    'revenue_est': revenue_est
                })
            return earnings_dates
    except:
        pass
    
    # Fallback: Intentar obtener earnings históricos
    try:
        earnings_hist = stock.earnings_dates
        if earnings_hist is not None and not earnings_hist.empty:
            return [{'date': str(idx), 'eps_est': 'Ver reporte', 'revenue_est': 'N/A'} 
                   for idx in earnings_hist.head(4).index]
    except:
        pass
    
    return []

def get_analyst_recommendations(stock):
    """Obtiene recomendaciones reales de analistas."""
    try:
        rec = stock.recommendations
        if rec is not None and not rec.empty:
            # Tomar el período más reciente
            latest = rec.iloc[-1]
            return {
                'strongBuy': latest.get('strongBuy', 0),
                'buy': latest.get('buy', 0),
                'hold': latest.get('hold', 0),
                'sell': latest.get('sell', 0),
                'strongSell': latest.get('strongSell', 0),
                'total': sum([latest.get(x, 0) for x in ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']])
            }
    except:
        pass
    return None

def get_earnings_estimates(stock):
    """Obtiene estimaciones de earnings."""
    try:
        eps_est = stock.earnings_estimate
        rev_est = stock.revenue_estimate
        return {
            'eps_next_q': eps_est.iloc[0].get('numberOfAnalysts', 0) if not eps_est.empty else 0,
            'eps_growth': eps_est.iloc[0].get('growth', 0) if not eps_est.empty else 0,
        }
    except:
        return {}

def get_insider_trading_real(ticker):
    """Scrapea insider trading de OpenInsider."""
    try:
        url = f"http://openinsider.com/screener?s={ticker}&o=&pl=&ph=&ll=&lh=&fd=730&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&xa=1&xd=1&xg=1&xf=1&xm=1&xx=1&xc=1&xw=1&insidername=&tickercount=&groupsize=1&sortcol=0&cnt=10&page=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', {'class': 'tinytable'})
        if table:
            rows = table.find_all('tr')[1:6]  # Top 5 transacciones
            transactions = []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 10:
                    transactions.append({
                        'insider': cols[1].text.strip(),
                        'relation': cols[2].text.strip(),
                        'date': cols[3].text.strip(),
                        'transaction': cols[4].text.strip(),
                        'type': cols[5].text.strip(),
                        'shares': cols[6].text.strip(),
                        'price': cols[7].text.strip(),
                        'value': cols[9].text.strip()
                    })
            return transactions
    except Exception as e:
        print(f"Error insider trading: {e}")
    return []

def get_similar_companies(sector, industry, current_ticker):
    """Obtiene competidores del mismo sector."""
    try:
        # Buscar ETFs del sector para obtener holdings
        sector_etfs = {
            'Technology': 'XLK',
            'Communication Services': 'XLC',
            'Consumer Cyclical': 'XLY',
            'Healthcare': 'XLV',
            'Financial Services': 'XLF',
            'Industrials': 'XLI',
            'Energy': 'XLE',
            'Utilities': 'XLU',
            'Real Estate': 'XLRE',
            'Materials': 'XLB',
            'Consumer Defensive': 'XLP'
        }
        
        etf_symbol = sector_etfs.get(sector, 'SPY')
        etf = yf.Ticker(etf_symbol)
        holdings = etf.info.get('holdings', [])
        
        # Filtrar holdings relevantes
        competitors = []
        for holding in holdings[:10]:
            symbol = holding.get('symbol', '')
            if symbol and symbol != current_ticker and len(symbol) <= 4:
                competitors.append({
                    'symbol': symbol,
                    'name': holding.get('holdingName', symbol),
                    'pct': holding.get('holdingPercent', 0)
                })
        
        return competitors[:5]
    except:
        return []

def fetch_finnhub_news_symbol(ticker, api_key):
    """Obtiene noticias específicas del ticker desde Finnhub."""
    if not api_key:
        return []
    
    try:
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={datetime.now().strftime('%Y-%m-%d')}&to={(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')}&token={api_key}"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        news_list = []
        for item in data[:5]:
            news_list.append({
                "datetime": datetime.fromtimestamp(item.get("datetime", 0)).strftime("%d/%m %H:%M"),
                "headline": item.get("headline", ""),
                "source": item.get("source", ""),
                "url": item.get("url", "#"),
                "summary": item.get("summary", "")[:150] + "..."
            })
        return news_list
    except:
        return []

# ────────────────────────────────────────────────
# FUNCIONES DE FORMATO
# ────────────────────────────────────────────────

def format_value(value, prefix="", suffix="", decimals=2):
    """Formatea valores numéricos."""
    if value is None or value == 0:
        return "N/A"
    if isinstance(value, (int, float)):
        if abs(value) >= 1e12:
            return f"{prefix}{value/1e12:.{decimals}f}T{suffix}"
        elif abs(value) >= 1e9:
            return f"{prefix}{value/1e9:.{decimals}f}B{suffix}"
        elif abs(value) >= 1e6:
            return f"{prefix}{value/1e6:.{decimals}f}M{suffix}"
        elif abs(value) >= 1e3:
            return f"{prefix}{value/1e3:.{decimals}f}K{suffix}"
        else:
            return f"{prefix}{value:.{decimals}f}{suffix}"
    return str(value)

def format_percentage(value, decimals=2):
    """Formatea porcentajes con color."""
    if value is None:
        return "N/A", "#888"
    if isinstance(value, float):
        color = "#00ffad" if value >= 0 else "#f23645"
        return f"{value:.{decimals}f}%", color
    return str(value), "#888"

def get_recommendation_color(rec):
    """Devuelve color según recomendación."""
    colors = {
        'strong_buy': '#00ffad',
        'buy': '#4caf50',
        'hold': '#ff9800',
        'sell': '#f23645',
        'strong_sell': '#d32f2f',
        'none': '#888'
    }
    return colors.get(rec, '#888')

def get_recommendation_text(rec):
    """Traduce recomendación al español."""
    translations = {
        'strong_buy': 'COMPRA FUERTE',
        'buy': 'COMPRA',
        'hold': 'MANTENER',
        'sell': 'VENDER',
        'strong_sell': 'VENTA FUERTE',
        'none': 'SIN DATOS'
    }
    return translations.get(rec, rec.upper())

# ────────────────────────────────────────────────
# COMPONENTES VISUALES
# ────────────────────────────────────────────────

def render_header(data):
    """Cabecera premium con datos de precio."""
    change_color = "#00ffad" if data['change_pct'] >= 0 else "#f23645"
    arrow = "▲" if data['change_pct'] >= 0 else "▼"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div style="margin-bottom: 5px;">
            <span style="background: #2a3f5f; color: #00ffad; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;">
                {data['sector']}
            </span>
            <span style="color: #666; font-size: 12px; margin-left: 10px;">
                {data['industry']} • {data['country']}
            </span>
        </div>
        <h1 style="color: white; margin: 0; font-size: 2.8rem; font-weight: 700;">
            {data['name']}
            <span style="color: #00ffad; font-size: 1.5rem; font-weight: 500;">({data['ticker']})</span>
        </h1>
        <div style="color: #666; font-size: 13px; margin-top: 8px;">
            {format_value(data['employees'], '', ' empleados', 0)} • 
            <a href="{data['website']}" target="_blank" style="color: #00ffad; text-decoration: none;">
                Sitio web →
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: right;">
            <div style="color: white; font-size: 3.2rem; font-weight: 700; line-height: 1;">
                ${data['price']:,.2f}
            </div>
            <div style="color: {change_color}; font-size: 1.4rem; font-weight: 600; margin-top: 5px;">
                {arrow} {data['change_abs']:+.2f} ({data['change_pct']:+.2f}%)
            </div>
            <div style="color: #666; font-size: 12px; margin-top: 5px;">
                Cap: {format_value(data['market_cap'], '$')} | Vol: {format_value(data['volume'], '', '', 0)}
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_price_stats(data):
    """Estadísticas de precio en tarjetas."""
    cols = st.columns(4)
    stats = [
        ("Apertura", f"${data['open']:,.2f}", "#888"),
        ("Máx. Día", f"${data['day_high']:,.2f}", "#00ffad"),
        ("Mín. Día", f"${data['day_low']:,.2f}", "#f23645"),
        ("52S Alto", f"${data['fifty_two_high']:,.2f}", "#888"),
    ]
    
    for col, (label, value, color) in zip(cols, stats):
        with col:
            st.markdown(f"""
            <div style="
                background: #0c0e12;
                border: 1px solid #1a1e26;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">
                    {label}
                </div>
                <div style="color: {color}; font-size: 1.3rem; font-weight: bold;">
                    {value}
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_fundamental_metrics(data):
    """Métricas fundamentales en grid."""
    st.markdown("### 📊 Métricas Fundamentales")
    
    # Primera fila: Rentabilidad
    cols = st.columns(4)
    metrics_row1 = [
        ("Crec. Ingresos", data['rev_growth'], "%", True),
        ("Margen EBITDA", data['ebitda_margin'], "%", True),
        ("Margen Neto", data['profit_margin'], "%", True),
        ("ROE", data['roe'], "%", True),
    ]
    
    for col, (label, value, suffix, is_good_high) in zip(cols, metrics_row1):
        with col:
            formatted, color = format_percentage(value)
            if not is_good_high and value is not None:
                color = "#f23645" if value > 0.5 else "#00ffad"  # Para métricas donde bajo es bueno
            st.markdown(f"""
            <div style="
                background: #0c0e12;
                border: 1px solid #1a1e26;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                margin-bottom: 15px;
            ">
                <div style="color: #666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                    {label}
                </div>
                <div style="color: {color}; font-size: 1.6rem; font-weight: bold;">
                    {formatted}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Segunda fila: Valoración
    cols = st.columns(4)
    metrics_row2 = [
        ("P/E Trailing", format_value(data['pe_trailing'], '', 'x', 1), "#00ffad"),
        ("P/E Forward", format_value(data['pe_forward'], '', 'x', 1), "#4caf50"),
        ("PEG Ratio", format_value(data['peg_ratio'], '', '', 2), "#ff9800"),
        ("Price/Book", format_value(data['price_to_book'], '', 'x', 1), "#888"),
    ]
    
    for col, (label, value, color) in zip(cols, metrics_row2):
        with col:
            st.markdown(f"""
            <div style="
                background: #0c0e12;
                border: 1px solid #1a1e26;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                margin-bottom: 15px;
            ">
                <div style="color: #666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                    {label}
                </div>
                <div style="color: {color}; font-size: 1.6rem; font-weight: bold;">
                    {value}
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_chart(hist_data, ticker):
    """Gráfico avanzado con volumen."""
    if hist_data.empty:
        st.warning("No hay datos históricos")
        return
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=hist_data.index,
        open=hist_data['Open'],
        high=hist_data['High'],
        low=hist_data['Low'],
        close=hist_data['Close'],
        increasing_line_color='#00ffad',
        decreasing_line_color='#f23645',
        name=ticker
    ), row=1, col=1)
    
    # Volumen
    colors = ['#00ffad' if hist_data['Close'].iloc[i] >= hist_data['Open'].iloc[i] 
              else '#f23645' for i in range(len(hist_data))]
    
    fig.add_trace(go.Bar(
        x=hist_data.index,
        y=hist_data['Volume'],
        marker_color=colors,
        name='Volumen',
        opacity=0.3
    ), row=2, col=1)
    
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='#0c0e12',
        paper_bgcolor='#11141a',
        font=dict(color='white', size=10),
        xaxis_rangeslider_visible=False,
        height=450,
        showlegend=False,
        margin=dict(l=40, r=40, t=30, b=40)
    )
    
    fig.update_xaxes(gridcolor='#1a1e26', showgrid=True)
    fig.update_yaxes(gridcolor='#1a1e26', showgrid=True)
    fig.update_yaxes(title_text="Precio ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volumen", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

def render_analyst_section(data, recommendations):
    """Sección de análisis de analistas."""
    st.markdown("### 🎯 Consenso de Analistas")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Recomendación principal
        rec_color = get_recommendation_color(data['recommendation'])
        rec_text = get_recommendation_text(data['recommendation'])
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {rec_color}22 0%, {rec_color}11 100%);
            border: 1px solid {rec_color}44;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            height: 100%;
        ">
            <div style="color: #888; font-size: 11px; text-transform: uppercase; margin-bottom: 10px;">
                Recomendación Consenso
            </div>
            <div style="color: {rec_color}; font-size: 1.8rem; font-weight: bold; margin-bottom: 5px;">
                {rec_text}
            </div>
            <div style="color: #666; font-size: 12px;">
                Basado en {data['num_analysts']} analistas
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Targets
        st.markdown(f"""
        <div style="margin-top: 15px; background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 15px;">
            <div style="color: #888; font-size: 10px; text-transform: uppercase; margin-bottom: 10px;">Objetivos de Precio</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color: #666; font-size: 12px;">Alto:</span>
                <span style="color: #00ffad; font-weight: bold;">${data['target_high']:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color: #666; font-size: 12px;">Medio:</span>
                <span style="color: white; font-weight: bold;">${data['target_mean']:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #666; font-size: 12px;">Bajo:</span>
                <span style="color: #f23645; font-weight: bold;">${data['target_low']:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if recommendations:
            # Gráfico de barras de recomendaciones
            categories = ['Compra\nFuerte', 'Compra', 'Mantener', 'Vender', 'Venta\nFuerte']
            values = [
                recommendations.get('strongBuy', 0),
                recommendations.get('buy', 0),
                recommendations.get('hold', 0),
                recommendations.get('sell', 0),
                recommendations.get('strongSell', 0)
            ]
            colors = ['#00ffad', '#4caf50', '#ff9800', '#f23645', '#d32f2f']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=categories,
                    y=values,
                    marker_color=colors,
                    text=values,
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                template="plotly_dark",
                plot_bgcolor='#0c0e12',
                paper_bgcolor='#11141a',
                font=dict(color='white', size=10),
                height=250,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
                yaxis_title="Nº Analistas",
                xaxis_tickfont_size=9
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de recomendaciones disponibles")

def render_earnings_calendar(earnings_dates):
    """Calendario de earnings real."""
    st.markdown("### 📅 Calendario de Resultados")
    
    if earnings_dates:
        cols = st.columns(min(len(earnings_dates), 4))
        for col, earning in zip(cols, earnings_dates):
            with col:
                st.markdown(f"""
                <div style="
                    background: #0c0e12;
                    border: 1px solid #2a3f5f;
                    border-radius: 10px;
                    padding: 15px;
                    text-align: center;
                ">
                    <div style="color: #00ffad; font-size: 12px; font-weight: bold; margin-bottom: 5px;">
                        📊 PRÓXIMO
                    </div>
                    <div style="color: white; font-size: 1.3rem; font-weight: bold; margin-bottom: 5px;">
                        {earning['date']}
                    </div>
                    <div style="color: #666; font-size: 11px;">
                        EPS Est: {earning['eps_est']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No hay fechas de earnings disponibles")

def render_financial_health(data):
    """Salud financiera."""
    st.markdown("### 💰 Salud Financiera")
    
    cols = st.columns(3)
    
    with cols[0]:
        st.markdown(f"""
        <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 20px;">
            <div style="color: #888; font-size: 11px; text-transform: uppercase; margin-bottom: 10px;">💵 Efectivo</div>
            <div style="color: #00ffad; font-size: 1.5rem; font-weight: bold;">{format_value(data['cash'], '$')}</div>
            <div style="color: #666; font-size: 11px; margin-top: 5px;">Total en balance</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        fcf_color = "#00ffad" if data['free_cashflow'] and data['free_cashflow'] > 0 else "#f23645"
        st.markdown(f"""
        <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 20px;">
            <div style="color: #888; font-size: 11px; text-transform: uppercase; margin-bottom: 10px;">🌊 Free Cash Flow</div>
            <div style="color: {fcf_color}; font-size: 1.5rem; font-weight: bold;">{format_value(data['free_cashflow'], '$')}</div>
            <div style="color: #666; font-size: 11px; margin-top: 5px;">Generación anual</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        debt_color = "#f23645" if data['debt_to_equity'] and data['debt_to_equity'] > 100 else "#00ffad"
        st.markdown(f"""
        <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 20px;">
            <div style="color: #888; font-size: 11px; text-transform: uppercase; margin-bottom: 10px;">⚖️ Deuda/Patrimonio</div>
            <div style="color: {debt_color}; font-size: 1.5rem; font-weight: bold;">{format_value(data['debt_to_equity'], '', '%', 1)}</div>
            <div style="color: #666; font-size: 11px; margin-top: 5px;">Ratio de apalancamiento</div>
        </div>
        """, unsafe_allow_html=True)

def render_dividends(data):
    """Sección de dividendos."""
    if data['dividend_yield'] and data['dividend_yield'] > 0:
        st.markdown("### 💎 Dividendos")
        
        yield_pct = data['dividend_yield'] * 100
        cols = st.columns(3)
        
        with cols[0]:
            st.markdown(f"""
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 20px; text-align: center;">
                <div style="color: #888; font-size: 11px; text-transform: uppercase; margin-bottom: 10px;">Yield</div>
                <div style="color: #00ffad; font-size: 2rem; font-weight: bold;">{yield_pct:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown(f"""
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 20px; text-align: center;">
                <div style="color: #888; font-size: 11px; text-transform: uppercase; margin-bottom: 10px;">Anual</div>
                <div style="color: white; font-size: 2rem; font-weight: bold;">${data['dividend_rate']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            ex_date = datetime.fromtimestamp(data['ex_div_date']).strftime('%d/%m/%Y') if data['ex_div_date'] else 'N/A'
            st.markdown(f"""
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 20px; text-align: center;">
                <div style="color: #888; font-size: 11px; text-transform: uppercase; margin-bottom: 10px;">Ex-Dividendo</div>
                <div style="color: white; font-size: 1.5rem; font-weight: bold;">{ex_date}</div>
            </div>
            """, unsafe_allow_html=True)

def render_insider_trading(insider_data):
    """Tabla de insider trading."""
    st.markdown("### 🏦 Insider Trading (Últimos 30 días)")
    
    if insider_data:
        df = pd.DataFrame(insider_data)
        st.dataframe(
            df[['date', 'insider', 'relation', 'transaction', 'shares', 'price', 'value']],
            column_config={
                'date': 'Fecha',
                'insider': 'Insider',
                'relation': 'Cargo',
                'transaction': 'Tipo',
                'shares': 'Acciones',
                'price': 'Precio',
                'value': 'Valor ($)'
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No hay datos de insider trading disponibles (requiere conexión a OpenInsider)")

def render_news(news_list):
    """Noticias reales."""
    st.markdown("### 📰 Noticias Recientes")
    
    if news_list:
        for news in news_list:
            st.markdown(f"""
            <div style="
                background: #0c0e12;
                border-left: 3px solid #00ffad;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 0 8px 8px 0;
            ">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #00ffad; font-size: 11px; font-weight: bold;">{news['source']}</span>
                    <span style="color: #666; font-size: 11px;">{news['datetime']}</span>
                </div>
                <div style="color: white; font-size: 14px; font-weight: 500; margin-bottom: 5px;">
                    {news['headline']}
                </div>
                <div style="color: #888; font-size: 12px; line-height: 1.4;">
                    {news['summary']}
                </div>
                <a href="{news['url']}" target="_blank" style="color: #00ffad; font-size: 11px; text-decoration: none;">
                    Leer más →
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No hay noticias recientes")

def render_outlook_real(data):
    """Perspectivas basadas en datos reales."""
    st.markdown("### 🔮 Perspectivas y Desafíos")
    
    # Generar puntos basados en métricas reales
    positive_points = []
    challenge_points = []
    
    if data['rev_growth'] and data['rev_growth'] > 0.1:
        positive_points.append(f"Crecimiento de ingresos sólido ({data['rev_growth']:.1%})")
    elif data['rev_growth'] and data['rev_growth'] < 0:
        challenge_points.append("Contracción de ingresos reciente")
    
    if data['free_cashflow'] and data['free_cashflow'] > 0:
        positive_points.append(f"Generación positiva de FCF ({format_value(data['free_cashflow'], '$')})")
    else:
        challenge_points.append("Free Cash Flow negativo o limitado")
    
    if data['roe'] and data['roe'] > 0.15:
        positive_points.append(f"ROE elevado ({data['roe']:.1%}) indica eficiencia")
    elif data['roe'] and data['roe'] < 0.08:
        challenge_points.append("ROE bajo sugiere menor rentabilidad")
    
    if data['debt_to_equity'] and data['debt_to_equity'] < 50:
        positive_points.append("Balance poco apalancado (Deuda/Patrimonio < 50%)")
    elif data['debt_to_equity'] and data['debt_to_equity'] > 100:
        challenge_points.append("Alto nivel de apalancamiento financiero")
    
    if data['eps_growth'] and data['eps_growth'] > 0.1:
        positive_points.append(f"Crecimiento de EPS acelerado ({data['eps_growth']:.1%})")
    
    if data['profit_margin'] and data['profit_margin'] > 0.15:
        positive_points.append(f"Márgenes de beneficio saludables ({data['profit_margin']:.1%})")
    elif data['profit_margin'] and data['profit_margin'] < 0.05:
        challenge_points.append("Márgenes de beneficio comprimidos")
    
    # Rellenar si faltan puntos
    while len(positive_points) < 3:
        positive_points.append("Posición de mercado establecida en su sector")
    while len(challenge_points) < 3:
        challenge_points.append("Entorno macroeconómico competitivo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        points_html = "".join([f"<li style='margin-bottom: 8px;'>{p}</li>" for p in positive_points[:4]])
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(0,255,173,0.1) 0%, rgba(0,255,173,0.05) 100%);
            border: 1px solid #00ffad44;
            border-radius: 12px;
            padding: 25px;
            height: 100%;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <div style="
                    width: 40px; height: 40px; background: #00ffad22; border-radius: 50%;
                    display: flex; align-items: center; justify-content: center;
                    margin-right: 15px; font-size: 20px;
                ">📈</div>
                <h3 style="color: #00ffad; margin: 0; font-size: 1.2rem;">Perspectivas Positivas</h3>
            </div>
            <ul style="color: #ccc; line-height: 1.6; padding-left: 20px; margin: 0;">
                {points_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        points_html = "".join([f"<li style='margin-bottom: 8px;'>{c}</li>" for c in challenge_points[:4]])
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(242,54,69,0.1) 0%, rgba(242,54,69,0.05) 100%);
            border: 1px solid #f2364544;
            border-radius: 12px;
            padding: 25px;
            height: 100%;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <div style="
                    width: 40px; height: 40px; background: #f2364522; border-radius: 50%;
                    display: flex; align-items: center; justify-content: center;
                    margin-right: 15px; font-size: 20px;
                ">⚠️</div>
                <h3 style="color: #f23645; margin: 0; font-size: 1.2rem;">Desafíos Pendientes</h3>
            </div>
            <ul style="color: #ccc; line-height: 1.6; padding-left: 20px; margin: 0;">
                {points_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)

def render_ai_analysis_enhanced(data):
    """Análisis IA mejorado con datos reales."""
    st.markdown("### 🤖 Análisis Inteligente Capyfin")
    
    model, name, err = get_ia_model()
    if not model:
        st.warning(f"IA no disponible: {err}")
        return
    
    prompt = f"""
    Actúa como analista senior de Capyfin. Realiza un análisis profesional de {data['name']} ({data['ticker']}) 
    basado EXCLUSIVAMENTE en estos datos reales:
    
    📊 DATOS FINANCIEROS CLAVE:
    • Precio: ${data['price']:.2f} (Cambio: {data['change_pct']:+.2f}%)
    • Market Cap: {format_value(data['market_cap'], '$')}
    • Crecimiento Ingresos: {format_value(data['rev_growth'], '', '%', 1)}
    • Margen EBITDA: {format_value(data['ebitda_margin'], '', '%', 1)}
    • Margen Neto: {format_value(data['profit_margin'], '', '%', 1)}
    • P/E Forward: {format_value(data['pe_forward'], '', 'x', 1)}
    • PEG Ratio: {format_value(data['peg_ratio'], '', '', 2)}
    • ROE: {format_value(data['roe'], '', '%', 1)}
    • Free Cash Flow: {format_value(data['free_cashflow'], '$')}
    • Deuda/Patrimonio: {format_value(data['debt_to_equity'], '', '%', 1)}
    • Beta: {data['beta']:.2f}
    
    🎯 CONSENSO ANALISTAS:
    • Recomendación: {get_recommendation_text(data['recommendation'])}
    • Objetivo medio: ${data['target_mean']:.2f}
    • Número de analistas: {data['num_analysts']}
    
    Genera un análisis estructurado en español:
    
    ### 📝 RESUMEN EJECUTIVO (3-4 líneas con valoración general)
    
    ### ✅ FORTALEZAS CLAVE (3-4 puntos específicos basados en las métricas superiores a la media)
    
    ### ⚠️ PUNTOS DE ATENCIÓN (3-4 riesgos objetivos basados en métricas débiles)
    
    ### 🎯 VEREDICTO (Compra/Mantener/Vender con precio objetivo implícito y horizonte temporal)
    
    Usa formato markdown con emojis. Sé conciso pero técnico. Menciona números específicos.
    """
    
    try:
        with st.spinner("Generando análisis profundo con IA..."):
            response = model.generate_content(prompt)
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%);
                border: 1px solid #2a3f5f;
                border-radius: 12px;
                padding: 25px;
            ">
                <div style="color: #ddd; line-height: 1.8; font-size: 14px;">
                    {response.text}
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error generando análisis: {e}")

# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    # CSS Global
    st.markdown("""
    <style>
        .stApp { background-color: #0c0e12; }
        .stTextInput > div > div > input {
            background-color: #1a1e26;
            color: white;
            border: 1px solid #2a3f5f;
            border-radius: 8px;
            padding: 12px;
        }
        .stButton > button {
            background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%);
            color: #0c0e12;
            border: none;
            border-radius: 8px;
            padding: 12px 30px;
            font-weight: bold;
            font-size: 14px;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,255,173,0.3);
        }
        h1, h2, h3 { color: white !important; }
        .stDataFrame { background-color: #0c0e12 !important; }
        .css-1d391kg { background-color: #11141a; }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("📅 Análisis de Earnings")
    st.markdown("""
    <div style="color: #888; margin-bottom: 30px;">
        Reportes trimestrales completos con datos fundamentales, técnicos y análisis de IA en tiempo real
    </div>
    """, unsafe_allow_html=True)

    # Input
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ticker = st.text_input("Introduce el Ticker", value="NVDA", placeholder="Ej: AAPL, MSFT, TSLA...").upper().strip()
    
    with col2:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 Analizar Empresa", use_container_width=True)
    
    with col3:
        st.write("")
        st.write("")
        if st.button("🎲 Aleatorio", use_container_width=True):
            import random
            tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "AMD", "CRM", "ADBE", "PYPL", "INTC", "DIS", "KO"]
            ticker = random.choice(tickers)
            st.session_state['random_ticker'] = ticker
            analyze_btn = True
    
    if 'random_ticker' in st.session_state:
        ticker = st.session_state['random_ticker']
        del st.session_state['random_ticker']

    if analyze_btn and ticker:
        with st.spinner(f"Cargando datos completos de {ticker}..."):
            data, stock = get_comprehensive_earnings_data(ticker)
            
            if not data:
                st.error(f"""
                ❌ No se pudieron obtener datos para **{ticker}**.
                
                Verifica que el ticker sea correcto o intenta con otro símbolo.
                """)
                return

            # Obtener datos adicionales
            earnings_dates = get_earnings_calendar_real(stock, ticker)
            recommendations = get_analyst_recommendations(stock)
            insider_data = get_insider_trading_real(ticker)
            
            # API Key para noticias
            api_key = st.secrets.get("FINNHUB_API_KEY", None)
            news = fetch_finnhub_news_symbol(ticker, api_key) if api_key else []
            
            # RENDERIZADO
            render_header(data)
            render_price_stats(data)
            
            st.markdown("---")
            
            # Layout principal: Gráfico + Info
            col_chart, col_info = st.columns([3, 2])
            
            with col_chart:
                render_chart(data['hist'], ticker)
            
            with col_info:
                st.markdown("#### 📋 Resumen del Negocio")
                summary = data['summary'][:400] + "..." if len(data['summary']) > 400 else data['summary']
                st.markdown(f"""
                <div style="
                    background: #0c0e12;
                    border: 1px solid #1a1e26;
                    border-radius: 10px;
                    padding: 20px;
                    height: 200px;
                    overflow-y: auto;
                    color: #aaa;
                    font-size: 13px;
                    line-height: 1.6;
                    margin-bottom: 20px;
                ">
                    {summary}
                </div>
                """, unsafe_allow_html=True)
                
                # Mini métricas
                st.markdown(f"""
                <div style="background: #0c0e12; border-radius: 8px; padding: 15px; border: 1px solid #1a1e26;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span style="color: #666; font-size: 12px;">Beta:</span>
                        <span style="color: white; font-weight: bold;">{data['beta']:.2f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span style="color: #666; font-size: 12px;">52S vs Máx:</span>
                        <span style="color: {'#00ffad' if data['pct_from_high'] > -10 else '#f23645'}; font-weight: bold;">{data['pct_from_high']:.1f}%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #666; font-size: 12px;">Vol/Me:</span>
                        <span style="color: white; font-weight: bold;">{format_value(data['avg_volume'], '', '', 0)}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            render_fundamental_metrics(data)
            
            st.markdown("---")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                render_analyst_section(data, recommendations)
            
            with col2:
                render_earnings_calendar(earnings_dates)
            
            st.markdown("---")
            render_financial_health(data)
            
            if data['dividend_yield'] and data['dividend_yield'] > 0:
                render_dividends(data)
            
            st.markdown("---")
            render_outlook_real(data)
            
            if insider_data:
                st.markdown("---")
                render_insider_trading(insider_data)
            
            if news:
                st.markdown("---")
                render_news(news)
            
            st.markdown("---")
            render_ai_analysis_enhanced(data)
            
            # Footer
            st.markdown("""
            <div style="
                text-align: center;
                color: #444;
                font-size: 12px;
                margin-top: 40px;
                padding: 20px;
                border-top: 1px solid #1a1e26;
            ">
                Datos proporcionados por Yahoo Finance & Finnhub • Análisis generado por IA Gemini<br>
                <span style="color: #00ffad;">Capyfin Dashboard Pro</span> • Para fines informativos únicamente
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
