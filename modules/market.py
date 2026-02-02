import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import get_market_index

def get_fear_greed_value():
    """Simula u obtiene el valor del sentimiento (0-100)."""
    # En producción, podrías usar scrapers para CNN Fear & Greed
    # Por ahora, fijamos un valor dinámico para el diseño
    return 65, "GREED" # Valor, Etiqueta

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    MASTER_HEIGHT = "420px"

    col1, col2, col3 = st.columns(3)
    
    # --- FILA 1: ESTABLECIDA ---
    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:15px; border-radius:10px; margin-bottom:12px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
                <div><div style="font-weight:bold; color:white; font-size:14px;">{n}</div><div style="color:#555; font-size:11px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:14px;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1] >= 0 else "#f23645"}; font-size:12px; font-weight:bold;">{get_market_index(t)[1]:+.2f}%</div></div>
            </div>''' for t, n in indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        # (Aquí va tu código del Economic Calendar Nativo que ya funciona)
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; overflow-y:auto; padding:10px;">{st.session_state.get("calendar_html", "Cargando eventos...")}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "SNDK", "NVDA", "DVLT", "PLTR"]
        reddit_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#333; font-weight:bold; font-size:11px;">{i+1:02d}</span>
                <span style="color:#00ffad; font-weight:bold; font-size:13px;">{tkr}</span>
                <span style="color:#f23645; font-size:9px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 6px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Top 10 Pulse</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # --- FILA 2: EL NUEVO MÓDULO ---
    st.write("")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        val, label = get_fear_greed_value()
        # Colores dinámicos según el valor
        meter_color = "#00ffad" if val > 50 else "#f23645"
        
        st.markdown(f'''
            <div class="group-container">
                <div class="group-header"><p class="group-title">Fear & Greed Index</p></div>
                <div class="group-content" style="background:#11141a; height:250px; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid #1a1e26; border-top:none;">
                    <div style="font-size: 3rem; font-weight: bold; color: {meter_color}; margin-bottom: -10px;">{val}</div>
                    <div style="font-size: 0.8rem; color: white; letter-spacing: 2px; font-weight: bold;">{label}</div>
                    <div style="width: 80%; background: #0c0e12; height: 10px; border-radius: 5px; margin-top: 20px; border: 1px solid #1a1e26; position: relative;">
                        <div style="width: {val}%; background: {meter_color}; height: 100%; border-radius: 5px; box-shadow: 0 0 10px {meter_color}88;"></div>
                    </div>
                    <div style="width: 80%; display: flex; justify-content: space-between; color: #444; font-size: 10px; margin-top: 5px; font-weight: bold;">
                        <span>FEAR</span><span>GREED</span>
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">Module 2.2</p></div><div class="group-content" style="background:#11141a; height:250px; border:1px solid #1a1e26; border-top:none; color:#222; display:flex; align-items:center; justify-content:center; font-weight:bold;">VOID</div></div>', unsafe_allow_html=True)
    
    with c3:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">Module 2.3</p></div><div class="group-content" style="background:#11141a; height:250px; border:1px solid #1a1e26; border-top:none; color:#222; display:flex; align-items:center; justify-content:center; font-weight:bold;">VOID</div></div>', unsafe_allow_html=True)
