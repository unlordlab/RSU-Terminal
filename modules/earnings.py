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
# CONFIGURACIÓN
# ────────────────────────────────────────────────

def rate_limit_delay():
    time.sleep(random.uniform(0.3, 0.8))

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
                        return content
                    else:
                        print(f"Archivo vacío: {prompt_path}")
        
        st.warning("⚠️ No se encontró earnings.txt, usando prompt embebido")
        return get_embedded_prompt()
        
    except Exception as e:
        print(f"Error cargando prompt RSU: {e}")
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
# FINANCIAL MODELING PREP API - MEJORADO
# ────────────────────────────────────────────────

def get_fmp_data(ticker, api_key):
    """Obtiene datos completos de Financial Modeling Prep API."""
    if not api_key:
        return None
    
    try:
        base_url = "https://financialmodelingprep.com/api/v3"
        
        # Income Statement (últimos 4 trimestres)
        income_url = f"{base_url}/income-statement/{ticker}?period=quarter&limit=8&apikey={api_key}"
        income_resp = requests.get(income_url, timeout=15)
        income = income_resp.json() if income_resp.status_code == 200 else []
        
        # Earnings Surprises (Actual vs Estimate histórico)
        surprises_url = f"{base_url}/earnings-surprises/{ticker}?apikey={api_key}"
        surprises_resp = requests.get(surprises_url, timeout=15)
        surprises = surprises_resp.json() if surprises_resp.status_code == 200 else []
        
        # Earnings Calendar (próximos)
        calendar_url = f"{base_url}/earning_calendar/{ticker}?apikey={api_key}"
        calendar_resp = requests.get(calendar_url, timeout=15)
        calendar = calendar_resp.json() if calendar_resp.status_code == 200 else []
        
        # Analyst Estimates
        estimates_url = f"{base_url}/analyst-estimates/{ticker}?period=quarter&limit=8&apikey={api_key}"
        estimates_resp = requests.get(estimates_url, timeout=15)
        estimates = estimates_resp.json() if estimates_resp.status_code == 200 else []
        
        # Company Outlook (guidance, segmentos, etc)
        outlook_url = f"{base_url}/company-outlook/{ticker}?apikey={api_key}"
        outlook_resp = requests.get(outlook_url, timeout=15)
        outlook = outlook_resp.json() if outlook_resp.status_code == 200 else {}
        
        # Key Metrics (para datos recientes)
        metrics_url = f"{base_url}/key-metrics/{ticker}?period=quarter&limit=4&apikey={api_key}"
        metrics_resp = requests.get(metrics_url, timeout=15)
        metrics = metrics_resp.json() if metrics_resp.status_code == 200 else []
        
        # Earnings Call Transcript (último disponible)
        transcript_url = f"{base_url}/earning_call_transcript/{ticker}?apikey={api_key}"
        transcript_resp = requests.get(transcript_url, timeout=15)
        transcript = transcript_resp.json() if transcript_resp.status_code == 200 else []
        
        return {
            'income_statement': income,
            'earnings_surprises': surprises,
            'earnings_calendar': calendar,
            'analyst_estimates': estimates,
            'company_outlook': outlook,
            'key_metrics': metrics,
            'transcript': transcript,
            'source': 'fmp',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"Error FMP: {e}")
        return None

def get_fmp_earnings_historical(ticker, api_key, limit=8):
    """Obtiene historial detallado de earnings trimestrales."""
    if not api_key:
        return []
    
    try:
        base_url = "https://financialmodelingprep.com/api/v3"
        
        # Historical Earnings
        hist_url = f"{base_url}/historical/earning_calendar/{ticker}?limit={limit}&apikey={api_key}"
        hist_resp = requests.get(hist_url, timeout=15)
        historical = hist_resp.json() if hist_resp.status_code == 200 else []
        
        return historical
        
    except Exception as e:
        print(f"Error FMP Historical: {e}")
        return []

