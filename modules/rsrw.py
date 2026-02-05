# modules/rsrw.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import time
import traceback

# =============================================================================
# CONSTANTES GLOBALES
# =============================================================================

SECTOR_ETFS = {
    "Tecnología": "XLK",
    "Salud": "XLV",
    "Financieros": "XLF",
    "Consumo Discrecional": "XLY",
    "Consumo Básico": "XLP",
    "Industriales": "XLI",
    "Energía": "XLE",
    "Materiales": "XLB",
    "Servicios Públicos": "XLU",
    "Bienes Raíces": "XLRE",
    "Comunicaciones": "XLC"
}

SECTOR_TICKERS = {
    "Tecnología": [
        "AAPL", "MSFT", "NVDA", "AVGO", "CSCO", "ADBE", "CRM", "ACN", "ORCL", "IBM",
        "INTC", "QCOM", "TXN", "AMD", "AMAT", "ADI", "MU", "KLAC", "LRCX", "SNPS",
        "CDNS", "PANW", "CRWD", "SNOW", "PLTR", "UBER", "ABNB", "SQ", "SHOP", "NET"
    ],
    "Salud": [
        "LLY", "UNH", "JNJ", "MRK", "ABBV", "PFE", "TMO", "ABT", "DHR", "BMY",
        "AMGN", "GILD", "VRTX", "REGN", "BIIB", "ZTS", "IQV", "DXCM", "EW", "ISRG",
        "BSX", "SYK", "BDX", "CI", "HUM"
    ],
    "Financieros": [
        "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK", "C",
        "AXP", "PNC", "USB", "TFC", "COF", "SCHW", "SPGI", "MCO", "ICE", "CME",
        "CB", "MMC", "PGR", "AIG", "MET"
    ],
    "Consumo Discrecional": [
        "AMZN", "TSLA", "HD", "PG", "COST", "WMT", "KO", "PEP", "MCD", "NKE",
        "DIS", "CMCSA", "LOW", "TJX", "SBUX", "BKNG", "MAR", "YUM", "DLTR", "DG",
        "TGT", "NCLH", "RCL", "CCL", "LVS"
    ],
    "Consumo Básico": [
        "PG", "KO", "PEP", "WMT", "COST", "PM", "MO", "MDLZ", "KHC", "GIS",
        "K", "HSY", "MKC", "CPB", "CAG", "SJM", "LW", "HRL", "TSN", "BG"
    ],
    "Industriales": [
        "CAT", "HON", "UNP", "UPS", "RTX", "BA", "GE", "LMT", "DE", "MMM",
        "CSX", "NSC", "FDX", "ITW", "GD", "NOC", "EMR", "ETN", "PH", "CMI"
    ],
    "Energía": [
        "XOM", "CVX", "COP", "EOG", "SLB", "MPC", "VLO", "PSX", "OXY", "WMB",
        "KMI", "OKE", "MPLX", "EPD", "ET", "ENB", "TRP", "SU", "IMO", "CVE"
    ],
    "Materiales": [
        "LIN", "APD", "SHW", "FCX", "NEM", "DOW", "ECL", "NUE", "VMC", "PPG",
        "CF", "MOS", "FMC", "ALB", "EMN", "LYB", "PKG", "AVY", "IP", "BLL"
    ],
    "Servicios Públicos": [
        "NEE", "SO", "DUK", "AEP", "SRE", "EXC", "XEL", "ED", "PEG", "WEC",
        "ES", "AWK", "D", "CNP", "NI", "FE", "AEE", "CMS", "LNT", "ETR"
    ],
    "Bienes Raíces": [
        "PLD", "AMT", "CCI", "EQIX", "PSA", "O", "WELL", "DLR", "SPG", "VICI",
        "AVB", "EQR", "EXR", "UDR", "MAA", "BXP", "ARE", "HST", "VTR", "PEAK"
    ],
    "Comunicaciones": [
        "GOOGL", "META", "NFLX", "VZ", "T", "TMUS", "CHTR", "CMCSA", "EA", "TTWO",
        "MTCH", "IAC", "FOXA", "NWSA", "IPG", "OMC", "LYV", "TTWO", "NFLX", "DIS",
        "WBD", "PARA", "NWSA", "FOXA", "GOOG"
    ]
}


