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
import time

# =============================================================================
# 1. SISTEMA DE DATOS ROBUSTO
# =============================================================================

@st.cache_data(ttl=3600)
def get_sp500_comprehensive():
    """Obtiene S&P 500 con múltiples estrategias de fallback."""
    
    # Estrategia 1: Wikipedia
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df = pd.read_html(url, match="Symbol")[0]
        tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        
        if len(tickers) >= 490:
            try:
                with open(".sp500_cache.json", "w") as f:
                    json.dump({"tickers": tickers, "date": datetime.now().isoformat()}, f)
            except:
                pass
            return tickers, "Wikipedia"
    except:
        pass
    
    # Estrategia 2: Cache local
    try:
        if os.path.exists(".sp500_cache.json"):
            with open(".sp500_cache.json", "r") as f:
                data = json.load(f)
                cached = data.get("tickers", [])
                if len(cached) >= 490:
                    return cached, "Cache"
    except:
        pass
    
    # Estrategia 3: Lista sectorial hardcodeada (200 tickers diversificados)
    sector_tickers = [
        # Technology (30)
        "AAPL", "MSFT", "NVDA", "AVGO", "CSCO", "ADBE", "CRM", "ACN", "ORCL", "IBM",
        "INTC", "QCOM", "TXN", "AMD", "AMAT", "ADI", "MU", "KLAC", "LRCX", "SNPS",
        "CDNS", "PANW", "CRWD", "SNOW", "PLTR", "UBER", "ABNB", "SQ", "SHOP", "NET",
        # Healthcare (25)
        "LLY", "UNH", "JNJ", "MRK", "ABBV", "PFE", "TMO", "ABT", "DHR", "BMY",
        "AMGN", "GILD", "VRTX", "REGN", "BIIB", "ZTS", "IQV", "DXCM", "EW", "ISRG",
        "BSX", "SYK", "BDX", "CI", "HUM",
        # Financials (25)
        "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK", "C",
        "AXP", "PNC", "USB", "TFC", "COF", "SCHW", "SPGI", "MCO", "ICE", "CME",
        "CB", "MMC", "PGR", "AIG", "MET",
        # Consumer (25)
        "AMZN", "TSLA", "HD", "PG", "COST", "WMT", "KO", "PEP", "MCD", "NKE",
        "DIS", "CMCSA", "LOW", "TJX", "SBUX", "BKNG", "MAR", "YUM", "DLTR", "DG",
        "TGT", "NCLH", "RCL", "CCL", "LVS",
        # Industrials (20)
        "CAT", "HON", "UNP", "UPS", "RTX", "BA", "GE", "LMT", "DE", "MMM",
        "CSX", "NSC", "FDX", "ITW", "GD", "NOC", "EMR", "ETN", "PH", "CMI",
        # Energy (15)
        "XOM", "CVX", "COP", "EOG", "SLB", "MPC", "VLO", "PSX", "OXY", "WMB",
        "KMI", "OKE", "MPLX", "EPD", "ET",
        # Materials (15)
        "LIN", "APD", "SHW", "FCX", "NEM", "DOW", "ECL", "NUE", "VMC", "PPG",
        "CF", "MOS", "FMC", "ALB", "EMN",
        # Utilities (15)
        "NEE", "SO", "DUK", "AEP", "SRE", "EXC", "XEL", "ED", "PEG", "WEC",
        "ES", "AWK", "D", "CNP", "NI",
        # Real Estate (15)
        "PLD", "AMT", "CCI", "EQIX", "PSA", "O", "WELL", "DLR", "SPG", "VICI",
        "AVB", "EQR", "EXR", "UDR", "MAA",
        # Communications (15)
        "GOOGL", "META", "NFLX", "VZ", "T", "TMUS", "CHTR", "CMCSA", "EA", "TTWO",
        "MTCH", "IAC", "FOXA", "NWSA", "IPG"
    ]
    
    # Eliminar duplicados manteniendo orden
    seen = set()
    unique = [x for x in sector_tickers if not (x in seen or seen.add(x))]
    
    if len(unique) >= 150:
        return unique, "Sectorial"
    
    # Fallback mínimo
    return ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "AVGO", "WMT",
            "JPM", "V", "UNH", "MA", "HD", "PG", "LLY", "MRK", "COST", "CVX"], "Fallback"


