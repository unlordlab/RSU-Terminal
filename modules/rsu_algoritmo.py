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

# Constantes de sectores para el McClellan mejorado
SECTOR_ETFS = ['XLK', 'XLF', 'XLV', 'XLY', 'XLP', 'XLI', 'XLB', 'XLRE', 'XLU']

def calcular_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def detectar_divergencia_bullish(df, lookback=30):
    """
    Detecta divergencia alcista regular: precio hace lower low, RSI hace higher low.
    Retorna +15 puntos si se detecta, 0 si no.
    """
    if len(df) < lookback + 14:
        return 0, None
    
    # Calcular RSI
    rsi = calcular_rsi(df['Close'], 14)
    
    # Encontrar mínimos locales en precio y RSI
    price = df['Close'].iloc[-lookback:]
    rsi_series = rsi.iloc[-lookback:]
    
    # Buscar dos mínimos consecutivos
    price_min_idx = price.rolling(window=5, center=True).min().dropna()
    rsi_min_idx = rsi_series.rolling(window=5, center=True).min().dropna()
    
    # Encontrar índices de mínimos locales
    price_lows = []
    rsi_lows = []
    
    for i in range(2, len(price)-2):
        if price.iloc[i] == price.iloc[i-2:i+3].min() and price.iloc[i] < price.iloc[i-1] and price.iloc[i] < price.iloc[i+1]:
            price_lows.append((i, price.iloc[i]))
        if rsi_series.iloc[i] == rsi_series.iloc[i-2:i+3].min() and rsi_series.iloc[i] < rsi_series.iloc[i-1] and rsi_series.iloc[i] < rsi_series.iloc[i+1]:
            rsi_lows.append((i, rsi_series.iloc[i]))
    
    if len(price_lows) >= 2 and len(rsi_lows) >= 2:
        # Tomar los dos últimos mínimos
        last_price_low = price_lows[-1]
        prev_price_low = price_lows[-2]
        last_rsi_low = rsi_lows[-1]
        prev_rsi_low = rsi_lows[-2]
        
        # Verificar divergencia: precio lower low, RSI higher low
        if last_price_low[1] < prev_price_low[1] and last_rsi_low[1] > prev_rsi_low[1]:
            return 15, {
                'tipo': 'Bullish Regular',
                'precio_prev': prev_price_low[1],
                'precio_last': last_price_low[1],
                'rsi_prev': prev_rsi_low[1],
                'rsi_last': last_rsi_low[1],
                'bonus': 15
            }
    
    return 0, None

def calcular_mcclellan_proxy_mejorado(df_spy, sector_data=None):
    """
    McClellan Proxy mejorado usando sectores (XLK, XLF, XLV, etc.) + SPY.
    Si no hay datos de sectores, usa el método anterior como fallback.
    """
    if df_spy is None or len(df_spy) < 50:
        return None, "Datos insuficientes"
    
    # Si tenemos datos de sectores, calcular amplitud real
    if sector_data and len(sector_data) > 0:
        try:
            # Calcular retornos diarios de cada sector
            sector_returns = {}
            valid_sectors = 0
            
            for sector, df in sector_data.items():
                if df is not None and len(df) > 1:
                    returns = df['Close'].pct_change()
                    sector_returns[sector] = returns
                    valid_sectors += 1
            
            if valid_sectors >= 3:
                # Crear DataFrame con retornos de sectores
                returns_df = pd.DataFrame(sector_returns)
                
                # Contar sectores positivos vs negativos por día
                advancers = (returns_df > 0).sum(axis=1)
                decliners = (returns_df < 0).sum(axis=1)
                total = advancers + decliners
                
                # Evitar división por cero
                total = total.replace(0, np.nan)
                
                # Net advances como porcentaje (RANA style)
                net_advances = ((advancers - decliners) / total) * 1000
                
                # EMA 19 y 39
                ema_19 = net_advances.ewm(span=19, adjust=False).mean()
                ema_39 = net_advances.ewm(span=39, adjust=False).mean()
                
                mcclellan = ema_19 - ema_39
                valor_actual = mcclellan.iloc[-1] if not pd.isna(mcclellan.iloc[-1]) else 0
                
                return valor_actual, f"Amplitud sectorial ({valid_sectors} ETFs)"
                
        except Exception as e:
            pass  # Fallback al método original
    
    # Fallback: método original basado solo en SPY
    returns = df_spy['Close'].pct_change()
    advancers = (returns > 0).rolling(window=19).sum()
    decliners = (returns < 0).rolling(window=19).sum()
    total = advancers + decliners
    total = total.replace(0, np.nan)
    
    net_advances = ((advancers - decliners) / total) * 1000
    ema_19 = net_advances.ewm(span=19, adjust=False).mean()
    ema_39 = net_advances.ewm(span=39, adjust=False).mean()
    
    mcclellan = ema_19 - ema_39
    valor_actual = mcclellan.iloc[-1] if not pd.isna(mcclellan.iloc[-1]) else 0
    
    return valor_actual, "Proxy SPY (fallback)"