# ────────────────────────────────────────────────
# FORMATO DE DATOS FMP MEJORADO
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
            
            # Calcular márgenes si hay datos
            if revenue > 0:
                gross_margin = (gross_profit / revenue) * 100
                operating_margin = (operating_income / revenue) * 100
                net_margin = (net_income / revenue) * 100
                result.append(f"  Márgenes: Gross {gross_margin:.1f}% | Operating {operating_margin:.1f}% | Net {net_margin:.1f}%")
    
    # Earnings Surprises - Actual vs Estimate
    surprises = fmp_data.get('earnings_surprises', [])
    if surprises:
        result.append("\n\n=== EARNINGS SURPRISES (Actual vs Estimate) ===")
        for s in surprises[:6]:
            date = s.get('date', 'N/D')
            actual = s.get('actualEarningResult', 'N/D')
            estimate = s.get('estimatedEarning', 'N/D')
            surprise = s.get('surprise', 'N/D')
            surprise_pct = s.get('surprisePercentage', 'N/D')
            
            # Determinar si es beat o miss
            try:
                actual_f = float(actual) if actual != 'N/D' else 0
                estimate_f = float(estimate) if estimate != 'N/D' else 0
                beat_miss = "BEAT ✅" if actual_f > estimate_f else "MISS ❌" if actual_f < estimate_f else "IN LINE ➖"
            except:
                beat_miss = "N/D"
            
            result.append(f"{date}: Actual ${actual} vs Est ${estimate} | Surprise: {surprise_pct}% {beat_miss}")
    
    # Analyst Estimates - Próximos trimestres
    estimates = fmp_data.get('analyst_estimates', [])
    if estimates:
        result.append("\n\n=== ANALYST ESTIMATES (Próximos períodos) ===")
        for e in estimates[:4]:
            date = e.get('date', 'N/D')
            period = e.get('period', 'N/D')
            eps_est = e.get('estimatedEps', 'N/D')
            revenue_est = e.get('estimatedRevenue', 'N/D')
            result.append(f"{date} ({period}): EPS Est ${eps_est} | Revenue Est ${revenue_est:,.0f}" if isinstance(revenue_est, (int, float)) else f"{date} ({period}): EPS Est ${eps_est} | Revenue Est {revenue_est}")
    
    # Próximos earnings
    calendar = fmp_data.get('earnings_calendar', [])
    if calendar:
        result.append("\n\n=== PRÓXIMOS EARNINGS PROGRAMADOS ===")
        for c in calendar[:2]:
            date = c.get('date', 'TBA')
            eps_est = c.get('epsEstimated', 'N/D')
            revenue_est = c.get('revenueEstimated', 'N/D')
            result.append(f"Fecha: {date} | EPS Est: ${eps_est} | Revenue Est: ${revenue_est:,.0f}" if isinstance(revenue_est, (int, float)) else f"Fecha: {date} | EPS Est: ${eps_est}")
    
    # Key Metrics recientes
    metrics = fmp_data.get('key_metrics', [])
    if metrics:
        result.append("\n\n=== KEY METRICS (Último trimestre) ===")
        m = metrics[0]
        result.append(f"Revenue per Share: ${m.get('revenuePerShare', 'N/D')}")
        result.append(f"Net Income per Share: ${m.get('netIncomePerShare', 'N/D')}")
        result.append(f"Free Cash Flow per Share: ${m.get('freeCashFlowPerShare', 'N/D')}")
        result.append(f"Book Value per Share: ${m.get('bookValuePerShare', 'N/D')}")
    
    # Outlook/Growth
    outlook = fmp_data.get('company_outlook', {})
    if outlook:
        result.append("\n\n=== COMPANY OUTLOOK ===")
        profile = outlook.get('profile', {})
        if profile:
            result.append(f"CEO: {profile.get('ceo', 'N/D')}")
            result.append(f"Employees: {profile.get('employees', 'N/D')}")
            result.append(f"Industry: {profile.get('industry', 'N/D')}")
            result.append(f"Sector: {profile.get('sector', 'N/D')}")
    
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
    
    # Calcular crecimiento YoY si hay datos históricos
    revenue_growth = None
    eps_growth = None
    
    if len(income) >= 5:  # Comparar con mismo trimestre año anterior
        try:
            current_rev = latest.get('revenue', 0)
            current_eps = latest.get('eps', 0)
            
            # Buscar mismo trimestre año anterior (aproximadamente 4 trimestres atrás)
            yoy = income[4] if len(income) > 4 else None
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
# VISUALIZACIÓN DE EARNINGS ESTILO REPORT
# ────────────────────────────────────────────────

