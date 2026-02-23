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
    """
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
        return {
            'estado': 'NO_CONTEXT',
            'mensaje': 'Mercado lejos de mínimos recientes',
            'dias_rally': 0,
            'signal': None,
            'color': '#888888',
            'icono': '⚪'
        }
    
    min_idx_pos = recent.index.get_loc(recent_low_idx)
    if min_idx_pos >= len(recent) - 2:
        return {
            'estado': 'RALLY_TOO_RECENT',
            'mensaje': 'Mínimo muy reciente, esperando desarrollo',
            'dias_rally': 0,
            'signal': None,
            'color': '#2962ff',
            'icono': '⏱️'
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
        return {
            'estado': 'NO_RALLY',
            'mensaje': 'Sin intento de rally detectado',
            'dias_rally': 0,
            'signal': None,
            'color': '#555555',
            'icono': '⚫'
        }
    
    dias_rally = len(post_low) - rally_start_idx
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
            'signal': 'invalidated',
            'color': '#f23645',
            'icono': '❌'
        }
    
    if dias_rally >= 4 and dias_rally <= 10:
        ultimo_dia = post_low.iloc[-1]
        ret_ultimo = ultimo_dia['returns'] * 100
        
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
                'mensaje': f'Posible FTD en desarrollo (+{round(ret_ultimo, 1)}%)',
                'dias_rally': dias_rally,
                'retorno': ret_ultimo,
                'signal': 'potential',
                'color': '#ff9800',
                'icono': '⏳'
            }
    
    if dias_rally < 4:
        return {
            'estado': 'RALLY_EARLY',
            'mensaje': f'Rally día {dias_rally} - Esperando día 4-7',
            'dias_rally': dias_rally,
            'signal': 'early',
            'color': '#2962ff',
            'icono': '⏱️'
        }
    
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
        'mensaje': f'Rally activo (día {dias_rally})',
        'dias_rally': dias_rally,
        'signal': 'active',
        'color': '#888888',
        'icono': '➡️'
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
            
            df_weekly = df.resample('W').last().dropna()
            df_daily = df.resample('D').last().dropna() if len(df) > 50 else None
            
            if len(df_weekly) < 14:
                raise ValueError("Datos insuficientes del backend")
            
            df_weekly['rsi'] = calcular_rsi(df_weekly['Close'])
            rsi_val = float(df_weekly['rsi'].iloc[-1])
            precio_val = float(df_weekly['Close'].iloc[-1])
            rsi_prev = float(df_weekly['rsi'].iloc[-2]) if len(df_weekly) > 1 else rsi_val
            rsi_trend = rsi_val - rsi_prev
            
            return rsi_val, precio_val, rsi_trend, df_daily
            
    except Exception as e:
        pass
    
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

def render_ftd_panel(ftd_data):
    """
    Renderiza el panel FTD usando st.html() para evitar problemas de escape
    """
    if not ftd_data:
        st.html("""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #11141a 100%); border: 2px solid #1a1e26; border-radius: 12px; padding: 20px; margin-top: 20px; font-family: sans-serif;">
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                <div style="font-size: 32px;">📊</div>
                <div>
                    <div style="color: white; font-size: 18px; font-weight: bold; margin: 0;">Follow-Through Day</div>
                    <div style="color: #888; font-size: 12px;">Sin datos suficientes</div>
                </div>
            </div>
            <div style="color: #888; text-align: center; padding: 20px;">
                No hay datos diarios disponibles para calcular FTD
            </div>
        </div>
        """)
        return
    
    ftd_color = ftd_data.get('color', '#888888')
    ftd_icon = ftd_data.get('icono', '●')
    ftd_signal = ftd_data.get('signal')
    mensaje = ftd_data.get('mensaje', '')
    dias_rally = ftd_data.get('dias_rally', 0)
    
    # Construir HTML base
    glow_style = f"box-shadow: 0 0 20px {ftd_color}44;" if ftd_signal == 'confirmed' else ""
    
    html_parts = []
    html_parts.append(f'<div style="background: linear-gradient(135deg, #0c0e12 0%, #11141a 100%); border: 2px solid {ftd_color}44; border-radius: 12px; padding: 20px; margin-top: 20px; {glow_style} font-family: sans-serif;">')
    
    # Header
    html_parts.append(f'''
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
            <div style="font-size: 32px;">{ftd_icon}</div>
            <div>
                <div style="color: white; font-size: 18px; font-weight: bold; margin: 0;">Follow-Through Day</div>
                <div style="color: #888; font-size: 12px;">CANSLIM - William O'Neil</div>
            </div>
        </div>
    ''')
    
    # Status badge
    html_parts.append(f'''
        <div style="display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; margin-top: 10px; background: {ftd_color}22; color: {ftd_color}; border: 1px solid {ftd_color}44;">
            {mensaje}
        </div>
    ''')
    
    # Progress bar si hay rally
    if dias_rally > 0:
        progress_width = min((dias_rally / 7) * 100, 100)
        html_parts.append(f'''
            <div style="width: 100%; height: 6px; background: #1a1e26; border-radius: 3px; margin-top: 15px; overflow: hidden;">
                <div style="height: 100%; border-radius: 3px; transition: width 0.5s ease; width: {progress_width}%; background: {ftd_color};"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 10px; color: #555;">
                <span>Día 1 (Rally)</span>
                <span style="color: {ftd_color}; font-weight: bold;">Día {dias_rally}</span>
                <span>Ventana FTD (4-7)</span>
            </div>
        ''')
    
    # Grid con métricas si hay retorno
    if 'retorno' in ftd_data:
        vol_color = "#00ffad" if ftd_data.get('volumen_up') else "#ff9800"
        vol_text = "↑ Sí" if ftd_data.get('volumen_up') else "→ No"
        retorno = round(ftd_data['retorno'], 2)
        estado_text = ftd_data['estado'].replace('_', ' ')
        
        html_parts.append(f'''
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;">
                <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 5px;">Retorno Día</div>
                    <div style="color: {ftd_color}; font-size: 1.2rem; font-weight: bold;">{retorno}%</div>
                </div>
                <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 5px;">Volumen</div>
                    <div style="color: {vol_color}; font-size: 1.2rem; font-weight: bold;">{vol_text}</div>
                </div>
                <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 5px;">Estado</div>
                    <div style="color: white; font-size: 1.0rem; font-weight: bold;">{estado_text}</div>
                </div>
            </div>
        ''')
    
    # Alerta especial para FTD confirmado
    if ftd_signal == 'confirmed':
        html_parts.append('''
            <div style="background: rgba(0, 255, 173, 0.1); border-left: 3px solid #00ffad; padding: 12px; margin-top: 15px; border-radius: 0 8px 8px 0;">
                <div style="color: #00ffad; font-size: 13px; font-weight: 500;">
                    ⚠️ Señal de cambio de tendencia confirmada. Considerar entrada gradual en posiciones largas según reglas CANSLIM.
                </div>
            </div>
        ''')
    
    html_parts.append('</div>')
    
    # Unir todo y renderizar
    full_html = ''.join(html_parts)
    st.html(full_html)

def render():
    set_style()
    
    # CSS global - usando st.markdown con cuidado
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
    .rsu-tip-text { visibility: hidden; width: 280px; background-color: #1e222d; color: #eee; text-align: left; padding: 12px; border-radius: 8px; position: absolute; z-index: 9999; top: 35px; right: 0; opacity: 0; transition: opacity 0.3s; font-size: 12px; border: 1px solid #444; box-shadow: 0 4px 20px rgba(0,0,0,0.8); line-height: 1.4; }
    .rsu-tip:hover .rsu-tip-text { visibility: visible; opacity: 1; }
    </style>
    """, unsafe_allow_html=True)
    
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
    
    # Layout de 2 columnas
    col1, col2 = st.columns([1, 1])
    
    # Columna 1: Semáforo RSI
    with col1:
        luz_r = "on" if estado == "ROJO" else ""
        luz_a = "on" if estado == "AMBAR" else ""
        luz_v = "on" if estado == "VERDE" else ""
        
        # Usar f-strings simples sin anidamientos complejos
        semaforo_html = f"""
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
        """
        st.markdown(semaforo_html, unsafe_allow_html=True)
        
        # Métricas bajo el semáforo
        m1, m2 = st.columns(2)
        with m1:
            metric_html = f"""
            <div class="rsu-metric">
                <div class="rsu-small">RSI</div>
                <div class="rsu-big" style="color:{color};">{rsi_val:.2f}</div>
                <div style="color:{trend_color};font-size:0.9rem;">{trend_arrow} {abs(rsi_trend):.2f}</div>
            </div>
            """
            st.markdown(metric_html, unsafe_allow_html=True)
        
        with m2:
            price_html = f"""
            <div class="rsu-metric">
                <div class="rsu-small">SPY</div>
                <div class="rsu-big">${precio_val:.2f}</div>
                <div style="color:#888;font-size:0.8rem;">{hora}</div>
            </div>
            """
            st.markdown(price_html, unsafe_allow_html=True)
    
    # Columna 2: Panel FTD usando la nueva función
    with col2:
        render_ftd_panel(ftd_data)
    
    # Barra de progreso RSI
    bar_html = f"""
    <div class="rsu-bar-box" style="margin-top: 20px;">
        <div style="color:#888;font-size:11px;margin-bottom:8px;text-transform:uppercase;">Posición RSI Semanal</div>
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
    """
    st.markdown(bar_html, unsafe_allow_html=True)
    
    # Zonas
    st.markdown("<h3 style='color:white;margin-top:30px;'>📊 Zonas RSI</h3>", unsafe_allow_html=True)
    z1, z2, z3 = st.columns(3)
    
    zonas_data = [
        ("#f23645", "VENTA", "> 70", "🔴", "Sobrecompra"),
        ("#ff9800", "NEUTRAL", "30-70", "🟡", "Esperar"),
        ("#00ffad", "COMPRA", "< 30", "🟢", "Sobreventa")
    ]
    
    cols = [z1, z2, z3]
    for col, (col_hex, title, range_txt, emoji, sub) in zip(cols, zonas_data):
        with col:
            zona_html = f"""
            <div class="rsu-box" style="border-color:{col_hex}44;">
                <div style="text-align:center;padding:20px;">
                    <div style="width:50px;height:50px;background:{col_hex}22;border:2px solid {col_hex};border-radius:50%;margin:0 auto 15px;display:flex;align-items:center;justify-content:center;font-size:20px;color:{col_hex};">{emoji}</div>
                    <h4 style="color:{col_hex};margin:0 0 10px 0;">{title}</h4>
                    <div style="color:white;font-size:1.5rem;font-weight:bold;">{range_txt}</div>
                    <p style="color:#888;font-size:12px;margin:10px 0 0 0;">{sub}</p>
                </div>
            </div>
            """
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

