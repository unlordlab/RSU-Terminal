import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import get_market_index

def get_crypto_prices():
    """Simula precios de Crypto (puedes conectar con API de Binance/CoinGecko luego)."""
    return [
        ("BTC", "104,231.50", "+2.4%"),
        ("ETH", "3,120.12", "-1.1%"),
        ("SOL", "245.88", "+5.7%"),
    ]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # --- CONFIGURACIÓN DE ALTURAS UNIFICADAS ---
    H1 = "420px"  # Altura Fila 1
    H2 = "300px"  # Altura Fila 2
    H3 = "250px"  # Altura Fila 3

    # --- FILA 1 ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Market Indices
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:15px; border-radius:10px; margin-bottom:12px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
                <div><div style="font-weight:bold; color:white; font-size:14px;">{n}</div><div style="color:#555; font-size:11px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:14px;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1] >= 0 else "#f23645"}; font-size:12px; font-weight:bold;">{get_market_index(t)[1]:+.2f}%</div></div>
            </div>''' for t, n in indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{H1}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        # Economic Calendar (Espacio para tu lógica de scraping o fallback)
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{H1}; overflow-y:auto; padding:10px;"><p style="color:#555; font-size:12px; text-align:center;">Real-time events loading...</p></div></div>', unsafe_allow_html=True)

    with col3:
        # Reddit Top 10
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "SNDK", "NVDA", "DVLT", "PLTR"]
        reddit_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#333; font-weight:bold; font-size:11px;">{i+1:02d}</span><span style="color:#00ffad; font-weight:bold; font-size:13px;">{tkr}</span><span style="color:#f23645; font-size:9px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 6px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Top 10 Pulse</p></div><div class="group-content" style="background:#11141a; height:{H1}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # --- FILA 2 ---
    st.write("")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # Fear & Greed
        val = 65
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Fear & Greed Index</p></div><div class="group-content" style="background:#11141a; height:{H2}; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div style="font-size:3.5rem; font-weight:bold; color:#00ffad;">{val}</div><div style="color:white; font-size:0.8rem; letter-spacing:2px; font-weight:bold;">GREED</div>
            <div style="width:80%; background:#0c0e12; height:10px; border-radius:5px; margin-top:20px; border:1px solid #1a1e26;"><div style="width:{val}%; background:#00ffad; height:100%; border-radius:5px; box-shadow:0 0 10px #00ffad88;"></div></div>
            </div></div>''', unsafe_allow_html=True)

    with c2:
        # Market Heatmap
        sectors = [("TECH", +1.2), ("FIN", -0.4), ("HLTH", +0.1), ("ENER", +2.1), ("CONS", -0.8), ("UTIL", -0.2)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:10px; font-weight:bold;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Sectors Heatmap</p></div><div class="group-content" style="background:#11141a; height:{H2}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c3:
        # CRYPTO PULSE
        cryptos = get_crypto_prices()
        crypto_html = "".join([f'''
            <div style="background:#0c0e12; padding:12px; border-radius:8px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="color:white; font-weight:bold; font-size:13px;">{symbol}</div><div style="color:#555; font-size:9px;">TOKEN</div></div>
                <div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${price}</div><div style="color:{"#00ffad" if "+" in change else "#f23645"}; font-size:11px; font-weight:bold;">{change}</div></div>
            </div>''' for symbol, price, change in cryptos])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p></div><div class="group-content" style="background:#11141a; height:{H2}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

    # --- FILA 3 (NUEVA) ---
    st.write("")
    f3_c1, f3_c2, f3_c3 = st.columns(3)
    
    for i, col in enumerate([f3_c1, f3_c2, f3_c3]):
        with col:
            st.markdown(f'''
                <div class="group-container">
                    <div class="group-header"><p class="group-title">Module 3.{i+1}</p></div>
                    <div class="group-content" style="background:#11141a; height:{H3}; border:1px solid #1a1e26; border-top:none; display:flex; align-items:center; justify-content:center; color:#222; font-weight:bold; letter-spacing:3px;">
                        VOID
                    </div>
                </div>''', unsafe_allow_html=True)
