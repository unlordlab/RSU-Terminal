# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.calibration import CalibratedClassifierCV
import warnings
warnings.filterwarnings('ignore')

# ────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ────────────────────────────────────────────────

def flatten_columns(df):
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df

def ensure_1d_series(data):
    if isinstance(data, pd.DataFrame):
        if data.shape[1] == 1:
            return data.iloc[:, 0]
        if 'Close' in data.columns:
            return data['Close']
        return data.iloc[:, 0]
    return data

def hex_to_rgba(hex_color, alpha=1.0):
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
    """Z-Score calculado sobre retornos logarítmicos para estacionariedad.
    Evita que el std escale con el nivel de precio absoluto."""
    price = ensure_1d_series(price)
    ema   = ensure_1d_series(ema)
    # Retornos log: estacionarios y comparables entre activos/épocas
    log_returns = np.log(price / price.shift(1))
    std_returns = log_returns.rolling(window=std_period).std()
    # Desviación relativa al precio actual, normalizada por vol de retornos
    deviation = (price - ema) / ema  # desviación porcentual respecto a la EMA
    return deviation / std_returns.replace(0, np.nan)

def calculate_rsi(prices, period=14):
    """RSI con suavizado de Wilder (ewm alpha=1/period), estándar de la industria."""
    prices = ensure_1d_series(prices)
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    # Wilder smoothing: alpha = 1/period (equivalente a com=period-1)
    avg_gain = gain.ewm(com=period - 1, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=300, show_spinner=False)
@st.cache_data(ttl=300, show_spinner=False)
def download_data(symbol, period, interval):
    """Descarga cacheada con TTL 5min. Normaliza índice a DatetimeIndex sin timezone."""
    data = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    if not data.empty:
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        # Quitar tz para evitar fechas incorrectas en strftime (bug yfinance + pandas)
        if hasattr(data.index, 'tz') and data.index.tz is not None:
            data.index = data.index.tz_localize(None)
    return data

@st.cache_data(ttl=300, show_spinner=False)
def get_multi_timeframe_trend(symbol):
    timeframes = {
        '1D': ('1y', '1d'),
        '4H': ('3mo', '1h'),
        '1H': ('1mo', '1h'),
        '15m': ('5d', '15m')
    }

    def fetch_tf(tf, period, interval):
        try:
            data = download_data(symbol, period, interval)
            if data.empty:
                return tf, {'trend': 'NO_DATA', 'strength': 0}
            data = flatten_columns(data)
            if 'Close' not in data.columns or len(data) < 50:
                return tf, {'trend': 'INSUFFICIENT_DATA', 'strength': 0}
            close = ensure_1d_series(data['Close'])
            ema_fast = calculate_ema(close, 9 if tf in ['15m', '1H'] else 20)
            ema_slow = calculate_ema(close, 21 if tf in ['15m', '1H'] else 50)
            current_price = float(close.iloc[-1])
            ema_fast_val = float(ema_fast.iloc[-1])
            ema_slow_val = float(ema_slow.iloc[-1])
            trend = "BULLISH" if ema_fast_val > ema_slow_val else "BEARISH"
            strength = abs(ema_fast_val - ema_slow_val) / current_price * 100
            return tf, {
                'trend': trend, 'strength': float(strength),
                'price': float(current_price), 'ema_fast': float(ema_fast_val), 'ema_slow': float(ema_slow_val)
            }
        except Exception as e:
            return tf, {'trend': 'ERROR', 'strength': 0, 'error': str(e)}

    trends = {}
    # Paralelizar las 4 descargas simultáneamente (reducción típica: 4x → 1x latencia)
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_tf, tf, period, interval): tf
                   for tf, (period, interval) in timeframes.items()}
        for future in as_completed(futures):
            tf, result = future.result()
            trends[tf] = result
    return trends

def analyze_volume_profile(data, lookback=20):
    data = flatten_columns(data)
    if 'Volume' not in data.columns:
        return {'current_volume': 0, 'avg_volume': 0, 'volume_ratio': 1,
                'trend_volume': "NEUTRAL", 'institutional_participation': False,
                'directional_bias': 'NEUTRAL', 'buy_pressure': 0.5}
    volume = ensure_1d_series(data['Volume'])
    close  = ensure_1d_series(data['Close']) if 'Close' in data.columns else None
    open_  = ensure_1d_series(data['Open'])  if 'Open'  in data.columns else None

    if len(volume) < lookback:
        return {'current_volume': 0, 'avg_volume': 0, 'volume_ratio': 1,
                'trend_volume': "NEUTRAL", 'institutional_participation': False,
                'directional_bias': 'NEUTRAL', 'buy_pressure': 0.5}

    current_vol = float(volume.iloc[-1])
    avg_vol     = float(volume.tail(lookback).mean())
    volume_ratio = current_vol / avg_vol if avg_vol > 0 else 1

    recent_vol   = float(volume.tail(5).mean())
    previous_vol = float(volume.iloc[-10:-5].mean()) if len(volume) >= 10 else recent_vol
    vol_trend    = ("INCREASING" if recent_vol > previous_vol * 1.1
                    else "DECREASING" if recent_vol < previous_vol * 0.9 else "STABLE")

    # Volumen direccional: separar velas alcistas vs bajistas
    buy_pressure = 0.5
    directional_bias = 'NEUTRAL'
    if close is not None and open_ is not None:
        recent = data.tail(lookback).copy()
        r_vol   = ensure_1d_series(recent['Volume'])
        r_close = ensure_1d_series(recent['Close'])
        r_open  = ensure_1d_series(recent['Open'])
        bull_vol = r_vol[r_close >= r_open].sum()
        bear_vol = r_vol[r_close < r_open].sum()
        total_dir_vol = bull_vol + bear_vol
        if total_dir_vol > 0:
            buy_pressure = float(bull_vol / total_dir_vol)
            directional_bias = ('COMPRADOR' if buy_pressure > 0.6
                                else 'VENDEDOR' if buy_pressure < 0.4 else 'NEUTRAL')

    return {
        'current_volume': int(current_vol), 'avg_volume': int(avg_vol),
        'volume_ratio': float(volume_ratio), 'trend_volume': vol_trend,
        'institutional_participation': volume_ratio > 2.0,
        'directional_bias': directional_bias, 'buy_pressure': buy_pressure
    }

def calculate_rsu_score(z_score, trend_alignment, volume_score, rsi_value):
    z_abs = abs(z_score)
    z_points = 40 if z_abs <= 0.5 else 30 if z_abs <= 1.0 else 15 if z_abs <= 2.0 else 0

    # Pesos por timeframe: mayor timeframe = mayor peso (jerarquía de tendencia)
    TF_WEIGHTS = {'1D': 0.45, '4H': 0.30, '1H': 0.15, '15m': 0.10}
    weighted_bullish = 0.0
    total_weight = 0.0
    valid_trends = {}
    for tf, trend in trend_alignment.items():
        if trend not in ['ERROR', 'NO_DATA', 'INSUFFICIENT_DATA', None]:
            w = TF_WEIGHTS.get(tf, 0.1)
            total_weight += w
            valid_trends[tf] = trend
            if trend == 'BULLISH':
                weighted_bullish += w
    if total_weight > 0:
        ratio = weighted_bullish / total_weight
        trend_points = 30 if ratio >= 0.75 else 20 if ratio >= 0.5 else 10 if ratio >= 0.25 else 0
    else:
        trend_points = 0
    vol_points = 20 if volume_score > 2.0 else 15 if volume_score > 1.5 else 10 if volume_score > 1.0 else 5
    rsi_points = 10 if 40 <= rsi_value <= 60 else 7 if 30 <= rsi_value < 40 or 60 < rsi_value <= 70 else 4 if 20 <= rsi_value < 30 or 70 < rsi_value <= 80 else 0
    total = z_points + trend_points + vol_points + rsi_points
    grade = "A+" if total >= 85 else "A" if total >= 75 else "B" if total >= 65 else "C" if total >= 50 else "D" if total >= 35 else "F"
    grade_text = "EXCELENTE" if total >= 85 else "MUY BUENA" if total >= 75 else "BUENA" if total >= 65 else "REGULAR" if total >= 50 else "DÉBIL" if total >= 35 else "PELIGROSO"
    if total >= 75 and abs(z_score) <= 1:
        verdict, color = "▸ OPORTUNIDAD ÓPTIMA", "#00ffad"
    elif total >= 60:
        verdict, color = "▸ OPORTUNIDAD MODERADA", "#ff9800"
    elif total >= 40:
        verdict, color = "▸ ESPERAR CONFIRMACIÓN", "#ff6d00"
    else:
        verdict, color = "▸ ZONA PELIGROSA // EVITAR", "#f23645"
    return {
        'total': total, 'z_component': z_points, 'trend_component': trend_points,
        'volume_component': vol_points, 'rsi_component': rsi_points,
        'trend_ratio': ratio if total_weight > 0 else 0,
        'grade': (grade, grade_text), 'verdict': (verdict, color)
    }

