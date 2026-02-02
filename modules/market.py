import streamlit as st
from config import get_market_index

def get_earnings_calendar():
    """Datos para el módulo 3.1 con fecha incluida."""
    return [
        ("AAPL", "Feb 05", "After Market", "High"),
        ("AMZN", "Feb 05", "After Market", "High"),
        ("GOOGL", "Feb 06", "Before Bell", "High"),
        ("TSLA", "Feb 07", "After Market", "High"),
    ]

def get_insider_trading():
    """Datos para el nuevo módulo 3.2 (Insider Trading)."""
    return [
        ("NVDA", "CEO", "SELL", "$12.5M"),
        ("MSFT", "CFO", "BUY", "$1.2M"),
        ("PLTR", "DIR", "BUY", "$450K"),
        ("TSLA", "DIR", "SELL", "$2.1M"),
    ]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # --- ALTURAS UNIFICADAS ---
    H_FIXED = "320px" 
    H_ROW3 = "260px"  # Un pelín más para que quepa bien la fecha

    # --- FILA 1 & 2 (Ya establecidas en el paso anterior) ---
    # ... [Mantener lógica de col1, col2, col3 de la versión anterior] ...

    # --- FILA 3 (ACTUALIZADA) ---
    st.write("")
    f3_c1, f3_c2, f3_c3 = st.columns(3)
    
    with f3_c1:
        # EARNINGS CALENDAR CON FECHA
        earnings = get_earnings_calendar()
        earn_html = "".join([f'''
            <div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; flex-direction:column;">
                    <span style="color:#00ffad; font-weight:bold; font-size:12px;">{t}</span>
                    <span style="color:#444; font-size:9px; font-weight:bold;">{date}</span>
                </div>
                <div style="text-align:right;">
                    <div style="color:#888; font-size:9px;">{time}</div>
                    <span style="color:{"#f23645" if imp=="High" else "#888"}; font-size:8px; font-weight:bold;">● {imp}</span>
                </div>
            </div>''' for t, date, time, imp in earnings])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_ROW3}; padding:12px; overflow-y:auto;">{earn_html}</div></div>', unsafe_allow_html=True)

    with f3_c2:
        # INSIDER TRADING TRACKER
        insiders = get_insider_trading()
        insider_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 12px; border-radius:6px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="color:white; font-weight:bold; font-size:11px;">{t}</span>
                    <span style="color:#555; font-size:9px; margin-left:5px;">{pos}</span>
                </div>
                <div style="text-align:right;">
                    <span style="color:{"#00ffad" if type=="BUY" else "#f23645"}; font-weight:bold; font-size:10px;">{type}</span>
                    <div style="color:#888; font-size:9px;">{amt}</div>
                </div>
            </div>''' for t, pos, type, amt in insiders])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Trading Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_ROW3}; padding:12px; overflow-y:auto;">{insider_html}</div></div>', unsafe_allow_html=True)

    with f3_c3:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Module 3.3</p></div><div class="group-content" style="background:#11141a; height:{H_ROW3}; display:flex; align-items:center; justify-content:center; color:#222; font-weight:bold;">VOID</div></div>', unsafe_allow_html=True)
