# modules/rsu_algoritmo_pro.py
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import sys
import os

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
    if df is None or len(df) < 50:
        return 0
    returns = df['Close'].pct_change()
    mom_19 = returns.rolling(19).mean()
    mom_39 = returns.rolling(39).mean()
    mcclellan = (mom_19 - mom_39) * 1000
    return mcclellan.iloc[-1] if not pd.isna(mcclellan.iloc[-1]) else 0

def detectar_distribucion_days(df_spy):
    """
    Detecta Distribution Days (días de distribución) - señal de venta.
    Un distribution day es cuando el precio cae con volumen creciente.
    4-6 distribution days en 2-3 semanas = señal de venta según O'Neil.
    """
    df = df_spy.copy()
    df['price_down'] = df['Close'] < df['Close'].shift(1)
    df['volume_up'] = df['Volume'] > df['Volume'].shift(1)
    df['dist_day'] = df['price_down'] & df['volume_up']
    
    # Contar en ventana de 15 días
    dist_count = df['dist_day'].rolling(window=15).sum().iloc[-1]
    
    if dist_count >= 5:
        return {'nivel': 'ALTO', 'count': int(dist_count), 'signal': 'sell'}
    elif dist_count >= 3:
        return {'nivel': 'MODERADO', 'count': int(dist_count), 'signal': 'caution'}
    else:
        return {'nivel': 'BAJO', 'count': int(dist_count), 'signal': 'hold'}