def get_z_color(z):
    return "#00ffad" if abs(z) <= 1 else "#ff9800" if abs(z) <= 2 else "#f23645"

# ────────────────────────────────────────────────
# VISUALIZACIONES
# ────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0c0e12",
    plot_bgcolor="#0a0c10",
    font=dict(color="white", family="Courier New, monospace"),
)

def create_z_score_gauge(z_score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=float(z_score),
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "TENSIÓN ELÁSTICA // Z-SCORE", 'font': {'size': 13, 'color': '#00ffad', 'family': 'VT323, monospace'}},
        number={'font': {'size': 28, 'color': 'white', 'family': 'VT323, monospace'}, 'suffix': "σ"},
        delta={'reference': 0, 'position': "top"},
        gauge={
            'axis': {'range': [-3, 3], 'tickwidth': 1, 'tickcolor': "#1a1e26"},
            'bar': {'color': get_z_color(z_score), 'thickness': 0.75},
            'bgcolor': "#0a0c10",
            'borderwidth': 2,
            'bordercolor': "rgba(0,255,173,0.2)",
            'steps': [
                {'range': [-3, -2], 'color': hex_to_rgba("#f23645", 0.15)},
                {'range': [-2, -1], 'color': hex_to_rgba("#ff9800", 0.15)},
                {'range': [-1, 1],  'color': hex_to_rgba("#00ffad", 0.12)},
                {'range': [1, 2],   'color': hex_to_rgba("#ff9800", 0.15)},
                {'range': [2, 3],   'color': hex_to_rgba("#f23645", 0.15)}
            ],
            'threshold': {'line': {'color': "white", 'width': 3}, 'thickness': 0.8, 'value': float(z_score)}
        }
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280, margin=dict(l=20, r=20, t=55, b=20))
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
            values.append(0); colors.append("#444"); labels.append("N/A")
    fig = go.Figure(data=[go.Bar(
        x=timeframes, y=values, marker_color=colors,
        marker_line=dict(color="rgba(0,255,173,0.27)", width=1),
        text=labels, textposition='outside',
        textfont=dict(color='white', size=11, family='VT323, monospace')
    )])
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="ALINEACIÓN MULTI-TIMEFRAME", font=dict(color="#00ffad", size=13, family='VT323, monospace')),
        xaxis=dict(color="white", gridcolor="#1a1e26", tickfont=dict(family='Courier New')),
        yaxis=dict(color="white", gridcolor="#1a1e26", range=[-1.6, 1.6],
                   tickvals=[-1, 0, 1], ticktext=['BAJISTA', 'NEUTRO', 'ALCISTA'],
                   tickfont=dict(family='Courier New')),
        height=260, margin=dict(l=50, r=20, t=50, b=40), showlegend=False
    )
    return fig

def create_volume_heatmap(data, vol_analysis):
    data = flatten_columns(data)
    recent_data = data.tail(20).copy()
    if 'Volume' not in recent_data.columns:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_LAYOUT, title=dict(text="SIN DATOS DE VOLUMEN", font=dict(color="#f23645")))
        return fig

    volume  = ensure_1d_series(recent_data['Volume'])
    avg_vol = vol_analysis['avg_volume']

    # Detectar si el índice incluye hora (intradía) o solo fecha (diario)
    idx = recent_data.index
    has_time = hasattr(idx[0], 'hour') and (idx[-1] - idx[0]).days < 7
    if has_time:
        x_labels = [ts.strftime('%d/%m %H:%M') for ts in idx]
    else:
        x_labels = [ts.strftime('%d %b %Y') for ts in idx]

    bar_colors, ratios, ratio_labels = [], [], []
    for vol in volume:
        ratio = vol / avg_vol if avg_vol > 0 else 1
        ratios.append(ratio)
        ratio_labels.append(f'{ratio:.2f}x')
        bar_colors.append(
            "#00ffad" if ratio > 2 else
            "#4caf50" if ratio > 1.5 else
            "#ff9800" if ratio > 1.0 else
            "#f23645"
        )

    fig = go.Figure(data=[go.Bar(
        x=x_labels,
        y=list(volume),
        marker_color=bar_colors,
        marker_line=dict(color="rgba(0,255,173,0.13)", width=0.5),
        text=ratio_labels,
        textposition='outside',
        textfont=dict(color='white', family='Courier New', size=9),
        hovertemplate='<b>%{x}</b><br>Volumen: %{y:,.0f}<br>Ratio vs avg: %{text}<extra></extra>',
        cliponaxis=False,
    )])

    fig.add_hline(
        y=avg_vol, line_dash="dash", line_color="rgba(0,255,173,0.5)",
        annotation_text="AVG 20d", annotation_position="top right",
        annotation_font=dict(color="#00ffad", family="Courier New", size=10)
    )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="VOLUMEN // GASOLINA DEL MOVIMIENTO (últimas 20 velas)",
                   font=dict(color="#00ffad", size=13, family='VT323, monospace')),
        xaxis=dict(color="white", gridcolor="#1a1e26", tickangle=-45,
                   tickfont=dict(family='Courier New', size=9)),
        yaxis=dict(color="white", gridcolor="#1a1e26", title="",
                   tickfont=dict(family='Courier New')),
        height=300, margin=dict(l=50, r=60, t=55, b=80), showlegend=False
    )
    return fig

def create_rsu_score_radar(score_components):
    categories = ['Z-SCORE', 'TENDENCIA', 'VOLUMEN', 'RSI']
    values = [
        score_components['z_component'] / 40 * 100,
        score_components['trend_component'] / 30 * 100,
        score_components['volume_component'] / 20 * 100,
        score_components['rsi_component'] / 10 * 100
    ]
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]], theta=categories + [categories[0]],
        fill='toself', fillcolor='rgba(0, 255, 173, 0.12)',
        line=dict(color='#00ffad', width=2),
        marker=dict(size=7, color='#00ffad', symbol='diamond')
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color='#888', gridcolor='#1a1e26',
                            tickfont=dict(family='Courier New', size=9)),
            angularaxis=dict(color='#00ffad', gridcolor='#1a1e26',
                             tickfont=dict(family='VT323, monospace', size=14)),
            bgcolor='#0a0c10'
        ),
        paper_bgcolor='#0c0e12', font=dict(color='white', family='Courier New'),
        title=dict(text="RSU SCORE // DESGLOSE", font=dict(color='#00ffad', size=13, family='VT323, monospace')),
        height=300, margin=dict(l=60, r=60, t=50, b=40)
    )
    return fig

