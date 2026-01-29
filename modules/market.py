# modules/market.py
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from config import get_cnn_fear_greed

@st.cache_data(ttl=3600)
def get_market_index(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).fast_info
        p = data['last_price']
        c = ((p - data['previous_close']) / data['previous_close']) * 100
        return p, c
    except:
        return 0.0, 0.0

def render():
    st.title("Market Overview")

    idx = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "VIX": "^VIX", "BTC": "BTC-USD"}
    cols = st.columns(4)
    for i, (n, s) in enumerate(idx.items()):
        p, c = get_market_index(s)
        color = "#00ffad" if (c >= 0 and n != "VIX") or (c < 0 and n == "VIX") else "#f23645"
        cols[i].markdown(
            f"""
            <div class="metric-card">
                <small>{n}</small>
                <h3>{p:,.1f}</h3>
                <p style="color:{color}">{c:.2f}%</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    t1, t2 = st.tabs(["📰 NOTICIAS", "💰 EARNINGS"])
    with t1:
        try:
            df = pd.read_csv(st.secrets["URL_NOTICIAS"])
            st.dataframe(df, use_container_width=True)
        except Exception:
            st.info("Falta URL_NOTICIAS en Secrets.")
    with t2:
        st.info("Aquí puedes añadir tabla de próximos earnings.")
