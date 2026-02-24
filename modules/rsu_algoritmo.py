# modules/rsu_algoritmo.py
import streamlit as st
import pandas as pd
import yfinance as yf
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
    rsi = 100 - (100 / (1 + rs))
    return rsi

def detectar_follow_through_day(df_daily):
    """
    Detecta Follow-Through Day y calcula RSI diario contextual.
    Retorna dict con estado FTD + RSI del momento del rally.
    """
    if df_daily is None or len(df_daily) < 20:
        return None
    
    df = df_daily.copy()
    df['returns'] = df['Close'].pct_change()
    df['volume_prev'] = df['Volume'].shift(1)
    df['volume_increase'] = df['Volume'] > df['volume_prev']
    df['price_up'] = df['returns'] > 0
    
    # Calcular RSI diario (14 periodos)
    df['rsi_daily'] = calcular_rsi(df['Close'], period=14)
    
    recent = df.tail(60).copy()
    recent_low = recent['Close'].min()
    recent_low_idx = recent['Close'].idxmin()
    current_price = df['Close'].iloc[-1]
    distancia_minimo = (current_price - recent_low) / recent_low
    
    # Contexto: ¿Estamos cerca de mínimos recientes? (condición para FTD válido)
    if distancia_minimo > 0.10:
        rsi_actual = float(df['rsi_daily'].iloc[-1])
        return {
            'estado': 'NO_CONTEXT',
            'mensaje': 'Mercado lejos de mínimos recientes',
            'dias_rally': 0,
            'signal': None,
            'color': '#888888',
            'icono': '⚪',
            'rsi_contexto': rsi_actual,
            'tipo_mercado': 'Tendencia establecida',
            'recomendacion': 'Usar RSI clásico (30/70)'
        }
    
    min_idx_pos = recent.index.get_loc(recent_low_idx)
    if min_idx_pos >= len(recent) - 2:
        rsi_en_minimo = float(df.loc[recent_low_idx, 'rsi_daily']) if recent_low_idx in df.index else 30
        return {
            'estado': 'RALLY_TOO_RECENT',
            'mensaje': 'Mínimo muy reciente, esperando desarrollo',
            'dias_rally': 0,
            'signal': None,
            'color': '#2962ff',
            'icono': '⏱️',
            'rsi_contexto': rsi_en_minimo,
            'tipo_mercado': 'Posible reversión',
            'recomendacion': 'Monitorear día 4-7 para FTD'
        }
    
    post_low = recent.iloc[min_idx_pos:].copy()
    rally_start = None
    rally_start_idx = None
    
    for i in range(1, len(post_low)):
        if post_low['price_up'].iloc[i]:
            rally_start = post_low.iloc[i]
            rally_start_idx = i
            break
    
    if rally_start is None:
        rsi_actual = float(df['rsi_daily'].iloc[-1])
        return {
            'estado': 'NO_RALLY',
            'mensaje': 'Sin intento de rally detectado',
            'dias_rally': 0,
            'signal': None,
            'color': '#555555',
            'icono': '⚫',
            'rsi_contexto': rsi_actual,
            'tipo_mercado': 'Bajista',
            'recomendacion': 'Esperar día 1 de rally'
        }
    
    dias_rally = len(post_low) - rally_start_idx
    low_dia_1 = post_low.iloc[rally_start_idx]['Low']
    rally_valido = True
    
    for i in range(rally_start_idx + 1, len(post_low)):
        if post_low.iloc[i]['Low'] < low_dia_1:
            rally_valido = False
            break
    
    # RSI en el día actual del rally
    rsi_actual = float(df['rsi_daily'].iloc[-1])
    rsi_tendencia = "Subiendo" if dias_rally > 1 and rsi_actual > float(post_low.iloc[-2]['rsi_daily']) else "Estable/Bajando"
    
    if not rally_valido:
        return {
            'estado': 'RALLY_FAILED',
            'mensaje': 'Rally invalidado (nuevo mínimo)',
            'dias_rally': dias_rally,
            'signal': 'invalidated',
            'color': '#f23645',
            'icono': '❌',
            'rsi_contexto': rsi_actual,
            'tipo_mercado': 'Bajista continuo',
            'recomendacion': 'Evitar longs, buscar shorts'
        }
    
    # Verificar condiciones de FTD (Día 4-7)
    if dias_rally >= 4 and dias_rally <= 10:
        ultimo_dia = post_low.iloc[-1]
        ret_ultimo = ultimo_dia['returns'] * 100
        
        # INTEGRACIÓN CLAVE: RSI debe confirmar (no estar sobrecomprado >70)
        rsi_confirmado = rsi_actual < 70  # Evitar comprar sobrecompra extrema
        
        if ret_ultimo >= 1.5 and ultimo_dia['volume_increase'] and rsi_confirmado:
            return {
                'estado': 'FTD_CONFIRMED',
                'mensaje': 'FOLLOW-THROUGH DAY CONFIRMADO',
                'dias_rally': dias_rally,
                'retorno': ret_ultimo,
                'volumen_up': True,
                'signal': 'confirmed',
                'color': '#00ffad',
                'icono': '🚀',
                'rsi_contexto': rsi_actual,
                'rsi_tendencia': rsi_tendencia,
                'tipo_mercado': 'Reversión Alcista Confirmada',
                'recomendacion': 'ENTRADA AGRESIVA: RSI {} confirma no sobrecompra'.format(int(rsi_actual))
            }
        elif ret_ultimo >= 1.5 and ultimo_dia['volume_increase'] and not rsi_confirmado:
            # FTD técnico pero RSI en sobrecompra - señal de precaución
            return {
                'estado': 'FTD_OVERBOUGHT',
                'mensaje': 'FTD Confirmado pero RSI > 70',
                'dias_rally': dias_rally,
                'retorno': ret_ultimo,
                'volumen_up': True,
                'signal': 'caution',
                'color': '#ff9800',
                'icono': '⚠️',
                'rsi_contexto': rsi_actual,
                'rsi_tendencia': rsi_tendencia,
                'tipo_mercado': 'Reversión con Precaución',
                'recomendacion': 'ESPERAR: RSI {} en sobrecompra, riesgo de pullback'.format(int(rsi_actual))
            }
        elif ret_ultimo >= 1.0:
            return {
                'estado': 'FTD_POTENTIAL',
                'mensaje': f'Posible FTD en desarrollo (+{round(ret_ultimo, 1)}%)',
                'dias_rally': dias_rally,
                'retorno': ret_ultimo,
                'signal': 'potential',
                'color': '#ff9800',
                'icono': '⏳',
                'rsi_contexto': rsi_actual,
                'rsi_tendencia': rsi_tendencia,
                'tipo_mercado': 'Rally en progreso',
                'recomendacion': 'Monitorear para confirmación'
            }
    
    if dias_rally < 4:
        return {
            'estado': 'RALLY_EARLY',
            'mensaje': f'Rally día {dias_rally} - Esperando día 4-7',
            'dias_rally': dias_rally,
            'signal': 'early',
            'color': '#2962ff',
            'icono': '⏱️',
            'rsi_contexto': rsi_actual,
            'rsi_tendencia': rsi_tendencia,
            'tipo_mercado': 'Rally temprano',
            'recomendacion': 'Paciencia, ventana FTD no abierta'
        }
    
    if dias_rally > 10:
        return {
            'estado': 'FTD_LATE',
            'mensaje': 'Ventana FTD cerrada (>10 días)',
            'dias_rally': dias_rally,
            'signal': 'expired',
            'color': '#f23645',
            'icono': '❌',
            'rsi_contexto': rsi_actual,
            'tipo_mercado': 'Rally maduro',
            'recomendacion': 'No perseguir, esperar consolidación'
        }
    
    return {
        'estado': 'RALLY_ACTIVE',
        'mensaje': f'Rally activo (día {dias_rally})',
        'dias_rally': dias_rally,
        'signal': 'active',
        'color': '#888888',
        'icono': '➡️',
        'rsi_contexto': rsi_actual,
        'tipo_mercado': 'Tendencia alcista',
        'recomendacion': 'Gestionar posiciones existentes'
    }

