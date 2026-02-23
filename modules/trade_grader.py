# -*- coding: utf-8 -*-
"""
RSU STRATEGIC TERMINAL v2.0
Estética TZU Strategic Momentum - Dark Tactical Interface
Fuentes: Monospace | Colores: Cyan #00ffd1, Rojo #ff4757, Negro #0a0a0a
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# ────────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL DE ESTILO TZU
# ────────────────────────────────────────────────

TZU_COLORS = {
    'bg_primary': '#0a0a0a',
    'bg_secondary': '#111111',
    'bg_tertiary': '#1a1a1a',
    'accent_cyan': '#00ffd1',
    'accent_red': '#ff4757',
    'accent_orange': '#ffa502',
    'accent_purple': '#8e44ad',
    'text_primary': '#ffffff',
    'text_secondary': '#888888',
    'text_muted': '#555555',
    'border': '#222222',
    'grid': '#1a1a1a',
    'positive': '#00ffd1',
    'negative': '#ff4757',
    'warning': '#ffa502'
}

THEMES_TZU = {
    "AI_CORE": {
        "name": "AI CORE",
        "ticker": "AI",
        "symbols": ["NVDA", "AMD", "TSM", "AVGO", "ARM", "SMCI", "PLTR"],
        "color": TZU_COLORS['accent_cyan'],
        "icon": "◈",
        "type": "TECH"
    },
    "SEMICON": {
        "name": "SEMICONDUCTOR",
        "ticker": "SEM",
        "symbols": ["INTC", "MU", "LRCX", "AMAT", "KLAC", "ASML", "QCOM"],
        "color": TZU_COLORS['accent_purple'],
        "icon": "◇",
        "type": "CYCLICAL"
    },
    "ENERGY": {
        "name": "QUANTUM ENERGY",
        "ticker": "QNR",
        "symbols": ["TSLA", "ENPH", "FSLR", "NEE", "CEG", "SMR", "OKLO"],
        "color": TZU_COLORS['accent_cyan'],
        "icon": "⚡",
        "type": "GROWTH"
    },
    "DEFENSE": {
        "name": "DEFENSE SYS",
        "ticker": "DFS",
        "symbols": ["LMT", "NOC", "RTX", "GD", "BA", "RKLB", "ASTS"],
        "color": TZU_COLORS['accent_orange'],
        "icon": "◉",
        "type": "VALUE"
    },
    "BIOTECH": {
        "name": "BIO GENESIS",
        "ticker": "BIO",
        "symbols": ["LLY", "NVO", "MRK", "AMGN", "VRTX", "CRSP", "REGN"],
        "color": TZU_COLORS['accent_cyan'],
        "icon": "✦",
        "type": "SPEC"
    },
    "CRYPTO": {
        "name": "CRYPTO INFRA",
        "ticker": "CRP",
        "symbols": ["COIN", "MSTR", "RIOT", "MARA", "CLSK", "HOOD"],
        "color": TZU_COLORS['accent_orange'],
        "icon": "₿",
        "type": "VOLATILE"
    },
    "CYBER": {
        "name": "CYBER DEFENSE",
        "ticker": "CYB",
        "symbols": ["CRWD", "PANW", "FTNT", "ZS", "OKTA", "NET"],
        "color": TZU_COLORS['accent_red'],
        "icon": "◊",
        "type": "TECH"
    },
    "GOLD": {
        "name": "GOLD RESERVE",
        "ticker": "GLD",
        "symbols": ["GLD", "NEM", "GOLD", "FNV", "WPM", "RGLD"],
        "color": TZU_COLORS['accent_orange'],
        "icon": "◆",
        "type": "SAFE"
    }
}

TIMEFRAMES_TZU = {
    "TURBO": {"label": "TURBO", "period": "1d", "interval": "5m", "fast": 9, "slow": 21},
    "INTRADAY": {"label": "INTRADAY", "period": "5d", "interval": "15m", "fast": 9, "slow": 21},
    "SWING": {"label": "SWING", "period": "1mo", "interval": "1h", "fast": 20, "slow": 50},
    "POSITION": {"label": "POSITION", "period": "3mo", "interval": "1d", "fast": 20, "slow": 50},
    "MACRO": {"label": "MACRO", "period": "1y", "interval": "1d", "fast": 50, "slow": 200}
}

# ────────────────────────────────────────────────
# FUNCIONES DE DATOS REALES
# ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_market_data(symbol, period, interval):
    """Fetch datos reales con manejo de errores TZU"""
    try:
        data = yf.download(symbol, period=period, interval=interval, 
                          progress=False, auto_adjust=True, timeout=10)
        if not data.empty and len(data) > 20:
            return data
        return None
    except:
        return None

def flatten_cols(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def calculate_tech_indicators(data, fast, slow):
    """Calcula indicadores técnicos estilo TZU"""
    data = flatten_cols(data)
    close = data['Close'].squeeze()
    
    # EMAs
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    sma_20 = close.rolling(window=20).mean()
    std_20 = close.rolling(window=20).std()
    upper_band = sma_20 + (std_20 * 2)
    lower_band = sma_20 - (std_20 * 2)
    
    # ATR (volatilidad)
    high = data['High'].squeeze()
    low = data['Low'].squeeze()
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    
    return {
        'close': close,
        'ema_fast': ema_fast,
        'ema_slow': ema_slow,
        'rsi': rsi,
        'upper_band': upper_band,
        'lower_band': lower_band,
        'atr': atr,
        'sma_20': sma_20
    }

def analyze_symbol_tzu(symbol, tf_config):
    """Análisis completo estilo TZU Strategic Momentum"""
    data = fetch_market_data(symbol, tf_config['period'], tf_config['interval'])
    if data is None:
        return None
    
    try:
        ind = calculate_tech_indicators(data, tf_config['fast'], tf_config['slow'])
        
        last_close = float(ind['close'].iloc[-1])
        prev_close = float(ind['close'].iloc[-2])
        change_pct = ((last_close - prev_close) / prev_close) * 100
        
        # Señales
        ema_bull = ind['ema_fast'].iloc[-1] > ind['ema_slow'].iloc[-1]
        price_above_ema = last_close > ind['ema_fast'].iloc[-1]
        rsi_val = float(ind['rsi'].iloc[-1])
        
        if rsi_val > 70:
            regime = "OVERBOUGHT"
            regime_color = TZU_COLORS['accent_red']
        elif rsi_val < 30:
            regime = "OVERSOLD"
            regime_color = TZU_COLORS['accent_cyan']
        else:
            regime = "NEUTRAL"
            regime_color = TZU_COLORS['text_secondary']
        
        # Score 0-100
        score = 0
        if ema_bull: score += 30
        if price_above_ema: score += 20
        if 40 < rsi_val < 60: score += 20
        elif 30 < rsi_val < 70: score += 10
        
        # Tendencia
        if score >= 60:
            signal = "LONG"
            signal_color = TZU_COLORS['accent_cyan']
        elif score <= 30:
            signal = "SHORT"
            signal_color = TZU_COLORS['accent_red']
        else:
            signal = "NEUTRAL"
            signal_color = TZU_COLORS['text_secondary']
        
        return {
            'symbol': symbol,
            'price': last_close,
            'change': change_pct,
            'signal': signal,
            'signal_color': signal_color,
            'score': score,
            'regime': regime,
            'regime_color': regime_color,
            'rsi': rsi_val,
            'ema_fast': float(ind['ema_fast'].iloc[-1]),
            'ema_slow': float(ind['ema_slow'].iloc[-1]),
            'atr': float(ind['atr'].iloc[-1]),
            'trend': "BULL" if ema_bull else "BEAR",
            'data': data,
            'indicators': ind
        }
    except:
        return None

# ────────────────────────────────────────────────
# COMPONENTES UI TZU STYLE
# ────────────────────────────────────────────────

def tzu_header():
    """Header estilo TZU Strategic Momentum"""
    st.markdown(f"""
    <div style="background: {TZU_COLORS['bg_secondary']}; 
                border-bottom: 1px solid {TZU_COLORS['border']};
                padding: 15px 25px;
                margin: -1rem -1rem 2rem -1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="font-family: monospace; font-size: 24px; font-weight: bold; 
                        color: {TZU_COLORS['accent_cyan']}; letter-spacing: 2px;">
                TZU
            </div>
            <div style="width: 1px; height: 30px; background: {TZU_COLORS['border']};"></div>
            <div style="font-family: monospace; font-size: 11px; color: {TZU_COLORS['text_secondary']}; 
                        text-transform: uppercase; letter-spacing: 1px;">
                Strategic Momentum<br>
                <span style="color: {TZU_COLORS['accent_cyan']};">● SYSTEM ACTIVE</span>
            </div>
        </div>
        <div style="font-family: monospace; font-size: 11px; color: {TZU_COLORS['text_muted']}; text-align: right;">
            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC<br>
            MARKET STATUS: <span style="color: {TZU_COLORS['accent_cyan']};">OPERATIONAL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def tzu_panel(title, subtitle="", accent=TZU_COLORS['accent_cyan']):
    """Panel container estilo TZU"""
    st.markdown(f"""
    <div style="background: {TZU_COLORS['bg_secondary']}; 
                border: 1px solid {TZU_COLORS['border']};
                border-left: 3px solid {accent};
                border-radius: 0 8px 8px 0;
                margin-bottom: 15px;">
        <div style="padding: 12px 15px; border-bottom: 1px solid {TZU_COLORS['border']};">
            <div style="font-family: monospace; font-size: 13px; font-weight: bold; 
                        color: {TZU_COLORS['text_primary']}; letter-spacing: 1px;">
                {title}
            </div>
            {f'<div style="font-family: monospace; font-size: 10px; color: {TZU_COLORS["text_muted"]}; margin-top: 2px;">{subtitle}</div>' if subtitle else ''}
        </div>
        <div style="padding: 15px;">
    """, unsafe_allow_html=True)

