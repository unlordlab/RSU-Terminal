# modules/rsrw.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
import os

# Cache persistente para tickers S&P 500
@st.cache_data(ttl=86400)  # 24 horas
def get_sp500_tickers_cached():
    """Obtiene S&P 500 con múltiples fallbacks"""
    tickers = []
    
    # Intento 1: Wikipedia
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df = pd.read_html(url)[0]
        tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        if len(tickers) >= 490:  # Validar que tenemos ~500
            # Guardar en cache local
            try:
                with open("sp500_cache.json", "w") as f:
                    json.dump(tickers, f)
            except:
                pass
            return tickers
    except Exception as e:
        print(f"Wikipedia falló: {e}")
    
    # Intento 2: Archivo local cache
    try:
        if os.path.exists("sp500_cache.json"):
            with open("sp500_cache.json", "r") as f:
                cached = json.load(f)
                if len(cached) >= 490:
                    return cached
    except:
        pass
    
    # Fallback: Lista hardcodeada actualizada
    fallback_tickers = [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "AVGO", "WMT",
        "JPM", "V", "UNH", "MA", "HD", "PG", "LLY", "MRK", "COST", "CVX",
        "PEP", "ABBV", "KO", "BAC", "TMO", "WFC", "CSCO", "ACN", "MCD", "ABT",
        "DHR", "VZ", "DIS", "NKE", "TXN", "ADBE", "PM", "CRM", "CMCSA", "XOM",
        "INTC", "QCOM", "NEE", "AMGN", "HON", "LOW", "IBM", "UPS", "LIN", "RTX",
        "UNP", "SPGI", "CAT", "MDT", "GS", "SBUX", "BLK", "INTU", "PLD", "CVS",
        "ELV", "AMAT", "T", "ISRG", "LMT", "GILD", "ADI", "VRTX", "NOW", "SYK",
        "BKNG", "ZTS", "TJX", "C", "NFLX", "DE", "SCHW", "MDLZ", "REGN", "CI",
        "CB", "SO", "BMY", "MMC", "ADP", "BSX", "MO", "ETN", "FI", "CME",
        "ICE", "MU", "KLAC", "SHW", "EQIX", "SNPS", "CDNS", "DUK", "ITW", "EOG",
        "CL", "HCA", "WM", "GD", "FDX", "APD", "PYPL", "AON", "SLB", "ATVI",
        "CSX", "VLO", "PSX", "MPC", "OXY", "DXCM", "EW", "F", "GM", "TGT",
        "SRE", "NSC", "EXC", "AEP", "PGR", "MET", "ALL", "TRV", "AIG", "KMB",
        "STZ", "MNST", "ROP", "CTAS", "FTNT", "PANW", "ZS", "CRWD", "OKTA", "DDOG",
        "NET", "FSLY", "TWLO", "SQ", "SHOP", "SPOT", "RBLX", "UBER", "LYFT", "DASH",
        "ABNB", "ZM", "DOCU", "TEAM", "ASAN", "MDB", "SNOW", "PLTR", "U", "RBLX",
        "COIN", "HOOD", "SOFI", "LCID", "RIVN", "NIO", "XPEV", "LI", "BYDDF", "TCEHY",
        "BABA", "JD", "PDD", "NTES", "BIDU", "TME", "VIPS", "IQ", "HUYA", "DOYU",
        "FUTU", "TIGR", "LU", "YRD", "QFIN", "LX", "PPDF", "JT", "XYF", "NTP",
        "EDU", "TAL", "GOTU", "DAO", "COUR", "UDMY", "CHGG", "LRN", "STRA", "LOPE",
        "ATGE", "CECO", "UTI", "RENN", "FENG", "WBAI", "SOHU", "CYOU", "JRJC", "HGSH"
    ]
    
    return fallback_tickers