def obtener_datos_spy():
    try:
        from modules.api_client import get_api_client
        client = get_api_client()
        data_json = client.get_history("SPY", "6mo")
        
        if data_json and "data" in data_json:
            df = pd.DataFrame(data_json["data"])
            date_col = 'Date' if 'Date' in df.columns else 'Datetime' if 'Datetime' in df.columns else None
            if date_col:
                df[date_col] = pd.to_datetime(df[date_col])
                df.set_index(date_col, inplace=True)
            
            # Datos diarios para FTD + RSI diario
            df_daily = df.resample('D').last().dropna()
            
            if len(df_daily) < 20:
                raise ValueError("Datos insuficientes del backend")
            
            return df_daily
            
    except Exception as e:
        pass
    
    try:
        ticker = yf.Ticker("SPY")
        df_daily = ticker.history(interval="1d", period="3mo")
        
        if df_daily.empty or len(df_daily) < 20:
            return None
        
        return df_daily
        
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def render_ftd_panel(ftd_data):
    """
    Renderiza el panel integrado FTD + RSI usando st.html()
    """
    if not ftd_data:
        st.html("""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #11141a 100%); border: 2px solid #1a1e26; border-radius: 12px; padding: 20px; margin-top: 20px; font-family: sans-serif;">
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                <div style="font-size: 32px;">📊</div>
                <div>
                    <div style="color: white; font-size: 18px; font-weight: bold; margin: 0;">RSU Algoritmo Integrado</div>
                    <div style="color: #888; font-size: 12px;">FTD + RSI Diario</div>
                </div>
            </div>
            <div style="color: #888; text-align: center; padding: 20px;">
                No hay datos disponibles
            </div>
        </div>
        """)
        return
    
    # Extraer datos
    ftd_color = ftd_data.get('color', '#888888')
    ftd_icon = ftd_data.get('icono', '●')
    mensaje = ftd_data.get('mensaje', '')
    dias_rally = ftd_data.get('dias_rally', 0)
    rsi_val = ftd_data.get('rsi_contexto', 0)
    tipo_mercado = ftd_data.get('tipo_mercado', 'Desconocido')
    recomendacion = ftd_data.get('recomendacion', '')
    signal = ftd_data.get('signal')
    
    # Determinar color del RSI para visualización
    if rsi_val < 30:
        rsi_color = '#00ffad'
        rsi_estado = 'SOBREVENTA'
    elif rsi_val > 70:
        rsi_color = '#f23645'
        rsi_estado = 'SOBRECOMPRA'
    else:
        rsi_color = '#ff9800'
        rsi_estado = 'NEUTRAL'
    
    # Glow si es confirmado
    glow_style = f"box-shadow: 0 0 20px {ftd_color}44;" if signal == 'confirmed' else ""
    
    html_parts = []
    html_parts.append(f'<div style="background: linear-gradient(135deg, #0c0e12 0%, #11141a 100%); border: 2px solid {ftd_color}44; border-radius: 12px; padding: 20px; margin-top: 20px; {glow_style} font-family: sans-serif;">')
    
    # Header con icono y título
    html_parts.append(f'''
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="font-size: 32px;">{ftd_icon}</div>
                <div>
                    <div style="color: white; font-size: 18px; font-weight: bold; margin: 0;">{tipo_mercado}</div>
                    <div style="color: #888; font-size: 12px;">FTD + RSI Diario (14)</div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="color: {rsi_color}; font-size: 24px; font-weight: bold;">{rsi_val:.1f}</div>
                <div style="color: #555; font-size: 10px;">RSI</div>
            </div>
        </div>
    ''')
    
    # Status badge principal
    html_parts.append(f'''
        <div style="background: {ftd_color}22; color: {ftd_color}; border: 1px solid {ftd_color}44; padding: 12px 16px; border-radius: 8px; font-weight: bold; font-size: 1rem; margin-bottom: 15px; text-align: center;">
            {mensaje}
        </div>
    ''')
    
    # Grid de métricas
    html_parts.append('<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 15px;">')
    
    # Día del rally
    if dias_rally > 0:
        html_parts.append(f'''
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 5px;">Día del Rally</div>
                <div style="color: {ftd_color}; font-size: 1.5rem; font-weight: bold;">{dias_rally}/7</div>
            </div>
        ''')
    
    # RSI Estado
    html_parts.append(f'''
        <div style="background: #0c0e12; border: 1px solid {rsi_color}44; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 5px;">RSI Estado</div>
            <div style="color: {rsi_color}; font-size: 1.2rem; font-weight: bold;">{rsi_estado}</div>
        </div>
    ''')
    
    # Retorno si existe
    if 'retorno' in ftd_data:
        ret = round(ftd_data['retorno'], 2)
        html_parts.append(f'''
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 5px;">Retorno Día</div>
                <div style="color: {"#00ffad" if ret > 0 else "#f23645"}; font-size: 1.2rem; font-weight: bold;">{ret}%</div>
            </div>
        ''')
    
    # Volumen
    if 'volumen_up' in ftd_data:
        vol_color = '#00ffad' if ftd_data['volumen_up'] else '#ff9800'
        vol_text = '↑ Confirmado' if ftd_data['volumen_up'] else '→ Bajo'
        html_parts.append(f'''
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 5px;">Volumen</div>
                <div style="color: {vol_color}; font-size: 1.0rem; font-weight: bold;">{vol_text}</div>
            </div>
        ''')
    
    html_parts.append('</div>')  # Cierre grid
    
    # Barra de progreso del rally
    if dias_rally > 0:
        progress = min((dias_rally / 7) * 100, 100)
        html_parts.append(f'''
            <div style="margin-bottom: 15px;">
                <div style="width: 100%; height: 8px; background: #1a1e26; border-radius: 4px; overflow: hidden;">
                    <div style="height: 100%; border-radius: 4px; width: {progress}%; background: linear-gradient(90deg, {ftd_color}, {ftd_color}88);"></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 10px; color: #555;">
                    <span>Día 1</span>
                    <span style="color: {ftd_color};">Ventana FTD (4-7)</span>
                    <span>Día 10</span>
                </div>
            </div>
        ''')
    
    # Recomendación final
    html_parts.append(f'''
        <div style="background: rgba(0, 255, 173, 0.05); border-left: 3px solid {ftd_color}; padding: 12px; border-radius: 0 8px 8px 0;">
            <div style="color: #ccc; font-size: 12px; font-weight: 500; line-height: 1.4;">
                <strong style="color: {ftd_color};">Estrategia:</strong> {recomendacion}
            </div>
        </div>
    ''')
    
    # Alerta especial para FTD confirmado
    if signal == 'confirmed':
        html_parts.append('''
            <div style="background: rgba(0, 255, 173, 0.1); border: 1px solid #00ffad44; padding: 12px; margin-top: 12px; border-radius: 8px; text-align: center;">
                <div style="color: #00ffad; font-size: 13px; font-weight: bold;">
                    🎯 SETUP COMPLETO: FTD Confirmado + RSI Favorable
                </div>
                <div style="color: #888; font-size: 11px; margin-top: 4px;">
                    Condiciones óptimas para considerar posiciones largas según CANSLIM
                </div>
            </div>
        ''')
    elif signal == 'caution':
        html_parts.append('''
            <div style="background: rgba(255, 152, 0, 0.1); border: 1px solid #ff980044; padding: 12px; margin-top: 12px; border-radius: 8px; text-align: center;">
                <div style="color: #ff9800; font-size: 13px; font-weight: bold;">
                    ⚠️ SETUP PARCIAL: FTD Confirmado pero RSI Elevado
                </div>
                <div style="color: #888; font-size: 11px; margin-top: 4px;">
                    Considerar entrada parcial o esperar pullback a RSI < 60
                </div>
            </div>
        ''')
    
    html_parts.append('</div>')
    
    st.html(''.join(html_parts))