def tzu_panel_end():
    st.markdown("</div></div>", unsafe_allow_html=True)

def tzu_metric(label, value, delta=None, unit="", color=None):
    """Métrica estilo TZU terminal"""
    if color is None:
        color = TZU_COLORS['accent_cyan'] if (delta is None or delta >= 0) else TZU_COLORS['accent_red']
    
    delta_html = ""
    if delta is not None:
        delta_color = TZU_COLORS['accent_cyan'] if delta >= 0 else TZU_COLORS['accent_red']
        delta_sign = "+" if delta >= 0 else ""
        delta_html = f'<div style="font-family: monospace; font-size: 11px; color: {delta_color}; margin-top: 4px;">{delta_sign}{delta:.2f}{unit}</div>'
    
    st.markdown(f"""
    <div style="text-align: center;">
        <div style="font-family: monospace; font-size: 9px; color: {TZU_COLORS['text_muted']}; 
                    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">
            {label}
        </div>
        <div style="font-family: monospace; font-size: 22px; font-weight: bold; color: {color};">
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def tzu_signal_badge(signal, color):
    """Badge de señal estilo TZU"""
    st.markdown(f"""
    <div style="display: inline-block; background: {color}22; 
                border: 1px solid {color}66; color: {color};
                font-family: monospace; font-size: 11px; font-weight: bold;
                padding: 4px 12px; border-radius: 4px; letter-spacing: 1px;">
        {signal}
    </div>
    """, unsafe_allow_html=True)

def tzu_progress_bar(value, max_val=100, color=TZU_COLORS['accent_cyan']):
    """Barra de progreso estilo TZU"""
    pct = min((value / max_val) * 100, 100)
    st.markdown(f"""
    <div style="background: {TZU_COLORS['bg_tertiary']}; height: 6px; border-radius: 3px; overflow: hidden;">
        <div style="background: {color}; width: {pct}%; height: 100%; 
                    box-shadow: 0 0 10px {color}66; transition: width 0.3s ease;">
        </div>
    </div>
    <div style="font-family: monospace; font-size: 9px; color: {TZU_COLORS['text_muted']}; 
                text-align: right; margin-top: 3px;">
        {value:.0f}/{max_val}
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# VISUALIZACIONES TZU STYLE
# ────────────────────────────────────────────────

def create_tzu_chart(data, ind, symbol, theme_color):
    """Gráfico de velas estilo TZU dark"""
    data = flatten_cols(data)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'].squeeze(),
        high=data['High'].squeeze(),
        low=data['Low'].squeeze(),
        close=data['Close'].squeeze(),
        increasing_line_color=TZU_COLORS['accent_cyan'],
        decreasing_line_color=TZU_COLORS['accent_red'],
        increasing_fillcolor=TZU_COLORS['accent_cyan'],
        decreasing_fillcolor=TZU_COLORS['accent_red'],
        line=dict(width=1),
        name=symbol
    ), row=1, col=1)
    
    # EMAs
    fig.add_trace(go.Scatter(x=data.index, y=ind['ema_fast'], 
                            line=dict(color=TZU_COLORS['accent_cyan'], width=1.5),
                            name=f"EMA{9}"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=ind['ema_slow'], 
                            line=dict(color=TZU_COLORS['accent_orange'], width=1.5),
                            name=f"EMA{21}"), row=1, col=1)
    
    # Bollinger Bands
    fig.add_trace(go.Scatter(x=data.index, y=ind['upper_band'], 
                            line=dict(color=TZU_COLORS['text_muted'], width=1, dash='dash'),
                            name="Upper BB", opacity=0.5), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=ind['lower_band'], 
                            line=dict(color=TZU_COLORS['text_muted'], width=1, dash='dash'),
                            name="Lower BB", opacity=0.5), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=data.index, y=ind['rsi'], 
                            line=dict(color=TZU_COLORS['accent_cyan'], width=1.5),
                            name="RSI"), row=2, col=1)
    
    # Líneas RSI referencia
    fig.add_hline(y=70, line_dash="dash", line_color=TZU_COLORS['accent_red'], 
                  opacity=0.5, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=TZU_COLORS['accent_cyan'], 
                  opacity=0.5, row=2, col=1)
    
    fig.update_layout(
        paper_bgcolor=TZU_COLORS['bg_secondary'],
        plot_bgcolor=TZU_COLORS['bg_primary'],
        font=dict(family="monospace", color=TZU_COLORS['text_secondary']),
        xaxis_rangeslider_visible=False,
        height=400,
        margin=dict(l=50, r=50, t=30, b=30),
        showlegend=False,
        xaxis=dict(gridcolor=TZU_COLORS['grid'], showgrid=True),
        yaxis=dict(gridcolor=TZU_COLORS['grid'], showgrid=True),
        xaxis2=dict(gridcolor=TZU_COLORS['grid']),
        yaxis2=dict(gridcolor=TZU_COLORS['grid'], range=[0, 100])
    )
    
    return fig

