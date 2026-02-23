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
    Detecta Follow-Through Day según la teoría de William O'Neil (CANSLIM).
    
    Reglas:
    1. Debe haber un nuevo mínimo previo (downtrend)
    2. Día 1: Intento de rally (cierre > cierre anterior)
    3. Días 2-3: El precio no debe hacer nuevo mínimo (mantenerse sobre el low del Día 1)
    4. Día 4-7: FTD confirmado con:
       - Subida >= 1.5% (ideal 2%+)
       - Volumen > volumen del día anterior
       - Vela verde fuerte cerrando sobre velas rojas previas
    
    Retorna: dict con estado del FTD o None
    """
    if df_daily is None or len(df_daily) < 20:
        return None
    
    # Calcular cambios porcentuales y volumen
    df = df_daily.copy()
    df['returns'] = df['Close'].pct_change()
    df['volume_prev'] = df['Volume'].shift(1)
    df['volume_increase'] = df['Volume'] > df['volume_prev']
    df['price_up'] = df['returns'] > 0
    
    # Buscar últimos 60 días para encontrar contexto
    recent = df.tail(60).copy()
    
    # Encontrar mínimos locales recientes (últimos 20 días)
    recent_low = recent['Close'].min()
    recent_low_idx = recent['Close'].idxmin()
    
    # Verificar si estamos en contexto de posible reversión (cerca de mínimos)
    current_price = df['Close'].iloc[-1]
    distancia_minimo = (current_price - recent_low) / recent_low
    
    # Si estamos lejos del mínimo reciente (>10%), no estamos en contexto de FTD
    if distancia_minimo > 0.10:
        return {
            'estado': 'NO_CONTEXT',
            'mensaje': 'Mercado lejos de mínimos recientes',
            'dias_rally': 0,
            'signal': None
        }
    
    # Buscar intento de rally (últimos 10 días desde el mínimo)
    min_idx_pos = recent.index.get_loc(recent_low_idx)
    if min_idx_pos >= len(recent) - 2:
        return {
            'estado': 'RALLY_TOO_RECENT',
            'mensaje': 'Mínimo muy reciente, esperando desarrollo',
            'dias_rally': 0,
            'signal': None
        }
    
    # Analizar días desde el mínimo
    post_low = recent.iloc[min_idx_pos:].copy()
    
    # Día 1 del rally: primer cierre positivo después del mínimo
    rally_start = None
    rally_start_idx = None
    
    for i in range(1, len(post_low)):
        if post_low['price_up'].iloc[i]:
            rally_start = post_low.iloc[i]
            rally_start_idx = i
            break
    
    if rally_start is None:
        return {
            'estado': 'NO_RALLY',
            'mensaje': 'Sin intento de rally detectado',
            'dias_rally': 0,
            'signal': None
        }
    
    # Contar días desde inicio del rally
    dias_rally = len(post_low) - rally_start_idx
    
    # Verificar que no se haya roto el low del día 1
    low_dia_1 = post_low.iloc[rally_start_idx]['Low']
    rally_valido = True
    
    for i in range(rally_start_idx + 1, len(post_low)):
        if post_low.iloc[i]['Low'] < low_dia_1:
            rally_valido = False
            break
    
    if not rally_valido:
        return {
            'estado': 'RALLY_FAILED',
            'mensaje': 'Rally invalidado (nuevo mínimo)',
            'dias_rally': dias_rally,
            'signal': 'invalidated'
        }
    
    # Verificar condiciones de FTD (Día 4-7)
    if dias_rally >= 4 and dias_rally <= 10:
        ultimo_dia = post_low.iloc[-1]
        ret_ultimo = ultimo_dia['returns'] * 100
        
        # Condiciones FTD: +1.5% y volumen creciente
        if ret_ultimo >= 1.5 and ultimo_dia['volume_increase']:
            return {
                'estado': 'FTD_CONFIRMED',
                'mensaje': 'FOLLOW-THROUGH DAY CONFIRMADO',
                'dias_rally': dias_rally,
                'retorno': ret_ultimo,
                'volumen_up': True,
                'signal': 'confirmed',
                'color': '#00ffad',
                'icono': '🚀'
            }
        elif ret_ultimo >= 1.0:
            return {
                'estado': 'FTD_POTENTIAL',
                'mensaje': 'Posible FTD en desarrollo (+{}%)'.format(round(ret_ultimo, 1)),
                'dias_rally': dias_rally,
                'retorno': ret_ultimo,
                'signal': 'potential',
                'color': '#ff9800',
                'icono': '⏳'
            }
    
    # Días 1-3: Rally temprano
    if dias_rally < 4:
        return {
            'estado': 'RALLY_EARLY',
            'mensaje': 'Rally día {} - Esperando día 4-7'.format(dias_rally),
            'dias_rally': dias_rally,
            'signal': 'early',
            'color': '#2962ff',
            'icono': '⏱️'
        }
    
    # Después del día 10 sin FTD
    if dias_rally > 10:
        return {
            'estado': 'FTD_LATE',
            'mensaje': 'Ventana FTD cerrada (>10 días)',
            'dias_rally': dias_rally,
            'signal': 'expired',
            'color': '#f23645',
            'icono': '❌'
        }
    
    return {
        'estado': 'RALLY_ACTIVE',
        'mensaje': 'Rally activo (día {})'.format(dias_rally),
        'dias_rally': dias_rally,
        'signal': 'active',
        'color': '#888888',
        'icono': '➡️'
    }

def obtener_datos_spy():
    """
    Obtiene datos de SPY. Intenta usar backend primero, fallback a yfinance.
    """
    # === NUEVO: Intentar backend primero ===
    try:
        from modules.api_client import get_api_client
        client = get_api_client()
        
        # Obtener históricos de 6 meses (aprox 26 semanas)
        data_json = client.get_history("SPY", "6mo")
        
        if data_json and "data" in data_json:
            df = pd.DataFrame(data_json["data"])
            
            # Convertir fecha a índice
            date_col = 'Date' if 'Date' in df.columns else 'Datetime' if 'Datetime' in df.columns else None
            if date_col:
                df[date_col] = pd.to_datetime(df[date_col])
                df.set_index(date_col, inplace=True)
            
            # Resamplear a semanal (igual que yfinance interval="1wk")
            df_weekly = df.resample('W').last().dropna()
            
            if len(df_weekly) < 14:
                raise ValueError("Datos insuficientes del backend")
            
            # Para FTD necesitamos datos diarios
            df_daily = df.resample('D').last().dropna() if len(df) > 50 else None
            
            df_weekly['rsi'] = calcular_rsi(df_weekly['Close'])
            rsi_val = float(df_weekly['rsi'].iloc[-1])
            precio_val = float(df_weekly['Close'].iloc[-1])
            rsi_prev = float(df_weekly['rsi'].iloc[-2]) if len(df_weekly) > 1 else rsi_val
            rsi_trend = rsi_val - rsi_prev
            
            return rsi_val, precio_val, rsi_trend, df_daily
            
    except Exception as e:
        pass
    
    # === ORIGINAL: Fallback a yfinance ===
    try:
        ticker = yf.Ticker("SPY")
        df_weekly = ticker.history(interval="1wk", period="6mo")
        df_daily = ticker.history(interval="1d", period="3mo")
        
        if df_weekly.empty or len(df_weekly) < 14:
            return None, None, None, None
        
        df_weekly['rsi'] = calcular_rsi(df_weekly['Close'])
        rsi_val = float(df_weekly['rsi'].iloc[-1])
        precio_val = float(df_weekly['Close'].iloc[-1])
        rsi_prev = float(df_weekly['rsi'].iloc[-2]) if len(df_weekly) > 1 else rsi_val
        rsi_trend = rsi_val - rsi_prev
        
        return rsi_val, precio_val, rsi_trend, df_daily
        
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None, None, None

def calcular_estado(rsi):
    if rsi < 30:
        return "VERDE", "COMPRA", "#00ffad", "RSI < 30: Zona de sobreventa"
    elif rsi > 70:
        return "ROJO", "VENTA", "#f23645", "RSI > 70: Zona de sobrecompra"
    else:
        return "AMBAR", "NEUTRAL", "#ff9800", "RSI 30-70: Zona neutral"

def render():
    set_style()
    
    # CSS expandido para FTD
    css = """
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
    .rsu-tip-text { visibility: hidden; width: 280px; background-color: #1e222d; color: #eee; text-align: left; padding: 12px; border-radius: 8px; position: absolute; z-index: 9999; top: 35px; right: 0; opacity: 0; transition: opacity 0.3s; font-size: 12px; border: 1px solid #444; box-shadow: 0 4px 20px rgba(0,0,0,0.8); line-height: 1.4; }
    .rsu-tip:hover .rsu-tip-text { visibility: visible; opacity: 1; }
    
    /* Nuevos estilos FTD */
    .ftd-panel { background: linear-gradient(135deg, #0c0e12 0%, #11141a 100%); border: 2px solid #1a1e26; border-radius: 12px; padding: 20px; margin-top: 20px; }
    .ftd-header { display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }
    .ftd-icon { font-size: 32px; }
    .ftd-title { color: white; font-size: 18px; font-weight: bold; margin: 0; }
    .ftd-subtitle { color: #888; font-size: 12px; }
    .ftd-status { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; margin-top: 10px; }
    .ftd-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }
    .ftd-item { background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 12px; text-align: center; }
    .ftd-label { color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 5px; }
    .ftd-value { color: white; font-size: 1.2rem; font-weight: bold; }
    .ftd-progress { width: 100%; height: 6px; background: #1a1e26; border-radius: 3px; margin-top: 15px; overflow: hidden; }
    .ftd-progress-bar { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
    .ftd-days { display: flex; justify-content: space-between; margin-top: 8px; font-size: 10px; color: #555; }
    .ftd-alert { background: rgba(0, 255, 173, 0.1); border-left: 3px solid #00ffad; padding: 12px; margin-top: 15px; border-radius: 0 8px 8px 0; }
    .ftd-alert-text { color: #00ffad; font-size: 13px; font-weight: 500; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    st.markdown('<div style="max-width:1200px;margin:0 auto;padding:20px;">', unsafe_allow_html=True)
    
    # Header
    c1, c2 = st.columns([6, 1])
    with c1:
        st.markdown("<h1 style='color:white;margin-bottom:5px;'>🚦 RSU ALGORITMO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#888;font-size:14px;margin-top:0;'>RSI Semanal + Follow-Through Day (CANSLIM)</p>", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="position:relative;height:50px;">
            <div class="rsu-tip" style="position:absolute;top:10px;right:0;">
                <div class="rsu-tip-icon">?</div>
                <div class="rsu-tip-text">
                    <strong>RSU Algoritmo + FTD</strong><br><br>
                    🟢 RSI < 30: Compra<br>
                    🟡 RSI 30-70: Neutral<br>
                    🔴 RSI > 70: Venta<br><br>
                    <strong>Follow-Through Day:</strong><br>
                    Confirmación de cambio de tendencia bajista a alcista según William O'Neil. Requiere rally de 4-7 días con +1.5% y volumen creciente.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Datos
    with st.spinner('Calculando RSI y FTD...'):
        rsi_val, precio_val, rsi_trend, df_daily = obtener_datos_spy()
        ftd_data = detectar_follow_through_day(df_daily) if df_daily is not None else None
    
    if rsi_val is None:
        st.error("Error al obtener datos")
        if st.button("🔄 Recargar"):
            st.rerun()
        return
    
    estado, senal, color, desc = calcular_estado(rsi_val)
    trend_color = "#00ffad" if rsi_trend >= 0 else "#f23645"
    trend_arrow = "↑" if rsi_trend >= 0 else "↓"
    hora = pd.Timestamp.now().strftime('%H:%M')
    
    # Layout de 3 columnas: Semáforo RSI, Métricas, y Panel FTD
    col1, col2 = st.columns([1, 1])
    
    # Columna 1: Semáforo RSI (original)
    with col1:
        luz_r = "on" if estado == "ROJO" else ""
        luz_a = "on" if estado == "AMBAR" else ""
        luz_v = "on" if estado == "VERDE" else ""
        
        html_semaforo = """
        <div class="rsu-box">
            <div class="rsu-head">
                <span class="rsu-title">Señal RSI Semanal</span>
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
        """.format(
            color=color,
            luz_r=luz_r,
            luz_a=luz_a,
            luz_v=luz_v,
            senal=senal,
            desc=desc
        )
        st.markdown(html_semaforo, unsafe_allow_html=True)
        
        # Métricas bajo el semáforo
        m1, m2 = st.columns(2)
        with m1:
            st.markdown("""
            <div class="rsu-metric">
                <div class="rsu-small">RSI</div>
                <div class="rsu-big" style="color:{color};">{rsi:.2f}</div>
                <div style="color:{trend_color};font-size:0.9rem;">{arrow} {trend:.2f}</div>
            </div>
            """.format(
                color=color,
                rsi=rsi_val,
                trend_color=trend_color,
                arrow=trend_arrow,
                trend=abs(rsi_trend)
            ), unsafe_allow_html=True)
        
        with m2:
            st.markdown("""
            <div class="rsu-metric">
                <div class="rsu-small">SPY</div>
                <div class="rsu-big">${price:.2f}</div>
                <div style="color:#888;font-size:0.8rem;">{hora}</div>
            </div>
            """.format(
                price=precio_val,
                hora=hora
            ), unsafe_allow_html=True)
    
    # Columna 2: Panel Follow-Through Day
    with col2:
        if ftd_data:
            ftd_color = ftd_data.get('color', '#888888')
            ftd_icon = ftd_data.get('icono', '●')
            ftd_signal = ftd_data.get('signal')
            
            # Determinar clase CSS especial para FTD confirmado
            glow_style = "box-shadow: 0 0 20px {}44;".format(ftd_color) if ftd_signal == 'confirmed' else ""
            
            ftd_html = """
            <div class="ftd-panel" style="border-color: {ftd_color}44; {glow_style}">
                <div class="ftd-header">
                    <div class="ftd-icon">{icon}</div>
                    <div>
                        <div class="ftd-title">Follow-Through Day</div>
                        <div class="ftd-subtitle">CANSLIM - William O'Neil</div>
                    </div>
                </div>
                
                <div class="ftd-status" style="background: {ftd_color}22; color: {ftd_color}; border: 1px solid {ftd_color}44;">
                    {mensaje}
                </div>
            """.format(
                ftd_color=ftd_color,
                glow_style=glow_style,
                icon=ftd_icon,
                mensaje=ftd_data['mensaje']
            )
            
            # Agregar métricas específicas si hay rally en progreso
            if ftd_data['dias_rally'] > 0:
                progress_width = min((ftd_data['dias_rally'] / 7) * 100, 100)
                ftd_html += """
                <div class="ftd-progress">
                    <div class="ftd-progress-bar" style="width: {width}%; background: {color};"></div>
                </div>
                <div class="ftd-days">
                    <span>Día 1 (Rally)</span>
                    <span style="color: {color}; font-weight: bold;">Día {dias}</span>
                    <span>Ventana FTD (4-7)</span>
                </div>
                """.format(
                    width=progress_width,
                    color=ftd_color,
                    dias=ftd_data['dias_rally']
                )
            
            # Agregar detalles de retorno si existe
            if 'retorno' in ftd_data:
                ftd_html += """
                <div class="ftd-grid" style="margin-top: 15px;">
                    <div class="ftd-item">
                        <div class="ftd-label">Retorno Día</div>
                        <div class="ftd-value" style="color: {color};">{ret}%</div>
                    </div>
                    <div class="ftd-item">
                        <div class="ftd-label">Volumen</div>
                        <div class="ftd-value" style="color: {vol_color};">{vol}</div>
                    </div>
                    <div class="ftd-item">
                        <div class="ftd-label">Estado</div>
                        <div class="ftd-value" style="font-size: 0.9rem;">{estado}</div>
                    </div>
                </div>
                """.format(
                    color=ftd_color,
                    ret=round(ftd_data['retorno'], 2),
                    vol_color="#00ffad" if ftd_data.get('volumen_up') else "#ff9800",
                    vol="↑ Sí" if ftd_data.get('volumen_up') else "→ No",
                    estado=ftd_data['estado'].replace('_', ' ')
                )
            
            # Alerta especial para FTD confirmado
            if ftd_signal == 'confirmed':
                ftd_html += """
                <div class="ftd-alert">
                    <div class="ftd-alert-text">
                        ⚠️ Señal de cambio de tendencia confirmada. Considerar entrada gradual en posiciones largas según reglas CANSLIM.
                    </div>
                </div>
                """
            
            ftd_html += "</div>"
            st.markdown(ftd_html, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="ftd-panel">
                <div class="ftd-header">
                    <div class="ftd-icon">📊</div>
                    <div>
                        <div class="ftd-title">Follow-Through Day</div>
                        <div class="ftd-subtitle">Sin datos suficientes</div>
                    </div>
                </div>
                <div style="color: #888; text-align: center; padding: 20px;">
                    No hay datos diarios disponibles para calcular FTD
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Barra de progreso RSI (debajo de todo)
    bar_html = """
    <div class="rsu-bar-box" style="margin-top: 20px;">
        <div style="color:#888;font-size:11px;margin-bottom:8px;text-transform:uppercase;">Posición RSI Semanal</div>
        <div class="rsu-bar-line">
            <div class="rsu-bar-fill" style="width:{width}%;background:linear-gradient(90deg,#00ffad,#ff9800,#f23645);"></div>
        </div>
        <div class="rsu-flex">
            <span>0</span>
            <span style="color:#00ffad;font-weight:bold;">30</span>
            <span style="color:#ff9800;font-weight:bold;">70</span>
            <span>100</span>
        </div>
        <div style="text-align:center;margin-top:8px;color:{color};font-weight:bold;font-size:13px;">
            {rsi:.1f} → {estado}
        </div>
    </div>
    """.format(
        width=rsi_val,
        color=color,
        rsi=rsi_val,
        estado=estado
    )
    st.markdown(bar_html, unsafe_allow_html=True)
    
    # Zonas (mantenidas abajo)
    st.markdown("<h3 style='color:white;margin-top:30px;'>📊 Zonas RSI</h3>", unsafe_allow_html=True)
    z1, z2, z3 = st.columns(3)
    
    zonas = [
        ("#f23645", "red", "VENTA", "> 70", "🔴", "Sobrecompra"),
        ("#ff9800", "yel", "NEUTRAL", "30-70", "🟡", "Esperar"),
        ("#00ffad", "grn", "COMPRA", "< 30", "🟢", "Sobreventa")
    ]
    
    cols = [z1, z2, z3]
    for i, (col, (col_hex, col_name, title, range_txt, emoji, sub)) in enumerate(zip(cols, zonas)):
        with col:
            zona_html = """
            <div class="rsu-box" style="border-color:{col_hex}44;">
                <div style="text-align:center;padding:20px;">
                    <div style="width:50px;height:50px;background:{col_hex}22;border:2px solid {col_hex};border-radius:50%;margin:0 auto 15px;display:flex;align-items:center;justify-content:center;font-size:20px;color:{col_hex};">{emoji}</div>
                    <h4 style="color:{col_hex};margin:0 0 10px 0;">{title}</h4>
                    <div style="color:white;font-size:1.5rem;font-weight:bold;">{range_txt}</div>
                    <p style="color:#888;font-size:12px;margin:10px 0 0 0;">{sub}</p>
                </div>
            </div>
            """.format(
                col_hex=col_hex,
                emoji=emoji,
                title=title,
                range_txt=range_txt,
                sub=sub
            )
            st.markdown(zona_html, unsafe_allow_html=True)
    
    # Leyenda FTD
    st.markdown("""
    <div style="margin-top: 30px; padding: 20px; background: #0c0e12; border-radius: 10px; border: 1px solid #1a1e26;">
        <h4 style="color: white; margin-top: 0;">📚 Sobre el Follow-Through Day</h4>
        <p style="color: #888; font-size: 13px; line-height: 1.6;">
            El <strong style="color: #00ffad;">Follow-Through Day</strong> es una señal desarrollada por William O'Neil (CANSLIM) 
            para identificar el cambio de una tendencia bajista a alcista. Ocurre entre el día 4 y 7 de un intento de rally 
            después de un mínimo significativo, con una subida del 1.5-2% o más y volumen creciente. 
            <br><br>
            <strong>Reglas clave:</strong><br>
            • Día 1: Intento de rally (cierre positivo después de mínimo)<br>
            • Días 2-3: No romper el low del día 1<br>
            • Días 4-7: FTD confirmado con +1.5% y volumen ↑<br>
            • Si ocurre después del día 10, pierde fiabilidad
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Recalcular", use_container_width=True):
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
