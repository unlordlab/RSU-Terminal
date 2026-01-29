# modules/market.py - US500, Nasdaq, VIX, BTC LIVE
import streamlit as st
import yfinance as yf
import time

def render():
    st.subheader("📊 MERCADOS - TIEMPO REAL")
    st.caption("🕐 Actualización cada 30s")
    
    # Contenedor para refresh automático
    market_placeholder = st.empty()
    
    # Loop infinito con pausa
    while True:
        with market_placeholder.container():
            # Obtener precios LIVE (SIN CACHE)
            try:
                # S&P 500 (SPY ETF)
                spy = yf.Ticker("SPY").fast_info
                sp500_price = spy['last_price']
                sp500_change = spy['regularMarketChangePercent']
                
                # Nasdaq (QQQ ETF)  
                qqq = yf.Ticker("QQQ").fast_info
                nasdaq_price = qqq['last_price']
                nasdaq_change = qqq['regularMarketChangePercent']
                
                # VIX
                vix = yf.Ticker("^VIX").fast_info
                vix_price = vix['last_price']
                vix_change = vix['regularMarketChangePercent']
                
                # Bitcoin
                btc = yf.Ticker("BTC-USD").fast_info
                btc_price = btc['last_price']
                btc_change = btc['regularMarketChangePercent']
                
            except:
                # Fallback datos
                sp500_price, sp500_change = 5890, 1.23
                nasdaq_price, nasdaq_change = 19230, 0.89
                vix_price, vix_change = 15.2, -0.8
                btc_price, btc_change = 68250, 2.45
            
            # KPIs 2x2
            col1, col2 = st.columns(2)
            col3, col4 = st.columns(2)
            
            with col1:
                st.metric("🇺🇸 S&P 500", f"${sp500_price:,.0f}", 
                         f"{sp500_change:+.2f}%")
            with col2:
                st.metric("📈 Nasdaq", f"${nasdaq_price:,.0f}", 
                         f"{nasdaq_change:+.2f}%")
            
            with col3:
                color = "🟢" if vix_price < 20 else "🟡" if vix_price < 30 else "🔴"
                st.metric(f"{color} VIX", f"{vix_price:.1f}", 
                         f"{vix_change:+.2f}%")
            with col4:
                st.metric("₿ Bitcoin", f"${btc_price:,.0f}", 
                         f"{btc_change:+.2f}%")
            
            # Última actualización
            st.caption(f"🕐 {time.strftime('%H:%M:%S')}")
        
        time.sleep(30)  # 30 segundos
