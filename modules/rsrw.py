import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

class RSRWEngine:
    def __init__(self):
        self.benchmark = "SPY"

    @st.cache_data(ttl=3600)
    def get_sp500_tickers(_self):
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        try:
            df = pd.read_html(url)[0]
            return df['Symbol'].str.replace('.', '-', regex=False).tolist()
        except:
            return ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"] # Fallback

    def scan_market(_self, tickers, period_days=30):
        all_symbols = tickers + [_self.benchmark]
        # Descarga masiva de precios y volumen
        data = yf.download(all_symbols, period=f"{period_days+50}d", interval="1d", progress=False)
        
        close_data = data['Close']
        volume_data = data['Volume']
        
        # Rendimiento relativo
        returns = (close_data.iloc[-1] / close_data.iloc[-period_days]) - 1
        spy_ret = returns[_self.benchmark]
        rs_scores = returns - spy_ret
        
        # Volumen Relativo (RVOL)
        avg_vol = volume_data.rolling(50).mean().iloc[-1]
        current_vol = volume_data.iloc[-1]
        rvol = current_vol / avg_vol
        
        results = pd.DataFrame({
            'Precio': close_data.iloc[-1],
            'RS Score': rs_scores,
            'RVOL': rvol
        }).drop(_self.benchmark)
        
        return results, spy_ret

def render():
    st.title("🔍 Scanner de Fuerza Relativa (RS/RW)")
    st.markdown("---")
    
    # Usamos el engine guardado en session_state
    engine = st.session_state.rsrw_engine

    col_a, col_b = st.columns([1, 2])
    with col_a:
        dias = st.slider("Ventana de tiempo (días)", 5, 60, 30)
    with col_b:
        st.info("💡 **Regla Wiki:** Busca RS > 0 (Fuerte) o RS < 0 (Débil) con RVOL > 1.2.")

    if st.button("🔥 ESCANEAR S&P 500"):
        with st.spinner("Sincronizando con el mercado..."):
            tickers = engine.get_sp500_tickers()
            results, spy_perf = engine.scan_market(tickers, dias)
            
            st.metric("Rendimiento SPY", f"{spy_perf:.2%}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<h3 style="color:#00ffad;">🚀 FUERZA RELATIVA (RS)</h3>', unsafe_allow_html=True)
                top = results.nlargest(15, 'RS Score')
                st.dataframe(top.style.format({'RS Score': '{:.2%}', 'RVOL': '{:.2f}', 'Precio': '${:.2f}'}), use_container_width=True)
                
            with c2:
                st.markdown('<h3 style="color:#d32f2f;">📉 DEBILIDAD RELATIVA (RW)</h3>', unsafe_allow_html=True)
                bottom = results.nsmallest(15, 'RS Score')
                st.dataframe(bottom.style.format({'RS Score': '{:.2%}', 'RVOL': '{:.2f}', 'Precio': '${:.2f}'}), use_container_width=True)

    st.divider()
    st.subheader("🎯 Validación Técnica Intradía")
    symbol = st.text_input("Ticker para validar VWAP:", "NVDA").upper()
    
    if symbol:
        df_intraday = yf.download(symbol, period="1d", interval="5m", progress=False)
        if not df_intraday.empty:
            # Cálculo de VWAP
            vp = (df_intraday['Close'] + df_intraday['High'] + df_intraday['Low']) / 3 * df_intraday['Volume']
            df_intraday['VWAP'] = vp.cumsum() / df_intraday['Volume'].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_intraday.index, open=df_intraday['Open'], high=df_intraday['High'], 
                                         low=df_intraday['Low'], close=df_intraday['Close'], name="Precio"))
            fig.add_trace(go.Scatter(x=df_intraday.index, y=df_intraday['VWAP'], line=dict(color='#ffaa00', dash='dash'), name="VWAP"))
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, 
                              margin=dict(l=0,r=0,b=0,t=30), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

            if df_intraday['Close'].iloc[-1] > df_intraday['VWAP'].iloc[-1]:
                st.markdown('<div class="index-delta pos">✅ BULLISH: Sobre VWAP</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="index-delta neg">⚠️ BEARISH: Bajo VWAP</div>', unsafe_allow_html=True)
