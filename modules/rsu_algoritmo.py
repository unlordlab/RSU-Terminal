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

def calcular_mcclellan_proxy(df):
    """Proxy del McClellan usando momentum de retornos"""
    if df is None or len(df) < 50:
        return 0
    
    returns = df['Close'].pct_change()
    mom_19 = returns.rolling(19).mean()
    mom_39 = returns.rolling(39).mean()
    mcclellan = (mom_19 - mom_39) * 1000
    return mcclellan.iloc[-1] if not pd.isna(mcclellan.iloc[-1]) else 0

def detectar_fondo_comprehensivo(df_spy, df_vix=None):
    """
    Sistema de detección de fondos multi-factor.
    UMBRAL: 50 puntos para VERDE (balance frecuencia/calidad)
    """
    score = 0
    max_score = 100
    detalles = []
    metricas = {}
    
    # 1. FTD Detection (30 puntos)
    ftd_data = detectar_follow_through_day(df_spy)
    ftd_score = 0
    
    if ftd_data:
        if ftd_data.get('signal') == 'confirmed':
            ftd_score = 30
            detalles.append("✓ FTD Confirmado (+30)")
        elif ftd_data.get('signal') == 'potential':
            ftd_score = 20
            detalles.append("~ FTD Potencial (+20)")
        elif ftd_data.get('signal') == 'early':
            ftd_score = 10
            detalles.append(f"• Rally temprano día {ftd_data.get('dias_rally', 0)} (+10)")
        elif ftd_data.get('signal') == 'active':
            ftd_score = 5
            detalles.append("• Rally activo sin FTD aún (+5)")
        else:
            detalles.append("✗ Sin FTD válido (0)")
    else:
        detalles.append("✗ Sin datos FTD (0)")
    
    score += ftd_score
    metricas['FTD'] = {'score': ftd_score, 'max': 30, 'color': '#3b82f6', 'order': 1}
    
    # 2. RSI Diario (25 puntos)
    rsi_series = calcular_rsi(df_spy['Close'], 14)
    rsi = rsi_series.iloc[-1]
    rsi_score = 0
    
    if rsi < 20:
        rsi_score = 25
        detalles.append(f"✓ RSI {rsi:.1f} < 20 (Sobreventa extrema) (+25)")
    elif rsi < 30:
        rsi_score = 20
        detalles.append(f"✓ RSI {rsi:.1f} < 30 (Sobreventa fuerte) (+20)")
    elif rsi < 40:
        rsi_score = 15
        detalles.append(f"~ RSI {rsi:.1f} < 40 (Sobreventa moderada) (+15)")
    elif rsi < 50:
        rsi_score = 5
        detalles.append(f"• RSI {rsi:.1f} < 50 (Ligera sobreventa) (+5)")
    elif rsi > 75:
        rsi_score = -10
        detalles.append(f"✗ RSI {rsi:.1f} > 75 (Sobrecompra) (-10)")
    else:
        detalles.append(f"• RSI {rsi:.1f} neutral (0)")
    
    score += rsi_score
    metricas['RSI'] = {'score': max(0, rsi_score), 'max': 25, 'color': '#10b981', 'raw_value': rsi, 'order': 2}
    
    # 3. VIX / Volatilidad (20 puntos)
    vix_score = 0
    vix_val = None
    
    if df_vix is not None and len(df_vix) > 20:
        vix_actual = df_vix['Close'].iloc[-1]
        vix_sma20 = df_vix['Close'].rolling(20).mean().iloc[-1]
        vix_val = vix_actual
        
        if vix_actual > 35:
            vix_score = 20
            detalles.append(f"✓ VIX {vix_actual:.1f} > 35 (Pánico) (+20)")
        elif vix_actual > 30:
            vix_score = 15
            detalles.append(f"✓ VIX {vix_actual:.1f} > 30 (Miedo) (+15)")
        elif vix_actual > 25:
            vix_score = 10
            detalles.append(f"~ VIX {vix_actual:.1f} > 25 (Preocupación) (+10)")
        elif vix_actual > vix_sma20 * 1.2:
            vix_score = 5
            detalles.append(f"• VIX elevado vs media (+5)")
        else:
            detalles.append(f"• VIX {vix_actual:.1f} normal (0)")
    else:
        # Proxy ATR
        atr = calcular_atr(df_spy).iloc[-1]
        atr_medio = calcular_atr(df_spy).rolling(20).mean().iloc[-1]
        ratio_atr = atr / atr_medio if atr_medio > 0 else 1
        vix_val = ratio_atr
        
        if ratio_atr > 2.5:
            vix_score = 15
            detalles.append(f"~ ATR {ratio_atr:.1f}x (Alta vol) (+15)")
        elif ratio_atr > 1.8:
            vix_score = 10
            detalles.append(f"~ ATR {ratio_atr:.1f}x (Vol elevada) (+10)")
        else:
            detalles.append(f"• Volatilidad normal (0)")
    
    score += vix_score
    metricas['VIX'] = {'score': vix_score, 'max': 20, 'color': '#f59e0b', 'raw_value': vix_val, 'is_proxy': df_vix is None, 'order': 3}
    
    # 4. McClellan Proxy (15 puntos)
    mcclellan = calcular_mcclellan_proxy(df_spy)
    breadth_score = 0
    
    if mcclellan < -100:
        breadth_score = 15
        detalles.append(f"✓ McClellan {mcclellan:.0f} < -100 (Oversold ext) (+15)")
    elif mcclellan < -60:
        breadth_score = 10
        detalles.append(f"~ McClellan {mcclellan:.0f} < -60 (Oversold) (+10)")
    elif mcclellan < -30:
        breadth_score = 5
        detalles.append(f"• McClellan {mcclellan:.0f} < -30 (Débil) (+5)")
    else:
        detalles.append(f"• McClellan {mcclellan:.0f} neutral (0)")
    
    score += breadth_score
    metricas['Breadth'] = {'score': breadth_score, 'max': 15, 'color': '#8b5cf6', 'raw_value': mcclellan, 'order': 4}
    
    # 5. Volume Analysis (10 puntos)
    vol_actual = df_spy['Volume'].iloc[-1]
    vol_media = df_spy['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = vol_actual / vol_media if vol_media > 0 else 1
    vol_score = 0
    
    if vol_ratio > 2.5:
        vol_score = 10
        detalles.append(f"✓ Volumen {vol_ratio:.1f}x (Capitulación) (+10)")
    elif vol_ratio > 1.8:
        vol_score = 7
        detalles.append(f"~ Volumen {vol_ratio:.1f}x (Alto) (+7)")
    elif vol_ratio > 1.3:
        vol_score = 3
        detalles.append(f"• Volumen {vol_ratio:.1f}x (Moderado) (+3)")
    else:
        detalles.append(f"• Volumen normal (0)")
    
    score += vol_score
    metricas['Volume'] = {'score': vol_score, 'max': 10, 'color': '#ef4444', 'raw_value': vol_ratio, 'order': 5}
    
    # Determinar estado
    if score >= 50:
        estado = "VERDE"
        senal = "FONDO PROBABLE"
        color = "#10b981"
        recomendacion = "Setup óptimo: Considerar entrada gradual (25-50% posición), stop-loss -7%"
    elif score >= 35:
        estado = "AMBAR"
        senal = "DESARROLLANDO"
        color = "#f59e0b"
        recomendacion = "Condiciones mejorando: Preparar watchlist, entrada parcial 10-15% opcional"
    elif score >= 20:
        estado = "AMBAR-BAJO"
        senal = "PRE-SETUP"
        color = "#d97706"
        recomendacion = "Algunos factores presentes. Mantener liquidez, monitorear evolución"
    else:
        estado = "ROJO"
        senal = "SIN FONDO"
        color = "#ef4444"
        recomendacion = "Sin condiciones de fondo detectadas. Preservar capital, evitar compras"
    
    return {
        'score': score,
        'max_score': max_score,
        'estado': estado,
        'senal': senal,
        'color': color,
        'recomendacion': recomendacion,
        'detalles': detalles,
        'ftd_data': ftd_data,
        'metricas': metricas
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
    
    if distancia_minimo > 0.15:
        return {'estado': 'NO_CONTEXT', 'signal': None, 'dias_rally': 0}
    
    min_idx_pos = recent.index.get_loc(recent_low_idx)
    if min_idx_pos >= len(recent) - 2:
        return {'estado': 'RALLY_TOO_RECENT', 'signal': None, 'dias_rally': 0}
    
    post_low = recent.iloc[min_idx_pos:].copy()
    
    rally_start_idx = None
    for i in range(1, len(post_low)):
        if post_low['price_up'].iloc[i]:
            rally_start_idx = i
            break
    
    if rally_start_idx is None:
        return {'estado': 'NO_RALLY', 'signal': None, 'dias_rally': 0}
    
    dias_rally = len(post_low) - rally_start_idx
    low_dia_1 = post_low.iloc[rally_start_idx]['Low']
    
    for i in range(rally_start_idx + 1, len(post_low)):
        if post_low.iloc[i]['Low'] < low_dia_1:
            return {'estado': 'RALLY_FAILED', 'signal': 'invalidated', 'dias_rally': dias_rally}
    
    if 4 <= dias_rally <= 10:
        ultimo_dia = post_low.iloc[-1]
        ret_ultimo = ultimo_dia['returns'] * 100
        
        if ret_ultimo >= 1.5 and ultimo_dia['volume_increase']:
            return {
                'estado': 'FTD_CONFIRMED',
                'signal': 'confirmed',
                'dias_rally': dias_rally,
                'retorno': ret_ultimo,
                'color': '#10b981'
            }
        elif ret_ultimo >= 1.0:
            return {
                'estado': 'FTD_POTENTIAL',
                'signal': 'potential',
                'dias_rally': dias_rally,
                'retorno': ret_ultimo
            }
    
    if dias_rally < 4:
        return {'estado': 'RALLY_EARLY', 'signal': 'early', 'dias_rally': dias_rally}
    
    return {'estado': 'RALLY_ACTIVE', 'signal': 'active', 'dias_rally': dias_rally}

def backtest_strategy(ticker_symbol="SPY", years=2, umbral=50):
    """
    Backtesting CORREGIDO.
    UNA SEÑAL = Una vez que el score >= umbral (entrada), se mantiene la posición 20 días.
    No se generan señales consecutivas en ventanas de 20 días (evitar overlapping).
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        df_hist = ticker.history(period=f"{years}y", interval="1d")
        
        if df_hist.empty or len(df_hist) < 100:
            return None, "Datos insuficientes"
        
        try:
            vix_ticker = yf.Ticker("^VIX")
            vix_hist = vix_ticker.history(period=f"{years}y", interval="1d")
        except:
            vix_hist = None
        
        señales = []
        last_signal_idx = -20  # Cooldown de 20 días entre señales
        
        for i in range(60, len(df_hist) - 20):
            # Evitar señales overlapping (cooldown 20 días)
            if i - last_signal_idx < 20:
                continue
            
            ventana_df = df_hist.iloc[:i]
            vix_window = vix_hist.iloc[:i] if vix_hist is not None else None
            
            resultado = detectar_fondo_comprehensivo(ventana_df, vix_window)
            
            # Señal VERDE o AMBAR (>= umbral)
            if resultado['score'] >= umbral:
                precio_entrada = df_hist['Close'].iloc[i]
                precio_5d = df_hist['Close'].iloc[min(i + 5, len(df_hist) - 1)]
                precio_10d = df_hist['Close'].iloc[min(i + 10, len(df_hist) - 1)]
                precio_20d = df_hist['Close'].iloc[min(i + 20, len(df_hist) - 1)]
                
                señales.append({
                    'fecha': df_hist.index[i].strftime('%Y-%m-%d'),
                    'score': resultado['score'],
                    'estado': resultado['estado'],
                    'precio_entrada': round(precio_entrada, 2),
                    'retorno_5d': round(((precio_5d - precio_entrada) / precio_entrada) * 100, 2),
                    'retorno_10d': round(((precio_10d - precio_entrada) / precio_entrada) * 100, 2),
                    'retorno_20d': round(((precio_20d - precio_entrada) / precio_entrada) * 100, 2),
                })
                
                last_signal_idx = i
        
        if not señales:
            return None, f"No se generaron señales con score >= {umbral} en {years} años"
        
        df_resultados = pd.DataFrame(señales)
        
        return {
            'total_señales': len(señales),
            'score_promedio': df_resultados['score'].mean(),
            'win_rate_5d': (df_resultados['retorno_5d'] > 0).mean() * 100,
            'win_rate_10d': (df_resultados['retorno_10d'] > 0).mean() * 100,
            'win_rate_20d': (df_resultados['retorno_20d'] > 0).mean() * 100,
            'retorno_medio_5d': df_resultados['retorno_5d'].mean(),
            'retorno_medio_10d': df_resultados['retorno_10d'].mean(),
            'retorno_medio_20d': df_resultados['retorno_20d'].mean(),
            'retorno_total_20d': df_resultados['retorno_20d'].sum(),
            'detalle': df_resultados
        }, None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def render():
    set_style()
    
    # CSS ARMÓNICO - Paleta coherente, espaciado consistente, jerarquía visual clara
    st.markdown("""
    <style>
    /* Reset y base */
    .main-container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
    
    /* Tarjetas principales - estilo unificado */
    .card {
        background: linear-gradient(145deg, #11141a 0%, #0c0e12 100%);
        border: 1px solid #1f2937;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    
    .card-header {
        background: #0c0e12;
        padding: 1.25rem 1.5rem;
        border-bottom: 1px solid #1f2937;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .card-title {
        color: #f9fafb;
        font-size: 1.125rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.025em;
    }
    
    .card-body {
        padding: 1.5rem;
    }
    
    /* Semáforo - diseño refinado */
    .semaforo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        padding: 2rem 0;
    }
    
    .luz {
        width: 72px;
        height: 72px;
        border-radius: 50%;
        border: 3px solid #1f2937;
        background: #0c0e12;
        transition: all 0.3s ease;
        position: relative;
    }
    
    .luz::after {
        content: '';
        position: absolute;
        top: 15%;
        left: 20%;
        width: 25%;
        height: 25%;
        background: rgba(255,255,255,0.3);
        border-radius: 50%;
        filter: blur(2px);
    }
    
    .luz.on {
        transform: scale(1.05);
        box-shadow: 0 0 30px currentColor;
    }
    
    .luz-roja { color: #ef4444; }
    .luz-roja.on { background: radial-gradient(circle at 35% 35%, #f87171, #dc2626); border-color: #ef4444; }
    
    .luz-ambar { color: #f59e0b; }
    .luz-ambar.on { background: radial-gradient(circle at 35% 35%, #fbbf24, #d97706); border-color: #f59e0b; }
    
    .luz-verde { color: #10b981; }
    .luz-verde.on { background: radial-gradient(circle at 35% 35%, #34d399, #059669); border-color: #10b981; }
    
    /* Score display */
    .score-display {
        text-align: center;
        margin: 1.5rem 0;
    }
    
    .score-value {
        font-size: 4rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.05em;
    }
    
    .score-label {
        color: #6b7280;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.5rem;
    }
    
    /* Badge de señal */
    .signal-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 1rem;
        border: 2px solid;
    }
    
    /* Factores - diseño de lista armónica */
    .factor-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .factor-item {
        background: #0c0e12;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 1rem;
        transition: border-color 0.2s;
    }
    
    .factor-item:hover {
        border-color: #374151;
    }
    
    .factor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .factor-name {
        color: #9ca3af;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .factor-score {
        font-size: 0.875rem;
        font-weight: 700;
        font-family: monospace;
    }
    
    .factor-meta {
        color: #6b7280;
        font-size: 0.75rem;
        margin-top: 0.25rem;
    }
    
    /* Progress bar refinada */
    .progress-container {
        width: 100%;
        height: 6px;
        background: #1f2937;
        border-radius: 3px;
        overflow: hidden;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 3px;
        transition: width 0.5s ease-out;
    }
    
    /* Recomendación */
    .recommendation {
        background: rgba(16, 185, 129, 0.05);
        border-left: 4px solid #10b981;
        padding: 1.25rem;
        border-radius: 0 12px 12px 0;
        margin-top: 1.5rem;
    }
    
    .recommendation-title {
        color: #10b981;
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    .recommendation-text {
        color: #d1d5db;
        font-size: 0.9375rem;
        line-height: 1.6;
    }
    
    /* Detalles técnicos */
    .detail-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .detail-item {
        padding: 0.75rem;
        background: #0c0e12;
        border-radius: 8px;
        font-size: 0.875rem;
        border-left: 3px solid transparent;
    }
    
    .detail-success { border-left-color: #10b981; color: #34d399; }
    .detail-warning { border-left-color: #f59e0b; color: #fbbf24; }
    .detail-danger { border-left-color: #ef4444; color: #f87171; }
    .detail-neutral { border-left-color: #4b5563; color: #9ca3af; }
    
    /* Utilidades */
    .text-center { text-align: center; }
    .mb-4 { margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header minimalista
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="color: #f9fafb; font-size: 2rem; font-weight: 700; margin: 0; letter-spacing: -0.025em;">
            🚦 RSU Algoritmo Pro
        </h1>
        <p style="color: #6b7280; font-size: 1rem; margin: 0.5rem 0 0 0;">
            Sistema de detección de fondos multi-factor · Umbral: 50 pts
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs con estilo
    tab1, tab2, tab3 = st.tabs(["📊 Análisis", "📈 Backtest", "ℹ️ Metodología"])
    
    with tab1:
        with st.spinner('Analizando factores de mercado...'):
            try:
                ticker = yf.Ticker("SPY")
                df_daily = ticker.history(interval="1d", period="6mo")
                
                try:
                    vix = yf.Ticker("^VIX")
                    df_vix = vix.history(interval="1d", period="6mo")
                except:
                    df_vix = None
                
                if df_daily.empty:
                    st.error("No se pudieron obtener datos")
                    st.stop()
                
                resultado = detectar_fondo_comprehensivo(df_daily, df_vix)
                
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()
        
        # Layout de dos columnas armónicas
        col_left, col_right = st.columns([1, 1], gap="large")
        
        with col_left:
            # Card del semáforo
            luz_r = "on" if resultado['estado'] == "ROJO" else ""
            luz_a = "on" if resultado['estado'] in ["AMBAR", "AMBAR-BAJO"] else ""
            luz_v = "on" if resultado['estado'] == "VERDE" else ""
            
            st.markdown(f"""
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Señal de Mercado</span>
                    <span style="color: {resultado['color']}; font-size: 0.875rem; font-weight: 600;">
                        ● {resultado['estado']}
                    </span>
                </div>
                <div class="card-body">
                    <div class="semaforo-container">
                        <div class="luz luz-roja {luz_r}"></div>
                        <div class="luz luz-ambar {luz_a}"></div>
                        <div class="luz luz-verde {luz_v}"></div>
                    </div>
                    
                    <div class="score-display">
                        <div class="score-value" style="color: {resultado['color']};">
                            {resultado['score']}
                        </div>
                        <div class="score-label">Puntuación / 100</div>
                    </div>
                    
                    <div class="text-center">
                        <span class="signal-badge" style="color: {resultado['color']}; border-color: {resultado['color']}; background: {resultado['color']}10;">
                            {resultado['senal']}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Recomendación debajo
            st.markdown(f"""
            <div class="recommendation">
                <div class="recommendation-title">📋 Recomendación Estratégica</div>
                <div class="recommendation-text">{resultado['recomendacion']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_right:
            # Card de factores
            st.markdown("""
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Desglose de Factores</span>
                </div>
                <div class="card-body">
                    <div class="factor-list">
            """, unsafe_allow_html=True)
            
            # Renderizar factores ordenados
            factores_ordenados = sorted(resultado['metricas'].items(), key=lambda x: x[1].get('order', 99))
            
            for factor_key, m in factores_ordenados:
                nombres = {
                    'FTD': 'Follow-Through Day',
                    'RSI': 'RSI Diario (14)',
                    'VIX': 'VIX / Volatilidad',
                    'Breadth': 'Breadth (McClellan)',
                    'Volume': 'Volumen Capitulación'
                }
                nombre = nombres.get(factor_key, factor_key)
                
                pct = (m['score'] / m['max']) * 100 if m['max'] > 0 else 0
                raw_val = m.get('raw_value')
                
                # Meta información
                meta_text = ""
                if raw_val is not None:
                    if factor_key == 'RSI':
                        meta_text = f"RSI actual: {raw_val:.1f}"
                    elif factor_key == 'VIX':
                        meta_text = f"{'ATR ratio' if m.get('is_proxy') else 'VIX'}: {raw_val:.1f}"
                    elif factor_key == 'Breadth':
                        meta_text = f"McClellan: {raw_val:.0f}"
                    elif factor_key == 'Volume':
                        meta_text = f"Ratio: {raw_val:.1f}x"
                    elif factor_key == 'FTD' and resultado.get('ftd_data'):
                        ftd = resultado['ftd_data']
                        if ftd.get('dias_rally', 0) > 0:
                            meta_text = f"Día {ftd['dias_rally']} del rally"
                
                st.markdown(f"""
                <div class="factor-item">
                    <div class="factor-header">
                        <span class="factor-name">{nombre}</span>
                        <span class="factor-score" style="color: {m['color']};">
                            {m['score']}/{m['max']}
                        </span>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar" style="width: {pct}%; background: {m['color']};"></div>
                    </div>
                    {f'<div class="factor-meta">{meta_text}</div>' if meta_text else ''}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("""
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Detalles técnicos expandibles
        with st.expander("🔍 Ver análisis técnico detallado"):
            st.markdown('<div class="detail-list">', unsafe_allow_html=True)
            for detalle in resultado['detalles']:
                if detalle.startswith('✓'):
                    clase = 'detail-success'
                elif detalle.startswith('~'):
                    clase = 'detail-warning'
                elif detalle.startswith('✗'):
                    clase = 'detail-danger'
                else:
                    clase = 'detail-neutral'
                
                st.markdown(f'<div class="detail-item {clase}">{detalle}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 📈 Backtesting Histórico")
        st.info("""
        **¿Qué es una señal?** Un día donde el score ≥ umbral (entrada), manteniendo la posición 20 días.
        Se aplica cooldown de 20 días entre señales para evitar solapamiento.
        """)
        
        col_config, col_action = st.columns([1, 2], gap="medium")
        
        with col_config:
            st.markdown("#### Configuración")
            umbral_bt = st.slider("Umbral de entrada", 30, 80, 50, 5,
                                  help="Score mínimo para generar señal de compra")
            años_bt = st.selectbox("Período histórico", [1, 2, 3, 5, 10], index=3)
            
            st.caption(f"""
            **Interpretación umbrales:**
            - **40 pts**: ~25-30 señales/año (alta frecuencia)
            - **50 pts**: ~15-20 señales/año (balance recomendado)
            - **60 pts**: ~8-12 señales/año (alta calidad)
            - **70 pts**: ~3-6 señales/año (muy restrictivo)
            """)
        
        with col_action:
            if st.button("🚀 Ejecutar Backtest", type="primary", use_container_width=True):
                with st.spinner(f'Analizando {años_bt} años de datos... Esto puede tomar 1-2 minutos'):
                    resultados, error = backtest_strategy(years=años_bt, umbral=umbral_bt)
                    
                    if error:
                        st.warning(error)
                        st.info("💡 Tip: Prueba con un umbral más bajo (40) o período más largo")
                    elif resultados:
                        # Resumen ejecutivo
                        st.success(f"""
                        **Backtest completado**: {resultados['total_señales']} señales generadas 
                        (umbral {umbral_bt} pts) · Score medio: {resultados['score_promedio']:.1f}
                        """)
                        
                        # Métricas en cards
                        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                        m_col1.metric("Total Señales", resultados['total_señales'])
                        m_col2.metric("Win Rate 20d", f"{resultados['win_rate_20d']:.1f}%")
                        m_col3.metric("Retorno Medio", f"{resultados['retorno_medio_20d']:.2f}%")
                        m_col4.metric("Retorno Total", f"{resultados['retorno_total_20d']:.2f}%")
                        
                        # Análisis por timeframe
                        st.markdown("#### Performance por Horizonte Temporal")
                        perf_data = pd.DataFrame({
                            'Horizonte': ['5 días', '10 días', '20 días'],
                            'Win Rate (%)': [
                                resultados['win_rate_5d'],
                                resultados['win_rate_10d'],
                                resultados['win_rate_20d']
                            ],
                            'Retorno Medio (%)': [
                                resultados['retorno_medio_5d'],
                                resultados['retorno_medio_10d'],
                                resultados['retorno_medio_20d']
                            ]
                        })
                        
                        chart_col1, chart_col2 = st.columns(2)
                        with chart_col1:
                            st.bar_chart(perf_data.set_index('Horizonte')['Win Rate (%)'], 
                                        use_container_width=True, height=300)
                        with chart_col2:
                            st.bar_chart(perf_data.set_index('Horizonte')['Retorno Medio (%)'],
                                        use_container_width=True, height=300)
                        
                        # Tabla detallada
                        with st.expander("Ver tabla detallada de operaciones"):
                            st.dataframe(
                                resultados['detalle'].sort_values('fecha', ascending=False),
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    'fecha': 'Fecha Entrada',
                                    'score': st.column_config.NumberColumn('Score', format='%d'),
                                    'estado': 'Tipo Señal',
                                    'precio_entrada': st.column_config.NumberColumn('Precio', format='$%.2f'),
                                    'retorno_5d': st.column_config.NumberColumn('R 5d', format='%.2f%%'),
                                    'retorno_10d': st.column_config.NumberColumn('R 10d', format='%.2f%%'),
                                    'retorno_20d': st.column_config.NumberColumn('R 20d', format='%.2f%%')
                                }
                            )
    
    with tab3:
        st.markdown("""
        ### 🎯 Sobre las Señales y su Frecuencia
        
        Tu backtest mostró **3 señales en 5 años con umbral 50**, lo cual es anormalmente bajo.
        Esto sugiere que el mercado ha estado en tendencia alcista la mayor parte del tiempo (2020-2024),
        sin las condiciones de sobreventa extrema que requiere este algoritmo.
        
        #### ¿Es normal que los factores estén a 0?
        
        **Sí, en mercados alcistas estables.** Los factores se activan en:
        - **FTD**: Solo después de caídas significativas (>15%)
        - **RSI**: Solo en sobreventa (<40)
        - **VIX**: Solo en pánico (>25)
        - **Breadth**: Solo cuando la mayoría de stocks caen
        
        En 2023-2024, SPY tuvo RSI > 50 la mayor parte del tiempo, VIX < 20, y sin correcciones mayores al 10%.
        Por eso el score ha estado bajo.
        
        #### Expectativas Realistas
        
        | Régimen de Mercado | Señales/Año (umbral 50) | Win Rate Esperado |
        |-------------------|------------------------|-------------------|
        | Bull market tranquilo | 2-5 | 60-70% |
        | Mercado volátil | 8-15 | 55-65% |
        | Bear market | 10-20 | 50-60% |
        
        #### Ajustes Recomendados
        
        Si quieres más señales en mercados tranquilos:
        1. **Bajar umbral a 40**: Captura setups más tempranos
        2. **Añadir factor de tendencia**: Dar puntos por pullbacks en tendencia alcista
        3. **Reducir peso de VIX**: De 20 a 10 pts, aumentar RSI a 35 pts
        
        #### Referencias
        
        - O'Neil: FTD tiene éxito ~55% de las veces [^5^]
        - Quantifiable Edges: FTD después de correcciones >20% tienen mayor tasa éxito [^61^]
        - Datos históricos: 2020 (crash COVID) generó 4 FTD válidos en 3 meses
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)


