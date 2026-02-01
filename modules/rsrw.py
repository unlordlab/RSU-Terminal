import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

class RSRWEngine:
    def __init__(self):
        self.benchmark = "SPY"

    def get_sp500_tickers(self):
        """Obtiene la lista completa y actualizada de tickers del S&P 500 desde Wikipedia."""
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            # Usamos pandas para leer la tabla directamente de la URL
            tables = pd.read_html(url)
            df = tables[0]
            # Extraemos la columna 'Symbol' y reemplazamos los puntos por guiones (ej. BRK.B -> BRK-B)
            tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
            return tickers
        except Exception as e:
            st.error(f"Error al obtener la lista del US500: {e}")
            # Lista de respaldo (Top 10) por si falla la conexión a Wikipedia
            return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "BRK-B", "UNH", "JPM"]

    def scan_market(self, tickers, period_days=30):
        all_symbols = tickers + [self.benchmark]
        try:
            # Descargamos datos para todos los activos (esto puede tardar unos segundos)
            data = yf.download(all_symbols, period=f"{period_days+40}d", interval="1d", progress=False)
            
            if data.empty or 'Close' not in data:
                return pd.DataFrame(), 0.0

            close = data['Close']
            volume = data['Volume']

            # Cálculo de rendimientos y fuerza relativa
            returns = (close.iloc[-1] / close.iloc[-period_days]) - 1
            spy_ret = returns[self.benchmark]
            rs_scores = returns - spy_ret
            
            # Cálculo de RVOL (Volumen relativo)
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
            st.error(f"Error en el escaneo: {e}")
            return pd.DataFrame(), 0.0

def render():
    st.title("🔍 Scanner de Fuerza Relativa (US500)")
    st.markdown("---")
    
    if 'rsrw_engine' not in st.session_state:
        st.session_state.rsrw_engine = RSRWEngine()
    
    engine = st.session_state.rsrw_engine

    dias = st.slider("Días de comparación vs SPY", 5, 60, 30)

    if st.button("🔥 ESCANEAR TODO EL S&P 500"):
        with st.spinner("Descargando datos de 500 activos... esto puede tardar 10-15 segundos."):
            tickers = engine.get_sp500_tickers()
            results, spy_perf = engine.scan_market(tickers, dias)
            
            if not results.empty:
                st.metric("Rendimiento SPY (Periodo)", f"{spy_perf:.2%}")
                
                c1, c2 = st.columns(2)
                
                with c1:
                    st.markdown('<h3 style="color:#00ffad;">🚀 LÍDERES RS (Strong)</h3>', unsafe_allow_html=True)
                    # Filtramos solo los que baten al SPY (RS Score > 0)
                    df_rs = results[results['RS Score'] > 0].nlargest(20, 'RS Score')
                    st.dataframe(df_rs.style.format({
                        'RS Score': '{:+.2%}', 
                        'RVOL': '{:.2f}', 
                        'Precio': '${:.2f}'
                    }), use_container_width=True)
                
                with c2:
                    st.markdown('<h3 style="color:#d32f2f;">📉 DEBILIDAD RW (Weak)</h3>', unsafe_allow_html=True)
                    # Filtramos solo los que pierden contra el SPY (RS Score < 0)
                    df_rw = results[results['RS Score'] < 0].nsmallest(20, 'RS Score')
                    st.dataframe(df_rw.style.format({
                        'RS Score': '{:+.2%}', 
                        'RVOL': '{:.2f}', 
                        'Precio': '${:.2f}'
                    }), use_container_width=True)
            else:
                st.error("No se pudieron procesar los datos.")

    st.divider()
    # Sección de validación VWAP (se mantiene igual)
    st.subheader("🎯 Validación Técnica Intradía")
    symbol = st.text_input("Ticker para VWAP:", "NVDA").upper()
    
    if symbol:
        df_intraday = yf.download(symbol, period="1d", interval="5m", progress=False)
        if not df_intraday.empty:
            if isinstance(df_intraday.columns, pd.MultiIndex):
                df_intraday.columns = df_intraday.columns.get_level_values(0)
            
            tp = (df_intraday['High'] + df_intraday['Low'] + df_intraday['Close']) / 3
            df_intraday['VWAP'] = (tp * df_intraday['Volume']).cumsum() / df_intraday['Volume'].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_intraday.index, open=df_intraday['Open'], 
                                        high=df_intraday['High'], low=df_intraday['Low'], 
                                        close=df_intraday['Close'], name="Precio"))
            fig.add_trace(go.Scatter(x=df_intraday.index, y=df_intraday['VWAP'], 
                                    line=dict(color='#ffaa00', dash='dash'), name="VWAP"))
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
