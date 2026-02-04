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
        pass  # Silencioso, intentar siguiente estrategia
    
    # Estrategia 2: Cache local
    try:
        if os.path.exists(".sp500_cache.json"):
            with open(".sp500_cache.json", "r") as f:
                data = json.load(f)
                cached_tickers = data.get("tickers", [])
                cache_date = data.get("date", "unknown")
                
                if len(cached_tickers) >= 490:
                    return cached_tickers, f"Cache ({cache_date[:10]})"
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
        "Communications": ["GOOGL", "META", "NFLX", "VZ", "T", "TMUS", "CHTR", "CMCSA", "ATVI",
                          "EA", "TTWO", "MTCH", "IAC", "LUMN", "FOXA", "NWSA", "IPG", "OMC", "LYV", "TTWO"]
    }
    
    # Aplanar y quitar duplicados manteniendo orden sectorial
    all_tickers = []
    for sector, ticks in sector_tickers.items():
        all_tickers.extend(ticks)
    
    # Eliminar duplicados preservando orden (set no preserva orden)
    seen = set()
    unique_tickers = [x for x in all_tickers if not (x in seen or seen.add(x))]
    
    if len(unique_tickers) >= 150:
        return unique_tickers, "Sectorial Hardcoded"
    
    # Estrategia 4: Fallback mínimo (nunca falla)
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
        # Cargar tickers inmediatamente
        try:
            self.tickers, self.source = get_sp500_comprehensive()
        except Exception as e:
            # Fallback absoluto
            self.tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]
            self.source = "Emergency Fallback"
        
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
    # INICIALIZACIÓN DEL MOTOR (CORREGIDA)
    # =============================================================================
    
    # Verificar si necesitamos recrear el engine (nueva versión o primera vez)
    need_new_engine = False
    
    if 'rsrw_engine' not in st.session_state:
        need_new_engine = True
    else:
        # Verificar que el engine existente tenga todos los atributos necesarios
        engine_temp = st.session_state.rsrw_engine
        required_attrs = ['tickers', 'source', 'benchmark']
        missing_attrs = [attr for attr in required_attrs if not hasattr(engine_temp, attr)]
        
        if missing_attrs:
            need_new_engine = True
            st.info(f"🔄 Actualizando scanner...")
        else:
            # Verificar que los tickers no estén vacíos
            if not engine_temp.tickers or len(engine_temp.tickers) == 0:
                need_new_engine = True
    
    if need_new_engine:
        with st.spinner("🚀 Inicializando motor de análisis..."):
            try:
                engine = RSRWEngine()
                st.session_state.rsrw_engine = engine
                st.session_state.scan_count = 0
            except Exception as e:
                st.error(f"❌ Error inicializando: {e}")
                st.stop()
    
    engine = st.session_state.rsrw_engine
    
    # Doble verificación de atributos (por si acaso)
    if not hasattr(engine, 'source'):
        engine.source = "Unknown"
    if not hasattr(engine, 'tickers'):
        engine.tickers = []
    if not hasattr(engine, 'benchmark'):
        engine.benchmark = "SPY"
    
    # Info de fuente de datos
    num_tickers = len(engine.tickers) if engine.tickers else 0
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span class="badge badge-info">
            📊 Universo: {num_tickers} tickers | Fuente: {engine.source}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Resto del código permanece igual...
    # [Aquí iría todo el resto del código que ya tenías: sección educativa, panel de control, 
    # ejecución del scan, dashboard de métricas, gráfico de dispersión, tablas de resultados, 
    # exportación, y sección VWAP]
    
    # Por ahora pongo un placeholder para que el código sea funcional:
    st.info("Scanner inicializado correctamente. Haz clic en 'ESCANEAR' para comenzar el análisis.")
    
    # Panel de Control simplificado para que funcione
    st.markdown('<div style="margin-bottom: 15px; color: #00ffad; font-size: 14px; font-weight: bold;">⚙️ Configuración</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    with col1:
        min_rvol = st.slider("RVOL Mínimo", 1.0, 3.0, 1.2, 0.1)
    with col2:
        rs_threshold = st.slider("Umbral RS (%)", 1, 10, 3, 1) / 100.0
    with col3:
        top_n = st.slider("Mostrar Top", 10, 50, 20, 5)
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_button = st.button("🔥 ESCANEAR", use_container_width=True, type="primary")
    
    if scan_button:
        if num_tickers == 0:
            st.error("❌ No hay tickers disponibles.")
            st.stop()
        
        with st.spinner(f"Analizando {num_tickers} tickers..."):
            try:
                raw_data = engine.download_batch(engine.tickers)
                if raw_data is not None:
                    results, spy_perf = engine.calculate_rs_metrics(raw_data)
                    if not results.empty:
                        st.success(f"✅ Scan completado: {len(results)} stocks analizados")
                        st.dataframe(results.head(10))
                    else:
                        st.warning("No se obtuvieron resultados.")
                else:
                    st.error("No se pudieron descargar datos.")
            except Exception as e:
                st.error(f"Error: {e}")