# =============================================================================
# 2. MOTOR DE ANÁLISIS
# =============================================================================

class RSRWEngine:
    def __init__(self):
        self.benchmark = "SPY"
        try:
            self.tickers, self.source = get_sp500_comprehensive()
        except:
            self.tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]
            self.source = "Emergency"
        
        # Limpiar duplicados inmediatamente
        self.tickers = list(dict.fromkeys(self.tickers))
        
    def download_batch(self, symbols, max_retries=3):
        """Descarga datos en lotes de 50 para evitar duplicados."""
        all_data = []
        
        # ELIMINAR DUPLICADOS antes de procesar
        symbols = list(dict.fromkeys(symbols))
        total_symbols = len(symbols)
        
        batch_size = 50  # Lotes más pequeños = menos problemas
        batches = [symbols[i:i+batch_size] for i in range(0, len(symbols), batch_size)]
        
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        for idx, batch in enumerate(batches):
            progress_text.text(f"Lote {idx+1}/{len(batches)} ({len(batch)} tickers)...")
            
            for attempt in range(max_retries):
                try:
                    if idx > 0:
                        time.sleep(0.3)
                    
                    # Añadir benchmark si no está
                    download_list = batch + [self.benchmark] if self.benchmark not in batch else batch
                    
                    data = yf.download(
                        download_list,
                        period="70d",
                        interval="1d",
                        progress=False,
                        threads=True,
                        timeout=30
                    )
                    
                    if not data.empty and 'Close' in data.columns:
                        # VERIFICAR que no haya duplicados en columnas
                        if isinstance(data.columns, pd.MultiIndex):
                            # Si es multiindex, aplanar y verificar
                            data = data.loc[:, ~data.columns.duplicated()]
                        
                        all_data.append(data)
                        break
                        
                except Exception as e:
                    if attempt == max_retries - 1:
                        st.warning(f"Lote {idx+1} falló: {str(e)[:30]}")
                    time.sleep(0.5)
            
            progress_bar.progress((idx + 1) / len(batches))
        
        progress_text.empty()
        progress_bar.empty()
        
        if not all_data:
            return None
        
        # COMBINAR con manejo de duplicados
        try:
            combined = pd.concat(all_data, axis=1)
            # Eliminar columnas duplicadas
            combined = combined.loc[:, ~combined.columns.duplicated()]
            return combined
        except Exception as e:
            st.error(f"Error combinando datos: {e}")
            return None
    
    def calculate_rs_metrics(self, data, periods=[5, 20, 60]):
        """Calcula métricas RS con manejo de duplicados."""
        
        if data is None or data.empty:
            return pd.DataFrame(), 0.0
        
        try:
            # APLANAR columnas si es multiindex
            if isinstance(data.columns, pd.MultiIndex):
                # Tomar solo el primer nivel (precios) y aplanar
                close = data['Close'].copy()
                volume = data['Volume'].copy() if 'Volume' in data else None
                
                # Si después de aplanar sigue siendo multiindex, tomer primer nivel
                if isinstance(close.columns, pd.MultiIndex):
                    close.columns = close.columns.get_level_values(0)
                if volume is not None and isinstance(volume.columns, pd.MultiIndex):
                    volume.columns = volume.columns.get_level_values(0)
            else:
                close = data['Close'] if 'Close' in data else None
                volume = data['Volume'] if 'Volume' in data else None
            
            if close is None or close.empty:
                return pd.DataFrame(), 0.0
            
            # Eliminar columnas duplicadas (tickers repetidos)
            close = close.loc[:, ~close.columns.duplicated()]
            if volume is not None:
                volume = volume.loc[:, ~volume.columns.duplicated()]
            
            # Verificar benchmark
            if self.benchmark not in close.columns:
                st.error(f"Benchmark {self.benchmark} no encontrado")
                return pd.DataFrame(), 0.0
            
            # Calcular RS para cada timeframe
            rs_data = {}
            valid_periods = []
            
            for period in periods:
                if len(close) >= period:
                    try:
                        # Retornos
                        returns = (close.iloc[-1] / close.iloc[-period]) - 1
                        
                        # Eliminar duplicados en índice si los hay
                        returns = returns[~returns.index.duplicated(keep='first')]
                        
                        spy_return = returns.get(self.benchmark, 0)
                        rs_series = returns - spy_return
                        
                        # Guardar con nombre único
                        col_name = f'RS_{period}d'
                        rs_data[col_name] = rs_series
                        valid_periods.append(period)
                    except Exception as e:
                        continue
            
            if not rs_data:
                return pd.DataFrame(), 0.0
            
            # Crear DataFrame
            df = pd.DataFrame(rs_data)
            
            # Alinear índices antes de añadir más columnas
            common_index = df.index
            
            # RVOL
            if volume is not None:
                try:
                    # Alinear volumen con el índice de RS
                    volume_aligned = volume.reindex(columns=common_index, fill_value=0)
                    avg_vol = volume_aligned.rolling(window=20, min_periods=1).mean()
                    current_vol = volume_aligned.iloc[-1]
                    rvol = current_vol / avg_vol.iloc[-1]
                    rvol = rvol.reindex(common_index, fill_value=1.0)
                    df['RVOL'] = rvol
                except:
                    df['RVOL'] = 1.0
            else:
                df['RVOL'] = 1.0
            
            # Precio
            try:
                price = close.iloc[-1].reindex(common_index)
                df['Precio'] = price
            except:
                df['Precio'] = 0
            
            # Score compuesto
            weights = {5: 0.5, 20: 0.3, 60: 0.2}
            weight_sum = sum(weights.get(p, 0.2) for p in valid_periods)
            
            if weight_sum > 0 and valid_periods:
                score_components = []
                for p in valid_periods:
                    col = f'RS_{p}d'
                    if col in df.columns:
                        score_components.append(df[col] * (weights.get(p, 0.2) / weight_sum))
                
                if score_components:
                    df['RS_Score'] = sum(score_components)
                else:
                    df['RS_Score'] = 0
            else:
                df['RS_Score'] = 0
            
            # Eliminar benchmark
            if self.benchmark in df.index:
                df = df.drop(self.benchmark)
            
            # Limpiar NaN y infinitos
            df = df.replace([float('inf'), float('-inf')], float('nan'))
            df = df.dropna()
            
            # SPY performance
            spy_perf = 0
            try:
                spy_col = close[self.benchmark]
                if len(spy_col) >= 20:
                    spy_perf = (spy_col.iloc[-1] / spy_col.iloc[-20]) - 1
            except:
                pass
            
            return df, spy_perf
            
        except Exception as e:
            st.error(f"Error en cálculo: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return pd.DataFrame(), 0.0


# =============================================================================
# 3. UI COMPLETA
# =============================================================================

def render():
    """Interfaz completa con todas las mejoras."""
    
    st.markdown("""
    <style>
        .main-header { text-align: center; margin-bottom: 30px; padding: 20px 0; }
        .main-title { color: white; font-size: 2.5rem; margin-bottom: 10px; font-weight: 700; }
        .main-subtitle { color: #888; font-size: 1.1rem; max-width: 700px; margin: 0 auto; line-height: 1.6; }
        .group-container { border: 1px solid #1a1e26; border-radius: 10px; overflow: hidden; background: #11141a; margin-bottom: 20px; }
        .group-header { background: #0c0e12; padding: 15px 20px; border-bottom: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center; }
        .group-title { margin: 0; color: white; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1.5px; }
        .group-content { padding: 20px; background: #11141a; }
        .metric-card { background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 20px 15px; text-align: center; }
        .metric-value { font-size: 2rem; font-weight: bold; color: white; margin-bottom: 5px; }
        .metric-label { font-size: 0.7rem; color: #666; text-transform: uppercase; letter-spacing: 1.5px; }
        .badge { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
        .badge-hot { background: rgba(242, 54, 69, 0.15); color: #f23645; border: 1px solid rgba(242, 54, 69, 0.3); }
        .badge-strong { background: rgba(0, 255, 173, 0.15); color: #00ffad; border: 1px solid rgba(0, 255, 173, 0.3); }
        .badge-info { background: rgba(41, 98, 255, 0.15); color: #2962ff; border: 1px solid rgba(41, 98, 255, 0.3); }
        .section-divider { border: none; height: 1px; background: linear-gradient(90deg, transparent 0%, #2a3f5f 50%, transparent 100%); margin: 40px 0; position: relative; }
        .section-divider::after { content: '◆'; position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); color: #2962ff; font-size: 8px; background: #0c0e12; padding: 0 15px; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title"><span style="color: #00ffad;">🔍</span> Scanner RS/RW Pro</h1>
        <p class="main-subtitle">
            Análisis institucional de Fuerza Relativa. Identifica flujo de capital 
            antes del movimiento mayoritario.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Inicialización
    if 'rsrw_engine' not in st.session_state:
        with st.spinner("🚀 Inicializando..."):
            engine = RSRWEngine()
            st.session_state.rsrw_engine = engine
            st.session_state.scan_count = 0
    
    engine = st.session_state.rsrw_engine
    
    # Verificar atributos
    if not hasattr(engine, 'source'):
        engine.source = "Unknown"
    if not hasattr(engine, 'tickers'):
        engine.tickers = []
    
    num_tickers = len(engine.tickers) if engine.tickers else 0
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span class="badge badge-info">📊 {num_tickers} tickers | {engine.source}</span>
    </div>
    """, unsafe_allow_html=True)

    # Guía educativa
    with st.expander("📚 Guía Completa: Cómo usar el Scanner", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            ### 🎯 Conceptos Fundamentales
            
            **Fuerza Relativa (RS)**  
            Mide el exceso de retorno vs SPY.
            - **RS = +5%**: Subió 5% más que el mercado
            - **RS = -3%**: Subió 3% menos (o cayó más)
            
            **Relative Volume (RVOL)**  
            Volumen hoy / Promedio 20 días.
            - **1.5-2.0**: Interés institucional
            - **>2.5**: Evento/catalizador probable
            """)
        with col2:
            st.markdown("""
            ### 📊 Multi-Timeframe
            
            | Timeframe | Peso | Qué mide |
            |-----------|------|----------|
            | **5 días** | 50% | Momentum inmediato |
            | **20 días** | 30% | Tendencia mensual |
            | **60 días** | 20% | Tendencia trimestral |
            
            **Setup ideal**: RS positivo en 3 timeframes + RVOL >1.5
            """)

    # Panel de control
    st.markdown('<div style="margin-bottom: 15px; color: #00ffad; font-size: 14px; font-weight: bold;">⚙️ Configuración</div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    with c1:
        min_rvol = st.slider("RVOL Mínimo", 1.0, 3.0, 1.2, 0.1)
    with c2:
        rs_threshold = st.slider("Umbral RS %", 1, 10, 3, 1) / 100.0
    with c3:
        top_n = st.slider("Top N", 10, 50, 20, 5)
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_btn = st.button("🔥 ESCANEAR", use_container_width=True, type="primary")

    # Ejecución del scan
    if scan_btn:
        if num_tickers == 0:
            st.error("❌ No hay tickers disponibles.")
            st.stop()
        
        with st.spinner(f"Analizando {num_tickers} tickers..."):
            raw_data = engine.download_batch(engine.tickers)
            
            if raw_data is None:
                st.error("❌ No se pudieron descargar datos.")
                st.stop()
            
            results, spy_perf = engine.calculate_rs_metrics(raw_data)
            
            if results.empty:
                st.warning("⚠️ No se obtuvieron resultados.")
            else:
                st.session_state.last_results = results
                
                # Métricas
                st.markdown('<div style="margin: 25px 0;">', unsafe_allow_html=True)
                mc = st.columns(4)
                
                with mc[0]:
                    color = "#00ffad" if spy_perf >= 0 else "#f23645"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: {color};">{spy_perf:+.2%}</div>
                        <div class="metric-label">SPY 20D</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with mc[1]:
                    strong = len(results[results['RS_Score'] > rs_threshold])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #00ffad;">{strong}</div>
                        <div class="metric-label">Strong RS</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with mc[2]:
                    high_rvol = len(results[results['RVOL'] > 1.5])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #ffaa00;">{high_rvol}</div>
                        <div class="metric-label">High RVOL</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with mc[3]:
                    setups = len(results[(results['RS_Score'] > rs_threshold) & (results['RVOL'] > min_rvol)])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #2962ff;">{setups}</div>
                        <div class="metric-label">Setups</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

                # Gráfico de dispersión
                fig = px.scatter(
                    results.reset_index().rename(columns={'index': 'Ticker'}),
                    x='RS_Score',
                    y='RVOL',
                    color='RS_Score',
                    color_continuous_scale=['#f23645', '#ff9800', '#00ffad'],
                    size='RVOL',
                    size_max=25,
                    hover_name='Ticker',
                    hover_data={'RS_Score': ':.2%', 'RVOL': ':.2f', 'Precio': ':$.2f'},
                    labels={'RS_Score': 'Fuerza Relativa', 'RVOL': 'Relative Volume'}
                )
                fig.add_hline(y=1.5, line_dash="dash", line_color="#ffaa00", opacity=0.6)
                fig.add_vline(x=0, line_dash="solid", line_color="white", opacity=0.3)
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor='#11141a',
                    plot_bgcolor='#0c0e12',
                    font_color='white',
                    height=450,
                    margin=dict(l=0, r=0, b=0, t=40)
                )
                st.plotly_chart(fig, use_container_width=True)

                # Tablas
                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                rc1, rc2 = st.columns(2)
                
                with rc1:
                    st.markdown("""
                    <div class="group-container">
                        <div class="group-header">
                            <span class="group-title">🚀 RS LEADERS</span>
                            <span class="badge badge-strong">LONG</span>
                        </div>
                        <div class="group-content">
                    """, unsafe_allow_html=True)
                    
                    df_rs = results[results['RS_Score'] > rs_threshold].nlargest(top_n, 'RS_Score')
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
                        st.info("No hay resultados")
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                with rc2:
                    st.markdown("""
                    <div class="group-container">
                        <div class="group-header">
                            <span class="group-title">📉 RS LAGGARDS</span>
                            <span class="badge badge-hot">AVOID</span>
                        </div>
                        <div class="group-content">
                    """, unsafe_allow_html=True)
                    
                    df_rw = results[results['RS_Score'] < -0.01].nsmallest(top_n, 'RS_Score')
                    
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
                        st.success("Mercado alcista general")
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                # Exportar
                if 'last_results' in st.session_state:
                    csv = st.session_state.last_results.to_csv().encode('utf-8')
                    st.download_button("📥 Exportar CSV", csv, 
                                     f"RS_Scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                     "text/csv")

    # VWAP
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<div style="margin-bottom: 15px; color: #00ffad; font-size: 14px; font-weight: bold;">🎯 Validación VWAP</div>', unsafe_allow_html=True)
    
    vc1, vc2 = st.columns([3, 1])
    with vc1:
        symbol = st.text_input("Ticker:", "NVDA").upper()
    with vc2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📈 Analizar", use_container_width=True):
            try:
                df = yf.download(symbol, period="1d", interval="5m", progress=False)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    tp = (df['High'] + df['Low'] + df['Close']) / 3
                    df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
                    
                    price = df['Close'].iloc[-1]
                    vwap = df['VWAP'].iloc[-1]
                    dev = ((price - vwap) / vwap) * 100
                    
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df.index, open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], name=symbol
                    ))
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['VWAP'],
                        line=dict(color='#ffaa00', width=2),
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
                    
                    if dev > 1:
                        st.success(f"✅ Sobre VWAP (+{dev:.1f}%)")
                    elif dev < -1:
                        st.error(f"🔻 Bajo VWAP ({dev:.1f}%)")
                    else:
                        st.info(f"➡️ Equilibrio ({dev:+.1f}%)")
                else:
                    st.warning("Sin datos")
            except Exception as e:
                st.error(f"Error: {e}")