def render_earnings_report_section(data, fmp_data):
    """Renderiza una sección de earnings report estilo las imágenes."""
    
    if not fmp_data:
        st.info("📊 Datos de FMP no disponibles. Configura FMP_API_KEY en secrets para ver el reporte completo.")
        return
    
    latest = get_latest_earnings_summary(fmp_data)
    
    if not latest:
        st.warning("⚠️ No se pudieron obtener datos recientes de earnings")
        return
    
    # Header del reporte
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
    
    # KPIs principales
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
    
    # Gráfico de Revenue y EPS histórico
    st.markdown("---")
    render_earnings_history_chart(fmp_data)
    
    # Forward Guidance
    st.markdown("---")
    render_forward_guidance(fmp_data, data)
    
    # Análisis de sorpresas
    st.markdown("---")
    render_earnings_surprises(fmp_data)

def render_earnings_history_chart(fmp_data):
    """Renderiza gráfico histórico de revenue y EPS."""
    income = fmp_data.get('income_statement', [])
    
    if not income or len(income) < 2:
        st.info("📊 Datos históricos insuficientes")
        return
    
    # Preparar datos (orden cronológico)
    dates = []
    revenues = []
    eps_values = []
    
    for i in reversed(income[:8]):  # Últimos 8 trimestres, ordenados
        dates.append(i.get('date', ''))
        revenues.append(i.get('revenue', 0) / 1e9)  # Convertir a billones
        eps_values.append(i.get('eps', 0))
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Revenue bars
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
    
    # EPS line
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
        
        # Generar bullets basados en datos
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
    
    # Próximos earnings
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
    
    # Crear visualización de beats/misses
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
        # Tabla de surprises
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
# RESTO DE FUNCIONES (mantenidas del código original)
# ────────────────────────────────────────────────

def get_yfinance_data(ticker_symbol):
    """Obtiene datos de yfinance."""
    try:
        rate_limit_delay()
        ticker = yf.Ticker(ticker_symbol)
        
        try:
            info = ticker.info
        except:
            info = dict(ticker.fast_info) if hasattr(ticker, 'fast_info') else {}
        
        try:
            hist = ticker.history(period="1y", auto_adjust=True)
            hist_dict = {
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'open': hist['Open'].tolist(),
                'high': hist['High'].tolist(),
                'low': hist['Low'].tolist(),
                'close': hist['Close'].tolist(),
                'volume': hist['Volume'].tolist()
            } if not hist.empty else None
        except:
            hist_dict = None
        
        try:
            calendar = ticker.calendar
            calendar_list = []
            if calendar is not None and not calendar.empty:
                for idx, row in calendar.iterrows():
                    calendar_list.append({
                        'date': str(idx),
                        'eps_est': row.get('Earnings Estimate', 'N/A'),
                        'revenue_est': row.get('Revenue Estimate', 'N/A')
                    })
        except:
            calendar_list = []
        
        return {
            'info': info, 
            'history': hist_dict, 
            'earnings': None,
            'calendar': calendar_list,
            'source': 'yfinance'
        }
        
    except Exception as e:
        print(f"Error yfinance: {e}")
        return None

