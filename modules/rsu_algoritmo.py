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
    """
    Proxy del McClellan Oscillator usando % de stocks sobre/bajo SMA 50.
    Como no tenemos datos de advancing/declining issues, usamos la distribución
    de retornos como proxy de breadth.
    """
    if df is None or len(df) < 50:
        return None
    
    # Calcular retornos diarios
    returns = df['Close'].pct_change()
    
    # Contar días positivos vs negativos en ventana de 19 días (EMA 19)
    advancers = (returns > 0).rolling(window=19).sum()
    decliners = (returns < 0).rolling(window=19).sum()
    total = advancers + decliners
    
    # Evitar división por cero
    total = total.replace(0, np.nan)
    
    # Net advances normalizado
    net_advances = ((advancers - decliners) / total) * 1000
    
    # EMA 19 y 39 del net advances
    ema_19 = net_advances.ewm(span=19, adjust=False).mean()
    ema_39 = net_advances.ewm(span=39, adjust=False).mean()
    
    mcClellan = ema_19 - ema_39
    return mcClellan.iloc[-1] if not pd.isna(mcClellan.iloc[-1]) else 0

def detectar_fondo_comprehensivo(df_spy, df_vix=None):
    """
    Sistema de detección de fondos multi-factor.
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
        elif ftd_data.get('signal') in ['potential', 'early']:
            ftd_score = 15
            detalles.append("~ FTD en desarrollo (+15)")
        elif ftd_data.get('signal') == 'active':
            ftd_score = 5
            detalles.append("• Rally activo sin FTD (+5)")
        else:
            detalles.append("✗ Sin FTD (0)")
    else:
        detalles.append("✗ Sin datos FTD (0)")
    
    score += ftd_score
    metricas['FTD'] = {'score': ftd_score, 'max': 30, 'color': '#2962ff'}
    
    # 2. RSI Diario (25 puntos)
    rsi_series = calcular_rsi(df_spy['Close'], 14)
    rsi = rsi_series.iloc[-1]
    rsi_score = 0
    
    if rsi < 25:
        rsi_score = 25
        detalles.append(f"✓ RSI {rsi:.1f} < 25 (Sobreventa extrema) (+25)")
    elif rsi < 35:
        rsi_score = 20
        detalles.append(f"✓ RSI {rsi:.1f} < 35 (Sobreventa fuerte) (+20)")
    elif rsi < 45:
        rsi_score = 10
        detalles.append(f"~ RSI {rsi:.1f} < 45 (Sobreventa moderada) (+10)")
    elif rsi > 75:
        rsi_score = -10
        detalles.append(f"✗ RSI {rsi:.1f} > 75 (Sobrecompra) (-10)")
    else:
        detalles.append(f"• RSI {rsi:.1f} neutral (0)")
    
    score += rsi_score
    metricas['RSI'] = {'score': max(0, rsi_score), 'max': 25, 'color': '#00ffad', 'raw_value': rsi}
    
    # 3. VIX / Volatilidad (20 puntos)
    vix_score = 0
    if df_vix is not None and len(df_vix) > 20:
        vix_actual = df_vix['Close'].iloc[-1]
        vix_sma20 = df_vix['Close'].rolling(20).mean().iloc[-1]
        
        if vix_actual > 35:
            vix_score = 20
            detalles.append(f"✓ VIX {vix_actual:.1f} > 35 (Pánico extremo) (+20)")
        elif vix_actual > 30:
            vix_score = 15
            detalles.append(f"✓ VIX {vix_actual:.1f} > 30 (Miedo significativo) (+15)")
        elif vix_actual > vix_sma20 * 1.3:
            vix_score = 10
            detalles.append(f"~ VIX elevado vs media (+10)")
        else:
            detalles.append(f"• VIX {vix_actual:.1f} normal (0)")
        
        metricas['VIX'] = {'score': vix_score, 'max': 20, 'color': '#ff9800', 'raw_value': vix_actual}
    else:
        # Proxy usando ATR de SPY
        atr = calcular_atr(df_spy).iloc[-1]
        atr_medio = calcular_atr(df_spy).rolling(20).mean().iloc[-1]
        ratio_atr = atr / atr_medio if atr_medio > 0 else 1
        
        if ratio_atr > 2.0:
            vix_score = 15
            detalles.append(f"~ ATR {ratio_atr:.1f}x normal (proxy VIX alto) (+15)")
        elif ratio_atr > 1.5:
            vix_score = 10
            detalles.append(f"~ ATR {ratio_atr:.1f}x normal (proxy VIX medio) (+10)")
        else:
            detalles.append(f"• Volatilidad normal (0)")
        
        metricas['VIX'] = {'score': vix_score, 'max': 20, 'color': '#ff9800', 'raw_value': ratio_atr, 'is_proxy': True}
    
    score += vix_score
    
    # 4. McClellan Oscillator Proxy (15 puntos)
    mcclellan = calcular_mcclellan_proxy(df_spy)
    breadth_score = 0
    
    if mcclellan < -80:
        breadth_score = 15
        detalles.append(f"✓ McClellan {mcclellan:.0f} < -80 (Oversold extremo) (+15)")
    elif mcclellan < -50:
        breadth_score = 10
        detalles.append(f"~ McClellan {mcclellan:.0f} < -50 (Oversold) (+10)")
    elif mcclellan < -20:
        breadth_score = 5
        detalles.append(f"• McClellan {mcclellan:.0f} < -20 (Débil) (+5)")
    else:
        detalles.append(f"• McClellan {mcclellan:.0f} neutral (0)")
    
    score += breadth_score
    metricas['Breadth'] = {'score': breadth_score, 'max': 15, 'color': '#9c27b0', 'raw_value': mcclellan}
    
    # 5. Volume Analysis (10 puntos)
    vol_actual = df_spy['Volume'].iloc[-1]
    vol_media = df_spy['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = vol_actual / vol_media if vol_media > 0 else 1
    vol_score = 0
    
    if vol_ratio > 2.0:
        vol_score = 10
        detalles.append(f"✓ Volumen {vol_ratio:.1f}x media (Capitulación) (+10)")
    elif vol_ratio > 1.5:
        vol_score = 7
        detalles.append(f"~ Volumen {vol_ratio:.1f}x media (Alto) (+7)")
    elif vol_ratio > 1.2:
        vol_score = 3
        detalles.append(f"• Volumen {vol_ratio:.1f}x media (+3)")
    else:
        detalles.append(f"• Volumen normal (0)")
    
    score += vol_score
    metricas['Volume'] = {'score': vol_score, 'max': 10, 'color': '#f23645', 'raw_value': vol_ratio}
    
    # Determinar estado
    if score >= 70:
        estado = "VERDE"
        senal = "FONDO PROBABLE"
        color = "#00ffad"
        recomendacion = "Setup óptimo: Considerar entrada gradual (25% posición inicial) con stop-loss -7%"
    elif score >= 50:
        estado = "AMBAR"
        senal = "DESARROLLANDO"
        color = "#ff9800"
        recomendacion = "Condiciones mejorando: Preparar watchlist, esperar confirmación adicional o entrada parcial (10-15%)"
    elif score >= 30:
        estado = "AMBAR-BAJO"
        senal = "PRE-SETUP"
        color = "#ff9800"
        recomendacion = "Algunos factores presentes pero insuficientes. Mantener liquidez, monitorear evolución"
    else:
        estado = "ROJO"
        senal = "SIN FONDO"
        color = "#f23645"
        recomendacion = "Sin condiciones de fondo detectadas. Preservar capital, evitar compras agresivas"
    
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
    
    if distancia_minimo > 0.10:
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
                'color': '#00ffad'
            }
    
    if dias_rally < 4:
        return {'estado': 'RALLY_EARLY', 'signal': 'early', 'dias_rally': dias_rally}
    
    return {'estado': 'RALLY_ACTIVE', 'signal': 'active', 'dias_rally': dias_rally}

def backtest_strategy(ticker_symbol="SPY", years=2):
    """
    Backtesting robusto de la estrategia.
    Detecta señales con score >= 50 (no solo 70) para tener suficientes muestras.
    """
    try:
        # Descargar datos históricos
        ticker = yf.Ticker(ticker_symbol)
        df_hist = ticker.history(period=f"{years}y", interval="1d")
        
        if df_hist.empty or len(df_hist) < 100:
            return None, "Datos insuficientes"
        
        # Intentar descargar VIX histórico
        try:
            vix_ticker = yf.Ticker("^VIX")
            vix_hist = vix_ticker.history(period=f"{years}y", interval="1d")
        except:
            vix_hist = None
        
        señales = []
        
        # Ventana de lookback para análisis (mínimo 60 días de datos)
        for i in range(60, len(df_hist) - 20):
            ventana_df = df_hist.iloc[:i]
            vix_window = vix_hist.iloc[:i] if vix_hist is not None else None
            
            resultado = detectar_fondo_comprehensivo(ventana_df, vix_window)
            
            # Capturar señales con score >= 50 (no solo 70) para tener muestras significativas
            if resultado['score'] >= 50:
                precio_entrada = df_hist['Close'].iloc[i]
                precio_salida_5d = df_hist['Close'].iloc[min(i + 5, len(df_hist) - 1)]
                precio_salida_10d = df_hist['Close'].iloc[min(i + 10, len(df_hist) - 1)]
                precio_salida_20d = df_hist['Close'].iloc[min(i + 20, len(df_hist) - 1)]
                
                retorno_5d = ((precio_salida_5d - precio_entrada) / precio_entrada) * 100
                retorno_10d = ((precio_salida_10d - precio_entrada) / precio_entrada) * 100
                retorno_20d = ((precio_salida_20d - precio_entrada) / precio_entrada) * 100
                
                señales.append({
                    'fecha': df_hist.index[i].strftime('%Y-%m-%d'),
                    'score': resultado['score'],
                    'precio_entrada': round(precio_entrada, 2),
                    'retorno_5d': round(retorno_5d, 2),
                    'retorno_10d': round(retorno_10d, 2),
                    'retorno_20d': round(retorno_20d, 2),
                    'exito_5d': retorno_5d > 0,
                    'exito_10d': retorno_10d > 0,
                    'exito_20d': retorno_20d > 0
                })
        
        if not señales:
            return None, "No se generaron señales con score >= 50 en el período analizado"
        
        df_resultados = pd.DataFrame(señales)
        
        # Métricas de performance
        metricas = {
            'total_señales': len(señales),
            'score_promedio': df_resultados['score'].mean(),
            'win_rate_5d': (df_resultados['exito_5d'].mean() * 100),
            'win_rate_10d': (df_resultados['exito_10d'].mean() * 100),
            'win_rate_20d': (df_resultados['exito_20d'].mean() * 100),
            'retorno_medio_5d': df_resultados['retorno_5d'].mean(),
            'retorno_medio_10d': df_resultados['retorno_10d'].mean(),
            'retorno_medio_20d': df_resultados['retorno_20d'].mean(),
            'retorno_total_20d': df_resultados['retorno_20d'].sum(),
            'mejor_señal': df_resultados.loc[df_resultados['retorno_20d'].idxmax()].to_dict(),
            'peor_señal': df_resultados.loc[df_resultados['retorno_20d'].idxmin()].to_dict(),
            'detalle': df_resultados
        }
        
        return metricas, None
        
    except Exception as e:
        return None, f"Error en backtest: {str(e)}"

def render():
    set_style()
    
    # CSS global
    st.markdown("""
    <style>
    .main-container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .rsu-box { background: #11141a; border: 1px solid #1a1e26; border-radius: 10px; margin-bottom: 20px; overflow: hidden; }
    .rsu-head { background: #0c0e12; padding: 15px 20px; border-bottom: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center; }
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
    .score-big { font-size: 3.5rem; font-weight: bold; color: white; text-align: center; margin: 10px 0; }
    .score-label { color: #888; font-size: 12px; text-align: center; text-transform: uppercase; letter-spacing: 1px; }
    .factor-container { background: #0c0e12; border-radius: 8px; padding: 15px; margin: 10px 0; }
    .factor-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .factor-name { color: #888; font-size: 11px; text-transform: uppercase; font-weight: bold; }
    .factor-score { color: white; font-size: 14px; font-weight: bold; }
    .progress-bg { width: 100%; height: 8px; background: #1a1e26; border-radius: 4px; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
    .recommendation-box { background: rgba(0, 255, 173, 0.05); border-left: 4px solid #00ffad; padding: 15px; margin-top: 20px; border-radius: 0 8px 8px 0; }
    .detail-item { padding: 8px 0; border-bottom: 1px solid #1a1e26; color: #ccc; font-size: 13px; }
    .detail-item:last-child { border-bottom: none; }
    .badge { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("<h1 style='color:white;margin-bottom:5px;'>🚦 RSU ALGORITMO PRO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#888;font-size:14px;margin-top:0;'>Detección de Fondos Multi-Factor (FTD + RSI + VIX + Breadth + Volume)</p>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Análisis Actual", "📈 Backtesting", "ℹ️ Metodología"])
    
    with tab1:
        with st.spinner('Analizando múltiples factores de mercado...'):
            # Obtener datos
            try:
                ticker = yf.Ticker("SPY")
                df_daily = ticker.history(interval="1d", period="6mo")
                
                # Intentar obtener VIX
                try:
                    vix = yf.Ticker("^VIX")
                    df_vix = vix.history(interval="1d", period="6mo")
                except:
                    df_vix = None
                
                if df_daily.empty:
                    st.error("No se pudieron obtener datos de SPY")
                    st.stop()
                
                resultado = detectar_fondo_comprehensivo(df_daily, df_vix)
                
            except Exception as e:
                st.error(f"Error al obtener datos: {e}")
                st.stop()
        
        # Layout principal
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            # Semáforo con Score
            luz_r = "on" if resultado['estado'] in ["ROJO"] else ""
            luz_a = "on" if resultado['estado'] in ["AMBAR", "AMBAR-BAJO"] else ""
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
                    <div class="score-big" style="color:{resultado['color']};">{resultado['score']}</div>
                    <div class="score-label">PUNTUACIÓN DE CONFIANZA (máx {resultado['max_score']})</div>
                    <div class="badge" style="background:{resultado['color']}22; border: 2px solid {resultado['color']}; color:{resultado['color']}; margin-top:15px;">
                        {resultado['senal']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Recomendación estratégica
            st.markdown(f"""
            <div class="recommendation-box">
                <div style="color:#00ffad;font-weight:bold;margin-bottom:8px;font-size:14px;">📋 RECOMENDACIÓN ESTRATÉGICA</div>
                <div style="color:#ccc;font-size:13px;line-height:1.5;">{resultado['recomendacion']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_right:
            # Panel de Factores DENTRO del contenedor principal
            st.markdown("""
            <div class="rsu-box">
                <div class="rsu-head">
                    <span class="rsu-title">Desglose de Factores</span>
                </div>
                <div class="rsu-body">
            """, unsafe_allow_html=True)
            
            # Renderizar cada factor
            factores_orden = ['FTD', 'RSI', 'VIX', 'Breadth', 'Volume']
            for factor_key in factores_orden:
                if factor_key in resultado['metricas']:
                    m = resultado['metricas'][factor_key]
                    nombre_display = {
                        'FTD': 'Follow-Through Day',
                        'RSI': 'RSI Diario < 35',
                        'VIX': 'VIX Extremo' if not m.get('is_proxy') else 'Volatilidad (Proxy VIX)',
                        'Breadth': 'Breadth Thrust (McClellan)',
                        'Volume': 'Volumen Capitulación'
                    }[factor_key]
                    
                    pct = (m['score'] / m['max']) * 100 if m['max'] > 0 else 0
                    raw_val = m.get('raw_value', 0)
                    
                    # Formatear valor raw
                    if factor_key == 'RSI':
                        raw_text = f"RSI: {raw_val:.1f}"
                    elif factor_key == 'VIX':
                        raw_text = f"{raw_val:.1f}" if not m.get('is_proxy') else f"{raw_val:.1f}x"
                    elif factor_key == 'Breadth':
                        raw_text = f"{raw_val:.0f}"
                    elif factor_key == 'Volume':
                        raw_text = f"{raw_val:.1f}x"
                    else:
                        raw_text = ""
                    
                    st.markdown(f"""
                    <div class="factor-container">
                        <div class="factor-header">
                            <span class="factor-name">{nombre_display} (max {m['max']} pts)</span>
                            <span class="factor-score" style="color:{m['color']};">{m['score']}/{m['max']}</span>
                        </div>
                        <div class="progress-bg">
                            <div class="progress-fill" style="width:{pct}%; background:{m['color']};"></div>
                        </div>
                        {f'<div style="color:#666; font-size:11px; margin-top:4px;">{raw_text}</div>' if raw_text else ''}
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Detalles técnicos expandibles
        with st.expander("🔍 Ver detalles técnicos completos", expanded=False):
            st.markdown("### Análisis detallado de factores:")
            for detalle in resultado['detalles']:
                # Colorear según el tipo de detalle
                if detalle.startswith('✓'):
                    color = '#00ffad'
                elif detalle.startswith('~'):
                    color = '#ff9800'
                elif detalle.startswith('✗'):
                    color = '#f23645'
                else:
                    color = '#888'
                
                st.markdown(f'<div class="detail-item" style="color:{color};">{detalle}</div>', unsafe_allow_html=True)
            
            # Información adicional del FTD si existe
            if resultado['ftd_data']:
                ftd = resultado['ftd_data']
                st.markdown("---")
                st.markdown("### Estado Follow-Through Day:")
                st.write(f"- **Estado**: {ftd.get('estado', 'N/A')}")
                st.write(f"- **Señal**: {ftd.get('signal', 'N/A')}")
                if 'dias_rally' in ftd:
                    st.write(f"- **Días de rally**: {ftd['dias_rally']}")
                if 'retorno' in ftd:
                    st.write(f"- **Último retorno**: {ftd['retorno']:.2f}%")
    
    with tab2:
        st.markdown("### 📊 Backtesting Histórico")
        st.info("Análisis de performance de señales con score ≥ 50 en los últimos 2 años. Este umbral más bajo permite obtener muestras estadísticamente significativas.")
        
        col_bt1, col_bt2 = st.columns([1, 3])
        with col_bt1:
            umbral_bt = st.slider("Umbral de señal", min_value=30, max_value=80, value=50, step=5, 
                                  help="Score mínimo para considerar una señal válida en el backtest")
            años_bt = st.selectbox("Período", options=[1, 2, 3, 5], index=1)
        
        with col_bt2:
            if st.button("🚀 Ejecutar Backtest Completo", type="primary", use_container_width=True):
                with st.spinner(f'Analizando {años_bt} años de datos históricos... Esto puede tomar 1-2 minutos'):
                    resultados_bt, error = backtest_strategy(years=años_bt)
                    
                    if error:
                        st.warning(error)
                    elif resultados_bt:
                        # Métricas principales
                        st.success(f"Backtest completado: {resultados_bt['total_señales']} señales generadas")
                        
                        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                        m_col1.metric("Total Señales", resultados_bt['total_señales'])
                        m_col2.metric("Score Promedio", f"{resultados_bt['score_promedio']:.1f}")
                        m_col3.metric("Win Rate (20d)", f"{resultados_bt['win_rate_20d']:.1f}%")
                        m_col4.metric("Retorno Medio (20d)", f"{resultados_bt['retorno_medio_20d']:.2f}%")
                        
                        # Gráfico de distribución de retornos
                        st.markdown("#### Distribución de Retornos")
                        chart_data = resultados_bt['detalle'][['retorno_5d', 'retorno_10d', 'retorno_20d']].rename(columns={
                            'retorno_5d': '5 días',
                            'retorno_10d': '10 días',
                            'retorno_20d': '20 días'
                        })
                        st.bar_chart(chart_data.mean())
                        
                        # Tabla detallada
                        with st.expander("Ver tabla detallada de operaciones"):
                            st.dataframe(
                                resultados_bt['detalle'].sort_values('fecha', ascending=False),
                                use_container_width=True,
                                hide_index=True
                            )
                        
                        # Mejor y peor señal
                        col_best, col_worst = st.columns(2)
                        with col_best:
                            st.markdown("#### 🏆 Mejor Señal")
                            best = resultados_bt['mejor_señal']
                            st.write(f"**Fecha**: {best['fecha']}")
                            st.write(f"**Score**: {best['score']}")
                            st.write(f"**Retorno 20d**: +{best['retorno_20d']}%")
                        
                        with col_worst:
                            st.markdown("#### ⚠️ Peor Señal")
                            worst = resultados_bt['peor_señal']
                            st.write(f"**Fecha**: {worst['fecha']}")
                            st.write(f"**Score**: {worst['score']}")
                            st.write(f"**Retorno 20d**: {worst['retorno_20d']}%")
    
    with tab3:
        st.markdown("""
        ### 🔬 Metodología Científica y Limitaciones
        
        **ADVERTENCIA IMPORTANTE**: Esta herramienta es un asistente de análisis técnico, no un sistema de trading automático garantizado. El market timing es inherentemente probabilístico.
        
        #### Sistema de Puntuación (0-100 puntos)
        
        | Factor | Peso | Descripción | Condiciones óptimas |
        |--------|------|-------------|---------------------|
        | **Follow-Through Day** | 30% | Confirmación O'Neil de cambio de tendencia | Día 4-7, +1.5%, volumen ↑ |
        | **RSI Diario** | 25% | Momentum sobrecomprado/sobreventa | < 30 para fondo, > 75 reduce score |
        | **VIX/Volatilidad** | 20% | Índice de miedo del mercado | > 30 indica pánico (contrarian) |
        | **Breadth (McClellan)** | 15% | Amplitud del mercado | < -50 indica oversold de amplitud |
        | **Volumen** | 10% | Capitulación vendedora | > 1.5x media diaria |
        
        #### Umbrales de Decisión
        
        - **Score 70-100 (VERDE)**: Múltiples factores alineados. Fondo probable pero no garantizado.
        - **Score 50-69 (AMBAR)**: Condiciones desarrollándose. Setup parcial o en formación.
        - **Score 30-49 (AMBAR-BAJO)**: Algunos factores presentes pero insuficientes.
        - **Score 0-29 (ROJO)**: Sin condiciones de fondo detectadas.
        
        #### Limitaciones Conocidas
        
        1. **Falsos positivos**: En bear markets prolongados (2008, 2022), pueden producirse 3-4 señales falsas antes del fondo real.
        2. **Retraso**: El sistema detecta fondos, no los predice. Siempre hay lag.
        3. **Proxy del McClellan**: Sin datos reales de advancing/declining issues, el cálculo es aproximado.
        4. **VIX**: No disponible 24/7; usamos proxy de volatilidad ATR cuando no hay datos.
        
        #### Gestión de Riesgo Recomendada
        
        1. **Posición**: Nunca > 25% del capital en una señal inicial
        2. **Stop-loss**: -7% del punto de entrada (obligatorio)
        3. **Escalado**: Añadir 25% más solo si funciona (pyramiding)
        4. **Time-stop**: Reevaluar si no hay movimiento en 10 días
        
        #### Referencias
        
        - O'Neil, W. (2009). *How to Make Money in Stocks*
        - McClellan, S. & M. (1998). *Patterns for Profit*
        - Bulkowski, T. (2010). *Encyclopedia of Candlestick Charts*
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)



