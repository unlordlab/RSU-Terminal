# modules/market.py
import streamlit as st
import yfinance as yf
import pandas as pd
from config import get_market_index

def render():
    """Función principal del dashboard - NO poner nada fuera de esta función"""
    st.title("Market Overview")
    
    # 4 cards principales
    idx = {
        "S&P 500": "^GSPC", 
        "NASDAQ": "^IXIC", 
        "VIX": "^VIX", 
        "BTC": "BTC-USD"
    }
    
    cols = st.columns(4)
    for i, (name, symbol) in enumerate(idx.items()):
        with cols[i]:
            price, change = get_market_index(symbol)
            
            # Color y emoji dinámicos
            if name == "VIX":
                color = "#00ffad" if change < 0 else "#f23645"
                trend_emoji = "📉" if change < 0 else "📈"
            else:
                color = "#00ffad" if change >= 0 else "#f23645"
                trend_emoji = "📈" if change >= 0 else "📉"
            
            # Card estilo pro
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 12px; opacity: 0.8; margin-bottom: 8px;">{name}</div>
                <div style="font-size: 28px; font-weight: bold; margin-bottom: 8px;">${price:,.0f}</div>
                <div style="font-size: 14px; color: {color}; font-weight: bold;">
                    {trend_emoji} {change:+.2f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Tabs noticias/earnings
    t1, t2 = st.tabs(["📰 NOTICIAS", "💰 EARNINGS"])
    
    with t1:
        try:
            df = pd.read_csv(st.secrets["URL_NOTICIAS"])
            st.dataframe(df[["Fecha", "Ticker", "Título", "Impacto"]], 
                        use_container_width=True, hide_index=True)
        except:
            st.info("🔄 Configura URL_NOTICIAS en Secrets")
    
    with t2:
        st.info("💼 Próximos Earnings Calendar - En desarrollo")

# FIN DEL ARCHIVO - NADA FUERA DE LA FUNCIÓN render()
