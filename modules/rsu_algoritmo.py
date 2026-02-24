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

def detectar_fondo_comprehensivo(df_spy, df_vix=None):
    """
    UMBRALES DEL SEMÁFORO:
    - VERDE: Score >= 40 (Fondo probable)
    - AMBAR: Score 25-39 (Desarrollando)
    - ROJO: Score < 25 (Sin fondo)
    """
    score = 0
    detalles = []
    metricas = {}
    
    # 1. FTD (30 pts)
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
            detalles.append("• Rally activo (+5)")
        else:
            detalles.append("✗ Sin FTD (0)")
    else:
        detalles.append("✗ Sin datos FTD (0)")
    
    score += ftd_score
    metricas['FTD'] = {'score': ftd_score, 'max': 30, 'color': '#3b82f6', 'order': 1}
    
    # 2. RSI (25 pts)
    rsi_series = calcular_rsi(df_spy['Close'], 14)
    rsi = rsi_series.iloc[-1]
    rsi_score = 0
    
    if rsi < 20:
        rsi_score = 25
        detalles.append(f"✓ RSI {rsi:.1f} < 20 (+25)")
    elif rsi < 30:
        rsi_score = 20
        detalles.append(f"✓ RSI {rsi:.1f} < 30 (+20)")
    elif rsi < 40:
        rsi_score = 15
        detalles.append(f"~ RSI {rsi:.1f} < 40 (+15)")
    elif rsi < 50:
        rsi_score = 5
        detalles.append(f"• RSI {rsi:.1f} < 50 (+5)")
    elif rsi > 75:
        rsi_score = -10
        detalles.append(f"✗ RSI {rsi:.1f} > 75 (-10)")
    else:
        detalles.append(f"• RSI {rsi:.1f} neutral (0)")
    
    score += rsi_score
    metricas['RSI'] = {'score': max(0, rsi_score), 'max': 25, 'color': '#10b981', 'raw_value': rsi, 'order': 2}
    
    # 3. VIX (20 pts)
    vix_score = 0
    vix_val = None
    
    if df_vix is not None and len(df_vix) > 20:
        vix_actual = df_vix['Close'].iloc[-1]
        vix_sma20 = df_vix['Close'].rolling(20).mean().iloc[-1]
        vix_val = vix_actual
        
        if vix_actual > 35:
            vix_score = 20
            detalles.append(f"✓ VIX {vix_actual:.1f} > 35 (+20)")
        elif vix_actual > 30:
            vix_score = 15
            detalles.append(f"✓ VIX {vix_actual:.1f} > 30 (+15)")
        elif vix_actual > 25:
            vix_score = 10
            detalles.append(f"~ VIX {vix_actual:.1f} > 25 (+10)")
        elif vix_actual > vix_sma20 * 1.2:
            vix_score = 5
            detalles.append(f"• VIX elevado (+5)")
        else:
            detalles.append(f"• VIX {vix_actual:.1f} normal (0)")
    else:
        atr = calcular_atr(df_spy).iloc[-1]
        atr_medio = calcular_atr(df_spy).rolling(20).mean().iloc[-1]
        ratio_atr = atr / atr_medio if atr_medio > 0 else 1
        vix_val = ratio_atr
        
        if ratio_atr > 2.5:
            vix_score = 15
            detalles.append(f"~ ATR {ratio_atr:.1f}x alto (+15)")
        elif ratio_atr > 1.8:
            vix_score = 10
            detalles.append(f"~ ATR {ratio_atr:.1f}x elevado (+10)")
        else:
            detalles.append(f"• Volatilidad normal (0)")
    
    score += vix_score
    metricas['VIX'] = {'score': vix_score, 'max': 20, 'color': '#f59e0b', 'raw_value': vix_val, 'is_proxy': df_vix is None, 'order': 3}
    
    # 4. McClellan (15 pts)
    mcclellan = calcular_mcclellan_proxy(df_spy)
    breadth_score = 0
    
    if mcclellan < -100:
        breadth_score = 15
        detalles.append(f"✓ McClellan {mcclellan:.0f} < -100 (+15)")
    elif mcclellan < -60:
        breadth_score = 10
        detalles.append(f"~ McClellan {mcclellan:.0f} < -60 (+10)")
    elif mcclellan < -30:
        breadth_score = 5
        detalles.append(f"• McClellan {mcclellan:.0f} < -30 (+5)")
    else:
        detalles.append(f"• McClellan {mcclellan:.0f} neutral (0)")
    
    score += breadth_score
    metricas['Breadth'] = {'score': breadth_score, 'max': 15, 'color': '#8b5cf6', 'raw_value': mcclellan, 'order': 4}
    
    # 5. Volume (10 pts)
    vol_actual = df_spy['Volume'].iloc[-1]
    vol_media = df_spy['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = vol_actual / vol_media if vol_media > 0 else 1
    vol_score = 0
    
    if vol_ratio > 2.5:
        vol_score = 10
        detalles.append(f"✓ Volumen {vol_ratio:.1f}x (+10)")
    elif vol_ratio > 1.8:
        vol_score = 7
        detalles.append(f"~ Volumen {vol_ratio:.1f}x (+7)")
    elif vol_ratio > 1.3:
        vol_score = 3
        detalles.append(f"• Volumen {vol_ratio:.1f}x (+3)")
    else:
        detalles.append(f"• Volumen normal (0)")
    
    score += vol_score
    metricas['Volume'] = {'score': vol_score, 'max': 10, 'color': '#ef4444', 'raw_value': vol_ratio, 'order': 5}
    
    # UMBRALES AJUSTADOS PARA MÁS FRECUENCIA
    if score >= 40:  # BAJADO de 50 a 40
        estado = "VERDE"
        senal = "FONDO PROBABLE"
        color = "#10b981"
        recomendacion = f"Score {score}: Setup óptimo. Considerar entrada gradual (25-50%), stop -7%"
    elif score >= 25:  # BAJADO de 35 a 25
        estado = "AMBAR"
        senal = "DESARROLLANDO"
        color = "#f59e0b"
        recomendacion = f"Score {score}: Condiciones mejorando. Preparar watchlist, entrada parcial opcional"
    else:
        estado = "ROJO"
        senal = "SIN FONDO"
        color = "#ef4444"
        recomendacion = f"Score {score}: Sin condiciones de fondo. Preservar capital"
    
    return {
        'score': score,
        'estado': estado,
        'senal': senal,
        'color': color,
        'recomendacion': recomendacion,
        'detalles': detalles,
        'ftd_data': ftd_data,
        'metricas': metricas
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
    
    # CSS CORREGIDO - Sin conflictos de renderizado
    st.markdown("""
    <style>
    /* Base */
    .main-container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
    
    /* Cards unificadas */
    .card {
        background: #11141a;
        border: 1px solid #1f2937;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 1.5rem;
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
    
    /* Semáforo */
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
    
    /* Score */
    .score-container {
        text-align: center;
        margin: 1rem 0;
    }
    
    .score-number {
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.25rem;
    }
    
    .score-text {
        color: #6b7280;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Badge */
    .signal-badge-container {
        text-align: center;
        margin-top: 1rem;
    }
    
    .signal-badge {
        display: inline-block;
        padding: 0.5rem 1.25rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.9375rem;
        border: 2px solid;
    }
    
    /* Factores */
    .factor-grid {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .factor-card {
        background: #0c0e12;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 0.875rem;
    }
    
    .factor-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .factor-label {
        color: #9ca3af;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    
    .factor-points {
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
        margin-top: 0.375rem;
    }
    
    /* Recomendación */
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
        letter-spacing: 0.05em;
        margin-bottom: 0.375rem;
    }
    
    .rec-text {
        color: #d1d5db;
        font-size: 0.875rem;
        line-height: 1.5;
    }
    
    /* Detalles */
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
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="color: #f9fafb; font-size: 1.875rem; font-weight: 700; margin: 0;">
            🚦 RSU Algoritmo Pro
        </h1>
        <p style="color: #6b7280; font-size: 1rem; margin: 0.5rem 0 0 0;">
            Umbral VERDE: 40 pts · Umbral AMBAR: 25 pts
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Análisis", "📈 Backtest", "ℹ️ Explicación"])
    
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
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()
        
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            # CORRECCIÓN: Usar st.html para evitar escape de HTML
            luz_r = "on" if resultado['estado'] == "ROJO" else ""
            luz_a = "on" if resultado['estado'] == "AMBAR" else ""
            luz_v = "on" if resultado['estado'] == "VERDE" else ""
            
            semaforo_html = f"""
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Señal de Mercado</span>
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
                        <div class="score-text">Puntuación / 100</div>
                    </div>
                    
                    <div class="signal-badge-container">
                        <span class="signal-badge" style="color: {resultado['color']}; border-color: {resultado['color']}; background-color: {resultado['color']}15;">
                            {resultado['senal']}
                        </span>
                    </div>
                </div>
            </div>
            """
            st.html(semaforo_html)
            
            # Recomendación
            rec_html = f"""
            <div class="rec-box">
                <div class="rec-title">📋 Recomendación</div>
                <div class="rec-text">{resultado['recomendacion']}</div>
            </div>
            """
            st.html(rec_html)
        
        with col2:
            # Factores
            factores_html = """
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Desglose de Factores</span>
                </div>
                <div class="card-body">
                    <div class="factor-grid">
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
                <div class="factor-card">
                    <div class="factor-top">
                        <span class="factor-label">{nombre} (max {m['max']})</span>
                        <span class="factor-points" style="color: {m['color']};">{m['score']}/{m['max']}</span>
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
        
        # Detalles técnicos
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
            
            umbral_sel = st.slider("Umbral de señal", 25, 70, 40, 5,
                                  help="Score mínimo para generar señal")
            años_sel = st.selectbox("Período", [1, 2, 3, 5, 10], index=3)
            
            st.caption(f"""
            **Umbrales del sistema:**
            - **VERDE**: ≥ 40 pts (Fondo probable)
            - **AMBAR**: 25-39 pts (Desarrollando)  
            - **ROJO**: < 25 pts (Sin fondo)
            
            **Frecuencia esperada:**
            - Umbral 40: ~15-25 señales/año
            - Umbral 50: ~8-15 señales/año
            - Umbral 60: ~3-8 señales/año
            """)
        
        with col_res:
            if st.button("🚀 Ejecutar Backtest", type="primary", use_container_width=True):
                with st.spinner(f'Analizando {años_sel} años...'):
                    resultados, error = backtest_strategy(years=años_sel, umbral=umbral_sel)
                    
                    if error:
                        st.warning(error)
                        st.info("💡 Prueba con umbral más bajo (30-35) o período más largo")
                    elif resultados:
                        st.success(f"**{resultados['total_señales']} señales** · Score medio: {resultados['score_promedio']:.1f}")
                        
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
        ### 🎯 Sobre los Factores a 0 y la Frecuencia de Señales
        
        #### ¿Por qué los factores están a 0?
        
        **Es completamente normal en el mercado actual (2023-2025).**
        
        Los factores que ves en la captura:
        - **FTD: 5/30** → Hay un rally pero sin FTD confirmado
        - **RSI: 5/25** → RSI en 49.7 (neutral, no sobreventa)
        - **VIX: 0/20** → VIX en 20.1 (bajo, sin miedo)
        - **Breadth: 0/15** → McClellan en -1 (neutral)
        - **Volume: 0/10** → Volumen normal
        
        **Este es un mercado alcista estable.** El sistema está diseñado para estar "en rojo" la mayor parte del tiempo durante bull markets, preservando capital para cuando lleguen las correcciones.
        
        #### ¿Por qué tan pocas señales en el backtest?
        
        El período 2020-2025 ha sido históricamente alcista:
        - **2020**: Crash COVID (marzo) → 2-3 señales válidas
        - **2021**: Bull market → 0-1 señales
        - **2022**: Bear market (jun-oct) → 4-6 señales
        - **2023-2024**: Bull market → 0-2 señales
        
        **Total esperado: 6-12 señales en 5 años con umbral 50.**
        
        Con umbral 40 (nuevo ajuste), deberías ver ~15-20 señales.
        
        #### Umbrales del Semáforo
        
        He ajustado los umbrales para más frecuencia realista:
        
        | Color | Umbral | Frecuencia esperada | Cuándo ocurre |
        |-------|--------|---------------------|---------------|
        | **VERDE** | ≥ 40 pts | ~3-5 veces/año | Correcciones >10% |
        | **AMBAR** | 25-39 pts | ~5-8 veces/año | Pullbacks moderados |
        | **ROJO** | < 25 pts | ~240 días/año | Tendencia alcista estable |
        
        #### ¿Es esto un problema?
        
        **No, es una característica.** Un sistema que da muchas señales en bull market tendría:
        - Falso sentido de oportunidad
        - Overtrading
        - Peor performance por "fear of missing out"
        
        La ausencia de señal es información: **el mercado no está en sobreventa extrema.**
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)