def render():
    set_style()
    
    # CSS global
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
    .rsu-metric { background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 20px; text-align: center; }
    .rsu-big { font-size: 2.2rem; font-weight: bold; color: white; margin: 10px 0; }
    .rsu-small { color: #888; font-size: 0.85rem; text-transform: uppercase; }
    .rsu-badge { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 8px; font-weight: bold; font-size: 1.1rem; margin-top: 10px; }
    .rsu-dot { width: 10px; height: 10px; border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,255,255,0.4); } 70% { opacity: 0.8; box-shadow: 0 0 0 10px rgba(255,255,255,0); } 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,255,255,0); } }
    .rsu-bar-box { background: #0c0e12; border-radius: 10px; padding: 15px; margin-top: 15px; border: 1px solid #1a1e26; }
    .rsu-bar-line { height: 10px; background: #1a1e26; border-radius: 5px; overflow: hidden; }
    .rsu-bar-fill { height: 100%; border-radius: 5px; }
    .rsu-flex { display: flex; justify-content: space-between; font-size: 11px; color: #555; margin-top: 5px; }
    .rsu-tip { position: relative; display: inline-block; }
    .rsu-tip-icon { width: 26px; height: 26px; border-radius: 50%; background: #1a1e26; border: 2px solid #555; display: flex; align-items: center; justify-content: center; color: #aaa; font-size: 14px; font-weight: bold; cursor: help; }
    .rsu-tip-icon:hover { border-color: #2962ff; color: #2962ff; }
    .rsu-tip-text { visibility: hidden; width: 300px; background-color: #1e222d; color: #eee; text-align: left; padding: 12px; border-radius: 8px; position: absolute; z-index: 9999; top: 35px; right: 0; opacity: 0; transition: opacity 0.3s; font-size: 12px; border: 1px solid #444; box-shadow: 0 4px 20px rgba(0,0,0,0.8); line-height: 1.4; }
    .rsu-tip:hover .rsu-tip-text { visibility: visible; opacity: 1; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="max-width:1200px;margin:0 auto;padding:20px;">', unsafe_allow_html=True)
    
    # Header
    c1, c2 = st.columns([6, 1])
    with c1:
        st.markdown("<h1 style='color:white;margin-bottom:5px;'>🚦 RSU ALGORITMO V2</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#888;font-size:14px;margin-top:0;'>Integración FTD + RSI Diario (CANSLIM)</p>", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="position:relative;height:50px;">
            <div class="rsu-tip" style="position:absolute;top:10px;right:0;">
                <div class="rsu-tip-icon">?</div>
                <div class="rsu-tip-text">
                    <strong>RSU Algoritmo V2</strong><br><br>
                    <strong>FTD (Follow-Through Day):</strong><br>
                    Señal de cambio de tendencia en días 4-7 después de un mínimo, con +1.5% y volumen creciente.<br><br>
                    <strong>RSI Diario (14):</strong><br>
                    Filtra el timing de entrada. FTD + RSI < 70 = Setup óptimo.<br><br>
                    <strong>Regla:</strong> RSI diario sincroniza mejor con la velocidad del FTD que RSI semanal.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Datos
    with st.spinner('Analizando FTD + RSI Diario...'):
        df_daily = obtener_datos_spy()
        if df_daily is not None:
            ftd_data = detectar_follow_through_day(df_daily)
            # Calcular RSI actual para el semáforo visual
            df_daily['rsi'] = calcular_rsi(df_daily['Close'], period=14)
            rsi_val = float(df_daily['rsi'].iloc[-1])
            precio_val = float(df_daily['Close'].iloc[-1])
            rsi_prev = float(df_daily['rsi'].iloc[-2]) if len(df_daily) > 1 else rsi_val
            rsi_trend = rsi_val - rsi_prev
        else:
            ftd_data = None
            rsi_val = None
    
    if rsi_val is None:
        st.error("Error al obtener datos")
        if st.button("🔄 Recargar"):
            st.rerun()
        return
    
    # Determinar estado del semáforo basado en FTD + RSI
    signal_type = ftd_data.get('signal') if ftd_data else None
    
    # Lógica integrada del semáforo
    if signal_type == 'confirmed':
        estado = "VERDE"
        senal = "COMPRA FTD"
        color = "#00ffad"
        desc = "FTD Confirmado + RSI Favorable"
    elif signal_type == 'caution':
        estado = "AMBAR"
        senal = "PRECAUCIÓN"
        color = "#ff9800"
        desc = "FTD Confirmado pero RSI > 70"
    elif signal_type == 'potential':
        estado = "AMBAR"
        senal = "POTENCIAL"
        color = "#ff9800"
        desc = "FTD en desarrollo"
    elif signal_type == 'early':
        estado = "AMBAR"
        senal = "ESPERA"
        color = "#2962ff"
        desc = f"Rally día {ftd_data.get('dias_rally', 0)} - Esperar día 4-7"
    elif signal_type == 'invalidated' or signal_type == 'expired':
        estado = "ROJO"
        senal = "NEUTRAL/BAJISTA"
        color = "#f23645"
        desc = "Sin setup válido"
    else:
        # Fallback a RSI clásico si no hay contexto FTD
        if rsi_val < 30:
            estado = "VERDE"
            senal = "COMPRA"
            color = "#00ffad"
            desc = "RSI < 30: Sobreventa"
        elif rsi_val > 70:
            estado = "ROJO"
            senal = "VENTA"
            color = "#f23645"
            desc = "RSI > 70: Sobrecompra"
        else:
            estado = "AMBAR"
            senal = "NEUTRAL"
            color = "#ff9800"
            desc = "RSI 30-70: Zona neutral"
    
    trend_color = "#00ffad" if rsi_trend >= 0 else "#f23645"
    trend_arrow = "↑" if rsi_trend >= 0 else "↓"
    hora = pd.Timestamp.now().strftime('%H:%M')
    
    # Layout
    col1, col2 = st.columns([1, 1])
    
    # Columna 1: Semáforo Integrado
    with col1:
        luz_r = "on" if estado == "ROJO" else ""
        luz_a = "on" if estado == "AMBAR" else ""
        luz_v = "on" if estado == "VERDE" else ""
        
        semaforo_html = f"""
        <div class="rsu-box">
            <div class="rsu-head">
                <span class="rsu-title">Señal Integrada FTD+RSI</span>
                <span style="color:{color};font-size:12px;font-weight:bold;">● TIEMPO REAL</span>
            </div>
            <div class="rsu-body rsu-center">
                <div class="rsu-luz red {luz_r}"></div>
                <div class="rsu-luz yel {luz_a}"></div>
                <div class="rsu-luz grn {luz_v}"></div>
                <div class="rsu-badge" style="background:{color}22;border:2px solid {color};color:{color};">
                    <span class="rsu-dot" style="background:{color};"></span>
                    {senal}
                </div>
                <p style="color:#888;font-size:13px;margin-top:15px;">{desc}</p>
            </div>
        </div>
        """
        st.markdown(semaforo_html, unsafe_allow_html=True)
        
        # Métricas
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div class="rsu-metric">
                <div class="rsu-small">RSI Diario (14)</div>
                <div class="rsu-big" style="color:{color};">{rsi_val:.2f}</div>
                <div style="color:{trend_color};font-size:0.9rem;">{trend_arrow} {abs(rsi_trend):.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with m2:
            st.markdown(f"""
            <div class="rsu-metric">
                <div class="rsu-small">Precio SPY</div>
                <div class="rsu-big">${precio_val:.2f}</div>
                <div style="color:#888;font-size:0.8rem;">{hora}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Columna 2: Panel FTD Integrado
    with col2:
        render_ftd_panel(ftd_data)
    
    # Barra de progreso RSI
    st.markdown(f"""
    <div class="rsu-bar-box" style="margin-top: 20px;">
        <div style="color:#888;font-size:11px;margin-bottom:8px;text-transform:uppercase;">RSI Diario (14) - Optimizado para Swing Trading</div>
        <div class="rsu-bar-line">
            <div class="rsu-bar-fill" style="width:{rsi_val}%;background:linear-gradient(90deg,#00ffad,#ff9800,#f23645);"></div>
        </div>
        <div class="rsu-flex">
            <span>0</span>
            <span style="color:#00ffad;font-weight:bold;">30</span>
            <span style="color:#ff9800;font-weight:bold;">70</span>
            <span>100</span>
        </div>
        <div style="text-align:center;margin-top:8px;color:{color};font-weight:bold;font-size:13px;">
            {rsi_val:.1f} → {estado}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Explicación de la integración
    st.markdown("""
    <div style="margin-top: 30px; padding: 20px; background: #0c0e12; border-radius: 10px; border: 1px solid #1a1e26;">
        <h4 style="color: white; margin-top: 0;">🔬 Por qué RSI Diario + FTD</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; color: #888; font-size: 13px; line-height: 1.6;">
            <div>
                <strong style="color: #00ffad;">✓ Sincronización Temporal</strong><br>
                FTD opera en días 4-7. RSI semanal es demasiado lento para capturar esta ventana. RSI diario (14) ofrece señales en el mismo timeframe que el FTD.
            </div>
            <div>
                <strong style="color: #00ffad;">✓ Filtrado de Entradas</strong><br>
                Un FTD con RSI > 70 es riesgoso (sobrecompra). La integración evita "comprar alto" incluso cuando el FTD técnico se confirma.
            </div>
            <div>
                <strong style="color: #00ffad;">✓ Backtesting Favorable</strong><br>
                Estudios muestran que RSI 14 en daily produce menor drawdown y mejor timing que weekly para swings de 5-15 días.
            </div>
            <div>
                <strong style="color: #00ffad;">✓ Reglas de Integración</strong><br>
                • FTD Confirmado + RSI < 70 = Entrada óptima<br>
                • FTD Confirmado + RSI > 70 = Precaución/Parcial<br>
                • Sin FTD = Usar RSI clásico (30/70)
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Zonas RSI
    st.markdown("<h3 style='color:white;margin-top:30px;'>📊 Zonas RSI Diario</h3>", unsafe_allow_html=True)
    z1, z2, z3 = st.columns(3)
    
    zonas_data = [
        ("#f23645", "SOBRECOMPRA", "> 70", "🔴", "Considerar toma de beneficios"),
        ("#ff9800", "NEUTRAL", "30-70", "🟡", "Esperar setup FTD"),
        ("#00ffad", "SOBREVENTA", "< 30", "🟢", "Preparar entrada en FTD")
    ]
    
    for col, (col_hex, title, range_txt, emoji, sub) in zip([z1, z2, z3], zonas_data):
        with col:
            st.markdown(f"""
            <div class="rsu-box" style="border-color:{col_hex}44;">
                <div style="text-align:center;padding:20px;">
                    <div style="width:50px;height:50px;background:{col_hex}22;border:2px solid {col_hex};border-radius:50%;margin:0 auto 15px;display:flex;align-items:center;justify-content:center;font-size:20px;color:{col_hex};">{emoji}</div>
                    <h4 style="color:{col_hex};margin:0 0 10px 0;">{title}</h4>
                    <div style="color:white;font-size:1.5rem;font-weight:bold;">{range_txt}</div>
                    <p style="color:#888;font-size:12px;margin:10px 0 0 0;">{sub}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    if st.button("🔄 Recalcular", use_container_width=True):
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


