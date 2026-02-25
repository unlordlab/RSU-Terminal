
# modules/rsu_algoritmo_pro.py
import streamlit as st
import streamlit.components.v1 as components
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

# Ventana de "memoria" para condiciones recientes
VENTANA_CONDICIONES = 10  # días

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
    # Verificar que hay suficientes datos para SMA200
    min_periods = min(len(df), 200)
    
    if len(df) >= 50:
        sma_50 = df['Close'].rolling(window=50, min_periods=50).mean().iloc[-1]
    else:
        sma_50 = df['Close'].mean()
    
    if len(df) >= 200:
        sma_200 = df['Close'].rolling(window=200, min_periods=200).mean().iloc[-1]
    else:
        # Si no hay 200 días, usar media móvil de todos los datos disponibles
        sma_200 = df['Close'].mean()
    
    if len(df) >= 21:
        ema_21 = df['Close'].ewm(span=21, adjust=False, min_periods=21).mean().iloc[-1]
    else:
        ema_21 = df['Close'].mean()
    
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
    Sistema de detección de fondos multi-factor V2.1 - MÁS PERMISIVO
    - Permite condiciones en ventana de 10 días (no solo hoy)
    - Convierte penalizaciones en advertencias visuales
    """
    score = 0
    max_score = 100
    detalles = []
    metricas = {}
    advertencias = []  # Reemplaza penalizaciones - no restan puntos
    
    # Obtener métricas de medias móviles (para contexto, no penalización)
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
    
    # 2. FTD Detection (35 pts)
    ftd_data = detectar_follow_through_day(df_spy)
    ftd_score = 0
    ftd_idx = None
    
    if ftd_data:
        if ftd_data.get('signal') == 'confirmed':
            ftd_score = 35
            ftd_idx = ftd_data.get('index')
            detalles.append("✓ FTD Confirmado (+35)")
            
            # ADVERTENCIA (no penalización) si FTD bajo EMA21
            if price < mm['ema_21']:
                advertencias.append(f"⚠️ FTD bajo EMA21 - Posible trampa para toros")
            
            # Verificación de seguimiento (Time Stop) - solo advertencia
            if ftd_idx and not verificar_ftd_follow_through(df_spy, ftd_idx, 3):
                advertencias.append(f"⚠️ FTD sin seguimiento en 3 días - Confirmación débil")
                
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
    
    # 3. RSI Diario (15 pts) - AHORA CON VENTANA DE 10 DÍAS
    rsi_series = calcular_rsi(df_spy['Close'], 14)
    
    # Buscar RSI mínimo en los últimos VENTANA_CONDICIONES días
    rsi_ventana = rsi_series.tail(VENTANA_CONDICIONES)
    rsi_minimo = rsi_ventana.min()
    rsi_actual = rsi_series.iloc[-1]
    rsi_fecha_min = rsi_ventana.idxmin()
    
    rsi_score = 0
    if rsi_minimo < 25:
        rsi_score = 15
        detalles.append(f"✓ RSI mínimo {rsi_minimo:.1f} < 25 en últimos {VENTANA_CONDICIONES} días (+15)")
    elif rsi_minimo < 35:
        rsi_score = 12
        detalles.append(f"✓ RSI mínimo {rsi_minimo:.1f} < 35 en últimos {VENTANA_CONDICIONES} días (+12)")
    elif rsi_minimo < 45:
        rsi_score = 5
        detalles.append(f"~ RSI mínimo {rsi_minimo:.1f} < 45 en últimos {VENTANA_CONDICIONES} días (+5)")
    elif rsi_actual > 75:
        rsi_score = -5  # Penalización leve solo por sobrecompra extrema actual
        detalles.append(f"✗ RSI actual {rsi_actual:.1f} > 75 (Sobrecompra) (-5)")
    else:
        detalles.append(f"• RSI en rango neutral (0)")
    
    score += rsi_score
    metricas['RSI'] = {
        'score': max(0, rsi_score), 
        'max': 15, 
        'color': '#00ffad', 
        'raw_value': rsi_actual,
        'minimo_reciente': rsi_minimo,
        'fecha_minimo': rsi_fecha_min.strftime('%Y-%m-%d') if pd.notna(rsi_fecha_min) else 'N/A'
    }
    
    # 4. VIX / Volatilidad (20 pts) - AHORA CON VENTANA DE 10 DÍAS
    vix_score = 0
    vix_valor = None
    vix_maximo = None
    
    if df_vix is not None and len(df_vix) > 20:
        # Buscar VIX máximo en ventana reciente
        vix_ventana = df_vix['Close'].tail(VENTANA_CONDICIONES)
        vix_maximo = vix_ventana.max()
        vix_actual = df_vix['Close'].iloc[-1]
        vix_fecha_max = vix_ventana.idxmax()
        
        if vix_maximo > 35:
            vix_score = 20
            detalles.append(f"✓ VIX máximo {vix_maximo:.1f} > 35 en últimos {VENTANA_CONDICIONES} días (+20)")
        elif vix_maximo > 30:
            vix_score = 15
            detalles.append(f"✓ VIX máximo {vix_maximo:.1f} > 30 en últimos {VENTANA_CONDICIONES} días (+15)")
        elif vix_maximo > 25:
            vix_score = 10
            detalles.append(f"~ VIX máximo {vix_maximo:.1f} > 25 en últimos {VENTANA_CONDICIONES} días (+10)")
        else:
            detalles.append(f"• VIX sin spike significativo (0)")
        
        # Advertencia si score alto pero VIX bajo actual (complacencia)
        if score > 50 and vix_actual < 20:
            advertencias.append(f"⚠️ VIX actual bajo ({vix_actual:.1f}) - Posible complacencia post-pánico")
        
        metricas['VIX'] = {
            'score': vix_score, 
            'max': 20, 
            'color': '#ff9800', 
            'raw_value': vix_actual,
            'maximo_reciente': vix_maximo,
            'fecha_maximo': vix_fecha_max.strftime('%Y-%m-%d') if pd.notna(vix_fecha_max) else 'N/A'
        }
    else:
        # Proxy usando ATR de SPY
        atr = calcular_atr(df_spy).iloc[-1]
        atr_medio = calcular_atr(df_spy).rolling(20).mean().iloc[-1]
        ratio_atr = atr / atr_medio if atr_medio > 0 else 1
        vix_valor = ratio_atr
        
        # Buscar máximo ATR en ventana
        atr_series = calcular_atr(df_spy)
        atr_ventana = atr_series.tail(VENTANA_CONDICIONES)
        atr_max = atr_ventana.max()
        atr_medio_ventana = atr_series.rolling(20).mean().tail(VENTANA_CONDICIONES).mean()
        ratio_max = atr_max / atr_medio_ventana if atr_medio_ventana > 0 else 1
        
        if ratio_max > 2.0:
            vix_score = 15
            detalles.append(f"~ ATR máximo {ratio_max:.1f}x normal en últimos {VENTANA_CONDICIONES} días (+15)")
        elif ratio_max > 1.5:
            vix_score = 10
            detalles.append(f"~ ATR máximo {ratio_max:.1f}x normal en últimos {VENTANA_CONDICIONES} días (+10)")
        else:
            detalles.append(f"• Volatilidad normal (0)")
        
        metricas['VIX'] = {
            'score': vix_score, 
            'max': 20, 
            'color': '#ff9800', 
            'raw_value': ratio_atr, 
            'is_proxy': True,
            'maximo_reciente': ratio_max
        }
    
    score += vix_score
    
    # 5. McClellan Oscillator Proxy Mejorado (20 pts)
    mcclellan, metodo = calcular_mcclellan_proxy_mejorado(df_spy, sector_data)
    breadth_score = 0
    
    # Buscar mínimo McClellan en ventana
    if isinstance(mcclellan, (int, float)):
        mcclellan_valor = mcclellan
    else:
        mcclellan_valor = mcclellan.iloc[-1] if hasattr(mcclellan, 'iloc') else 0
    
    if mcclellan_valor < -80:
        breadth_score = 20
        detalles.append(f"✓ McClellan {mcclellan_valor:.0f} < -80 (Oversold extremo) (+20) [{metodo}]")
    elif mcclellan_valor < -50:
        breadth_score = 15
        detalles.append(f"~ McClellan {mcclellan_valor:.0f} < -50 (Oversold) (+15) [{metodo}]")
    elif mcclellan_valor < -20:
        breadth_score = 5
        detalles.append(f"• McClellan {mcclellan_valor:.0f} < -20 (Débil) (+5) [{metodo}]")
    else:
        detalles.append(f"• McClellan {mcclellan_valor:.0f} neutral (0) [{metodo}]")
    
    score += breadth_score
    metricas['Breadth'] = {'score': breadth_score, 'max': 20, 'color': '#9c27b0', 'raw_value': mcclellan_valor, 'metodo': metodo}
    
    # 6. Volume Analysis (10 pts) - CON VENTANA
    vol_ventana = df_spy['Volume'].tail(VENTANA_CONDICIONES)
    vol_maximo = vol_ventana.max()
    vol_media = df_spy['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio_max = vol_maximo / vol_media if vol_media > 0 else 1
    vol_actual = df_spy['Volume'].iloc[-1]
    vol_ratio_actual = vol_actual / vol_media if vol_media > 0 else 1
    vol_score = 0
    
    if vol_ratio_max > 2.0:
        vol_score = 10
        detalles.append(f"✓ Volumen máximo {vol_ratio_max:.1f}x media (Capitulación) (+10)")
    elif vol_ratio_max > 1.5:
        vol_score = 7
        detalles.append(f"~ Volumen máximo {vol_ratio_max:.1f}x media (Alto) (+7)")
    elif vol_ratio_max > 1.2:
        vol_score = 3
        detalles.append(f"• Volumen máximo {vol_ratio_max:.1f}x media (+3)")
    else:
        detalles.append(f"• Volumen sin spike significativo (0)")
    
    score += vol_score
    metricas['Volume'] = {
        'score': vol_score, 
        'max': 10, 
        'color': '#f23645', 
        'raw_value': vol_ratio_actual,
        'maximo_reciente': vol_ratio_max
    }
    
    # 7. ADVERTENCIAS DE CONTEXTO (no penalizaciones)
    # SMA200 - Advertencia si estamos bajo, pero NO resta puntos
    if price < mm['sma_200']:
        distancia_sma200 = (price - mm['sma_200']) / mm['sma_200'] * 100
        advertencias.append(f"⚠️ Precio {distancia_sma200:.1f}% bajo SMA200 - Fondo en mercado bajista")
        detalles.append(f"• Bajo SMA200 (Contexto: Mercado bajista)")
    else:
        detalles.append(f"• Sobre SMA200 (Contexto: Tendencia alcista)")
    
    metricas['SMA200'] = {
        'score': 0,  # No suma ni resta
        'max': 0, 
        'color': '#ff9800' if price < mm['sma_200'] else '#00ffad', 
        'raw_value': price - mm['sma_200'],
        'distancia_pct': (price - mm['sma_200']) / mm['sma_200'] * 100 if mm['sma_200'] != 0 else 0,
        'advertencia': price < mm['sma_200']
    }
    
    # EMA21 - Advertencia si FTD bajo ella
    if price < mm['ema_21']:
        advertencias.append(f"📉 Precio bajo EMA21 - Resistencia dinámica cercana")
    
    # Determinar estado con sistema permisivo
    volumen_confirmado = vol_score >= 3
    
    if score >= 70:
        if volumen_confirmado:
            estado = "VERDE"
            senal = "FONDO PROBABLE"
            color = "#00ffad"
            recomendacion = f"Setup óptimo detectado. Score: {score}/100. "
            if len(advertencias) > 0:
                recomendacion += f"⚠️ {len(advertencias)} advertencia(s): Revisar condiciones de riesgo antes de entrar."
            else:
                recomendacion += "Múltiples factores alineados con volumen. Considerar entrada gradual (25%) con stop -7%."
        else:
            estado = "VERDE-VOL"
            senal = "SETUP SIN VOLUMEN"
            color = "#00ffad"
            recomendacion = f"Score alto ({score}) pero volumen insuficiente. Esperar confirmación o reducir posición (10-15%)."
    elif score >= 50:
        estado = "AMBAR"
        senal = "DESARROLLANDO"
        color = "#ff9800"
        recomendacion = "Condiciones mejorando. Preparar watchlist, esperar confirmación adicional o entrada parcial (10-15%)."
    elif score >= 30:
        estado = "AMBAR-BAJO"
        senal = "PRE-SETUP"
        color = "#ff9800"
        recomendacion = "Algunos factores presentes pero insuficientes. Mantener liquidez, monitorear evolución."
    else:
        estado = "ROJO"
        senal = "SIN FONDO"
        color = "#f23645"
        recomendacion = "Sin condiciones de fondo detectadas. Preservar capital."
    
    return {
        'score': score,
        'max_score': max_score,
        'estado': estado,
        'senal': senal,
        'color': color,
        'recomendacion': recomendacion,
        'detalles': detalles,
        'advertencias': advertencias,
        'ftd_data': ftd_data,
        'metricas': metricas,
        'medias_moviles': mm,
        'divergencia_data': div_data,
        'ventana_dias': VENTANA_CONDICIONES
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


def calcular_max_drawdown(precios, precio_entrada):
    """
    Calcula el máximo drawdown porcentual desde el punto de entrada.
    
    Args:
        precios: Serie de precios (pandas Series) después de la entrada
        precio_entrada: Precio de entrada en la señal
    
    Returns:
        float: Máximo drawdown porcentual (negativo)
    """
    if len(precios) < 2:
        return 0.0
    
    # Calcular el running maximum desde la entrada
    running_max = precios.expanding().max()
    
    # Calcular drawdown en cada punto: (precio_actual - running_max) / running_max
    drawdowns = (precios - running_max) / running_max * 100
    
    # El máximo drawdown es el valor más negativo
    max_dd = drawdowns.min()
    
    return max_dd if max_dd < 0 else 0.0


def backtest_strategy(ticker_symbol="SPY", years=2, umbral_señal=50, usar_sectores=False):
    """
    Backtesting robusto con umbral configurable.
    INCLUYE: Drawdown máximo, win rate a 5, 20 y 60 días.
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
        
        # Pre-cargar datos sectoriales si se solicita
        sectores_hist = {}
        if usar_sectores:
            st.info("Modo preciso: Descargando datos sectoriales...")
            for etf in SECTOR_ETFS:
                try:
                    t = yf.Ticker(etf)
                    sectores_hist[etf] = t.history(period=f"{years}y", interval="1d")
                except:
                    continue
        
        señales = []
        
        # Ventana de lookback para análisis
        for i in range(60, len(df_hist) - 60):  # Cambiado a -60 para permitir cálculo de 60 días
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
            
            # Usar el umbral configurable
            if resultado['score'] >= umbral_señal:
                precio_entrada = df_hist['Close'].iloc[i]
                
                # Calcular precios de salida para diferentes períodos
                precio_salida_5d = df_hist['Close'].iloc[min(i + 5, len(df_hist) - 1)]
                precio_salida_10d = df_hist['Close'].iloc[min(i + 10, len(df_hist) - 1)]
                precio_salida_20d = df_hist['Close'].iloc[min(i + 20, len(df_hist) - 1)]
                precio_salida_60d = df_hist['Close'].iloc[min(i + 60, len(df_hist) - 1)]  # NUEVO: 60 días
                
                # Calcular retornos
                retorno_5d = ((precio_salida_5d - precio_entrada) / precio_entrada) * 100
                retorno_10d = ((precio_salida_10d - precio_entrada) / precio_entrada) * 100
                retorno_20d = ((precio_salida_20d - precio_entrada) / precio_entrada) * 100
                retorno_60d = ((precio_salida_60d - precio_entrada) / precio_entrada) * 100  # NUEVO
                
                # NUEVO: Calcular máximo drawdown en los 60 días posteriores
                precios_60d = df_hist['Close'].iloc[i:min(i + 61, len(df_hist))]
                max_drawdown = calcular_max_drawdown(precios_60d, precio_entrada)
                
                señales.append({
                    'fecha': df_hist.index[i].strftime('%Y-%m-%d'),
                    'score': resultado['score'],
                    'estado': resultado['estado'],
                    'advertencias': len(resultado['advertencias']),
                    'precio_entrada': round(precio_entrada, 2),
                    'retorno_5d': round(retorno_5d, 2),
                    'retorno_10d': round(retorno_10d, 2),
                    'retorno_20d': round(retorno_20d, 2),
                    'retorno_60d': round(retorno_60d, 2),  # NUEVO
                    'max_drawdown_60d': round(max_drawdown, 2),  # NUEVO: Drawdown máximo
                    'exito_5d': retorno_5d > 0,
                    'exito_10d': retorno_10d > 0,
                    'exito_20d': retorno_20d > 0,
                    'exito_60d': retorno_60d > 0,  # NUEVO
                    'umbral_usado': umbral_señal
                })
        
        if not señales:
            return None, f"No se generaron señales con score >= {umbral_señal} en el período analizado"
        
        df_resultados = pd.DataFrame(señales)
        
        # Métricas de performance actualizadas
        metricas = {
            'total_señales': len(señales),
            'umbral_aplicado': umbral_señal,
            'score_promedio': df_resultados['score'].mean(),
            'win_rate_5d': (df_resultados['exito_5d'].mean() * 100),
            'win_rate_10d': (df_resultados['exito_10d'].mean() * 100),
            'win_rate_20d': (df_resultados['exito_20d'].mean() * 100),
            'win_rate_60d': (df_resultados['exito_60d'].mean() * 100),  # NUEVO
            'retorno_medio_5d': df_resultados['retorno_5d'].mean(),
            'retorno_medio_10d': df_resultados['retorno_10d'].mean(),
            'retorno_medio_20d': df_resultados['retorno_20d'].mean(),
            'retorno_medio_60d': df_resultados['retorno_60d'].mean(),  # NUEVO
            'retorno_total_20d': df_resultados['retorno_20d'].sum(),
            'retorno_total_60d': df_resultados['retorno_60d'].sum(),  # NUEVO
            'max_drawdown_promedio': df_resultados['max_drawdown_60d'].mean(),  # NUEVO
            'peor_drawdown': df_resultados['max_drawdown_60d'].min(),  # NUEVO
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
    try:
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
    except Exception as e:
        st.error(f"Error al crear gráfico: {e}")
        return None

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
    .warning-box { background: rgba(255, 152, 0, 0.1); border-left: 4px solid #ff9800; padding: 10px; margin: 5px 0; border-radius: 0 4px 4px 0; font-size: 12px; color: #ff9800; }
    .warning-box.danger { background: rgba(242, 54, 69, 0.1); border-left-color: #f23645; color: #f23645; }
    .detail-item { padding: 8px 0; border-bottom: 1px solid #1a1e26; color: #ccc; font-size: 13px; }
    .detail-item:last-child { border-bottom: none; }
    .badge { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; }
    .metric-card { background: #0c0e12; border-radius: 8px; padding: 15px; text-align: center; border: 1px solid #1a1e26; }
    .metric-value { font-size: 1.5rem; font-weight: bold; color: white; }
    .metric-label { font-size: 0.8rem; color: #888; margin-top: 5px; }
    .ventana-badge { display: inline-block; background: #1a1e26; color: #00ffad; padding: 4px 8px; border-radius: 4px; font-size: 11px; margin-left: 10px; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("<h1 style='color:white;margin-bottom:5px;'>🚦 RSU ALGORITMO PRO v2.1</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#888;font-size:14px;margin-top:0;'>Detección de Fondos Multi-Factor <span class='ventana-badge'>Ventana: {VENTANA_CONDICIONES} días</span></p>", unsafe_allow_html=True)
    
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
            luz_a = "on" if resultado['estado'] in ["AMBAR", "AMBAR-BAJO"] else ""
            luz_v = "on" if resultado['estado'] in ["VERDE", "VERDE-VOL"] else ""
            
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
                distancia_ema21 = ((mm['price'] - mm['ema_21'])/mm['ema_21']*100) if mm['ema_21'] != 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:{'#00ffad' if mm['price'] > mm['ema_21'] else '#ff9800'};">{mm['ema_21']:.2f}</div>
                    <div class="metric-label">EMA 21 ({distancia_ema21:+.2f}%)</div>
                </div>
                """, unsafe_allow_html=True)
            with col_mm2:
                distancia_sma50 = ((mm['price'] - mm['sma_50'])/mm['sma_50']*100) if mm['sma_50'] != 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:{'#00ffad' if mm['price'] > mm['sma_50'] else '#ff9800'};">{mm['sma_50']:.2f}</div>
                    <div class="metric-label">SMA 50 ({distancia_sma50:+.2f}%)</div>
                </div>
                """, unsafe_allow_html=True)
            with col_mm3:
                distancia_sma200 = mm.get('distancia_pct', 0)
                color_sma200 = '#00ffad' if mm['price'] > mm['sma_200'] else '#f23645'
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:{color_sma200};">{mm['sma_200']:.2f}</div>
                    <div class="metric-label">SMA 200 ({distancia_sma200:+.1f}%)</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Recomendación estratégica
            st.markdown(f"""
            <div class="recommendation-box">
                <div style="color:#00ffad;font-weight:bold;margin-bottom:8px;font-size:14px;">📋 RECOMENDACIÓN ESTRATÉGICA</div>
                <div style="color:#ccc;font-size:13px;line-height:1.5;">{resultado['recomendacion']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Advertencias (no penalizaciones)
            if resultado['advertencias']:
                st.markdown("<div style='margin-top:15px;'><strong style='color:#ff9800;'>⚠️ Advertencias de Contexto:</strong></div>", unsafe_allow_html=True)
                for adv in resultado['advertencias']:
                    es_danger = "bajo SMA200" in adv or "trampa" in adv
                    clase = "danger" if es_danger else ""
                    st.markdown(f'<div class="warning-box {clase}">{adv}</div>', unsafe_allow_html=True)
        
        with col_right:
            # Panel de Factores - CORREGIDO: Usar components.html para renderizar HTML crudo
            factores_orden = ['FTD', 'RSI', 'VIX', 'Breadth', 'Volume', 'Divergencia', 'SMA200']
            
            # Construir HTML de factores
            factores_html = ""
            for factor_key in factores_orden:
                if factor_key in resultado['metricas']:
                    m = resultado['metricas'][factor_key]
                    
                    # Nombres personalizados
                    nombres_display = {
                        'FTD': 'Follow-Through Day',
                        'RSI': 'RSI (Ventana 10d)',
                        'VIX': 'VIX / Volatilidad (Ventana 10d)',
                        'Breadth': 'Breadth (McClellan)',
                        'Volume': 'Volumen (Ventana 10d)',
                        'Divergencia': 'Divergencia Alcista',
                        'SMA200': 'Contexto SMA200'
                    }
                    
                    nombre_display = nombres_display.get(factor_key, factor_key)
                    pct = (m['score'] / m['max']) * 100 if m['max'] > 0 else 0
                    raw_val = m.get('raw_value', 0)
                    
                    # Formatear valor raw con información de ventana
                    if factor_key == 'RSI':
                        min_rec = m.get('minimo_reciente', raw_val)
                        fecha_min = m.get('fecha_minimo', 'N/A')
                        raw_text = f"Actual: {raw_val:.1f} | Mín: {min_rec:.1f} ({fecha_min})"
                    elif factor_key == 'VIX':
                        max_rec = m.get('maximo_reciente', raw_val)
                        fecha_max = m.get('fecha_maximo', 'N/A')
                        raw_text = f"Actual: {raw_val:.1f} | Máx: {max_rec:.1f} ({fecha_max})"
                    elif factor_key == 'Breadth':
                        raw_text = f"{raw_val:.0f} ({m.get('metodo', 'Proxy')})"
                    elif factor_key == 'Volume':
                        max_rec = m.get('maximo_reciente', raw_val)
                        raw_text = f"Actual: {raw_val:.1f}x | Máx: {max_rec:.1f}x"
                    elif factor_key == 'Divergencia':
                        raw_text = "Detectada" if m['score'] > 0 else "No detectada"
                    elif factor_key == 'SMA200':
                        distancia = m.get('distancia_pct', 0)
                        raw_text = f"Distancia: {distancia:+.1f}%"
                    else:
                        raw_text = ""
                    
                    # Color especial para advertencias
                    bar_color = m['color']
                    if factor_key == 'SMA200' and m.get('advertencia'):
                        bar_color = '#ff9800'  # Naranja para advertencia
                    
                    # Añadir factor al HTML (en una sola línea para evitar problemas)
                    raw_text_html = f'<div style="color:#666; font-size:11px; margin-top:4px;">{raw_text}</div>' if raw_text else ''
                    
                    factores_html += f'<div class="factor-container"><div class="factor-header"><span class="factor-name">{nombre_display} (max {m["max"]} pts)</span><span class="factor-score" style="color:{bar_color};">{m["score"]}/{m["max"]}</span></div><div class="progress-bg"><div class="progress-fill" style="width:{pct}%; background:{bar_color};"></div></div>{raw_text_html}</div>'

            # Construir HTML completo del contenedor con CSS incluido
            html_completo = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ margin: 0; padding: 0; background: #11141a; font-family: sans-serif; }}
                .rsu-box {{ background: #11141a; border: 1px solid #1a1e26; border-radius: 10px; overflow: hidden; }}
                .rsu-head {{ background: #0c0e12; padding: 15px 20px; border-bottom: 1px solid #1a1e26; }}
                .rsu-title {{ color: white; font-size: 16px; font-weight: bold; margin: 0; }}
                .rsu-body {{ padding: 20px; }}
                .factor-container {{ background: #0c0e12; border-radius: 8px; padding: 15px; margin: 10px 0; }}
                .factor-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
                .factor-name {{ color: #888; font-size: 11px; text-transform: uppercase; font-weight: bold; }}
                .factor-score {{ color: white; font-size: 14px; font-weight: bold; }}
                .progress-bg {{ width: 100%; height: 8px; background: #1a1e26; border-radius: 4px; overflow: hidden; }}
                .progress-fill {{ height: 100%; border-radius: 4px; transition: width 0.5s ease; }}
            </style>
            </head>
            <body>
            <div class="rsu-box">
                <div class="rsu-head">
                    <span class="rsu-title">Desglose de Factores v2.1</span>
                </div>
                <div class="rsu-body">
                    {factores_html}
                </div>
            </div>
            </body>
            </html>
            """
            
            # Usar components.html para renderizar el HTML correctamente
            components.html(html_completo, height=800, scrolling=False)
        
        # Gráfico de Zonas de Acumulación
        st.markdown("### 📊 Zonas de Acumulación (Score > 70)")
        try:
            fig = crear_grafico_acumulacion(df_daily, resultado)
            if fig:
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
                
                st.markdown("### Contexto de Medias Móviles:")
                dist_ema21 = ((mm['price'] - mm['ema_21'])/mm['ema_21']*100) if mm['ema_21'] != 0 else 0
                dist_sma50 = ((mm['price'] - mm['sma_50'])/mm['sma_50']*100) if mm['sma_50'] != 0 else 0
                dist_sma200 = ((mm['price'] - mm['sma_200'])/mm['sma_200']*100) if mm['sma_200'] != 0 else 0
                
                st.write(f"**Precio vs EMA21**: {dist_ema21:+.2f}%")
                st.write(f"**Precio vs SMA50**: {dist_sma50:+.2f}%")
                st.write(f"**Precio vs SMA200**: {dist_sma200:+.2f}%")
    
    with tab2:
        st.markdown("### 📊 Backtesting Histórico v2.1")
        st.info(f"Análisis con ventana de {VENTANA_CONDICIONES} días. Las condiciones pueden haber ocurrido en cualquier día de la ventana, no solo el día de la señal.")
        
        col_bt1, col_bt2, col_bt3 = st.columns([1, 1, 2])
        with col_bt1:
            umbral_bt = st.slider("Umbral de señal", min_value=30, max_value=85, value=50, step=5, 
                                  help="Score mínimo para considerar entrada.")
            años_bt = st.selectbox("Período", options=[1, 2, 3, 5], index=3)  # Default 5 años
        
        with col_bt2:
            modo_preciso = st.checkbox("Modo Preciso (Sectores)", value=False, 
                                   help="Descarga datos sectoriales (lento)")
            comparar_umbrales = st.checkbox("Comparar umbrales 50/70/80", value=False,
                                          help="Ejecuta 3 backtests para comparar")
        
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
                                    'Win Rate 5d': f"{res['win_rate_5d']:.1f}%",
                                    'Win Rate 20d': f"{res['win_rate_20d']:.1f}%",
                                    'Win Rate 60d': f"{res['win_rate_60d']:.1f}%",
                                    'Max DD Prom': f"{res['max_drawdown_promedio']:.1f}%",
                                    'Retorno Medio 60d': f"{res['retorno_medio_60d']:.2f}%"
                                })
                        progress_bar.progress((idx + 1) / 3)
                    
                    if resultados_comparativa:
                        st.success("Comparativa completada")
                        df_comp = pd.DataFrame(resultados_comparativa)
                        st.dataframe(df_comp, use_container_width=True, hide_index=True)
                        
                        # Gráfico comparativo
                        st.bar_chart(df_comp.set_index('Umbral')[['Win Rate 5d', 'Win Rate 20d', 'Win Rate 60d']])
                else:
                    # Backtest simple
                    with st.spinner(f'Analizando {años_bt} años con umbral {umbral_bt}...'):
                        resultados_bt, error = backtest_strategy(years=años_bt, umbral_señal=umbral_bt, usar_sectores=modo_preciso)
                        
                        if error:
                            st.warning(error)
                        elif resultados_bt:
                            st.success(f"Backtest completado: {resultados_bt['total_señales']} señales (Umbral: {resultados_bt['umbral_aplicado']})")
                            
                            # Métricas principales con nuevos campos
                            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                            m_col1.metric("Win Rate 5d", f"{resultados_bt['win_rate_5d']:.1f}%")
                            m_col2.metric("Win Rate 20d", f"{resultados_bt['win_rate_20d']:.1f}%")
                            m_col3.metric("Win Rate 60d", f"{resultados_bt['win_rate_60d']:.1f}%")
                            m_col4.metric("Max DD Promedio", f"{resultados_bt['max_drawdown_promedio']:.1f}%", 
                                          delta=f"Peor: {resultados_bt['peor_drawdown']:.1f}%", delta_color="inverse")
                            
                            # Segunda fila de métricas
                            m_col5, m_col6, m_col7, m_col8 = st.columns(4)
                            m_col5.metric("Total Señales", resultados_bt['total_señales'])
                            m_col6.metric("Score Promedio", f"{resultados_bt['score_promedio']:.1f}")
                            m_col7.metric("Retorno Medio 60d", f"{resultados_bt['retorno_medio_60d']:.2f}%")
                            m_col8.metric("Retorno Total 60d", f"{resultados_bt['retorno_total_60d']:.2f}%")
                            
                            # Distribución de retornos incluyendo 60d
                            st.markdown("#### Distribución de Retornos")
                            chart_data = resultados_bt['detalle'][['retorno_5d', 'retorno_20d', 'retorno_60d']].rename(columns={
                                'retorno_5d': '5 días',
                                'retorno_20d': '20 días',
                                'retorno_60d': '60 días'
                            })
                            st.bar_chart(chart_data.mean())
                            
                            # Análisis de Drawdown
                            st.markdown("#### Análisis de Drawdown (60 días)")
                            dd_data = resultados_bt['detalle']['max_drawdown_60d']
                            col_dd1, col_dd2, col_dd3 = st.columns(3)
                            col_dd1.metric("Drawdown Promedio", f"{dd_data.mean():.2f}%")
                            col_dd2.metric("Peor Drawdown", f"{dd_data.min():.2f}%")
                            col_dd3.metric("Señales con DD > -10%", f"{(dd_data < -10).sum()}/{len(dd_data)}")
                            
                            # Histograma de drawdowns
                            st.bar_chart(dd_data.value_counts(bins=10).sort_index())
                            
                            # Tabla detallada
                            with st.expander("Ver tabla detallada"):
                                display_df = resultados_bt['detalle'].sort_values('fecha', ascending=False)
                                st.dataframe(
                                    display_df,
                                    use_container_width=True,
                                    hide_index=True
                                )
                            
                            # Análisis por año
                            st.markdown("#### Distribución Temporal")
                            resultados_bt['detalle']['año'] = pd.to_datetime(resultados_bt['detalle']['fecha']).dt.year
                            señales_por_año = resultados_bt['detalle'].groupby('año').size()
                            st.bar_chart(señales_por_año)
    
    with tab3:
        st.markdown(f"""
        ### 🔬 Metodología Científica v2.1 - MÁS PERMISIVA
        
        **CAMBIO CLAVE**: Ventana de {VENTANA_CONDICIONES} días para condiciones
        
        #### Problema de la Versión Anterior
        El algoritmo requería que RSI < 35, VIX > 30, etc. **ocurrieran exactamente el mismo día**.
        Esto es irrealista: el pánico (VIX alto) suele ocurrir 2-5 días antes que el RSI toque fondo.
        
        #### Solución: Condiciones en Ventana
        Ahora el algoritmo busca:
        - **RSI**: Mínimo en últimos {VENTANA_CONDICIONES} días < 35 (no solo hoy)
        - **VIX**: Máximo en últimos {VENTANA_CONDICIONES} días > 30 (captura spike reciente)
        - **Volumen**: Máximo en últimos {VENTANA_CONDICIONES} días > 1.5x media
        
        Esto permite capturar la "confluencia temporal" de factores, no solo la instantánea.
        
        #### Sistema de Advertencias (no Penalizaciones)
        
        **Antes**: Restar -10 pts por estar bajo SMA200
        **Ahora**: Mostrar advertencia naranja/roja pero mantener score
        
        Por qué: Los fondos **naturalmente** ocurren bajo las medias móviles. Penalizar esto es contraproducente.
        
        Las advertencias indican:
        - 🔴 **Riesgo alto**: FTD bajo EMA21, precio lejos de SMA200
        - 🟡 **Precaución**: VIX bajo post-pánico, falta de seguimiento del FTD
        
        #### Nuevo Sistema de Puntuación
        
        | Factor | Peso | Tipo | Lógica |
        |--------|------|------|--------|
        | **FTD** | 35 | Binario | Confirmado o no |
        | **RSI** | 15 | Ventana 10d | Mínimo < 35 en ventana |
        | **VIX** | 20 | Ventana 10d | Máximo > 30 en ventana |
        | **Breadth** | 20 | Actual | McClellan < -50 |
        | **Volumen** | 10 | Ventana 10d | Máximo > 1.5x en ventana |
        | **Divergencia** | 15 | Binario | RSI vs Precio |
        
        #### Métricas de Backtest
        
        **Win Rates**: 5d, 10d, 20d, 60d días después de la señal
        
        **Drawdown Máximo**: Peor caída desde el punto de entrada durante los 60 días siguientes.
        Calculado como: `min((precio_t - running_max) / running_max) * 100`
        
        #### Umbrales de Decisión
        
        - **Score 70+**: 🟢 VERDE - Fondo probable (con o sin volumen)
        - **Score 50-69**: 🟡 AMBAR - Desarrollando
        - **Score < 50**: 🔴 ROJO - Sin fondo
        
        #### Gestión de Riesgo con Advertencias
        
        Cuando hay advertencias activas:
        1. Reducir tamaño de posición (15% en lugar de 25%)
        2. Stop-loss más ajustado (-5% en lugar de -7%)
        3. Esperar confirmación adicional (cierre sobre EMA21)
        
        #### Referencias
        
        - O'Neil, W. (2009). *How to Make Money in Stocks*
        - McClellan, S. & M. (1998). *Patterns for Profit*
        - Bulkowski, T. (2010). *Encyclopedia of Candlestick Charts*
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)