def calcular_medias_moviles(df):
    """Calcula SMA 50, 200 y EMA 21."""
    sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
    sma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
    ema_21 = df['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
    
    return {
        'sma_50': sma_50,
        'sma_200': sma_200,
        'ema_21': ema_21,
        'price': df['Close'].iloc[-1]
    }

def verificar_ftd_follow_through(df, ftd_idx, dias_verificacion=3):
    """
    Verifica si después de un FTD confirmado, el precio supera el máximo del día FTD
    en los siguientes 'dias_verificacion' días.
    Retorna: True si hay seguimiento, False si falla (lateralización).
    """
    if ftd_idx is None or ftd_idx >= len(df) - 1:
        return True  # No podemos verificar, asumimos válido
    
    precio_ftd_max = df['High'].iloc[ftd_idx]
    
    # Verificar los siguientes días
    dias_disponibles = min(dias_verificacion, len(df) - ftd_idx - 1)
    
    for i in range(1, dias_disponibles + 1):
        if df['High'].iloc[ftd_idx + i] > precio_ftd_max:
            return True  # Superó el máximo, hay seguimiento
    
    return False  # No superó, FTD débil/falso

def detectar_fondo_comprehensivo(df_spy, df_vix=None, sector_data=None):
    """
    Sistema de detección de fondos multi-factor V2.0
    Pesos rebalanceados y nuevos filtros de calidad.
    """
    score = 0
    max_score = 100
    detalles = []
    metricas = {}
    penalizaciones = []
    
    # Obtener métricas de medias móviles
    mm = calcular_medias_moviles(df_spy)
    price = mm['price']
    
    # 1. DIVERGENCIA BULLISH (Nuevo factor +15 pts)
    div_score, div_data = detectar_divergencia_bullish(df_spy)
    if div_score > 0:
        score += div_score
        detalles.append(f"✓ Divergencia Alcista detectada (+{div_score})")
        metricas['Divergencia'] = {'score': div_score, 'max': 15, 'color': '#ffd700', 'raw_value': div_data}
    else:
        detalles.append("• Sin divergencia detectada (0)")
        metricas['Divergencia'] = {'score': 0, 'max': 15, 'color': '#ffd700'}
    
    # 2. FTD Detection (35 pts - subido de 30)
    ftd_data = detectar_follow_through_day(df_spy)
    ftd_score = 0
    ftd_idx = None
    
    if ftd_data:
        if ftd_data.get('signal') == 'confirmed':
            ftd_score = 35
            ftd_idx = ftd_data.get('index')
            detalles.append("✓ FTD Confirmado (+35)")
            
            # Penalización si no supera EMA21 (trampa para toros)
            if price < mm['ema_21']:
                penalizacion = -10
                score += penalizacion
                penalizaciones.append(f"⚠️ FTD bajo EMA21 ({price:.2f} < {mm['ema_21']:.2f}) ({penalizacion})")
            
            # Verificación de seguimiento (Time Stop)
            if ftd_idx and not verificar_ftd_follow_through(df_spy, ftd_idx, 3):
                penalizacion = -5
                score += penalizacion
                penalizaciones.append(f"⚠️ FTD sin seguimiento en 3 días ({penalizacion})")
                
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
    metricas['FTD'] = {'score': max(0, ftd_score), 'max': 35, 'color': '#2962ff', 'raw_value': ftd_data}
    
    # 3. RSI Diario (15 pts - bajado de 25 para evitar redundancia con VIX)
    rsi_series = calcular_rsi(df_spy['Close'], 14)
    rsi = rsi_series.iloc[-1]
    rsi_score = 0
    
    if rsi < 25:
        rsi_score = 15
        detalles.append(f"✓ RSI {rsi:.1f} < 25 (Sobreventa extrema) (+15)")
    elif rsi < 35:
        rsi_score = 12
        detalles.append(f"✓ RSI {rsi:.1f} < 35 (Sobreventa fuerte) (+12)")
    elif rsi < 45:
        rsi_score = 5
        detalles.append(f"~ RSI {rsi:.1f} < 45 (Sobreventa moderada) (+5)")
    elif rsi > 75:
        rsi_score = -10
        detalles.append(f"✗ RSI {rsi:.1f} > 75 (Sobrecompra) (-10)")
    else:
        detalles.append(f"• RSI {rsi:.1f} neutral (0)")
    
    score += rsi_score
    metricas['RSI'] = {'score': max(0, rsi_score), 'max': 15, 'color': '#00ffad', 'raw_value': rsi}
    
    # 4. VIX / Volatilidad (20 pts - se mantiene como validador)
    vix_score = 0
    vix_valor = None
    
    if df_vix is not None and len(df_vix) > 20:
        vix_actual = df_vix['Close'].iloc[-1]
        vix_sma20 = df_vix['Close'].rolling(20).mean().iloc[-1]
        vix_valor = vix_actual
        
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
        
        # Validador: Si score técnico es alto pero VIX < 20 (complacencia), reducir confianza
        if score > 50 and vix_actual < 20:
            penalizacion = -10
            score += penalizacion
            penalizaciones.append(f"⚠️ Alta complacencia (VIX {vix_actual:.1f} < 20) ({penalizacion})")
        
        metricas['VIX'] = {'score': vix_score, 'max': 20, 'color': '#ff9800', 'raw_value': vix_actual}
    else:
        # Proxy usando ATR de SPY
        atr = calcular_atr(df_spy).iloc[-1]
        atr_medio = calcular_atr(df_spy).rolling(20).mean().iloc[-1]
        ratio_atr = atr / atr_medio if atr_medio > 0 else 1
        vix_valor = ratio_atr
        
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
    
    # 5. McClellan Oscillator Proxy Mejorado (20 pts - subido de 15)
    mcclellan, metodo = calcular_mcclellan_proxy_mejorado(df_spy, sector_data)
    breadth_score = 0
    
    if mcclellan < -80:
        breadth_score = 20
        detalles.append(f"✓ McClellan {mcclellan:.0f} < -80 (Oversold extremo) (+20) [{metodo}]")
    elif mcclellan < -50:
        breadth_score = 15
        detalles.append(f"~ McClellan {mcclellan:.0f} < -50 (Oversold) (+15) [{metodo}]")
    elif mcclellan < -20:
        breadth_score = 5
        detalles.append(f"• McClellan {mcclellan:.0f} < -20 (Débil) (+5) [{metodo}]")
    else:
        detalles.append(f"• McClellan {mcclellan:.0f} neutral (0) [{metodo}]")
    
    score += breadth_score
    metricas['Breadth'] = {'score': breadth_score, 'max': 20, 'color': '#9c27b0', 'raw_value': mcclellan, 'metodo': metodo}
    
    # 6. Volume Analysis (10 pts - se mantiene)
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
    
    # 7. FILTRO DE SEGURIDAD: SMA 200 (Penalización importante)
    sma200_penalty = 0
    if price < mm['sma_200']:
        sma200_penalty = -10
        score += sma200_penalty
        penalizaciones.append(f"⚠️ Precio bajo SMA200 ({price:.2f} < {mm['sma_200']:.2f}) ({sma200_penalty})")
        detalles.append(f"✗ Bajo SMA200 (Mercado bajista) ({sma200_penalty})")
    else:
        detalles.append(f"✓ Sobre SMA200 (Tendencia alcista) (0)")
    
    metricas['SMA200'] = {
        'score': 0 if sma200_penalty == 0 else abs(sma200_penalty), 
        'max': 0, 
        'color': '#ff5722', 
        'raw_value': price - mm['sma_200'],
        'is_penalty': sma200_penalty < 0
    }
    
    # Determinar estado con nuevo sistema de filtros
    volumen_bajo = vol_score < 3
    
    if score >= 70 and not volumen_bajo:
        estado = "VERDE"
        senal = "FONDO PROBABLE"
        color = "#00ffad"
        recomendacion = "Setup óptimo: Considerar entrada gradual (25% posición inicial) con stop-loss -7%. Múltiples factores alineados con volumen confirmado."
    elif score >= 70 and volumen_bajo:
        estado = "AMBAR"
        senal = "SETUP SIN VOLUMEN"
        color = "#ff9800"
        recomendacion = "Score alto pero volumen insuficiente. Esperar confirmación de volumen en siguiente sesión o reducir tamaño de posición (10-15%)."
    elif score >= 50:
        estado = "AMBAR"
        senal = "DESARROLLANDO"
        color = "#ff9800"
        recomendacion = "Condiciones mejorando: Preparar watchlist, esperar confirmación adicional o entrada parcial (10-15%)."
    elif score >= 30:
        estado = "AMBAR-BAJO"
        senal = "PRE-SETUP"
        color = "#ff9800"
        recomendacion = "Algunos factores presentes pero insuficientes. Mantener liquidez, monitorear evolución."
    else:
        estado = "ROJO"
        senal = "SIN FONDO"
        color = "#f23645"
        recomendacion = "Sin condiciones de fondo detectadas. Preservar capital, evitar compras agresivas."
    
    return {
        'score': score,
        'max_score': max_score,
        'estado': estado,
        'senal': senal,
        'color': color,
        'recomendacion': recomendacion,
        'detalles': detalles,
        'penalizaciones': penalizaciones,
        'ftd_data': ftd_data,
        'metricas': metricas,
        'medias_moviles': mm,
        'divergencia_data': div_data
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
    """Versión mejorada del FTD detection con índice de retorno."""
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
        return {'estado': 'NO_CONTEXT', 'signal': None, 'dias_rally': 0, 'index': None}
    
    min_idx_pos = recent.index.get_loc(recent_low_idx)
    if min_idx_pos >= len(recent) - 2:
        return {'estado': 'RALLY_TOO_RECENT', 'signal': None, 'dias_rally': 0, 'index': None}
    
    post_low = recent.iloc[min_idx_pos:].copy()
    
    rally_start_idx = None
    for i in range(1, len(post_low)):
        if post_low['price_up'].iloc[i]:
            rally_start_idx = i
            break
    
    if rally_start_idx is None:
        return {'estado': 'NO_RALLY', 'signal': None, 'dias_rally': 0, 'index': None}
    
    dias_rally = len(post_low) - rally_start_idx
    low_dia_1 = post_low.iloc[rally_start_idx]['Low']
    
    for i in range(rally_start_idx + 1, len(post_low)):
        if post_low.iloc[i]['Low'] < low_dia_1:
            return {'estado': 'RALLY_FAILED', 'signal': 'invalidated', 'dias_rally': dias_rally, 'index': None}
    
    # Calcular índice real en el dataframe original para verificación de seguimiento
    if 4 <= dias_rally <= 10:
        ultimo_dia = post_low.iloc[-1]
        ret_ultimo = ultimo_dia['returns'] * 100
        
        if ret_ultimo >= 1.5 and ultimo_dia['volume_increase']:
            # Encontrar el índice real
            idx_real = df.index.get_loc(post_low.index[-1])
            return {
                'estado': 'FTD_CONFIRMED',
                'signal': 'confirmed',
                'dias_rally': dias_rally,
                'retorno': ret_ultimo,
                'color': '#00ffad',
                'index': idx_real,
                'date': post_low.index[-1]
            }
    
    if dias_rally < 4:
        return {'estado': 'RALLY_EARLY', 'signal': 'early', 'dias_rally': dias_rally, 'index': None}
    
    return {'estado': 'RALLY_ACTIVE', 'signal': 'active', 'dias_rally': dias_rally, 'index': None}

def descargar_datos_sectores():
    """Descarga datos de ETFs sectoriales para el McClellan mejorado."""
    sector_data = {}
    with st.spinner('Cargando datos sectoriales para análisis de amplitud...'):
        for etf in SECTOR_ETFS:
            try:
                ticker = yf.Ticker(etf)
                df = ticker.history(period="3mo", interval="1d")
                if not df.empty:
                    sector_data[etf] = df
            except:
                continue
    return sector_data

def backtest_strategy(ticker_symbol="SPY", years=2, umbral_señal=50, usar_sectores=False):
    """
    Backtesting robusto con umbral configurable.
    
    Args:
        umbral_señal: Score mínimo para considerar entrada (comparar 50 vs 70 vs 80)
        usar_sectores: Si True, descarga datos sectoriales para cada punto (más lento pero preciso)
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
        
        # Pre-cargar datos sectoriales si se solicita (para backtest preciso pero lento)
        sectores_hist = {}
        if usar_sectores:
            st.info("Modo preciso: Descargando datos sectoriales para cada punto de análisis (esto puede tardar varios minutos)...")
            for etf in SECTOR_ETFS:
                try:
                    t = yf.Ticker(etf)
                    sectores_hist[etf] = t.history(period=f"{years}y", interval="1d")
                except:
                    continue
        
        señales = []
        
        # Ventana de lookback para análisis
        for i in range(60, len(df_hist) - 20):
            ventana_df = df_hist.iloc[:i]
            vix_window = vix_hist.iloc[:i] if vix_hist is not None else None
            
            # Para sectores, usar datos hasta i si están disponibles
            sector_window = None
            if usar_sectores and sectores_hist:
                sector_window = {}
                for etf, df_sec in sectores_hist.items():
                    if len(df_sec) >= i:
                        sector_window[etf] = df_sec.iloc[:i]
            
            resultado = detectar_fondo_comprehensivo(ventana_df, vix_window, sector_window)
            
            # Usar el umbral configurable en lugar de fijo 50
            if resultado['score'] >= umbral_señal:
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
                    'estado': resultado['estado'],
                    'precio_entrada': round(precio_entrada, 2),
                    'retorno_5d': round(retorno_5d, 2),
                    'retorno_10d': round(retorno_10d, 2),
                    'retorno_20d': round(retorno_20d, 2),
                    'exito_5d': retorno_5d > 0,
                    'exito_10d': retorno_10d > 0,
                    'exito_20d': retorno_20d > 0,
                    'umbral_usado': umbral_señal
                })
        
        if not señales:
            return None, f"No se generaron señales con score >= {umbral_señal} en el período analizado"
        
        df_resultados = pd.DataFrame(señales)
        
        # Métricas de performance
        metricas = {
            'total_señales': len(señales),
            'umbral_aplicado': umbral_señal,
            'score_promedio': df_resultados['score'].mean(),
            'win_rate_5d': (df_resultados['exito_5d'].mean() * 100),
            'win_rate_10d': (df_resultados['exito_10d'].mean() * 100),
            'win_rate_20d': (df_resultados['exito_20d'].mean() * 100),
            'retorno_medio_5d': df_resultados['retorno_5d'].mean(),
            'retorno_medio_10d': df_resultados['retorno_10d'].mean(),
            'retorno_medio_20d': df_resultados['retorno_20d'].mean(),
            'retorno_total_20d': df_resultados['retorno_20d'].sum(),
            'mejor_señal': df_resultados.loc[df_resultados['retorno_20d'].idxmax()].to_dict() if len(df_resultados) > 0 else None,
            'peor_señal': df_resultados.loc[df_resultados['retorno_20d'].idxmin()].to_dict() if len(df_resultados) > 0 else None,
            'detalle': df_resultados
        }
        
        return metricas, None
        
    except Exception as e:
        return None, f"Error en backtest: {str(e)}"

def crear_grafico_acumulacion(df, resultado):
    """
    Crea un gráfico de velas con zonas de acumulación sombreadas cuando score > 70.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Calcular score histórico para sombreado
    scores_historicos = []
    fechas = []
    
    # Solo calcular para los últimos 60 días para rendimiento
    ventana = min(60, len(df))
    
    for i in range(ventana, 0, -1):
        idx = len(df) - i
        ventana_df = df.iloc[:idx]
        
        # Calcular score simplificado para visualización
        rsi = calcular_rsi(ventana_df['Close'], 14).iloc[-1]
        vol_ratio = ventana_df['Volume'].iloc[-1] / ventana_df['Volume'].rolling(20).mean().iloc[-1]
        
        score_simple = 0
        if rsi < 35:
            score_simple += 40
        elif rsi < 45:
            score_simple += 20
        
        if vol_ratio > 1.5:
            score_simple += 20
        
        scores_historicos.append(score_simple)
        fechas.append(df.index[idx])
    
    # Crear figura
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.7, 0.3])
    
    # Gráfico de velas
    fig.add_trace(go.Candlestick(
        x=df.index[-ventana:],
        open=df['Open'].iloc[-ventana:],
        high=df['High'].iloc[-ventana:],
        low=df['Low'].iloc[-ventana:],
        close=df['Close'].iloc[-ventana:],
        name='SPY'
    ), row=1, col=1)
    
    # Añadir zona de acumulación (score > 70)
    for i, (fecha, score) in enumerate(zip(fechas, scores_historicos)):
        if score >= 70:
            fig.add_vrect(
                x0=fecha,
                x1=df.index[min(len(df)-ventana+i+1, len(df)-1)],
                fillcolor="rgba(0, 255, 173, 0.2)",
                layer="below",
                line_width=0,
                row=1, col=1
            )
    
    # Añadir EMA21 y SMA200
    ema21 = df['Close'].ewm(span=21).mean()
    sma200 = df['Close'].rolling(window=200).mean()
    
    fig.add_trace(go.Scatter(x=df.index[-ventana:], y=ema21.iloc[-ventana:],
                            mode='lines', name='EMA21', line=dict(color='#ff9800', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index[-ventana:], y=sma200.iloc[-ventana:],
                            mode='lines', name='SMA200', line=dict(color='#f23645', width=1, dash='dash')), row=1, col=1)
    
    # Volumen
    colors = ['#00ffad' if df['Close'].iloc[i] > df['Open'].iloc[i] else '#f23645' 
              for i in range(len(df)-ventana, len(df))]
    
    fig.add_trace(go.Bar(
        x=df.index[-ventana:],
        y=df['Volume'].iloc[-ventana:],
        marker_color=colors,
        name='Volumen'
    ), row=2, col=1)
    
    fig.update_layout(
        title='Análisis Técnico con Zonas de Acumulación (Score > 70)',
        yaxis_title='Precio ($)',
        yaxis2_title='Volumen',
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        paper_bgcolor='#11141a',
        plot_bgcolor='#11141a',
        font=dict(color='white'),
        showlegend=True,
        height=600
    )
    
    return fig

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
    .penalty-box { background: rgba(242, 54, 69, 0.05); border-left: 4px solid #f23645; padding: 10px; margin: 5px 0; border-radius: 0 4px 4px 0; font-size: 12px; }
    .detail-item { padding: 8px 0; border-bottom: 1px solid #1a1e26; color: #ccc; font-size: 13px; }
    .detail-item:last-child { border-bottom: none; }
    .badge { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; }
    .metric-card { background: #0c0e12; border-radius: 8px; padding: 15px; text-align: center; border: 1px solid #1a1e26; }
    .metric-value { font-size: 1.5rem; font-weight: bold; color: white; }
    .metric-label { font-size: 0.8rem; color: #888; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("<h1 style='color:white;margin-bottom:5px;'>🚦 RSU ALGORITMO PRO v2.0</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#888;font-size:14px;margin-top:0;'>Detección de Fondos Multi-Factor con Análisis Sectorial y Divergencias</p>", unsafe_allow_html=True)
    
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
                
                # Descargar datos sectoriales para McClellan mejorado
                sector_data = descargar_datos_sectores()
                
                if df_daily.empty:
                    st.error("No se pudieron obtener datos de SPY")
                    st.stop()
                
                resultado = detectar_fondo_comprehensivo(df_daily, df_vix, sector_data)
                
            except Exception as e:
                st.error(f"Error al obtener datos: {e}")
                st.stop()
        
        # Layout principal
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            # Semáforo con Score
            luz_r = "on" if resultado['estado'] in ["ROJO"] else ""
            luz_a = "on" if resultado['estado'] in ["AMBAR", "AMBAR-BAJO", "SETUP SIN VOLUMEN"] else ""
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
            
            # Métricas de medias móviles
            mm = resultado['medias_moviles']
            col_mm1, col_mm2, col_mm3 = st.columns(3)
            with col_mm1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:{'#00ffad' if mm['price'] > mm['ema_21'] else '#f23645'};">{mm['ema_21']:.2f}</div>
                    <div class="metric-label">EMA 21</div>
                </div>
                """, unsafe_allow_html=True)
            with col_mm2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:{'#00ffad' if mm['price'] > mm['sma_50'] else '#f23645'};">{mm['sma_50']:.2f}</div>
                    <div class="metric-label">SMA 50</div>
                </div>
                """, unsafe_allow_html=True)
            with col_mm3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:{'#00ffad' if mm['price'] > mm['sma_200'] else '#f23645'};">{mm['sma_200']:.2f}</div>
                    <div class="metric-label">SMA 200</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Recomendación estratégica
            st.markdown(f"""
            <div class="recommendation-box">
                <div style="color:#00ffad;font-weight:bold;margin-bottom:8px;font-size:14px;">📋 RECOMENDACIÓN ESTRATÉGICA</div>
                <div style="color:#ccc;font-size:13px;line-height:1.5;">{resultado['recomendacion']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Penalizaciones si existen
            if resultado['penalizaciones']:
                st.markdown("<div style='margin-top:15px;'><strong style='color:#f23645;'>⚠️ Penalizaciones aplicadas:</strong></div>", unsafe_allow_html=True)
                for pen in resultado['penalizaciones']:
                    st.markdown(f'<div class="penalty-box">{pen}</div>', unsafe_allow_html=True)
        
        with col_right:
            # Panel de Factores
            st.markdown("""
            <div class="rsu-box">
                <div class="rsu-head">
                    <span class="rsu-title">Desglose de Factores v2.0</span>
                </div>
                <div class="rsu-body">
            """, unsafe_allow_html=True)
            
            # Renderizar cada factor
            factores_orden = ['FTD', 'RSI', 'VIX', 'Breadth', 'Volume', 'Divergencia', 'SMA200']
            for factor_key in factores_orden:
                if factor_key in resultado['metricas']:
                    m = resultado['metricas'][factor_key]
                    
                    # Nombres personalizados
                    nombres_display = {
                        'FTD': 'Follow-Through Day',
                        'RSI': 'RSI Diario',
                        'VIX': 'VIX / Volatilidad',
                        'Breadth': 'Breadth (McClellan)',
                        'Volume': 'Volumen Capitulación',
                        'Divergencia': 'Divergencia Alcista',
                        'SMA200': 'Filtro SMA200'
                    }
                    
                    nombre_display = nombres_display.get(factor_key, factor_key)
                    pct = (m['score'] / m['max']) * 100 if m['max'] > 0 else 0
                    raw_val = m.get('raw_value', 0)
                    
                    # Formatear valor raw
                    if factor_key == 'RSI':
                        raw_text = f"RSI: {raw_val:.1f}"
                    elif factor_key == 'VIX':
                        raw_text = f"{raw_val:.1f}" if not m.get('is_proxy') else f"ATR: {raw_val:.1f}x"
                    elif factor_key == 'Breadth':
                        raw_text = f"{raw_val:.0f} ({m.get('metodo', 'Proxy')})"
                    elif factor_key == 'Volume':
                        raw_text = f"{raw_val:.1f}x media"
                    elif factor_key == 'Divergencia':
                        raw_text = "Detectada" if m['score'] > 0 else "No detectada"
                    elif factor_key == 'SMA200':
                        raw_text = f"Distancia: {raw_val:.2f}$" if not m.get('is_penalty') else "Bajo SMA200"
                        if m.get('is_penalty'):
                            pct = 100  # Mostrar barra completa en rojo para penalización
                    else:
                        raw_text = ""
                    
                    # Color especial para penalizaciones
                    bar_color = m['color'] if not m.get('is_penalty') else '#f23645'
                    
                    st.markdown(f"""
                    <div class="factor-container">
                        <div class="factor-header">
                            <span class="factor-name">{nombre_display} (max {m['max']} pts)</span>
                            <span class="factor-score" style="color:{bar_color};">{m['score']}/{m['max']}</span>
                        </div>
                        <div class="progress-bg">
                            <div class="progress-fill" style="width:{pct}%; background:{bar_color};"></div>
                        </div>
                        {f'<div style="color:#666; font-size:11px; margin-top:4px;">{raw_text}</div>' if raw_text else ''}
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Gráfico de Zonas de Acumulación
        st.markdown("### 📊 Zonas de Acumulación (Score > 70)")
        try:
            fig = crear_grafico_acumulacion(df_daily, resultado)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error al generar gráfico: {e}")
        
        # Detalles técnicos expandibles
        with st.expander("🔍 Ver detalles técnicos completos", expanded=False):
            col_det1, col_det2 = st.columns(2)
            
            with col_det1:
                st.markdown("### Análisis de Factores:")
                for detalle in resultado['detalles']:
                    if detalle.startswith('✓'):
                        color = '#00ffad'
                    elif detalle.startswith('~'):
                        color = '#ff9800'
                    elif detalle.startswith('✗'):
                        color = '#f23645'
                    else:
                        color = '#888'
                    
                    st.markdown(f'<div class="detail-item" style="color:{color};">{detalle}</div>', unsafe_allow_html=True)
            
            with col_det2:
                if resultado['divergencia_data']:
                    st.markdown("### Detalle de Divergencia:")
                    div = resultado['divergencia_data']
                    st.write(f"**Tipo**: {div['tipo']}")
                    st.write(f"**Precio previo**: {div['precio_prev']:.2f}")
                    st.write(f"**Precio actual**: {div['precio_last']:.2f}")
                    st.write(f"**RSI previo**: {div['rsi_prev']:.2f}")
                    st.write(f"**RSI actual**: {div['rsi_last']:.2f}")
                
                if resultado['ftd_data'] and resultado['ftd_data'].get('signal') == 'confirmed':
                    st.markdown("### Estado FTD:")
                    ftd = resultado['ftd_data']
                    st.write(f"**Estado**: {ftd.get('estado')}")
                    st.write(f"**Días de rally**: {ftd.get('dias_rally')}")
                    st.write(f"**Retorno FTD**: {ftd.get('retorno', 'N/A')}%")
                    if ftd.get('date'):
                        st.write(f"**Fecha FTD**: {ftd['date'].strftime('%Y-%m-%d')}")
    
    with tab2:
        st.markdown("### 📊 Backtesting Histórico v2.0")
        st.info("Análisis de performance con umbral configurable. Compara resultados entre diferentes niveles de exigencia (50 vs 70 vs 80).")
        
        col_bt1, col_bt2, col_bt3 = st.columns([1, 1, 2])
        with col_bt1:
            umbral_bt = st.slider("Umbral de señal", min_value=30, max_value=85, value=50, step=5, 
                                  help="Score mínimo para considerar entrada. Umbral alto = menos señales pero mayor calidad.")
            años_bt = st.selectbox("Período", options=[1, 2, 3, 5], index=1)
        
        with col_bt2:
            modo_preciso = st.checkbox("Modo Preciso (Sectores)", value=False, 
                                   help="Descarga datos sectoriales para cada punto (muy lento pero preciso)")
            comparar_umbrales = st.checkbox("Comparar umbrales 50/70/80", value=False,
                                          help="Ejecuta backtest con 3 umbrales diferentes para comparar")
        
        with col_bt3:
            if st.button("🚀 Ejecutar Backtest", type="primary", use_container_width=True):
                if comparar_umbrales:
                    # Comparar múltiples umbrales
                    umbrales = [50, 70, 80]
                    resultados_comparativa = []
                    
                    progress_bar = st.progress(0)
                    for idx, umb in enumerate(umbrales):
                        with st.spinner(f'Analizando umbral {umb}... ({idx+1}/3)'):
                            res, err = backtest_strategy(years=años_bt, umbral_señal=umb, usar_sectores=False)
                            if res:
                                resultados_comparativa.append({
                                    'Umbral': umb,
                                    'Señales': res['total_señales'],
                                    'Win Rate 20d': f"{res['win_rate_20d']:.1f}%",
                                    'Retorno Medio 20d': f"{res['retorno_medio_20d']:.2f}%",
                                    'Retorno Total': f"{res['retorno_total_20d']:.2f}%"
                                })
                        progress_bar.progress((idx + 1) / 3)
                    
                    if resultados_comparativa:
                        st.success("Comparativa completada")
                        df_comp = pd.DataFrame(resultados_comparativa)
                        st.dataframe(df_comp, use_container_width=True, hide_index=True)
                        
                        # Gráfico comparativo
                        st.bar_chart(df_comp.set_index('Umbral')[['Win Rate 20d', 'Retorno Medio 20d']])
                else:
                    # Backtest simple
                    with st.spinner(f'Analizando {años_bt} años con umbral {umbral_bt}...'):
                        resultados_bt, error = backtest_strategy(years=años_bt, umbral_señal=umbral_bt, usar_sectores=modo_preciso)
                        
                        if error:
                            st.warning(error)
                        elif resultados_bt:
                            st.success(f"Backtest completado: {resultados_bt['total_señales']} señales (Umbral: {resultados_bt['umbral_aplicado']})")
                            
                            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                            m_col1.metric("Total Señales", resultados_bt['total_señales'])
                            m_col2.metric("Score Promedio", f"{resultados_bt['score_promedio']:.1f}")
                            m_col3.metric("Win Rate (20d)", f"{resultados_bt['win_rate_20d']:.1f}%")
                            m_col4.metric("Retorno Medio (20d)", f"{resultados_bt['retorno_medio_20d']:.2f}%")
                            
                            # Gráfico de distribución
                            st.markdown("#### Distribución de Retornos")
                            chart_data = resultados_bt['detalle'][['retorno_5d', 'retorno_10d', 'retorno_20d']].rename(columns={
                                'retorno_5d': '5 días',
                                'retorno_10d': '10 días',
                                'retorno_20d': '20 días'
                            })
                            st.bar_chart(chart_data.mean())
                            
                            # Tabla detallada
                            with st.expander("Ver tabla detallada"):
                                st.dataframe(
                                    resultados_bt['detalle'].sort_values('fecha', ascending=False),
                                    use_container_width=True,
                                    hide_index=True
                                )
    
    with tab3:
        st.markdown("""
        ### 🔬 Metodología Científica v2.0
        
        **ADVERTENCIA**: Esta herramienta es un asistente de análisis técnico, no un sistema de trading automático garantizado.
        
        #### Nuevo Sistema de Puntuación Rebalanceado (0-100 puntos)
        
        | Factor | Peso v1 | Peso v2 | Razón del Cambio |
        |--------|---------|---------|------------------|
        | **FTD** | 30 | 35 | Más predictivo, pero con filtros de calidad |
        | **RSI** | 25 | 15 | Reducido para evitar redundancia con VIX |
        | **VIX** | 20 | 20 | Se mantiene como validador de pánico |
        | **Breadth** | 15 | 20 | Ahora con datos sectoriales reales (XLK, XLF, etc.) |
        | **Volumen** | 10 | 10 | Filtro de seguridad obligatorio |
        | **Divergencia** | 0 | 15 | **NUEVO**: Bono por divergencia alcista RSI |
        
        #### Nuevos Filtros de Calidad (Penalizaciones)
        
        1. **FTD bajo EMA21 (-10 pts)**: Trampa para toros clásica de O'Neil
        2. **FTD sin seguimiento (-5 pts)**: Si no supera máximo del FTD en 3 días
        3. **Precio bajo SMA200 (-10 pts)**: Evitar "catching a falling knife" en mercado bajista
        4. **VIX < 20 con score alto (-10 pts)**: Complacencia en mercado alcista maduro
        
        #### Umbrales de Decisión Mejorados
        
        - **Score 70+ + Volumen alto**: 🟢 VERDE - Fondo probable
        - **Score 70+ + Volumen bajo**: 🟡 AMBAR - Setup sin confirmación
        - **Score 50-69**: 🟡 AMBAR - Desarrollando
        - **Score < 50**: 🔴 ROJO - Sin fondo
        
        #### Mejoras en el McClellan Proxy
        
        **Antes**: Solo usaba retornos del SPY (proxy débil)
        **Ahora**: Descarga XLK, XLF, XLV, XLY, XLP, XLI, XLB, XLRE, XLU
        - Calcula % de sectores en alza vs baja
        - Más sensible a fondos "anchos" vs "estrechos"
        
        #### Detección de Divergencia
        
        Algoritmo busca:
        - Precio hace **Lower Low** (mínimo más bajo)
        - RSI hace **Higher Low** (mínimo más alto)
        - Señal de agotamiento de venta antes del FTD
        
        #### Gestión de Riesgo
        
        1. **Posición inicial**: 25% máximo en señal VERDE
        2. **Stop-loss**: -7% obligatorio
        3. **Time-stop**: Reevaluar si no hay movimiento en 10 días
        4. **Escalado**: Añadir 25% solo si funciona (pyramiding)
        
        #### Referencias
        
        - O'Neil, W. (2009). *How to Make Money in Stocks*
        - McClellan, S. & M. (1998). *Patterns for Profit*
        - Bulkowski, T. (2010). *Encyclopedia of Candlestick Charts*
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
