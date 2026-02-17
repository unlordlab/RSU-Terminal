import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from config import get_ia_model
import time
import random
from functools import wraps
import hashlib
import requests
import os
import re

# ────────────────────────────────────────────────
# CONFIGURACIÓN Y LOGGING
# ────────────────────────────────────────────────

def rate_limit_delay():
    time.sleep(random.uniform(0.3, 0.8))

def log_debug(message):
    """Helper para debug en Streamlit."""
    print(f"[DEBUG] {message}")

# ────────────────────────────────────────────────
# CARGA DE PROMPT RSU
# ────────────────────────────────────────────────

def load_rsu_prompt():
    """Carga el prompt de análisis hedge fund desde earnings.txt en raíz."""
    try:
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'earnings.txt'),
            os.path.join(os.path.dirname(__file__), 'earnings.txt'),
            os.path.join(os.getcwd(), 'earnings.txt'),
            os.path.join(os.getcwd(), 'modules', '..', 'earnings.txt'),
            'earnings.txt',
        ]
        
        for prompt_path in possible_paths:
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        log_debug(f"Prompt cargado desde: {prompt_path}")
                        return content
        
        st.warning("⚠️ No se encontró earnings.txt, usando prompt embebido")
        return get_embedded_prompt()
        
    except Exception as e:
        log_debug(f"Error cargando prompt RSU: {e}")
        return get_embedded_prompt()

def get_embedded_prompt():
    """Prompt embebido como fallback."""
    return """Eres un analista de hedge fund senior. Analiza la empresa usando estos datos:

{datos_ticker}

Genera un análisis fundamental con:
1. Snapshot ejecutivo (precio, market cap, thesis 1 línea)
2. Valoración relativa (P/E, PEG análisis)
3. Calidad del negocio (márgenes, ROE, ROA)
4. Salud financiera (cash, deuda, FCF)
5. Dinámica de mercado (vs 52 semanas, consenso analistas)
6. Catalysts y riesgos
7. Bull/Bear/Base case
8. Score /10 y recomendación final

Fecha actual: {current_date}
Sé específico con los números proporcionados."""

# ────────────────────────────────────────────────
# FINANCIAL MODELING PREP API - DATOS FUNDAMENTALES
# ────────────────────────────────────────────────

