# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ────────────────────────────────────────────────

def flatten_columns(df):
    """Aplana columnas MultiIndex de yfinance."""
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df

def ensure_1d_series(data):
    """Asegura que los datos sean Serie 1D"""
    if isinstance(data, pd.DataFrame):
        if data.shape[1] == 1:
            return data.iloc[:, 0]
        if 'Close' in data.columns:
            return data['Close']
        return data.iloc[:, 0]
    return data

def hex_to_rgba(hex_color, alpha=1.0):
    """Convierte hex a rgba para Plotly"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

# ────────────────────────────────────────────────
# CÁLCULOS MATEMÁTICOS
# ────────────────────────────────────────────────

def calculate_ema(prices, period):
    prices = ensure_1d_series(prices)
    return prices.ewm(span=period, adjust=False).mean()

def calculate_z_score(price, ema, std_period=20):
    price = ensure_1d_series(price)
    ema = ensure_1d_series(ema)
    std = price.rolling(window=std_period).std()
    return (price - ema) / std

def calculate_rsi(prices, period=14):
    prices = ensure_1d_series(prices)
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_multi_timeframe_trend(symbol):
    trends = {}
    timeframes = {
        '1D': ('1y', '1d'),
        '4H': ('3mo', '1h'),
        '1H': ('1mo', '1h'),
        '15m': ('5d', '15m')
    }
    
    for tf, (period, interval) in timeframes.items():
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
            if data.empty:
                trends[tf] = {'trend': 'NO_DATA', 'strength': 0}
                continue
            
            data = flatten_columns(data)
            
            if 'Close' not in data.columns or len(data) < 50:
                trends[tf] = {'trend': 'INSUFFICIENT_DATA', 'strength': 0}
                continue
            
            close = ensure_1d_series(data['Close'])
            ema_fast = calculate_ema(close, 9 if tf in ['15m', '1H'] else 20)
            ema_slow = calculate_ema(close, 21 if tf in ['15m', '1H'] else 50)
            
            current_price = float(close.iloc[-1])
            ema_fast_val = float(ema_fast.iloc[-1])
            ema_slow_val = float(ema_slow.iloc[-1])
            
            trend = "BULLISH" if ema_fast_val > ema_slow_val else "BEARISH"
            strength = abs(ema_fast_val - ema_slow_val) / current_price * 100
            
            trends[tf] = {
                'trend': trend,
                'strength': float(strength),
                'price': float(current_price),
                'ema_fast': float(ema_fast_val),
                'ema_slow': float(ema_slow_val)
            }
        except Exception as e:
            trends[tf] = {'trend': 'ERROR', 'strength': 0, 'error': str(e)}
    
    return trends

def analyze_volume_profile(data, lookback=20):
    data = flatten_columns(data)
    if 'Volume' not in data.columns:
        return {'current_volume': 0, 'avg_volume': 0, 'volume_ratio': 1, 
                'trend_volume': "NEUTRAL", 'institutional_participation': False}
    
    volume = ensure_1d_series(data['Volume'])
    if len(volume) < lookback:
        return {'current_volume': 0, 'avg_volume': 0, 'volume_ratio': 1, 
                'trend_volume': "NEUTRAL", 'institutional_participation': False}
    
    current_vol = float(volume.iloc[-1])
    avg_vol = float(volume.tail(lookback).mean())
    volume_ratio = current_vol / avg_vol if avg_vol > 0 else 1
    
    recent_vol = float(volume.tail(5).mean())
    previous_vol = float(volume.iloc[-10:-5].mean()) if len(volume) >= 10 else recent_vol
    vol_trend = "INCREASING" if recent_vol > previous_vol * 1.1 else "DECREASING" if recent_vol < previous_vol * 0.9 else "STABLE"
    
    return {
        'current_volume': int(current_vol),
        'avg_volume': int(avg_vol),
        'volume_ratio': float(volume_ratio),
        'trend_volume': vol_trend,
        'institutional_participation': volume_ratio > 2.0
    }

def calculate_rsu_score(z_score, trend_alignment, volume_score, rsi_value):
    z_abs = abs(z_score)
    z_points = 40 if z_abs <= 0.5 else 30 if z_abs <= 1.0 else 15 if z_abs <= 2.0 else 0
    
    tf_count = len([t for t in trend_alignment.values() if t not in ['ERROR', 'NO_DATA', 'INSUFFICIENT_DATA', None]])
    bullish_count = len([t for t in trend_alignment.values() if t == 'BULLISH'])
    
    if tf_count > 0:
        ratio = bullish_count / tf_count
        trend_points = 30 if ratio >= 0.75 else 20 if ratio >= 0.5 else 10 if ratio >= 0.25 else 0
    else:
        trend_points = 0
    
    vol_points = 20 if volume_score > 2.0 else 15 if volume_score > 1.5 else 10 if volume_score > 1.0 else 5
    rsi_points = 10 if 40 <= rsi_value <= 60 else 7 if 30 <= rsi_value < 40 or 60 < rsi_value <= 70 else 4 if 20 <= rsi_value < 30 or 70 < rsi_value <= 80 else 0
    
    total = z_points + trend_points + vol_points + rsi_points
    
    grade = "A+" if total >= 85 else "A" if total >= 75 else "B" if total >= 65 else "C" if total >= 50 else "D" if total >= 35 else "F"
    grade_text = "EXCELENTE" if total >= 85 else "MUY BUENA" if total >= 75 else "BUENA" if total >= 65 else "REGULAR" if total >= 50 else "DÉBIL" if total >= 35 else "PELIGROSO"
    
    if total >= 75 and abs(z_score) <= 1:
        verdict, color = "🟢 OPORTUNIDAD ÓPTIMA", "#00ffad"
    elif total >= 60:
        verdict, color = "🟡 OPORTUNIDAD MODERADA", "#ff9800"
    elif total >= 40:
        verdict, color = "🟠 ESPERAR CONFIRMACIÓN", "#ff6d00"
    else:
        verdict, color = "🔴 ZONA PELIGROSA / EVITAR", "#f23645"
    
    return {
        'total': total, 'z_component': z_points, 'trend_component': trend_points,
        'volume_component': vol_points, 'rsi_component': rsi_points,
        'grade': (grade, grade_text), 'verdict': (verdict, color)
    }

def get_z_color(z):
    return "#00ffad" if abs(z) <= 1 else "#ff9800" if abs(z) <= 2 else "#f23645"

# ────────────────────────────────────────────────
# VISUALIZACIONES
# ────────────────────────────────────────────────

def create_z_score_gauge(z_score):
    # Usar rgba en lugar de hex con transparencia
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=float(z_score),
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Tensión Elástica (Z-Score)", 'font': {'size': 14, 'color': 'white'}},
        number={'font': {'size': 24, 'color': 'white'}, 'suffix': "σ"},
        delta={'reference': 0, 'position': "top"},
        gauge={
            'axis': {'range': [-3, 3], 'tickwidth': 1, 'tickcolor': "#1a1e26"},
            'bar': {'color': get_z_color(z_score), 'thickness': 0.75},
            'bgcolor': "#0c0e12",
            'borderwidth': 2,
            'bordercolor': "#1a1e26",
            'steps': [
                {'range': [-3, -2], 'color': hex_to_rgba("#f23645", 0.13)},  # rgba con alpha
                {'range': [-2, -1], 'color': hex_to_rgba("#ff9800", 0.13)},
                {'range': [-1, 1], 'color': hex_to_rgba("#00ffad", 0.13)},
                {'range': [1, 2], 'color': hex_to_rgba("#ff9800", 0.13)},
                {'range': [2, 3], 'color': hex_to_rgba("#f23645", 0.13)}
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.8, 'value': float(z_score)}
        }
    ))
    fig.update_layout(paper_bgcolor="#11141a", font={'color': "white"}, height=280, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def create_trend_alignment_chart(trends):
    timeframes = list(trends.keys())
    values, colors, labels = [], [], []
    
    for tf in timeframes:
        trend = trends.get(tf, {}).get('trend', 'ERROR')
        if trend == 'BULLISH':
            values.append(1); colors.append("#00ffad"); labels.append("ALCISTA")
        elif trend == 'BEARISH':
            values.append(-1); colors.append("#f23645"); labels.append("BAJISTA")
        else:
            values.append(0); colors.append("#888"); labels.append("N/A")
    
    fig = go.Figure(data=[go.Bar(x=timeframes, y=values, marker_color=colors, text=labels, textposition='outside', textfont=dict(color='white', size=11))])
    fig.update_layout(
        paper_bgcolor="#11141a", plot_bgcolor="#0c0e12", font=dict(color="white"),
        title=dict(text="Alineación de Tendencias", font=dict(color="white", size=14)),
        xaxis=dict(color="white", gridcolor="#1a1e26"),
        yaxis=dict(color="white", gridcolor="#1a1e26", range=[-1.5, 1.5], tickvals=[-1, 0, 1], ticktext=['BAJISTA', 'NEUTRO', 'ALCISTA']),
        height=250, margin=dict(l=40, r=20, t=50, b=40), showlegend=False
    )
    return fig

def create_volume_heatmap(data, vol_analysis):
    data = flatten_columns(data)
    recent_data = data.tail(20).copy()
    
    if 'Volume' not in recent_data.columns:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor="#11141a", plot_bgcolor="#0c0e12", title=dict(text="Sin datos de volumen", font=dict(color="white")))
        return fig
    
    volume = ensure_1d_series(recent_data['Volume'])
    avg_vol = vol_analysis['avg_volume']
    
    colors = []
    for vol in volume:
        ratio = vol / avg_vol if avg_vol > 0 else 1
        colors.append("#00ffad" if ratio > 2 else "#4caf50" if ratio > 1.5 else "#ff9800" if ratio > 1 else "#f23645")
    
    fig = go.Figure(data=[go.Bar(
        x=recent_data.index.strftime('%m-%d'), y=volume, marker_color=colors,
        hovertemplate='Fecha: %{x}<br>Volumen: %{y:,.0f}<br>Ratio: %{text:.2f}x<extra></extra>',
        text=[v/avg_vol for v in volume]
    )])
    fig.add_hline(y=avg_vol, line_dash="dash", line_color="white", annotation_text="Promedio", annotation_position="right")
    fig.update_layout(
        paper_bgcolor="#11141a", plot_bgcolor="#0c0e12", font=dict(color="white"),
        title=dict(text="Volumen Reciente (Gasolina Real)", font=dict(color="white", size=14)),
        xaxis=dict(color="white", gridcolor="#1a1e26", tickangle=-45),
        yaxis=dict(color="white", gridcolor="#1a1e26", title="Volumen"),
        height=250, margin=dict(l=50, r=50, t=50, b=60), showlegend=False
    )
    return fig

def create_rsu_score_radar(score_components):
    categories = ['Z-Score', 'Tendencia', 'Volumen', 'RSI']
    values = [
        score_components['z_component'] / 40 * 100,
        score_components['trend_component'] / 30 * 100,
        score_components['volume_component'] / 20 * 100,
        score_components['rsi_component'] / 10 * 100
    ]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]], theta=categories + [categories[0]],
        fill='toself', fillcolor='rgba(0, 255, 173, 0.3)',
        line=dict(color='#00ffad', width=2), marker=dict(size=8, color='#00ffad')
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], color='white', gridcolor='#1a1e26'),
                   angularaxis=dict(color='white', gridcolor='#1a1e26'), bgcolor='#0c0e12'),
        paper_bgcolor='#11141a', font=dict(color='white'),
        title=dict(text="Desglose del RSU Score", font=dict(color='white', size=14)),
        height=300, margin=dict(l=60, r=60, t=50, b=40)
    )
    return fig

def create_price_chart_with_emas(data, symbol):
    data = flatten_columns(data)
    close = ensure_1d_series(data['Close'])
    ema_9 = calculate_ema(close, 9)
    ema_21 = calculate_ema(close, 21)
    ema_50 = calculate_ema(close, 50)
    z_scores = calculate_z_score(close, ema_21)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, 
                        row_heights=[0.7, 0.3], subplot_titles=(f'{symbol} - Análisis Técnico', 'Z-Score Histórico'))
    
    fig.add_trace(go.Candlestick(
        x=data.index, open=ensure_1d_series(data['Open']), high=ensure_1d_series(data['High']),
        low=ensure_1d_series(data['Low']), close=close, name='Precio',
        increasing_line_color='#00ffad', decreasing_line_color='#f23645'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=data.index, y=ema_9, line=dict(color='#00d9ff', width=1.5), name='EMA 9'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=ema_21, line=dict(color='#ff9800', width=1.5), name='EMA 21'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=ema_50, line=dict(color='#9c27b0', width=1.5), name='EMA 50'), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=data.index, y=z_scores, mode='lines', line=dict(color='white', width=1),
                               name='Z-Score', fill='tozeroy', fillcolor='rgba(100,100,100,0.1)'), row=2, col=1)
    
    for level in [-2, -1, 1, 2]:
        fig.add_hline(y=level, line_dash="dash", line_color="#444", line_width=1, row=2, col=1)
    fig.add_hline(y=0, line_color="#00ffad", line_width=2, row=2, col=1)
    
    fig.update_layout(
        paper_bgcolor='#11141a', plot_bgcolor='#0c0e12', font=dict(color='white'),
        xaxis_rangeslider_visible=False, height=500, margin=dict(l=50, r=50, t=50, b=40),
        legend=dict(bgcolor='rgba(17, 20, 26, 0.8)', bordercolor='#1a1e26', borderwidth=1, font=dict(color='white'))
    )
    fig.update_xaxes(gridcolor='#1a1e26', color='white')
    fig.update_yaxes(gridcolor='#1a1e26', color='white')
    return fig

# ────────────────────────────────────────────────
# SECCIONES EDUCATIVAS Y DE RIESGO
# ────────────────────────────────────────────────

def render_explanation_section():
    """Renderiza la sección de explicación de la metodología"""
    st.markdown("""
    <div style="background:linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border:1px solid #2a3f5f; border-radius:15px; padding:25px; margin:20px 0;">
        <h3 style="color:#00ffad; margin-bottom:20px; font-size:1.3rem;">📚 ¿CÓMO FUNCIONA RSU EMA EDGE?</h3>
        
        <div style="display:grid; gap:20px;">
            <div style="background:#0c0e12; padding:15px; border-radius:10px; border-left:3px solid #00ffad;">
                <h4 style="color:#00ffad; margin:0 0 10px 0; font-size:1rem;">1️⃣ Tensión Elástica (Z-Score) - 40%</h4>
                <p style="color:#aaa; margin:0; font-size:0.9rem; line-height:1.5;">
                    La EMA actúa como una "liga elástica". El Z-Score mide cuántas desviaciones estándar 
                    se ha alejado el precio de esa media. Valores entre -1 y +1σ indican que el precio 
                    está en su "zona de confort estadístico". Valores extremos (>±2σ) sugieren que el 
                    precio está sobreextendido y probabilísticamente tenderá a revertir a la media.
                </p>
            </div>
            
            <div style="background:#0c0e12; padding:15px; border-radius:10px; border-left:3px solid #2196f3;">
                <h4 style="color:#2196f3; margin:0 0 10px 0; font-size:1rem;">2️⃣ Alineación Multi-Timeframe - 30%</h4>
                <p style="color:#aaa; margin:0; font-size:0.9rem; line-height:1.5;">
                    "La tendencia es tu amiga". Analizamos 4 timeframes simultáneamente (15m, 1H, 4H, 1D) 
                    usando cruces de EMA. Cuando 3 o más timeframes están alineados (alcistas o bajistas), 
                    la probabilidad de que el movimiento continúe aumenta significativamente. Evita nadar 
                    contra la corriente.
                </p>
            </div>
            
            <div style="background:#0c0e12; padding:15px; border-radius:10px; border-left:3px solid #ff9800;">
                <h4 style="color:#ff9800; margin:0 0 10px 0; font-size:1rem;">3️⃣ Volumen como Gasolina - 20%</h4>
                <p style="color:#aaa; margin:0; font-size:0.9rem; line-height:1.5;">
                    El volumen es el combustible de los movimientos. Un rebote sin volumen es como un coche 
                    sin gasolina: no llegará lejos. Comparamos el volumen actual vs el promedio de 20 días. 
                    Ratios >2x sugieren participación institucional (dinero "inteligente").
                </p>
            </div>
            
            <div style="background:#0c0e12; padding:15px; border-radius:10px; border-left:3px solid #9c27b0;">
                <h4 style="color:#9c27b0; margin:0 0 10px 0; font-size:1rem;">4️⃣ RSI - Filtro de Momentum - 10%</h4>
                <p style="color:#aaa; margin:0; font-size:0.9rem; line-height:1.5;">
                    El RSI (Índice de Fuerza Relativa) evita que entremos en zonas de sobrecompra (>70) 
                    o sobreventa extrema (<30). Buscamos el "punto dulce" entre 40-60 donde el momentum 
                    tiene espacio para continuar sin estar exhausto.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_risks_section():
    """Renderiza la sección de riesgos y limitaciones"""
    st.markdown("""
    <div style="background:linear-gradient(135deg, #1a0f0f 0%, #261a1a 100%); border:2px solid #f23645; border-radius:15px; padding:25px; margin:20px 0;">
        <h3 style="color:#f23645; margin-bottom:20px; font-size:1.3rem;">⚠️ RIESGOS Y LIMITACIONES CRÍTICAS</h3>
        
        <div style="display:grid; gap:15px;">
            <div style="background:#0c0e12; padding:15px; border-radius:8px; border:1px solid #f2364533;">
                <h4 style="color:#f23645; margin:0 0 8px 0; font-size:0.95rem;">🎲 Naturaleza Probabilística</h4>
                <p style="color:#aaa; margin:0; font-size:0.85rem; line-height:1.4;">
                    <strong>ESTA HERRAMIENTA NO PREDICE EL FUTURO.</strong> Un Z-Score alto no garantiza 
                    reversión, solo indica que estadísticamente es más probable. El mercado puede permanecer 
                    irracional más tiempo del que puedes permanecer solvente. El Z-Score de +3 puede 
                    convertirse en +5 (tendencia parabólica) antes de revertir.
                </p>
            </div>
            
            <div style="background:#0c0e12; padding:15px; border-radius:8px; border:1px solid #f2364533;">
                <h4 style="color:#f23645; margin:0 0 8px 0; font-size:0.95rem;">📰 Eventos de Cola Negra (Black Swans)</h4>
                <p style="color:#aaa; margin:0; font-size:0.85rem; line-height:1.4;">
                    Esta herramienta no detecta eventos impredecibles: guerras, fraudes corporativos, 
                    decisiones de la FED sorpresa, tweets de CEOs, etc. El análisis técnico falla 
                    catastróficamente ante noticias fundamentales de alto impacto.
                </p>
            </div>
            
            <div style="background:#0c0e12; padding:15px; border-radius:8px; border:1px solid #f2364533;">
                <h4 style="color:#f23645; margin:0 0 8px 0; font-size:0.95rem;">⏱️ Lag en Datos</h4>
                <p style="color:#aaa; margin:0; font-size:0.85rem; line-height:1.4;">
                    Los datos de yfinance tienen delay (15 min para intradía). En mercados volátiles, 
                    el "setup perfecto" puede desaparecer antes de que ejecutes. Esta herramienta es 
                    para análisis, no para ejecución en tiempo real.
                </p>
            </div>
            
            <div style="background:#0c0e12; padding:15px; border-radius:8px; border:1px solid #f2364533;">
                <h4 style="color:#f23645; margin:0 0 8px 0; font-size:0.95rem;">🤖 Sobre-optimización (Curve Fitting)</h4>
                <p style="color:#aaa; margin:0; font-size:0.85rem; line-height:1.4;">
                    Los parámetros (EMA 9/21/50, RSI 14, lookback 20) funcionan bien en condiciones 
                    normales pero pueden fallar en regímenes de mercado cambiantes. No hay "santo grial" 
                    en el trading. Los mercados evolucionan y las estrategias dejan de funcionar.
                </p>
            </div>
            
            <div style="background:#0c0e12; padding:15px; border-radius:8px; border:1px solid #ff980033;">
                <h4 style="color:#ff9800; margin:0 0 8px 0; font-size:0.95rem;">💡 Uso Recomendado</h4>
                <p style="color:#aaa; margin:0; font-size:0.85rem; line-height:1.4;">
                    Usa esta herramienta como <strong>filtro de probabilidad</strong>, no como señal de 
                    entrada única. Combínala con:<br>
                    • Análisis fundamental del activo<br>
                    • Contexto macroeconómico (noticias, earnings)<br>
                    • Gestión de riesgo estricta (stop losses, sizing)<br>
                    • Diario de trading para trackear tu edge real
                </p>
            </div>
        </div>
        
        <div style="margin-top:20px; padding:15px; background:#f2364511; border-radius:8px; text-align:center;">
            <p style="color:#f23645; margin:0; font-size:0.9rem; font-weight:bold;">
                🚨 NUNCA ARRIESGUES MÁS DEL 1-2% DE TU CAPITAL EN UNA SOLA OPERACIÓN 🚨
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# COMPONENTES UI
# ────────────────────────────────────────────────

def render_metric_card(title, value, subtitle, color, icon=""):
    st.markdown(f"""
    <div style="background:#0c0e12; padding:15px; border-radius:10px; border:1px solid #1a1e26; text-align:center;">
        <div style="color:#888; font-size:11px; text-transform:uppercase; margin-bottom:5px;">{title}</div>
        <div style="color:{color}; font-size:28px; font-weight:bold;">{icon} {value}</div>
        <div style="color:#666; font-size:10px; margin-top:5px;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def render_verdict_banner(score_data):
    grade, grade_text = score_data['grade']
    verdict, color = score_data['verdict']
    
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border:2px solid {color}; border-radius:15px; 
                padding:25px; text-align:center; margin:20px 0; box-shadow:0 0 20px {color}33;">
        <div style="display:flex; justify-content:center; align-items:center; gap:20px; margin-bottom:15px;">
            <div style="font-size:64px; font-weight:bold; color:{color};">{score_data['total']}</div>
            <div style="text-align:left;">
                <div style="font-size:24px; color:{color}; font-weight:bold;">{grade}</div>
                <div style="font-size:12px; color:#888;">{grade_text}</div>
            </div>
        </div>
        <div style="font-size:18px; color:white; font-weight:bold; letter-spacing:1px;">{verdict}</div>
        <div style="margin-top:15px; display:flex; justify-content:center; gap:10px; flex-wrap:wrap;">
            <span style="background:#00ffad22; color:#00ffad; padding:5px 12px; border-radius:15px; font-size:11px;">Z-Score: {score_data['z_component']}/40</span>
            <span style="background:#2196f322; color:#2196f3; padding:5px 12px; border-radius:15px; font-size:11px;">Tendencia: {score_data['trend_component']}/30</span>
            <span style="background:#ff980022; color:#ff9800; padding:5px 12px; border-radius:15px; font-size:11px;">Volumen: {score_data['volume_component']}/20</span>
            <span style="background:#9c27b022; color:#9c27b0; padding:5px 12px; border-radius:15px; font-size:11px;">RSI: {score_data['rsi_component']}/10</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .stApp { background: #0c0e12; }
        h1, h2, h3 { color: white !important; }
        p { color: #ccc !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { 
            background: #0c0e12; 
            color: #888; 
            border: 1px solid #1a1e26;
            border-radius: 8px 8px 0 0;
        }
        .stTabs [aria-selected="true"] { 
            background: #1a1e26; 
            color: #00ffad; 
            border-bottom: 2px solid #00ffad;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align:center; margin-bottom:30px;">
        <h1 style="font-size:2.5rem; margin-bottom:10px;">⚡ RSU EMA EDGE</h1>
        <p style="color:#888; font-size:1.1rem; max-width:600px; margin:0 auto;">Detector de Mentiras y Medidor de Riesgo Científico</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs para organizar la información
    tab1, tab2, tab3 = st.tabs(["🎯 Análisis", "📚 Metodología", "⚠️ Riesgos"])
    
    with tab1:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            symbol = st.text_input("Símbolo del Activo", value="AAPL", 
                                  help="Ingresa el ticker (ej: AAPL, MSFT, BTC-USD)", key="symbol_input").upper().strip()
        
        with col2:
            timeframe = st.selectbox("Timeframe Principal", ["15m", "1h", "4h", "1d"], index=3, key="timeframe_select")
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_btn = st.button("🔍 ANALIZAR", use_container_width=True, type="primary", key="analyze_button")
        
        show_debug = st.checkbox("Mostrar debug de datos", value=False, key="debug_checkbox")
        
        if analyze_btn or symbol:
            with st.spinner("Calculando matrices de probabilidad..."):
                try:
                    tf_map = {"15m": ("5d", "15m"), "1h": ("1mo", "1h"), "4h": ("3mo", "1h"), "1d": ("1y", "1d")}
                    period, interval = tf_map.get(timeframe, ("1y", "1d"))
                    
                    if show_debug:
                        st.write(f"Descargando: {symbol} | Periodo: {period} | Intervalo: {interval}")
                    
                    data = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
                    
                    if show_debug:
                        st.write("Estructura original:")
                        st.write(f"Columns: {data.columns.tolist()}")
                    
                    if data.empty:
                        st.error(f"No se pudieron descargar datos para {symbol}.")
                        return
                    
                    data = flatten_columns(data)
                    
                    if show_debug:
                        st.write("Después de flatten_columns:")
                        st.write(f"Columns: {data.columns.tolist()}")
                        st.dataframe(data.head(3))
                    
                    required = ['Close', 'High', 'Low', 'Open']
                    missing = [r for r in required if r not in data.columns]
                    
                    if missing:
                        st.error(f"Faltan columnas: {missing}")
                        st.write(f"Columnas disponibles: {data.columns.tolist()}")
                        return
                    
                    if len(data) < 50:
                        st.error(f"Datos insuficientes ({len(data)} filas).")
                        return
                    
                    # Cálculos
                    close = ensure_1d_series(data['Close'])
                    ema_21 = calculate_ema(close, 21)
                    current_z = float(calculate_z_score(close, ema_21).iloc[-1])
                    
                    trends = get_multi_timeframe_trend(symbol)
                    vol_analysis = analyze_volume_profile(data)
                    
                    rsi_series = calculate_rsi(close)
                    rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
                    
                    trend_alignment = {k: v.get('trend') for k, v in trends.items()}
                    rsu_data = calculate_rsu_score(current_z, trend_alignment, vol_analysis['volume_ratio'], rsi)
                    
                    # Dashboard
                    render_verdict_banner(rsu_data)
                    
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        render_metric_card("TENSIÓN ELÁSTICA", f"{current_z:+.2f}σ", "Z-Score vs EMA21", get_z_color(current_z), "⚡")
                    with m2:
                        trend_1d = trends.get('1D', {}).get('trend', 'N/A')
                        trend_color = "#00ffad" if trend_1d == "BULLISH" else "#f23645" if trend_1d == "BEARISH" else "#888"
                        render_metric_card("TENDENCIA 1D", trend_1d, "Dirección principal", trend_color, "📈")
                    with m3:
                        vol_color = "#00ffad" if vol_analysis['volume_ratio'] > 1.5 else "#ff9800" if vol_analysis['volume_ratio'] > 1 else "#f23645"
                        render_metric_card("VOLUMEN", f"{vol_analysis['volume_ratio']:.2f}x", "vs Promedio 20d", vol_color, "⛽")
                    with m4:
                        rsi_color = "#00ffad" if 40 <= rsi <= 60 else "#ff9800" if 30 <= rsi < 40 or 60 < rsi <= 70 else "#f23645"
                        render_metric_card("RSI", f"{rsi:.1f}", "Momentum 14d", rsi_color, "💪")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    g1, g2 = st.columns([2, 1])
                    with g1:
                        st.plotly_chart(create_price_chart_with_emas(data, symbol), use_container_width=True, key="price_chart")
                    with g2:
                        st.plotly_chart(create_z_score_gauge(current_z), use_container_width=True, key="z_gauge")
                        
                        z_interp = "✅ Precio cerca de la media." if abs(current_z) <= 0.5 else "⚠️ Ligera desviación." if abs(current_z) <= 1 else "🚨 Precio estirado." if abs(current_z) <= 2 else "❌ Extremo estadístico."
                        st.markdown(f"""
                        <div style="background:#0c0e12; padding:12px; border-radius:8px; border-left:3px solid {get_z_color(current_z)}; margin-top:10px;">
                            <div style="color:white; font-size:12px; font-weight:bold;">Interpretación:</div>
                            <div style="color:#aaa; font-size:11px;">{z_interp}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    g3, g4 = st.columns(2)
                    with g3:
                        st.plotly_chart(create_trend_alignment_chart(trends), use_container_width=True, key="trend_chart")
                    with g4:
                        st.plotly_chart(create_rsu_score_radar(rsu_data), use_container_width=True, key="radar_chart")
                    
                    st.plotly_chart(create_volume_heatmap(data, vol_analysis), use_container_width=True, key="vol_chart")
                    
                    # Detalles técnicos en expander
                    with st.expander("🔬 DETALLES TÉCNICOS DEL CÁLCULO", expanded=False):
                        st.subheader("Parámetros Utilizados")
                        st.json({
                            "símbolo": symbol,
                            "timeframe_principal": timeframe,
                            "periodo_descarga": period,
                            "intervalo": interval,
                            "filas_datos": len(data),
                            "rango_fechas": f"{data.index[0].strftime('%Y-%m-%d')} a {data.index[-1].strftime('%Y-%m-%d')}"
                        })
                        
                        st.subheader("Cálculos por Componente")
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            st.markdown("**Z-Score (Tensión Elástica)**")
                            st.code(f"""
Precio actual: {float(close.iloc[-1]):.2f}
EMA 21: {float(ema_21.iloc[-1]):.2f}
Desviación estándar (20d): {float(close.rolling(20).std().iloc[-1]):.2f}
Z-Score: (Precio - EMA) / STD = {current_z:.3f}
Puntos asignados: {rsu_data['z_component']}/40
                            """)
                            
                            st.markdown("**RSI (Momentum)**")
                            st.code(f"""
RSI (14 días): {rsi:.2f}
Zona: {"Neutral (40-60)" if 40 <= rsi <= 60 else "Alta (60-70)" if 60 < rsi <= 70 else "Baja (30-40)" if 30 <= rsi < 40 else "Extrema"}
Puntos asignados: {rsu_data['rsi_component']}/10
                            """)
                        
                        with col_c2:
                            st.markdown("**Multi-Timeframe**")
                            for tf, info in trends.items():
                                st.write(f"• **{tf}**: {info.get('trend', 'N/A')} (fuerza: {info.get('strength', 0):.3f}%)")
                            st.code(f"Timeframes alcistas: {len([t for t in trend_alignment.values() if t == 'BULLISH'])}/4\nPuntos asignados: {rsu_data['trend_component']}/30")
                            
                            st.markdown("**Volumen**")
                            st.code(f"""
Volumen hoy: {vol_analysis['current_volume']:,}
Promedio 20d: {vol_analysis['avg_volume']:,}
Ratio: {vol_analysis['volume_ratio']:.2f}x
Tendencia: {vol_analysis['trend_volume']}
Puntos asignados: {rsu_data['volume_component']}/20
                            """)
                        
                        st.subheader("Fórmula Final")
                        st.code(f"""
RSU SCORE = {rsu_data['z_component']} + {rsu_data['trend_component']} + {rsu_data['volume_component']} + {rsu_data['rsi_component']} = {rsu_data['total']}/100
                        """)
                        
                        st.info("""
                        **Nota técnica**: El Z-Score asume distribución normal de retornos, lo cual 
                        es una aproximación. Los mercados financieros tienen "colas gordas" (fat tails), 
                        meaning que eventos extremos son más probables que en una distribución normal pura.
                        """)
                    
                except Exception as e:
                    st.error(f"Error en el análisis: {str(e)}")
                    import traceback
                    with st.expander("Detalles técnicos del error"):
                        st.code(traceback.format_exc())
    
    with tab2:
        render_explanation_section()
    
    with tab3:
        render_risks_section()