def create_price_chart_with_emas(data, symbol):
    data = flatten_columns(data)
    close = ensure_1d_series(data['Close'])
    ema_9  = calculate_ema(close, 9)
    ema_21 = calculate_ema(close, 21)
    ema_50 = calculate_ema(close, 50)
    z_scores = calculate_z_score(close, ema_21)

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{symbol} // ANÁLISIS TÉCNICO', 'Z-SCORE HISTÓRICO')
    )

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=ensure_1d_series(data['Open']),
        high=ensure_1d_series(data['High']),
        low=ensure_1d_series(data['Low']),
        close=close, name='PRECIO',
        increasing_line_color='#00ffad', decreasing_line_color='#f23645',
        increasing_fillcolor='rgba(0,255,173,0.6)', decreasing_fillcolor='rgba(242,54,69,0.6)'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=data.index, y=ema_9,  line=dict(color='#00d9ff', width=1.5, dash='dot'), name='EMA 9'),  row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=ema_21, line=dict(color='#ff9800', width=1.5), name='EMA 21'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=ema_50, line=dict(color='#9c27b0', width=1.5), name='EMA 50'), row=1, col=1)

    z_color = z_scores.apply(get_z_color)
    fig.add_trace(go.Scatter(
        x=data.index, y=z_scores, mode='lines',
        line=dict(color='#00ffad', width=1.5),
        name='Z-SCORE', fill='tozeroy', fillcolor='rgba(0,255,173,0.05)'
    ), row=2, col=1)

    for level in [-2, -1, 1, 2]:
        fig.add_hline(y=level, line_dash="dash", line_color="#333", line_width=1, row=2, col=1)
    fig.add_hline(y=0, line_color="rgba(0,255,173,0.27)", line_width=1.5, row=2, col=1)

    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_rangeslider_visible=False, height=520,
        margin=dict(l=50, r=50, t=60, b=40),
        legend=dict(bgcolor='rgba(12,14,18,0.9)', bordercolor='rgba(0,255,173,0.2)', borderwidth=1,
                    font=dict(color='white', family='Courier New', size=11))
    )
    fig.update_annotations(font=dict(color='#00ffad', family='VT323, monospace', size=14))
    fig.update_xaxes(gridcolor='#1a1e26', color='white')
    fig.update_yaxes(gridcolor='#1a1e26', color='white')
    return fig

# ────────────────────────────────────────────────
# CSS Y ESTILOS GLOBALES
# ────────────────────────────────────────────────

GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

    .stApp { background: #0c0e12; }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'VT323', monospace !important;
        color: #00ffad !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    h1 {
        font-size: 3.5rem !important;
        text-shadow: 0 0 20px #00ffad55;
        border-bottom: 2px solid #00ffad;
        padding-bottom: 12px;
    }
    h2 {
        font-size: 2rem !important;
        color: #00d9ff !important;
        border-left: 4px solid #00ffad;
        padding-left: 12px;
        margin-top: 35px !important;
    }
    h3 {
        font-size: 1.6rem !important;
        color: #ff9800 !important;
    }

    p, li {
        font-family: 'Courier New', monospace;
        color: #ccc !important;
        line-height: 1.8;
        font-size: 0.93rem;
    }
    strong { color: #00ffad; font-weight: bold; }
    ul { list-style: none; padding-left: 0; }
    ul li::before { content: "▸ "; color: #00ffad; font-weight: bold; margin-right: 8px; }
    hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00ffad, transparent); margin: 35px 0; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid #00ffad33; }
    .stTabs [data-baseweb="tab"] {
        background: #0c0e12;
        color: #555;
        border: 1px solid #1a1e26;
        border-radius: 4px 4px 0 0;
        font-family: 'VT323', monospace;
        font-size: 1rem;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .stTabs [aria-selected="true"] {
        background: #0a0c10;
        color: #00ffad !important;
        border: 1px solid #00ffad44;
        border-bottom: 2px solid #00ffad;
    }

    /* Inputs */
    .stTextInput input, .stSelectbox select {
        background: #0a0c10 !important;
        border: 1px solid #00ffad33 !important;
        color: white !important;
        font-family: 'Courier New', monospace !important;
    }
    .stButton button {
        font-family: 'VT323', monospace !important;
        font-size: 1.1rem !important;
        letter-spacing: 2px !important;
        background: #00ffad11 !important;
        border: 1px solid #00ffad !important;
        color: #00ffad !important;
        border-radius: 4px !important;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background: #00ffad22 !important;
        box-shadow: 0 0 12px #00ffad44;
    }

    /* Terminal box */
    .terminal-box {
        background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
        border: 1px solid #00ffad33;
        border-radius: 6px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 0 12px #00ffad0a;
    }
    .phase-box {
        background: #0a0c10;
        border-left: 3px solid #00ffad;
        padding: 18px;
        margin: 12px 0;
        border-radius: 0 6px 6px 0;
    }
    .risk-box {
        background: linear-gradient(135deg, #1a0f0f 0%, #261a1a 100%);
        border: 1px solid #f2364533;
        border-radius: 6px;
        padding: 18px;
        margin: 12px 0;
    }
    .highlight-quote {
        background: #00ffad0d;
        border: 1px solid #00ffad33;
        border-radius: 6px;
        padding: 18px;
        margin: 18px 0;
        font-family: 'VT323', monospace;
        font-size: 1.2rem;
        color: #00ffad;
        text-align: center;
        letter-spacing: 1px;
    }
    .metric-card {
        background: #0a0c10;
        padding: 16px;
        border-radius: 6px;
        border: 1px solid #1a1e26;
        text-align: center;
        transition: border-color 0.2s;
    }
    .metric-card:hover { border-color: #00ffad33; }
    .metric-title { color: #555; font-size: 10px; text-transform: uppercase; font-family: 'Courier New'; letter-spacing: 2px; margin-bottom: 6px; }
    .metric-value { font-family: 'VT323', monospace; font-size: 2rem; font-weight: bold; }
    .metric-sub { color: #555; font-size: 10px; margin-top: 4px; font-family: 'Courier New'; }

    /* Verdict banner */
    .verdict-badge {
        display: inline-block;
        padding: 5px 14px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 11px;
        letter-spacing: 1px;
    }
    .stExpander { border: 1px solid #1a1e26 !important; border-radius: 6px !important; }
    .stCheckbox label { font-family: 'Courier New', monospace; color: #888 !important; font-size: 0.85rem; }
    .stSpinner { color: #00ffad; }
</style>
"""

# ────────────────────────────────────────────────
# COMPONENTES UI
# ────────────────────────────────────────────────

def render_metric_card(title, value, subtitle, color):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value" style="color:{color};">{value}</div>
        <div class="metric-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def render_verdict_banner(score_data):
    grade, grade_text = score_data['grade']
    verdict, color = score_data['verdict']
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border:2px solid {color};
                border-radius:8px; padding:28px; text-align:center; margin:20px 0;
                box-shadow:0 0 25px {color}22;">
        <div style="font-family:'VT323',monospace; font-size:0.9rem; color:#555; margin-bottom:10px; letter-spacing:3px;">
            RSU SCORE // VEREDICTO DEL SISTEMA
        </div>
        <div style="display:flex; justify-content:center; align-items:center; gap:24px; margin-bottom:14px;">
            <div style="font-family:'VT323',monospace; font-size:5rem; font-weight:bold; color:{color};
                        text-shadow:0 0 20px {color}66; line-height:1;">{score_data['total']}</div>
            <div style="text-align:left;">
                <div style="font-family:'VT323',monospace; font-size:2rem; color:{color};">{grade}</div>
                <div style="font-family:'Courier New'; font-size:11px; color:#888; letter-spacing:2px;">{grade_text}</div>
            </div>
        </div>
        <div style="font-family:'VT323',monospace; font-size:1.3rem; color:white; letter-spacing:3px;">{verdict}</div>
        <div style="margin-top:16px; display:flex; justify-content:center; gap:8px; flex-wrap:wrap;">
            <span class="verdict-badge" style="background:#00ffad11; color:#00ffad; border:1px solid #00ffad33;">Z-SCORE {score_data['z_component']}/40</span>
            <span class="verdict-badge" style="background:#2196f311; color:#2196f3; border:1px solid #2196f333;">TENDENCIA {score_data['trend_component']}/30</span>
            <span class="verdict-badge" style="background:#ff980011; color:#ff9800; border:1px solid #ff980033;">VOLUMEN {score_data['volume_component']}/20</span>
            <span class="verdict-badge" style="background:#9c27b011; color:#9c27b0; border:1px solid #9c27b033;">RSI {score_data['rsi_component']}/10</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# SECCIÓN METODOLOGÍA
# ────────────────────────────────────────────────

def render_explanation_section():
    st.markdown("""
    <h2>01 // TENSIÓN ELÁSTICA — Z-SCORE (40 PTS)</h2>
    <div class="terminal-box">
        <p>La EMA actúa como una <strong>liga elástica</strong>. El Z-Score mide cuántas desviaciones estándar
        se ha alejado el precio de esa media. Valores entre <strong>-1σ y +1σ</strong> indican zona de confort
        estadístico. Valores extremos (&gt;±2σ) sugieren que el precio está sobreextendido y
        probabilísticamente tenderá a revertir a la media.</p>
    </div>

    <h2>02 // ALINEACIÓN MULTI-TIMEFRAME (30 PTS)</h2>
    <div class="phase-box">
        <p>Analizamos <strong>4 timeframes simultáneamente</strong> (15m, 1H, 4H, 1D) usando cruces de EMA.
        Cuando 3 o más timeframes están alineados, la probabilidad de continuación aumenta significativamente.
        Evita nadar contra la corriente.</p>
    </div>

    <h2>03 // VOLUMEN COMO GASOLINA (20 PTS)</h2>
    <div class="terminal-box" style="border-color:#ff9800;">
        <p>El volumen es el <strong>combustible</strong> de los movimientos. Un rebote sin volumen es como un coche
        sin gasolina: no llegará lejos. Ratios <strong>&gt;2x</strong> sugieren participación institucional.</p>
    </div>

    <h2>04 // RSI — FILTRO DE MOMENTUM (10 PTS)</h2>
    <div class="phase-box" style="border-left-color:#9c27b0;">
        <p>El RSI evita entradas en zonas de sobrecompra (&gt;70) o sobreventa extrema (&lt;30).
        Buscamos el <strong>punto dulce entre 40-60</strong> donde el momentum tiene espacio para continuar.</p>
    </div>

    <div class="highlight-quote">
        "El edge no está en predecir. Está en operar cuando la probabilidad es favorable."
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# SECCIÓN RIESGOS
# ────────────────────────────────────────────────

def render_risks_section():
    st.markdown("""
    <div style="font-family:'VT323',monospace; font-size:0.85rem; color:#555; letter-spacing:3px; margin-bottom:15px;">
        [ADVERTENCIA // LEER ANTES DE OPERAR]
    </div>

    <h2 style="color:#f23645 !important; border-left-color:#f23645;">01 // NATURALEZA PROBABILÍSTICA</h2>
    <div class="risk-box">
        <p><strong style="color:#f23645;">ESTA HERRAMIENTA NO PREDICE EL FUTURO.</strong> Un Z-Score alto no garantiza
        reversión, solo indica que estadísticamente es más probable. El mercado puede permanecer
        irracional más tiempo del que puedes permanecer solvente.</p>
    </div>

    <h2 style="color:#f23645 !important; border-left-color:#f23645;">02 // EVENTOS DE COLA NEGRA</h2>
    <div class="risk-box">
        <p>Esta herramienta no detecta eventos impredecibles: guerras, fraudes corporativos,
        decisiones de la FED sorpresa. El análisis técnico falla catastróficamente ante
        noticias fundamentales de alto impacto.</p>
    </div>

    <h2 style="color:#f23645 !important; border-left-color:#f23645;">03 // LAG EN DATOS</h2>
    <div class="risk-box">
        <p>Los datos de yfinance tienen delay de <strong>15 min en intradía</strong>. Esta herramienta es
        para análisis, no para ejecución en tiempo real.</p>
    </div>

    <h2 style="color:#f23645 !important; border-left-color:#f23645;">04 // SOBRE-OPTIMIZACIÓN</h2>
    <div class="risk-box">
        <p>Los parámetros (EMA 9/21/50, RSI 14, lookback 20) funcionan bien en condiciones
        normales pero pueden fallar en regímenes de mercado cambiantes. No hay santo grial en el trading.</p>
    </div>

    <h2 style="color:#ff9800 !important; border-left-color:#ff9800;">▸ USO RECOMENDADO</h2>
    <div class="terminal-box" style="border-color:#ff9800;">
        <p>Usa esta herramienta como <strong>filtro de probabilidad</strong>, no como señal única.</p>
        <ul>
            <li>Análisis fundamental del activo</li>
            <li>Contexto macroeconómico (noticias, earnings)</li>
            <li>Gestión de riesgo estricta (stop losses, sizing)</li>
            <li>Diario de trading para trackear tu edge real</li>
        </ul>
    </div>

    <div class="highlight-quote" style="border-color:#f23645; color:#f23645; background:#f2364508;">
        NUNCA ARRIESGUES MÁS DEL 1-2% DE TU CAPITAL EN UNA SOLA OPERACIÓN
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# BACKTEST + ML ENGINE
# ────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def build_feature_matrix(symbol, horizon_days=5):
    """
    Descarga 2 años de datos diarios y construye features + etiquetas para ML/backtest.
    Label: 1 si el precio sube >= 1% en los próximos `horizon_days` días, else 0.
    """
    raw = download_data(symbol, '2y', '1d')
    if raw.empty or len(raw) < 100:
        return None, "Datos insuficientes para backtest (mínimo 100 días)."
    data = flatten_columns(raw).copy()

    close  = ensure_1d_series(data['Close'])
    volume = ensure_1d_series(data['Volume']) if 'Volume' in data.columns else pd.Series(1, index=close.index)
    open_  = ensure_1d_series(data['Open'])   if 'Open'  in data.columns else close

    # ── Features ──────────────────────────────────────────────
    ema9  = calculate_ema(close, 9)
    ema21 = calculate_ema(close, 21)
    ema50 = calculate_ema(close, 50)

    # Z-Score (retornos log, estacionario)
    log_ret   = np.log(close / close.shift(1))
    std20     = log_ret.rolling(20).std()
    dev_pct   = (close - ema21) / ema21
    z_score   = dev_pct / std20.replace(0, np.nan)

    # RSI Wilder
    rsi = calculate_rsi(close, 14)

    # Momentum
    ret_1d  = close.pct_change(1)
    ret_5d  = close.pct_change(5)
    ret_20d = close.pct_change(20)

    # EMA slopes (velocidad de tendencia)
    ema21_slope = ema21.pct_change(3)
    ema50_slope = ema50.pct_change(5)

    # Cruce EMA rápida/lenta (señal binaria)
    ema_cross = (ema9 > ema21).astype(int)

    # Volumen relativo y direccional
    vol_avg20 = volume.rolling(20).mean()
    vol_ratio = volume / vol_avg20.replace(0, 1)
    bull_vol  = volume.where(close >= open_, 0)
    bear_vol  = volume.where(close < open_,  0)
    vol_dir   = (bull_vol.rolling(10).sum() /
                 (bull_vol.rolling(10).sum() + bear_vol.rolling(10).sum() + 1e-9))

    # Volatilidad
    atr = (close.rolling(14).std() / close)

    # ── Feature DataFrame ──────────────────────────────────────
    feat = pd.DataFrame({
        'z_score':      z_score,
        'rsi':          rsi,
        'ret_1d':       ret_1d,
        'ret_5d':       ret_5d,
        'ret_20d':      ret_20d,
        'ema21_slope':  ema21_slope,
        'ema50_slope':  ema50_slope,
        'ema_cross':    ema_cross,
        'vol_ratio':    vol_ratio,
        'vol_dir':      vol_dir,
        'atr':          atr,
        'ema9_vs_21':   (ema9 - ema21) / ema21,
        'ema21_vs_50':  (ema21 - ema50) / ema50,
    }, index=close.index)

    # ── Label: retorno futuro > +1% en horizon_days ────────────
    future_ret = close.shift(-horizon_days) / close - 1
    feat['label']       = (future_ret > 0.01).astype(int)
    feat['future_ret']  = future_ret
    feat['close']       = close.values
    feat['date']        = close.index

    feat = feat.dropna()
    return feat, None


@st.cache_data(ttl=600, show_spinner=False)
def train_ml_model(symbol, horizon_days=5):
    """Entrena Random Forest con TimeSeriesSplit (sin data leakage) y calibra probabilidades."""
    feat_df, err = build_feature_matrix(symbol, horizon_days)
    if feat_df is None:
        return None, None, None, err

    feature_cols = ['z_score','rsi','ret_1d','ret_5d','ret_20d',
                    'ema21_slope','ema50_slope','ema_cross',
                    'vol_ratio','vol_dir','atr','ema9_vs_21','ema21_vs_50']

    X = feat_df[feature_cols].values
    y = feat_df['label'].values

    if len(X) < 80:
        return None, None, None, "Histórico demasiado corto para entrenar."

    # TimeSeriesSplit: respeta orden cronológico, sin mirar el futuro
    tscv   = TimeSeriesSplit(n_splits=5)
    scaler = StandardScaler()

    # Random Forest base
    rf_base = RandomForestClassifier(
        n_estimators=200, max_depth=6, min_samples_leaf=10,
        class_weight='balanced', random_state=42, n_jobs=-1
    )
    # Calibración isotónica para que las probabilidades sean fiables
    model = CalibratedClassifierCV(rf_base, cv=tscv, method='isotonic')

    # Entrenamos en el 80% más antiguo, evaluamos en el 20% más reciente
    split_idx  = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    model.fit(X_train_sc, y_train)
    y_prob = model.predict_proba(X_test_sc)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    try:
        auc = roc_auc_score(y_test, y_prob)
    except Exception:
        auc = 0.5

    # Importancia de features (del estimador base)
    try:
        importances = model.calibrated_classifiers_[0].estimator.feature_importances_
    except Exception:
        importances = np.zeros(len(feature_cols))

    metrics = {
        'auc':          round(auc, 3),
        'accuracy':     round((y_pred == y_test).mean(), 3),
        'win_rate_pred':round(y_pred.mean(), 3),
        'win_rate_real':round(y_test.mean(), 3),
        'n_train':      len(X_train),
        'n_test':       len(X_test),
        'feature_cols': feature_cols,
        'importances':  importances.tolist(),
    }

    # Probabilidad actual (último punto)
    X_current  = scaler.transform(X[-1:])
    prob_now   = float(model.predict_proba(X_current)[0, 1])

    return model, scaler, {'metrics': metrics, 'prob_now': prob_now,
                           'feat_df': feat_df, 'feature_cols': feature_cols,
                           'y_test': y_test, 'y_prob': y_prob,
                           'X_test_dates': feat_df.index[split_idx:]}, None


def run_backtest(feat_df, horizon_days=5, score_threshold=60):
    """
    Backtest estadístico puro (sin ML): simula entradas cuando Z-Score ≤ 1σ.
    Mide win rate, retorno promedio y distribución por Z-Score bucket.
    """
    df = feat_df.copy()

    # Buckets de Z-Score
    bins   = [-np.inf, -2, -1, 0, 1, 2, np.inf]
    labels = ['<-2σ', '-2σ/-1σ', '-1σ/0', '0/+1σ', '+1σ/+2σ', '>+2σ']
    df['z_bucket'] = pd.cut(df['z_score'], bins=bins, labels=labels)

    results = []
    for bucket in labels:
        sub = df[df['z_bucket'] == bucket]
        if len(sub) < 5:
            continue
        results.append({
            'bucket':      bucket,
            'n_trades':    len(sub),
            'win_rate':    round(sub['label'].mean() * 100, 1),
            'avg_ret_pct': round(sub['future_ret'].mean() * 100, 2),
            'med_ret_pct': round(sub['future_ret'].median() * 100, 2),
            'best_ret':    round(sub['future_ret'].max() * 100, 2),
            'worst_ret':   round(sub['future_ret'].min() * 100, 2),
        })

    # Equity curve: entrar cuando |z| <= 1 y mantener horizon_days
    signals = df[df['z_score'].abs() <= 1].copy()
    equity_dates  = list(signals.index)
    equity_rets   = list(signals['future_ret'])

    return pd.DataFrame(results), equity_dates, equity_rets


# ── Gráficos del engine ────────────────────────────────────────

def create_backtest_distribution(bt_df, horizon_days):
    fig = go.Figure()
    colors = ['#f23645','#ff6d00','#ff9800','#4caf50','#ff9800','#f23645']
    for i, row in bt_df.iterrows():
        fig.add_trace(go.Bar(
            x=[row['bucket']], y=[row['win_rate']],
            marker_color=colors[i % len(colors)],
            marker_line=dict(color='rgba(0,255,173,0.3)', width=1),
            name=row['bucket'],
            text=[f"{row['win_rate']}%<br>n={row['n_trades']}"],
            textposition='outside',
            textfont=dict(color='white', family='VT323,monospace', size=12),
            hovertemplate=(f"<b>{row['bucket']}</b><br>"
                           f"Win Rate: {row['win_rate']}%<br>"
                           f"Ret avg: {row['avg_ret_pct']}%<br>"
                           f"n trades: {row['n_trades']}<extra></extra>"),
        ))
    fig.add_hline(y=50, line_dash='dash', line_color='rgba(255,255,255,0.3)',
                  annotation_text='50% (azar)', annotation_font_color='#888',
                  annotation_font_family='Courier New')
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text=f"WIN RATE POR ZONA Z-SCORE // HORIZONTE {horizon_days}D",
                   font=dict(color='#00ffad', size=13, family='VT323,monospace')),
        xaxis=dict(color='white', gridcolor='#1a1e26', tickfont=dict(family='Courier New')),
        yaxis=dict(color='white', gridcolor='#1a1e26', range=[0, 110],
                   title='Win Rate (%)', tickfont=dict(family='Courier New')),
        showlegend=False, height=320, margin=dict(l=50, r=20, t=55, b=40)
    )
    return fig


def create_equity_curve(equity_dates, equity_rets, symbol):
    if not equity_dates:
        return go.Figure()
    cum = np.cumprod([1 + r for r in equity_rets])
    cum_pct = (cum - 1) * 100
    colors  = ['#00ffad' if r >= 0 else '#f23645' for r in equity_rets]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3], vertical_spacing=0.06,
                        subplot_titles=('EQUITY CURVE // ENTRADAS Z≤1σ', 'RETORNO POR TRADE'))
    fig.add_trace(go.Scatter(
        x=equity_dates, y=cum_pct,
        line=dict(color='#00ffad', width=2),
        fill='tozeroy', fillcolor='rgba(0,255,173,0.07)',
        name='Equity acumulado',
        hovertemplate='%{x|%Y-%m-%d}<br>Retorno acum: %{y:.1f}%<extra></extra>'
    ), row=1, col=1)
    fig.add_hline(y=0, line_color='rgba(255,255,255,0.2)', row=1, col=1)
    fig.add_trace(go.Bar(
        x=equity_dates, y=[r * 100 for r in equity_rets],
        marker_color=colors, name='Ret por trade',
        hovertemplate='%{x|%Y-%m-%d}<br>Ret: %{y:.2f}%<extra></extra>'
    ), row=2, col=1)
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=460, showlegend=False,
        margin=dict(l=50, r=30, t=60, b=40),
    )
    fig.update_annotations(font=dict(color='#00ffad', family='VT323,monospace', size=13))
    fig.update_xaxes(gridcolor='#1a1e26', color='white')
    fig.update_yaxes(gridcolor='#1a1e26', color='white')
    return fig


def create_feature_importance_chart(feature_cols, importances):
    paired = sorted(zip(importances, feature_cols), reverse=True)
    imps, names = zip(*paired)
    fig = go.Figure(go.Bar(
        x=list(imps), y=list(names), orientation='h',
        marker_color='#00d9ff',
        marker_line=dict(color='rgba(0,217,255,0.3)', width=1),
        text=[f"{v:.3f}" for v in imps], textposition='outside',
        textfont=dict(color='white', family='Courier New', size=10)
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="IMPORTANCIA DE FEATURES // RANDOM FOREST",
                   font=dict(color='#00d9ff', size=13, family='VT323,monospace')),
        xaxis=dict(color='white', gridcolor='#1a1e26', tickfont=dict(family='Courier New')),
        yaxis=dict(color='white', gridcolor='#1a1e26', tickfont=dict(family='Courier New', size=10),
                   autorange='reversed'),
        height=380, margin=dict(l=130, r=60, t=55, b=40), showlegend=False
    )
    return fig


def create_ml_calibration_chart(y_test, y_prob):
    """Reliability diagram: probabilidades predichas vs frecuencia real."""
    bins   = np.linspace(0, 1, 11)
    mids   = (bins[:-1] + bins[1:]) / 2
    freqs  = []
    counts = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (y_prob >= lo) & (y_prob < hi)
        if mask.sum() > 0:
            freqs.append(y_test[mask].mean())
            counts.append(mask.sum())
        else:
            freqs.append(None)
            counts.append(0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode='lines',
        line=dict(color='rgba(255,255,255,0.25)', dash='dash', width=1),
        name='Calibración perfecta'
    ))
    fig.add_trace(go.Scatter(
        x=list(mids), y=freqs, mode='lines+markers',
        line=dict(color='#00ffad', width=2),
        marker=dict(size=[max(4, c // 3) for c in counts], color='#00ffad',
                    symbol='circle', line=dict(color='#0a0c10', width=1)),
        name='Modelo',
        hovertemplate='Prob predicha: %{x:.2f}<br>Freq real: %{y:.2f}<extra></extra>'
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="CALIBRACIÓN // PROBABILIDAD PREDICHA vs FRECUENCIA REAL",
                   font=dict(color='#00ffad', size=13, family='VT323,monospace')),
        xaxis=dict(title='Probabilidad predicha', color='white', gridcolor='#1a1e26',
                   range=[0, 1], tickfont=dict(family='Courier New')),
        yaxis=dict(title='Frecuencia real de subida', color='white', gridcolor='#1a1e26',
                   range=[0, 1], tickfont=dict(family='Courier New')),
        height=300, margin=dict(l=60, r=20, t=55, b=50), showlegend=True,
        legend=dict(bgcolor='rgba(12,14,18,0.9)', bordercolor='rgba(0,255,173,0.2)',
                    borderwidth=1, font=dict(color='white', family='Courier New', size=10))
    )
    return fig


def create_prob_gauge(prob, horizon_days):
    color = '#00ffad' if prob >= 0.6 else '#ff9800' if prob >= 0.45 else '#f23645'
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(prob * 100, 1),
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"PROB. SUBIDA +1% // {horizon_days}D",
               'font': {'size': 13, 'color': color, 'family': 'VT323,monospace'}},
        number={'font': {'size': 36, 'color': 'white', 'family': 'VT323,monospace'}, 'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#1a1e26'},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': '#0a0c10',
            'borderwidth': 2, 'bordercolor': 'rgba(0,255,173,0.2)',
            'steps': [
                {'range': [0, 40],   'color': hex_to_rgba('#f23645', 0.12)},
                {'range': [40, 55],  'color': hex_to_rgba('#ff9800', 0.12)},
                {'range': [55, 100], 'color': hex_to_rgba('#00ffad', 0.12)},
            ],
            'threshold': {'line': {'color': 'white', 'width': 3},
                          'thickness': 0.8, 'value': round(prob * 100, 1)}
        }
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def render_backtest_ml_section():
    st.markdown("""
    <div style="font-family:'VT323',monospace; color:#555; font-size:0.85rem; letter-spacing:3px; margin-bottom:18px;">
        [MOTOR DE PROBABILIDAD HISTÓRICA // BACKTEST + ML]
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        bt_symbol = st.text_input("SÍMBOLO", value="AAPL", key="bt_symbol",
                                  help="Ticker para backtest (2 años de histórico diario)").upper().strip()
    with col2:
        horizon = st.selectbox("HORIZONTE (días)", [3, 5, 10, 20], index=1, key="bt_horizon")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("// EJECUTAR ANÁLISIS", use_container_width=True,
                            type="primary", key="bt_run_btn")

    st.markdown("""
    <div class="phase-box" style="border-left-color:#00d9ff; margin-bottom:20px;">
        <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:0.95rem; letter-spacing:2px;">
            ¿QUÉ HACE ESTA TAB?
        </div>
        <div style="font-family:'Courier New'; color:#aaa; font-size:11px; margin-top:6px; line-height:1.7;">
            ▸ <b>Backtest estadístico</b>: analiza 2 años de datos reales y mide cuál fue el win rate 
            histórico para cada zona del Z-Score.<br>
            ▸ <b>Random Forest calibrado</b>: entrena un modelo ML con 13 features técnicas usando 
            TimeSeriesSplit (sin data leakage) y estima la probabilidad de subida para HOY.<br>
            ▸ <b>Sin magia</b>: AUC > 0.55 ya es útil como filtro adicional. AUC ~0.50 = aleatorio.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if run_btn and bt_symbol:
        with st.spinner("Entrenando modelo // calculando backtest histórico..."):

            # ── Backtest estadístico ────────────────────────────────
            feat_df, err = build_feature_matrix(bt_symbol, horizon)
            if feat_df is None:
                st.error(err)
                return

            bt_df, eq_dates, eq_rets = run_backtest(feat_df, horizon)

            # ── Modelo ML ─────────────────────────────────────────
            model, scaler, ml_result, ml_err = train_ml_model(bt_symbol, horizon)
            if ml_result is None:
                st.warning(f"ML no disponible: {ml_err}")

            st.markdown("<hr>", unsafe_allow_html=True)

            # ── Sección 1: Probabilidad actual ─────────────────────
            if ml_result:
                prob   = ml_result['prob_now']
                m      = ml_result['metrics']
                prob_color = '#00ffad' if prob >= 0.6 else '#ff9800' if prob >= 0.45 else '#f23645'
                verdict_ml = ("▸ SEÑAL ALCISTA" if prob >= 0.6
                              else "▸ SEÑAL NEUTRA" if prob >= 0.45
                              else "▸ SEÑAL BAJISTA")

                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#0c0e12,#1a1e26);
                            border:2px solid {prob_color}; border-radius:8px;
                            padding:24px; text-align:center; margin-bottom:24px;
                            box-shadow:0 0 20px {prob_color}22;">
                    <div style="font-family:'VT323',monospace; color:#555; font-size:0.85rem;
                                letter-spacing:3px; margin-bottom:8px;">
                        PROBABILIDAD ML // {bt_symbol} // HORIZONTE {horizon}D
                    </div>
                    <div style="font-family:'VT323',monospace; font-size:4.5rem; color:{prob_color};
                                text-shadow:0 0 18px {prob_color}66; line-height:1;">
                        {prob*100:.1f}%
                    </div>
                    <div style="font-family:'VT323',monospace; font-size:1.2rem;
                                color:white; letter-spacing:3px; margin-top:8px;">
                        {verdict_ml}
                    </div>
                    <div style="margin-top:14px; display:flex; justify-content:center; gap:10px; flex-wrap:wrap;">
                        <span class="verdict-badge" style="background:#00d9ff11;color:#00d9ff;border:1px solid #00d9ff33;">
                            AUC {m['auc']}
                        </span>
                        <span class="verdict-badge" style="background:#00ffad11;color:#00ffad;border:1px solid #00ffad33;">
                            ACC {m['accuracy']:.0%}
                        </span>
                        <span class="verdict-badge" style="background:#ff980011;color:#ff9800;border:1px solid #ff980033;">
                            TRAIN {m['n_train']} días
                        </span>
                        <span class="verdict-badge" style="background:#9c27b011;color:#9c27b0;border:1px solid #9c27b033;">
                            TEST {m['n_test']} días
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                p1, p2 = st.columns([1, 2])
                with p1:
                    st.plotly_chart(create_prob_gauge(prob, horizon),
                                    use_container_width=True, key="prob_gauge")
                with p2:
                    st.plotly_chart(
                        create_ml_calibration_chart(
                            ml_result['y_test'], ml_result['y_prob']
                        ), use_container_width=True, key="calib_chart"
                    )

            st.markdown("<hr>", unsafe_allow_html=True)

            # ── Sección 2: Backtest por zona Z-Score ───────────────
            st.markdown("""
            <div style="font-family:'VT323',monospace; color:#00ffad; font-size:1.3rem;
                        letter-spacing:3px; margin-bottom:12px;">
                02 // BACKTEST ESTADÍSTICO // WIN RATE POR ZONA
            </div>
            """, unsafe_allow_html=True)

            st.plotly_chart(create_backtest_distribution(bt_df, horizon),
                            use_container_width=True, key="bt_dist")

            # Tabla de resultados
            display_df = bt_df.rename(columns={
                'bucket':      'Zona Z-Score',
                'n_trades':    'N Entradas',
                'win_rate':    'Win Rate %',
                'avg_ret_pct': 'Ret. Medio %',
                'med_ret_pct': 'Ret. Mediana %',
                'best_ret':    'Mejor %',
                'worst_ret':   'Peor %',
            })

            def style_row(row):
                wr = row['Win Rate %']
                color = '#00332a' if wr >= 60 else '#332200' if wr >= 50 else '#330a0a'
                return [f'background-color:{color}'] * len(row)

            st.dataframe(
                display_df.style.apply(style_row, axis=1)
                                .format({'Win Rate %': '{:.1f}', 'Ret. Medio %': '{:.2f}',
                                         'Ret. Mediana %': '{:.2f}', 'Mejor %': '{:.2f}',
                                         'Peor %': '{:.2f}'}),
                use_container_width=True, hide_index=True
            )

            st.markdown("<hr>", unsafe_allow_html=True)

            # ── Sección 3: Equity curve ────────────────────────────
            st.markdown("""
            <div style="font-family:'VT323',monospace; color:#00ffad; font-size:1.3rem;
                        letter-spacing:3px; margin-bottom:12px;">
                03 // EQUITY CURVE // ESTRATEGIA Z≤1σ
            </div>
            """, unsafe_allow_html=True)

            if eq_dates:
                total_ret   = (np.prod([1 + r for r in eq_rets]) - 1) * 100
                n_trades    = len(eq_rets)
                wr_bt       = sum(r > 0 for r in eq_rets) / n_trades * 100
                avg_ret     = np.mean(eq_rets) * 100
                max_dd_arr  = np.array(eq_rets)
                cum_arr     = np.cumprod(1 + max_dd_arr)
                roll_max    = np.maximum.accumulate(cum_arr)
                dd_arr      = (cum_arr - roll_max) / roll_max * 100
                max_dd      = dd_arr.min()

                dd1, dd2, dd3, dd4 = st.columns(4)
                dd_color = '#00ffad' if total_ret >= 0 else '#f23645'
                with dd1:
                    render_metric_card("RETORNO TOTAL", f"{total_ret:+.1f}%",
                                       f"Estrategia Z≤1σ / {horizon}d", dd_color)
                with dd2:
                    render_metric_card("WIN RATE BT", f"{wr_bt:.1f}%",
                                       f"{n_trades} entradas históricas", '#00ffad' if wr_bt >= 55 else '#ff9800')
                with dd3:
                    render_metric_card("RET. MEDIO", f"{avg_ret:+.2f}%",
                                       "Por entrada", '#00ffad' if avg_ret >= 0 else '#f23645')
                with dd4:
                    render_metric_card("MAX DRAWDOWN", f"{max_dd:.1f}%",
                                       "Peor racha histórica", '#f23645')

                st.markdown("<br>", unsafe_allow_html=True)
                st.plotly_chart(create_equity_curve(eq_dates, eq_rets, bt_symbol),
                                use_container_width=True, key="equity_curve")
            else:
                st.warning("No hay suficientes entradas Z≤1σ en el período analizado.")

            st.markdown("<hr>", unsafe_allow_html=True)

            # ── Sección 4: Feature importance ─────────────────────
            if ml_result:
                st.markdown("""
                <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.3rem;
                            letter-spacing:3px; margin-bottom:12px;">
                    04 // IMPORTANCIA DE FEATURES // RANDOM FOREST
                </div>
                """, unsafe_allow_html=True)

                m = ml_result['metrics']
                st.plotly_chart(
                    create_feature_importance_chart(m['feature_cols'], m['importances']),
                    use_container_width=True, key="feat_importance"
                )

                st.markdown(f"""
                <div class="terminal-box" style="margin-top:16px;">
                    <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1rem; letter-spacing:2px; margin-bottom:8px;">
                        INTERPRETACIÓN DEL MODELO
                    </div>
                    <div style="font-family:'Courier New'; color:#aaa; font-size:11px; line-height:1.8;">
                        ▸ <strong style="color:#00ffad;">AUC {m['auc']}</strong>: 
                        {"Modelo con poder predictivo útil (> 0.55)" if m['auc'] > 0.55 else "Cerca del azar (0.50 = aleatorio). Tomar con cautela."}
                        <br>
                        ▸ Win rate real en test: {m['win_rate_real']:.0%} — Win rate predicho: {m['win_rate_pred']:.0%}
                        <br>
                        ▸ Las features más importantes revelan qué factores el modelo considera más predictivos.
                        <br>
                        ▸ <strong style="color:#ff9800;">ADVERTENCIA</strong>: backtests pasados no garantizan resultados futuros.
                          Usa este módulo como filtro adicional, nunca como señal única.
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div style="text-align:center; margin-bottom:35px;">
        <div style="font-family:'VT323',monospace; font-size:0.95rem; color:#555; margin-bottom:8px; letter-spacing:3px;">
            [SISTEMA DE ANÁLISIS TÉCNICO // ENCRIPTADO AES-256]
        </div>
        <h1>⚡ RSU EMA EDGE</h1>
        <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.1rem; letter-spacing:4px; margin-top:8px;">
            DETECTOR DE PROBABILIDAD // MEDIDOR DE TENSIÓN ELÁSTICA
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["// ANÁLISIS", "// BACKTEST + ML", "// METODOLOGÍA", "// RIESGOS"])

    with tab1:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            symbol = st.text_input("SÍMBOLO DEL ACTIVO", value="AAPL",
                                   help="Ticker (ej: AAPL, MSFT, BTC-USD)", key="symbol_input").upper().strip()
        with col2:
            timeframe = st.selectbox("TIMEFRAME", ["15m", "1h", "4h", "1d"], index=3, key="timeframe_select")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_btn = st.button("// ANALIZAR", use_container_width=True, type="primary", key="analyze_button")

        show_debug = st.checkbox("mostrar debug de datos", value=False, key="debug_checkbox")

        if analyze_btn:
            with st.spinner("Calculando matrices de probabilidad..."):
                try:
                    tf_map = {"15m": ("5d", "15m"), "1h": ("1mo", "1h"), "4h": ("3mo", "1h"), "1d": ("1y", "1d")}
                    period, interval = tf_map.get(timeframe, ("1y", "1d"))

                    if show_debug:
                        st.write(f"Descargando: {symbol} | Periodo: {period} | Intervalo: {interval}")

                    data = download_data(symbol, period, interval)

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
                        return

                    if len(data) < 50:
                        st.error(f"Datos insuficientes ({len(data)} filas).")
                        return

                    # Cálculos
                    close  = ensure_1d_series(data['Close'])
                    ema_21 = calculate_ema(close, 21)
                    current_z = float(calculate_z_score(close, ema_21).iloc[-1])

                    trends       = get_multi_timeframe_trend(symbol)
                    vol_analysis = analyze_volume_profile(data)

                    rsi_series = calculate_rsi(close)
                    rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0

                    trend_alignment = {k: v.get('trend') for k, v in trends.items()}
                    rsu_data = calculate_rsu_score(current_z, trend_alignment, vol_analysis['volume_ratio'], rsi)

                    # Veredicto
                    render_verdict_banner(rsu_data)

                    # Métricas
                    m1, m2, m3, m4, m5 = st.columns(5)
                    with m1:
                        render_metric_card("TENSIÓN ELÁSTICA", f"{current_z:+.2f}σ", "Z-Score vs EMA21", get_z_color(current_z))
                    with m2:
                        trend_1d = trends.get('1D', {}).get('trend', 'N/A')
                        trend_color = "#00ffad" if trend_1d == "BULLISH" else "#f23645" if trend_1d == "BEARISH" else "#555"
                        render_metric_card("TENDENCIA 1D", trend_1d, "Dirección principal (ponderada)", trend_color)
                    with m3:
                        vol_color = "#00ffad" if vol_analysis['volume_ratio'] > 1.5 else "#ff9800" if vol_analysis['volume_ratio'] > 1 else "#f23645"
                        render_metric_card("VOLUMEN", f"{vol_analysis['volume_ratio']:.2f}x", "vs Promedio 20d", vol_color)
                    with m4:
                        rsi_color = "#00ffad" if 40 <= rsi <= 60 else "#ff9800" if 30 <= rsi < 40 or 60 < rsi <= 70 else "#f23645"
                        render_metric_card("RSI", f"{rsi:.1f}", "Momentum Wilder 14d", rsi_color)
                    with m5:
                        bias = vol_analysis.get('directional_bias', 'NEUTRAL')
                        bp   = vol_analysis.get('buy_pressure', 0.5)
                        bias_color = "#00ffad" if bias == 'COMPRADOR' else "#f23645" if bias == 'VENDEDOR' else "#888"
                        render_metric_card("PRESIÓN", bias, f"Compra: {bp:.0%}", bias_color)

                    st.markdown("<hr>", unsafe_allow_html=True)

                    # Gráficos principales
                    g1, g2 = st.columns([2, 1])
                    with g1:
                        st.plotly_chart(create_price_chart_with_emas(data, symbol), use_container_width=True, key="price_chart")
                    with g2:
                        st.plotly_chart(create_z_score_gauge(current_z), use_container_width=True, key="z_gauge")
                        z_interp = "▸ Precio cerca de la media." if abs(current_z) <= 0.5 else "▸ Ligera desviación." if abs(current_z) <= 1 else "▸ Precio estirado." if abs(current_z) <= 2 else "▸ Extremo estadístico."
                        st.markdown(f"""
                        <div class="phase-box" style="border-left-color:{get_z_color(current_z)}; margin-top:10px;">
                            <div style="font-family:'VT323',monospace; color:{get_z_color(current_z)}; font-size:1rem; letter-spacing:2px;">INTERPRETACIÓN</div>
                            <div style="font-family:'Courier New'; color:#aaa; font-size:11px; margin-top:4px;">{z_interp}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    g3, g4 = st.columns(2)
                    with g3:
                        st.plotly_chart(create_trend_alignment_chart(trends), use_container_width=True, key="trend_chart")
                    with g4:
                        st.plotly_chart(create_rsu_score_radar(rsu_data), use_container_width=True, key="radar_chart")

                    st.plotly_chart(create_volume_heatmap(data, vol_analysis), use_container_width=True, key="vol_chart")

                    # Detalles técnicos
                    with st.expander("// DETALLES TÉCNICOS DEL CÁLCULO", expanded=False):
                        st.subheader("Parámetros Utilizados")
                        st.json({
                            "símbolo": symbol, "timeframe_principal": timeframe,
                            "periodo_descarga": period, "intervalo": interval,
                            "filas_datos": len(data),
                            "rango_fechas": f"{data.index[0].strftime('%Y-%m-%d')} a {data.index[-1].strftime('%Y-%m-%d')}"
                        })

                        st.subheader("Cálculos por Componente")
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            st.markdown("**Z-Score (Tensión Elástica)**")
                            st.code(f"""
Precio actual: {float(close.iloc[-1]):.2f}
EMA 21:        {float(ema_21.iloc[-1]):.2f}
STD (20d):     {float(close.rolling(20).std().iloc[-1]):.2f}
Z-Score:       {current_z:.3f}
Puntos:        {rsu_data['z_component']}/40
                            """)
                            st.markdown("**RSI (Momentum)**")
                            st.code(f"""
RSI (14d):  {rsi:.2f}
Zona:       {"Neutral (40-60)" if 40 <= rsi <= 60 else "Alta (60-70)" if 60 < rsi <= 70 else "Baja (30-40)" if 30 <= rsi < 40 else "Extrema"}
Puntos:     {rsu_data['rsi_component']}/10
                            """)
                        with col_c2:
                            st.markdown("**Multi-Timeframe (Ponderado)**")
                            TF_W = {'1D': 0.45, '4H': 0.30, '1H': 0.15, '15m': 0.10}
                            for tf, info in trends.items():
                                w = TF_W.get(tf, 0.1)
                                st.write(f"▸ **{tf}** (peso {w:.0%}): {info.get('trend', 'N/A')} ({info.get('strength', 0):.3f}%)")
                            st.code(f"Ratio alcista ponderado: {rsu_data.get('trend_ratio',0):.1%}\nPuntos:   {rsu_data['trend_component']}/30")

                            st.markdown("**Volumen**")
                            st.code(f"""
Hoy:      {vol_analysis['current_volume']:,}
Avg 20d:  {vol_analysis['avg_volume']:,}
Ratio:    {vol_analysis['volume_ratio']:.2f}x
Trend:    {vol_analysis['trend_volume']}
Presión:  {vol_analysis.get('directional_bias','N/A')} ({vol_analysis.get('buy_pressure',0.5):.0%} compra)
Puntos:   {rsu_data['volume_component']}/20
                            """)

                        st.subheader("Fórmula Final")
                        st.code(f"RSU SCORE = {rsu_data['z_component']} + {rsu_data['trend_component']} + {rsu_data['volume_component']} + {rsu_data['rsi_component']} = {rsu_data['total']}/100")

                        st.info("Nota: El Z-Score v2 usa retornos logarítmicos para estacionariedad — evita que el std escale con el nivel de precio. El RSI usa suavizado de Wilder (EWM) estándar de la industria. Los timeframes 1D/4H tienen mayor peso en la tendencia que 1H/15m.")

                except Exception as e:
                    st.error(f"Error en el análisis: {str(e)}")
                    import traceback
                    with st.expander("Detalles técnicos del error"):
                        st.code(traceback.format_exc())

    with tab2:
        render_backtest_ml_section()

    with tab3:
        render_explanation_section()

    with tab4:
        render_risks_section()


