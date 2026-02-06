# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components

# ────────────────────────────────────────────────
# FUNCIONES AUXILIARES PARA MANEJAR MULTIINDEX
# ────────────────────────────────────────────────

def flatten_columns(df):
    """
    Aplana las columnas MultiIndex de yfinance (ticker, campo) -> campo
    """
    if isinstance(df.columns, pd.MultiIndex):
        # Si es MultiIndex, tomar el segundo nivel (Close, Open, etc)
        df.columns = df.columns.get_level_values(1)
    return df

def safe_get_series(df, column):
    """
    Extrae una serie de forma segura, manejando MultiIndex
    """
    df = flatten_columns(df)
    if column in df.columns:
        series = df[column]
        # Asegurar que es una Serie 1D, no DataFrame
        if isinstance(series, pd.DataFrame):
            return series.iloc[:, 0]
        return series
    return None

# ────────────────────────────────────────────────
# CÁLCULOS MATEMÁTICOS - NÚCLEO DEL RSU EMA EDGE
# ────────────────────────────────────────────────

def calculate_ema(prices, period):
    """Calcula EMA usando fórmula estándar"""
    # Asegurar que prices es 1D
    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0]
    return prices.ewm(span=period, adjust=False).mean()

def calculate_z_score(price, ema, std_period=20):
    """
    Z-Score: Medida de "Tensión Elástica"
    Cuántas desviaciones estándar está el precio de la EMA
    """
    # Asegurar 1D
    if isinstance(price, pd.DataFrame):
        price = price.iloc[:, 0]
    if isinstance(ema, pd.DataFrame):
        ema = ema.iloc[:, 0]
    
    std = price.rolling(window=std_period).std()
    z_score = (price - ema) / std
    return z_score

def calculate_rsi(prices, period=14):
    """RSI para confirmación adicional"""
    # Asegurar 1D
    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0]
        
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_multi_timeframe_trend(symbol):
    """
    Análisis Multi-Timeframe: Verifica alineación de tendencias
    Returns: dict con señales de 1D, 4H, 1H, 15m
    """
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
            data = flatten_columns(data)
            
            if len(data) > 50:
                close = data['Close']
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
    """
    Análisis de Volumen: "Gasolina Real"
    Compara volumen actual vs promedio para detectar participación institucional
    """
    data = flatten_columns(data)
    
    if 'Volume' not in data.columns or data['Volume'].isna().all():
        return {
            'current_volume': 0,
            'avg_volume': 0,
            'volume_ratio': 1,
            'trend_volume': "NEUTRAL",
            'institutional_participation': False
        }
    
    volume = data['Volume']
    # Asegurar 1D
    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]
    
    current_vol = float(volume.iloc[-1])
    avg_vol = float(volume.tail(lookback).mean())
    volume_ratio = current_vol / avg_vol if avg_vol > 0 else 1
    
    # Análisis de tendencia de volumen
    recent_vol = float(volume.tail(5).mean())
    previous_vol = float(volume.iloc[-10:-5].mean()) if len(volume) >= 10 else recent_vol
    vol_trend = "INCREASING" if recent_vol > previous_vol * 1.1 else "DECREASING" if recent_vol < previous_vol * 0.9 else "STABLE"
    
    institutional = volume_ratio > 2.0
    
    return {
        'current_volume': int(current_vol),
        'avg_volume': int(avg_vol),
        'volume_ratio': float(volume_ratio),
        'trend_volume': vol_trend,
        'institutional_participation': institutional
    }