def create_tzu_heatmap(themes_data):
    """Heatmap de fuerza sectorial estilo TZU"""
    sectors = []
    scores = []
    colors = []
    
    for theme_key, data in themes_data.items():
        if data and len(data) > 0:
            avg_score = np.mean([d['score'] for d in data if d])
            sectors.append(THEMES_TZU[theme_key]['ticker'])
            scores.append(avg_score)
            
            if avg_score >= 60:
                colors.append(TZU_COLORS['accent_cyan'])
            elif avg_score >= 40:
                colors.append(TZU_COLORS['accent_orange'])
            else:
                colors.append(TZU_COLORS['accent_red'])
    
    fig = go.Figure(data=[go.Bar(
        x=scores,
        y=sectors,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color=TZU_COLORS['text_secondary'], width=1)
        ),
        text=[f"{s:.0f}" for s in scores],
        textposition="outside",
        textfont=dict(family="monospace", color=TZU_COLORS['text_primary'], size=11)
    )])
    
    fig.update_layout(
        paper_bgcolor=TZU_COLORS['bg_secondary'],
        plot_bgcolor=TZU_COLORS['bg_primary'],
        font=dict(family="monospace", color=TZU_COLORS['text_secondary']),
        height=300,
        margin=dict(l=80, r=50, t=30, b=30),
        xaxis=dict(gridcolor=TZU_COLORS['grid'], range=[0, 100], title="STRENGTH SCORE"),
        yaxis=dict(gridcolor=TZU_COLORS['grid']),
        showlegend=False
    )
    
    return fig

