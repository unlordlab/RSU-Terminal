# modules/market.py
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from config import get_market_index

def render_credit_spreads():
    """Genera el gràfic de High Yield Credit Spreads estil captura"""
    # Simulem dades o usem FRED si tens la llibreria instal·lada
    # Per aquest exemple, creem una sèrie temporal realista
    dates = pd.date_range(start="2025-05-27", periods=100, freq='D')
    values = [3.2, 3.1, 3.3, 3.1, 2.9, 3.0, 2.8, 3.1, 2.9, 2.7, 2.8, 3.1, 2.9, 2.8, 2.7] # ... simplificat
    # Estenem per tenir 100 punts
    import numpy as np
    values = np.interp(np.linspace(0, 14, 100), np.arange(15), values) + np.random.normal(0, 0.05, 100)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=values, fill='tozeroy',
        line=dict(color='#f23645', width=2),
        fillcolor='rgba(242, 54, 69, 0.1)'
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, color="#555"),
        yaxis=dict(showgrid=True, gridcolor="#222", color="#555", side="left", title="Spread (%)"),
        hovermode="x unified"
    )
    return fig

def render():
    st.title("Market Dashboard")
    
    col_left, col_right = st.columns([1, 2])
    
    # --- COLUMNA ESQUERRA: MARKET INDICES ---
    with col_left:
        st.markdown('<div class="group-container">', unsafe_allow_html=True)
        st.markdown('<div class="group-title">Market Indices</div>', unsafe_allow_html=True)
        
        indices = [
            {"label": "SPY", "name": "S&P 500", "ticker": "SPY"},
            {"label": "QQQ", "name": "Nasdaq 100", "ticker": "QQQ"},
            {"label": "DIA", "name": "Dow Jones", "ticker": "DIA"},
            {"label": "IWM", "name": "Russell 2000", "ticker": "IWM"}
        ]
        
        for idx in indices:
            price, delta = get_market_index(idx['ticker'])
            d_class = "pos" if delta >= 0 else "neg"
            d_sign = "+" if delta >= 0 else ""
            
            st.markdown(f"""
                <div class="index-card">
                    <div class="index-name-container">
                        <p class="index-ticker">{idx['label']}</p>
                        <p class="index-fullname">{idx['name']}</p>
                    </div>
                    <div class="index-price-container">
                        <p class="index-price">${price:,.2f}</p>
                        <div class="index-delta {d_class}">{d_sign}{delta:.2f}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown('<div class="container-footer">Market Open • Updated Just Now</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- COLUMNA DRETA: CREDIT SPREADS ---
    with col_right:
        st.markdown('<div class="group-container">', unsafe_allow_html=True)
        col_t1, col_t2 = st.columns([2,1])
        with col_t1:
            st.markdown('<div class="group-title">US High Yield Credit Spreads</div>', unsafe_allow_html=True)
        with col_t2:
            st.markdown('<p style="text-align:right; color:#888; font-size:12px;">Current: <span style="color:white; font-weight:bold;">2.72%</span></p>', unsafe_allow_html=True)
        
        st.plotly_chart(render_credit_spreads(), use_container_width=True)
        st.markdown('<div class="container-footer">Option-Adjusted Spread (OAS) • Higher spreads indicate higher credit risk</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Espai i següents seccions (Notícies/Earnings)
    st.write("---")
    render_analysis_section()

def render_analysis_section():
    t1, t2 = st.tabs(["📰 NOTICIAS", "💰 EARNINGS"])
    # ... (el teu codi de t1 i t2 es manté igual) ...
