# app.py - RSU Terminal Dashboard COMPLETO
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import yfinance as yf
import pandas as pd

# Importar módulos
from modules import cartera, credit_spreads, fear_greed

# Configuración página
st.set_page_config(
    page_title="RSU Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header principal
    st.markdown('<h1 class="main-header">🚀 RSU Terminal</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("📊 Dashboard")
    page = st.sidebar.selectbox(
        "Navegación:",
        ["📈 Overview", "💼 Cartera", "📈 Credit Spreads", "😱 Fear & Greed"]
    )
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💼 Cartera", "📈 Credit Spreads", "😱 Fear & Greed"])
    
    with tab1:
        render_overview()
    
    with tab2:
        cartera.render()
    
    with tab3:
        credit_spreads.render()
    
    with tab4:
        fear_greed.render()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        Desarrollado con ❤️ para Zaragoza, España | Jan 2026
    </div>
    """, unsafe_allow_html=True)

def render_overview():
    """Dashboard principal con KPIs clave"""
    st.subheader("📊 Resumen Ejecutivo")
    
    # KPIs principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Fear & Greed
        fg_value = 65  # Demo - se actualiza desde módulo
        fg_color = "🟢" if fg_value < 50 else "🟡" if fg_value < 75 else "🔴"
        st.metric(f"{fg_color} Fear & Greed", fg_value, None)
    
    with col2:
        # Cartera PnL
        total_pnl = 2450  # Demo - desde cartera
        st.metric("💰 Total PnL", f"${total_pnl:,}", "+12.3%")
    
    with col3:
        # HY Spread
        hy_spread = 2.71
        st.metric("📈 HY Spread", f"{hy_spread}%", "-0.02%")
    
    with col4:
        # Posiciones
        positions = 3
        st.metric("📋 Posiciones", positions, None)
    
    # Gráficos principales
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Cartera PnL")
        fig_pnl = go.Figure()
        fig_pnl.add_trace(go.Bar(
            x=['NVDA', 'TSLA', 'AAPL'],
            y=[102, 38, 180],
            marker_color=['green', 'green', 'green']
        ))
        fig_pnl.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_pnl, use_container_width=True)
    
    with col2:
        st.subheader("📊 Credit Spreads")
        fig_spread = go.Figure()
        fig_spread.add_trace(go.Scatter(
            x=pd.date_range(end=datetime.now(), periods=30),
            y=[2.71, 2.69, 2.68, 2.64] * 8,
            mode='lines'
        ))
        fig_spread.add_hline(y=4.0, line_dash="dash", line_color="red")
        fig_spread.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_spread, use_container_width=True)

if __name__ == "__main__":
    main()
