import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

class RSRWEngine:
    def __init__(self):
        self.benchmark = "SPY"

    def get_sp500_tickers(self):
        # Lista optimizada de alta liquidez para asegurar datos rápidos y fiables
        return [
            "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "BRK-B", "UNH", "JNJ",
            "XOM", "JPM", "V", "PG", "MA", "AVGO", "HD", "CVX", "LLY", "ABBV", "MRK", 
            "COST", "PEP", "ADBE", "WMT", "KO", "CSCO", "TMO", "MCD", "CRM", "BAC", 
            "NFLX", "ORCL", "AMD", "ABT", "DIS", "TXN", "PM", "CAT", "INTC", "UNP", 
            "IBM", "HON", "GE", "SBUX", "DE", "LMT", "BA", "GS", "BLK", "ADI", "TJX",
            "MU", "SCHW", "LRCX", "TGT", "CL", "WM", "ETN", "MAR", "FDX", "ORLY", "PH",
            "PANW", "SNPS", "CDNS", "ANET", "INTU", "AMAT", "QCOM", "TXN", "AMGN", "ISRG"
        ]

    def scan_market(self, tickers, period_days=30):
        all_symbols = tickers + [self.benchmark]
        try:
            # Descarga de datos históricos (ajustada para tener margen de cálculo)
            data = yf.download(all_symbols, period=f"{period_days+40}d", interval="1d", progress=False)
            
            if data.empty or 'Close' not in data:
                return pd.DataFrame(), 0.0

            close = data['Close']
            volume = data['Volume']

            # 1. Rendimiento del activo y del Benchmark
            returns = (close.iloc[-1] / close.iloc[-period_days]) - 1
            spy_ret = returns[self.benchmark]
            
            # 2. RS Score (Diferencia porcentual pura vs SPY)
            rs_scores = returns - spy_ret
            
            # 3. RVOL (Volumen actual vs Media 50 días)
            rvol = volume.iloc[-1] / volume.rolling(50).mean().iloc[-1]
            
            # Unimos todo en un DataFrame
            df = pd.DataFrame({
                'Precio': close.iloc[-1],
                'RS Score': rs_scores,
                'RVOL': rvol
            }).dropna()
            
            if self.benchmark in df.index:
                df = df.drop(self.benchmark)
                
            return df, spy_ret
        except Exception as e:
            st.error(f"Error en el motor de cálculo: {e}")
            return pd.DataFrame(), 0.0

def render():
    st.title("🔍 Scanner de Fuerza Relativa (RS/RW)")
    st.markdown("---")
    
    # Referencia al motor en session_state (inicializado en app.py)
    if 'rsrw_engine' not in st.session_state:
        st.session_state.rsrw_engine = RSRWEngine()
    
    engine = st.session_state.rsrw_engine

    # Controles de usuario
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        dias = st.slider("Días de comparación", 5, 60, 30, help="Periodo para medir la fuerza relativa contra el SPY")
    with col_c2:
        st.info("💡 **Estrategia:** Compra activos con **RS Score > 0** y **RVOL > 1.2**. Vende activos con **RS Score < 0**.")

    if st.button("🔥 EJECUTAR ESCÁNER DE MERCADO"):
        with st.spinner("Sincronizando con la cinta de precios..."):
            tickers = engine.get_sp500_tickers()
            results, spy_perf = engine.scan_market(tickers, dias)
            
            if not results.empty:
                st.metric("Rendimiento SPY en el periodo", f"{spy_perf:.2%}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<h3 style="color:#00ffad;">🚀 TOP 15 FUERZA (RS)</h3>', unsafe_allow_html=True)
                    # FILTRO CRÍTICO: Solo los que baten al mercado (RS > 0)
                    df_rs = results[results['RS Score'] > 0].nlargest(15, 'RS Score')
                    if not df_rs.empty:
                        st.dataframe(df_rs.style.format({
                            'RS Score': '{:+.2%}', 
                            'RVOL': '{:.2f}', 
                            'Precio': '${:.2f}'
                        }).background_gradient(subset=['RVOL'], cmap='Greens', vmin=1.0, vmax=2.0), 
                        use_container_width=True)
                    else:
                        st.warning("No hay activos batiendo al SPY en este periodo.")
                
                with col2:
                    st.markdown('<h3 style="color:#d32f2f;">📉 TOP 15 DEBILIDAD (RW)</h3>', unsafe_allow_html=True)
                    # FILTRO CRÍTICO: Solo los que pierden contra el mercado (RS < 0)
                    df_rw = results[results['RS Score'] < 0].nsmallest(15, 'RS Score')
                    if not df_rw.empty:
                        st.dataframe(df_rw.style.format({
                            'RS Score': '{:+.2%}', 
                            'RVOL': '{:.2f}', 
                            'Precio': '${:.2f}'
                        }).background_gradient(subset=['RVOL'], cmap='Reds', vmin=1.0, vmax=2.0), 
                        use_container_width=True)
                    else:
                        st.warning("No hay activos con debilidad relativa clara.")
            else:
                st.error("Error al obtener datos. Reintenta en unos segundos.")

    st.divider()
    
    # --- SECCIÓN INTRADÍA VWAP ---
    st.subheader("🎯 Validación de Entrada (VWAP)")
    symbol = st.text_input("Introduce Ticker (ej: NVDA, TSLA, AAPL):", "NVDA").upper()
    
    if symbol:
        df_5m = yf.download(symbol, period="1d", interval="5m", progress=False)
        
        if not df_5m.empty:
            # Limpiar columnas por si yfinance devuelve MultiIndex
            if isinstance(df_5m.columns, pd.MultiIndex):
                df_5m.columns = df_5m.columns.get_level_values(0)
            
            # Cálculo de VWAP
            # VWAP = suma(Precio * Volumen) / suma(Volumen)
            avg_p = (df_5m['High'] + df_5m['Low'] + df_5m['Close']) / 3
            df_5m['VWAP'] = (avg_p * df_5m['Volume']).cumsum() / df_5m['Volume'].cumsum()
            
            # Gráfico interactivo
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df_5m.index, open=df_5m['Open'], high=df_5m['High'],
                low=df_5m['Low'], close=df_5m['Close'], name="Precio"
            ))
            fig.add_trace(go.Scatter(
                x=df_5m.index, y=df_5m['VWAP'], 
                line=dict(color='#ffaa00', width=2, dash='dash'), name="VWAP"
            ))
            
            fig.update_layout(
                template="plotly_dark", height=450, 
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Lógica de semáforo de entrada
            try:
                last_price = float(df_5m['Close'].iloc[-1])
                last_vwap = float(df_5m['VWAP'].iloc[-1])
                
                if last_price > last_vwap:
                    st.markdown(f'<div style="background-color:rgba(0, 255, 173, 0.1); padding:15px; border-radius:10px; border:1px solid #00ffad; color:#00ffad; font-weight:bold; text-align:center;">✅ BULLISH CONFIRMADO: El precio de {symbol} está sobre la VWAP.</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="background-color:rgba(211, 47, 47, 0.1); padding:15px; border-radius:10px; border:1px solid #d32f2f; color:#d32f2f; font-weight:bold; text-align:center;">⚠️ PRECAUCIÓN: El precio de {symbol} está bajo la VWAP. Esperar rotura.</div>', unsafe_allow_html=True)
            except Exception:
                pass
        else:
            st.warning(f"No hay datos intradía disponibles para {symbol} en este momento.")
