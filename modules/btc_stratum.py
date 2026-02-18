# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ═══════════════════════════════════════════════════════════════════════════════
# RSU BITCOIN ACCUMULATION MODEL
# Basado en el indicador 200W MA de Gold-Tourist1996 (r/mltraders)
# ═══════════════════════════════════════════════════════════════════════════════

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
    'zone_wait': '#666666'          # Wait zone
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
# CÁLCULOS DEL MODELO DE ACUMULACIÓN
# ───────────────────────────────────────────────────────────────────────────────

def calculate_200w_ma(data):
    """Calcula la Media Móvil de 200 Semanas"""
    close = ensure_1d_series(data['Close'])
    # 200 semanas = 200 * 7 = 1400 días aproximadamente
    # Usamos 1400 periodos diarios como aproximación
    return close.rolling(window=1400, min_periods=100).mean()

def calculate_accumulation_zones(data):
    """
    Calcula las zonas de acumulación basadas en la 200W MA
    Zonas:
    - MAXIMUM OPPORTUNITY: < -50% de la MA200
    - AGGRESSIVE BUY: -50% a -25%
    - STRONG BUY: -25% a 0% (MA200)
    - GOOD BUY: 0% a +25%
    - DCA ZONE: +25% a +50%
    - LIGHT BUY: > +50%
    """
    close = ensure_1d_series(data['Close'])
    ma200 = calculate_200w_ma(data)
    
    # Niveles de precio
    minus_50 = ma200 * 0.50
    minus_25 = ma200 * 0.75
    plus_25 = ma200 * 1.25
    plus_50 = ma200 * 1.50
    
    # Determinar zona actual
    current_price = float(close.iloc[-1])
    current_ma = float(ma200.iloc[-1]) if not pd.isna(ma200.iloc[-1]) else current_price
    
    deviation = ((current_price - current_ma) / current_ma) * 100 if current_ma > 0 else 0
    
    if current_price < minus_50.iloc[-1]:
        zone = "MAXIMUM OPPORTUNITY"
        zone_color = COLORS['zone_max']
        allocation_pct = 20
        urgency = "CRÍTICO"
    elif current_price < minus_25.iloc[-1]:
        zone = "AGGRESSIVE BUY"
        zone_color = COLORS['zone_agg']
        allocation_pct = 40
        urgency = "ALTA"
    elif current_price < current_ma:
        zone = "STRONG BUY"
        zone_color = COLORS['zone_strong']
        allocation_pct = 30
        urgency = "MEDIA-ALTA"
    elif current_price < plus_25.iloc[-1]:
        zone = "GOOD BUY"
        zone_color = COLORS['zone_good']
        allocation_pct = 10
        urgency = "MEDIA"
    elif current_price < plus_50.iloc[-1]:
        zone = "DCA ZONE"
        zone_color = COLORS['zone_dca']
        allocation_pct = 0  # Esperar mejor entrada
        urgency = "BAJA"
    else:
        zone = "LIGHT BUY / WAIT"
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
    
    # Contar días en cada zona
    max_opp_days = len(close[close < minus_50])
    agg_buy_days = len(close[(close >= minus_50) & (close < minus_25)])
    strong_buy_days = len(close[(close >= minus_25) & (close < ma200)])
    good_buy_days = len(close[(close >= ma200) & (close < plus_25)])
    dca_days = len(close[(close >= plus_25) & (close < plus_50)])
    light_buy_days = len(close[close >= plus_50])
    
    return {
        'total_days': total_days,
        'zones': {
            'MAXIMUM OPPORTUNITY': {'days': max_opp_days, 'pct': (max_opp_days/total_days)*100 if total_days > 0 else 0},
            'AGGRESSIVE BUY': {'days': agg_buy_days, 'pct': (agg_buy_days/total_days)*100 if total_days > 0 else 0},
            'STRONG BUY': {'days': strong_buy_days, 'pct': (strong_buy_days/total_days)*100 if total_days > 0 else 0},
            'GOOD BUY': {'days': good_buy_days, 'pct': (good_buy_days/total_days)*100 if total_days > 0 else 0},
            'DCA ZONE': {'days': dca_days, 'pct': (dca_days/total_days)*100 if total_days > 0 else 0},
            'LIGHT BUY': {'days': light_buy_days, 'pct': (light_buy_days/total_days)*100 if total_days > 0 else 0}
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
    
    # Fondo negro absoluto
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_panel']
    )
    
    # Velas de precio
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=ensure_1d_series(data['Open']),
        high=ensure_1d_series(data['High']),
        low=ensure_1d_series(data['Low']),
        close=close,
        name='BTC Price',
        increasing_line_color=COLORS['accent_green'],
        decreasing_line_color=COLORS['accent_red'],
        increasing_fillcolor=COLORS['accent_green'],
        decreasing_fillcolor=COLORS['accent_red']
    ))
    
    # Líneas de zonas
    series = zone_data['series']
    
    # MA 200 (línea central gris)
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=series['ma200'],
        line=dict(color='#666666', width=2, dash='solid'),
        name='200W MA',
        hovertemplate='200W MA: %{y:,.0f}<extra></extra>'
    ))
    
    # Niveles de zona (líneas grises sutiles)
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
    
    # Rellenos de zonas (gradiente de gris a verde)
    # Zona -50% a -25% (más oscura/oportunidad máxima)
    fig.add_trace(go.Scatter(
        x=data.index, y=series['minus_50'],
        fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=series['minus_25'],
        fill='tonexty', fillcolor='rgba(0,107,27,0.15)',  # zone_max con transparencia
        mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    
    # Zona -25% a MA200
    fig.add_trace(go.Scatter(
        x=data.index, y=series['minus_25'],
        fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=series['ma200'],
        fill='tonexty', fillcolor='rgba(40,167,69,0.12)',  # zone_strong
        mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    
    # Zona MA200 a +25%
    fig.add_trace(go.Scatter(
        x=data.index, y=series['ma200'],
        fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=series['plus_25'],
        fill='tonexty', fillcolor='rgba(120,168,50,0.10)',  # zone_good
        mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    
    # Zona +25% a +50%
    fig.add_trace(go.Scatter(
        x=data.index, y=series['plus_25'],
        fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=series['plus_50'],
        fill='tonexty', fillcolor='rgba(170,140,40,0.08)',  # zone_dca
        mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
    ))
    
    # Layout final
    fig.update_layout(
        title=dict(
            text=f'₿ {symbol} | 200 WEEK MA ACCUMULATION MODEL',
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

def create_zone_gauge(deviation_pct, current_zone):
    """Crea un gauge visual de en qué tan lejos estamos de la MA200"""
    
    # Normalizar valor para el gauge (-100 a +100)
    gauge_val = max(-100, min(100, deviation_pct))
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=gauge_val,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={
            'text': "DEVIATION FROM 200W MA", 
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
    
    zones = ["MAXIMUM\nOPPORTUNITY", "AGGRESSIVE\nBUY", "STRONG\nBUY", "GOOD\nBUY", "DCA\nZONE", "LIGHT BUY\n/WAIT"]
    allocations = [20, 40, 30, 10, 0, 0]
    colors = [COLORS['zone_max'], COLORS['zone_agg'], COLORS['zone_strong'], 
              COLORS['zone_good'], COLORS['zone_dca'], COLORS['zone_light']]
    
    # Determinar zona activa
    active_idx = zones.index(zone_data['zone'].replace(" ", "\n")) if zone_data['zone'] in [z.replace("\n", " ") for z in zones] else 5
    
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
            text=f"{alloc}%" if alloc > 0 else "HOLD",
            textposition='outside',
            textfont=dict(color='white' if i == active_idx else COLORS['text_dim'], size=14),
            hovertemplate=f'<b>{zone.replace(chr(10), " ")}</b><br>Asignación: {alloc}%<extra></extra>',
            showlegend=False
        ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_panel'],
        title=dict(
            text='CAPITAL ALLOCATION STRATEGY',
            font=dict(color=COLORS['accent_green'], family='Courier New, monospace', size=16)
        ),
        xaxis=dict(
            color=COLORS['text_dim'],
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            color=COLORS['text_dim'],
            gridcolor=COLORS['grid'],
            title='Porcentaje de Capital (%)',
            range=[0, 50]
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
            text='HISTORICAL ZONE DISTRIBUTION',
            font=dict(color=COLORS['text_dim'], family='Courier New, monospace', size=14)
        ),
        font=dict(family='Courier New, monospace', color=COLORS['text']),
        showlegend=False,
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        annotations=[dict(
            text=f'{hist_data["total_days"]} days<br>analyzed',
            x=0.5, y=0.5,
            font=dict(size=12, color=COLORS['text_dim']),
            showarrow=False
        )]
    )
    
    return fig

# ───────────────────────────────────────────────────────────────────────────────
# COMPONENTES UI
# ───────────────────────────────────────────────────────────────────────────────

def render_status_panel(zone_data):
    """Renderiza el panel de estado superior"""
    
    zone = zone_data['zone']
    color = zone_data['zone_color']
    price = zone_data['current_price']
    ma = zone_data['ma200']
    dev = zone_data['deviation_pct']
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {hex_to_rgba(color, 0.2)} 0%, {COLORS['bg_panel']} 100%);
        border: 2px solid {color};
        border-radius: 8px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 0 30px {hex_to_rgba(color, 0.3)};
    ">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 30px; text-align: center;">
            <div>
                <div style="color: {COLORS['text_dim']}; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;">
                    Current Zone
                </div>
                <div style="color: {color}; font-size: 24px; font-weight: bold; font-family: 'Courier New', monospace; text-shadow: 0 0 10px {hex_to_rgba(color, 0.5)};">
                    {zone}
                </div>
                <div style="color: {COLORS['text_dim']}; font-size: 10px; margin-top: 5px;">
                    Urgency: {zone_data['urgency']}
                </div>
            </div>
            
            <div>
                <div style="color: {COLORS['text_dim']}; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;">
                    BTC Price vs 200W MA
                </div>
                <div style="color: {COLORS['accent_cyan']}; font-size: 32px; font-weight: bold; font-family: 'Courier New', monospace;">
                    ${price:,.0f}
                </div>
                <div style="color: {COLORS['accent_green'] if dev < 0 else COLORS['accent_red']}; font-size: 14px; margin-top: 5px; font-family: 'Courier New', monospace;">
                    {dev:+.1f}% vs MA200 (${ma:,.0f})
                </div>
            </div>
            
            <div>
                <div style="color: {COLORS['text_dim']}; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;">
                    Recommended Allocation
                </div>
                <div style="color: {COLORS['accent_green'] if zone_data['allocation_pct'] > 0 else COLORS['text_dim']}; font-size: 32px; font-weight: bold; font-family: 'Courier New', monospace;">
                    {zone_data['allocation_pct']}%
                </div>
                <div style="color: {COLORS['text_dim']}; font-size: 10px; margin-top: 5px;">
                    of available capital
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_zone_levels(zone_data):
    """Muestra los niveles de precio de cada zona"""
    
    levels = zone_data['levels']
    
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_panel']};
        border: 1px solid {COLORS['grid']};
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    ">
        <div style="color: {COLORS['text_dim']}; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; text-align: center;">
            Accumulation Zone Levels (200W MA Based)
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; text-align: center;">
            <div style="padding: 10px; background: {hex_to_rgba(COLORS['zone_max'], 0.2)}; border-radius: 4px; border-left: 3px solid {COLORS['zone_max']};">
                <div style="color: {COLORS['zone_max']}; font-size: 10px; font-weight: bold;">MAX OPP</div>
                <div style="color: white; font-size: 12px; font-family: 'Courier New', monospace;">&lt; ${levels['minus_50']:,.0f}</div>
                <div style="color: {COLORS['text_dim']}; font-size: 9px;">-50%</div>
            </div>
            
            <div style="padding: 10px; background: {hex_to_rgba(COLORS['zone_agg'], 0.2)}; border-radius: 4px; border-left: 3px solid {COLORS['zone_agg']};">
                <div style="color: {COLORS['zone_agg']}; font-size: 10px; font-weight: bold;">AGGRESSIVE</div>
                <div style="color: white; font-size: 12px; font-family: 'Courier New', monospace;">${levels['minus_50']:,.0f} - ${levels['minus_25']:,.0f}</div>
                <div style="color: {COLORS['text_dim']}; font-size: 9px;">-50% to -25%</div>
            </div>
            
            <div style="padding: 10px; background: {hex_to_rgba(COLORS['zone_strong'], 0.2)}; border-radius: 4px; border-left: 3px solid {COLORS['zone_strong']};">
                <div style="color: {COLORS['zone_strong']}; font-size: 10px; font-weight: bold;">STRONG</div>
                <div style="color: white; font-size: 12px; font-family: 'Courier New', monospace;">${levels['minus_25']:,.0f} - ${levels['ma200']:,.0f}</div>
                <div style="color: {COLORS['text_dim']}; font-size: 9px;">-25% to MA</div>
            </div>
            
            <div style="padding: 10px; background: {hex_to_rgba(COLORS['zone_good'], 0.2)}; border-radius: 4px; border-left: 3px solid {COLORS['zone_good']};">
                <div style="color: {COLORS['zone_good']}; font-size: 10px; font-weight: bold;">GOOD</div>
                <div style="color: white; font-size: 12px; font-family: 'Courier New', monospace;">${levels['ma200']:,.0f} - ${levels['plus_25']:,.0f}</div>
                <div style="color: {COLORS['text_dim']}; font-size: 9px;">MA to +25%</div>
            </div>
            
            <div style="padding: 10px; background: {hex_to_rgba(COLORS['zone_dca'], 0.2)}; border-radius: 4px; border-left: 3px solid {COLORS['zone_dca']};">
                <div style="color: {COLORS['zone_dca']}; font-size: 10px; font-weight: bold;">DCA</div>
                <div style="color: white; font-size: 12px; font-family: 'Courier New', monospace;">${levels['plus_25']:,.0f} - ${levels['plus_50']:,.0f}</div>
                <div style="color: {COLORS['text_dim']}; font-size: 9px;">+25% to +50%</div>
            </div>
            
            <div style="padding: 10px; background: {hex_to_rgba(COLORS['zone_light'], 0.2)}; border-radius: 4px; border-left: 3px solid {COLORS['zone_light']};">
                <div style="color: {COLORS['zone_light']}; font-size: 10px; font-weight: bold;">WAIT</div>
                <div style="color: white; font-size: 12px; font-family: 'Courier New', monospace;">&gt; ${levels['plus_50']:,.0f}</div>
                <div style="color: {COLORS['text_dim']}; font-size: 9px;">+50%+</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_warning_section():
    """Sección de advertencias y metodología"""
    
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_panel']};
        border: 1px solid {COLORS['accent_red']};
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    ">
        <div style="color: {COLORS['accent_red']}; font-size: 14px; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 2px;">
            ⚠️ Critical Risk Disclosures
        </div>
        
        <div style="color: {COLORS['text_dim']}; font-size: 12px; line-height: 1.6;">
            <p><strong style="color: {COLORS['text']};">1. Historical Performance ≠ Future Results:</strong> 
            This model is based on historical 4-year cycle analysis. Bitcoin's past behavior around the 200W MA 
            does not guarantee future accumulation zones will behave identically.</p>
            
            <p><strong style="color: {COLORS['text']};">2. Model Assumptions:</strong> 
            The 200W MA assumes Bitcoin continues its long-term adoption trend. A structural break in 
            Bitcoin's fundamentals (regulatory ban, superior technology replacement, quantum computing attacks) 
            could invalidate this model permanently.</p>
            
            <p><strong style="color: {COLORS['text']};">3. Capital Allocation Risk:</strong> 
            Deploying 20% of capital in "Maximum Opportunity" zones assumes you can withstand further 
            drawdowns of 50-80%. These zones often coincide with maximum fear and potential exchange solvency crises.</p>
            
            <p><strong style="color: {COLORS['text']};">4. No Exit Strategy:</strong> 
            This tool provides accumulation signals only. It does NOT tell you when to sell. 
            You need a separate exit methodology (e.g., MVRV z-score, Pi Cycle, etc.).</p>
            
            <p><strong style="color: {COLORS['accent_orange']};">5. This is NOT Financial Advice:</strong> 
            This is a probabilistic framework for long-term Bitcoin accumulation. Never invest more than 
            you can afford to lose entirely. Cryptocurrency markets are highly volatile and unregulated.</p>
        </div>
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
            letter-spacing: 3px;
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
        div[data-testid="stSpinner"] {{
            color: {COLORS['accent_green']} !important;
            font-family: 'Courier New', monospace;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px; padding: 20px; border-bottom: 1px solid {COLORS['grid']};">
        <div style="font-size: 48px; margin-bottom: 10px;">₿</div>
        <h1 style="margin: 0; font-size: 2rem;">RSU Bitcoin Accumulation Model</h1>
        <p style="color: {COLORS['text_dim']}; font-family: 'Courier New', monospace; font-size: 14px; margin-top: 10px;">
            200 Week Moving Average Zone Strategy | Based on r/mltraders methodology by Gold-Tourist1996
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs
    tab_analysis, tab_methodology, tab_risks = st.tabs(["📊 Zone Analysis", "📖 Methodology", "⚠️ Risk Warnings"])
    
    with tab_analysis:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            symbol = st.text_input("Asset Symbol", value="BTC-USD", 
                                 help="Enter Yahoo Finance ticker (BTC-USD, ETH-USD, etc.)").upper().strip()
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_btn = st.button("⟳ LOAD DATA", use_container_width=True, type="primary")
        
        if analyze_btn or symbol:
            with st.spinner("Calculating 200W MA accumulation zones..."):
                try:
                    # Descargar datos desde 2015 para tener suficiente historia para 200W MA
                    data = yf.download(symbol, start="2015-01-01", interval="1d", progress=False, auto_adjust=True)
                    
                    if data.empty or len(data) < 200:
                        st.error(f"Insufficient data for {symbol}. Need at least 200 days.")
                        return
                    
                    data = flatten_columns(data)
                    
                    # Calcular zonas
                    zone_data = calculate_accumulation_zones(data)
                    hist_data = get_historical_zones_analysis(data)
                    
                    # Panel de estado
                    render_status_panel(zone_data)
                    
                    # Gráfico principal
                    st.plotly_chart(create_main_chart(data, zone_data, symbol), use_container_width=True)
                    
                    # Grid inferior
                    col_g1, col_g2, col_g3 = st.columns([1, 1, 1])
                    
                    with col_g1:
                        st.plotly_chart(create_zone_gauge(zone_data['deviation_pct'], zone_data['zone']), 
                                      use_container_width=True)
                    
                    with col_g2:
                        st.plotly_chart(create_allocation_matrix(zone_data), use_container_width=True)
                    
                    with col_g3:
                        st.plotly_chart(create_historical_distribution(hist_data), use_container_width=True)
                    
                    # Niveles de zona
                    render_zone_levels(zone_data)
                    
                    # Detalles técnicos
                    with st.expander("🔬 TECHNICAL SPECIFICATIONS", expanded=False):
                        st.markdown(f"""
                        <div style="font-family: 'Courier New', monospace; color: {COLORS['text_dim']}; font-size: 12px;">
                        <pre style="background: {COLORS['bg_panel']}; padding: 15px; border-radius: 4px; border: 1px solid {COLORS['grid']};">
CALCULATION PARAMETERS:
----------------------
Asset:              {symbol}
Data Range:         {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}
Total Days:         {len(data)}
200W MA Period:     1400 days (200 weeks × 7 days)

CURRENT METRICS:
----------------------
Price:              ${zone_data['current_price']:,.2f}
200W MA:            ${zone_data['ma200']:,.2f}
Deviation:          {zone_data['deviation_pct']:+.2f}%
Zone:               {zone_data['zone']}
Allocation:         {zone_data['allocation_pct']}%

ZONE THRESHOLDS:
----------------------
Maximum Opportunity:  &lt; ${zone_data['levels']['minus_50']:,.2f} (-50%)
Aggressive Buy:     ${zone_data['levels']['minus_50']:,.2f} to ${zone_data['levels']['minus_25']:,.2f}
Strong Buy:         ${zone_data['levels']['minus_25']:,.2f} to ${zone_data['levels']['ma200']:,.2f}
Good Buy:           ${zone_data['levels']['ma200']:,.2f} to ${zone_data['levels']['plus_25']:,.2f}
DCA Zone:           ${zone_data['levels']['plus_25']:,.2f} to ${zone_data['levels']['plus_50']:,.2f}
Wait/Light Buy:     &gt; ${zone_data['levels']['plus_50']:,.2f} (+50%)

HISTORICAL FREQUENCY:
----------------------
Maximum Opportunity:  {hist_data['zones']['MAXIMUM OPPORTUNITY']['pct']:.1f}% of time
Aggressive Buy:       {hist_data['zones']['AGGRESSIVE BUY']['pct']:.1f}% of time
Strong Buy:           {hist_data['zones']['STRONG BUY']['pct']:.1f}% of time
Good Buy:             {hist_data['zones']['GOOD BUY']['pct']:.1f}% of time
DCA Zone:             {hist_data['zones']['DCA ZONE']['pct']:.1f}% of time
Light Buy/Wait:       {hist_data['zones']['LIGHT BUY']['pct']:.1f}% of time
                        </pre>
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"System error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    with tab_methodology:
        st.markdown(f"""
        <div style="background: {COLORS['bg_panel']}; border: 1px solid {COLORS['grid']}; border-radius: 8px; padding: 25px; margin: 20px 0;">
            <h3 style="color: {COLORS['accent_cyan']}; margin-bottom: 20px; font-size: 1.2rem; text-transform: uppercase; letter-spacing: 2px;">
                📚 Model Methodology
            </h3>
            
            <div style="color: {COLORS['text_dim']}; font-size: 13px; line-height: 1.8;">
                <p><strong style="color: {COLORS['accent_green']};">1. The 200 Week Moving Average (200W MA)</strong><br>
                This is the backbone of the model - a long-term trend indicator that smooths 4 years of price action. 
                Historically, Bitcoin has never fallen below the 200W MA for extended periods during bull markets, 
                making it a "floor" for long-term accumulation.</p>
                
                <p><strong style="color: {COLORS['accent_green']};">2. Deviation Bands as Accumulation Zones</strong><br>
                The model creates 5 zones based on percentage deviation from the 200W MA:
                <ul style="margin-left: 20px; color: {COLORS['text_dim']};">
                    <li><span style="color: {COLORS['zone_max']};">Maximum Opportunity (&lt;-50%):</span> Historic generational bottoms (2015, 2018, 2022)</li>
                    <li><span style="color: {COLORS['zone_agg']};">Aggressive Buy (-50% to -25%):</span> Deep bear market accumulation</li>
                    <li><span style="color: {COLORS['zone_strong']};">Strong Buy (-25% to MA):</span> Below long-term trend, high probability entry</li>
                    <li><span style="color: {COLORS['zone_good']};">Good Buy (MA to +25%):</span> At or slightly above trend, dollar-cost averaging</li>
                    <li><span style="color: {COLORS['zone_dca']};">DCA Zone (+25% to +50%):</span> Early bull market, only small allocations</li>
                    <li><span style="color: {COLORS['zone_light']};">Wait Zone (&gt;+50%):</span> Overextended, wait for better entries</li>
                </ul></p>
                
                <p><strong style="color: {COLORS['accent_green']};">3. Capital Allocation Strategy</strong><br>
                The recommended allocation (20/40/30/10/0/0) is designed to deploy more capital when Bitcoin is 
                statistically cheaper vs its long-term trend, while preserving capital when it's expensive. 
                This is a <em>buy-only</em> accumulation framework, not a trading strategy.</p>
                
                <p><strong style="color: {COLORS['accent_orange']};">4. Historical Context</strong><br>
                Since 2015, Bitcoin has spent only ~2-3% of time in "Maximum Opportunity" zones, typically during 
                capitulation events (exchange failures, regulatory FUD, macro crashes). These are psychologically 
                difficult times to buy, which is precisely why they offer the best risk/reward.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with tab_risks:
        render_warning_section()

if __name__ == "__main__":
    main()