def calculate_rsu_score(z_score, trend_alignment, volume_score, rsi_value):
    """
    RSU Score (0-100): Veredicto Final
    Combina todos los factores en una métrica única
    """
    # Normalizar Z-Score (0-40 puntos)
    z_abs = abs(z_score)
    if z_abs <= 0.5:
        z_points = 40
    elif z_abs <= 1.0:
        z_points = 30
    elif z_abs <= 2.0:
        z_points = 15
    else:
        z_points = 0
    
    # Alineación de tendencia (0-30 puntos)
    tf_count = len([t for t in trend_alignment.values() if t not in ['ERROR', None]])
    bullish_count = len([t for t in trend_alignment.values() if t == 'BULLISH'])
    
    if tf_count > 0:
        alignment_ratio = bullish_count / tf_count
        if alignment_ratio >= 0.75:
            trend_points = 30
        elif alignment_ratio >= 0.5:
            trend_points = 20
        elif alignment_ratio >= 0.25:
            trend_points = 10
        else:
            trend_points = 0
    else:
        trend_points = 0
    
    # Volumen (0-20 puntos)
    if volume_score > 2.0:
        vol_points = 20
    elif volume_score > 1.5:
        vol_points = 15
    elif volume_score > 1.0:
        vol_points = 10
    else:
        vol_points = 5
    
    # RSI (0-10 puntos)
    if 40 <= rsi_value <= 60:
        rsi_points = 10
    elif 30 <= rsi_value < 40 or 60 < rsi_value <= 70:
        rsi_points = 7
    elif 20 <= rsi_value < 30 or 70 < rsi_value <= 80:
        rsi_points = 4
    else:
        rsi_points = 0
    
    total_score = z_points + trend_points + vol_points + rsi_points
    
    return {
        'total': int(total_score),
        'z_component': int(z_points),
        'trend_component': int(trend_points),
        'volume_component': int(vol_points),
        'rsi_component': int(rsi_points),
        'grade': get_grade(total_score),
        'verdict': get_verdict(total_score, z_score)
    }

def get_grade(score):
    if score >= 85: return "A+", "EXCELENTE"
    elif score >= 75: return "A", "MUY BUENA"
    elif score >= 65: return "B", "BUENA"
    elif score >= 50: return "C", "REGULAR"
    elif score >= 35: return "D", "DÉBIL"
    else: return "F", "PELIGROSO"

def get_verdict(score, z_score):
    if score >= 75 and abs(z_score) <= 1:
        return "🟢 OPORTUNIDAD ÓPTIMA", "#00ffad"
    elif score >= 60:
        return "🟡 OPORTUNIDAD MODERADA", "#ff9800"
    elif score >= 40:
        return "🟠 ESPERAR CONFIRMACIÓN", "#ff6d00"
    else:
        return "🔴 ZONA PELIGROSA / EVITAR", "#f23645"

# ────────────────────────────────────────────────
# VISUALIZACIONES AVANZADAS
# ────────────────────────────────────────────────

def create_z_score_gauge(z_score):
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
                {'range': [-3, -2], 'color': "#f2364522"},
                {'range': [-2, -1], 'color': "#ff980022"},
                {'range': [-1, 1], 'color': "#00ffad22"},
                {'range': [1, 2], 'color': "#ff980022"},
                {'range': [2, 3], 'color': "#f2364522"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.8,
                'value': float(z_score)
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="#11141a",
        font={'color': "white", 'family': "Arial"},
        height=280,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def get_z_color(z):
    if abs(z) <= 1:
        return "#00ffad"
    elif abs(z) <= 2:
        return "#ff9800"
    else:
        return "#f23645"

def create_trend_alignment_chart(trends):
    timeframes = list(trends.keys())
    values = []
    colors = []
    labels = []
    
    for tf in timeframes:
        trend_data = trends.get(tf, {})
        trend = trend_data.get('trend', 'ERROR')
        if trend == 'BULLISH':
            values.append(1)
            colors.append("#00ffad")
            labels.append("ALCISTA")
        elif trend == 'BEARISH':
            values.append(-1)
            colors.append("#f23645")
            labels.append("BAJISTA")
        else:
            values.append(0)
            colors.append("#888")
            labels.append("N/A")
    
    fig = go.Figure(data=[
        go.Bar(
            x=timeframes,
            y=values,
            marker_color=colors,
            text=labels,
            textposition='outside',
            textfont=dict(color='white', size=11)
        )
    ])
    
    fig.update_layout(
        paper_bgcolor="#11141a",
        plot_bgcolor="#0c0e12",
        font=dict(color="white"),
        title=dict(text="Alineación de Tendencias (Multi-Timeframe)", font=dict(color="white", size=14)),
        xaxis=dict(color="white", gridcolor="#1a1e26"),
        yaxis=dict(color="white", gridcolor="#1a1e26", range=[-1.5, 1.5], 
                   tickvals=[-1, 0, 1], ticktext=['BAJISTA', 'NEUTRO', 'ALCISTA']),
        height=250,
        margin=dict(l=40, r=20, t=50, b=40),
        showlegend=False
    )
    
    return fig

def create_volume_heatmap(data, vol_analysis):
    data = flatten_columns(data)
    recent_data = data.tail(20).copy()
    
    volume = recent_data['Volume']
    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]
    
    colors = []
    avg_vol = vol_analysis['avg_volume']
    for vol in volume:
        ratio = vol / avg_vol if avg_vol > 0 else 1
        if ratio > 2:
            colors.append("#00ffad")
        elif ratio > 1.5:
            colors.append("#4caf50")
        elif ratio > 1:
            colors.append("#ff9800")
        else:
            colors.append("#f23645")
    
    fig = go.Figure(data=[
        go.Bar(
            x=recent_data.index.strftime('%m-%d'),
            y=volume,
            marker_color=colors,
            hovertemplate='Fecha: %{x}<br>Volumen: %{y:,.0f}<br>Ratio: %{text:.2f}x<extra></extra>',
            text=[v/avg_vol for v in volume]
        )
    ])
    
    fig.add_hline(
        y=avg_vol, 
        line_dash="dash", 
        line_color="white",
        annotation_text="Promedio",
        annotation_position="right"
    )
    
    fig.update_layout(
        paper_bgcolor="#11141a",
        plot_bgcolor="#0c0e12",
        font=dict(color="white"),
        title=dict(text="Volumen Reciente (Gasolina Real)", font=dict(color="white", size=14)),
        xaxis=dict(color="white", gridcolor="#1a1e26", tickangle=-45),
        yaxis=dict(color="white", gridcolor="#1a1e26", title="Volumen"),
        height=250,
        margin=dict(l=50, r=50, t=50, b=60),
        showlegend=False
    )
    
    return fig