# =============================================================================
# FUNCIONES DE DATOS
# =============================================================================

def get_sp500_comprehensive():
    """Obtiene S&P 500 con clasificación por sectores."""
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
    except Exception as e:
        st.warning(f"Wikipedia error: {e}")
    
    try:
        if os.path.exists(".sp500_cache.json"):
            with open(".sp500_cache.json", "r") as f:
                data = json.load(f)
                cached = data.get("tickers", [])
                if len(cached) >= 490:
                    return cached, "Cache"
    except Exception as e:
        st.warning(f"Cache error: {e}")
    
    # Fallback: usar tickers predefinidos
    all_tickers = []
    for sector, ticks in SECTOR_TICKERS.items():
        all_tickers.extend(ticks)
    seen = set()
    unique = [x for x in all_tickers if not (x in seen or seen.add(x))]
    return unique, "Sectorial"


def get_sector_for_ticker(ticker):
    """Determina el sector de un ticker."""
    for sector, tickers in SECTOR_TICKERS.items():
        if ticker in tickers:
            return sector
    return "Otros"


# =============================================================================
# MOTOR DE ANÁLISIS
# =============================================================================

class RSRWEngine:
    def __init__(self):
        self.benchmark = "SPY"
        self.sector_etfs = SECTOR_ETFS
        self.tickers = []
        self.source = "Unknown"
        
        try:
            self.tickers, self.source = get_sp500_comprehensive()
        except Exception as e:
            st.error(f"Error cargando tickers: {e}")
            self.tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "BRK-B", "UNH", "JNJ"]
            self.source = "Emergency"
        
        if self.tickers:
            self.tickers = list(dict.fromkeys(self.tickers))
        else:
            self.tickers = ["AAPL", "MSFT", "NVDA"]
    
    def download_batch(self, symbols, max_retries=3):
        """Descarga datos en lotes."""
        if not symbols:
            st.error("No hay símbolos para descargar")
            return None
        
        all_data = []
        symbols = list(dict.fromkeys(symbols))
        download_symbols = symbols + list(self.sector_etfs.values())
        batch_size = 50
        batches = [download_symbols[i:i+batch_size] for i in range(0, len(download_symbols), batch_size)]
        
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        for idx, batch in enumerate(batches):
            progress_text.text(f"Descargando lote {idx+1}/{len(batches)} ({len(batch)} símbolos)...")
            for attempt in range(max_retries):
                try:
                    if idx > 0:
                        time.sleep(0.3)
                    data = yf.download(
                        batch,
                        period="70d",
                        interval="1d",
                        progress=False,
                        threads=True,
                        timeout=30
                    )
                    if not data.empty:
                        all_data.append(data)
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        st.warning(f"Error en lote {idx+1}: {e}")
                    time.sleep(0.5)
            progress_bar.progress((idx + 1) / len(batches))
        
        progress_text.empty()
        progress_bar.empty()
        
        if not all_data:
            return None
        
        try:
            combined = pd.concat(all_data, axis=1)
            return combined
        except Exception as e:
            st.error(f"Error combinando datos: {e}")
            return None
    
    def calculate_rs_metrics(self, data, periods=[5, 20, 60]):
        """Calcula métricas RS con análisis sectorial."""
        if data is None or data.empty:
            st.error("Datos vacíos")
            return pd.DataFrame(), pd.DataFrame(), 0.0
        
        try:
            if isinstance(data.columns, pd.MultiIndex):
                close = data.xs('Close', level=0, axis=1) if 'Close' in data.columns.get_level_values(0) else None
                volume = data.xs('Volume', level=0, axis=1) if 'Volume' in data.columns.get_level_values(0) else None
            else:
                close = data['Close'] if 'Close' in data.columns else None
                volume = data['Volume'] if 'Volume' in data.columns else None
            
            if close is None or close.empty:
                st.error("No se encontraron datos de cierre")
                return pd.DataFrame(), pd.DataFrame(), 0.0
            
            if isinstance(close, pd.Series):
                close = close.to_frame()
            
            close = close.loc[:, ~close.columns.duplicated()]
            
            # Calcular RS sectorial
            sector_rs = {}
            for sector, etf in self.sector_etfs.items():
                if etf in close.columns and self.benchmark in close.columns:
                    try:
                        sector_ret = (close[etf].iloc[-1] / close[etf].iloc[-20]) - 1
                        spy_ret = (close[self.benchmark].iloc[-1] / close[self.benchmark].iloc[-20]) - 1
                        sector_rs[sector] = {
                            'RS': sector_ret - spy_ret,
                            'Return': sector_ret,
                            'ETF': etf
                        }
                    except:
                        pass
            
            sector_df = pd.DataFrame(sector_rs).T if sector_rs else pd.DataFrame()
            
            if self.benchmark not in close.columns:
                st.error(f"Benchmark {self.benchmark} no encontrado")
                return pd.DataFrame(), sector_df, 0.0
            
            # Calcular métricas RS
            rs_data = {}
            valid_periods = []
            for period in periods:
                if len(close) >= period:
                    try:
                        returns = (close.iloc[-1] / close.iloc[-period]) - 1
                        spy_return = returns.get(self.benchmark, 0)
                        rs_series = returns - spy_return
                        rs_data[f'RS_{period}d'] = rs_series
                        valid_periods.append(period)
                    except:
                        continue
            
            if not rs_data:
                st.error("No se calcularon métricas RS")
                return pd.DataFrame(), sector_df, 0.0
            
            df = pd.DataFrame(rs_data)
            common_index = df.index
            
            df['Sector'] = [get_sector_for_ticker(t) for t in common_index]
            df['RS_vs_Sector'] = 0.0
            
            for ticker in common_index:
                sector = df.loc[ticker, 'Sector']
                if sector in sector_rs:
                    ticker_rs = df.loc[ticker, 'RS_20d'] if 'RS_20d' in df.columns else 0
                    sector_val = sector_rs[sector]['RS']
                    df.loc[ticker, 'RS_vs_Sector'] = ticker_rs - sector_val
            
            # Calcular RVOL
            df['RVOL'] = 1.0
            if volume is not None:
                try:
                    if isinstance(volume, pd.Series):
                        volume = volume.to_frame()
                    volume = volume.loc[:, ~volume.columns.duplicated()]
                    vol_aligned = volume.reindex(columns=common_index, fill_value=0)
                    if not vol_aligned.empty:
                        avg_vol = vol_aligned.rolling(window=20, min_periods=1).mean()
                        current_vol = vol_aligned.iloc[-1]
                        rvol = current_vol / avg_vol.iloc[-1]
                        df['RVOL'] = rvol.reindex(common_index, fill_value=1.0)
                except Exception as e:
                    st.warning(f"Error RVOL: {e}")
            
            try:
                df['Precio'] = close.iloc[-1].reindex(common_index)
            except:
                df['Precio'] = 0
            
            # Calcular Score compuesto
            weights = {5: 0.5, 20: 0.3, 60: 0.2}
            weight_sum = sum(weights.get(p, 0.2) for p in valid_periods)
            
            if weight_sum > 0 and valid_periods:
                score_components = []
                for p in valid_periods:
                    col = f'RS_{p}d'
                    if col in df.columns:
                        score_components.append(df[col] * (weights.get(p, 0.2) / weight_sum))
                df['RS_Score'] = sum(score_components) if score_components else 0
            else:
                df['RS_Score'] = 0
            
            # Filtrar benchmarks y ETFs
            to_drop = [self.benchmark] + list(self.sector_etfs.values())
            df = df[~df.index.isin(to_drop)]
            
            # Limpiar datos
            df = df.replace([float('inf'), float('-inf')], float('nan'))
            df = df.dropna()
            
            # Calcular rendimiento SPY
            spy_perf = 0
            try:
                spy_col = close[self.benchmark]
                if len(spy_col) >= 20:
                    spy_perf = (spy_col.iloc[-1] / spy_col.iloc[-20]) - 1
            except:
                pass
            
            return df, sector_df, spy_perf
        
        except Exception as e:
            st.error(f"Error en cálculo RS: {str(e)}")
            st.code(traceback.format_exc())
            return pd.DataFrame(), pd.DataFrame(), 0.0