def get_finnhub_data(ticker, api_key):
    """Obtiene datos de Finnhub."""
    if not api_key:
        return None
    
    try:
        base_url = "https://finnhub.io/api/v1"
        headers = {"X-Finnhub-Token": api_key}
        
        quote_resp = requests.get(f"{base_url}/quote", params={"symbol": ticker}, headers=headers, timeout=10)
        quote = quote_resp.json() if quote_resp.status_code == 200 else {}
        
        profile_resp = requests.get(f"{base_url}/stock/profile2", params={"symbol": ticker}, headers=headers, timeout=10)
        profile = profile_resp.json() if profile_resp.status_code == 200 else {}
        
        metrics_resp = requests.get(f"{base_url}/stock/metric", params={"symbol": ticker, "metric": "all"}, headers=headers, timeout=10)
        metrics = metrics_resp.json().get('metric', {}) if metrics_resp.status_code == 200 else {}
        
        return {
            'info': {
                'longName': profile.get('name'),
                'sector': profile.get('finnhubIndustry'),
                'industry': profile.get('industry'),
                'country': profile.get('country'),
                'website': profile.get('weburl'),
                'longBusinessSummary': profile.get('description'),
                'currentPrice': quote.get('c'),
                'previousClose': quote.get('pc'),
                'open': quote.get('o'),
                'dayHigh': quote.get('h'),
                'dayLow': quote.get('l'),
                'marketCap': (profile.get('marketCapitalization') or 0) * 1e6,
                'volume': quote.get('v'),
                'beta': metrics.get('beta'),
                'revenueGrowth': metrics.get('revenueGrowth5Y'),
                'ebitdaMargins': metrics.get('ebitdaMarginAnnual'),
                'profitMargins': metrics.get('netProfitMarginAnnual'),
                'trailingPE': metrics.get('peTTM'),
                'forwardPE': metrics.get('peNormalizedAnnual'),
                'returnOnEquity': metrics.get('roeTTM'),
                'trailingEps': metrics.get('epsTTM'),
                'totalCash': metrics.get('cashPerShareAnnual', 0) * (profile.get('shareOutstanding') or 0) * 1e6 if profile.get('shareOutstanding') else 0,
                'totalDebt': metrics.get('totalDebtAnnual'),
                'dividendYield': metrics.get('dividendYieldIndicatedAnnual'),
                'debtToEquity': metrics.get('totalDebtToTotalEquityAnnual'),
            },
            'history': None,
            'earnings': None,
            'calendar': [],
            'source': 'finnhub'
        }
        
    except Exception as e:
        print(f"Error Finnhub: {e}")
        return None

