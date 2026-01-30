# modules/market.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from config import get_market_index

def render_credit_spreads_chart():
    # Simulación de datos (puedes conectar con FRED API después)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='D')
    values = np.random.uniform(2.5, 3.5, size=30)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=values, fill='tozeroy',
        line=dict(color='#f23645', width=2),
        fillcolor='rgba(242, 54, 69, 0.1)'
    ))
    fig.update_layout(
        height=250, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#222")
    )
    return fig

def render():
    st.title("Market Dashboard")
    
    col_idx, col_spread = st.columns([1, 2])
    
    # CAJA IZQUIERDA: ÍNDICES
    with col_idx:
        st.markdown('<div class="group-container">', unsafe_allow_html=True)
        st.markdown('<div class="group-title">Market Indices</div>', unsafe_allow_html=True)
        
        indices = [
            {"label": "SPY", "n": "S&P 500", "t": "SPY"},
            {"label": "QQQ", "n": "Nasdaq 100", "t": "QQQ"},
            {"label": "DIA", "n": "Dow Jones", "t": "DIA"},
            {"label": "IWM", "n": "Russell 2000", "t": "IWM"}
        ]
        
        for idx in indices:
            p, c = get_market_index(idx['t'])
            color_class = "pos" if c >= 0 else "neg"
            st.markdown(f"""
                <div class="index-card">
                    <div><p class="index-ticker">{idx['label']}</p></div>
                    <div style="text-align:right;">
                        <p class="index-price">${p:,.2f}</p>
                        <span class="index-delta {color_class}">{c:+.2f}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # CAJA DERECHA: CREDIT SPREADS
    with col_spread:
        st.markdown('<div class="group-container">', unsafe_allow_html=True)
        st.markdown('<div class="group-title">US High Yield Credit Spreads</div>', unsafe_allow_html=True)
        st.plotly_chart(render_credit_spreads_chart(), use_container_width=True)
        st.markdown('<p style="color:#555; font-size:10px; text-align:center;">OAS - Higher spreads indicate higher credit risk</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")
    # Aquí puedes añadir el buscador de tickers para el gráfico de TradingView...