class RSRWEngine:
    def __init__(self):
        self.benchmark = "SPY"
        # Cargar tickers inmediatamente
        try:
            self.tickers = get_sp500_tickers_cached()
        except Exception as e:
            print(f"Error cargando tickers: {e}")
            self.tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]  # Fallback mínimo
    
    def get_multi_timeframe_rs(self, tickers=None, periods=[5, 20, 60]):
        """Calcula RS en múltiples timeframes para contexto"""
        if tickers is None:
            tickers = self.tickers
            
        all_symbols = list(tickers) + [self.benchmark]
        max_days = max(periods) + 10
        
        try:
            # Descargar datos
            data = yf.download(
                all_symbols, 
                period=f"{max_days}d", 
                interval="1d", 
                progress=False,
                threads=True  # Paralelizar
            )
            
            if data.empty:
                return pd.DataFrame(), 0.0
            
            # Manejar diferentes estructuras de datos
            if len(all_symbols) == 1:
                close = data['Close'].to_frame(name=self.benchmark)
                volume = data['Volume'].to_frame(name=self.benchmark) if 'Volume' in data else None
            else:
                if 'Close' in data.columns:
                    close = data['Close']
                    volume = data['Volume'] if 'Volume' in data else None
                else:
                    return pd.DataFrame(), 0.0
            
            # Verificar que tenemos datos suficientes
            if close.empty or len(close) < 5:
                return pd.DataFrame(), 0.0
            
            # Calcular RS para cada timeframe
            rs_data = {}
            for period in periods:
                if len(close) >= period:
                    try:
                        returns = (close.iloc[-1] / close.iloc[-period]) - 1
                        spy_ret = returns[self.benchmark] if self.benchmark in returns else 0
                        rs_data[f'RS_{period}d'] = returns - spy_ret
                    except:
                        continue
            
            # Si no hay datos RS, retornar vacío
            if not rs_data:
                return pd.DataFrame(), 0.0
            
            # RVOL
            rvol = pd.Series(1.0, index=close.columns)
            if volume is not None and not volume.empty:
                try:
                    vol_mean = volume.rolling(20).mean()
                    if not vol_mean.empty:
                        rvol = volume.iloc[-1] / vol_mean.iloc[-1]
                except:
                    pass
            
            # Crear DataFrame
            df = pd.DataFrame(rs_data)
            df['Precio'] = close.iloc[-1]
            df['RVOL'] = rvol
            
            # Score compuesto
            weights = {5: 0.5, 20: 0.3, 60: 0.2}
            available_periods = [p for p in periods if f'RS_{p}d' in df.columns]
            if available_periods:
                df['RS_Score'] = sum(df[f'RS_{p}d'] * weights.get(p, 0.2) for p in available_periods)
            else:
                df['RS_Score'] = 0
            
            # Eliminar benchmark
            if self.benchmark in df.index:
                df = df.drop(self.benchmark)
            
            # Filtrar solo tickers válidos
            df = df[df.index.isin(tickers)]
            df = df.dropna()
            
            # SPY performance
            spy_perf = 0
            if self.benchmark in close.columns and len(close) >= 20:
                spy_perf = (close[self.benchmark].iloc[-1] / close[self.benchmark].iloc[-20]) - 1
            
            return df, spy_perf
            
        except Exception as e:
            st.error(f"Error en cálculo: {str(e)}")
            return pd.DataFrame(), 0.0