def create_rsu_score_radar(score_components):
    categories = ['Z-Score<br>(Tensión)', 'Tendencia<br>(Timeframes)', 'Volumen<br>(Gasolina)', 'RSI<br>(Momentum)']
    values = [
        score_components['z_component'] / 40 * 100,
        score_components['trend_component'] / 30 * 100,
        score_components['volume_component'] / 20 * 100,
        score_components['rsi_component'] / 10 * 100
    ]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(0, 255, 173, 0.3)',
        line=dict(color='#00ffad', width=2),
        marker=dict(size=8, color='#00ffad')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                color='white',
                gridcolor='#1a1e26'
            ),
            angularaxis=dict(
                color='white',
                gridcolor='#1a1e26'
            ),
            bgcolor='#0c0e12'
        ),
        paper_bgcolor='#11141a',
        font=dict(color='white'),
        title=dict(text="Desglose del RSU Score", font=dict(color='white', size=14)),
        height=300,
        margin=dict(l=60, r=60, t=50, b=40)
    )
    
    return fig

def create_price_chart_with_emas(data, symbol):
    data = flatten_columns(data)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.08, 
                        row_heights=[0.7, 0.3],
                        subplot_titles=(f'{symbol} - Análisis Técnico', 'Z-Score Histórico'))
    
    close = data['Close']
    ema_9 = calculate_ema(close, 9)
    ema_21 = calculate_ema(close, 21)
    ema_50 = calculate_ema(close, 50)
    
    z_scores = calculate_z_score(close, ema_21)
    
    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Precio',
        increasing_line_color='#00ffad',
        decreasing_line_color='#f23645'
    ), row=1, col=1)
    
    # EMAs
    fig.add_trace(go.Scatter(x=data.index, y=ema_9, line=dict(color='#00d9ff', width=1.5), name='EMA 9'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=ema_21, line=dict(color='#ff9800', width=1.5), name='EMA 21'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=ema_50, line=dict(color='#9c27b0', width=1.5), name='EMA 50'), row=1, col=1)
    
    # Z-Score
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=z_scores, 
        mode='lines',
        line=dict(color='white', width=1),
        name='Z-Score',
        fill='tozeroy',
        fillcolor='rgba(100,100,100,0.1)'
    ), row=2, col=1)
    
    for level in [-2, -1, 1, 2]:
        fig.add_hline(y=level, line_dash="dash", line_color="#444", line_width=1, row=2, col=1)
    
    fig.add_hline(y=0, line_color="#00ffad", line_width=2, row=2, col=1)
    
    fig.update_layout(
        paper_bgcolor='#11141a',
        plot_bgcolor='#0c0e12',
        font=dict(color='white'),
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=50, r=50, t=50, b=40),
        legend=dict(
            bgcolor='rgba(17, 20, 26, 0.8)',
            bordercolor='#1a1e26',
            borderwidth=1,
            font=dict(color='white')
        )
    )
    
    fig.update_xaxes(gridcolor='#1a1e26', color='white')
    fig.update_yaxes(gridcolor='#1a1e26', color='white')
    
    return fig

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
    <div style="background:linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); 
                border:2px solid {color}; 
                border-radius:15px; 
                padding:25px; 
                text-align:center;
                margin:20px 0;
                box-shadow:0 0 20px {color}33;">
        <div style="display:flex; justify-content:center; align-items:center; gap:20px; margin-bottom:15px;">
            <div style="font-size:64px; font-weight:bold; color:{color};">{score_data['total']}</div>
            <div style="text-align:left;">
                <div style="font-size:24px; color:{color}; font-weight:bold;">{grade}</div>
                <div style="font-size:12px; color:#888;">{grade_text}</div>
            </div>
        </div>
        <div style="font-size:18px; color:white; font-weight:bold; letter-spacing:1px;">
            {verdict}
        </div>
        <div style="margin-top:15px; display:flex; justify-content:center; gap:10px; flex-wrap:wrap;">
            <span style="background:#00ffad22; color:#00ffad; padding:5px 12px; border-radius:15px; font-size:11px;">
                Z-Score: {score_data['z_component']}/40
            </span>
            <span style="background:#2196f322; color:#2196f3; padding:5px 12px; border-radius:15px; font-size:11px;">
                Tendencia: {score_data['trend_component']}/30
            </span>
            <span style="background:#ff980022; color:#ff9800; padding:5px 12px; border-radius:15px; font-size:11px;">
                Volumen: {score_data['volume_component']}/20
            </span>
            <span style="background:#9c27b022; color:#9c27b0; padding:5px 12px; border-radius:15px; font-size:11px;">
                RSI: {score_data['rsi_component']}/10
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .stApp {
            background: #0c0e12;
        }
        div[data-testid="stMetricValue"] {
            color: white !important;
        }
        div[data-testid="stMetricLabel"] {
            color: #888 !important;
        }
        h1, h2, h3 {
            color: white !important;
        }
        p {
            color: #ccc !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align:center; margin-bottom:30px;">
        <h1 style="font-size:2.5rem; margin-bottom:10px;">⚡ RSU EMA EDGE</h1>
        <p style="color:#888; font-size:1.1rem; max-width:600px; margin:0 auto;">
            Detector de Mentiras y Medidor de Riesgo Científico
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        symbol = st.text_input("Símbolo del Activo", value="AAPL", 
                              help="Ingresa el ticker (ej: AAPL, MSFT, BTC-USD)").upper().strip()
    
    with col2:
        timeframe = st.selectbox("Timeframe Principal", 
                                ["15m", "1h", "4h", "1d"],
                                index=3)
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("🔍 ANALIZAR", use_container_width=True, 
                               type="primary")
    
    if analyze_btn or symbol:
        with st.spinner("Calculando matrices de probabilidad..."):
            try:
                tf_map = {
                    "15m": ("5d", "15m"),
                    "1h": ("1mo", "1h"),
                    "4h": ("3mo", "1h"),
                    "1d": ("1y", "1d")
                }
                
                period, interval = tf_map.get(timeframe, ("1y", "1d"))
                
                # Descargar datos
                data = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
                
                if data.empty or len(data) < 50:
                    st.error("Datos insuficientes para análisis. Intenta con otro timeframe o símbolo.")
                    return
                
                # Aplanar columnas inmediatamente
                data = flatten_columns(data)
                
                # Verificar que tenemos las columnas necesarias
                required_cols = ['Close', 'Open', 'High', 'Low']
                missing = [c for c in required_cols if c not in data.columns]
                if missing:
                    st.error(f"Faltan columnas: {missing}")
                    return
                
                # ─── CÁLCULOS PRINCIPALES ───
                
                # 1. Tensión Elástica (Z-Score)
                close = data['Close']
                ema_21 = calculate_ema(close, 21)
                current_z = float(calculate_z_score(close, ema_21).iloc[-1])
                
                # 2. Multi-Timeframe
                trends = get_multi_timeframe_trend(symbol)
                
                # 3. Volumen
                vol_analysis = analyze_volume_profile(data)
                
                # 4. RSI
                rsi_series = calculate_rsi(close)
                rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
                
                # 5. RSU Score Final
                trend_alignment = {k: v.get('trend') for k, v in trends.items()}
                rsu_data = calculate_rsu_score(
                    current_z, 
                    trend_alignment, 
                    vol_analysis['volume_ratio'],
                    rsi
                )
                
                # ─── DASHBOARD DE RESULTADOS ───
                
                render_verdict_banner(rsu_data)
                
                m1, m2, m3, m4 = st.columns(4)
                
                with m1:
                    z_color = get_z_color(current_z)
                    render_metric_card(
                        "TENSIÓN ELÁSTICA", 
                        f"{current_z:+.2f}σ", 
                        "Z-Score vs EMA21", 
                        z_color,
                        "⚡"
                    )
                
                with m2:
                    trend_1d = trends.get('1D', {}).get('trend', 'N/A')
                    trend_color = "#00ffad" if trend_1d == "BULLISH" else "#f23645" if trend_1d == "BEARISH" else "#888"
                    render_metric_card(
                        "TENDENCIA 1D", 
                        trend_1d, 
                        "Dirección principal", 
                        trend_color,
                        "📈"
                    )
                
                with m3:
                    vol_color = "#00ffad" if vol_analysis['volume_ratio'] > 1.5 else "#ff9800" if vol_analysis['volume_ratio'] > 1 else "#f23645"
                    render_metric_card(
                        "VOLUMEN", 
                        f"{vol_analysis['volume_ratio']:.2f}x", 
                        "vs Promedio 20d", 
                        vol_color,
                        "⛽"
                    )
                
                with m4:
                    rsi_color = "#00ffad" if 40 <= rsi <= 60 else "#ff9800" if 30 <= rsi < 40 or 60 < rsi <= 70 else "#f23645"
                    render_metric_card(
                        "RSI", 
                        f"{rsi:.1f}", 
                        "Momentum 14d", 
                        rsi_color,
                        "💪"
                    )
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                g1, g2 = st.columns([2, 1])
                
                with g1:
                    fig_price = create_price_chart_with_emas(data, symbol)
                    st.plotly_chart(fig_price, use_container_width=True, key="price_chart")
                
                with g2:
                    fig_gauge = create_z_score_gauge(current_z)
                    st.plotly_chart(fig_gauge, use_container_width=True, key="z_gauge")
                    
                    z_interpretation = ""
                    if abs(current_z) <= 0.5:
                        z_interpretation = "✅ Precio cerca de la media. Zona óptima para entrada."
                    elif abs(current_z) <= 1:
                        z_interpretation = "⚠️ Ligera desviación. Aceptable con confirmación."
                    elif abs(current_z) <= 2:
                        z_interpretation = "🚨 Precio estirado. Esperar retorno a la media."
                    else:
                        z_interpretation = "❌ Extremo estadístico. Latigazo inminente."
                    
                    st.markdown(f"""
                    <div style="background:#0c0e12; padding:12px; border-radius:8px; border-left:3px solid {get_z_color(current_z)}; margin-top:10px;">
                        <div style="color:white; font-size:12px; font-weight:bold; margin-bottom:5px;">Interpretación:</div>
                        <div style="color:#aaa; font-size:11px; line-height:1.4;">{z_interpretation}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                g3, g4 = st.columns(2)
                
                with g3:
                    fig_trend = create_trend_alignment_chart(trends)
                    st.plotly_chart(fig_trend, use_container_width=True, key="trend_chart")
                
                with g4:
                    fig_radar = create_rsu_score_radar(rsu_data)
                    st.plotly_chart(fig_radar, use_container_width=True, key="radar_chart")
                
                fig_vol = create_volume_heatmap(data, vol_analysis)
                st.plotly_chart(fig_vol, use_container_width=True, key="vol_chart")
                
                with st.expander("📊 ANÁLISIS DETALLADO POR COMPONENTE", expanded=False):
                    
                    st.markdown("""
                    <div style="background:#11141a; border:1px solid #1a1e26; border-radius:10px; padding:20px; margin-bottom:15px;">
                        <h4 style="color:#00ffad; margin-bottom:10px;">1. Tensión Elástica (Z-Score)</h4>
                    """, unsafe_allow_html=True)
                    
                    col_z1, col_z2 = st.columns(2)
                    with col_z1:
                        st.metric("Z-Score Actual", f"{current_z:.3f}")
                        std_val = float(close.rolling(20).std().iloc[-1])
                        st.metric("Desviación Estándar", f"{std_val:.2f}")
                    with col_z2:
                        current_price = float(close.iloc[-1])
                        ema_val = float(ema_21.iloc[-1])
                        st.metric("Distancia a EMA21", f"{((current_price / ema_val - 1) * 100):+.2f}%")
                        st.metric("Probabilidad de Reversión", f"{min(abs(current_z) * 25, 95):.0f}%")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style="background:#11141a; border:1px solid #1a1e26; border-radius:10px; padding:20px; margin-bottom:15px;">
                        <h4 style="color:#2196f3; margin-bottom:10px;">2. Análisis Multi-Timeframe</h4>
                    """, unsafe_allow_html=True)
                    
                    trend_df_data = []
                    for tf, info in trends.items():
                        trend_df_data.append({
                            'Timeframe': tf,
                            'Tendencia': info.get('trend', 'N/A'),
                            'Fuerza (%)': f"{info.get('strength', 0):.3f}",
                            'Precio': f"${info.get('price', 0):.2f}",
                            'EMA Rápida': f"${info.get('ema_fast', 0):.2f}",
                            'EMA Lenta': f"${info.get('ema_slow', 0):.2f}"
                        })
                    
                    st.dataframe(pd.DataFrame(trend_df_data), use_container_width=True, hide_index=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style="background:#11141a; border:1px solid #1a1e26; border-radius:10px; padding:20px; margin-bottom:15px;">
                        <h4 style="color:#ff9800; margin-bottom:10px;">3. Análisis de Volumen (Gasolina Real)</h4>
                    """, unsafe_allow_html=True)
                    
                    col_v1, col_v2, col_v3 = st.columns(3)
                    with col_v1:
                        st.metric("Volumen Actual", f"{vol_analysis['current_volume']:,}")
                    with col_v2:
                        st.metric("Volumen Promedio (20d)", f"{vol_analysis['avg_volume']:,}")
                    with col_v3:
                        st.metric("Tendencia de Volumen", vol_analysis['trend_volume'])
                    
                    inst_part = "✅ SÍ" if vol_analysis['institutional_participation'] else "❌ NO"
                    st.markdown(f"""
                    <div style="margin-top:15px; padding:10px; background:#0c0e12; border-radius:5px;">
                        <span style="color:white; font-weight:bold;">Participación Institucional Detectada:</span> 
                        <span style="color:{'#00ffad' if vol_analysis['institutional_participation'] else '#f23645'}; font-weight:bold;">{inst_part}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style="background:#11141a; border:1px solid #1a1e26; border-radius:10px; padding:20px;">
                        <h4 style="color:#9c27b0; margin-bottom:10px;">4. Fórmula del RSU Score</h4>
                        <div style="background:#0c0e12; padding:15px; border-radius:5px; font-family:monospace; font-size:12px; color:#00ffad;">
                    """, unsafe_allow_html=True)
                    
                    st.code(f"""
RSU Score = Z_Component + Trend_Component + Volume_Component + RSI_Component

Z-Score ({rsu_data['z_component']}/40):
  • |Z| ≤ 0.5 → 40 pts (Zona Óptima)
  • 0.5 < |Z| ≤ 1.0 → 30 pts (Buena)
  • 1.0 < |Z| ≤ 2.0 → 15 pts (Precaución)
  • |Z| > 2.0 → 0 pts (Peligro)

Tendencia ({rsu_data['trend_component']}/30):
  • 75%+ timeframes alineados → 30 pts
  • 50-75% → 20 pts
  • 25-50% → 10 pts
  • <25% → 0 pts

Volumen ({rsu_data['volume_component']}/20):
  • Ratio > 2.0x → 20 pts (Confirmación Fuerte)
  • 1.5-2.0x → 15 pts
  • 1.0-1.5x → 10 pts
  • <1.0x → 5 pts (Señal Débil)

RSI ({rsu_data['rsi_component']}/10):
  • 40-60 → 10 pts (Zona Neutral)
  • 30-40 o 60-70 → 7 pts
  • 20-30 o 70-80 → 4 pts
  • Extremo → 0 pts

TOTAL: {rsu_data['total']}/100
                    """, language=None)
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                st.markdown("""
                <div style="margin-top:30px; padding:15px; background:#1a1e26; border-radius:8px; border-left:3px solid #ff9800;">
                    <div style="color:#ff9800; font-weight:bold; font-size:12px; margin-bottom:5px;">⚠️ ADVERTENCIA</div>
                    <div style="color:#888; font-size:11px; line-height:1.4;">
                        Esta herramienta proporciona análisis estadístico basado en datos históricos. 
                        No predice el futuro. El Z-Score mide desviaciones estadísticas, no garantiza reversión. 
                        El análisis de volumen detecta anomalías, no intención institucional directa. 
                        Siempre combina esta información con tu propio análisis y gestión de riesgo.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error en el análisis: {str(e)}")
                st.info("Verifica que el símbolo sea correcto (ej: AAPL, MSFT, BTC-USD, ETH-USD)")
                import traceback
                with st.expander("Detalles técnicos del error"):
                    st.code(traceback.format_exc())