def process_data(raw_data, ticker):
    """Procesa datos crudos."""
    if not raw_data:
        return None
    
    info = raw_data.get('info', {})
    
    def get(keys, default=None):
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            if key in info and info[key] is not None:
                val = info[key]
                if isinstance(val, pd.Series):
                    return val.iloc[0] if len(val) > 0 else default
                if isinstance(val, (int, float, str, bool)):
                    return val
                try:
                    return float(val)
                except:
                    return val
        return default
    
    price = get(['currentPrice', 'regularMarketPrice', 'previousClose', 'c'], 0)
    prev_close = get(['previousClose', 'regularMarketPreviousClose', 'pc'], price)
    
    if price == 0:
        return None
    
    hist_df = pd.DataFrame()
    hist_data = raw_data.get('history')
    if hist_data:
        try:
            hist_df = pd.DataFrame({
                'Open': hist_data['open'],
                'High': hist_data['high'],
                'Low': hist_data['low'],
                'Close': hist_data['close'],
                'Volume': hist_data['volume']
            }, index=pd.to_datetime(hist_data['dates']))
        except:
            pass
    
    data = {
        "ticker": ticker,
        "name": get(['longName', 'shortName', 'name'], ticker),
        "sector": get(['sector', 'finnhubIndustry'], 'N/A'),
        "industry": get(['industry'], 'N/A'),
        "country": get(['country'], 'N/A'),
        "employees": int(get(['fullTimeEmployees'], 0) or 0),
        "website": get(['website', 'weburl'], '#'),
        "summary": get(['longBusinessSummary', 'description'], f"Empresa {ticker}"),
        
        "price": float(price),
        "prev_close": float(prev_close),
        "open": float(get(['open', 'regularMarketOpen', 'o'], price)),
        "day_high": float(get(['dayHigh', 'regularMarketDayHigh', 'h'], price * 1.01)),
        "day_low": float(get(['dayLow', 'regularMarketDayLow', 'l'], price * 0.99)),
        "fifty_two_high": float(get(['fiftyTwoWeekHigh', '52WeekHigh'], price * 1.2)),
        "fifty_two_low": float(get(['fiftyTwoWeekLow', '52WeekLow'], price * 0.8)),
        "volume": int(get(['volume', 'regularMarketVolume', 'v'], 0) or 0),
        "avg_volume": int(get(['averageVolume', 'avgVolume'], 0) or 0),
        
        "market_cap": float(get(['marketCap', 'marketCapitalization'], 0) or 0),
        "enterprise_value": float(get(['enterpriseValue'], 0) or 0),
        
        "rev_growth": float(get(['revenueGrowth', 'revenueGrowth5Y'])) if get(['revenueGrowth', 'revenueGrowth5Y']) is not None else None,
        "ebitda_margin": float(get(['ebitdaMargins', 'ebitdaMarginAnnual'])) if get(['ebitdaMargins', 'ebitdaMarginAnnual']) is not None else None,
        "profit_margin": float(get(['profitMargins', 'netProfitMarginAnnual'])) if get(['profitMargins', 'netProfitMarginAnnual']) is not None else None,
        "operating_margin": float(get(['operatingMargins'])) if get(['operatingMargins']) is not None else None,
        "gross_margin": float(get(['grossMargins'])) if get(['grossMargins']) is not None else None,
        
        "pe_trailing": float(get(['trailingPE', 'peTrailing', 'peTTM'])) if get(['trailingPE', 'peTrailing', 'peTTM']) is not None else None,
        "pe_forward": float(get(['forwardPE', 'peForward', 'peNormalizedAnnual'])) if get(['forwardPE', 'peForward', 'peNormalizedAnnual']) is not None else None,
        "peg_ratio": float(get(['pegRatio'])) if get(['pegRatio']) is not None else None,
        "price_to_sales": float(get(['priceToSalesTrailing12Months'])) if get(['priceToSalesTrailing12Months']) is not None else None,
        "price_to_book": float(get(['priceToBook'])) if get(['priceToBook']) is not None else None,
        
        "eps": float(get(['trailingEps', 'epsTTM'])) if get(['trailingEps', 'epsTTM']) is not None else None,
        "eps_forward": float(get(['forwardEps'])) if get(['forwardEps']) is not None else None,
        "eps_growth": float(get(['earningsGrowth'])) if get(['earningsGrowth']) is not None else None,
        
        "roe": float(get(['returnOnEquity', 'roeTTM'])) if get(['returnOnEquity', 'roeTTM']) is not None else None,
        "roa": float(get(['returnOnAssets'])) if get(['returnOnAssets']) is not None else None,
        
        "cash": float(get(['totalCash', 'freeCashflow'], 0) or 0),
        "free_cashflow": float(get(['freeCashflow'], 0) or 0),
        "operating_cashflow": float(get(['operatingCashflow'], 0) or 0),
        "debt": float(get(['totalDebt', 'totalDebtAnnual'], 0) or 0),
        "debt_to_equity": float(get(['debtToEquity', 'totalDebtToTotalEquityAnnual'])) if get(['debtToEquity', 'totalDebtToTotalEquityAnnual']) is not None else None,
        "current_ratio": float(get(['currentRatio'])) if get(['currentRatio']) is not None else None,
        
        "dividend_rate": float(get(['dividendRate'], 0) or 0),
        "dividend_yield": float(get(['dividendYield', 'dividendYieldIndicatedAnnual'], 0) or 0) / 100 if get(['dividendYield'], 0) and get(['dividendYield'], 0) > 1 else float(get(['dividendYield'], 0) or 0),
        "ex_div_date": get(['exDividendDate']),
        "payout_ratio": float(get(['payoutRatio'], 0) or 0),
        
        "target_high": float(get(['targetHighPrice'], price * 1.2)),
        "target_low": float(get(['targetLowPrice'], price * 0.8)),
        "target_mean": float(get(['targetMeanPrice', 'targetMedianPrice'], price)),
        "target_median": float(get(['targetMedianPrice', 'targetMeanPrice'], price)),
        "recommendation": get(['recommendationKey'], 'none'),
        "num_analysts": int(get(['numberOfAnalystOpinions'], 0) or 0),
        
        "hist": hist_df,
        "earnings_hist": pd.DataFrame(),
        "earnings_calendar": raw_data.get('calendar', []),
        "beta": float(get(['beta'], 0) or 0),
        
        "is_real_data": raw_data.get('source') != 'mock',
        "data_source": raw_data.get('source', 'unknown')
    }
    
    if data['prev_close'] and data['prev_close'] != 0:
        data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
        data['change_abs'] = data['price'] - data['prev_close']
    else:
        data['change_pct'] = 0
        data['change_abs'] = 0
        
    if data['fifty_two_high'] and data['fifty_two_high'] != 0:
        data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
    else:
        data['pct_from_high'] = 0
    
    return data