# =============================================================================
# UI COMPLETA
# =============================================================================

def render():
    """Interfaz completa con explicaciones exhaustivas."""
    
    # CSS
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
        .metric-value { font-size: 1.8rem; font-weight: bold; color: white; margin-bottom: 5px; }
        .metric-label { font-size: 0.7rem; color: #666; text-transform: uppercase; letter-spacing: 1.5px; }
        .badge { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
        .badge-hot { background: rgba(242, 54, 69, 0.15); color: #f23645; border: 1px solid rgba(242, 54, 69, 0.3); }
        .badge-strong { background: rgba(0, 255, 173, 0.15); color: #00ffad; border: 1px solid rgba(0, 255, 173, 0.3); }
        .badge-info { background: rgba(41, 98, 255, 0.15); color: #2962ff; border: 1px solid rgba(41, 98, 255, 0.3); }
        .section-divider { border: none; height: 1px; background: linear-gradient(90deg, transparent 0%, #2a3f5f 50%, transparent 100%); margin: 40px 0; position: relative; }
        .section-divider::after { content: '◆'; position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); color: #2962ff; font-size: 8px; background: #0c0e12; padding: 0 15px; }
        .help-box { background: linear-gradient(135deg, rgba(41,98,255,0.1) 0%, rgba(0,255,173,0.05) 100%); border-left: 3px solid #00ffad; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; }
        .help-title { color: #00ffad; font-weight: bold; font-size: 13px; margin-bottom: 5px; }
        .help-text { color: #aaa; font-size: 12px; line-height: 1.5; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title"><span style="color: #00ffad;">🔍</span> Scanner RS/RW Pro</h1>
        <p class="main-subtitle">
            Análisis institucional de Fuerza Relativa con contexto sectorial. 
            Identifica flujo de capital y rotación entre sectores.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ========== INICIALIZACIÓN SEGURA ==========
    engine = None
    
    # Intentar obtener o crear el motor
    try:
        if 'rsrw_engine' not in st.session_state:
            with st.spinner("🚀 Inicializando motor..."):
                new_engine = RSRWEngine()
                st.session_state.rsrw_engine = new_engine
        
        engine = st.session_state.rsrw_engine
        
    except Exception as e:
        st.error(f"❌ Error al inicializar: {e}")
        st.code(traceback.format_exc())
        # Crear motor de emergencia
        engine = RSRWEngine()
        st.session_state.rsrw_engine = engine
    
    # Verificar que el motor es válido
    if engine is None:
        st.error("❌ Error crítico: No se pudo crear el motor")
        st.stop()
    
    # Verificar atributos con valores por defecto
    if not hasattr(engine, 'tickers') or engine.tickers is None:
        engine.tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]
    
    if not hasattr(engine, 'source'):
        engine.source = "Default"
    
    if not hasattr(engine, 'sector_etfs'):
        engine.sector_etfs = SECTOR_ETFS
    
    num_tickers = len(engine.tickers) if engine.tickers else 0
    num_sectors = len(engine.sector_etfs) if engine.sector_etfs else 0
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span class="badge badge-info">📊 {num_tickers} tickers | {num_sectors} sectores | {engine.source}</span>
    </div>
    """, unsafe_allow_html=True)

    # ========== GUÍA EDUCATIVA ==========
    with st.expander("📚 Guía Completa: Dominando el Análisis RS/RW", expanded=False):
        tab1, tab2, tab3 = st.tabs(["🎯 Conceptos", "📊 Estrategias", "⚠️ Riesgos"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                ### ¿Qué es la Fuerza Relativa (RS)?
                
                La Fuerza Relativa **NO es el RSI**. Es una medida de cuánto un activo 
                está superando (o subperformando) al benchmark del mercado (S&P 500).
                
                **Fórmula:**
                ```
                RS = Retorno del Stock - Retorno del SPY
                ```
                
                **Interpretación:**
                - **RS = +5%**: El stock subió 5% más que el mercado
                - **RS = -3%**: El stock subió 3% menos que el mercado
                """)
            with col2:
                st.markdown("""
                ### Relative Volume (RVOL)
                
                El RVOL mide si el volumen actual es anormal comparado con el promedio.
                
                **Umbrales clave:**
                - **1.0 - 1.3**: Volumen normal
                - **1.5 - 2.0**: 🔥 **Interés institucional**
                - **>3.0**: ⚠️ **Parabolic move**
                """)
        
        with tab2:
            st.markdown("""
            ### Estrategia de Trading con RS/RW
            
            **SETUP LARGO:**
            1. SPY > 20EMA (tendencia alcista)
            2. RS_Score > 3% + RVOL > 1.5
            3. Sector con RS positivo
            4. Entrada en pullback al VWAP
            """)
        
        with tab3:
            st.markdown("""
            ### ⚠️ Falsos Positivos
            
            1. **RS alto sin volumen** → Evitar
            2. **Solo RS 5d positivo** → Rebote técnico
            3. **Stock fuerte en sector débil** → No es fuerza real
            """)

    # ========== CONFIGURACIÓN ==========
    st.markdown('<div style="margin-bottom: 15px; color: #00ffad; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px;">⚙️ Configuración del Scanner</div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    
    with c1:
        st.markdown("""
        <div class="help-box">
            <div class="help-title">📊 RVOL Mínimo</div>
            <div class="help-text">Filtra stocks sin interés institucional. <strong>1.5</strong> = 50% más volumen.</div>
        </div>
        """, unsafe_allow_html=True)
        min_rvol = st.slider("RVOL", 1.0, 3.0, 1.2, 0.1, label_visibility="collapsed")
    
    with c2:
        st.markdown("""
        <div class="help-box">
            <div class="help-title">🎯 Umbral RS (%)</div>
            <div class="help-text">Mínimo de outperformance vs SPY. <strong>3%</strong> recomendado.</div>
        </div>
        """, unsafe_allow_html=True)
        rs_threshold = st.slider("RS %", 1, 10, 3, 1, label_visibility="collapsed") / 100.0
    
    with c3:
        st.markdown("""
        <div class="help-box">
            <div class="help-title">📈 Top N Resultados</div>
            <div class="help-text">Número de stocks a mostrar. <strong>20</strong> recomendado.</div>
        </div>
        """, unsafe_allow_html=True)
        top_n = st.slider("Top N", 10, 50, 20, 5, label_visibility="collapsed")
    
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_btn = st.button("🔥 ESCANEAR", use_container_width=True, type="primary")

    # ========== EJECUCIÓN DEL SCAN ==========
    if scan_btn:
        if num_tickers == 0:
            st.error("❌ No hay tickers disponibles.")
            st.stop()
        
        with st.spinner(f"Analizando {num_tickers} tickers..."):
            try:
                raw_data = engine.download_batch(engine.tickers)
                
                if raw_data is None:
                    st.error("❌ No se pudieron descargar datos.")
                    st.stop()
                
                results, sector_data, spy_perf = engine.calculate_rs_metrics(raw_data)
                
                if results.empty:
                    st.warning("⚠️ No se obtuvieron resultados.")
                else:
                    st.session_state.last_results = results
                    st.session_state.last_sector_data = sector_data
                    
                    # Métricas
                    st.markdown('<div style="margin: 25px 0;">', unsafe_allow_html=True)
                    mc = st.columns(5)
                    
                    with mc[0]:
                        color = "#00ffad" if spy_perf >= 0 else "#f23645"
                        icon = "▲" if spy_perf >= 0 else "▼"
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value" style="color: {color};">{spy_perf:+.2%}</div>
                            <div class="metric-label">SPY 20D</div>
                            <div style="color: {color}; font-size: 11px; margin-top: 5px;">{icon} Tendencia</div>
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
                            <div class="metric-label">Setups Activos</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with mc[4]:
                        if not sector_data.empty and 'RS' in sector_data.columns:
                            top_sector = sector_data['RS'].idxmax()
                            top_sector_rs = sector_data.loc[top_sector, 'RS']
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-value" style="color: #00ffad; font-size: 1.4rem;">{top_sector}</div>
                                <div class="metric-label">Sector Líder</div>
                                <div style="color: #00ffad; font-size: 11px; margin-top: 5px;">{top_sector_rs:+.2%}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""<div class="metric-card"><div class="metric-value">-</div><div class="metric-label">Sector Líder</div></div>""", unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Gráfico de sectores
                    if not sector_data.empty:
                        st.markdown('<div style="margin-bottom: 15px; color: #00ffad; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px;">🔄 Rotación Sectorial</div>', unsafe_allow_html=True)
                        
                        sector_fig = go.Figure()
                        colors = ['#00ffad' if x > 0 else '#f23645' for x in sector_data['RS']]
                        
                        sector_fig.add_trace(go.Bar(
                            x=sector_data.index,
                            y=sector_data['RS'],
                            marker_color=colors,
                            text=[f"{x:+.2%}" for x in sector_data['RS']],
                            textposition='outside',
                            textfont=dict(size=10, color='white')
                        ))
                        
                        sector_fig.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.3)
                        
                        sector_fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor='#11141a',
                            plot_bgcolor='#0c0e12',
                            font_color='white',
                            height=300,
                            margin=dict(l=0, r=0, b=50, t=30),
                            title=dict(text="Fuerza Relativa de Sectores vs S&P 500 (20 días)", font_size=12, font_color='#888'),
                            xaxis_tickangle=-45,
                            yaxis=dict(title="RS vs SPY", tickformat='.1%'),
                            showlegend=False
                        )
                        
                        st.plotly_chart(sector_fig, use_container_width=True)

                    # Tablas de resultados
                    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                    st.markdown('<div style="margin-bottom: 15px; color: #00ffad; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px;">🎯 Resultados Detallados</div>', unsafe_allow_html=True)
                    
                    rc1, rc2 = st.columns(2)
                    
                    with rc1:
                        st.markdown("""
                        <div class="group-container">
                            <div class="group-header">
                                <span class="group-title">🚀 LÍDERES RS</span>
                                <span class="badge badge-strong">LONG CANDIDATES</span>
                            </div>
                            <div class="group-content">
                        """, unsafe_allow_html=True)
                        
                        df_rs = results[results['RS_Score'] > rs_threshold].nlargest(top_n, 'RS_Score')
                        df_rs = df_rs[df_rs['RVOL'] >= min_rvol]
                        
                        if not df_rs.empty:
                            df_rs['Setup'] = df_rs.apply(
                                lambda x: '🔥 HOT' if x['RVOL'] > 2.0 and x['RS_Score'] > 0.05 and x['RS_vs_Sector'] > 0
                                else ('✅ Strong' if x['RS_vs_Sector'] > 0 else '⚠️ Sector Weak'),
                                axis=1
                            )
                            
                            display_cols = ['RS_Score', 'RVOL', 'RS_vs_Sector', 'Sector', 'Setup']
                            st.dataframe(
                                df_rs[display_cols].style
                                .format({'RS_Score': '{:+.2%}', 'RVOL': '{:.2f}x', 'RS_vs_Sector': '{:+.2%}'})
                                .background_gradient(subset=['RS_Score'], cmap='Greens')
                                .background_gradient(subset=['RVOL'], cmap='YlGn'),
                                use_container_width=True,
                                height=350
                            )
                        else:
                            st.info("No hay líderes RS con los filtros actuales.")
                        
                        st.markdown("</div></div>", unsafe_allow_html=True)
                    
                    with rc2:
                        st.markdown("""
                        <div class="group-container">
                            <div class="group-header">
                                <span class="group-title">📉 LAGGARDS</span>
                                <span class="badge badge-hot">AVOID / SHORT</span>
                            </div>
                            <div class="group-content">
                        """, unsafe_allow_html=True)
                        
                        df_rw = results[results['RS_Score'] < -0.01].nsmallest(top_n, 'RS_Score')
                        
                        if not df_rw.empty:
                            display_cols = ['RS_Score', 'RVOL', 'RS_vs_Sector', 'Sector']
                            st.dataframe(
                                df_rw[display_cols].style
                                .format({'RS_Score': '{:+.2%}', 'RVOL': '{:.2f}x', 'RS_vs_Sector': '{:+.2%}'})
                                .background_gradient(subset=['RS_Score'], cmap='Reds_r'),
                                use_container_width=True,
                                height=350
                            )
                        else:
                            st.success("✅ No hay debilidad significativa.")
                        
                        st.markdown("</div></div>", unsafe_allow_html=True)
                    
                    # Exportar
                    if 'last_results' in st.session_state:
                        csv = st.session_state.last_results.to_csv().encode('utf-8')
                        st.download_button("📥 Exportar CSV", csv, f"RS_Scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv")
            
            except Exception as e:
                st.error(f"Error en el análisis: {e}")
                st.code(traceback.format_exc())

    # ========== VWAP ==========
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<div style="margin-bottom: 15px; color: #00ffad; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px;">🎯 Validación Intradía con VWAP</div>', unsafe_allow_html=True)
    
    vc1, vc2 = st.columns([3, 1])
    with vc1:
        symbol = st.text_input("Ticker para análisis VWAP:", "NVDA", help="Introduce un ticker").upper()
    with vc2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📈 Analizar VWAP", use_container_width=True):
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
                        low=df['Low'], close=df['Close'], name=symbol,
                        increasing_line_color='#00ffad',
                        decreasing_line_color='#f23645'
                    ))
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['VWAP'],
                        line=dict(color='#ffaa00', width=3),
                        name="VWAP"
                    ))
                    
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor='#11141a',
                        plot_bgcolor='#0c0e12',
                        height=450,
                        margin=dict(l=0, r=0, b=0, t=30),
                        title=f"{symbol} - Precio: ${price:.2f} | VWAP: ${vwap:.2f} | Desv: {dev:+.2f}%"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if dev > 2:
                        st.success(f"✅ **{symbol} FUERTE sobre VWAP (+{dev:.1f}%)**")
                    elif dev > 0.5:
                        st.info(f"➡️ **{symbol} sobre VWAP (+{dev:.1f}%)**")
                    elif dev > -0.5:
                        st.warning(f"⚠️ **{symbol} en equilibrio ({dev:+.1f}%)**")
                    elif dev > -2:
                        st.warning(f"📉 **{symbol} bajo VWAP ({dev:.1f}%)**")
                    else:
                        st.error(f"🔻 **{symbol} FUERTE bajo VWAP ({dev:.1f}%)**")
                else:
                    st.warning("Sin datos disponibles.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
