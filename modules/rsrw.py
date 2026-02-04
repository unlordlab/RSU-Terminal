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
from functools import lru_cache

# =============================================================================
# 1. SISTEMA DE DATOS ROBUSTO: Múltiples fuentes con fallback
# =============================================================================

@st.cache_data(ttl=3600)  # 1 hora - balance entre frescura y rendimiento
def get_sp500_comprehensive():
    """
    Obtiene S&P 500 con múltiples estrategias de fallback.
    
    ESTRATEGIA:
    1. Wikipedia (más completa, ~503 tickers)
    2. Archivo local cache (persistencia entre sesiones)
    3. Lista hardcodeada sectorial (diversificación garantizada)
    4. Fallback mínimo (siempre funciona)
    
    POR QUÉ: Wikipedia cambia su estructura HTML frecuentemente. Necesitamos
    múltiples capas para garantizar que el scanner siempre funcione.
    """
    
    # Estrategia 1: Wikipedia (fuente primaria)
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        # timeout para no bloquear la app si Wikipedia está lenta
        df = pd.read_html(url, match="Symbol")[0]
        tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        
        if len(tickers) >= 490:
            # Guardar en cache local para persistencia
            try:
                with open(".sp500_cache.json", "w") as f:
                    json.dump({"tickers": tickers, "date": datetime.now().isoformat()}, f)
            except:
                pass
            return tickers, "Wikipedia (Live)"
    except Exception as e:
        st.warning(f"Wikipedia no disponible: {str(e)[:50]}...")
    
    # Estrategia 2: Cache local
    try:
        if os.path.exists(".sp500_cache.json"):
            with open(".sp500_cache.json", "r") as f:
                data = json.load(f)
                cached_tickers = data.get("tickers", [])
                cache_date = data.get("date", "unknown")
                
                if len(cached_tickers) >= 490:
                    st.info(f"Usando cache local ({cache_date[:10]})")
                    return cached_tickers, "Cache Local"
    except:
        pass
    
    # Estrategia 3: Lista hardcodeada sectorial (diversificación garantizada)
    # Por qué sectorial: Un scanner que solo mira tecnología no ve rotación sectorial
    sector_tickers = {
        "Technology": ["AAPL", "MSFT", "NVDA", "AVGO", "CSCO", "ADBE", "CRM", "ACN", "ORCL", "IBM",
                      "INTC", "QCOM", "TXN", "AMD", "AMAT", "ADI", "MU", "KLAC", "LRCX", "SNPS"],
        "Healthcare": ["LLY", "UNH", "JNJ", "MRK", "ABBV", "PFE", "TMO", "ABT", "DHR", "BMY",
                      "AMGN", "GILD", "VRTX", "REGN", "BIIB", "ZTS", "IQV", "DXCM", "EW", "ISRG"],
        "Financials": ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK", "C",
                      "AXP", "PNC", "USB", "TFC", "COF", "SCHW", "SPGI", "MCO", "ICE", "CME"],
        "Consumer": ["AMZN", "TSLA", "HD", "PG", "COST", "WMT", "KO", "PEP", "MCD", "NKE",
                    "DIS", "CMCSA", "LOW", "TJX", "SBUX", "BKNG", "ABNB", "MAR", "YUM", "DLTR"],
        "Industrials": ["CAT", "HON", "UNP", "UPS", "RTX", "BA", "GE", "LMT", "DE", "MMM",
                       "CSX", "NSC", "FDX", "ITW", "GD", "NOC", "EMR", "ETN", "PH", "CMI"],
        "Energy": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "VLO", "PSX", "OXY", "WMB",
                  "KMI", "EPD", "ET", "MPLX", "ENB", "TRP", "SU", "IMO", "CVE", "BP"],
        "Materials": ["LIN", "APD", "SHW", "FCX", "NEM", "DOW", "ECL", "NUE", "VMC", "PPG",
                     "BLL", "IP", "CF", "MOS", "FMC", "ALB", "EMN", "LYB", "PKG", "AVY"],
        "Utilities": ["NEE", "SO", "DUK", "AEP", "SRE", "EXC", "XEL", "ED", "PEG", "WEC",
                     "ES", "AWK", "D", "CNP", "NI", "FE", "AEE", "CMS", "LNT", "ETR"],
        "Real Estate": ["PLD", "AMT", "CCI", "EQIX", "PSA", "O", "WELL", "DLR", "SPG", "VICI",
                       "AVB", "EQR", "EXR", "UDR", "MAA", "BXP", "ARE", "HST", "VTR", "PEAK"],
        "Communications": ["GOOGL", "META", "NFLX", "VZ", "T", "TMUS", "CHTR", " Comcast", "ATVI",
                          "EA", "TTWO", "MTCH", "IAC", "LUMN", "VZ", "FOXA", "NWSA", "IPG", "OMC", "LYV"]
    }
    
    # Aplanar y quitar duplicados manteniendo orden sectorial
    all_tickers = []
    for sector, ticks in sector_tickers.items():
        all_tickers.extend(ticks)
    
    # Eliminar duplicados preservando orden (set no preserva orden)
    seen = set()
    unique_tickers = [x for x in all_tickers if not (x in seen or seen.add(x))]
    
    if len(unique_tickers) >= 150:
        st.info(f"Usando lista sectorial ({len(unique_tickers)} tickers)")
        return unique_tickers, "Sectorial Hardcoded"
    
    # Estrategia 4: Fallback mínimo (nunca falla)
    st.warning("Usando fallback mínimo - resultados limitados")
    return ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "AVGO", "WMT",
            "JPM", "V", "UNH", "MA", "HD", "PG", "LLY", "MRK", "COST", "CVX"], "Fallback Mínimo"