def get_mock_data(ticker):
    """Datos de demostración."""
    mock_db = {
        "AAPL": {"name": "Apple Inc.", "sector": "Technology", "price": 275.69, "market_cap": 4.05e12, "rev_growth": 0.157, "pe_forward": 29.7, "eps": 7.91, "dividend_yield": 0.0038, "roe": 1.52, "beta": 1.107, "ebitda_margin": 0.351, "profit_margin": 0.270},
        "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "price": 420.30, "market_cap": 3.1e12, "rev_growth": 0.15, "pe_forward": 32.0, "eps": 11.80, "dividend_yield": 0.007, "roe": 0.38, "beta": 0.9, "ebitda_margin": 0.45, "profit_margin": 0.35},
        "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "price": 875.50, "market_cap": 2.15e12, "rev_growth": 2.10, "pe_forward": 35.0, "eps": 12.90, "dividend_yield": 0.0003, "roe": 0.55, "beta": 1.75, "ebitda_margin": 0.58, "profit_margin": 0.48},
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
        "ticker": ticker, "name": mock["name"], "sector": mock["sector"], "industry": "Technology",
        "country": "United States", "employees": 100000, "website": "#",
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
        "roe": mock["roe"], "roa": mock["roe"] * 0.6, "cash": mock["market_cap"] * 0.05,
        "free_cashflow": mock["market_cap"] * 0.03, "operating_cashflow": mock["market_cap"] * 0.04,
        "debt": mock["market_cap"] * 0.15, "debt_to_equity": 50.0, "current_ratio": 1.2,
        "dividend_rate": price * mock["dividend_yield"], "dividend_yield": mock["dividend_yield"],
        "ex_div_date": None, "payout_ratio": 0.20, "target_high": price * 1.3,
        "target_low": price * 0.8, "target_mean": price * 1.1, "target_median": price * 1.1,
        "recommendation": "buy", "num_analysts": 35, "hist": pd.DataFrame(),
        "earnings_hist": pd.DataFrame(), "earnings_calendar": [],
        "beta": mock["beta"], "is_real_data": False, "data_source": "mock",
        "change_pct": 2.04, "change_abs": price * 0.02, "pct_from_high": -5.0
    }

# ────────────────────────────────────────────────
# FUNCIONES DE RENDER
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
# ANÁLISIS RSU - CON FMP DATA Y FECHA ACTUAL
# ────────────────────────────────────────────────