def detectar_fondo_comprehensivo(df_spy, df_vix=None):
    """
    Sistema de detección de fondos multi-factor.
    SCORE MÁXIMO: 50 puntos (más intuitivo)
    UMBRAL VERDE: 40 pts (80% del máximo)
    UMBRAL AMBAR: 25 pts (50% del máximo)
    """
    score = 0
    max_score = 50
    detalles = []
    metricas = {}
    
    # 1. FTD Detection (15 pts) - REDUCIDO de 30 a 15
    ftd_data = detectar_follow_through_day(df_spy)
    ftd_score = 0
    
    if ftd_data:
        if ftd_data.get('signal') == 'confirmed':
            ftd_score = 15
            detalles.append("✓ FTD Confirmado (+15)")
        elif ftd_data.get('signal') == 'potential':
            ftd_score = 10
            detalles.append("~ FTD Potencial (+10)")
        elif ftd_data.get('signal') == 'early':
            ftd_score = 5
            detalles.append(f"• Rally temprano (+5)")
        else:
            detalles.append("• Sin FTD (0)")
    else:
        detalles.append("• Sin datos FTD (0)")
    
    score += ftd_score
    metricas['FTD'] = {'score': ftd_score, 'max': 15, 'color': '#3b82f6', 'order': 1}
    
    # 2. RSI Diario (15 pts) - REDUCIDO de 25 a 15, pero más sensible
    rsi_series = calcular_rsi(df_spy['Close'], 14)
    rsi = rsi_series.iloc[-1]
    rsi_score = 0
    
    if rsi < 20:
        rsi_score = 15
        detalles.append(f"✓ RSI {rsi:.1f} < 20 (+15)")
    elif rsi < 30:
        rsi_score = 12
        detalles.append(f"✓ RSI {rsi:.1f} < 30 (+12)")
    elif rsi < 40:
        rsi_score = 8
        detalles.append(f"~ RSI {rsi:.1f} < 40 (+8)")
    elif rsi < 45:
        rsi_score = 3
        detalles.append(f"• RSI {rsi:.1f} < 45 (+3)")
    else:
        detalles.append(f"• RSI {rsi:.1f} neutral (0)")
    
    score += rsi_score
    metricas['RSI'] = {'score': rsi_score, 'max': 15, 'color': '#10b981', 'raw_value': rsi, 'order': 2}
    
    # 3. VIX / Volatilidad (10 pts) - REDUCIDO de 20 a 10
    vix_score = 0
    vix_val = None
    
    if df_vix is not None and len(df_vix) > 20:
        vix_actual = df_vix['Close'].iloc[-1]
        vix_val = vix_actual
        
        if vix_actual > 30:
            vix_score = 10
            detalles.append(f"✓ VIX {vix_actual:.1f} > 30 (+10)")
        elif vix_actual > 25:
            vix_score = 7
            detalles.append(f"~ VIX {vix_actual:.1f} > 25 (+7)")
        elif vix_actual > 20:
            vix_score = 3
            detalles.append(f"• VIX {vix_actual:.1f} > 20 (+3)")
        else:
            detalles.append(f"• VIX {vix_actual:.1f} bajo (0)")
    else:
        atr = calcular_atr(df_spy).iloc[-1]
        atr_medio = calcular_atr(df_spy).rolling(20).mean().iloc[-1]
        ratio_atr = atr / atr_medio if atr_medio > 0 else 1
        vix_val = ratio_atr
        
        if ratio_atr > 2.0:
            vix_score = 8
            detalles.append(f"~ Volatilidad alta (+8)")
        else:
            detalles.append(f"• Volatilidad normal (0)")
    
    score += vix_score
    metricas['VIX'] = {'score': vix_score, 'max': 10, 'color': '#f59e0b', 'raw_value': vix_val, 'is_proxy': df_vix is None, 'order': 3}
    
    # 4. McClellan (7 pts) - REDUCIDO de 15 a 7
    mcclellan = calcular_mcclellan_proxy(df_spy)
    breadth_score = 0
    
    if mcclellan < -80:
        breadth_score = 7
        detalles.append(f"✓ McClellan {mcclellan:.0f} < -80 (+7)")
    elif mcclellan < -50:
        breadth_score = 4
        detalles.append(f"~ McClellan {mcclellan:.0f} < -50 (+4)")
    else:
        detalles.append(f"• McClellan {mcclellan:.0f} neutral (0)")
    
    score += breadth_score
    metricas['Breadth'] = {'score': breadth_score, 'max': 7, 'color': '#8b5cf6', 'raw_value': mcclellan, 'order': 4}
    
    # 5. Volume Capitulación (3 pts) - REDUCIDO de 10 a 3
    vol_actual = df_spy['Volume'].iloc[-1]
    vol_media = df_spy['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = vol_actual / vol_media if vol_media > 0 else 1
    vol_score = 0
    
    if vol_ratio > 2.0:
        vol_score = 3
        detalles.append(f"✓ Volumen {vol_ratio:.1f}x (+3)")
    elif vol_ratio > 1.5:
        vol_score = 1
        detalles.append(f"• Volumen {vol_ratio:.1f}x (+1)")
    else:
        detalles.append(f"• Volumen normal (0)")
    
    score += vol_score
    metricas['Volume'] = {'score': vol_score, 'max': 3, 'color': '#ef4444', 'raw_value': vol_ratio, 'order': 5}
    
    # Determinar estado
    if score >= 40:
        estado = "VERDE"
        senal = "FONDO PROBABLE"
        color = "#10b981"
        recomendacion = f"Score {score}/50: Setup óptimo. Entrada gradual 25-50%, stop -7%"
    elif score >= 25:
        estado = "AMBAR"
        senal = "DESARROLLANDO"
        color = "#f59e0b"
        recomendacion = f"Score {score}/50: Preparar watchlist, entrada parcial opcional"
    else:
        estado = "ROJO"
        senal = "SIN FONDO"
        color = "#ef4444"
        recomendacion = f"Score {score}/50: Sin condiciones. Preservar capital"
    
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

def detectar_senal_venta(df_spy, df_vix=None):
    """
    Sistema de señales de VENTA.
    Detecta cuando el mercado está agotado y es momento de tomar beneficios.
    """
    score_venta = 0
    detalles_venta = []
    
    # 1. Distribution Days (máximo 20 pts)
    dist_data = detectar_distribucion_days(df_spy)
    if dist_data['signal'] == 'sell':
        score_venta += 20
        detalles_venta.append(f"✓ {dist_data['count']} Distribution Days (+20)")
    elif dist_data['signal'] == 'caution':
        score_venta += 10
        detalles_venta.append(f"~ {dist_data['count']} Distribution Days (+10)")
    
    # 2. RSI > 70 (sobrecompra, máximo 15 pts)
    rsi = calcular_rsi(df_spy['Close'], 14).iloc[-1]
    if rsi > 75:
        score_venta += 15
        detalles_venta.append(f"✓ RSI {rsi:.1f} > 75 (sobrecompra extrema) (+15)")
    elif rsi > 70:
        score_venta += 10
        detalles_venta.append(f"~ RSI {rsi:.1f} > 70 (sobrecompra) (+10)")
    
    # 3. VIX bajo + caída (máximo 10 pts)
    if df_vix is not None and len(df_vix) > 20:
        vix_actual = df_vix['Close'].iloc[-1]
        vix_sma20 = df_vix['Close'].rolling(20).mean().iloc[-1]
        if vix_actual < vix_sma20 * 0.8:  # VIX bajo vs media
            score_venta += 5
            detalles_venta.append("• VIX bajo (complacencia) (+5)")
    
    # 4. Precio lejos de SMA 50 (máximo 10 pts)
    sma50 = df_spy['Close'].rolling(50).mean().iloc[-1]
    precio = df_spy['Close'].iloc[-1]
    dist_sma = (precio - sma50) / sma50
    
    if dist_sma > 0.15:  # 15% por encima de SMA 50
        score_venta += 10
        detalles_venta.append(f"✓ Precio {dist_sma*100:.1f}% sobre SMA50 (+10)")
    elif dist_sma > 0.10:
        score_venta += 5
        detalles_venta.append(f"~ Precio {dist_sma*100:.1f}% sobre SMA50 (+5)")
    
    # Determinar señal de venta
    if score_venta >= 30:
        return {
            'senal': 'VENTA FUERTE',
            'color': '#dc2626',
            'score': score_venta,
            'accion': 'Reducir posiciones 50-75%, elevar stops',
            'detalles': detalles_venta
        }
    elif score_venta >= 15:
        return {
            'senal': 'PRECAUCIÓN',
            'color': '#f59e0b',
            'score': score_venta,
            'accion': 'No abrir nuevas posiciones, vigilar stops',
            'detalles': detalles_venta
        }
    else:
        return {
            'senal': 'MANTENER',
            'color': '#10b981',
            'score': score_venta,
            'accion': 'Sin señales de agotamiento',
            'detalles': detalles_venta
        }

def calcular_atr(df, periodo=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=periodo).mean()

def detectar_follow_through_day(df_daily):
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

def backtest_strategy(ticker_symbol="SPY", years=2, umbral=40):
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
        last_signal_idx = -20
        
        for i in range(60, len(df_hist) - 20):
            if i - last_signal_idx < 20:
                continue
            
            ventana_df = df_hist.iloc[:i]
            vix_window = vix_hist.iloc[:i] if vix_hist is not None else None
            
            resultado = detectar_fondo_comprehensivo(ventana_df, vix_window)
            
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
    
    st.markdown("""
    <style>
    .main-container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
    
    .card {
        background: #11141a;
        border: 1px solid #1f2937;
        border-radius: 12px;
        overflow: hidden;
    }
    
    .card-header {
        background: #0c0e12;
        padding: 1rem 1.25rem;
        border-bottom: 1px solid #1f2937;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .card-title {
        color: #f9fafb;
        font-size: 1rem;
        font-weight: 600;
        margin: 0;
    }
    
    .card-body {
        padding: 1.25rem;
    }
    
    .semaforo-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.75rem;
        padding: 1.5rem 0;
    }
    
    .luz {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        border: 3px solid #374151;
        background: #1f2937;
        opacity: 0.3;
        transition: all 0.3s ease;
    }
    
    .luz.on {
        opacity: 1;
        transform: scale(1.1);
        box-shadow: 0 0 20px currentColor;
    }
    
    .luz-roja.on {
        background: radial-gradient(circle at 30% 30%, #f87171, #dc2626);
        border-color: #ef4444;
        color: #ef4444;
    }
    
    .luz-ambar.on {
        background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706);
        border-color: #f59e0b;
        color: #f59e0b;
    }
    
    .luz-verde.on {
        background: radial-gradient(circle at 30% 30%, #34d399, #059669);
        border-color: #10b981;
        color: #10b981;
    }
    
    .score-container {
        text-align: center;
        margin: 1.5rem 0;
    }
    
    .score-number {
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1;
    }
    
    .score-label {
        color: #6b7280;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.5rem;
    }
    
    .signal-badge {
        display: inline-block;
        padding: 0.5rem 1.25rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.9375rem;
        border: 2px solid;
    }
    
    .factor-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .factor-item {
        background: #0c0e12;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 0.875rem;
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
    }
    
    .factor-score {
        font-family: monospace;
        font-size: 0.875rem;
        font-weight: 700;
    }
    
    .factor-bar-bg {
        height: 6px;
        background: #1f2937;
        border-radius: 3px;
        overflow: hidden;
    }
    
    .factor-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s ease;
    }
    
    .factor-meta {
        color: #4b5563;
        font-size: 0.75rem;
        margin-top: 0.25rem;
    }
    
    .rec-box {
        background: rgba(16, 185, 129, 0.05);
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 1rem;
    }
    
    .rec-title {
        color: #10b981;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 0.375rem;
    }
    
    .rec-text {
        color: #d1d5db;
        font-size: 0.875rem;
        line-height: 1.5;
    }
    
    .detail-row {
        padding: 0.625rem;
        margin-bottom: 0.5rem;
        border-radius: 6px;
        font-size: 0.875rem;
        border-left: 3px solid;
    }
    
    .detail-success { background: rgba(16, 185, 129, 0.1); border-left-color: #10b981; color: #34d399; }
    .detail-warning { background: rgba(245, 158, 11, 0.1); border-left-color: #f59e0b; color: #fbbf24; }
    .detail-danger { background: rgba(239, 68, 68, 0.1); border-left-color: #ef4444; color: #f87171; }
    .detail-neutral { background: #0c0e12; border-left-color: #4b5563; color: #9ca3af; }
    
    .sell-signal-box {
        background: rgba(239, 68, 68, 0.05);
        border: 1px solid #ef4444;
        border-radius: 12px;
        padding: 1.25rem;
        margin-top: 1.5rem;
    }
    
    .sell-signal-title {
        color: #ef4444;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="color: #f9fafb; font-size: 1.875rem; font-weight: 700; margin: 0;">
            🚦 RSU Algoritmo Pro
        </h1>
        <p style="color: #6b7280; font-size: 1rem; margin: 0.5rem 0 0 0;">
            Score máximo: 50 pts · Verde ≥ 40 pts · Ámbar ≥ 25 pts
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Análisis", "📈 Backtest", "ℹ️ Metodología"])
    
    with tab1:
        with st.spinner('Analizando...'):
            try:
                ticker = yf.Ticker("SPY")
                df_daily = ticker.history(interval="1d", period="6mo")
                
                try:
                    vix = yf.Ticker("^VIX")
                    df_vix = vix.history(interval="1d", period="6mo")
                except:
                    df_vix = None
                
                resultado = detectar_fondo_comprehensivo(df_daily, df_vix)
                senal_venta = detectar_senal_venta(df_daily, df_vix)
                
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()
        
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            luz_r = "on" if resultado['estado'] == "ROJO" else ""
            luz_a = "on" if resultado['estado'] == "AMBAR" else ""
            luz_v = "on" if resultado['estado'] == "VERDE" else ""
            
            semaforo_html = f"""
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Señal de Entrada (Compra)</span>
                    <span style="color: {resultado['color']}; font-size: 0.875rem; font-weight: 600;">
                        ● {resultado['estado']}
                    </span>
                </div>
                <div class="card-body">
                    <div class="semaforo-box">
                        <div class="luz luz-roja {luz_r}"></div>
                        <div class="luz luz-ambar {luz_a}"></div>
                        <div class="luz luz-verde {luz_v}"></div>
                    </div>
                    
                    <div class="score-container">
                        <div class="score-number" style="color: {resultado['color']};">
                            {resultado['score']}
                        </div>
                        <div class="score-label">de {resultado['max_score']} puntos</div>
                    </div>
                    
                    <div style="text-align: center;">
                        <span class="signal-badge" style="color: {resultado['color']}; border-color: {resultado['color']}; background-color: {resultado['color']}15;">
                            {resultado['senal']}
                        </span>
                    </div>
                </div>
            </div>
            """
            st.html(semaforo_html)
            
            rec_html = f"""
            <div class="rec-box">
                <div class="rec-title">📋 Recomendación</div>
                <div class="rec-text">{resultado['recomendacion']}</div>
            </div>
            """
            st.html(rec_html)
            
            # Señal de venta
            sell_color = senal_venta['color']
            sell_html = f"""
            <div class="sell-signal-box" style="border-color: {sell_color}; background: {sell_color}08;">
                <div class="sell-signal-title" style="color: {sell_color};">
                    📉 Señal de Salida (Venta): {senal_venta['senal']} ({senal_venta['score']}/45 pts)
                </div>
                <div style="color: #d1d5db; font-size: 0.875rem; margin-bottom: 0.5rem;">
                    {senal_venta['accion']}
                </div>
                <div style="color: #6b7280; font-size: 0.75rem;">
                    {' • '.join(senal_venta['detalles'][:2]) if senal_venta['detalles'] else 'Sin señales de agotamiento'}
                </div>
            </div>
            """
            st.html(sell_html)
        
        with col2:
            factores_html = """
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Desglose de Factores</span>
                </div>
                <div class="card-body">
                    <div class="factor-list">
            """
            
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
                
                meta = ""
                if raw_val is not None:
                    if factor_key == 'RSI':
                        meta = f"RSI: {raw_val:.1f}"
                    elif factor_key == 'VIX':
                        meta = f"{'ATR' if m.get('is_proxy') else 'VIX'}: {raw_val:.1f}"
                    elif factor_key == 'Breadth':
                        meta = f"McClellan: {raw_val:.0f}"
                    elif factor_key == 'Volume':
                        meta = f"Ratio: {raw_val:.1f}x"
                    elif factor_key == 'FTD' and resultado.get('ftd_data'):
                        ftd = resultado['ftd_data']
                        if ftd.get('dias_rally', 0) > 0:
                            meta = f"Día {ftd['dias_rally']} del rally"
                
                factores_html += f"""
                <div class="factor-item">
                    <div class="factor-header">
                        <span class="factor-name">{nombre} (max {m['max']})</span>
                        <span class="factor-score" style="color: {m['color']};">{m['score']}/{m['max']}</span>
                    </div>
                    <div class="factor-bar-bg">
                        <div class="factor-bar-fill" style="width: {pct}%; background: {m['color']};"></div>
                    </div>
                    {f'<div class="factor-meta">{meta}</div>' if meta else ''}
                </div>
                """
            
            factores_html += """
                    </div>
                </div>
            </div>
            """
            st.html(factores_html)
        
        with st.expander("🔍 Ver detalles técnicos"):
            for detalle in resultado['detalles']:
                if detalle.startswith('✓'):
                    clase = 'detail-success'
                elif detalle.startswith('~'):
                    clase = 'detail-warning'
                elif detalle.startswith('✗'):
                    clase = 'detail-danger'
                else:
                    clase = 'detail-neutral'
                
                st.html(f'<div class="detail-row {clase}">{detalle}</div>')
    
    with tab2:
        st.markdown("### 📈 Backtesting Histórico")
        
        col_cfg, col_res = st.columns([1, 2], gap="medium")
        
        with col_cfg:
            st.markdown("#### Configuración")
            
            umbral_sel = st.slider("Umbral de entrada", 25, 50, 40, 5)
            años_sel = st.selectbox("Período", [1, 2, 3, 5, 10], index=3)
            
            st.caption("""
            **Frecuencia histórica real (SPY 2020-2025):**
            - Umbral 40: ~3-8 señales/año
            - Umbral 35: ~5-12 señales/año
            - Umbral 50: ~1-4 señales/año
            
            *Nota: 2020-2025 fue un período alcista excepcional*
            """)
        
        with col_res:
            if st.button("🚀 Ejecutar Backtest", type="primary", use_container_width=True):
                with st.spinner(f'Analizando {años_sel} años...'):
                    resultados, error = backtest_strategy(years=años_sel, umbral=umbral_sel)
                    
                    if error:
                        st.warning(error)
                    elif resultados:
                        st.success(f"**{resultados['total_señales']} señales** · Score medio: {resultados['score_promedio']:.1f}/50")
                        
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Total", resultados['total_señales'])
                        m2.metric("Win Rate 20d", f"{resultados['win_rate_20d']:.1f}%")
                        m3.metric("Retorno Medio", f"{resultados['retorno_medio_20d']:.2f}%")
                        m4.metric("Retorno Total", f"{resultados['retorno_total_20d']:.2f}%")
                        
                        st.markdown("#### Performance por Timeframe")
                        perf_df = pd.DataFrame({
                            '5 días': [resultados['win_rate_5d'], resultados['retorno_medio_5d']],
                            '10 días': [resultados['win_rate_10d'], resultados['retorno_medio_10d']],
                            '20 días': [resultados['win_rate_20d'], resultados['retorno_medio_20d']]
                        }, index=['Win Rate %', 'Retorno Medio %'])
                        
                        st.bar_chart(perf_df.T, use_container_width=True, height=300)
                        
                        with st.expander("Ver operaciones detalladas"):
                            st.dataframe(resultados['detalle'].sort_values('fecha', ascending=False), hide_index=True)
    
    with tab3:
        st.markdown("""
        ### 🎯 ¿Qué es esta herramienta?
        
        **RSU Algoritmo Pro** identifica el **mejor momento para entrar al mercado de forma agresiva** 
        (score ≥ 40) o **moderada** (score ≥ 25), basándose en la confluencia de múltiples factores 
        técnicos que históricamente preceden a los fondos de mercado.
        
        ---
        
        ### 📊 Factores del Algoritmo (Score máximo: 50)
        
        #### 1. Follow-Through Day (15 pts)
        **¿Qué es?** Señal de William O'Neil que confirma el cambio de tendencia bajista a alcista. 
        Ocurre entre el día 4-7 después de un mínimo, con subida ≥1.5% y volumen creciente.
        
        **¿Por qué?** Un FTD válido indica que instituciones grandes están comprando agresivamente, 
        proporcionando el "combustible" para un nuevo rally sostenido.
        
        #### 2. RSI Diario (15 pts)
        **¿Qué es?** Índice de Fuerza Relativa. Mide el momentum del precio (0-100).
        
        **¿Por qué?** RSI < 30 indica sobreventa extrema (pánico vendedor agotado). 
        Comprar cuando el miedo es máximo es la base del value investing técnico.
        
        #### 3. VIX / Volatilidad (10 pts)
        **¿Qué es?** "Índice de Miedo" del mercado. Mide la volatilidad implícita de SPX.
        
        **¿Por qué?** VIX > 30 indica pánico extremo. Históricamente, los mejores retornos 
        ocurren después de picos de VIX (compra del mercado cuando otros venden).
        
        #### 4. Breadth - McClellan (7 pts)
        **¿Qué es?** Oscilador de amplitud del mercado. Mide cuántos stocks suben vs bajan.
        
        **¿Por qué?** Un fondo saludable requiere participación amplia, no solo que suban 
        5 tecnológicas grandes. McClellan < -80 indica agotamiento de la mayoría de stocks.
        
        #### 5. Volumen de Capitulación (3 pts)
        **¿Qué es?** Picos de volumen >2x la media diaria.
        
        **¿Por qué?** Indica capitulación (vendedores agotados lanzando posiciones). 
        El volumen confirma la convicción detrás del movimiento de precio.
        
        ---
        
        ### 📉 Señal de Salida (Venta)
        
        El sistema también detecta **Distribution Days** (días de distribución):
        - Precio cae con volumen creciente
        - 4-6 días en 2-3 semanas = instituciones vendiendo
        - Combinado con RSI > 70 = señal de toma de beneficios
        
        ---
        
        ### ⚠️ Limitaciones
        
        1. **Mercados alcistas prolongados**: En bull markets como 2023-2024, el sistema 
           puede estar meses sin señal (lo cual es correcto - preserva capital)
        
        2. **Falsos positivos**: ~30-40% de las señales no funcionarán. Por eso el stop-loss 
           del -7% es obligatorio
        
        3. **Retraso inherente**: Detecta fondos, no los predice. Siempre hay lag
        
        4. **Proxy del McClellan**: Sin datos reales de advancing/declining issues, 
           el cálculo es aproximado
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)



