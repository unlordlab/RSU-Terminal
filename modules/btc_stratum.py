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
    return close.rolling(window=1400, min_periods=100).mean()

def calculate_accumulation_zones(data):
    """
    Calcula las zonas de acumulación basadas en la 200W MA
    """
    close = ensure_1d_series(data['Close'])
    ma200 = calculate_200w_ma(data)
    
    minus_50 = ma200 * 0.50
    minus_25 = ma200 * 0.75
    plus_25 = ma200 * 1.25
    plus_50 = ma200 * 1.50
    
    current_price = float(close.iloc[-1])
    current_ma = float(ma200.iloc[-1]) if not pd.isna(ma200.iloc[-1]) else current_price
    
    deviation = ((current_price - current_ma) / current_ma) * 100 if current_ma > 0 else 0
    
    if current_price < minus_50.iloc[-1]:
        zone = "OPORTUNIDAD MÁXIMA"
        zone_color = COLORS['zone_max']
        allocation_pct = 20
        urgency = "CRÍTICA"
    elif current_price < minus_25.iloc[-1]:
        zone = "COMPRA AGRESIVA"
        zone_color = COLORS['zone_agg']
        allocation_pct = 40
        urgency = "ALTA"
    elif current_price < current_ma:
        zone = "COMPRA FUERTE"
        zone_color = COLORS['zone_strong']
        allocation_pct = 30
        urgency = "MEDIA-ALTA"
    elif current_price < plus_25.iloc[-1]:
        zone = "BUENA COMPRA"
        zone_color = COLORS['zone_good']
        allocation_pct = 10
        urgency = "MEDIA"
    elif current_price < plus_50.iloc[-1]:
        zone = "ZONA DCA"
        zone_color = COLORS['zone_dca']
        allocation_pct = 0
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
            text=f'₿ {symbol} | MODELO DE ACUMULACIÓN MA 200 SEMANAS',
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
    
    gauge_val = max(-100, min(100, deviation_pct))
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=gauge_val,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={
            'text': "DESVIACIÓN DE LA MA 200S", 
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
    allocations = [20, 40, 30, 10, 0, 0]
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
            text='ESTRATEGIA DE ASIGNACIÓN DE CAPITAL',
            font=dict(color=COLORS['accent_green'], family='Courier New, monospace', size=16)
        ),
        xaxis=dict(
            color=COLORS['text_dim'],
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            color=COLORS['text_dim'],
            gridcolor=COLORS['grid'],
            title='Porcentaje del Capital (%)',
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
            text='DISTRIBUCIÓN HISTÓRICA DE ZONAS',
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
# COMPONENTES UI CON STREAMLIT NATIVO (EVITAR HTML RAW)
# ───────────────────────────────────────────────────────────────────────────────

def render_status_panel(zone_data):
    """Renderiza el panel de estado superior usando componentes nativos de Streamlit"""
    
    zone = zone_data['zone']
    color = zone_data['zone_color']
    price = zone_data['current_price']
    ma = zone_data['ma200']
    dev = zone_data['deviation_pct']
    
    # Contenedor principal con borde de color
    with st.container():
        st.markdown("""
        <style>
        .zone-container {
            background: linear-gradient(135deg, """ + hex_to_rgba(color, 0.2) + """ 0%, """ + COLORS['bg_panel'] + """ 100%);
            border: 2px solid """ + color + """;
            border-radius: 8px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 0 30px """ + hex_to_rgba(color, 0.3) + """;
        }
        </style>
        """, unsafe_allow_html=True)
        
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
            st.markdown("**ASIGNACIÓN RECOMENDADA**")
            alloc_color = COLORS['accent_green'] if zone_data['allocation_pct'] > 0 else COLORS['text_dim']
            st.markdown(f"<h1 style='color: {alloc_color}; margin: 0;'>{zone_data['allocation_pct']}%</h1>", unsafe_allow_html=True)
            st.caption("del capital disponible")

def render_zone_levels(zone_data):
    """Muestra los niveles de precio de cada zona usando métricas de Streamlit"""
    
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
    """Sección de advertencias usando expanders y texto nativo"""
    
    with st.expander("⚠️ AVISOS DE RIESGO CRÍTICOS", expanded=True):
        st.markdown(f"""
        <div style='color: {COLORS['text_dim']};'>
        
        **1. Rendimiento Histórico ≠ Resultados Futuros**
        Este modelo se basa en el análisis histórico del ciclo de 4 años. El comportamiento pasado de Bitcoin 
        alrededor de la MA 200S no garantiza que las zonas de acumulación futuras se comporten de manera idéntica.
        
        **2. Supuestos del Modelo**
        La MA 200S asume que Bitcoin continúa su tendencia de adopción a largo plazo. Una ruptura estructural 
        en los fundamentos de Bitcoin (prohibición regulatoria, tecnología superior, ataques de computación cuántica) 
        podría invalidar este modelo permanentemente.
        
        **3. Riesgo de Asignación de Capital**
        Desplegar el 20% del capital en zonas de "Oportunidad Máxima" asume que puedes soportar caídas 
        adicionales del 50-80%. Estas zonas suelen coincidir con máximo miedo y posibles crisis de solvencia 
        de exchanges.
        
        **4. Sin Estrategia de Salida**
        Esta herramienta proporciona señales de acumulación únicamente. NO indica cuándo vender. 
        Necesitas una metodología de salida separada (ej. MVRV z-score, Pi Cycle, etc.).
        
        **5. Esto NO es Asesoramiento Financiero**
        Este es un marco probabilístico para la acumulación a largo plazo de Bitcoin. Nunca inviertas más 
        de lo que puedas permitirte perder por completo. Los mercados de criptomonedas son altamente 
        volátiles y no regulados.
        </div>
        """, unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ───────────────────────────────────────────────────────────────────────────────

def main():
    # CSS Global simplificado
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
        <h1 style="margin: 0; font-size: 2rem;">Modelo de Acumulación RSU Bitcoin</h1>
        <p style="color: {COLORS['text_dim']}; font-family: 'Courier New', monospace; font-size: 14px; margin-top: 10px;">
            Estrategia de Zonas basada en Media Móvil de 200 Semanas | Metodología de r/mltraders por Gold-Tourist1996
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs en castellano
    tab_analysis, tab_methodology, tab_risks = st.tabs(["📊 Análisis de Zonas", "📖 Metodología", "⚠️ Riesgos"])
    
    with tab_analysis:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            symbol = st.text_input("Símbolo del Activo", value="BTC-USD", 
                                 help="Ingresa el ticker de Yahoo Finance (BTC-USD, ETH-USD, etc.)").upper().strip()
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_btn = st.button("⟳ CARGAR DATOS", use_container_width=True, type="primary")
        
        if analyze_btn or symbol:
            with st.spinner("Calculando zonas de acumulación MA 200S..."):
                try:
                    data = yf.download(symbol, start="2015-01-01", interval="1d", progress=False, auto_adjust=True)
                    
                    if data.empty or len(data) < 200:
                        st.error(f"Datos insuficientes para {symbol}. Se necesitan al menos 200 días.")
                        return
                    
                    data = flatten_columns(data)
                    
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
                    with st.expander("🔬 ESPECIFICACIONES TÉCNICAS", expanded=False):
                        st.code(f"""
PARÁMETROS DE CÁLCULO:
----------------------
Activo:             {symbol}
Rango de Datos:     {data.index[0].strftime('%Y-%m-%d')} a {data.index[-1].strftime('%Y-%m-%d')}
Total de Días:      {len(data)}
Período MA 200S:    1400 días (200 semanas × 7 días)

MÉTRICAS ACTUALES:
----------------------
Precio:             ${zone_data['current_price']:,.2f}
MA 200S:            ${zone_data['ma200']:,.2f}
Desviación:         {zone_data['deviation_pct']:+.2f}%
Zona:               {zone_data['zone']}
Asignación:         {zone_data['allocation_pct']}%

UMBRALES DE ZONAS:
----------------------
Oportunidad Máxima:   < ${zone_data['levels']['minus_50']:,.2f} (-50%)
Compra Agresiva:    ${zone_data['levels']['minus_50']:,.2f} a ${zone_data['levels']['minus_25']:,.2f}
Compra Fuerte:      ${zone_data['levels']['minus_25']:,.2f} a ${zone_data['levels']['ma200']:,.2f}
Buena Compra:       ${zone_data['levels']['ma200']:,.2f} a ${zone_data['levels']['plus_25']:,.2f}
Zona DCA:           ${zone_data['levels']['plus_25']:,.2f} a ${zone_data['levels']['plus_50']:,.2f}
Esperar:            > ${zone_data['levels']['plus_50']:,.2f} (+50%)

FRECUENCIA HISTÓRICA:
----------------------
Oportunidad Máxima:  {hist_data['zones']['OPORTUNIDAD MÁXIMA']['pct']:.1f}% del tiempo
Compra Agresiva:     {hist_data['zones']['COMPRA AGRESIVA']['pct']:.1f}% del tiempo
Compra Fuerte:       {hist_data['zones']['COMPRA FUERTE']['pct']:.1f}% del tiempo
Buena Compra:        {hist_data['zones']['BUENA COMPRA']['pct']:.1f}% del tiempo
Zona DCA:            {hist_data['zones']['ZONA DCA']['pct']:.1f}% del tiempo
Esperar:             {hist_data['zones']['COMPRA LIGERA']['pct']:.1f}% del tiempo
                        """)
                        
                except Exception as e:
                    st.error(f"Error del sistema: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    with tab_methodology:
        with st.container():
            st.markdown(f"""
            ### 📚 Metodología del Modelo
            
            **1. La Media Móvil de 200 Semanas (MA 200S)**
            
            Este es el pilar del modelo - un indicador de tendencia a largo plazo que suaviza 4 años de acción del precio. 
            Históricamente, Bitcoin nunca ha caído por debajo de la MA 200S por períodos extendidos durante mercados alcistas, 
            convirtiéndola en un "piso" para la acumulación a largo plazo.
            
            **2. Bandas de Desviación como Zonas de Acumulación**
            
            El modelo crea 5 zonas basadas en la desviación porcentual de la MA 200S:
            """)
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(f"""
                - <span style='color: {COLORS['zone_max']};'>**Oportunidad Máxima (<-50%)**</span>: Fondos generacionales históricos (2015, 2018, 2022)
                - <span style='color: {COLORS['zone_agg']};'>**Compra Agresiva (-50% a -25%)**</span>: Acumulación en mercado bajista profundo
                - <span style='color: {COLORS['zone_strong']};'>**Compra Fuerte (-25% a MA)**</span>: Por debajo de la tendencia, entrada de alta probabilidad
                """, unsafe_allow_html=True)
            with col_m2:
                st.markdown(f"""
                - <span style='color: {COLORS['zone_good']};'>**Buena Compra (MA a +25%)**</span>: En o ligeramente por encima de la tendencia, DCA
                - <span style='color: {COLORS['zone_dca']};'>**Zona DCA (+25% a +50%)**</span>: Mercado alcista temprano, solo pequeñas asignaciones
                - <span style='color: {COLORS['zone_light']};'>**Esperar (>+50%)**</span>: Sobreextendido, esperar mejores entradas
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            **3. Estrategia de Asignación de Capital**
            
            La asignación recomendada (20/40/30/10/0/0) está diseñada para desplegar más capital cuando Bitcoin está 
            estadísticamente más barato vs su tendencia a largo plazo, mientras se preserva capital cuando está caro. 
            Este es un marco de acumulación <em>solo compra</em>, no una estrategia de trading.
            
            **4. Contexto Histórico**
            
            Desde 2015, Bitcoin ha pasado solo ~2-3% del tiempo en zonas de "Oportunidad Máxima", típicamente durante 
            eventos de capitulación (fallas de exchanges, FUD regulatorio, crashes macro). Estos son momentos 
            psicológicamente difíciles para comprar, precisamente por eso ofrecen la mejor relación riesgo/recompensa.
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