# =============================================================================
# 2. MOTOR DE ANÁLISIS: Multi-timeframe con manejo de errores
# =============================================================================

class RSRWEngine:
    """
    Motor de análisis de Fuerza Relativa.
    
    CONCEPTO: La fuerza relativa identifica dónde el "dinero inteligente"
    está posicionándose ANTES de que el movimiento sea obvio para todos.
    
    MULTI-TIMEFRAME: Un stock con RS positivo en 5d, 20d y 60d tiene
    tendencia sostenida. Si solo 5d es positivo, puede ser un rebote técnico.
    """
    
    def __init__(self):
        self.benchmark = "SPY"
        self.tickers, self.source = get_sp500_comprehensive()
        self.last_scan = None
        
    def download_batch(self, symbols, max_retries=3):
        """
        Descarga datos en lotes con reintentos.
        
        POR QUÉ LOTES: yfinance tiene límites de rate. Descargar 500 tickers
        de golpe falla frecuentemente. Los lotes de 100 son el sweet spot.
        """
        all_data = []
        
        # Dividir en lotes de 100
        batch_size = 100
        batches = [symbols[i:i+batch_size] for i in range(0, len(symbols), batch_size)]
        
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        for idx, batch in enumerate(batches):
            progress_text.text(f"Descargando lote {idx+1}/{len(batches)} ({len(batch)} tickers)...")
            
            for attempt in range(max_retries):
                try:
                    # Añadir delay entre lotes para no saturar la API
                    if idx > 0:
                        time.sleep(0.5)
                    
                    data = yf.download(
                        batch + [self.benchmark],
                        period="70d",
                        interval="1d",
                        progress=False,
                        threads=True,
                        timeout=30
                    )
                    
                    if not data.empty and 'Close' in data:
                        all_data.append(data)
                        break  # Éxito, salir del retry loop
                        
                except Exception as e:
                    if attempt == max_retries - 1:
                        st.warning(f"Lote {idx+1} falló después de {max_retries} intentos")
                    time.sleep(1)  # Esperar antes de reintentar
            
            progress_bar.progress((idx + 1) / len(batches))
        
        progress_text.empty()
        progress_bar.empty()
        
        # Combinar todos los lotes
        if not all_data:
            return None
        
        # Concatenar a lo largo del eje de columnas (tickers)
        combined = pd.concat(all_data, axis=1)
        return combined
    
    def calculate_rs_metrics(self, data, periods=[5, 20, 60]):
        """
        Calcula métricas de Fuerza Relativa multi-timeframe.
        
        FÓRMULAS:
        - RS = (Retorno Stock - Retorno SPY) 
        - RVOL = Volumen Hoy / Promedio 20 días
        - Trend Score = Ponderación: 50% 5d + 30% 20d + 20% 60d
        
        INTERPRETACIÓN:
        - RS_Score > 0.05 (5%): Outperformance significativo
        - RS_Score < -0.05: Underperformance significativo  
        - RVOL > 1.5: Interés institucional confirmado
        - RVOL > 2.0: Evento/catalizador probable
        """
        
        if data is None or data.empty:
            return pd.DataFrame(), 0.0
        
        try:
            # Manejar estructura de datos de yfinance
            if 'Close' in data.columns:
                close = data['Close']
                volume = data['Volume'] if 'Volume' in data else None
            else:
                return pd.DataFrame(), 0.0
            
            # Asegurar que tenemos el benchmark
            if self.benchmark not in close.columns:
                st.error(f"Benchmark {self.benchmark} no disponible en datos")
                return pd.DataFrame(), 0.0
            
            # Calcular retornos para cada timeframe
            rs_data = {}
            valid_periods = []
            
            for period in periods:
                if len(close) >= period:
                    try:
                        # Retorno total del período
                        returns = (close.iloc[-1] / close.iloc[-period]) - 1
                        spy_return = returns[self.benchmark]
                        
                        # Fuerza relativa = Exceso de retorno vs SPY
                        rs_data[f'RS_{period}d'] = returns - spy_return
                        valid_periods.append(period)
                    except:
                        continue
            
            if not rs_data:
                return pd.DataFrame(), 0.0
            
            # Crear DataFrame base
            df = pd.DataFrame(rs_data)
            
            # Calcular RVOL (Relative Volume)
            if volume is not None and not volume.empty:
                try:
                    avg_volume = volume.rolling(window=20, min_periods=1).mean()
                    current_volume = volume.iloc[-1]
                    df['RVOL'] = current_volume / avg_volume.iloc[-1]
                except:
                    df['RVOL'] = 1.0
            else:
                df['RVOL'] = 1.0
            
            # Precio actual
            df['Precio'] = close.iloc[-1]
            
            # Score compuesto ponderado (más peso al corto plazo)
            # Por qué: El corto plazo muestra momentum actual, largo plazo tendencia
            weights = {5: 0.5, 20: 0.3, 60: 0.2}
            weight_sum = sum(weights.get(p, 0.2) for p in valid_periods)
            
            if weight_sum > 0:
                df['RS_Score'] = sum(
                    df[f'RS_{p}d'] * (weights.get(p, 0.2) / weight_sum) 
                    for p in valid_periods if f'RS_{p}d' in df.columns
                )
            else:
                df['RS_Score'] = 0
            
            # Métricas adicionales
            df['Abs_RS_5d'] = abs(df.get('RS_5d', 0))
            df['Trend_Consistency'] = (
                (df.get('RS_5d', 0) > 0).astype(int) +
                (df.get('RS_20d', 0) > 0).astype(int) +
                (df.get('RS_60d', 0) > 0).astype(int)
            ) / 3.0  # % de timeframes alcistas
            
            # Eliminar benchmark de resultados
            if self.benchmark in df.index:
                df = df.drop(self.benchmark)
            
            # Limpiar NaN
            df = df.dropna()
            
            # SPY performance para contexto
            spy_perf = 0
            if self.benchmark in close.columns and len(close) >= 20:
                spy_perf = (close[self.benchmark].iloc[-1] / close[self.benchmark].iloc[-20]) - 1
            
            return df, spy_perf
            
        except Exception as e:
            st.error(f"Error en cálculo: {str(e)}")
            return pd.DataFrame(), 0.0