def render_rsu_earnings_analysis(data, fmp_data=None):
    """Renderiza el análisis con datos de FMP si están disponibles."""
    
    base_prompt = load_rsu_prompt()
    
    if not base_prompt:
        st.warning("⚠️ Prompt RSU no encontrado.")
        return
    
    # Formatear datos de FMP con fecha actual
    fmp_formatted = format_fmp_earnings_data(fmp_data) if fmp_data else "No disponible"
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Construir datos para el prompt - FORMATO MÁS COMPACTO
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
    
    # Si no hay placeholders, concatenar
    if "{datos_ticker}" not in base_prompt:
        prompt_completo = f"{base_prompt}\n\n{datos_ticker}\n\n=== INSTRUCCION ===\nGenera el reporte COMPLETO en español. Usa los datos proporcionados. La fecha actual es {current_date}. Si algún dato es 0 o None, indícalo explícitamente."
    
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
            
            # Detectar si la respuesta parece truncada
            if not response_text.strip().endswith('---') and len(response_text) > 100:
                if '## 8. VEREDICTO RSU' not in response_text or len(response_text) < 2000:
                    st.warning("⚠️ La respuesta parece incompleta. Intentando regenerar...")
                    
                    short_prompt = f"""Análisis fundamental rápido de {data['ticker']} al {current_date}:

Precio: ${data['price']:.2f} | Market Cap: {format_value(data['market_cap'], '$')}
P/E: {format_value(data.get('pe_forward'), '', 'x', 2)} | ROE: {format_value(data.get('roe'), '', '%', 2)} | Margen: {format_value(data.get('profit_margin'), '', '%', 2)}

Genera:
1. Snapshot (thesis 1 línea)
2. Valoración (P/E, PEG análisis)
3. Calidad negocio (márgenes, ROE)
4. Salud financiera (cash, deuda)
5. Consenso analistas
6. Bull/Bear case
7. Score /10 y recomendación final

Sé conciso pero completo."""
                    
                    response = model.generate_content(
                        short_prompt,
                        generation_config={
                            "temperature": 0.2,
                            "max_output_tokens": 4096,
                        }
                    )
                    response_text = response.text
            
            # TERMINAL HACKER STYLE OUTPUT
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
            .terminal-body table {
                border-collapse: collapse;
                width: 100%;
                margin: 10px 0;
            }
            .terminal-body th, .terminal-body td {
                border: 1px solid #2a3f5f;
                padding: 8px;
                text-align: left;
            }
            .terminal-body th {
                background-color: #1a1e26;
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
            
            with st.expander("🔧 Ver prompt enviado (debug)"):
                st.text_area("Prompt", prompt_completo, height=300)
                st.text_area("Respuesta raw", response_text, height=200)
            
    except Exception as e:
        st.error(f"❌ Error en generación: {e}")
        st.error(f"Detalles: {str(e)}")
        generate_fallback_analysis(data)

def generate_fallback_analysis(data):
    """Genera un análisis básico localmente si la IA falla."""
    
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
    
    if data.get('profit_margin') and data['profit_margin'] > 0.15:
        score += 0.5
        factors.append("Buenos márgenes")
    
    if data.get('debt_to_equity') and data['debt_to_equity'] < 50:
        score += 0.5
        factors.append("Baja deuda")
    
    score = max(1, min(10, score))
    
    recommendation = "COMPRA FUERTE" if score >= 8 else "COMPRA" if score >= 6.5 else "MANTENER" if score >= 5 else "VENDER" if score >= 3 else "VENDER FUERTE"
    
    st.markdown(f"""
    ### 📊 ANÁLISIS FALLBACK (IA no disponible)
    
    **{data['ticker']} - {data['name']}**
    
    | Métrica | Valor |
    |---------|-------|
    | Precio | ${data['price']:.2f} |
    | P/E Forward | {format_value(data.get('pe_forward'), '', 'x', 2)} |
    | ROE | {format_value(data.get('roe'), '', '%', 2)} |
    | Margen Neto | {format_value(data.get('profit_margin'), '', '%', 2)} |
    
    **Score RSU: {score:.1f}/10**
    
    **Recomendación: {recommendation}**
    
    **Factores considerados:** {', '.join(factors) if factors else 'Datos limitados'}
    """)

# ────────────────────────────────────────────────
# MAIN - CON SECCIÓN DE EARNINGS REPORT
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .stApp { background-color: #0c0e12; }
        .stTextInput > div > div > input { background-color: #1a1e26; color: white; border: 1px solid #2a3f5f; border-radius: 8px; }
        .stButton > button { background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%); color: #0c0e12; border: none; border-radius: 8px; font-weight: bold; }
        ::-webkit-scrollbar {
            width: 8px;
            background: #0c0e12;
        }
        ::-webkit-scrollbar-thumb {
            background: #00ffad;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #00cc8a;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📅 Análisis de Earnings")
    st.markdown('<div style="color: #888; margin-bottom: 20px;">Análisis fundamental con IA y datos en tiempo real</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("Ticker", value="AAPL").upper().strip()
    with col2:
        st.write("")
        st.write("")
        analyze = st.button("🔍 Analizar", use_container_width=True)
    
    if analyze and ticker:
        with st.spinner("Cargando datos..."):
            # Intentar obtener datos de FMP primero (CRÍTICO para earnings)
            fmp_api_key = st.secrets.get("FMP_API_KEY", None)
            fmp_data = None
            
            if fmp_api_key:
                fmp_data = get_fmp_data(ticker, fmp_api_key)
                if fmp_data:
                    st.success(f"✅ FMP API conectado - Datos actualizados al {fmp_data.get('last_updated', 'ahora')}")
            
            # Datos de yfinance/Finnhub para fundamentales y precio
            raw = get_yfinance_data(ticker)
            if not raw:
                finnhub_key = st.secrets.get("FINNHUB_API_KEY", None)
                if finnhub_key:
                    raw = get_finnhub_data(ticker, finnhub_key)
            
            if raw:
                data = process_data(raw, ticker)
            else:
                data = get_mock_data(ticker)
        
        if not data:
            st.error("No se pudieron obtener datos")
            return
        
        change_color = "#00ffad" if data.get('change_pct', 0) >= 0 else "#f23645"
        source_color = {"yfinance": "#00ffad", "finnhub": "#4caf50", "mock": "#ff9800"}.get(data.get('data_source'), "#888")
        source_label = {"yfinance": "YAHOO FINANCE", "finnhub": "FINNHUB", "mock": "DEMO"}.get(data.get('data_source'), "UNKNOWN")
        
        # Header principal
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            <div style="margin-bottom: 5px;">
                <span style="background: {source_color}22; color: {source_color}; padding: 4px 12px; border-radius: 4px; font-size: 10px; font-weight: bold; border: 1px solid {source_color};">
                    ● {source_label}
                </span>
                <span style="color: #666; font-size: 12px; margin-left: 10px;">{data.get('sector', 'N/A')} • {data.get('industry', 'N/A')}</span>
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
        
        # === NUEVA SECCIÓN: EARNINGS REPORT ESTILO IMÁGENES ===
        st.markdown("---")
        render_earnings_report_section(data, fmp_data)
        
        # Métricas fundamentales
        st.markdown("---")
        st.markdown("### 📊 Métricas Fundamentales")
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
                    color = "#00ffad" if value else "#888"
                st.markdown(f"""
                <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 18px; text-align: center;">
                    <div style="color: #666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">{label}</div>
                    <div style="color: {color}; font-size: 1.4rem; font-weight: bold;">{formatted}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Gráfico de precio y métricas clave
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
            st.markdown(f"<div style='color: #aaa; font-size: 13px; line-height: 1.6;'>{data.get('summary', 'N/A')[:300]}...</div>", unsafe_allow_html=True)
            
            st.markdown("#### 💰 Métricas Clave")
            st.markdown(f"""
            <div style="background: #0c0e12; border-radius: 8px; padding: 15px; border: 1px solid #1a1e26; font-size: 12px; line-height: 2;">
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">Cash:</span> <span style="color: #00ffad; font-weight: bold;">{format_value(data.get('cash'), '$')}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">Deuda:</span> <span style="color: #f23645; font-weight: bold;">{format_value(data.get('debt'), '$')}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">FCF:</span> <span style="color: {'#00ffad' if (data.get('free_cashflow') or 0) > 0 else '#f23645'}; font-weight: bold;">{format_value(data.get('free_cashflow'), '$')}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">Beta:</span> <span style="color: white; font-weight: bold;">{data.get('beta', 0):.2f}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">52S vs Max:</span> <span style="color: {'#00ffad' if data.get('pct_from_high', 0) > -10 else '#f23645'}; font-weight: bold;">{data.get('pct_from_high', 0):.1f}%</span></div>
            </div>
            """, unsafe_allow_html=True)
        
        # Perspectivas y análisis RSU
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
        
        # Análisis RSU con IA
        st.markdown("---")
        render_rsu_earnings_analysis(data, fmp_data)
        
        # Footer
        st.markdown(f"""
        <div style="text-align: center; color: #444; font-size: 11px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #1a1e26;">
            Datos proporcionados por Yahoo Finance & Financial Modeling Prep | Análisis generado por IA Gemini<br>
            <span style="color: #00ffad;">RSU Dashboard Pro</span> • Para fines informativos únicamente
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