def get_fmp_data(ticker, api_key):
    """Obtiene datos completos de Financial Modeling Prep API."""
    if not api_key:
        log_debug("FMP_API_KEY no configurado")
        return None
    
    try:
        base_url = "https://financialmodelingprep.com/api/v3"
        
        log_debug(f"Solicitando datos FMP para {ticker}...")
        
        # Income Statement (últimos 4 trimestres)
        income_url = f"{base_url}/income-statement/{ticker}?period=quarter&limit=8&apikey={api_key}"
        income_resp = requests.get(income_url, timeout=15)
        income = income_resp.json() if income_resp.status_code == 200 else []
        log_debug(f"Income Statement: {len(income)} registros")
        
        # Balance Sheet (para cash, deuda, etc)
        balance_url = f"{base_url}/balance-sheet-statement/{ticker}?period=quarter&limit=1&apikey={api_key}"
        balance_resp = requests.get(balance_url, timeout=15)
        balance = balance_resp.json() if balance_resp.status_code == 200 else []
        log_debug(f"Balance Sheet: {len(balance)} registros")
        
        # Cash Flow Statement (para FCF)
        cashflow_url = f"{base_url}/cash-flow-statement/{ticker}?period=quarter&limit=1&apikey={api_key}"
        cashflow_resp = requests.get(cashflow_url, timeout=15)
        cashflow = cashflow_resp.json() if cashflow_resp.status_code == 200 else []
        log_debug(f"Cash Flow: {len(cashflow)} registros")
        
        # Key Metrics (ROE, márgenes, ratios)
        metrics_url = f"{base_url}/key-metrics/{ticker}?period=quarter&limit=1&apikey={api_key}"
        metrics_resp = requests.get(metrics_url, timeout=15)
        metrics = metrics_resp.json() if metrics_resp.status_code == 200 else []
        log_debug(f"Key Metrics: {len(metrics)} registros")
        
        # Financial Ratios
        ratios_url = f"{base_url}/ratios/{ticker}?period=quarter&limit=1&apikey={api_key}"
        ratios_resp = requests.get(ratios_url, timeout=15)
        ratios = ratios_resp.json() if ratios_resp.status_code == 200 else []
        log_debug(f"Ratios: {len(ratios)} registros")
        
        # Earnings Surprises
        surprises_url = f"{base_url}/earnings-surprises/{ticker}?apikey={api_key}"
        surprises_resp = requests.get(surprises_url, timeout=15)
        surprises = surprises_resp.json() if surprises_resp.status_code == 200 else []
        
        # Earnings Calendar
        calendar_url = f"{base_url}/earning_calendar/{ticker}?apikey={api_key}"
        calendar_resp = requests.get(calendar_url, timeout=15)
        calendar = calendar_resp.json() if calendar_resp.status_code == 200 else []
        
        # Analyst Estimates
        estimates_url = f"{base_url}/analyst-estimates/{ticker}?period=quarter&limit=4&apikey={api_key}"
        estimates_resp = requests.get(estimates_url, timeout=15)
        estimates = estimates_resp.json() if estimates_resp.status_code == 200 else []
        
        # Company Profile (para sector, industria, etc)
        profile_url = f"{base_url}/profile/{ticker}?apikey={api_key}"
        profile_resp = requests.get(profile_url, timeout=15)
        profile = profile_resp.json() if profile_resp.status_code == 200 else []
        profile = profile[0] if profile else {}
        
        # Quote (precio actual)
        quote_url = f"{base_url}/quote/{ticker}?apikey={api_key}"
        quote_resp = requests.get(quote_url, timeout=15)
        quote = quote_resp.json() if quote_resp.status_code == 200 else []
        quote = quote[0] if quote else {}
        
        return {
            'income_statement': income,
            'balance_sheet': balance,
            'cash_flow': cashflow,
            'key_metrics': metrics,
            'ratios': ratios,
            'earnings_surprises': surprises,
            'earnings_calendar': calendar,
            'analyst_estimates': estimates,
            'profile': profile,
            'quote': quote,
            'source': 'fmp',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        log_debug(f"Error FMP: {e}")
        return None

# ────────────────────────────────────────────────
# EXTRACCIÓN DE DATOS FUNDAMENTALES DESDE FMP
# ────────────────────────────────────────────────

def extract_fundamentals_from_fmp(fmp_data):
    """Extrae métricas fundamentales de los datos de FMP."""
    if not fmp_data:
        return {}
    
    fundamentals = {}
    
    try:
        # Datos del quote (precio actual)
        quote = fmp_data.get('quote', {})
        if quote:
            fundamentals['price'] = quote.get('price', 0)
            fundamentals['market_cap'] = quote.get('marketCap', 0)
            fundamentals['volume'] = quote.get('volume', 0)
            fundamentals['avg_volume'] = quote.get('avgVolume', 0)
            fundamentals['change_pct'] = quote.get('changesPercentage', 0)
            fundamentals['prev_close'] = quote.get('previousClose', 0)
            fundamentals['open'] = quote.get('open', 0)
            fundamentals['day_high'] = quote.get('dayHigh', 0)
            fundamentals['day_low'] = quote.get('dayLow', 0)
            fundamentals['fifty_two_high'] = quote.get('yearHigh', 0)
            fundamentals['fifty_two_low'] = quote.get('yearLow', 0)
            fundamentals['beta'] = quote.get('beta', 0)
            fundamentals['eps'] = quote.get('eps', 0)
            fundamentals['pe_trailing'] = quote.get('pe', 0)
        
        # Datos del perfil
        profile = fmp_data.get('profile', {})
        if profile:
            fundamentals['name'] = profile.get('companyName', '')
            fundamentals['sector'] = profile.get('sector', 'N/A')
            fundamentals['industry'] = profile.get('industry', 'N/A')
            fundamentals['country'] = profile.get('country', 'N/A')
            fundamentals['employees'] = profile.get('fullTimeEmployees', 0)
            fundamentals['website'] = profile.get('website', '#')
            fundamentals['summary'] = profile.get('description', f"Empresa {fundamentals.get('ticker', '')}")
            fundamentals['exchange'] = profile.get('exchange', 'N/A')
        
        # Key Metrics (ratios financieros)
        metrics = fmp_data.get('key_metrics', [])
        if metrics:
            m = metrics[0]
            fundamentals['pe_forward'] = m.get('peRatio', 0)
            fundamentals['price_to_book'] = m.get('pbRatio', 0)
            fundamentals['price_to_sales'] = m.get('priceToSalesRatio', 0)
            fundamentals['peg_ratio'] = m.get('pegRatio', 0)
            fundamentals['roe'] = m.get('roe', 0)
            fundamentals['roa'] = m.get('roa', 0)
            fundamentals['debt_to_equity'] = m.get('debtToEquity', 0)
            fundamentals['current_ratio'] = m.get('currentRatio', 0)
            fundamentals['quick_ratio'] = m.get('quickRatio', 0)
            fundamentals['dividend_yield'] = m.get('dividendYield', 0)
            fundamentals['payout_ratio'] = m.get('payoutRatio', 0)
        
        # Financial Ratios (márgenes)
        ratios = fmp_data.get('ratios', [])
        if ratios:
            r = ratios[0]
            fundamentals['gross_margin'] = r.get('grossProfitMargin', 0)
            fundamentals['operating_margin'] = r.get('operatingProfitMargin', 0)
            fundamentals['profit_margin'] = r.get('netProfitMargin', 0)
            fundamentals['ebitda_margin'] = r.get('ebitdaMargin', 0)
            fundamentals['rev_growth'] = r.get('revenueGrowth', 0)
            fundamentals['eps_growth'] = r.get('epsgrowth', 0)
        
        # Balance Sheet (cash y deuda)
        balance = fmp_data.get('balance_sheet', [])
        if balance:
            b = balance[0]
            fundamentals['cash'] = b.get('cashAndCashEquivalents', 0)
            fundamentals['total_debt'] = b.get('totalDebt', 0)
            fundamentals['total_equity'] = b.get('totalStockholdersEquity', 0)
            fundamentals['total_assets'] = b.get('totalAssets', 0)
        
        # Cash Flow (FCF)
        cashflow = fmp_data.get('cash_flow', [])
        if cashflow:
            c = cashflow[0]
            fundamentals['operating_cashflow'] = c.get('operatingCashFlow', 0)
            fundamentals['capital_expenditure'] = c.get('capitalExpenditure', 0)
            # Calcular FCF
            ocf = c.get('operatingCashFlow', 0)
            capex = c.get('capitalExpenditure', 0)
            fundamentals['free_cashflow'] = ocf - capex if ocf and capex else 0
        
        # Analyst data
        estimates = fmp_data.get('analyst_estimates', [])
        if estimates:
            e = estimates[0]
            fundamentals['eps_forward'] = e.get('estimatedEps', 0)
            fundamentals['target_mean'] = e.get('targetPrice', 0)
            fundamentals['num_analysts'] = e.get('numberOfAnalysts', 0)
        
        # Calcular pct_from_high
        if fundamentals.get('price') and fundamentals.get('fifty_two_high'):
            fundamentals['pct_from_high'] = ((fundamentals['price'] - fundamentals['fifty_two_high']) / fundamentals['fifty_two_high']) * 100
        
        log_debug(f"Fundamentos extraídos: {len(fundamentals)} campos")
        log_debug(f"Precio: {fundamentals.get('price')}, MarketCap: {fundamentals.get('market_cap')}, ROE: {fundamentals.get('roe')}")
        
    except Exception as e:
        log_debug(f"Error extrayendo fundamentos: {e}")
    
    return fundamentals

# ────────────────────────────────────────────────
# FORMATO DE DATOS FMP PARA EL PROMPT
# ────────────────────────────────────────────────

def format_fmp_earnings_data(fmp_data):
    """Formatea datos de FMP para el prompt con información reciente."""
    if not fmp_data:
        return "No disponible"
    
    result = []
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    result.append(f"=== DATOS ACTUALIZADOS AL: {current_date} ===\n")
    
    # Income Statement - Últimos 4 trimestres
    income = fmp_data.get('income_statement', [])
    if income:
        result.append("=== INCOME STATEMENT (Últimos trimestres) ===")
        for i in income[:4]:
            date = i.get('date', 'N/D')
            period = i.get('period', 'N/D')
            revenue = i.get('revenue', 0)
            net_income = i.get('netIncome', 0)
            eps = i.get('eps', 0)
            ebitda = i.get('ebitda', 0)
            gross_profit = i.get('grossProfit', 0)
            operating_income = i.get('operatingIncome', 0)
            
            result.append(f"\n{date} ({period}):")
            result.append(f"  Revenue: ${revenue:,.0f} | Net Income: ${net_income:,.0f} | EPS: ${eps:.2f}")
            result.append(f"  EBITDA: ${ebitda:,.0f} | Gross Profit: ${gross_profit:,.0f} | Operating Income: ${operating_income:,.0f}")
            
            if revenue > 0:
                gross_margin = (gross_profit / revenue) * 100
                operating_margin = (operating_income / revenue) * 100
                net_margin = (net_income / revenue) * 100
                result.append(f"  Márgenes: Gross {gross_margin:.1f}% | Operating {operating_margin:.1f}% | Net {net_margin:.1f}%")
    
    # Earnings Surprises
    surprises = fmp_data.get('earnings_surprises', [])
    if surprises:
        result.append("\n\n=== EARNINGS SURPRISES (Actual vs Estimate) ===")
        for s in surprises[:6]:
            date = s.get('date', 'N/D')
            actual = s.get('actualEarningResult', 'N/D')
            estimate = s.get('estimatedEarning', 'N/D')
            surprise_pct = s.get('surprisePercentage', 'N/D')
            
            try:
                actual_f = float(actual) if actual != 'N/D' else 0
                estimate_f = float(estimate) if estimate != 'N/D' else 0
                beat_miss = "BEAT ✅" if actual_f > estimate_f else "MISS ❌" if actual_f < estimate_f else "IN LINE ➖"
            except:
                beat_miss = "N/D"
            
            result.append(f"{date}: Actual ${actual} vs Est ${estimate} | Surprise: {surprise_pct}% {beat_miss}")
    
    # Analyst Estimates
    estimates = fmp_data.get('analyst_estimates', [])
    if estimates:
        result.append("\n\n=== ANALYST ESTIMATES (Próximos períodos) ===")
        for e in estimates[:4]:
            date = e.get('date', 'N/D')
            period = e.get('period', 'N/D')
            eps_est = e.get('estimatedEps', 'N/D')
            revenue_est = e.get('estimatedRevenue', 'N/D')
            result.append(f"{date} ({period}): EPS Est ${eps_est} | Revenue Est ${revenue_est:,.0f}" if isinstance(revenue_est, (int, float)) else f"{date} ({period}): EPS Est ${eps_est}")
    
    # Próximos earnings
    calendar = fmp_data.get('earnings_calendar', [])
    if calendar:
        result.append("\n\n=== PRÓXIMOS EARNINGS PROGRAMADOS ===")
        for c in calendar[:2]:
            date = c.get('date', 'TBA')
            eps_est = c.get('epsEstimated', 'N/D')
            revenue_est = c.get('revenueEstimated', 'N/D')
            result.append(f"Fecha: {date} | EPS Est: ${eps_est}" + (f" | Revenue Est: ${revenue_est:,.0f}" if isinstance(revenue_est, (int, float)) else ""))
    
    return "\n".join(result) if result else "No disponible"

def get_latest_earnings_summary(fmp_data):
    """Extrae el resumen del último earnings report."""
    if not fmp_data:
        return None
    
    income = fmp_data.get('income_statement', [])
    surprises = fmp_data.get('earnings_surprises', [])
    
    if not income:
        return None
    
    latest = income[0]
    latest_surprise = surprises[0] if surprises else {}
    
    revenue_growth = None
    eps_growth = None
    
    if len(income) >= 5:
        try:
            current_rev = latest.get('revenue', 0)
            current_eps = latest.get('eps', 0)
            yoy = income[4]
            if yoy:
                yoy_rev = yoy.get('revenue', 0)
                yoy_eps = yoy.get('eps', 0)
                if yoy_rev > 0:
                    revenue_growth = ((current_rev - yoy_rev) / yoy_rev) * 100
                if yoy_eps != 0:
                    eps_growth = ((current_eps - yoy_eps) / abs(yoy_eps)) * 100
        except:
            pass
    
    return {
        'date': latest.get('date', 'N/D'),
        'period': latest.get('period', 'N/D'),
        'revenue': latest.get('revenue', 0),
        'net_income': latest.get('netIncome', 0),
        'eps': latest.get('eps', 0),
        'ebitda': latest.get('ebitda', 0),
        'gross_profit': latest.get('grossProfit', 0),
        'operating_income': latest.get('operatingIncome', 0),
        'revenue_growth_yoy': revenue_growth,
        'eps_growth_yoy': eps_growth,
        'eps_surprise_pct': latest_surprise.get('surprisePercentage', 0),
        'eps_beat': latest_surprise.get('actualEarningResult', 0) > latest_surprise.get('estimatedEarning', 0) if latest_surprise else False
    }

# ────────────────────────────────────────────────
# VISUALIZACIÓN DE EARNINGS REPORT
# ────────────────────────────────────────────────

def render_earnings_report_section(data, fmp_data):
    """Renderiza una sección de earnings report estilo profesional."""
    
    if not fmp_data:
        st.info("📊 Datos de FMP no disponibles. Configura FMP_API_KEY en secrets para ver el reporte completo.")
        return
    
    latest = get_latest_earnings_summary(fmp_data)
    
    if not latest:
        st.warning("⚠️ No se pudieron obtener datos recientes de earnings")
        return
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px;">
        <div style="color: #00ffad; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px;">
            📅 {latest['date']} • {data['ticker']} Earnings Report
        </div>
        <h2 style="color: white; margin: 0; font-size: 2rem;">
            {data['name']} {latest['period']} Earnings
        </h2>
        <p style="color: #888; margin-top: 10px;">
            {data['sector']} • {data.get('industry', 'N/A')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        revenue = latest['revenue']
        rev_growth = latest['revenue_growth_yoy']
        rev_color = "#00ffad" if rev_growth and rev_growth > 0 else "#f23645" if rev_growth and rev_growth < 0 else "#888"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">Total Revenue</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${revenue/1e9:.2f}B</div>
            {f'<div style="color: {rev_color}; font-size: 12px; margin-top: 5px;">{"▲" if rev_growth > 0 else "▼"} {abs(rev_growth):.1f}% YoY</div>' if rev_growth else '<div style="color: #666; font-size: 12px;">N/D</div>'}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        eps = latest['eps']
        eps_growth = latest['eps_growth_yoy']
        eps_surprise = latest['eps_surprise_pct']
        eps_color = "#00ffad" if eps_growth and eps_growth > 0 else "#f23645"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">EPS</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${eps:.2f}</div>
            {f'<div style="color: {eps_color}; font-size: 12px; margin-top: 5px;">{"▲" if eps_growth > 0 else "▼"} {abs(eps_growth):.1f}% YoY</div>' if eps_growth else ''}
            {f'<div style="color: #00ffad; font-size: 11px; margin-top: 3px;">Beat by {eps_surprise}%</div>' if latest['eps_beat'] and eps_surprise else ''}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        net_income = latest['net_income']
        margin = (net_income / latest['revenue'] * 100) if latest['revenue'] > 0 else 0
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">Net Income</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${net_income/1e6:.0f}M</div>
            <div style="color: #888; font-size: 12px; margin-top: 5px;">{margin:.1f}% Margin</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        ebitda = latest['ebitda']
        ebitda_margin = (ebitda / latest['revenue'] * 100) if latest['revenue'] > 0 else 0
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">EBITDA</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${ebitda/1e6:.0f}M</div>
            <div style="color: #888; font-size: 12px; margin-top: 5px;">{ebitda_margin:.1f}% Margin</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    render_earnings_history_chart(fmp_data)
    
    st.markdown("---")
    render_forward_guidance(fmp_data, data)
    
    st.markdown("---")
    render_earnings_surprises(fmp_data)

def render_earnings_history_chart(fmp_data):
    """Renderiza gráfico histórico de revenue y EPS."""
    income = fmp_data.get('income_statement', [])
    
    if not income or len(income) < 2:
        st.info("📊 Datos históricos insuficientes")
        return
    
    dates = []
    revenues = []
    eps_values = []
    
    for i in reversed(income[:8]):
        dates.append(i.get('date', ''))
        revenues.append(i.get('revenue', 0) / 1e9)
        eps_values.append(i.get('eps', 0))
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=dates,
            y=revenues,
            name='Revenue (B$)',
            marker_color='#2a3f5f',
            opacity=0.8
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=eps_values,
            name='EPS ($)',
            mode='lines+markers',
            line=dict(color='#00ffad', width=3),
            marker=dict(size=8, color='#00ffad', symbol='diamond')
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title="📈 Revenue & EPS History (Quarterly)",
        template="plotly_dark",
        plot_bgcolor='#0c0e12',
        paper_bgcolor='#11141a',
        font=dict(color='white', size=11),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode='x unified'
    )
    
    fig.update_xaxes(gridcolor='#1a1e26', showgrid=True, tickangle=-45)
    fig.update_yaxes(title_text="Revenue (Billions $)", secondary_y=False, gridcolor='#1a1e26')
    fig.update_yaxes(title_text="EPS ($)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

def render_forward_guidance(fmp_data, data):
    """Renderiza sección de forward guidance."""
    
    estimates = fmp_data.get('analyst_estimates', [])
    calendar = fmp_data.get('earnings_calendar', [])
    
    st.markdown("### 🎯 Forward Guidance & Expectativas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(0,255,173,0.1) 0%, rgba(0,255,173,0.02) 100%); border: 1px solid #00ffad33; border-radius: 12px; padding: 20px;">
            <div style="color: #00ffad; font-size: 14px; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center;">
                <span style="margin-right: 8px;">📈</span> Expectativas Positivas
            </div>
            <ul style="color: #ccc; line-height: 1.8; margin: 0; padding-left: 20px;">
        """, unsafe_allow_html=True)
        
        positive_points = []
        
        if estimates:
            next_eps = estimates[0].get('estimatedEps', 0)
            curr_eps = estimates[1].get('estimatedEps', next_eps) if len(estimates) > 1 else next_eps
            if next_eps > curr_eps:
                positive_points.append(f"Crecimiento EPS esperado: ${curr_eps:.2f} → ${next_eps:.2f}")
        
        income = fmp_data.get('income_statement', [])
        if income and len(income) >= 2:
            latest_rev = income[0].get('revenue', 0)
            prev_rev = income[1].get('revenue', 0)
            if latest_rev > prev_rev:
                growth = ((latest_rev - prev_rev) / prev_rev) * 100
                positive_points.append(f"Momentum revenue: +{growth:.1f}% vs trimestre anterior")
        
        if data.get('rev_growth') and data['rev_growth'] > 0.1:
            positive_points.append(f"Fuerte crecimiento anual de ingresos ({data['rev_growth']:.1%})")
        
        if not positive_points:
            positive_points = [
                "Tendencia de crecimiento en segmentos clave",
                "Mejoras operativas esperadas",
                "Demanda sostenida en mercados principales"
            ]
        
        for point in positive_points[:4]:
            st.markdown(f"<li>{point}</li>", unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(242,54,69,0.1) 0%, rgba(242,54,69,0.02) 100%); border: 1px solid #f2364533; border-radius: 12px; padding: 20px;">
            <div style="color: #f23645; font-size: 14px; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center;">
                <span style="margin-right: 8px;">⚠️</span> Riesgos a Monitorear
            </div>
            <ul style="color: #ccc; line-height: 1.8; margin: 0; padding-left: 20px;">
        """, unsafe_allow_html=True)
        
        risk_points = []
        
        if data.get('beta') and data['beta'] > 1.5:
            risk_points.append(f"Alta volatilidad (Beta: {data['beta']:.2f})")
        
        if data.get('pe_forward') and data['pe_forward'] > 30:
            risk_points.append(f"Valoración exigente (P/E Forward: {data['pe_forward']:.1f}x)")
        
        surprises = fmp_data.get('earnings_surprises', [])
        if surprises:
            recent_misses = sum(1 for s in surprises[:4] if s.get('actualEarningResult', 0) < s.get('estimatedEarning', 0))
            if recent_misses >= 2:
                risk_points.append(f"Historial reciente de misses ({recent_misses}/4 últimos)")
        
        if not risk_points:
            risk_points = [
                "Incertidumbre macroeconómica global",
                "Presión competitiva en el sector",
                "Volatilidad en costos de materiales"
            ]
        
        for point in risk_points[:4]:
            st.markdown(f"<li>{point}</li>", unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)
    
    if calendar:
        st.markdown("---")
        st.markdown("#### 📅 Próximos Earnings")
        
        cols = st.columns(min(len(calendar), 3))
        for i, (col, event) in enumerate(zip(cols, calendar[:3])):
            with col:
                eps_est = event.get('epsEstimated', 'TBA')
                rev_est = event.get('revenueEstimated', 0)
                date = event.get('date', 'TBA')
                
                st.markdown(f"""
                <div style="background: #0c0e12; border: 1px solid #2a3f5f; border-radius: 8px; padding: 15px; text-align: center;">
                    <div style="color: #00ffad; font-size: 11px; font-weight: bold; margin-bottom: 5px;">{date}</div>
                    <div style="color: white; font-size: 16px; font-weight: bold; margin: 5px 0;">EPS Est: ${eps_est}</div>
                    <div style="color: #888; font-size: 11px;">Rev Est: ${rev_est/1e9:.2f}B</div>
                </div>
                """, unsafe_allow_html=True)

def render_earnings_surprises(fmp_data):
    """Renderiza análisis de earnings surprises."""
    surprises = fmp_data.get('earnings_surprises', [])
    
    if not surprises:
        return
    
    st.markdown("### 🎯 Earnings Track Record")
    
    beats = sum(1 for s in surprises if s.get('actualEarningResult', 0) >= s.get('estimatedEarning', 0))
    total = len(surprises)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        beat_rate = (beats / total * 100) if total > 0 else 0
        color = "#00ffad" if beat_rate >= 75 else "#ffa500" if beat_rate >= 50 else "#f23645"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            <div style="color: #666; font-size: 12px; margin-bottom: 10px;">Beat Rate (Últimos {total})</div>
            <div style="color: {color}; font-size: 3rem; font-weight: bold;">{beat_rate:.0f}%</div>
            <div style="color: {color}; font-size: 14px;">{beats}/{total} Beats</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        table_data = []
        for s in surprises[:6]:
            date = s.get('date', 'N/D')
            actual = s.get('actualEarningResult', 0)
            estimate = s.get('estimatedEarning', 0)
            surprise_pct = s.get('surprisePercentage', 0)
            
            status = "✅ BEAT" if actual >= estimate else "❌ MISS"
            status_color = "#00ffad" if actual >= estimate else "#f23645"
            
            table_data.append({
                'Fecha': date,
                'Actual': f"${actual:.2f}",
                'Estimado': f"${estimate:.2f}",
                'Sorpresa': f"{surprise_pct:+.1f}%",
                'Resultado': status
            })
        
        df_surprises = pd.DataFrame(table_data)
        st.dataframe(df_surprises, use_container_width=True, hide_index=True)

# ────────────────────────────────────────────────
# YFINANCE COMO BACKUP (solo precios)
# ────────────────────────────────────────────────

def get_yfinance_data(ticker_symbol):
    """Obtiene datos de precios de yfinance (fallback)."""
    try:
        rate_limit_delay()
        ticker = yf.Ticker(ticker_symbol)
        
        try:
            info = ticker.info
            log_debug(f"YFinance info keys: {list(info.keys())[:10]}...")
        except Exception as e:
            log_debug(f"YFinance info error: {e}")
            info = {}
        
        # Intentar obtener datos básicos
        hist = ticker.history(period="1y", auto_adjust=True)
        hist_dict = None
        if not hist.empty:
            hist_dict = {
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'open': hist['Open'].tolist(),
                'high': hist['High'].tolist(),
                'low': hist['Low'].tolist(),
                'close': hist['Close'].tolist(),
                'volume': hist['Volume'].tolist()
            }
        
        # Intentar obtener calendar
        calendar_list = []
        try:
            calendar = ticker.calendar
            if calendar is not None and not calendar.empty:
                for idx, row in calendar.iterrows():
                    calendar_list.append({
                        'date': str(idx),
                        'eps_est': row.get('Earnings Estimate', 'N/A'),
                        'revenue_est': row.get('Revenue Estimate', 'N/A')
                    })
        except:
            pass
        
        return {
            'info': info, 
            'history': hist_dict, 
            'earnings': None,
            'calendar': calendar_list,
            'source': 'yfinance'
        }
        
    except Exception as e:
        log_debug(f"Error yfinance: {e}")
        return None

# ────────────────────────────────────────────────
# PROCESAMIENTO DE DATOS UNIFICADO
# ────────────────────────────────────────────────

def process_combined_data(ticker, fmp_data, yf_data):
    """Combina datos de FMP y YFinance, priorizando FMP para fundamentales."""
    
    data = {
        'ticker': ticker,
        'name': ticker,
        'sector': 'N/A',
        'industry': 'N/A',
        'country': 'N/A',
        'employees': 0,
        'website': '#',
        'summary': f"Empresa {ticker}",
        
        'price': 0,
        'prev_close': 0,
        'open': 0,
        'day_high': 0,
        'day_low': 0,
        'fifty_two_high': 0,
        'fifty_two_low': 0,
        'volume': 0,
        'avg_volume': 0,
        'market_cap': 0,
        'change_pct': 0,
        'change_abs': 0,
        'pct_from_high': 0,
        
        'rev_growth': None,
        'ebitda_margin': None,
        'profit_margin': None,
        'operating_margin': None,
        'gross_margin': None,
        
        'pe_trailing': None,
        'pe_forward': None,
        'peg_ratio': None,
        'price_to_sales': None,
        'price_to_book': None,
        
        'eps': None,
        'eps_forward': None,
        'eps_growth': None,
        
        'roe': None,
        'roa': None,
        
        'cash': 0,
        'free_cashflow': 0,
        'operating_cashflow': 0,
        'debt': 0,
        'debt_to_equity': None,
        'current_ratio': None,
        
        'dividend_rate': 0,
        'dividend_yield': 0,
        'payout_ratio': 0,
        
        'target_high': 0,
        'target_low': 0,
        'target_mean': 0,
        'target_median': 0,
        'recommendation': 'none',
        'num_analysts': 0,
        
        'beta': 0,
        'hist': pd.DataFrame(),
        'earnings_hist': pd.DataFrame(),
        'earnings_calendar': [],
        
        'is_real_data': False,
        'data_source': 'none'
    }
    
    # 1. PRIORIDAD: Datos de FMP (más completos y confiables)
    if fmp_data:
        log_debug("Procesando datos de FMP...")
        fmp_fund = extract_fundamentals_from_fmp(fmp_data)
        
        if fmp_fund:
            # Sobrescribir con datos de FMP
            for key, value in fmp_fund.items():
                if key in data and value is not None and value != 0:
                    data[key] = value
                    log_debug(f"FMP {key}: {value}")
            
            data['is_real_data'] = True
            data['data_source'] = 'fmp'
            log_debug(f"FMP datos aplicados. Precio: {data['price']}, ROE: {data['roe']}")
    
    # 2. BACKUP: Datos de YFinance (principalmente para histórico de precios)
    if yf_data:
        log_debug("Procesando datos de YFinance...")
        
        # Solo usar precios de YFinance si FMP no los tiene
        if data['price'] == 0:
            info = yf_data.get('info', {})
            data['price'] = info.get('currentPrice', info.get('regularMarketPrice', 0))
            data['prev_close'] = info.get('previousClose', 0)
            data['market_cap'] = info.get('marketCap', 0)
            data['data_source'] = 'yfinance'
            log_debug(f"YFinance precio usado: {data['price']}")
        
        # Siempre usar el histórico de YFinance (FMP no tiene precios históricos)
        if yf_data.get('history'):
            try:
                hist_data = yf_data['history']
                data['hist'] = pd.DataFrame({
                    'Open': hist_data['open'],
                    'High': hist_data['high'],
                    'Low': hist_data['low'],
                    'Close': hist_data['close'],
                    'Volume': hist_data['volume']
                }, index=pd.to_datetime(hist_data['dates']))
                log_debug(f"Histórico YFinance cargado: {len(data['hist'])} registros")
            except Exception as e:
                log_debug(f"Error cargando histórico YFinance: {e}")
        
        data['earnings_calendar'] = yf_data.get('calendar', [])
    
    # 3. Calcular campos derivados
    if data['price'] and data['prev_close'] and data['prev_close'] != 0:
        data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
        data['change_abs'] = data['price'] - data['prev_close']
    
    if data['price'] and data['fifty_two_high'] and data['fifty_two_high'] != 0:
        data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
    
    # 4. Validación final
    if data['price'] == 0:
        log_debug("ERROR: No se pudo obtener precio de ninguna fuente")
        return None
    
    log_debug(f"Datos finales - Precio: {data['price']}, MarketCap: {data['market_cap']}, ROE: {data['roe']}, Margen: {data['profit_margin']}")
    
    return data

# ────────────────────────────────────────────────
# MOCK DATA (último recurso)
# ────────────────────────────────────────────────

def get_mock_data(ticker):
    """Datos de demostración cuando todo falla."""
    log_debug(f"Usando MOCK DATA para {ticker}")
    
    mock_db = {
        "AAPL": {"name": "Apple Inc.", "sector": "Technology", "price": 275.69, "market_cap": 4.05e12, "rev_growth": 0.157, "pe_forward": 29.7, "eps": 7.91, "dividend_yield": 0.0038, "roe": 1.52, "beta": 1.107, "ebitda_margin": 0.351, "profit_margin": 0.270},
        "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "price": 420.30, "market_cap": 3.1e12, "rev_growth": 0.15, "pe_forward": 32.0, "eps": 11.80, "dividend_yield": 0.007, "roe": 0.38, "beta": 0.9, "ebitda_margin": 0.45, "profit_margin": 0.35},
        "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "price": 875.50, "market_cap": 2.15e12, "rev_growth": 2.10, "pe_forward": 35.0, "eps": 12.90, "dividend_yield": 0.0003, "roe": 0.55, "beta": 1.75, "ebitda_margin": 0.58, "profit_margin": 0.48},
        "TER": {"name": "Teradyne, Inc.", "sector": "Technology", "industry": "Semiconductor Equipment", "price": 314.66, "market_cap": 50.05e9, "rev_growth": 0.438, "pe_forward": 24.5, "eps": 7.91, "dividend_yield": 0.003, "roe": 0.25, "beta": 1.45, "ebitda_margin": 0.32, "profit_margin": 0.24, "cash": 2.1e9, "debt": 0.8e9, "free_cashflow": 1.2e9},
    }
    
    if ticker not in mock_db:
        seed = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 1000
        base_price = 50 + (seed % 950)
        mock_db[ticker] = {
            "name": f"{ticker} Corp.", "sector": "Technology", "price": float(base_price),
            "market_cap": float(base_price * 1e9 * random.uniform(0.5, 5)),
            "rev_growth": random.uniform(-0.1, 0.5), "pe_forward": random.uniform(15, 50),
            "eps": float(base_price) / random.uniform(15, 40), "dividend_yield": random.choice([0.0, 0.0, 0.0, 0.02, 0.04]),
            "roe": random.uniform(0.05, 0.40), "beta": random.uniform(0.8, 2.0),
            "ebitda_margin": random.uniform(0.15, 0.40), "profit_margin": random.uniform(0.10, 0.30)
        }
    
    mock = mock_db[ticker]
    price = float(mock["price"])
    
    return {
        "ticker": ticker, "name": mock["name"], "sector": mock["sector"], "industry": mock.get("industry", "Technology"),
        "country": "United States", "employees": mock.get("employees", 100000), "website": "#",
        "summary": f"{mock['name']} es líder en su sector con fuerte posición de mercado.",
        "price": price, "prev_close": price * 0.98, "open": price, "day_high": price * 1.02,
        "day_low": price * 0.98, "fifty_two_high": price * 1.3, "fifty_two_low": price * 0.7,
        "volume": 50000000, "avg_volume": 45000000, "market_cap": mock["market_cap"],
        "enterprise_value": mock["market_cap"] * 1.1, "rev_growth": mock["rev_growth"],
        "ebitda_margin": mock["ebitda_margin"], "profit_margin": mock["profit_margin"],
        "operating_margin": mock["profit_margin"] * 1.2, "gross_margin": 0.45,
        "pe_trailing": mock["pe_forward"] * 1.1, "pe_forward": mock["pe_forward"],
        "peg_ratio": 1.5, "price_to_sales": 8.0, "price_to_book": 25.0,
        "eps": mock["eps"], "eps_forward": mock["eps"] * 1.15, "eps_growth": mock["rev_growth"],
        "roe": mock["roe"], "roa": mock["roe"] * 0.6, "cash": mock.get("cash", mock["market_cap"] * 0.05),
        "free_cashflow": mock.get("free_cashflow", mock["market_cap"] * 0.03), "operating_cashflow": mock["market_cap"] * 0.04,
        "debt": mock.get("debt", mock["market_cap"] * 0.15), "debt_to_equity": 50.0, "current_ratio": 1.2,
        "dividend_rate": price * mock["dividend_yield"], "dividend_yield": mock["dividend_yield"],
        "ex_div_date": None, "payout_ratio": 0.20, "target_high": price * 1.3,
        "target_low": price * 0.8, "target_mean": price * 1.1, "target_median": price * 1.1,
        "recommendation": "buy", "num_analysts": 35, "hist": pd.DataFrame(),
        "earnings_hist": pd.DataFrame(), "earnings_calendar": [],
        "beta": mock["beta"], "is_real_data": False, "data_source": "mock",
        "change_pct": 2.04, "change_abs": price * 0.02, "pct_from_high": -5.0
    }

# ────────────────────────────────────────────────
# FUNCIONES DE FORMATO
# ────────────────────────────────────────────────

def format_value(value, prefix="", suffix="", decimals=2):
    if value is None or value == 0 or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    try:
        val = float(value)
        if abs(val) >= 1e12:
            return f"{prefix}{val/1e12:.{decimals}f}T{suffix}"
        elif abs(val) >= 1e9:
            return f"{prefix}{val/1e9:.{decimals}f}B{suffix}"
        elif abs(val) >= 1e6:
            return f"{prefix}{val/1e6:.{decimals}f}M{suffix}"
        elif abs(val) >= 1e3:
            return f"{prefix}{val/1e3:.{decimals}f}K{suffix}"
        return f"{prefix}{val:.{decimals}f}{suffix}"
    except:
        return str(value)

def format_pct(value, decimals=2):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A", "#888"
    try:
        val = float(value) * 100 if abs(float(value)) < 1 else float(value)
        color = "#00ffad" if val >= 0 else "#f23645"
        return f"{val:.{decimals}f}%", color
    except:
        return "N/A", "#888"

def generate_outlook_points(data):
    """Genera puntos de outlook basados en métricas reales."""
    positive = []
    challenges = []
    
    if data.get('rev_growth'):
        if data['rev_growth'] > 0.20:
            positive.append(f"🚀 Crecimiento explosivo de ingresos ({data['rev_growth']:.1%})")
        elif data['rev_growth'] > 0.10:
            positive.append(f"📈 Sólido crecimiento de ingresos ({data['rev_growth']:.1%})")
        elif data['rev_growth'] > 0:
            positive.append(f"↗️ Crecimiento moderado de ingresos ({data['rev_growth']:.1%})")
        else:
            challenges.append(f"📉 Contracción de ingresos ({data['rev_growth']:.1%})")
    
    if data.get('profit_margin'):
        if data['profit_margin'] > 0.25:
            positive.append(f"💰 Márgenes de beneficio excepcionales ({data['profit_margin']:.1%})")
        elif data['profit_margin'] > 0.15:
            positive.append(f"✅ Márgenes de beneficio saludables ({data['profit_margin']:.1%})")
        elif data['profit_margin'] < 0.05:
            challenges.append(f"⚠️ Márgenes de beneficio comprimidos ({data['profit_margin']:.1%})")
    
    if data.get('ebitda_margin'):
        if data['ebitda_margin'] > 0.30:
            positive.append(f"🏭 Alta generación operativa (EBITDA {data['ebitda_margin']:.1%})")
    
    if data.get('roe'):
        if data['roe'] > 0.30:
            positive.append(f"🎯 ROE excepcional ({data['roe']:.1%}) - Eficiencia superior")
        elif data['roe'] > 0.15:
            positive.append(f"📊 ROE sólido ({data['roe']:.1%})")
        elif data['roe'] < 0.08:
            challenges.append(f"📉 ROE bajo ({data['roe']:.1%}) - Menor rentabilidad")
    
    if data.get('debt_to_equity'):
        if data['debt_to_equity'] < 50:
            positive.append(f"⚖️ Balance poco apalancado (Deuda/Pat {data['debt_to_equity']:.0f}%)")
        elif data['debt_to_equity'] > 100:
            challenges.append(f"⚠️ Alto apalancamiento financiero ({data['debt_to_equity']:.0f}%)")
    
    if data.get('free_cashflow') and data['free_cashflow'] > 0:
        positive.append(f"💵 Generación robusta de Free Cash Flow ({format_value(data['free_cashflow'], '$')})")
    elif data.get('free_cashflow') and data['free_cashflow'] < 0:
        challenges.append(f"🔥 Free Cash Flow negativo - quema de caja")
    
    if data.get('pe_forward'):
        if data['pe_forward'] < 15:
            positive.append(f"💎 Valoración atractiva (P/E {data['pe_forward']:.1f}x)")
        elif data['pe_forward'] > 40:
            challenges.append(f"💸 Valoración elevada (P/E {data['pe_forward']:.1f}x) - altas expectativas")
    
    if data.get('dividend_yield') and data['dividend_yield'] > 0.02:
        positive.append(f"🎁 Dividendo atractivo ({data['dividend_yield']:.2%} yield)")
    
    if data.get('target_mean') and data.get('price'):
        upside = ((data['target_mean'] - data['price']) / data['price']) * 100
        if upside > 20:
            positive.append(f"🎯 Potencial alcista del {upside:.1f}% vs consenso")
        elif upside < -10:
            challenges.append(f"📉 Precio por encima del consenso ({upside:.1f}%)")
    
    defaults_pos = [
        "🌟 Posición de liderazgo en el sector",
        "🔧 Fortalezas operativas diferenciadas",
        "📱 Exposición a tendencias de crecimiento"
    ]
    defaults_chal = [
        "🌪️ Exposición a ciclos económicos",
        "⚔️ Presión competitiva del sector",
        "🌍 Incertidumbre macroeconómica global"
    ]
    
    while len(positive) < 3:
        positive.append(defaults_pos[len(positive) % len(defaults_pos)])
    while len(challenges) < 3:
        challenges.append(defaults_chal[len(challenges) % len(defaults_chal)])
    
    return positive[:4], challenges[:4]

# ────────────────────────────────────────────────
# ANÁLISIS RSU CON IA
# ────────────────────────────────────────────────

def render_rsu_earnings_analysis(data, fmp_data=None):
    """Renderiza el análisis con datos de FMP si están disponibles."""
    
    base_prompt = load_rsu_prompt()
    
    if not base_prompt:
        st.warning("⚠️ Prompt RSU no encontrado.")
        return
    
    fmp_formatted = format_fmp_earnings_data(fmp_data) if fmp_data else "No disponible"
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    datos_ticker = f"""=== DATOS DEL TICKER ===
TICKER: {data['ticker']}
COMPANY: {data['name']}
SECTOR: {data.get('sector', 'N/A')}
INDUSTRY: {data.get('industry', 'N/A')}

=== DATOS DE MERCADO ===
PRICE: ${data['price']:.2f} | CHANGE: {data.get('change_pct', 0):+.2f}% | MARKET_CAP: {format_value(data['market_cap'], '$')}
VOLUME: {format_value(data['volume'], '', '', 0)} | AVG_VOLUME: {format_value(data['avg_volume'], '', '', 0)}
BETA: {data.get('beta', 'N/A')} | 52W_RANGE: ${data.get('fifty_two_low', 0):.2f}-${data.get('fifty_two_high', 0):.2f} | PCT_FROM_HIGH: {data.get('pct_from_high', 0):.1f}%

=== VALORACIÓN ===
P/E_TRAILING: {format_value(data.get('pe_trailing'), '', 'x', 2)} | P/E_FORWARD: {format_value(data.get('pe_forward'), '', 'x', 2)}
PEG_RATIO: {format_value(data.get('peg_ratio'), '', '', 2)} | P/S: {format_value(data.get('price_to_sales'), '', 'x', 2)} | P/B: {format_value(data.get('price_to_book'), '', 'x', 2)}
EPS: ${data.get('eps', 'N/A')} | EPS_FORWARD: ${data.get('eps_forward', 'N/A')} | EPS_GROWTH: {format_value(data.get('eps_growth'), '', '%', 2)}

=== MÁRGENES ===
GROSS_MARGIN: {format_value(data.get('gross_margin'), '', '%', 2)} | OPERATING_MARGIN: {format_value(data.get('operating_margin'), '', '%', 2)}
EBITDA_MARGIN: {format_value(data.get('ebitda_margin'), '', '%', 2)} | PROFIT_MARGIN: {format_value(data.get('profit_margin'), '', '%', 2)}

=== RENTABILIDAD ===
ROE: {format_value(data.get('roe'), '', '%', 2)} | ROA: {format_value(data.get('roa'), '', '%', 2)}

=== BALANCE ===
CASH: {format_value(data.get('cash'), '$')} | DEBT: {format_value(data.get('debt'), '$')}
FREE_CASH_FLOW: {format_value(data.get('free_cashflow'), '$')} | OPERATING_CASH_FLOW: {format_value(data.get('operating_cashflow'), '$')}
DEBT_TO_EQUITY: {format_value(data.get('debt_to_equity'), '', '%', 2)} | CURRENT_RATIO: {data.get('current_ratio', 'N/A')}

=== DIVIDENDOS ===
DIVIDEND_RATE: ${data.get('dividend_rate', 0):.2f} | DIVIDEND_YIELD: {format_value(data.get('dividend_yield'), '', '%', 2)} | PAYOUT_RATIO: {format_value(data.get('payout_ratio'), '', '%', 2)}

=== CONSENSO ANALISTAS ===
RECOMMENDATION: {data.get('recommendation', 'N/A').upper()} | NUM_ANALYSTS: {data.get('num_analysts', 'N/A')}
TARGET_MEAN: ${data.get('target_mean', 0):.2f} | TARGET_HIGH: ${data.get('target_high', 0):.2f} | TARGET_LOW: ${data.get('target_low', 0):.2f}

{f"=== DATOS FMP (EARNINGS DETALLADOS - ACTUALIZADOS) ===" if fmp_data else ""}
{fmp_formatted}

=== FECHA DE ANÁLISIS ===
{current_date}
"""
    
    prompt_completo = base_prompt.replace("{datos_ticker}", datos_ticker).replace("{current_date}", current_date)
    
    if "{datos_ticker}" not in base_prompt:
        prompt_completo = f"{base_prompt}\n\n{datos_ticker}\n\n=== INSTRUCCION ===\nGenera el reporte COMPLETO en español. Usa los datos proporcionados. La fecha actual es {current_date}."
    
    model, name, err = get_ia_model()
    
    if not model:
        st.info("🤖 IA no configurada.")
        return
    
    try:
        with st.spinner("🧠 Generando análisis... (puede tomar 30-60s)"):
            
            response = model.generate_content(
                prompt_completo,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                },
                safety_settings={
                    'HATE': 'BLOCK_NONE',
                    'HARASSMENT': 'BLOCK_NONE',
                    'SEXUAL': 'BLOCK_NONE',
                    'DANGEROUS': 'BLOCK_NONE'
                }
            )
            
            response_text = response.text
            
            if not response_text.strip().endswith('---') and len(response_text) > 100:
                if '## 8. VEREDICTO RSU' not in response_text or len(response_text) < 2000:
                    st.warning("⚠️ Respuesta incompleta, regenerando...")
                    
                    short_prompt = f"""Análisis fundamental rápido de {data['ticker']} al {current_date}:

Precio: ${data['price']:.2f} | Market Cap: {format_value(data['market_cap'], '$')}
P/E: {format_value(data.get('pe_forward'), '', 'x', 2)} | ROE: {format_value(data.get('roe'), '', '%', 2)} | Margen: {format_value(data.get('profit_margin'), '', '%', 2)}

Genera análisis completo."""
                    
                    response = model.generate_content(
                        short_prompt,
                        generation_config={"temperature": 0.2, "max_output_tokens": 4096}
                    )
                    response_text = response.text
            
            st.markdown("""
            <style>
            .terminal-box {
                background-color: #0c0e12;
                border: 1px solid #00ffad;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                margin: 20px 0;
            }
            .terminal-header {
                background: linear-gradient(90deg, #00ffad22 0%, #00ffad11 100%);
                border-bottom: 1px solid #00ffad;
                padding: 12px 16px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .terminal-title {
                color: #00ffad;
                font-size: 13px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            .terminal-ticker {
                color: #00ffad;
                font-size: 11px;
                margin-left: auto;
                opacity: 0.8;
            }
            .terminal-body {
                padding: 20px;
                color: #e0e0e0;
                line-height: 1.6;
                font-size: 13px;
            }
            .terminal-body h1, .terminal-body h2, .terminal-body h3 {
                color: #00ffad;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            .terminal-footer {
                border-top: 1px solid #2a3f5f;
                padding: 8px 16px;
                font-size: 10px;
                color: #666;
                display: flex;
                justify-content: space-between;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="terminal-box">
                <div class="terminal-header">
                    <span style="color: #00ffad;">⬤</span>
                    <span class="terminal-title">RSU Hedge Fund Analysis Terminal</span>
                    <span class="terminal-ticker">{data['ticker']} | {current_date}</span>
                </div>
                <div class="terminal-body">
            """, unsafe_allow_html=True)
            
            st.markdown(response_text, unsafe_allow_html=True)
            
            word_count = len(response_text.split())
            char_count = len(response_text)
            
            st.markdown(f"""
                </div>
                <div class="terminal-footer">
                    <span>{name} | {word_count} palabras | {char_count} caracteres</span>
                    <span style="color: #00ffad;">RSU_TERMINAL_v2.0</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔧 Debug: Prompt y Respuesta"):
                st.text_area("Prompt", prompt_completo, height=300)
                st.text_area("Respuesta", response_text, height=200)
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        generate_fallback_analysis(data)

def generate_fallback_analysis(data):
    """Análisis básico si la IA falla."""
    score = 5.0
    factors = []
    
    if data.get('pe_forward') and data['pe_forward'] < 20:
        score += 1
        factors.append("P/E atractivo")
    elif data.get('pe_forward') and data['pe_forward'] > 40:
        score -= 1
        factors.append("P/E elevado")
    
    if data.get('roe') and data['roe'] > 0.15:
        score += 1
        factors.append("ROE sólido")
    
    score = max(1, min(10, score))
    recommendation = "COMPRA FUERTE" if score >= 8 else "COMPRA" if score >= 6.5 else "MANTENER" if score >= 5 else "VENDER"
    
    st.markdown(f"""
    ### 📊 ANÁLISIS FALLBACK
    
    **{data['ticker']} - {data['name']}**
    
    | Métrica | Valor |
    |---------|-------|
    | Precio | ${data['price']:.2f} |
    | P/E Forward | {format_value(data.get('pe_forward'), '', 'x', 2)} |
    | ROE | {format_value(data.get('roe'), '', '%', 2)} |
    
    **Score: {score:.1f}/10** | **{recommendation}**
    """)

# ────────────────────────────────────────────────
# MAIN - FLUJO PRINCIPAL CORREGIDO
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .stApp { background-color: #0c0e12; }
        .stTextInput > div > div > input { background-color: #1a1e26; color: white; border: 1px solid #2a3f5f; border-radius: 8px; }
        .stButton > button { background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%); color: #0c0e12; border: none; border-radius: 8px; font-weight: bold; }
        ::-webkit-scrollbar { width: 8px; background: #0c0e12; }
        ::-webkit-scrollbar-thumb { background: #00ffad; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📅 Análisis de Earnings")
    st.markdown('<div style="color: #888; margin-bottom: 20px;">Análisis fundamental con IA y datos en tiempo real</div>', unsafe_allow_html=True)
    
    # Verificar configuración
    fmp_key = st.secrets.get("FMP_API_KEY", None)
    if not fmp_key:
        st.warning("⚠️ **FMP_API_KEY no configurado**. Ve a Settings > Secrets y agrega tu API key de Financial Modeling Prep para obtener datos completos.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("Ticker", value="AAPL").upper().strip()
    with col2:
        st.write("")
        st.write("")
        analyze = st.button("🔍 Analizar", use_container_width=True)
    
    if analyze and ticker:
        with st.spinner("Cargando datos de múltiples fuentes..."):
            
            # 1. Obtener datos de FMP (prioridad alta)
            fmp_data = None
            if fmp_key:
                fmp_data = get_fmp_data(ticker, fmp_key)
                if fmp_data:
                    st.success(f"✅ FMP API conectado")
            
            # 2. Obtener datos de YFinance (para precios históricos)
            yf_data = get_yfinance_data(ticker)
            
            # 3. Combinar datos
            data = process_combined_data(ticker, fmp_data, yf_data)
            
            # 4. Si todo falla, usar mock
            if not data:
                st.error("❌ No se pudieron obtener datos de ninguna fuente. Usando datos de demostración.")
                data = get_mock_data(ticker)
        
        if not data:
            st.error("Error crítico al cargar datos")
            return
        
        # Mostrar fuente de datos
        source_emoji = {"fmp": "🟢", "yfinance": "🟡", "mock": "🔴"}
        source_name = {"fmp": "FMP API", "yfinance": "Yahoo Finance", "mock": "Demo"}
        
        st.info(f"{source_emoji.get(data['data_source'], '⚪')} **Fuente de datos:** {source_name.get(data['data_source'], 'Desconocida')}")
        
        # Header
        change_color = "#00ffad" if data.get('change_pct', 0) >= 0 else "#f23645"
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            <div style="margin-bottom: 5px;">
                <span style="color: #666; font-size: 12px;">{data.get('sector', 'N/A')} • {data.get('industry', 'N/A')}</span>
            </div>
            <h1 style="color: white; margin: 0; font-size: 2.2rem;">{data.get('name')} <span style="color: #00ffad; font-size: 1.2rem;">({ticker})</span></h1>
            <div style="color: #666; font-size: 12px; margin-top: 5px;">{data.get('country', '')} • {format_value(data.get('employees'), '', ' empleados', 0)}</div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: right;">
                <div style="color: white; font-size: 2.8rem; font-weight: 700;">${data.get('price', 0):,.2f}</div>
                <div style="color: {change_color}; font-size: 1.1rem; font-weight: 600;">{'▲' if data.get('change_pct', 0) >= 0 else '▼'} {data.get('change_pct', 0):+.2f}%</div>
                <div style="color: #666; font-size: 11px; margin-top: 5px;">Cap: {format_value(data.get('market_cap'), '$')} | Vol: {format_value(data.get('volume'), '', '', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # SECCIÓN EARNINGS REPORT
        st.markdown("---")
        render_earnings_report_section(data, fmp_data)
        
        # MÉTRICAS FUNDAMENTALES
        st.markdown("---")
        st.markdown("### 📊 Métricas Fundamentales")
        
        # Verificar si tenemos datos reales
        has_real_data = data.get('roe') is not None or data.get('pe_forward') is not None
        
        if not has_real_data:
            st.warning("⚠️ **Datos fundamentales limitados.** Configura FMP_API_KEY para obtener métricas completas (ROE, P/E, márgenes, etc.)")
        
        cols = st.columns(4)
        metrics = [
            ("Crec. Ingresos", data.get('rev_growth'), True),
            ("Margen EBITDA", data.get('ebitda_margin'), True),
            ("ROE", data.get('roe'), True),
            ("P/E Forward", data.get('pe_forward'), False),
        ]
        
        for col, (label, value, is_pct) in zip(cols, metrics):
            with col:
                if is_pct and value is not None:
                    formatted, color = format_pct(value)
                else:
                    formatted = format_value(value, '', 'x' if 'P/E' in label else '', 1)
                    color = "#00ffad" if value and value != 0 else "#666"
                
                # Si es N/A, mostrar warning visual
                is_na = formatted == "N/A"
                
                st.markdown(f"""
                <div style="background: {'#1a1e26' if is_na else '#0c0e12'}; border: 1px solid {'#f2364533' if is_na else '#1a1e26'}; border-radius: 10px; padding: 18px; text-align: center; {'opacity: 0.7;' if is_na else ''}">
                    <div style="color: #666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">{label}</div>
                    <div style="color: {color}; font-size: 1.4rem; font-weight: bold;">{formatted}</div>
                    {f'<div style="color: #f23645; font-size: 9px; margin-top: 5px;">Sin datos</div>' if is_na else ''}
                </div>
                """, unsafe_allow_html=True)
        
        # GRÁFICO Y MÉTRICAS CLAVE
        st.markdown("---")
        col_chart, col_info = st.columns([3, 2])
        
        with col_chart:
            if not data.get('hist', pd.DataFrame()).empty:
                hist = data['hist']
                fig = go.Figure(data=[go.Candlestick(
                    x=hist.index, open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'],
                    increasing_line_color='#00ffad', decreasing_line_color='#f23645'
                )])
                fig.update_layout(
                    template="plotly_dark", plot_bgcolor='#0c0e12', paper_bgcolor='#11141a',
                    font=dict(color='white'), xaxis_rangeslider_visible=False,
                    height=350, margin=dict(l=30, r=30, t=30, b=30),
                    title="Precio (1 año)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Gráfico de precio no disponible")
        
        with col_info:
            st.markdown("#### 📋 Sobre la Empresa")
            summary = data.get('summary', 'N/A')
            st.markdown(f"<div style='color: #aaa; font-size: 13px; line-height: 1.6;'>{summary[:300]}{'...' if len(summary) > 300 else ''}</div>", unsafe_allow_html=True)
            
            st.markdown("#### 💰 Métricas Clave")
            
            # Mostrar valores con indicadores de disponibilidad
            cash_val = format_value(data.get('cash'), '$')
            debt_val = format_value(data.get('debt'), '$')
            fcf_val = format_value(data.get('free_cashflow'), '$')
            
            st.markdown(f"""
            <div style="background: #0c0e12; border-radius: 8px; padding: 15px; border: 1px solid #1a1e26; font-size: 12px; line-height: 2;">
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">Cash:</span> <span style="color: {'#00ffad' if cash_val != 'N/A' else '#666'}; font-weight: bold;">{cash_val}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">Deuda:</span> <span style="color: {'#f23645' if debt_val != 'N/A' else '#666'}; font-weight: bold;">{debt_val}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">FCF:</span> <span style="color: {'#00ffad' if data.get('free_cashflow', 0) > 0 else '#f23645' if data.get('free_cashflow', 0) < 0 else '#666'}; font-weight: bold;">{fcf_val}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">Beta:</span> <span style="color: white; font-weight: bold;">{data.get('beta', 0):.2f}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">52S vs Max:</span> <span style="color: {'#00ffad' if data.get('pct_from_high', 0) > -10 else '#f23645'}; font-weight: bold;">{data.get('pct_from_high', 0):.1f}%</span></div>
            </div>
            """, unsafe_allow_html=True)
        
        # PERSPECTIVAS
        st.markdown("---")
        st.markdown("### 🔮 Perspectivas y Desafíos")
        
        positive, challenges = generate_outlook_points(data)
        
        col_pos, col_chal = st.columns(2)
        with col_pos:
            points_html = "".join([f"<li style='margin-bottom: 12px; padding-left: 10px; border-left: 3px solid #00ffad;'>{p}</li>" for p in positive])
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(0,255,173,0.08) 0%, rgba(0,255,173,0.02) 100%); border: 1px solid #00ffad33; border-radius: 12px; padding: 25px; height: 100%;">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div style="width: 36px; height: 36px; background: #00ffad22; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 18px;">📈</div>
                    <h3 style="color: #00ffad; margin: 0; font-size: 1.1rem;">Perspectivas Positivas</h3>
                </div>
                <ul style="color: #ccc; line-height: 1.6; padding-left: 0; list-style: none; margin: 0;">
                    {points_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col_chal:
            points_html = "".join([f"<li style='margin-bottom: 12px; padding-left: 10px; border-left: 3px solid #f23645;'>{c}</li>" for c in challenges])
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(242,54,69,0.08) 0%, rgba(242,54,69,0.02) 100%); border: 1px solid #f2364533; border-radius: 12px; padding: 25px; height: 100%;">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div style="width: 36px; height: 36px; background: #f2364522; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 18px;">⚠️</div>
                    <h3 style="color: #f23645; margin: 0; font-size: 1.1rem;">Desafíos Pendientes</h3>
                </div>
                <ul style="color: #ccc; line-height: 1.6; padding-left: 0; list-style: none; margin: 0;">
                    {points_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # ANÁLISIS RSU
        st.markdown("---")
        render_rsu_earnings_analysis(data, fmp_data)
        
        # FOOTER
        st.markdown(f"""
        <div style="text-align: center; color: #444; font-size: 11px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #1a1e26;">
            Datos: Financial Modeling Prep + Yahoo Finance | Análisis: IA Gemini<br>
            <span style="color: #00ffad;">RSU Dashboard Pro</span> • Para fines informativos únicamente
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
