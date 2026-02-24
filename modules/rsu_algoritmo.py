# modules/rsu_algoritmo_pro.py
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import set_style

def calcular_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calcular_mcclellan_oscillator(df_breadth):
    """
    Calcula el McClellan Oscillator (breadth indicator).
    Requiere datos de advancing/declining issues.
    Simplificado: usamos ratio de stocks sobre/bajo medias móviles como proxy.
    """
    if df_breadth is None:
        return None
    
    # Proxy: % de stocks sobre SMA 50
    advances = (df_breadth['Close'] > df_breadth['Close'].rolling(50).mean()).sum()
    declines = (df_breadth['Close'] < df_breadth['Close'].rolling(50).mean()).sum()
    total = advances + declines
    
    if total == 0:
        return None
    
    net_advances = ((advances - declines) / total) * 1000
    
    # EMAs 19 y 39
    ema_19 = pd.Series(net_advances).ewm(span=19, adjust=False).mean()
    ema_39 = pd.Series(net_advances).ewm(span=39, adjust=False).mean()
    
    return ema_19.iloc[-1] - ema_39.iloc[-1] if len(ema_19) > 0 else None

def detectar_fondo_comprehensivo(df_spy, df_vix=None, df_breadth=None):
    """
    Sistema de detección de fondos multi-factor.
    
    Factores (pesos):
    1. FTD (30%): Confirmación de cambio de tendencia O'Neil
    2. RSI Diario < 35 (25%): Sobreventa extrema
    3. VIX Spike > 30 (20%): Miedo extremo (contrarian)
    4. McClellan Oscillator < -50 luego thrust (15%): Breadth thrust
    5. Put/Call Ratio > 1.2 (10%): Sentimiento extremo bajista
    
    Score > 70% = Fondo probable (Semáforo Verde)
    Score 40-70% = Condiciones desarrollándose (Ámbar)
    Score < 40% = Sin fondo detectado (Rojo)
    """
    score = 0
    detalles = []
    
    # 1. FTD Detection (30 puntos)
    ftd_data = detectar_follow_through_day(df_spy)
    if ftd_data and ftd_data.get('signal') == 'confirmed':
        score += 30
        detalles.append("✓ FTD Confirmado (+30)")
    elif ftd_data and ftd_data.get('signal') in ['potential', 'early']:
        score += 15
        detalles.append("~ FTD en desarrollo (+15)")
    
    # 2. RSI Diario (25 puntos)
    rsi = calcular_rsi(df_spy['Close'], 14).iloc[-1]
    if rsi < 30:
        score += 25
        detalles.append("✓ RSI < 30 (Sobreventa extrema) (+25)")
    elif rsi < 40:
        score += 15
        detalles.append("~ RSI < 40 (Sobreventa) (+15)")
    elif rsi > 70:
        score -= 10
        detalles.append("✗ RSI > 70 (Sobrecompra) (-10)")
    
    # 3. VIX Analysis (20 puntos) - Proxy usando ATR si no hay VIX
    if df_vix is not None and len(df_vix) > 20:
        vix_actual = df_vix['Close'].iloc[-1]
        vix_sma20 = df_vix['Close'].rolling(20).mean().iloc[-1]
        
        if vix_actual > 30:
            score += 20
            detalles.append("✓ VIX > 30 (Miedo extremo) (+20)")
        elif vix_actual > vix_sma20 * 1.5:
            score += 15
            detalles.append("~ VIX elevado vs media (+15)")
    else:
        # Proxy: ATR de SPY
        atr = calcular_atr(df_spy).iloc[-1]
        atr_medio = calcular_atr(df_spy).rolling(20).mean().iloc[-1]
        if atr > atr_medio * 1.5:
            score += 10
            detalles.append("~ Volatilidad elevada (proxy VIX) (+10)")
    
    # 4. McClellan Oscillator (15 puntos)
    mcclellan = calcular_mcclellan_oscillator(df_breadth if df_breadth is not None else df_spy)
    if mcclellan is not None:
        if mcclellan < -50:
            score += 15
            detalles.append("✓ McClellan < -50 (Oversold breadth) (+15)")
        elif mcclellan < -20:
            score += 8
            detalles.append("~ McClellan < -20 (+8)")
    
    # 5. Volume Analysis como proxy de Put/Call (10 puntos)
    vol_actual = df_spy['Volume'].iloc[-1]
    vol_media = df_spy['Volume'].rolling(20).mean().iloc[-1]
    if vol_actual > vol_media * 1.5:
        score += 10
        detalles.append("✓ Volumen extremo (posible capitulación) (+10)")
    
    # Determinar estado
    if score >= 70:
        estado = "VERDE"
        senal = "FONDO PROBABLE"
        color = "#00ffad"
        recomendacion = "Considerar entrada gradual (25% posición inicial)"
    elif score >= 40:
        estado = "AMBAR"
        senal = "DESARROLLANDO"
        color = "#ff9800"
        recomendacion = "Preparar watchlist, esperar confirmación adicional"
    else:
        estado = "ROJO"
        senal = "SIN FONDO"
        color = "#f23645"
        recomendacion = "Mantener efectivo, evitar compras agresivas"
    
    return {
        'score': score,
        'estado': estado,
        'senal': senal,
        'color': color,
        'recomendacion': recomendacion,
        'detalles': detalles,
        'ftd_data': ftd_data,
        'rsi': rsi,
        'mcclellan': mcclellan,
        'metricas': {
            'FTD': 30 if ftd_data and ftd_data.get('signal') == 'confirmed' else 0,
            'RSI': 25 if rsi < 30 else (15 if rsi < 40 else 0),
            'VIX/Vol': 20 if (df_vix is not None and df_vix['Close'].iloc[-1] > 30) else 0,
            'Breadth': 15 if (mcclellan is not None and mcclellan < -50) else 0,
            'Volume': 10 if vol_actual > vol_media * 1.5 else 0
        }
    }