# ────────────────────────────────────────────────
# RENDER PRINCIPAL TZU TERMINAL
# ────────────────────────────────────────────────

def render_tzu_terminal():
    """Render completo del terminal TZU"""
    
    # CSS Global TZU
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {TZU_COLORS['bg_primary']};
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0;
            background: {TZU_COLORS['bg_secondary']};
            border-bottom: 1px solid {TZU_COLORS['border']};
        }}
        .stTabs [data-baseweb="tab"] {{
            background: transparent;
            color: {TZU_COLORS['text_muted']};
            border: none;
            border-bottom: 2px solid transparent;
            border-radius: 0;
            padding: 12px 24px;
            font-family: monospace;
            font-size: 11px;
            letter-spacing: 1px;
        }}
        .stTabs [aria-selected="true"] {{
            color: {TZU_COLORS['accent_cyan']};
            border-bottom-color: {TZU_COLORS['accent_cyan']};
            background: {TZU_COLORS['bg_tertiary']};
        }}
        div[data-testid="stButton"] > button {{
            background: {TZU_COLORS['bg_secondary']};
            border: 1px solid {TZU_COLORS['border']};
            color: {TZU_COLORS['text_secondary']};
            font-family: monospace;
            font-size: 11px;
            letter-spacing: 1px;
            text-transform: uppercase;
            border-radius: 4px;
            padding: 8px 16px;
        }}
        div[data-testid="stButton"] > button:hover {{
            border-color: {TZU_COLORS['accent_cyan']};
            color: {TZU_COLORS['accent_cyan']};
            box-shadow: 0 0 15px {TZU_COLORS['accent_cyan']}33;
        }}
        div[data-testid="stMetricValue"] {{
            font-family: monospace;
            color: {TZU_COLORS['accent_cyan']};
        }}
        .stDataFrame {{
            font-family: monospace;
            font-size: 11px;
        }}
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: {TZU_COLORS['bg_primary']};
        }}
        ::-webkit-scrollbar-thumb {{
            background: {TZU_COLORS['border']};
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {TZU_COLORS['accent_cyan']};
        }}
    </style>
    """, unsafe_allow_html=True)
    
    tzu_header()
    
    # Control Panel Superior
    st.markdown(f"""
    <div style="background: {TZU_COLORS['bg_secondary']}; 
                border: 1px solid {TZU_COLORS['border']};
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown(f'<div style="font-family: monospace; font-size: 10px; color: {TZU_COLORS["text_muted"]}; margin-bottom: 5px;">TIMEFRAME SELECTOR</div>', unsafe_allow_html=True)
        tf_selected = st.selectbox("", list(TIMEFRAMES_TZU.keys()), 
                                   format_func=lambda x: f"◈ {TIMEFRAMES_TZU[x]['label']}",
                                   label_visibility="collapsed")
    
    with col2:
        st.markdown(f'<div style="font-family: monospace; font-size: 10px; color: {TZU_COLORS["text_muted"]}; margin-bottom: 5px;">SYSTEM MODE</div>', unsafe_allow_html=True)
        mode = st.selectbox("", ["LIVE DATA", "SIMULATION"], label_visibility="collapsed")
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("◉ EXECUTE SCAN", use_container_width=True):
            st.session_state.scan_triggered = True
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    tf_config = TIMEFRAMES_TZU[tf_selected]
    
    # Si no hay scan, mostrar estado standby
    if not st.session_state.get('scan_triggered'):
        st.markdown(f"""
        <div style="text-align: center; padding: 100px 0; opacity: 0.5;">
            <div style="font-family: monospace; font-size: 48px; color: {TZU_COLORS['accent_cyan']}; margin-bottom: 20px;">
                ◈
            </div>
            <div style="font-family: monospace; font-size: 14px; color: {TZU_COLORS['text_secondary']}; letter-spacing: 2px;">
                SYSTEM STANDBY
            </div>
            <div style="font-family: monospace; font-size: 11px; color: {TZU_COLORS['text_muted']}; margin-top: 10px;">
                SELECT TIMEFRAME AND EXECUTE SCAN TO INITIALIZE
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Ejecutar Scan
    with st.spinner(""):
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        all_results = {}
        total_symbols = sum(len(t["symbols"]) for t in THEMES_TZU.values())
        processed = 0
        
        for theme_key, theme in THEMES_TZU.items():
            progress_text.markdown(f"""
            <div style="font-family: monospace; font-size: 11px; color: {TZU_COLORS['accent_cyan']};">
                > SCANNING SECTOR: {theme['ticker']} // {theme['name'].upper()}
            </div>
            """, unsafe_allow_html=True)
            
            theme_results = []
            for symbol in theme["symbols"]:
                result = analyze_symbol_tzu(symbol, tf_config)
                if result:
                    theme_results.append(result)
                processed += 1
                progress_bar.progress(processed / total_symbols)
                time.sleep(0.05)
            
            all_results[theme_key] = theme_results
        
        progress_text.empty()
        progress_bar.empty()
    
    # Dashboard Principal - Grid Layout
    st.markdown(f"""
    <div style="font-family: monospace; font-size: 10px; color: {TZU_COLORS['accent_cyan']}; 
                margin-bottom: 15px; letter-spacing: 1px;">
        > SCAN COMPLETE :: {datetime.now().strftime('%H:%M:%S')} :: {tf_config['label']} MODE
    </div>
    """, unsafe_allow_html=True)
    
    # Fila 1: Market Overview
    st.markdown("### MARKET BREADTH")
    cols_overview = st.columns(4)
    
    total_symbols = sum(len(r) for r in all_results.values())
    long_signals = sum(len([x for x in r if x['signal'] == 'LONG']) for r in all_results.values())
    short_signals = sum(len([x for x in r if x['signal'] == 'SHORT']) for r in all_results.values())
    avg_score = np.mean([x['score'] for r in all_results.values() for x in r]) if total_symbols > 0 else 0
    
    with cols_overview[0]:
        tzu_panel("ACTIVE ASSETS", f"TOTAL MONITORED")
        tzu_metric("COUNT", f"{total_symbols}", unit="")
        tzu_panel_end()
    
    with cols_overview[1]:
        tzu_panel("LONG EXPOSURE", f"BULLISH SIGNALS", TZU_COLORS['accent_cyan'])
        tzu_metric("POSITIONS", f"{long_signals}", delta=(long_signals/total_symbols*100 if total_symbols else 0), unit="%", color=TZU_COLORS['accent_cyan'])
        tzu_panel_end()
    
    with cols_overview[2]:
        tzu_panel("SHORT EXPOSURE", f"BEARISH SIGNALS", TZU_COLORS['accent_red'])
        tzu_metric("POSITIONS", f"{short_signals}", delta=-(short_signals/total_symbols*100 if total_symbols else 0), unit="%", color=TZU_COLORS['accent_red'])
        tzu_panel_end()
    
    with cols_overview[3]:
        tzu_panel("SYSTEM SCORE", f"AGGREGATE STRENGTH", TZU_COLORS['accent_orange'])
        tzu_metric("AVG", f"{avg_score:.0f}", unit="/100", color=TZU_COLORS['accent_orange'])
        tzu_progress_bar(avg_score, 100, TZU_COLORS['accent_orange'])
        tzu_panel_end()
    
    # Fila 2: Heatmap y Top Movers
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        tzu_panel("SECTORIAL HEATMAP", "STRENGTH BY THEME")
        st.plotly_chart(create_tzu_heatmap(all_results), use_container_width=True, key="heatmap")
        tzu_panel_end()
    
    with col_right:
        tzu_panel("TOP MOMENTUM", "HIGHEST SCORE ASSETS")
        
        all_assets = [x for r in all_results.values() for x in r]
        top_assets = sorted(all_assets, key=lambda x: x['score'], reverse=True)[:5]
        
        for asset in top_assets:
            trend_color = TZU_COLORS['accent_cyan'] if asset['trend'] == 'BULL' else TZU_COLORS['accent_red']
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center;
                        background: {TZU_COLORS['bg_primary']};
                        border-left: 2px solid {trend_color};
                        padding: 10px;
                        margin-bottom: 8px;
                        font-family: monospace;">
                <div>
                    <span style="color: {TZU_COLORS['text_primary']}; font-weight: bold;">{asset['symbol']}</span>
                    <span style="color: {TZU_COLORS['text_muted']}; font-size: 10px; margin-left: 10px;">
                        {asset['regime']}
                    </span>
                </div>
                <div style="text-align: right;">
                    <div style="color: {TZU_COLORS['accent_cyan'] if asset['change'] >= 0 else TZU_COLORS['accent_red']}; 
                                font-size: 12px; font-weight: bold;">
                        {asset['change']:+.2f}%
                    </div>
                    <div style="color: {TZU_COLORS['text_muted']}; font-size: 9px;">
                        SCORE: {asset['score']}/100
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        tzu_panel_end()
    
    # Fila 3: Detalle por Sector (Tabs)
    st.markdown("---")
    st.markdown("### SECTOR DETAIL // TECHNICAL ANALYSIS")
    
    tabs = st.tabs([f"◈ {t['ticker']}" for t in THEMES_TZU.values()])
    
    for i, (theme_key, theme) in enumerate(THEMES_TZU.items()):
        with tabs[i]:
            results = all_results.get(theme_key, [])
            if not results:
                st.warning("NO DATA AVAILABLE")
                continue
            
            # Grid de métricas del sector
            metric_cols = st.columns(len(results))
            
            for j, asset in enumerate(results):
                with metric_cols[j]:
                    signal_color = asset['signal_color']
                    
                    st.markdown(f"""
                    <div style="background: {TZU_COLORS['bg_secondary']};
                                border: 1px solid {TZU_COLORS['border']};
                                border-top: 3px solid {signal_color};
                                padding: 15px;
                                text-align: center;">
                        <div style="font-family: monospace; font-size: 16px; font-weight: bold; 
                                    color: {TZU_COLORS['text_primary']}; margin-bottom: 5px;">
                            {asset['symbol']}
                        </div>
                        <div style="font-family: monospace; font-size: 20px; font-weight: bold; 
                                    color: {signal_color}; margin: 10px 0;">
                            ${asset['price']:.2f}
                        </div>
                        <div style="font-family: monospace; font-size: 11px; 
                                    color: {TZU_COLORS['accent_cyan'] if asset['change'] >= 0 else TZU_COLORS['accent_red']};">
                            {asset['change']:+.2f}%
                        </div>
                        <div style="margin-top: 10px;">
                            <span style="background: {signal_color}22; color: {signal_color};
                                        font-family: monospace; font-size: 10px; padding: 2px 8px;
                                        border-radius: 2px; border: 1px solid {signal_color}44;">
                                {asset['signal']}
                            </span>
                        </div>
                        <div style="font-family: monospace; font-size: 9px; color: {TZU_COLORS['text_muted']}; 
                                    margin-top: 8px;">
                            RSI: {asset['rsi']:.1f} | ATR: {asset['atr']:.2f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Gráfico del líder del sector
            leader = max(results, key=lambda x: x['score'])
            st.markdown(f"""
            <div style="font-family: monospace; font-size: 10px; color: {TZU_COLORS['text_muted']}; 
                        margin: 20px 0 10px 0;">
                > CHART ANALYSIS: {leader['symbol']} | SIGNAL: {leader['signal']} | SCORE: {leader['score']}/100
            </div>
            """, unsafe_allow_html=True)
            
            fig = create_tzu_chart(leader['data'], leader['indicators'], leader['symbol'], theme['color'])
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{theme_key}")
    
    # Footer TZU
    st.markdown(f"""
    <div style="border-top: 1px solid {TZU_COLORS['border']}; margin-top: 40px; padding-top: 20px;
                font-family: monospace; font-size: 9px; color: {TZU_COLORS['text_muted']};
                display: flex; justify-content: space-between;">
        <div>
            TZU STRATEGIC TERMINAL v2.0 | RSU MODULE<br>
            DATA SOURCE: YAHOO FINANCE | DELAY: 15MIN
        </div>
        <div style="text-align: right;">
            MEMORY USAGE: OPTIMAL<br>
            LAST SYNC: {datetime.now().strftime('%H:%M:%S')} UTC
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    if 'scan_triggered' not in st.session_state:
        st.session_state.scan_triggered = False
    render()


