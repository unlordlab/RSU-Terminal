import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index
import requests
from bs4 import BeautifulSoup
import re

def get_overall_top_10():
    try:
        url = "https://www.buzztickr.com/reddit-buzz/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        tickers = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:11]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 1:
                    tkr = cols[1].text.strip().replace('$', '')
                    if tkr: tickers.append(tkr)
        return tickers if tickers else ["SPY", "TSLA", "NVDA", "AAPL", "AMD", "MSFT", "QQQ", "GME", "PLTR", "AMZN"]
    except:
        return ["SPY", "TSLA", "NVDA", "AAPL", "AMD", "MSFT", "QQQ", "GME", "PLTR", "AMZN"]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # --- CONFIGURACIÓN DE ALTURA UNIFICADA ---
    # Ajustamos a 400px para que quepan bien los 10 de Reddit y los índices
    MASTER_HEIGHT = "400px"

    col1, col2, col3 = st.columns(3)
    
    # 1. MARKET INDICES
    with col1:
        indices_list = [
            {"label": "S&P 500", "full": "US 500 INDEX", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "NASDAQ COMP", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "INDUSTRIAL AVG", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "SMALL CAP", "t": "^RUT"}
        ]
        indices_html = "".join([f'''
            <div style="background-color: #0c0e12; padding: 12px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; border: 1px solid #1a1e26;">
                <div><div style="font-weight: bold; color: white; font-size: 13px;">{idx['label']}</div><div style="color: #555; font-size: 10px;">{idx['full']}</div></div>
                <div style="text-align: right;"><div style="font-weight: bold; color: white;">{get_market_index(idx['t'])[0]:,.2f}</div><div style="color: {"#00ffad" if get_market_index(idx['t'])[1] >= 0 else "#f23645"}; font-size: 11px; font-weight: bold;">{get_market_index(idx['t'])[1]:+.2f}%</div></div>
            </div>''' for idx in indices_list])
        
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background-color: #11141a; padding: 15px; height: {MASTER_HEIGHT}; border-radius: 0 0 8px 8px;">{indices_html}</div></div>''', unsafe_allow_html=True)

    # 2. CALENDARIO ECONÓMICO (Versión Full Integration)
    with col2:
        # El contenedor de Streamlit
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div style="background-color: #11141a; height: {MASTER_HEIGHT}; border-radius: 0 0 8px 8px; overflow: hidden; border: 1px solid #1a1e26; border-top: none;">''', unsafe_allow_html=True)
        
        # El componente ocupa el 100% del espacio del div anterior
        components.html('''
            <style>
                body { margin: 0; padding: 0; background-color: #11141a; overflow: hidden; }
                .tradingview-widget-container { height: 100%; width: 100%; }
            </style>
            <div class="tradingview-widget-container">
                <iframe scrolling="no" allowtransparency="true" frameborder="0" 
                    src="https://www.tradingview-widget.com/embed-widget/events/?locale=en#%7B%22colorTheme%22%3A%22dark%22%2C%22isMaximized%22%3Atrue%2C%22width%22%3A%22100%25%22%2C%22height%22%3A%22100%25%22%2C%22importanceFilter%22%3A%22-1%2C0%2C1%22%2C%22currencyFilter%22%3A%22USD%2CEUR%22%7D" 
                    style="width: 100%; height: 100%;"></iframe>
            </div>
        ''', height=395) # Ligeramente menor que MASTER_HEIGHT para evitar scroll del componente
        
        st.markdown('</div></div>', unsafe_allow_html=True)

    # 3. REDDIT TOP 10 PULSE
    with col3:
        top_10 = get_overall_top_10()
        buzz_items = "".join([f'''
            <div style="background-color: #0c0e12; padding: 7px 12px; border-radius: 6px; margin-bottom: 6px; border: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #444; font-weight: bold; font-size: 10px;">{i+1:02d}</span>
                <span style="color: #00ffad; font-weight: bold; font-size: 12px; flex-grow: 1; margin-left: 10px;">{tkr}</span>
                <span style="color: #f23645; font-size: 8px; font-weight: bold; background: rgba(242,54,69,0.1); padding: 2px 6px; border-radius: 4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(top_10)])
        
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Reddit Top 10 Pulse</p></div><div class="group-content" style="background-color: #11141a; padding: 15px; height: {MASTER_HEIGHT}; border-radius: 0 0 8px 8px; overflow-y: auto;">{buzz_items}</div></div>''', unsafe_allow_html=True)

    # --- FILA 2 ---
    st.write("") 
    cols2 = st.columns(3)
    for i, c in enumerate(cols2):
        with c:
            st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Module 2.{i+1}</p></div><div class="group-content" style="background-color: #11141a; height: 280px; display: flex; align-items: center; justify-content: center; border-radius: 0 0 8px 8px; border: 1px solid #1a1e26; border-top: none;"><p style="color: #222; font-size: 0.7rem; font-weight: bold; letter-spacing: 3px;">VOID</p></div></div>''', unsafe_allow_html=True)
