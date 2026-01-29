import streamlit as st
import pandas as pd
from config import get_market_index

def draw_index_card(ticker, name, symbol):
    """Renderiza una caja de índice estilizada"""
    price, change = get_market_index(symbol)
    
    # Determinar color y flecha
    color_class = "pos" if change >= 0 else "neg"
    arrow = "▲" if change >= 0 else "▼"
    
    # Invertir colores si es el VIX (opcional, si decides incluirlo)
    if ticker == "VIX":
        color_class = "neg" if change >= 0 else "pos"

    st.markdown(f"""
        <div class="index-card">
            <div class="index-name-container">
                <p class="index-ticker">{ticker}</p>
                <p class="index-fullname">{name}</p>
            </div>
            <div class="index-price-container">
                <p class="index-price">${price:,.2f}</p>
                <span class="index-delta {color_class}">
                    {arrow} {abs(change):.2f}%
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render():
    st.title("Market Overview")
    
    # Definición de los 4 índices solicitados
    indices = [
        {"ticker": "US500", "name": "S&P 500 Index", "symbol": "^GSPC"},
        {"ticker": "NASDAQ", "name": "Nasdaq 100", "symbol": "^IXIC"},
        {"ticker": "DOW J", "name": "DJ Industrial Avg", "symbol": "^DJI"},
        {"ticker": "RUSSELL", "name": "Russell 2000", "symbol": "^RUT"}
    ]
    
    # Renderizar en 4 columnas
    cols = st.columns(4)
    for i, item in enumerate(indices):
        with cols[i]:
            draw_index_card(item["ticker"], item["name"], item["symbol"])
    
    # Tabs inferiores
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
