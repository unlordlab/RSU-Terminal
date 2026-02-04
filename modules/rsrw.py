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
            return tickers
    except Exception as e:
        st.warning(f"Wikipedia falló: {e}")
    
    # Intento 2: Archivo local cache
    try:
        if os.path.exists("sp500_cache.json"):
            with open("sp500_cache.json", "r") as f:
                cached = json.load(f)
                if len(cached) >= 490:
                    return cached
    except:
        pass
    
    # Fallback: Lista hardcodeada actualizada (top 100 + diversidad sectorial)
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
        self.tickers = get_sp500_tickers_cached()
    
    def get_multi_timeframe_rs(self, tickers, periods=[5, 20, 60]):
        """Calcula RS en múltiples timeframes para contexto"""
        all_symbols = tickers + [self.benchmark]
        max_days = max(periods) + 10
        
        try:
            data = yf.download(all_symbols, period=f"{max_days}d", interval="1d", progress=False)
            if data.empty or 'Close' not in data:
                return pd.DataFrame(), 0.0
            
            close = data['Close']
            volume = data['Volume'] if 'Volume' in data else None
            
            # Calcular RS para cada timeframe
            rs_data = {}
            for period in periods:
                if len(close) >= period:
                    returns = (close.iloc[-1] / close.iloc[-period]) - 1
                    spy_ret = returns[self.benchmark]
                    rs_data[f'RS_{period}d'] = returns - spy_ret
            
            # RVOL solo si tenemos volumen
            rvol = None
            if volume is not None and not volume.empty:
                try:
                    rvol = volume.iloc[-1] / volume.rolling(20).mean().iloc[-1]
                except:
                    rvol = pd.Series([1.0] * len(tickers), index=tickers)
            
            # Crear DataFrame
            df = pd.DataFrame(rs_data)
            df['Precio'] = close.iloc[-1]
            df['RVOL'] = rvol if rvol is not None else 1.0
            
            # Score compuesto (ponderado)
            weights = {5: 0.5, 20: 0.3, 60: 0.2}  # Más peso al corto plazo
            available_periods = [p for p in periods if f'RS_{p}d' in df.columns]
            if available_periods:
                df['RS_Score'] = sum(df[f'RS_{p}d'] * weights.get(p, 0.2) for p in available_periods)
            else:
                df['RS_Score'] = 0
            
            # Eliminar benchmark
            if self.benchmark in df.index:
                df = df.drop(self.benchmark)
            
            # Filtrar solo los tickers solicitados que existen en datos
            df = df[df.index.isin(tickers)]
            
            spy_perf = ((close[self.benchmark].iloc[-1] / close[self.benchmark].iloc[-20]) - 1) if len(close) >= 20 else 0
            return df, spy_perf
            
        except Exception as e:
            st.error(f"Error en cálculo RS: {e}")
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

    # Info Educativa Expandible
    with st.expander("📚 ¿Qué es la Fuerza Relativa (RS) y por qué importa?", expanded=False):
        st.markdown("""
        ### Conceptos Clave
        
        **🔥 Relative Strength (RS)**  
        Mide cuánto outperforma o underperforma un activo vs el benchmark (SPY).  
        - **RS > 0**: El activo sube más (o cae menos) que el mercado  
        - **RS < 0**: El activo muestra debilidad relativa  
        
        **📊 Relative Volume (RVOL)**  
        Volumen actual / Volumen promedio (20 días).  
        - **RVOL > 1.5**: Interés institucional confirmado  
        - **RVOL > 2.0**: Movimiento significativo, posible catalizador  
        - **RVOL < 1.0**: Falta de convicción, evitar
        
        **🎯 Estrategia de Uso**  
        1. **Mercado alcista (SPY > 20EMA)**: Buscar RS > 2% + RVOL > 1.5 para largos  
        2. **Mercado bajista**: Buscar RW (RS negativo) para shorts o evitar  
        3. **Divergencias**: RS positivo pero precio plano = acumulación institucional
        
        **⚠️ Limitaciones**  
        - RS es *lagging* en corto plazo (5d)  
        - Sin contexto de sector puede dar falsos positivos  
        - Requiere confirmación de precio (breakouts, soportes)
        """)
        
        # Métricas de contexto
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("S&P 500 Tickers", "~503", help="Actualizado diariamente")
        with col2:
            st.metric("Datos Históricos", "20+ años", help="Vía Yahoo Finance")
        with col3:
            st.metric("Actualización", "Tiempo real", help="Delay 15 min (datos gratis)")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Inicializar engine
    if 'rsrw_engine' not in st.session_state:
        with st.spinner("Cargando universo S&P 500..."):
            st.session_state.rsrw_engine = RSRWEngine()
    
    engine = st.session_state.rsrw_engine
    
    # Panel de Control
    st.markdown('<div style="margin-bottom: 10px; color: #00ffad; font-size: 14px; font-weight: bold;">⚙️ CONFIGURACIÓN DEL SCAN</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        min_rvol = st.slider("RVOL Mínimo", 1.0, 3.0, 1.2, 0.1, 
                            help="Volumen relativo mínimo para filtrar stocks sin interés institucional")
    with col2:
        top_n = st.slider("Top N Resultados", 10, 50, 20, 5,
                         help="Número de stocks a mostrar por categoría")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_button = st.button("🔥 ESCANEAR", use_container_width=True, type="primary")

    if scan_button:
        with st.spinner(f"Analizando {len(engine.tickers)} tickers en múltiples timeframes..."):
            results, spy_perf = engine.get_multi_timeframe_rs(engine.tickers)
            
            if not results.empty:
                # Dashboard de Métricas
                st.markdown('<div style="margin: 20px 0;">', unsafe_allow_html=True)
                metric_cols = st.columns(4)
                
                with metric_cols[0]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: {'#00ffad' if spy_perf >= 0 else '#f23645'};">{spy_perf:+.1%}</div>
                        <div class="metric-label">SPY 20D Change</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_cols[1]:
                    strong_rs = len(results[results['RS_Score'] > 0.05])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #00ffad;">{strong_rs}</div>
                        <div class="metric-label">Strong RS (>5%)</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_cols[2]:
                    high_rvol = len(results[results['RVOL'] > 1.5])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #ffaa00;">{high_rvol}</div>
                        <div class="metric-label">High RVOL (>1.5x)</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_cols[3]:
                    setups = len(results[(results['RS_Score'] > 0.03) & (results['RVOL'] > 1.2)])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #2962ff;">{setups}</div>
                        <div class="metric-label">Setups Activos</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

                # Gráfico de dispersión RS vs RVOL
                st.markdown('<div style="margin-bottom: 10px; color: #00ffad; font-size: 14px; font-weight: bold;">📊 MAPA RS vs RVOL</div>', unsafe_allow_html=True)
                
                fig = px.scatter(
                    results.reset_index(),
                    x='RS_Score',
                    y='RVOL',
                    hover_data=['index', 'Precio'],
                    color='RS_Score',
                    color_continuous_scale=['#f23645', '#ff9800', '#00ffad'],
                    size='RVOL',
                    size_max=20,
                    labels={'RS_Score': 'Fuerza Relativa (Score)', 'RVOL': 'Volumen Relativo', 'index': 'Ticker'}
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor='#11141a',
                    plot_bgcolor='#0c0e12',
                    font_color='white',
                    height=400,
                    margin=dict(l=0, r=0, b=0, t=10)
                )
                fig.add_hline(y=1.5, line_dash="dash", line_color="#ffaa00", opacity=0.5, annotation_text="RVOL 1.5")
                fig.add_vline(x=0, line_dash="dash", line_color="white", opacity=0.3)
                st.plotly_chart(fig, use_container_width=True)

                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

                # Tablas de Resultados
                col_rs, col_rw = st.columns(2)
                
                with col_rs:
                    st.markdown("""
                    <div class="group-container">
                        <div class="group-header">
                            <span class="group-title">🚀 FUERZA RELATIVA (RS)</span>
                            <span class="badge badge-strong">LONG SETUPS</span>
                        </div>
                        <div class="group-content">
                    """, unsafe_allow_html=True)
                    
                    df_rs = results[results['RS_Score'] > 0].nlargest(top_n, 'RS_Score')
                    df_rs = df_rs[df_rs['RVOL'] >= min_rvol]
                    
                    if not df_rs.empty:
                        # Añadir badges
                        df_rs_display = df_rs.copy()
                        df_rs_display['Setup'] = df_rs_display.apply(
                            lambda x: '🔥 HOT' if x['RVOL'] > 2 and x['RS_Score'] > 0.05 else ('✅ Strong' if x['RS_Score'] > 0.03 else 'Neutral'), 
                            axis=1
                        )
                        
                        st.dataframe(
                            df_rs_display[['RS_Score', 'RVOL', 'Setup']].style
                            .format({'RS_Score': '{:+.2%}', 'RVOL': '{:.2f}x'})
                            .background_gradient(subset=['RS_Score'], cmap='Greens')
                            .background_gradient(subset=['RVOL'], cmap='YlGn', vmin=1, vmax=3),
                            use_container_width=True,
                            height=400
                        )
                    else:
                        st.info("No hay setups de RS con los filtros actuales")
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                with col_rw:
                    st.markdown("""
                    <div class="group-container">
                        <div class="group-header">
                            <span class="group-title">📉 DEBILIDAD RELATIVA (RW)</span>
                            <span class="badge badge-hot">AVOID/SHORT</span>
                        </div>
                        <div class="group-content">
                    """, unsafe_allow_html=True)
                    
                    df_rw = results[results['RS_Score'] < 0].nsmallest(top_n, 'RS_Score')
                    
                    if not df_rw.empty:
                        df_rw_display = df_rw.copy()
                        df_rw_display['Alerta'] = df_rw_display['RS_Score'].apply(
                            lambda x: '⚠️ Weak' if x < -0.05 else 'Fading'
                        )
                        
                        st.dataframe(
                            df_rw_display[['RS_Score', 'RVOL', 'Alerta']].style
                            .format({'RS_Score': '{:+.2%}', 'RVOL': '{:.2f}x'})
                            .background_gradient(subset=['RS_Score'], cmap='Reds_r')
                            .background_gradient(subset=['RVOL'], cmap='OrRd', vmin=1, vmax=3),
                            use_container_width=True,
                            height=400
                        )
                    else:
                        st.info("Mercado alcista general - poca debilidad relativa")
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)

                # Exportar resultados
                st.markdown("<br>", unsafe_allow_html=True)
                col_exp1, col_exp2 = st.columns([6, 1])
                with col_exp2:
                    csv = results.to_csv().encode('utf-8')
                    st.download_button(
                        "📥 CSV",
                        csv,
                        f"rs_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        "text/csv",
                        use_container_width=True
                    )

            else:
                st.error("❌ No se pudieron obtener datos. Posibles causas:\n"
                        "- Límite de rate de Yahoo Finance\n"
                        "- Problemas de conectividad\n"
                        "- Mercado cerrado sin datos recientes")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Sección VWAP Intradía
    st.markdown('<div style="margin-bottom: 10px; color: #00ffad; font-size: 14px; font-weight: bold;">🎯 VALIDACIÓN INTRADÍA (VWAP)</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
        <p style="color: #888; font-size: 13px; margin: 0;">
            💡 <strong>Uso:</strong> Valida setups del scanner en tiempo real. Precio sobre VWAP = sesgo alcista. 
            Cruce bajo VWAP = stop loss o toma de ganancias parcial.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        symbol = st.text_input("Ticker a validar:", "NVDA", key="vwap_symbol").upper()
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        vwap_button = st.button("📈 Analizar", use_container_width=True)

    if vwap_button and symbol:
        with st.spinner(f"Cargando datos intradía de {symbol}..."):
            try:
                df_i = yf.download(symbol, period="1d", interval="5m", progress=False)
                
                if not df_i.empty and len(df_i) > 5:
                    # Limpiar columnas multi-index si existen
                    if isinstance(df_i.columns, pd.MultiIndex):
                        df_i.columns = df_i.columns.get_level_values(0)
                    
                    # Calcular VWAP
                    tp = (df_i['High'] + df_i['Low'] + df_i['Close']) / 3
                    df_i['VWAP'] = (tp * df_i['Volume']).cumsum() / df_i['Volume'].cumsum()
                    
                    # Calcular desviación
                    current_price = df_i['Close'].iloc[-1]
                    vwap = df_i['VWAP'].iloc[-1]
                    deviation = ((current_price - vwap) / vwap) * 100
                    
                    # Métricas
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("Precio Actual", f"${current_price:.2f}")
                    with cols[1]:
                        st.metric("VWAP", f"${vwap:.2f}")
                    with cols[2]:
                        st.metric("Desviación", f"{deviation:+.2f}%", 
                                 delta="Sobre VWAP" if deviation > 0 else "Bajo VWAP")
                    
                    # Gráfico
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df_i.index,
                        open=df_i['Open'],
                        high=df_i['High'],
                        low=df_i['Low'],
                        close=df_i['Close'],
                        name=symbol
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_i.index,
                        y=df_i['VWAP'],
                        line=dict(color='#ffaa00', width=2, dash='dash'),
                        name="VWAP"
                    ))
                    
                    # Zonas
                    fig.add_hrect(y0=vwap*0.99, y1=vwap*1.01, 
                                 fillcolor="rgba(255,170,0,0.1)", line_width=0,
                                 annotation_text="Zona VWAP")
                    
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor='#11141a',
                        plot_bgcolor='#0c0e12',
                        font_color='white',
                        height=450,
                        xaxis_rangeslider_visible=False,
                        margin=dict(l=0, r=0, b=0, t=30),
                        title=f"{symbol} - Análisis Intradía"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Señal
                    if deviation > 1:
                        st.success(f"✅ **{symbol}** muestra fuerza sobre VWAP (+{deviation:.1f}%). Sesgo alcista confirmado.")
                    elif deviation < -1:
                        st.error(f"⚠️ **{symbol}** bajo VWAP ({deviation:.1f}%). Debilidad intradía o pullback saludable.")
                    else:
                        st.info(f"➖ **{symbol}** en equilibrio respecto a VWAP ({deviation:.1f}%). Esperar breakout.")
                        
                else:
                    st.warning(f"No hay datos suficientes para {symbol}. Mercado puede estar cerrado.")
                    
            except Exception as e:
                st.error(f"Error al cargar {symbol}: {e}")
