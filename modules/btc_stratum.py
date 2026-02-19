# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# ═══════════════════════════════════════════════════════════════════════════════
# RSU BITCOIN ACCUMULATION MODEL v2.0
# Basado en: 200W MA + MVRV Z-Score + Puell Multiple + AHR999 + Macro Conditions
# ═══════════════════════════════════════════════════════════════════════════════

# Solo configurar página si se ejecuta standalone (no como módulo importado)
if __name__ == "__main__":
    st.set_page_config(
        page_title="RSU | Bitcoin Accumulation Model",
        page_icon="₿",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

# ───────────────────────────────────────────────────────────────────────────────
# PALETA DE COLORES RSU TERMINAL
# ───────────────────────────────────────────────────────────────────────────────

COLORS = {
    'bg_dark': '#050505',
    'bg_panel': '#0a0a0a',
    'grid': '#1a1a1a',
    'text': '#e0e0e0',
    'text_dim': '#666666',
    'accent_green': '#00ff41',      # Matrix green
    'accent_cyan': '#00d4ff',       # Cyberpunk cyan
    'accent_red': '#ff003c',        # Alert red
    'accent_orange': '#ff9f1c',     # Warning orange
    'accent_yellow': '#ffd60a',     # Caution yellow
    'accent_purple': '#9d4edd',     # Deep purple
    'zone_max': '#006b1b',          # Maximum opportunity - deep green
    'zone_agg': '#009627',          # Aggressive buy
    'zone_strong': '#28a745',       # Strong buy
    'zone_good': '#78a832',         # Good buy
    'zone_dca': '#aa8c28',          # DCA zone
    'zone_light': '#aa5028',        # Light buy
    'zone_wait': '#666666',         # Wait zone
    'rsu_extreme': '#00ff00',       # RSU Score < 20
    'rsu_strong': '#00ff88',        # RSU Score 20-40
    'rsu_moderate': '#ffff00',      # RSU Score 40-60
    'rsu_weak': '#ff8800',          # RSU Score 60-80
    'rsu_poor': '#ff0044'           # RSU Score > 80
}

# ───────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ───────────────────────────────────────────────────────────────────────────────

def hex_to_rgba(hex_color, alpha=1.0):
    """Convierte hex a rgba para Plotly"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

def flatten_columns(df):
    """Aplana columnas MultiIndex de yfinance"""
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

# ───────────────────────────────────────────────────────────────────────────────
# CÁLCULOS DE INDICADORES ON-CHAIN Y MACRO
# ───────────────────────────────────────────────────────────────────────────────

def calculate_200w_ma(data):
    """Calcula la Media Móvil de 200 Semanas"""
    close = ensure_1d_series(data['Close'])
    return close.rolling(window=1400, min_periods=100).mean()

def calculate_mvrv_z_score(data, market_cap_data=None):
    """
    Calcula MVRV Z-Score simplificado basado en desviación del precio vs MA200W
    En producción, esto debería conectarse a datos reales de market cap realizados
    """
    close = ensure_1d_series(data['Close'])
    ma200 = calculate_200w_ma(data)
    
    # Simulación: MVRV correlaciona fuertemente con desviación de la media móvil larga
    # Valores típicos: <-1.5 = sobreventa extrema, >3.5 = sobrecompra extrema
    deviation = (close - ma200) / ma200
    
    # Aproximación del Z-score basada en desviación histórica
    mvrv_z = deviation * 3.5  # Factor de escala empírico
    
    return mvrv_z

def calculate_puell_multiple(data):
    """
    Calcula Puell Multiple simplificado basado en momentum de emisión
    En producción: requiere datos de minería y emisión diaria
    """
    close = ensure_1d_series(data['Close'])
    
    # SMA de 365 días como proxy de "costo de producción" promedio
    sma_365 = close.rolling(window=365).mean()
    
    # Puell = Precio actual / Media móvil de emisión (aproximada por SMA365)
    puell = close / sma_365
    
    # Normalizar a escala típica (0.5 = bottom, 4.0 = top)
    return puell

def calculate_ahr999(data):
    """
    Calcula índice AHR999 simplificado
    Fórmula original: (Precio / 200DMA) / log(200DMA)
    """
    close = ensure_1d_series(data['Close'])
    ma200 = calculate_200w_ma(data)
    
    # Evitar división por cero
    ma200_safe = ma200.replace(0, np.nan)
    
    ahr999 = (close / ma200_safe) / np.log(ma200_safe)
    
    return ahr999

def get_macro_conditions():
    """
    Obtiene condiciones macroeconómicas relevantes
    En producción: conectar a APIs de FRED, Yahoo Finance para DXY
    """
    try:
        # DXY (Dollar Index) - proxy de liquidez global inversa
        dxy = yf.download("DX-Y.NYB", period="1y", interval="1d", progress=False, auto_adjust=True)
        dxy = flatten_columns(dxy)
        dxy_current = float(ensure_1d_series(dxy['Close']).iloc[-1])
        dxy_ma50 = ensure_1d_series(dxy['Close']).rolling(50).mean().iloc[-1]
        
        # Tendencia DXY: >50MA = restrictivo (malo para BTC), <50MA = expansivo (bueno)
        dxy_score = 50 if pd.isna(dxy_ma50) else (50 - ((dxy_current / dxy_ma50 - 1) * 500))
        dxy_score = max(0, min(100, dxy_score))  # Clamp 0-100
        
        # FED Funds Rate proxy usando datos de mercado (TLT inverso)
        tlt = yf.download("TLT", period="1y", interval="1d", progress=False, auto_adjust=True)
        tlt = flatten_columns(tlt)
        tlt_yield = 20 - (float(ensure_1d_series(tlt['Close']).iloc[-1]) / 10)  # Aproximación
        
        # Score de liquidez: 100 = muy expansiva, 0 = muy restrictiva
        liquidity_score = max(0, min(100, 100 - (tlt_yield * 10)))
        
        return {
            'dxy': dxy_current,
            'dxy_score': dxy_score,
            'liquidity_score': liquidity_score,
            'fed_proxy': tlt_yield,
            'status': 'EXPANSIVO' if liquidity_score > 60 else 'NEUTRAL' if liquidity_score > 40 else 'RESTRICTIVO'
        }
    except:
        return {
            'dxy': 103.0,
            'dxy_score': 50,
            'liquidity_score': 50,
            'fed_proxy': 5.0,
            'status': 'NEUTRAL (Datos no disponibles)'
        }

def get_halving_cycle():
    """
    Calcula la posición en el ciclo de halving de Bitcoin
    Halvings: 2012-11-28, 2016-07-09, 2020-05-11, 2024-04-19 (próximo ~2028)
    """
    halving_dates = [
        datetime(2012, 11, 28),
        datetime(2016, 7, 9),
        datetime(2020, 5, 11),
        datetime(2024, 4, 19)
    ]
    
    now = datetime.now()
    last_halving = max([h for h in halving_dates if h <= now])
    next_halving = datetime(2028, 4, 1)  # Estimado
    
    days_since = (now - last_halving).days
    days_total = (next_halving - last_halving).days
    progress = days_since / days_total
    
    # Fases del ciclo: Acumulación (0-20%), Bull Early (20-40%), Bull Late (40-60%), 
    # Distribución (60-80%), Bear (80-100%)
    if progress < 0.2:
        phase = "ACUMULACIÓN"
        phase_color = COLORS['zone_max']
    elif progress < 0.4:
        phase = "BULL TEMPRANO"
        phase_color = COLORS['zone_strong']
    elif progress < 0.6:
        phase = "BULL AVANZADO"
        phase_color = COLORS['zone_good']
    elif progress < 0.8:
        phase = "DISTRIBUCIÓN"
        phase_color = COLORS['zone_dca']
    else:
        phase = "MERADO BAJISTA"
        phase_color = COLORS['zone_light']
    
    return {
        'days_since': days_since,
        'days_to_next': (next_halving - now).days,
        'progress_pct': progress * 100,
        'phase': phase,
        'phase_color': phase_color,
        'year_in_cycle': days_since / 365.25
    }

def calculate_rsu_score(data):
    """
    Calcula el RSU Score Compuesto
    Ponderaciones: 200W MA (40%) + MVRV Z-Score (30%) + Puell (20%) + AHR999 (10%)
    Score: 0-100 (0 = máxima oportunidad, 100 = máximo riesgo)
    """
    close = ensure_1d_series(data['Close'])
    ma200 = calculate_200w_ma(data)
    
    # 1. Score de 200W MA (40%)
    ma_deviation = ((close - ma200) / ma200).iloc[-1]
    # Normalizar: -50% = 0, 0% = 50, +50% = 100
    ma_score = ((ma_deviation + 0.5) / 1.0) * 100
    ma_score = max(0, min(100, ma_score))
    
    # 2. MVRV Z-Score (30%)
    mvrv = calculate_mvrv_z_score(data).iloc[-1]
    # Normalizar: -1.5 = 0, 0 = 50, 3.5 = 100
    mvrv_score = ((mvrv + 1.5) / 5.0) * 100
    mvrv_score = max(0, min(100, mvrv_score))
    
    # 3. Puell Multiple (20%)
    puell = calculate_puell_multiple(data).iloc[-1]
    # Normalizar: 0.5 = 0, 1.0 = 50, 4.0 = 100
    puell_score = ((puell - 0.5) / 3.5) * 100
    puell_score = max(0, min(100, puell_score))
    
    # 4. AHR999 (10%)
    ahr = calculate_ahr999(data).iloc[-1]
    # Normalizar: 0.5 = 0, 1.2 = 50, 5.0 = 100
    ahr_score = ((ahr - 0.5) / 4.5) * 100
    ahr_score = max(0, min(100, ahr_score))
    
    # Score ponderado
    rsu_score = (
        ma_score * 0.40 +
        mvrv_score * 0.30 +
        puell_score * 0.20 +
        ahr_score * 0.10
    )
    
    # Determinar señal
    if rsu_score < 20:
        signal = "OPORTUNIDAD EXTREMA"
        signal_color = COLORS['rsu_extreme']
        allocation = 25
    elif rsu_score < 40:
        signal = "ACUMULACIÓN FUERTE"
        signal_color = COLORS['rsu_strong']
        allocation = 20
    elif rsu_score < 60:
        signal = "ACUMULACIÓN MODERADA"
        signal_color = COLORS['rsu_moderate']
        allocation = 10
    elif rsu_score < 80:
        signal = "NEUTRAL/ESPERA"
        signal_color = COLORS['rsu_weak']
        allocation = 0
    else:
        signal = "SOBRECOMPRA/RIESGO"
        signal_color = COLORS['rsu_poor']
        allocation = 0
    
    return {
        'total_score': rsu_score,
        'components': {
            'ma200': {'score': ma_score, 'weight': 40, 'raw': ma_deviation},
            'mvrv': {'score': mvrv_score, 'weight': 30, 'raw': mvrv},
            'puell': {'score': puell_score, 'weight': 20, 'raw': puell},
            'ahr999': {'score': ahr_score, 'weight': 10, 'raw': ahr}
        },
        'signal': signal,
        'signal_color': signal_color,
        'allocation': allocation
    }

# ───────────────────────────────────────────────────────────────────────────────
# CÁLCULOS DEL MODELO DE ACUMULACIÓN (ORIGINAL + RSU)
# ───────────────────────────────────────────────────────────────────────────────

def calculate_accumulation_zones(data):
    """
    Calcula las zonas de acumulación basadas en la 200W MA + RSU Score
    """
    close = ensure_1d_series(data['Close'])
    ma200 = calculate_200w_ma(data)
    rsu_data = calculate_rsu_score(data)
    
    minus_50 = ma200 * 0.50
    minus_25 = ma200 * 0.75
    plus_25 = ma200 * 1.25
    plus_50 = ma200 * 1.50
    
    current_price = float(close.iloc[-1])
    current_ma = float(ma200.iloc[-1]) if not pd.isna(ma200.iloc[-1]) else current_price
    
    deviation = ((current_price - current_ma) / current_ma) * 100 if current_ma > 0 else 0
    
    # Priorizar señal RSU Score sobre MA200 simple
    rsu_signal = rsu_data['signal']
    rsu_score = rsu_data['total_score']
    
    if rsu_score < 20 or current_price < minus_50.iloc[-1]:
        zone = "OPORTUNIDAD MÁXIMA"
        zone_color = COLORS['zone_max']
        allocation_pct = 25 if rsu_score < 20 else 20
        urgency = "CRÍTICA"
    elif rsu_score < 40 or current_price < minus_25.iloc[-1]:
        zone = "COMPRA AGRESIVA"
        zone_color = COLORS['zone_agg']
        allocation_pct = 20 if rsu_score < 40 else 15
        urgency = "ALTA"
    elif rsu_score < 60 or current_price < current_ma:
        zone = "COMPRA FUERTE"
        zone_color = COLORS['zone_strong']
        allocation_pct = 15 if rsu_score < 60 else 10
        urgency = "MEDIA-ALTA"
    elif rsu_score < 70 or current_price < plus_25.iloc[-1]:
        zone = "BUENA COMPRA"
        zone_color = COLORS['zone_good']
        allocation_pct = 10 if rsu_score < 70 else 5
        urgency = "MEDIA"
    elif rsu_score < 85 or current_price < plus_50.iloc[-1]:
        zone = "ZONA DCA"
        zone_color = COLORS['zone_dca']
        allocation_pct = 5 if rsu_score < 85 else 0
        urgency = "BAJA"
    else:
        zone = "ESPERAR / COMPRA LIGERA"
        zone_color = COLORS['zone_light']
        allocation_pct = 0
        urgency = "ESPERAR"
    
    return {
        'current_price': current_price,
        'ma200': current_ma,
        'deviation_pct': deviation,
        'zone': zone,
        'zone_color': zone_color,
        'allocation_pct': allocation_pct,
        'urgency': urgency,
        'rsu_score': rsu_data,
        'levels': {
            'minus_50': float(minus_50.iloc[-1]) if not pd.isna(minus_50.iloc[-1]) else None,
            'minus_25': float(minus_25.iloc[-1]) if not pd.isna(minus_25.iloc[-1]) else None,
            'ma200': current_ma,
            'plus_25': float(plus_25.iloc[-1]) if not pd.isna(plus_25.iloc[-1]) else None,
            'plus_50': float(plus_50.iloc[-1]) if not pd.isna(plus_50.iloc[-1]) else None
        },
        'series': {
            'ma200': ma200,
            'minus_50': minus_50,
            'minus_25': minus_25,
            'plus_25': plus_25,
            'plus_50': plus_50
        }
    }

def get_historical_zones_analysis(data):
    """Analiza históricamente cuánto tiempo ha pasado BTC en cada zona"""
    close = ensure_1d_series(data['Close'])
    ma200 = calculate_200w_ma(data)
    
    minus_50 = ma200 * 0.50
    minus_25 = ma200 * 0.75
    plus_25 = ma200 * 1.25
    plus_50 = ma200 * 1.50
    
    total_days = len(close.dropna())
    
    max_opp_days = len(close[close < minus_50])
    agg_buy_days = len(close[(close >= minus_50) & (close < minus_25)])
    strong_buy_days = len(close[(close >= minus_25) & (close < ma200)])
    good_buy_days = len(close[(close >= ma200) & (close < plus_25)])
    dca_days = len(close[(close >= plus_25) & (close < plus_50)])
    light_buy_days = len(close[close >= plus_50])
    
    return {
        'total_days': total_days,
        'zones': {
            'OPORTUNIDAD MÁXIMA': {'days': max_opp_days, 'pct': (max_opp_days/total_days)*100 if total_days > 0 else 0},
            'COMPRA AGRESIVA': {'days': agg_buy_days, 'pct': (agg_buy_days/total_days)*100 if total_days > 0 else 0},
            'COMPRA FUERTE': {'days': strong_buy_days, 'pct': (strong_buy_days/total_days)*100 if total_days > 0 else 0},
            'BUENA COMPRA': {'days': good_buy_days, 'pct': (good_buy_days/total_days)*100 if total_days > 0 else 0},
            'ZONA DCA': {'days': dca_days, 'pct': (dca_days/total_days)*100 if total_days > 0 else 0},
            'COMPRA LIGERA': {'days': light_buy_days, 'pct': (light_buy_days/total_days)*100 if total_days > 0 else 0}
        }
    }

# ───────────────────────────────────────────────────────────────────────────────
# VISUALIZACIONES
# ───────────────────────────────────────────────────────────────────────────────

def create_main_chart(data, zone_data, symbol="BTC-USD"):
    """Crea el gráfico principal con zonas de acumulación"""
    data = flatten_columns(data)
    close = ensure_1d_series(data['Close'])
    
    fig = go.Figure()
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_panel']
    )
    
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=ensure_1d_series(data['Open']),
        high=ensure_1d_series(data['High']),
        low=ensure_1d_series(data['Low']),
        close=close,
        name='Precio BTC',
        increasing_line_color=COLORS['accent_green'],
        decreasing_line_color=COLORS['accent_red'],
        increasing_fillcolor=COLORS['accent_green'],
        decreasing_fillcolor=COLORS['accent_red']
    ))
    
    series = zone_data['series']
    
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=series['ma200'],
        line=dict(color='#666666', width=2, dash='solid'),
        name='MA 200S',
        hovertemplate='MA 200S: %{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=series['minus_50'],
        line=dict(color='#333333', width=1),
        name='-50%',
        showlegend=False,
        hovertemplate='-50%: %{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=series['minus_25'],
        line=dict(color='#444444', width=1),
        name='-25%',
        showlegend=False,
        hovertemplate='-25%: %{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=series['plus_25'],
        line=dict(color='#444444', width=1),
        name='+25%',
        showlegend=False,
        hovertemplate='+25%: %{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=series['plus_50'],
        line=dict(color='#333333', width=1),
        name='+50%',
        showlegend=False,
        hovertemplate='+50%: %{y:,.0f}<extra></extra>'
    ))
    
    # Rellenos de zonas
    fig.add_trace(go.Scatter(
        x=data.index, y=series['minus_50'],
        fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=series['minus_25'],
        fill='tonexty', fillcolor='rgba(0,107,27,0.15)',
        mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index, y=series['minus_25'],
        fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=series['ma200'],
        fill='tonexty', fillcolor='rgba(40,167,69,0.12)',
        mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index, y=series['ma200'],
        fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=series['plus_25'],
        fill='tonexty', fillcolor='rgba(120,168,50,0.10)',
        mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index, y=series['plus_25'],
        fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=series['plus_50'],
        fill='tonexty', fillcolor='rgba(170,140,40,0.08)',
        mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    
    fig.update_layout(
        title=dict(
            text=f'₿ {symbol} | MODELO RSU v2.0 - ACUMULACIÓN MULTI-INDICADOR',
            font=dict(family='Courier New, monospace', size=20, color=COLORS['accent_cyan']),
            x=0.5
        ),
        xaxis=dict(
            gridcolor=COLORS['grid'],
            color=COLORS['text_dim'],
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            gridcolor=COLORS['grid'],
            color=COLORS['text_dim'],
            showgrid=True,
            zeroline=False,
            tickformat=',.0f'
        ),
        font=dict(family='Courier New, monospace', color=COLORS['text']),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(10,10,10,0.8)',
            bordercolor=COLORS['grid'],
            borderwidth=1,
            font=dict(color=COLORS['text_dim'])
        ),
        height=600,
        margin=dict(l=60, r=40, t=80, b=40),
        hovermode='x unified'
    )
    
    return fig

def create_rsu_gauge(rsu_data):
    """Crea un gauge visual del RSU Score"""
    
    score = rsu_data['total_score']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={
            'text': "RSU SCORE", 
            'font': {'size': 16, 'color': COLORS['accent_cyan'], 'family': 'Courier New, monospace', 'weight': 'bold'}
        },
        number={
            'font': {'size': 40, 'color': rsu_data['signal_color'], 'family': 'Courier New, monospace'},
            'valueformat': '.1f'
        },
        gauge={
            'axis': {
                'range': [0, 100], 
                'tickwidth': 2, 
                'tickcolor': COLORS['grid'],
                'tickmode': 'array',
                'tickvals': [0, 20, 40, 60, 80, 100],
                'ticktext': ['0', '20', '40', '60', '80', '100']
            },
            'bar': {
                'color': rsu_data['signal_color'],
                'thickness': 0.85
            },
            'bgcolor': COLORS['bg_panel'],
            'borderwidth': 3,
            'bordercolor': COLORS['grid'],
            'steps': [
                {'range': [0, 20], 'color': hex_to_rgba(COLORS['rsu_extreme'], 0.3)},
                {'range': [20, 40], 'color': hex_to_rgba(COLORS['rsu_strong'], 0.25)},
                {'range': [40, 60], 'color': hex_to_rgba(COLORS['rsu_moderate'], 0.2)},
                {'range': [60, 80], 'color': hex_to_rgba(COLORS['rsu_weak'], 0.15)},
                {'range': [80, 100], 'color': hex_to_rgba(COLORS['rsu_poor'], 0.1)}
            ],
            'threshold': {
                'line': {'color': 'white', 'width': 4}, 
                'thickness': 0.9, 
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        font={'color': COLORS['text'], 'family': 'Courier New, monospace'},
        height=350,
        margin=dict(l=20, r=20, t=80, b=20),
        annotations=[dict(
            text=rsu_data['signal'],
            x=0.5, y=-0.1,
            font=dict(size=14, color=rsu_data['signal_color'], family='Courier New, monospace'),
            showarrow=False
        )]
    )
    
    return fig

def create_rsu_breakdown(rsu_data):
    """Gráfico de desglose de componentes del RSU Score"""
    
    components = rsu_data['components']
    
    labels = ['MA 200S (40%)', 'MVRV Z (30%)', 'Puell (20%)', 'AHR999 (10%)']
    scores = [
        components['ma200']['score'],
        components['mvrv']['score'],
        components['puell']['score'],
        components['ahr999']['score']
    ]
    colors = [COLORS['accent_cyan'], COLORS['accent_purple'], COLORS['accent_orange'], COLORS['accent_yellow']]
    
    fig = go.Figure()
    
    for i, (label, score, color) in enumerate(zip(labels, scores, colors)):
        fig.add_trace(go.Bar(
            x=[label],
            y=[score],
            marker_color=color,
            marker_line_color='white',
            marker_line_width=2,
            text=f"{score:.1f}",
            textposition='outside',
            textfont=dict(color='white', size=12, family='Courier New, monospace'),
            hovertemplate=f'<b>{label}</b><br>Score: {score:.1f}<extra></extra>',
            showlegend=False
        ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_panel'],
        title=dict(
            text='DESGLOSE RSU SCORE',
            font=dict(color=COLORS['accent_cyan'], family='Courier New, monospace', size=14)
        ),
        xaxis=dict(
            color=COLORS['text_dim'],
            tickfont=dict(size=9, family='Courier New, monospace')
        ),
        yaxis=dict(
            color=COLORS['text_dim'],
            gridcolor=COLORS['grid'],
            title='Score (0-100)',
            range=[0, 110]
        ),
        font=dict(family='Courier New, monospace'),
        height=300,
        margin=dict(l=40, r=20, t=60, b=40),
        bargap=0.4
    )
    
    return fig

def create_zone_gauge(deviation_pct, current_zone):
    """Crea un gauge visual de en qué tan lejos estamos de la MA200"""
    
    gauge_val = max(-100, min(100, deviation_pct))
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=gauge_val,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={
            'text': "DESVIACIÓN MA 200S", 
            'font': {'size': 14, 'color': COLORS['text_dim'], 'family': 'Courier New, monospace'}
        },
        number={
            'font': {'size': 36, 'color': COLORS['accent_cyan'], 'family': 'Courier New, monospace'},
            'suffix': "%",
            'valueformat': '+.1f'
        },
        delta={
            'reference': 0, 
            'position': "top",
            'font': {'color': COLORS['text_dim']}
        },
        gauge={
            'axis': {
                'range': [-100, 100], 
                'tickwidth': 1, 
                'tickcolor': COLORS['grid'],
                'tickmode': 'array',
                'tickvals': [-50, -25, 0, 25, 50],
                'ticktext': ['-50%', '-25%', 'MA200', '+25%', '+50%']
            },
            'bar': {
                'color': COLORS['accent_cyan'] if gauge_val < 0 else COLORS['accent_orange'],
                'thickness': 0.8
            },
            'bgcolor': COLORS['bg_panel'],
            'borderwidth': 2,
            'bordercolor': COLORS['grid'],
            'steps': [
                {'range': [-100, -50], 'color': hex_to_rgba(COLORS['zone_max'], 0.3)},
                {'range': [-50, -25], 'color': hex_to_rgba(COLORS['zone_agg'], 0.25)},
                {'range': [-25, 0], 'color': hex_to_rgba(COLORS['zone_strong'], 0.2)},
                {'range': [0, 25], 'color': hex_to_rgba(COLORS['zone_good'], 0.15)},
                {'range': [25, 50], 'color': hex_to_rgba(COLORS['zone_dca'], 0.1)},
                {'range': [50, 100], 'color': hex_to_rgba(COLORS['zone_light'], 0.1)}
            ],
            'threshold': {
                'line': {'color': 'white', 'width': 3}, 
                'thickness': 0.9, 
                'value': gauge_val
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        font={'color': COLORS['text'], 'family': 'Courier New, monospace'},
        height=300,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig

def create_allocation_matrix(zone_data):
    """Crea visualización de la matriz de asignación de capital"""
    
    zones = ["OPORTUNIDAD\nMÁXIMA", "COMPRA\nAGRESIVA", "COMPRA\nFUERTE", "BUENA\nCOMPRA", "ZONA\nDCA", "ESPERAR"]
    allocations = [25, 20, 15, 10, 5, 0]
    colors = [COLORS['zone_max'], COLORS['zone_agg'], COLORS['zone_strong'], 
              COLORS['zone_good'], COLORS['zone_dca'], COLORS['zone_light']]
    
    zone_mapping = {
        "OPORTUNIDAD MÁXIMA": 0,
        "COMPRA AGRESIVA": 1,
        "COMPRA FUERTE": 2,
        "BUENA COMPRA": 3,
        "ZONA DCA": 4,
        "ESPERAR / COMPRA LIGERA": 5
    }
    
    active_idx = zone_mapping.get(zone_data['zone'], 5)
    
    fig = go.Figure()
    
    for i, (zone, alloc, color) in enumerate(zip(zones, allocations, colors)):
        opacity = 1.0 if i == active_idx else 0.3
        border_width = 3 if i == active_idx else 1
        
        fig.add_trace(go.Bar(
            x=[zone],
            y=[alloc],
            marker_color=color,
            marker_line_color='white' if i == active_idx else color,
            marker_line_width=border_width,
            opacity=opacity,
            text=f"{alloc}%" if alloc > 0 else "ESPERAR",
            textposition='outside',
            textfont=dict(color='white' if i == active_idx else COLORS['text_dim'], size=14),
            hovertemplate=f'<b>{zone.replace(chr(10), " ")}</b><br>Asignación: {alloc}%<extra></extra>',
            showlegend=False
        ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_panel'],
        title=dict(
            text='ESTRATEGIA DE ASIGNACIÓN',
            font=dict(color=COLORS['accent_green'], family='Courier New, monospace', size=16)
        ),
        xaxis=dict(
            color=COLORS['text_dim'],
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            color=COLORS['text_dim'],
            gridcolor=COLORS['grid'],
            title='Capital (%)',
            range=[0, 30]
        ),
        font=dict(family='Courier New, monospace'),
        height=300,
        margin=dict(l=40, r=20, t=60, b=40),
        bargap=0.3
    )
    
    return fig

def create_historical_distribution(hist_data):
    """Gráfico de distribución histórica de zonas"""
    
    zones = list(hist_data['zones'].keys())
    percentages = [hist_data['zones'][z]['pct'] for z in zones]
    colors = [COLORS['zone_max'], COLORS['zone_agg'], COLORS['zone_strong'], 
              COLORS['zone_good'], COLORS['zone_dca'], COLORS['zone_light']]
    
    fig = go.Figure(data=[go.Pie(
        labels=zones,
        values=percentages,
        hole=0.6,
        marker_colors=colors,
        textinfo='label+percent',
        textfont=dict(color='white', size=10),
        hovertemplate='<b>%{label}</b><br>Tiempo: %{value:.1f}%<extra></extra>'
    )])
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        title=dict(
            text='DISTRIBUCIÓN HISTÓRICA',
            font=dict(color=COLORS['text_dim'], family='Courier New, monospace', size=14)
        ),
        font=dict(family='Courier New, monospace', color=COLORS['text']),
        showlegend=False,
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        annotations=[dict(
            text=f'{hist_data["total_days"]} días<br>analizados',
            x=0.5, y=0.5,
            font=dict(size=12, color=COLORS['text_dim']),
            showarrow=False
        )]
    )
    
    return fig

# ───────────────────────────────────────────────────────────────────────────────
# COMPONENTES UI
# ───────────────────────────────────────────────────────────────────────────────

def render_rsu_dashboard(zone_data, macro_data, halving_data):
    """Renderiza el dashboard principal del RSU Score"""
    
    rsu = zone_data['rsu_score']
    
    st.markdown("---")
    
    # Header del RSU Score
    cols = st.columns([2, 1, 1])
    
    with cols[0]:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {hex_to_rgba(rsu['signal_color'], 0.2)} 0%, {COLORS['bg_panel']} 100%);
            border: 3px solid {rsu['signal_color']};
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 0 40px {hex_to_rgba(rsu['signal_color'], 0.4)};
        ">
            <div style="text-align: center;">
                <div style="color: {COLORS['text_dim']}; font-size: 12px; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 10px;">
                    RSU SCORE COMPUESTO
                </div>
                <div style="color: {rsu['signal_color']}; font-size: 56px; font-weight: bold; font-family: 'Courier New', monospace; text-shadow: 0 0 20px {hex_to_rgba(rsu['signal_color'], 0.8)};">
                    {rsu['total_score']:.1f}
                </div>
                <div style="color: {rsu['signal_color']}; font-size: 18px; font-weight: bold; margin-top: 10px;">
                    {rsu['signal']}
                </div>
                <div style="color: {COLORS['text_dim']}; font-size: 11px; margin-top: 5px;">
                    Asignación Sugerida: <span style="color: {COLORS['accent_green']}; font-weight: bold;">{rsu['allocation']}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        # Macro Conditions
        liquidity_color = COLORS['accent_green'] if macro_data['liquidity_score'] > 60 else COLORS['accent_yellow'] if macro_data['liquidity_score'] > 40 else COLORS['accent_red']
        
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_panel']};
            border: 2px solid {COLORS['grid']};
            border-radius: 8px;
            padding: 20px;
            height: 100%;
        ">
            <div style="color: {COLORS['accent_cyan']}; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; text-align: center;">
                CONDICIONES MACRO
            </div>
            <div style="margin-bottom: 10px;">
                <span style="color: {COLORS['text_dim']}; font-size: 10px;">LIQUIDEZ:</span><br>
                <span style="color: {liquidity_color}; font-size: 16px; font-weight: bold;">{macro_data['status']}</span>
            </div>
            <div style="margin-bottom: 10px;">
                <span style="color: {COLORS['text_dim']}; font-size: 10px;">DXY:</span><br>
                <span style="color: {COLORS['text']}; font-size: 14px; font-family: monospace;">{macro_data['dxy']:.2f}</span>
            </div>
            <div>
                <span style="color: {COLORS['text_dim']}; font-size: 10px;">SCORE:</span><br>
                <span style="color: {liquidity_color}; font-size: 14px; font-weight: bold;">{macro_data['liquidity_score']:.0f}/100</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        # Halving Cycle
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_panel']};
            border: 2px solid {halving_data['phase_color']};
            border-radius: 8px;
            padding: 20px;
            height: 100%;
        ">
            <div style="color: {COLORS['accent_cyan']}; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; text-align: center;">
                CICLO HALVING
            </div>
            <div style="margin-bottom: 10px;">
                <span style="color: {COLORS['text_dim']}; font-size: 10px;">FASE:</span><br>
                <span style="color: {halving_data['phase_color']}; font-size: 14px; font-weight: bold;">{halving_data['phase']}</span>
            </div>
            <div style="margin-bottom: 10px;">
                <span style="color: {COLORS['text_dim']}; font-size: 10px;">PROGRESO:</span><br>
                <span style="color: {COLORS['text']}; font-size: 14px; font-family: monospace;">{halving_data['progress_pct']:.1f}%</span>
            </div>
            <div>
                <span style="color: {COLORS['text_dim']}; font-size: 10px;">PRÓXIMO:</span><br>
                <span style="color: {COLORS['text']}; font-size: 12px; font-family: monospace;">{halving_data['days_to_next']} días</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

def render_status_panel(zone_data):
    """Renderiza el panel de estado de zona clásica"""
    
    zone = zone_data['zone']
    color = zone_data['zone_color']
    price = zone_data['current_price']
    ma = zone_data['ma200']
    dev = zone_data['deviation_pct']
    
    cols = st.columns(3)
    
    with cols[0]:
        st.markdown(f"**ZONA ACTUAL**")
        st.markdown(f"<h2 style='color: {color}; margin: 0;'>{zone}</h2>", unsafe_allow_html=True)
        st.caption(f"Urgencia: {zone_data['urgency']}")
    
    with cols[1]:
        st.markdown("**PRECIO BTC vs MA 200S**")
        st.markdown(f"<h1 style='color: {COLORS['accent_cyan']}; margin: 0;'>${price:,.0f}</h1>", unsafe_allow_html=True)
        dev_color = COLORS['accent_green'] if dev < 0 else COLORS['accent_red']
        st.markdown(f"<span style='color: {dev_color};'>{dev:+.1f}% vs MA200 (${ma:,.0f})</span>", unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown("**ASIGNACIÓN CLÁSICA**")
        alloc_color = COLORS['accent_green'] if zone_data['allocation_pct'] > 0 else COLORS['text_dim']
        st.markdown(f"<h1 style='color: {alloc_color}; margin: 0;'>{zone_data['allocation_pct']}%</h1>", unsafe_allow_html=True)
        st.caption("basado en MA200")

def render_zone_levels(zone_data):
    """Muestra los niveles de precio de cada zona"""
    
    levels = zone_data['levels']
    
    st.markdown("---")
    st.markdown("**NIVELES DE ZONAS DE ACUMULACIÓN (Basado en MA 200 Semanas)**")
    
    cols = st.columns(6)
    
    zone_info = [
        ("OPORTUNIDAD MÁXIMA", f"< ${levels['minus_50']:,.0f}", "-50%", COLORS['zone_max']),
        ("COMPRA AGRESIVA", f"${levels['minus_50']:,.0f} - ${levels['minus_25']:,.0f}", "-50% a -25%", COLORS['zone_agg']),
        ("COMPRA FUERTE", f"${levels['minus_25']:,.0f} - ${levels['ma200']:,.0f}", "-25% a MA", COLORS['zone_strong']),
        ("BUENA COMPRA", f"${levels['ma200']:,.0f} - ${levels['plus_25']:,.0f}", "MA a +25%", COLORS['zone_good']),
        ("ZONA DCA", f"${levels['plus_25']:,.0f} - ${levels['plus_50']:,.0f}", "+25% a +50%", COLORS['zone_dca']),
        ("ESPERAR", f"> ${levels['plus_50']:,.0f}", "+50%+", COLORS['zone_light']),
    ]
    
    for i, (name, price_range, pct, color) in enumerate(zone_info):
        with cols[i]:
            st.markdown(f"<p style='color: {color}; font-weight: bold; font-size: 0.8rem;'>{name}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-family: monospace; font-size: 0.9rem;'>${price_range}</p>", unsafe_allow_html=True)
            st.caption(pct)

def render_warning_section():
    """Sección de advertencias"""
    
    with st.expander("⚠️ AVISOS DE RIESGO CRÍTICOS", expanded=True):
        st.markdown(f"""
        <div style='color: {COLORS['text_dim']};'>
        
        **1. RSU Score es un Modelo Probabilístico**
        La combinación de indicadores (MA200W 40% + MVRV 30% + Puell 20% + AHR999 10%) mejora la filtración de falsos positivos,
        pero no elimina el riesgo. Los mercados pueden comportarse de manera irracional más tiempo del que puedes mantener solvente.
        
        **2. Condiciones Macro No Consideradas en Score**
        El DXY y tasas de la FED son mostrados como referencia pero NO están incluidos en el cálculo del RSU Score para mantener
        la pureza de los indicadores on-chain. Un DXY alcista fuerte (>105) puede anular señales de compra técnicamente válidas.
        
        **3. Ciclos de Halving son Guías, no Garantías**
        Aunque el halving reduce la oferta, la demanda puede no materializarse como en ciclos anteriores. La correlación
        halving-precio ha disminuido con la maduración del mercado.
        
        **4. Datos On-Chain Son Aproximaciones**
        MVRV Z-Score, Puell Multiple y AHR999 en esta implementación usan cálculos proxy basados en precio/volumen.
        Para análisis institucional, usar APIs especializadas (Glassnode, CryptoQuant).
        
        **5. Esto NO es Asesoramiento Financiero**
        Nunca inviertas más de lo que puedas permitirte perder. El modelo RSU es para acumulación a largo plazo (3-5 años),
        no para trading de corto plazo.
        </div>
        """, unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ───────────────────────────────────────────────────────────────────────────────

def main():
    # CSS Global
    st.markdown(f"""
    <style>
    .stApp {{
        background-color: {COLORS['bg_dark']};
    }}
    h1, h2, h3 {{
        color: {COLORS['accent_cyan']} !important;
        font-family: 'Courier New', monospace !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {COLORS['bg_panel']};
        padding: 10px;
        border-radius: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: {COLORS['bg_dark']};
        color: {COLORS['text_dim']};
        border: 1px solid {COLORS['grid']};
        border-radius: 4px;
        padding: 10px 20px;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        font-size: 12px;
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLORS['bg_panel']};
        color: {COLORS['accent_green']};
        border: 1px solid {COLORS['accent_green']};
        box-shadow: 0 0 10px {hex_to_rgba(COLORS['accent_green'], 0.3)};
    }}
    .stButton>button {{
        background: {COLORS['bg_panel']};
        color: {COLORS['accent_cyan']};
        border: 1px solid {COLORS['accent_cyan']};
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    .stButton>button:hover {{
        background: {COLORS['accent_cyan']};
        color: {COLORS['bg_dark']};
        box-shadow: 0 0 20px {hex_to_rgba(COLORS['accent_cyan'], 0.5)};
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px; padding: 20px; border-bottom: 1px solid {COLORS['grid']};">
        <div style="font-size: 48px; margin-bottom: 10px;">₿</div>
        <h1 style="margin: 0; font-size: 2rem;">Modelo RSU Bitcoin v2.0</h1>
        <p style="color: {COLORS['text_dim']}; font-family: 'Courier New', monospace; font-size: 14px; margin-top: 10px;">
            Multi-Indicador: MA200S + MVRV + Puell + AHR999 + Macro | Ciclo Halving Integrado
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs
    tab_analysis, tab_methodology, tab_risks = st.tabs(["📊 Análisis RSU", "📖 Metodología", "⚠️ Riesgos"])
    
    with tab_analysis:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            symbol = st.text_input("Símbolo del Activo", value="BTC-USD", 
                                 help="Ingresa el ticker de Yahoo Finance (BTC-USD, ETH-USD, etc.)").upper().strip()
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_btn = st.button("⟳ CARGAR DATOS", use_container_width=True, type="primary")
        
        if analyze_btn or symbol:
            with st.spinner("Calculando RSU Score y condiciones de mercado..."):
                try:
                    data = yf.download(symbol, start="2015-01-01", interval="1d", progress=False, auto_adjust=True)
                    
                    if data.empty or len(data) < 200:
                        st.error(f"Datos insuficientes para {symbol}. Se necesitan al menos 200 días.")
                        return
                    
                    data = flatten_columns(data)
                    
                    # Calcular todos los datos
                    zone_data = calculate_accumulation_zones(data)
                    macro_data = get_macro_conditions()
                    halving_data = get_halving_cycle()
                    hist_data = get_historical_zones_analysis(data)
                    
                    # Dashboard RSU Principal
                    render_rsu_dashboard(zone_data, macro_data, halving_data)
                    
                    # Gráfico principal
                    st.plotly_chart(create_main_chart(data, zone_data, symbol), use_container_width=True)
                    
                    # Grid de métricas
                    col_g1, col_g2, col_g3 = st.columns([1, 1, 1])
                    
                    with col_g1:
                        st.plotly_chart(create_rsu_gauge(zone_data['rsu_score']), use_container_width=True)
                    
                    with col_g2:
                        st.plotly_chart(create_rsu_breakdown(zone_data['rsu_score']), use_container_width=True)
                    
                    with col_g3:
                        st.plotly_chart(create_zone_gauge(zone_data['deviation_pct'], zone_data['zone']), 
                                      use_container_width=True)
                    
                    # Segunda fila
                    col_h1, col_h2 = st.columns([2, 1])
                    
                    with col_h1:
                        st.plotly_chart(create_allocation_matrix(zone_data), use_container_width=True)
                    
                    with col_h2:
                        st.plotly_chart(create_historical_distribution(hist_data), use_container_width=True)
                    
                    # Niveles de zona clásicos
                    render_zone_levels(zone_data)
                    
                    # Panel clásico para referencia
                    with st.expander("📊 Zonas Clásicas MA200 (Referencia)", expanded=False):
                        render_status_panel(zone_data)
                    
                    # Detalles técnicos
                    with st.expander("🔬 ESPECIFICACIONES TÉCNICAS RSU", expanded=False):
                        rsu = zone_data['rsu_score']
                        st.code(f"""
╔══════════════════════════════════════════════════════════════════╗
║                    RSU SCORE BREAKDOWN v2.0                      ║
╠══════════════════════════════════════════════════════════════════╣
  ACTIVO: {symbol}
  RANGO:  {data.index[0].strftime('%Y-%m-%d')} a {data.index[-1].strftime('%Y-%m-%d')}
  
┌─ INDICADORES ON-CHAIN ─────────────────────────────────────────┐
│ MA 200S (40%):     Score {rsu['components']['ma200']['score']:.1f} | Raw: {rsu['components']['ma200']['raw']:.3f}
│ MVRV Z (30%):      Score {rsu['components']['mvrv']['score']:.1f} | Raw: {rsu['components']['mvrv']['raw']:.3f}
│ Puell (20%):       Score {rsu['components']['puell']['score']:.1f} | Raw: {rsu['components']['puell']['raw']:.3f}
│ AHR999 (10%):      Score {rsu['components']['ahr999']['score']:.1f} | Raw: {rsu['components']['ahr999']['raw']:.3f}
└────────────────────────────────────────────────────────────────┘

┌─ CONDICIONES MACRO ────────────────────────────────────────────┐
│ DXY:               {macro_data['dxy']:.2f} ({macro_data['dxy_score']:.0f}/100)
│ Liquidez:          {macro_data['liquidity_score']:.0f}/100 - {macro_data['status']}
└────────────────────────────────────────────────────────────────┘

┌─ CICLO HALVING ────────────────────────────────────────────────┐
│ Fase:              {halving_data['phase']}
│ Progreso:          {halving_data['progress_pct']:.1f}%
│ Días al próximo:   {halving_data['days_to_next']}
└────────────────────────────────────────────────────────────────┘

RSU SCORE FINAL: {rsu['total_score']:.2f}/100
SEÑAL: {rsu['signal']}
ASIGNACIÓN: {rsu['allocation']}%
                        """)
                        
                except Exception as e:
                    st.error(f"Error del sistema: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    with tab_methodology:
        with st.container():
            st.markdown(f"""
            ### 📚 Metodología RSU v2.0
            
            **1. RSU Score Compuesto (Ponderado)**
            
            El RSU Score combina múltiples indicadores on-chain probados para filtrar falsos positivos:
            
            - **MA 200S (40%)**: Tendencia a largo plazo, "piso" histórico de Bitcoin
            - **MVRV Z-Score (30%)**: Valor de mercado vs valor realizado, identifica tops/bottoms
            - **Puell Multiple (20%)**: Ingresos de mineros, señal de costo de producción
            - **AHR999 (10%)**: Índice específico de acumulación para Bitcoin
            
            **Fórmula**: `RSU = (MA×0.4) + (MVRV×0.3) + (Puell×0.2) + (AHR999×0.1)`
            
            **Interpretación**:
            - **0-20**: Oportunidad extrema (acumulación agresiva)
            - **20-40**: Acumulación fuerte
            - **40-60**: Acumulación moderada/DCA
            - **60-80**: Neutral/espera
            - **80-100**: Sobrecompra/riesgo alto
            """)
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(f"""
                **2. Condiciones Macro (Referencia)**
                
                Mostradas pero NO incluidas en el score para mantener pureza on-chain:
                
                - **DXY > 105**: Restrictivo para BTC (dólar fuerte)
                - **DXY < 100**: Expansivo para BTC (dólar débil)
                - **FED Pivot**: Cambio en política monetaria
                
                **3. Ciclo de Halving**
                
                Bitcoin tiene ciclos de ~4 años correlacionados con halvings:
                - **Año 1 post-halving**: Acumulación/Bull temprano
                - **Año 2**: Bull market principal
                - **Año 3**: Distribución/top
                - **Año 4**: Bear market/pre-halving
                """)
            with col_m2:
                st.markdown(f"""
                **4. Estrategia de Asignación Dinámica**
                
                El modelo ajusta asignación basada en RSU Score + Zona MA200:
                
                | RSU Score | Señal | Asignación |
                |-----------|-------|------------|
                | 0-20 | Extrema | 25% |
                | 20-40 | Fuerte | 20% |
                | 40-60 | Moderada | 10% |
                | 60-80 | Neutral | 0% |
                | 80-100 | Riesgo | 0% |
                
                **Nota**: La asignación máxima se alcanza solo cuando RSU Score < 20
                Y el precio está bajo MA200S (confluencia de señales).
                """)
    
    with tab_risks:
        render_warning_section()

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN RENDER PARA INTEGRACIÓN CON APP PRINCIPAL RSU
# ═══════════════════════════════════════════════════════════════════════════════

def render():
    """
    Punto de entrada principal para la sección BTC STRATUM.
    Esta función es llamada por la aplicación principal RSU cuando el usuario
    selecciona esta opción del menú lateral.
    """
    main()

# Mantener compatibilidad con ejecución directa (python btc_stratum.py)
if __name__ == "__main__":
    main()
