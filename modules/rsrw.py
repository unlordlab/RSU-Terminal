import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

class RSRWEngine:
    def __init__(self):
        self.benchmark = "SPY"

    def get_sp500_tickers(self):
        # Lista de alta liquidez para evitar errores de conexión masiva
        return [
            "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "BRK-B", "UNH", "JNJ",
            "XOM", "JPM", "V", "PG", "MA", "AVGO", "HD", "CVX", "LLY", "ABBV", "MRK", 
            "COST", "PEP", "ADBE", "WMT", "KO", "CSCO", "TMO", "MCD", "CRM", "BAC", 
            "NFLX", "ORCL", "AMD", "ABT", "DIS", "TXN", "PM", "CAT", "INTC", "UNP", 
            "IBM", "HON", "GE", "SBUX", "DE", "LMT", "BA", "GS", "BLK", "ADI", "TJX",
            "MU", "SCHW", "LRCX", "TGT", "CL", "WM", "ETN", "MAR", "FDX", "ORLY", "PH"
        ]

    def scan_market(self, tickers, period_days=30):
        all_symbols = tickers + [self.benchmark]
        try:
            # Descarga de datos
            data = yf.download(all_symbols, period=f"{period_days+40}d", interval="1d", progress=False)
            
            if data.empty: return pd.DataFrame(), 0.0

            # Limpieza de columnas MultiIndex si existen
            close = data['Close']
            volume = data['Volume']

            # Calcular rendimientos: (Precio Hoy / Precio hace N días) - 1
            returns = (close.iloc[-1] / close.iloc[-period_days]) - 1
            spy_ret = returns[self.benchmark]
            
            # RS Score = Diferencia respecto al SPY
            rs_scores = returns - spy_ret
            
            # RVOL = Volumen actual / Media de 50 días
            rvol = volume.iloc[-1] / volume.rolling(50).mean().iloc[-1]
            
            # Construir DataFrame final
            df = pd.DataFrame({
                'Precio': close.iloc[-1],
                'RS Score': rs_scores,
                'RVOL': rvol
            }).dropna()
            
            if self.benchmark in df.index:
                df = df.drop(self.benchmark)
                
            return df, spy_ret
        except Exception as e:
            st.error(f"Error en el escáner: {e}")
            return pd.DataFrame(), 0.0

def render():
    st.title("🔍 Scanner de Fuerza Relativa (RS/RW)")
    st.markdown("---")
    
    # Usar el motor desde session_state
    if 'rsrw_engine' not in st.session_state:
        st.session_state.rsrw_engine = RSRWEngine()
    
    engine = st.session_state.rsrw_engine

    dias = st.slider("Días de análisis (Periodo de comparación)", 5, 60, 30)

    if st.button("🔥 EJECUTAR SCANNER"):
        with st.spinner("Analizando activos..."):
            tickers = engine.get_sp500_tickers()
            results, spy_perf = engine.scan_market(tickers, dias)
            
            if not results.empty:
                st.metric("Rendimiento SPY (Periodo)", f"{spy_perf:.2%}")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<h3 style="color:#00ffad;">🚀 TOP RS (Fuerte)</h3>', unsafe_allow_html=True)
                    # Filtramos solo los que tienen score positivo y ordenamos de mayor a menor
                    df_rs = results[results['RS Score'] > 0].nlargest(15, 'RS Score')
                    st.dataframe(df_rs.style.format({'RS Score': '{:.2%}', 'RVOL': '{:.2f}', 'Precio': '${:.2f}'}), use_container_width=True)
                
                with c2:
                    st.markdown('<h3 style="color:#d32f2f;">📉 TOP RW (Débil)</h3>', unsafe_allow_html=True)
                    # Filtramos solo los que tienen score negativo y ordenamos de menor a mayor
                    df_rw = results[results['RS Score'] < 0].nsmallest(15, 'RS Score')
                    st.dataframe(df_rw.style.format({'RS Score': '{:.2%}', 'RVOL': '{:.2f}', 'Precio': '${:.2f}'}), use_container_width=True)
            else:
                st.warning("No se recibieron datos del servidor de Yahoo Finance.")

    st.divider()
    st.subheader("🎯 Validación Técnica Intradía")
    symbol = st.text_input("Introduce Ticker para VWAP:", "NVDA").upper()
    
    if symbol:
        df = yf.download(symbol, period="1d", interval="5m", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # Cálculo de VWAP
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio"))
            fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], line=dict(color='#ffaa00', dash='dash'), name="VWAP"))
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig, use_container_width=True)

            try:
                curr_p = float(df['Close'].iloc[-1])
                curr_v = float(df['VWAP'].iloc[-1])
                if curr_p > curr_v:
                    st.markdown('<div style="color:#00ffad; font-weight:bold;">✅ BULLISH: Precio > VWAP</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="color:#d32f2f; font-weight:bold;">⚠️ BEARISH: Precio < VWAP</div>', unsafe_allow_html=True)
            except: pass
