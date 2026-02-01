# modules/rsrw.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

class RSRWEngine:
    def __init__(self):
        self.benchmark = "SPY"

    def get_sp500_tickers(self):
        """Obtiene la lista del S&P 500 desde Wikipedia y limpia formatos."""
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            df = pd.read_html(url)[0]
            # Yahoo Finance usa '-' en lugar de '.' para acciones como BRK-B
            return df['Symbol'].str.replace('.', '-', regex=False).tolist()
        except Exception:
            return ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]

    def scan_market(self, tickers, period_days=30):
        all_symbols = tickers + [self.benchmark]
        try:
            data = yf.download(all_symbols, period=f"{period_days+50}d", interval="1d", progress=False)
            if data.empty: return pd.DataFrame(), 0.0

            close = data['Close']
            volume = data['Volume']

            # Calcular rendimientos y RS Score
            returns = (close.iloc[-1] / close.iloc[-period_days]) - 1
            spy_ret = returns[self.benchmark]
            rs_scores = returns - spy_ret
            
            # Calcular RVOL (Volumen Relativo)
            rvol = volume.iloc[-1] / volume.rolling(50).mean().iloc[-1]
            
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
    # --- DESCRIPCIÓN DE LA HERRAMIENTA ---
    st.title("🔍 Scanner de Fuerza Relativa (US500)")
    st.markdown("""
    Esta herramienta analiza los **500 activos del S&P 500** en tiempo real para identificar dónde está entrando el dinero institucional.
    * **RS (Relative Strength):** Activos que suben más (o caen menos) que el mercado (SPY).
    * **RW (Relative Weakness):** Activos que muestran debilidad frente al mercado.
    * **RVOL:** Volumen relativo. Un valor > 1.2 indica **presencia institucional**.
    """)
    st.info("🎯 **Estrategia:** Busca activos en la tabla verde con RS alto y RVOL > 1.2 para operaciones en largo.")
    
    st.markdown("---")
    
    if 'rsrw_engine' not in st.session_state:
        st.session_state.rsrw_engine = RSRWEngine()
    
    engine = st.session_state.rsrw_engine
    dias = st.slider("Ventana de tiempo (Días)", 5, 60, 30)

    if st.button("🔥 ESCANEAR TODO EL MERCADO"):
        with st.spinner("Analizando 500 tickers..."):
            tickers = engine.get_sp500_tickers()
            results, spy_perf = engine.scan_market(tickers, dias)
            
            if not results.empty:
                st.metric("Rendimiento SPY", f"{spy_perf:.2%}")
                
                c1, c2 = st.columns(2)
                
                with c1:
                    st.markdown('<h3 style="color:#00ffad;">🚀 LÍDERES RS (Strong)</h3>', unsafe_allow_html=True)
                    df_rs = results[results['RS Score'] > 0].nlargest(20, 'RS Score')
                    # APLICACIÓN DE COLORES (GRADIENTES)
                    st.dataframe(
                        df_rs.style.format({'RS Score': '{:+.2%}', 'RVOL': '{:.2f}', 'Precio': '${:.2f}'})
                        .background_gradient(subset=['RS Score'], cmap='Greens')
                        .background_gradient(subset=['RVOL'], cmap='YlGn', vmin=1.0, vmax=2.5),
                        use_container_width=True
                    )
                
                with c2:
                    st.markdown('<h3 style="color:#d32f2f;">📉 DEBILIDAD RW (Weak)</h3>', unsafe_allow_html=True)
                    df_rw = results[results['RS Score'] < 0].nsmallest(20, 'RS Score')
                    # APLICACIÓN DE COLORES (GRADIENTES)
                    st.dataframe(
                        df_rw.style.format({'RS Score': '{:+.2%}', 'RVOL': '{:.2f}', 'Precio': '${:.2f}'})
                        .background_gradient(subset=['RS Score'], cmap='Reds_r')
                        .background_gradient(subset=['RVOL'], cmap='OrRd', vmin=1.0, vmax=2.5),
                        use_container_width=True
                    )
            else:
                st.warning("No se pudieron obtener datos. Reintenta en unos segundos.")

    st.divider()
    
    # --- SECCIÓN VWAP ---
    st.subheader("🎯 Validación Intradía")
    symbol = st.text_input("Ticker para validar:", "NVDA").upper()
    
    if symbol:
        df_i = yf.download(symbol, period="1d", interval="5m", progress=False)
        if not df_i.empty:
            if isinstance(df_i.columns, pd.MultiIndex): df_i.columns = df_i.columns.get_level_values(0)
            
            # Cálculo VWAP
            tp = (df_i['High'] + df_i['Low'] + df_i['Close']) / 3
            df_i['VWAP'] = (tp * df_i['Volume']).cumsum() / df_i['Volume'].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_i.index, open=df_i['Open'], high=df_i['High'], low=df_i['Low'], close=df_i['Close'], name="Precio"))
            fig.add_trace(go.Scatter(x=df_i.index, y=df_i['VWAP'], line=dict(color='#ffaa00', dash='dash'), name="VWAP"))
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,b=0,t=30))
            st.plotly_chart(fig, use_container_width=True)

            price, vwap = df_i['Close'].iloc[-1], df_i['VWAP'].iloc[-1]
            if price > vwap:
                st.success(f"✅ {symbol} sobre VWAP: Confirmación alcista.")
            else:
                st.error(f"⚠️ {symbol} bajo VWAP: Debilidad intradía.")