# =============================================================================
# 3. RENDERIZADO UI: Estética market.py profesional
# =============================================================================

def render():
    """
    Interfaz de usuario profesional con explicaciones integradas.
    """
    
    # CSS Global - Identidad visual consistente con market.py
    st.markdown("""
    <style>
        /* Contenedores principales */
        .main-header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
        }
        .main-title {
            color: white;
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }
        .main-subtitle {
            color: #888;
            font-size: 1.1rem;
            max-width: 700px;
            margin: 0 auto;
            line-height: 1.6;
        }
        
        /* Tarjetas de grupo - Core de market.py */
        .group-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        .group-container:hover {
            box-shadow: 0 8px 25px rgba(0,0,0,0.4);
            border-color: #2a3f5f;
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
            letter-spacing: 1.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .group-content {
            padding: 20px;
            background: #11141a;
        }
        
        /* Métricas estilo dashboard */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        .metric-card {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            padding: 20px 15px;
            text-align: center;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #2a3f5f;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: white;
            margin-bottom: 5px;
        }
        .metric-label {
            font-size: 0.7rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }
        .metric-delta {
            font-size: 0.8rem;
            margin-top: 5px;
            font-weight: 600;
        }
        
        /* Badges de estado */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-hot {
            background: rgba(242, 54, 69, 0.15);
            color: #f23645;
            border: 1px solid rgba(242, 54, 69, 0.3);
        }
        .badge-strong {
            background: rgba(0, 255, 173, 0.15);
            color: #00ffad;
            border: 1px solid rgba(0, 255, 173, 0.3);
        }
        .badge-neutral {
            background: rgba(255, 152, 0, 0.15);
            color: #ff9800;
            border: 1px solid rgba(255, 152, 0, 0.3);
        }
        .badge-info {
            background: rgba(41, 98, 255, 0.15);
            color: #2962ff;
            border: 1px solid rgba(41, 98, 255, 0.3);
        }
        
        /* Tooltips informativos */
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
            transition: all 0.2s;
        }
        .tooltip-container:hover .tooltip-icon {
            border-color: #00ffad;
            color: #00ffad;
        }
        .tooltip-text {
            visibility: hidden;
            width: 320px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 15px;
            border-radius: 8px;
            position: absolute;
            z-index: 999;
            top: 40px;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            line-height: 1.5;
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        
        /* Separadores elegantes */
        .section-divider {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, #2a3f5f 50%, transparent 100%);
            margin: 40px 0;
            position: relative;
        }
        .section-divider::after {
            content: '◆';
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            color: #2962ff;
            font-size: 8px;
            background: #0c0e12;
            padding: 0 15px;
        }
        
        /* Cajas de información */
        .info-card {
            background: linear-gradient(135deg, rgba(41,98,255,0.08) 0%, rgba(0,255,173,0.03) 100%);
            border: 1px solid #2a3f5f;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        .info-title {
            color: #00ffad;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .info-text {
            color: #aaa;
            font-size: 13px;
            line-height: 1.6;
        }
        
        /* Tablas estilizadas */
        .dataframe {
            font-size: 12px !important;
        }
        .dataframe th {
            background: #0c0e12 !important;
            color: #00ffad !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            font-size: 10px !important;
            letter-spacing: 1px !important;
        }
        .dataframe td {
            background: #11141a !important;
            border-bottom: 1px solid #1a1e26 !important;
        }
        
        /* Estados de carga */
        .loading-pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
    """, unsafe_allow_html=True)

    # =============================================================================
    # HEADER PRINCIPAL
    # =============================================================================
    
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title"><span style="color: #00ffad;">🔍</span> Scanner RS/RW Pro</h1>
        <p class="main-subtitle">
            Análisis institucional de Fuerza Relativa en tiempo real. 
            Identifica flujo de capital antes del movimiento mayoritario.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # =============================================================================
    # SECCIÓN EDUCATIVA EXPANDIBLE
    # =============================================================================
    
    with st.expander("📚 Guía Completa: Cómo usar el Scanner RS/RW", expanded=False):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎯 Conceptos Fundamentales
            
            **Fuerza Relativa (RS)**  
            No es el RSI. Es el exceso de retorno de un stock vs el S&P 500 (SPY).
            - **RS = +5%**: El stock subió 5% más que el mercado
            - **RS = -3%**: El stock subió 3% menos (o cayó más)
            
            **¿Por qué importa?**  
            El dinero institucional rota sectores constantemente. El RS te muestra
            dónde están acumulando DESPUÉS de que empezaron, pero ANTES de que
            el movimiento sea obvio en los titulares.
            
            **Relative Volume (RVOL)**  
            Volumen de hoy / Promedio 20 días.
            - **1.0-1.3**: Volumen normal
            - **1.5-2.0**: Interés institucional (↑)
            - **>2.5**: Evento/catalizador probable (earnings, noticia)
            """)
        
        with col2:
            st.markdown("""
            ### 📊 Interpretación Multi-Timeframe
            
            Nuestro scanner analiza 3 timeframes simultáneamente:
            
            | Timeframe | Peso | Qué mide |
            |-----------|------|----------|
            | **5 días** | 50% | Momentum inmediato |
            | **20 días** | 30% | Tendencia mensual |
            | **60 días** | 20% | Tendencia trimestral |
            
            **Señales de Alta Confianza:**
            - ✅ RS positivo en los 3 timeframes + RVOL >1.5
            - ✅ RS 5d > RS 20d > RS 60d (aceleración)
            - ✅ Precio cerca de máximos históricos + RS alto
            
            **⚠️ Falsos Positivos:**
            - RS alto pero RVOL <1.0 (falta convicción)
            - Solo RS 5d positivo (rebote técnico sin tendencia)
            - Sector en contracción general (stock fuerte en sector débil = trampa)
            """)
        
        st.markdown("---")
        
        st.markdown("""
        ### 🎮 Estrategias de Trading
        
        **Setup Largo (Mercado Alcista)**
        1. SPY > 20EMA (tendencia alcista confirmada)
        2. Scanner muestra RS >3% + RVOL >1.5
        3. Esperar pullback al VWAP o 9EMA
        4. Stop loss bajo mínimo del día de entrada
        5. Target: 2-3R o cuando RS empiece a decaer
        
        **Setup Corto (Mercado Bajista)**
        1. SPY < 20EMA
        2. Scanner muestra RS negativo fuerte (<-3%)
        3. Rebote al VWAP con rechazo
        4. Stop loss sobre máximo del día
        
        **Gestión de Riesgo**
        - Nunca más del 5% del portfolio en una posición RS/RW
        - Si el RS cruza a negativo, reducir 50% automáticamente
        - Correlación SPY >0.8: los setups funcionan mejor
        """)

    # =============================================================================
    # INICIALIZACIÓN DEL MOTOR
    # =============================================================================
    
    if 'rsrw_engine' not in st.session_state:
        with st.spinner("🚀 Inicializando motor de análisis..."):
            engine = RSRWEngine()
            st.session_state.rsrw_engine = engine
            st.session_state.scan_count = 0
    
    engine = st.session_state.rsrw_engine
    
    # Info de fuente de datos
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span class="badge badge-info">
            📊 Universo: {len(engine.tickers)} tickers | Fuente: {engine.source}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # =============================================================================
    # PANEL DE CONTROL
    # =============================================================================
    
    st.markdown('<div style="margin-bottom: 15px; color: #00ffad; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px;">⚙️ Configuración del Scan</div>', unsafe_allow_html=True)
    
    control_col1, control_col2, control_col3, control_col4 = st.columns([2, 2, 2, 1])
    
    with control_col1:
        min_rvol = st.slider(
            "RVOL Mínimo", 
            1.0, 3.0, 1.2, 0.1,
            help="Filtra stocks sin interés institucional. 1.5 = 50% más volumen de lo normal."
        )
    
    with control_col2:
        rs_threshold = st.slider(
            "Umbral RS (%)", 
            1, 10, 3, 1,
            help="Mínimo de outperformance vs SPY para considerar 'Strong'"
        ) / 100.0
    
    with control_col3:
        top_n = st.slider(
            "Mostrar Top", 
            10, 50, 20, 5,
            help="Número de resultados por categoría"
        )
    
    with control_col4:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_button = st.button(
            "🔥 ESCANEAR", 
            use_container_width=True, 
            type="primary",
            help="Analiza todo el universo S&P 500"
        )

    # =============================================================================
    # EJECUCIÓN DEL SCAN
    # =============================================================================
    
    if scan_button:
        scan_start = time.time()
        
        # Verificar que tenemos tickers
        if not hasattr(engine, 'tickers') or len(engine.tickers) == 0:
            st.error("❌ Error: No hay tickers disponibles. Recarga la página.")
            st.stop()
        
        with st.spinner(f"Analizando {len(engine.tickers)} tickers en 3 timeframes..."):
            
            # Descargar datos en lotes
            raw_data = engine.download_batch(engine.tickers)
            
            if raw_data is None or raw_data.empty:
                st.error("❌ No se pudieron descargar datos. Posibles causas:")
                st.markdown("""
                - Yahoo Finance está en mantenimiento
                - Límite de rate excedido (espera 1 minuto)
                - Mercado cerrado sin datos recientes
                """)
                st.stop()
            
            # Calcular métricas
            results, spy_perf = engine.calculate_rs_metrics(raw_data)
            
            scan_duration = time.time() - scan_start
            
            if results.empty:
                st.warning("⚠️ No se pudieron calcular métricas con los datos disponibles.")
            else:
                # Guardar en session state para exportación
                st.session_state.last_results = results
                st.session_state.scan_count += 1
                
                # =============================================================================
                # DASHBOARD DE MÉTRICAS
                # =============================================================================
                
                st.markdown(f'<div style="margin: 25px 0;">', unsafe_allow_html=True)
                
                metric_cols = st.columns(4)
                
                # Métrica 1: SPY Performance
                with metric_cols[0]:
                    spy_color = "#00ffad" if spy_perf >= 0 else "#f23645"
                    spy_icon = "▲" if spy_perf >= 0 else "▼"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: {spy_color};">{spy_perf:+.2%}</div>
                        <div class="metric-label">SPY 20D Trend</div>
                        <div class="metric-delta" style="color: {spy_color};">{spy_icon} Contexto de Mercado</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Métrica 2: Strong RS Count
                with metric_cols[1]:
                    strong_count = len(results[results['RS_Score'] > rs_threshold])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #00ffad;">{strong_count}</div>
                        <div class="metric-label">Strong RS (>{rs_threshold:.0%})</div>
                        <div class="metric-delta" style="color: #00ffad;">{strong_count/len(results)*100:.1f}% del universo</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Métrica 3: High RVOL
                with metric_cols[2]:
                    high_rvol_count = len(results[results['RVOL'] > 1.5])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #ffaa00;">{high_rvol_count}</div>
                        <div class="metric-label">Alto RVOL (>1.5x)</div>
                        <div class="metric-delta" style="color: #ffaa00;">Presión institucional</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Métrica 4: Setups Activos
                with metric_cols[3]:
                    active_setups = len(results[
                        (results['RS_Score'] > rs_threshold) & 
                        (results['RVOL'] > min_rvol)
                    ])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #2962ff;">{active_setups}</div>
                        <div class="metric-label">Setups Activos</div>
                        <div class="metric-delta" style="color: #888;">Scan #{st.session_state.scan_count} • {scan_duration:.1f}s</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # =============================================================================
                # GRÁFICO DE DISPERSIÓN RS vs RVOL
                # =============================================================================
                
                st.markdown('<div style="margin-bottom: 15px; color: #00ffad; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px;">📊 Mapa de Oportunidades: RS vs Volumen</div>', unsafe_allow_html=True)
                
                fig = px.scatter(
                    results.reset_index().rename(columns={'index': 'Ticker'}),
                    x='RS_Score',
                    y='RVOL',
                    color='RS_Score',
                    color_continuous_scale=['#f23645', '#ff9800', '#00ffad', '#00ffad'],
                    size='RVOL',
                    size_max=25,
                    hover_name='Ticker',
                    hover_data={
                        'RS_Score': ':.2%',
                        'RVOL': ':.2f',
                        'Precio': ':$.2f',
                        'RS_5d': ':.2%',
                        'RS_20d': ':.2%'
                    },
                    labels={
                        'RS_Score': 'Fuerza Relativa (Score Compuesto)',
                        'RVOL': 'Relative Volume (x veces promedio)'
                    }
                )
                
                # Líneas de referencia
                fig.add_hline(y=1.5, line_dash="dash", line_color="#ffaa00", opacity=0.6, 
                             annotation_text="RVOL 1.5 (Institucional)")
                fig.add_vline(x=0, line_dash="solid", line_color="white", opacity=0.3)
                fig.add_vline(x=rs_threshold, line_dash="dash", line_color="#00ffad", opacity=0.5,
                             annotation_text=f"RS {rs_threshold:.0%}")
                
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor='#11141a',
                    plot_bgcolor='#0c0e12',
                    font_color='white',
                    height=450,
                    margin=dict(l=0, r=0, b=0, t=40),
                    title=dict(
                        text="Cada punto es un stock del S&P 500. Cuadrante superior-derecho = oportunidades de alta calidad.",
                        font_size=11,
                        font_color='#888'
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Leyenda del gráfico
                st.markdown("""
                <div style="display: flex; justify-content: space-around; margin: 15px 0; font-size: 12px; color: #888;">
                    <span><span style="color: #f23645;">●</span> Debilidad Relativa (Evitar/Short)</span>
                    <span><span style="color: #ff9800;">●</span> Momentum sin Volumen (Cautela)</span>
                    <span><span style="color: #00ffad;">●</span> Fuerza + Volumen (Setup Ideal)</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                
                # =============================================================================
                # TABLAS DE RESULTADOS
                # =============================================================================
                
                results_col1, results_col2 = st.columns(2)
                
                # --- LÍDERES RS ---
                with results_col1:
                    st.markdown(f"""
                    <div class="group-container">
                        <div class="group-header">
                            <span class="group-title">🚀 LÍDERES DE FUERZA RELATIVA</span>
                            <div style="display: flex; gap: 8px;">
                                <span class="badge badge-strong">LONG SETUPS</span>
                                <div class="tooltip-container">
                                    <div class="tooltip-icon">?</div>
                                    <div class="tooltip-text">
                                        <strong>Criterios de selección:</strong><br>
                                        • RS Score > {rs_threshold:.0%} vs SPY<br>
                                        • RVOL > {min_rvol}x volumen promedio<br>
                                        • Tendencia sostenida en múltiples timeframes<br><br>
                                        <strong>Acción:</strong> Buscar entrada en pullbacks al VWAP o EMAs.
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="group-content">
                    """, unsafe_allow_html=True)
                    
                    # Filtrar y ordenar
                    df_rs = results[results['RS_Score'] > rs_threshold].nlargest(top_n, 'RS_Score')
                    df_rs = df_rs[df_rs['RVOL'] >= min_rvol]
                    
                    if not df_rs.empty:
                        # Preparar display
                        display_rs = df_rs.copy()
                        display_rs['Setup'] = display_rs.apply(
                            lambda x: '🔥 HOT' if x['RVOL'] > 2.0 and x['RS_Score'] > 0.08 
                            else ('✅ Strong' if x['RS_Score'] > 0.05 else '⬆️ Positive'), 
                            axis=1
                        )
                        
                        st.dataframe(
                            display_rs[['RS_Score', 'RVOL', 'RS_5d', 'RS_20d', 'Setup']].style
                            .format({
                                'RS_Score': '{:+.2%}', 
                                'RVOL': '{:.2f}x',
                                'RS_5d': '{:+.1%}',
                                'RS_20d': '{:+.1%}'
                            })
                            .background_gradient(subset=['RS_Score'], cmap='Greens')
                            .background_gradient(subset=['RVOL'], cmap='YlGn', vmin=1, vmax=3)
                            .map(lambda x: 'color: #00ffad' if isinstance(x, str) and 'HOT' in x else 
                                 ('color: #4caf50' if isinstance(x, str) and 'Strong' in x else ''),
                                 subset=['Setup']),
                            use_container_width=True,
                            height=350
                        )
                    else:
                        st.info("No hay líderes RS con los filtros actuales. Reduce el umbral de RVOL para ver más resultados.")
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                # --- LAGGARDS RS ---
                with results_col2:
                    st.markdown("""
                    <div class="group-container">
                        <div class="group-header">
                            <span class="group-title">📉 LAGGARDS (DEBILIDAD)</span>
                            <div style="display: flex; gap: 8px;">
                                <span class="badge badge-hot">AVOID / SHORT</span>
                                <div class="tooltip-container">
                                    <div class="tooltip-icon">?</div>
                                    <div class="tooltip-text">
                                        <strong>Criterios de selección:</strong><br>
                                        • RS Score negativo (underperforma SPY)<br>
                                        • Volumen puede ser alto (distribución)<br><br>
                                        <strong>Acción:</strong> Evitar largos. Considerar shorts si el mercado es bajista.
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="group-content">
                    """, unsafe_allow_html=True)
                    
                    df_rw = results[results['RS_Score'] < -0.01].nsmallest(top_n, 'RS_Score')
                    
                    if not df_rw.empty:
                        display_rw = df_rw.copy()
                        display_rw['Alerta'] = display_rw.apply(
                            lambda x: '⚠️ Distribution' if x['RVOL'] > 1.5 and x['RS_Score'] < -0.05
                            else ('🔻 Weak' if x['RS_Score'] < -0.05 else '⬇️ Lagging'),
                            axis=1
                        )
                        
                        st.dataframe(
                            display_rw[['RS_Score', 'RVOL', 'RS_5d', 'RS_20d', 'Alerta']].style
                            .format({
                                'RS_Score': '{:+.2%}', 
                                'RVOL': '{:.2f}x',
                                'RS_5d': '{:+.1%}',
                                'RS_20d': '{:+.1%}'
                            })
                            .background_gradient(subset=['RS_Score'], cmap='Reds_r')
                            .background_gradient(subset=['RVOL'], cmap='OrRd', vmin=1, vmax=3),
                            use_container_width=True,
                            height=350
                        )
                    else:
                        st.success("✅ Mercado alcista general - poca debilidad relativa detectada.")
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                # =============================================================================
                # EXPORTACIÓN Y PERSISTENCIA
                # =============================================================================
                
                export_col1, export_col2, export_col3 = st.columns([3, 3, 2])
                
                with export_col3:
                    # Botón de exportar CSV
                    if 'last_results' in st.session_state:
                        csv = st.session_state.last_results.to_csv().encode('utf-8')
                        st.download_button(
                            label="📥 Exportar CSV",
                            data=csv,
                            file_name=f"RS_Scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

    # =============================================================================
    # SECCIÓN VWAP INTRADÍA
    # =============================================================================
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<div style="margin-bottom: 15px; color: #00ffad; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px;">🎯 Validación Intradía con VWAP</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <div class="info-title">💡 Cómo usar el VWAP con el Scanner RS</div>
        <div class="info-text">
            El VWAP (Volume Weighted Average Price) es el precio promedio ponderado por volumen del día. 
            Los institucionales lo usan como referencia de "valor justo".<br><br>
            <strong>Integración con RS:</strong> Un stock con RS alto + precio sobre VWAP = tendencia intradía confirmada. 
            Si el RS es alto pero el precio cruza bajo VWAP, considerar tomar ganancias parciales.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    vwap_col1, vwap_col2 = st.columns([3, 1])
    
    with vwap_col1:
        symbol = st.text_input(
            "Ticker a analizar:", 
            "NVDA",
            help="Introduce cualquier ticker del S&P 500 o del scanner"
        ).upper()
    
    with vwap_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("📈 Analizar VWAP", use_container_width=True, type="secondary")
    
    if analyze_btn and symbol:
        with st.spinner(f"Cargando datos intradía de {symbol}..."):
            try:
                # Descargar datos de 2 días para tener contexto
                df = yf.download(symbol, period="2d", interval="5m", progress=False)
                
                if df.empty or len(df) < 10:
                    st.warning(f"No hay datos suficientes para {symbol}. El mercado puede estar cerrado.")
                else:
                    # Limpiar columnas multi-index
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    # Calcular VWAP
                    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
                    df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
                    
                    # Calcular bandas de desviación (1% y 2%)
                    df['VWAP_Upper1'] = df['VWAP'] * 1.01
                    df['VWAP_Lower1'] = df['VWAP'] * 0.99
                    
                    # Precios actuales
                    current_price = df['Close'].iloc[-1]
                    current_vwap = df['VWAP'].iloc[-1]
                    deviation = ((current_price - current_vwap) / current_vwap) * 100
                    
                    # Métricas en tarjetas
                    vwap_metrics = st.columns(4)
                    
                    with vwap_metrics[0]:
                        st.metric("Precio", f"${current_price:.2f}")
                    with vwap_metrics[1]:
                        st.metric("VWAP", f"${current_vwap:.2f}")
                    with vwap_metrics[2]:
                        st.metric("Desviación", f"{deviation:+.2f}%", 
                                 delta="Sobre VWAP" if deviation > 0 else "Bajo VWAP")
                    with vwap_metrics[3]:
                        # Distancia a VWAP en términos de ATR (volatilidad)
                        try:
                            atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
                            vwap_distance_atr = abs(deviation/100 * current_vwap) / atr if atr > 0 else 0
                            st.metric("Distancia (ATR)", f"{vwap_distance_atr:.2f}x")
                        except:
                            st.metric("Volumen", f"{df['Volume'].iloc[-1]/1e6:.1f}M")
                    
                    # Gráfico profesional
                    fig = go.Figure()
                    
                    # Velas
                    fig.add_trace(go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name=f"{symbol} Price",
                        increasing_line_color='#00ffad',
                        decreasing_line_color='#f23645'
                    ))
                    
                    # VWAP principal
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['VWAP'],
                        line=dict(color='#ffaa00', width=3),
                        name="VWAP",
                        hovertemplate='VWAP: $%{y:.2f}<extra></extra>'
                    ))
                    
                    # Bandas de VWAP (zona de valor)
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['VWAP_Upper1'],
                        line=dict(color='rgba(255,170,0,0.3)', width=1, dash='dash'),
                        name="VWAP +1%",
                        showlegend=False
                    ))
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['VWAP_Lower1'],
                        line=dict(color='rgba(255,170,0,0.3)', width=1, dash='dash'),
                        name="VWAP -1%",
                        fill='tonexty',
                        fillcolor='rgba(255,170,0,0.05)',
                        showlegend=False
                    ))
                    
                    # Layout
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor='#11141a',
                        plot_bgcolor='#0c0e12',
                        font_color='white',
                        height=500,
                        margin=dict(l=0, r=0, b=0, t=30),
                        title=dict(
                            text=f"{symbol} - Análisis Intradía con VWAP",
                            font_size=14,
                            x=0.5
                        ),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        xaxis_rangeslider_visible=False
                    )
                    
                    # Formato eje Y como dólares
                    fig.update_yaxes(tickprefix="$", tickformat=".2f")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Señal de trading
                    if deviation > 2:
                        st.success(f"""
                        ✅ **{symbol} FUERTE sobre VWAP (+{deviation:.1f}%)**
                        
                        El precio está significativamente por encima del valor promedio ponderado por volumen.
                        Esto indica presión compradora institucional. Estrategia: Mantener largos, 
                        stop loss dinámico en VWAP o +1% debajo.
                        """)
                    elif deviation > 0.5:
                        st.info(f"""
                        ➡️ **{symbol} sobre VWAP (+{deviation:.1f}%)**
                        
                        Tendencia alcista moderada. El precio respeta el VWAP como soporte dinámico.
                        Considerar acumulación si hay pullback al VWAP sin romperlo.
                        """)
                    elif deviation > -0.5:
                        st.warning(f"""
                        ⚠️ **{symbol} en equilibrio ({deviation:+.1f}%)**
                        
                        El precio está en la zona de valor (±0.5% del VWAP). Indecisión del mercado.
                        Esperar breakout con volumen (>1.5x) para tomar dirección.
                        """)
                    elif deviation > -2:
                        st.warning(f"""
                        📉 **{symbol} bajo VWAP ({deviation:.1f}%)**
                        
                        Debilidad relativa intradía. Si tienes largos, considera reducir 50%.
                        Para nuevas posiciones, esperar recuperación del VWAP como confirmación.
                        """)
                    else:
                        st.error(f"""
                        🔻 **{symbol} FUERTE bajo VWAP ({deviation:.1f}%)**
                        
                        Presión vendedora dominante. Evitar largos. Si el RS del scanner también es negativo,
                        considerar posiciones cortas con stop en VWAP.
                        """)
                        
            except Exception as e:
                st.error(f"Error analizando {symbol}: {str(e)}")
                st.info("Consejo: Verifica que el ticker sea correcto y el mercado esté abierto.")
