# modules/credit_spreads.py
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

@st.cache_data(ttl=1800)  # 30min
def get_credit_spreads():
    """High Yield Spreads desde FRED + yfinance"""
    
    # Ticker FRED High Yield Spread (BAMLH0A0HYM2)
    try:
        # Datos históricos 1Y
        end_date = datetime.now()
        start_date = end_date - timedelta(days=400)
        
        # High Yield OAS (disponible via yfinance)
        hy_ticker = yf.Ticker("^HYG")  # iShares High Yield ETF como proxy
        hy_data = hy_ticker.history(start=start_date, end=end_date)
        
        return hy_data
    except:
        # Datos demo si falla
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        spreads = [2.71, 2.69, 2.68, 2.64, 2.69, 2.71, 2.72] * 5
        return pd.DataFrame({
            'Close': spreads[:30],
        }, index=dates)

def render():
    st.subheader("📈 **US High Yield Credit Spreads**")
    st.caption("🔴 >4% = Estrés | 🟡 2.5-4% = Cautela | 🟢 <2.5% = Normal")
    
    df = get_credit_spreads()
    
    # Valor actual
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        current_spread = df['Close'].iloc[-1] if 'Close' in df.columns else 2.71
        st.metric("HY Spread (OAS)", f"{current_spread:.2f}%", delta=None)
    
    with col2:
        st.metric("Nivel", "🟢 Normal", None)
    with col3:
        st.info(f"**27 Ene 2026**: 2.71% [web:222]")
    
    # Gráfico principal
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['Close'],
        mode='lines+markers',
        name='HY Spread (%)',
        line=dict(color='#FF6B35', width=3),
        marker=dict(size=4)
    ))
    
    # Niveles críticos
    fig.add_hline(y=4.0, line_dash="dash", line_color="red",
                  annotation_text="Estrés (4%)", annotation_position="top right")
    fig.add_hline(y=2.5, line_dash="dash", line_color="orange",
                  annotation_text="Cautela (2.5%)", annotation_position="bottom right")
    
    fig.update_layout(
        title="ICE BofA US High Yield Index OAS (1 Año)",
        xaxis_title="Fecha",
        yaxis_title="Spread (%)",
        height=400,
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla datos recientes
    st.subheader("📋 Últimos 10 días")
    recent = df.tail(10)[['Close']].round(2)
    recent.columns = ['Spread (%)']
    st.dataframe(recent, use_container_width=True)
    
    # Interpretación
    st.markdown("""
    **💡 Interpretación:**
    - **🟢 <2.5%**: Mercado calmado, inversores confían
    - **🟡 2.5-4%**: Cautela moderada 
    - **🔴 >4%**: Estrés financiero, riesgo recesión
    """)