def render():
    # CSS Estilo market.py
    st.markdown("""
    <style>
        .group-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
            margin-bottom: 20px;
        }
        .group-header {
            background: #0c0e12;
            padding: 15px 20px;
            border-bottom: 1px solid #1a1e26;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .group-title {
            margin: 0;
            color: white;
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .group-content {
            padding: 20px;
            background: #11141a;
        }
        .tooltip-container {
            position: relative;
            cursor: help;
        }
        .tooltip-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: #1a1e26;
            border: 2px solid #555;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 14px;
            font-weight: bold;
        }
        .tooltip-text {
            visibility: hidden;
            width: 300px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 12px;
            border-radius: 8px;
            position: absolute;
            z-index: 999;
            top: 35px;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            box-shadow: 0 8px 20px rgba(0,0,0,0.5);
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        .metric-card {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: white;
        }
        .metric-label {
            font-size: 0.75rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 5px;
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .badge-hot {
            background: rgba(242, 54, 69, 0.2);
            color: #f23645;
            border: 1px solid rgba(242, 54, 69, 0.4);
        }
        .badge-strong {
            background: rgba(0, 255, 173, 0.2);
            color: #00ffad;
            border: 1px solid rgba(0, 255, 173, 0.4);
        }
        .badge-neutral {
            background: rgba(255, 152, 0, 0.2);
            color: #ff9800;
            border: 1px solid rgba(255, 152, 0, 0.4);
        }
        .section-divider {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #2a3f5f, transparent);
            margin: 30px 0;
        }
        .info-box {
            background: linear-gradient(135deg, rgba(41,98,255,0.1) 0%, rgba(0,255,173,0.05) 100%);
            border: 1px solid #2a3f5f;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header Principal
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: white; font-size: 2.5rem; margin-bottom: 10px;">
            <span style="color: #00ffad;">🔍</span> Scanner RS/RW
        </h1>
        <p style="color: #888; font-size: 1.1rem; max-width: 700px; margin: 0 auto;">
            Análisis de Fuerza Relativa en el S&P 500. Identifica dónde fluye el capital institucional 
            antes del resto del mercado.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Info Educativa
    with st.expander("📚 ¿Qué es la Fuerza Relativa (RS)?", expanded=False):
        st.markdown("""
        ### Conceptos Clave
        
        **🔥 Relative Strength (RS)**  
        Mide cuánto outperforma un activo vs el benchmark (SPY).  
        - **RS > 0**: El activo sube más que el mercado  
        - **RS < 0**: El activo muestra debilidad relativa  
        
        **📊 Relative Volume (RVOL)**  
        - **RVOL > 1.5**: Interés institucional confirmado  
        - **RVOL > 2.0**: Movimiento significativo  
        
        **🎯 Estrategia**  
        1. Mercado alcista: RS > 2% + RVOL > 1.5 para largos  
        2. Mercado bajista: Buscar RS negativo para shorts
        """)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Inicializar engine con manejo de errores
    if 'rsrw_engine' not in st.session_state:
        try:
            with st.spinner("Inicializando scanner..."):
                engine = RSRWEngine()
                st.session_state.rsrw_engine = engine
                st.session_state.engine_initialized = True
        except Exception as e:
            st.error(f"Error inicializando scanner: {e}")
            st.stop()
    
    engine = st.session_state.rsrw_engine
    
    # Verificar que el engine tiene tickers
    if not hasattr(engine, 'tickers') or not engine.tickers:
        st.error("Error: No se pudieron cargar los tickers. Recargando...")
        try:
            engine = RSRWEngine()
            st.session_state.rsrw_engine = engine
        except:
            st.error("Error crítico. Por favor recarga la página.")
            st.stop()

    # Panel de Control
    st.markdown('<div style="margin-bottom: 10px; color: #00ffad; font-size: 14px; font-weight: bold;">⚙️ CONFIGURACIÓN</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        min_rvol = st.slider("RVOL Mínimo", 1.0, 3.0, 1.2, 0.1)
    with col2:
        top_n = st.slider("Top N", 10, 50, 20, 5)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_button = st.button("🔥 ESCANEAR", use_container_width=True, type="primary")

    if scan_button:
        # Verificar tickers antes de escanear
        num_tickers = len(engine.tickers) if hasattr(engine, 'tickers') else 0
        
        if num_tickers == 0:
            st.error("No hay tickers disponibles para escanear.")
            st.stop()
        
        with st.spinner(f"Analizando {num_tickers} tickers..."):
            try:
                results, spy_perf = engine.get_multi_timeframe_rs()
                
                if results.empty:
                    st.warning("No se obtuvieron resultados. Intenta de nuevo.")
                else:
                    # Dashboard de Métricas
                    st.markdown('<div style="margin: 20px 0;">', unsafe_allow_html=True)
                    metric_cols = st.columns(4)
                    
                    with metric_cols[0]:
                        color = "#00ffad" if spy_perf >= 0 else "#f23645"
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value" style="color: {color};">{spy_perf:+.1%}</div>
                            <div class="metric-label">SPY 20D</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with metric_cols[1]:
                        strong_rs = len(results[results['RS_Score'] > 0.05])
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value" style="color: #00ffad;">{strong_rs}</div>
                            <div class="metric-label">Strong RS</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with metric_cols[2]:
                        high_rvol = len(results[results['RVOL'] > 1.5])
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value" style="color: #ffaa00;">{high_rvol}</div>
                            <div class="metric-label">High RVOL</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with metric_cols[3]:
                        setups = len(results[(results['RS_Score'] > 0.03) & (results['RVOL'] > 1.2)])
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value" style="color: #2962ff;">{setups}</div>
                            <div class="metric-label">Setups</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Tablas
                    col_rs, col_rw = st.columns(2)
                    
                    with col_rs:
                        st.markdown("""
                        <div class="group-container">
                            <div class="group-header">
                                <span class="group-title">🚀 RS LEADERS</span>
                                <span class="badge badge-strong">LONG</span>
                            </div>
                            <div class="group-content">
                        """, unsafe_allow_html=True)
                        
                        df_rs = results[results['RS_Score'] > 0].nlargest(top_n, 'RS_Score')
                        df_rs = df_rs[df_rs['RVOL'] >= min_rvol]
                        
                        if not df_rs.empty:
                            st.dataframe(
                                df_rs[['RS_Score', 'RVOL', 'Precio']].style
                                .format({'RS_Score': '{:+.2%}', 'RVOL': '{:.2f}x', 'Precio': '${:.2f}'})
                                .background_gradient(subset=['RS_Score'], cmap='Greens')
                                .background_gradient(subset=['RVOL'], cmap='YlGn'),
                                use_container_width=True,
                                height=300
                            )
                        else:
                            st.info("No hay setups")
                        
                        st.markdown("</div></div>", unsafe_allow_html=True)
                    
                    with col_rw:
                        st.markdown("""
                        <div class="group-container">
                            <div class="group-header">
                                <span class="group-title">📉 RS LAGGARDS</span>
                                <span class="badge badge-hot">AVOID</span>
                            </div>
                            <div class="group-content">
                        """, unsafe_allow_html=True)
                        
                        df_rw = results[results['RS_Score'] < 0].nsmallest(top_n, 'RS_Score')
                        
                        if not df_rw.empty:
                            st.dataframe(
                                df_rw[['RS_Score', 'RVOL', 'Precio']].style
                                .format({'RS_Score': '{:+.2%}', 'RVOL': '{:.2f}x', 'Precio': '${:.2f}'})
                                .background_gradient(subset=['RS_Score'], cmap='Reds_r')
                                .background_gradient(subset=['RVOL'], cmap='OrRd'),
                                use_container_width=True,
                                height=300
                            )
                        else:
                            st.info("Mercado alcista general")
                        
                        st.markdown("</div></div>", unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"Error durante el scan: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # VWAP Section
    st.markdown('<div style="margin-bottom: 10px; color: #00ffad; font-size: 14px; font-weight: bold;">🎯 VWAP INTRADÍA</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        symbol = st.text_input("Ticker:", "NVDA").upper()
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📈 Analizar", use_container_width=True):
            try:
                df = yf.download(symbol, period="1d", interval="5m", progress=False)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    tp = (df['High'] + df['Low'] + df['Close']) / 3
                    df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df.index, open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], name=symbol
                    ))
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['VWAP'],
                        line=dict(color='#ffaa00', width=2, dash='dash'),
                        name="VWAP"
                    ))
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor='#11141a',
                        plot_bgcolor='#0c0e12',
                        height=400,
                        margin=dict(l=0, r=0, b=0, t=30)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    price = df['Close'].iloc[-1]
                    vwap = df['VWAP'].iloc[-1]
                    if price > vwap:
                        st.success(f"✅ Sobre VWAP")
                    else:
                        st.error(f"⚠️ Bajo VWAP")
                else:
                    st.warning("Sin datos")
            except Exception as e:
                st.error(f"Error: {e}")