def calcular_atr(df, periodo=14):
    """Calcula Average True Range"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=periodo).mean()

def detectar_follow_through_day(df_daily):
    """Versión mejorada del FTD detection"""
    if df_daily is None or len(df_daily) < 20:
        return None
    
    df = df_daily.copy()
    df['returns'] = df['Close'].pct_change()
    df['volume_prev'] = df['Volume'].shift(1)
    df['volume_increase'] = df['Volume'] > df['volume_prev']
    df['price_up'] = df['returns'] > 0
    
    recent = df.tail(60).copy()
    recent_low = recent['Close'].min()
    recent_low_idx = recent['Close'].idxmin()
    current_price = df['Close'].iloc[-1]
    distancia_minimo = (current_price - recent_low) / recent_low
    
    if distancia_minimo > 0.10:
        return {'estado': 'NO_CONTEXT', 'signal': None}
    
    min_idx_pos = recent.index.get_loc(recent_low_idx)
    if min_idx_pos >= len(recent) - 2:
        return {'estado': 'RALLY_TOO_RECENT', 'signal': None}
    
    post_low = recent.iloc[min_idx_pos:].copy()
    
    # Encontrar día 1 del rally
    rally_start_idx = None
    for i in range(1, len(post_low)):
        if post_low['price_up'].iloc[i]:
            rally_start_idx = i
            break
    
    if rally_start_idx is None:
        return {'estado': 'NO_RALLY', 'signal': None}
    
    dias_rally = len(post_low) - rally_start_idx
    low_dia_1 = post_low.iloc[rally_start_idx]['Low']
    
    # Validar que no se rompió el low del día 1
    for i in range(rally_start_idx + 1, len(post_low)):
        if post_low.iloc[i]['Low'] < low_dia_1:
            return {'estado': 'RALLY_FAILED', 'signal': 'invalidated', 'dias_rally': dias_rally}
    
    # Verificar FTD
    if 4 <= dias_rally <= 10:
        ultimo_dia = post_low.iloc[-1]
        ret_ultimo = ultimo_dia['returns'] * 100
        
        if ret_ultimo >= 1.5 and ultimo_dia['volume_increase']:
            return {
                'estado': 'FTD_CONFIRMED',
                'signal': 'confirmed',
                'dias_rally': dias_rally,
                'retorno': ret_ultimo,
                'color': '#00ffad'
            }
    
    return {'estado': 'RALLY_ACTIVE', 'signal': 'active', 'dias_rally': dias_rally}

def backtest_strategy(df_historical, ventana=20):
    """
    Backtesting simple de la estrategia.
    Detecta señales VERDE y calcula retorno a 20 días.
    """
    señales = []
    
    for i in range(60, len(df_historical) - ventana):
        ventana_df = df_historical.iloc[:i]
        resultado = detectar_fondo_comprehensivo(ventana_df)
        
        if resultado['estado'] == 'VERDE':
            precio_entrada = df_historical['Close'].iloc[i]
            precio_salida = df_historical['Close'].iloc[i + ventana]
            retorno = (precio_salida - precio_entrada) / precio_entrada
            
            señales.append({
                'fecha': df_historical.index[i],
                'score': resultado['score'],
                'precio_entrada': precio_entrada,
                'precio_salida': precio_salida,
                'retorno_20d': retorno * 100,
                'exito': retorno > 0
            })
    
    if not señales:
        return None
    
    df_resultados = pd.DataFrame(señales)
    win_rate = df_resultados['exito'].mean() * 100
    retorno_medio = df_resultados['retorno_20d'].mean()
    retorno_total = df_resultados['retorno_20d'].sum()
    
    return {
        'total_señales': len(señales),
        'win_rate': win_rate,
        'retorno_medio': retorno_medio,
        'retorno_total': retorno_total,
        'detalle': df_resultados
    }

def render():
    set_style()
    
    st.markdown("""
    <style>
    .rsu-box { background: #11141a; border: 1px solid #1a1e26; border-radius: 10px; margin-bottom: 20px; }
    .rsu-head { background: #0c0e12; padding: 15px 20px; border-bottom: 1px solid #1a1e26; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .rsu-title { color: white; font-size: 16px; font-weight: bold; margin: 0; }
    .rsu-body { padding: 20px; }
    .rsu-luz { width: 80px; height: 80px; border-radius: 50%; border: 4px solid #1a1e26; background: #0c0e12; margin: 10px auto; }
    .rsu-luz.on { box-shadow: 0 0 30px currentColor; transform: scale(1.1); }
    .rsu-luz.red { color: #f23645; }
    .rsu-luz.red.on { background: radial-gradient(circle at 30% 30%, #ff6b6b, #f23645); border-color: #f23645; }
    .rsu-luz.yel { color: #ff9800; }
    .rsu-luz.yel.on { background: radial-gradient(circle at 30% 30%, #ffb74d, #ff9800); border-color: #ff9800; }
    .rsu-luz.grn { color: #00ffad; }
    .rsu-luz.grn.on { background: radial-gradient(circle at 30% 30%, #69f0ae, #00ffad); border-color: #00ffad; }
    .rsu-center { text-align: center; }
    .score-big { font-size: 3rem; font-weight: bold; color: white; text-align: center; margin: 20px 0; }
    .score-label { color: #888; font-size: 12px; text-align: center; text-transform: uppercase; }
    .factor-box { background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 12px; margin: 8px 0; }
    .factor-title { color: #888; font-size: 11px; text-transform: uppercase; margin-bottom: 4px; }
    .factor-value { color: white; font-size: 14px; font-weight: bold; }
    .recommendation-box { background: rgba(0, 255, 173, 0.1); border-left: 4px solid #00ffad; padding: 15px; margin-top: 20px; border-radius: 0 8px 8px 0; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="max-width:1200px;margin:0 auto;padding:20px;">', unsafe_allow_html=True)
    
    # Header
    st.markdown("<h1 style='color:white;margin-bottom:5px;'>🚦 RSU ALGORITMO PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#888;font-size:14px;margin-top:0;'>Detección de Fondos Multi-Factor (FTD + RSI + VIX + Breadth)</p>", unsafe_allow_html=True)
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["📊 Análisis Actual", "📈 Backtesting", "ℹ️ Metodología"])
    
    with tab1:
        with st.spinner('Analizando múltiples factores...'):
            # Obtener datos
            ticker = yf.Ticker("SPY")
            df_daily = ticker.history(interval="1d", period="6mo")
            
            # Intentar obtener VIX
            try:
                vix = yf.Ticker("^VIX")
                df_vix = vix.history(interval="1d", period="6mo")
            except:
                df_vix = None
            
            resultado = detectar_fondo_comprehensivo(df_daily, df_vix)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Semáforo con Score
            luz_r = "on" if resultado['estado'] == "ROJO" else ""
            luz_a = "on" if resultado['estado'] == "AMBAR" else ""
            luz_v = "on" if resultado['estado'] == "VERDE" else ""
            
            st.markdown(f"""
            <div class="rsu-box">
                <div class="rsu-head">
                    <span class="rsu-title">Señal Integrada</span>
                    <span style="color:{resultado['color']};font-size:12px;font-weight:bold;">● {resultado['estado']}</span>
                </div>
                <div class="rsu-body rsu-center">
                    <div class="rsu-luz red {luz_r}"></div>
                    <div class="rsu-luz yel {luz_a}"></div>
                    <div class="rsu-luz grn {luz_v}"></div>
                    <div class="score-big" style="color:{resultado['color']};">{resultado['score']}/100</div>
                    <div class="score-label">Puntuación de Confianza</div>
                    <div style="background:{resultado['color']}22;border:2px solid {resultado['color']};color:{resultado['color']};padding:10px 20px;border-radius:8px;font-weight:bold;margin-top:15px;display:inline-block;">
                        {resultado['senal']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Factores desglosados
            st.markdown('<div class="rsu-box"><div class="rsu-head"><span class="rsu-title">Desglose de Factores</span></div><div class="rsu-body">', unsafe_allow_html=True)
            
            factores = [
                ("Follow-Through Day", resultado['metricas']['FTD'], 30, "#2962ff"),
                ("RSI Diario < 35", resultado['metricas']['RSI'], 25, "#00ffad"),
                ("VIX Extremo", resultado['metricas']['VIX/Vol'], 20, "#ff9800"),
                ("Breadth Thrust", resultado['metricas']['Breadth'], 15, "#9c27b0"),
                ("Volumen Capitulación", resultado['metricas']['Volume'], 10, "#f23645")
            ]
            
            for nombre, valor, maximo, color in factores:
                porcentaje = (valor / maximo) * 100 if maximo > 0 else 0
                st.markdown(f"""
                <div class="factor-box">
                    <div class="factor-title">{nombre} (max {maximo} pts)</div>
                    <div style="display:flex;align-items:center;gap:10px;margin-top:5px;">
                        <div style="flex:1;height:8px;background:#1a1e26;border-radius:4px;overflow:hidden;">
                            <div style="width:{porcentaje}%;height:100%;background:{color};border-radius:4px;"></div>
                        </div>
                        <div style="color:{color};font-weight:bold;min-width:30px;text-align:right;">{valor}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Recomendación
        st.markdown(f"""
        <div class="recommendation-box">
            <div style="color:#00ffad;font-weight:bold;margin-bottom:5px;">📋 RECOMENDACIÓN ESTRATÉGICA</div>
            <div style="color:#ccc;font-size:14px;">{resultado['recomendacion']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Detalles técnicos
        with st.expander("Ver detalles técnicos"):
            for detalle in resultado['detalles']:
                st.write(detalle)
    
    with tab2:
        st.markdown("### 📊 Backtesting Histórico")
        st.write("Análisis de performance de señales VERDE en los últimos 2 años")
        
        if st.button("Ejecutar Backtest", type="primary"):
            with st.spinner('Calculando... (puede tomar un minuto)'):
                # Obtener 2 años de datos
                df_hist = ticker.history(interval="1d", period="2y")
                resultados_bt = backtest_strategy(df_hist)
                
                if resultados_bt:
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Señales", resultados_bt['total_señales'])
                    col2.metric("Win Rate", f"{resultados_bt['win_rate']:.1f}%")
                    col3.metric("Retorno Medio", f"{resultados_bt['retorno_medio']:.2f}%")
                    col4.metric("Retorno Total", f"{resultados_bt['retorno_total']:.2f}%")
                    
                    st.line_chart(resultados_bt['detalle'].set_index('fecha')['retorno_20d'])
                    
                    st.write("**Detalle de operaciones:**")
                    st.dataframe(resultados_bt['detalle'])
                else:
                    st.warning("No se generaron señales VERDE en el período analizado")
    
    with tab3:
        st.markdown("""
        ### 🔬 Metodología Científica
        
        **ADVERTENCIA**: Esta herramienta es un asistente de análisis, no un oráculo. El market timing es estadísticamente desafiante.
        
        #### 1. Follow-Through Day (30%)
        Basado en William O'Neil (CANSLIM). Un FTD válido ocurre entre el día 4-7 después de un mínimo, con +1.5% de subida y volumen creciente. 
        *Limitación*: ~30% de los FTD fallan según estudios históricos [^5^].
        
        #### 2. RSI Diario (25%)
        Índice de Fuerza Relativa de 14 períodos. < 30 indica sobreventa.
        *Limitación*: El mercado puede permanecer sobrecomprado/sobrevento por semanas.
        
        #### 3. VIX / Volatilidad (20%)
        El "índice de miedo". Lecturas > 30 indican pánico, típicamente asociadas con fondos.
        *Limitación*: El VIX puede quedarse elevado por meses (ej. 2008-2009).
        
        #### 4. McClellan Oscillator (15%)
        Breadth indicator. Mide la amplitud del mercado. Un thrust de -50 a +50 confirma fuerza.
        *Limitación*: Requiere datos de advancing/declining issues; nuestro cálculo es un proxy.
        
        #### 5. Volumen de Capitulación (10%)
        Picos de volumen > 1.5x la media sugieren capitulación (agotamiento vendedor).
        
        #### Reglas de Integración
        - **Score > 70**: Múltiples factores alineados. Fondo probable, pero no garantizado.
        - **Score 40-70**: Algunos factores presentes. Esperar confirmación.
        - **Score < 40**: Sin condiciones de fondo. Preservar capital.
        
        #### Gestión de Riesgo Recomendada
        1. Nunca arriesgar > 2% del capital en una señal
        2. Stop-loss obligatorio: -7% debajo del punto de entrada
        3. Entrada gradual: 25% inicial, escalonar si funciona
        4. Time-stop: Si no sube en 10 días, reconsiderar
        
        #### Referencias
        - O'Neil, W. (2009). How to Make Money in Stocks
        - McClellan, S. & M. (1998). Patterns for Profit
        - Investopedia (2025). Put-Call Ratio Analysis [^37^]
        - StockCharts (2025). McClellan Oscillator [^39^]
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)



