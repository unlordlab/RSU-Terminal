# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ═══════════════════════════════════════════════════════════════════════════════
# RSU BITCOIN ACCUMULATION MODEL v2.1
# Basado en: 200W MA + MVRV Z-Score + Puell Multiple + AHR999 + Macro Conditions
# Nuevas features: Stress Test Scenarios + Alertas Progresivas
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
    'bg_dark': '#0c0e12',
    'bg_panel': '#1a1e26',
    'grid': '#2a3f5f',
    'text': '#cccccc',
    'text_dim': '#666666',
    'accent_green': '#00ffad',      # Terminal mint — roadmap primary
    'accent_cyan': '#00d9ff',       # Electric cyan
    'accent_red': '#f23645',        # Alert red
    'accent_orange': '#ff9800',     # Warning orange
    'accent_yellow': '#ffd60a',     # Caution yellow
    'accent_purple': '#9c27b0',     # Deep purple
    'zone_max': '#006b1b',          # Maximum opportunity - deep green
    'zone_agg': '#009627',          # Aggressive buy
    'zone_strong': '#28a745',       # Strong buy
    'zone_good': '#78a832',         # Good buy
    'zone_dca': '#aa8c28',          # DCA zone
    'zone_light': '#aa5028',        # Light buy
    'zone_wait': '#666666',         # Wait zone
    'rsu_extreme': '#00ffad',       # RSU Score < 20
    'rsu_strong': '#00d9ff',        # RSU Score 20-40
    'rsu_moderate': '#ffd60a',      # RSU Score 40-60
    'rsu_weak': '#ff9800',          # RSU Score 60-80
    'rsu_poor': '#f23645',          # RSU Score > 80
    'stress_extreme': '#f23645',    # Stress test extremo
    'stress_moderate': '#ff9800',   # Stress test moderado
    'alert_info': '#00d9ff'         # Alertas informativas
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

def calculate_ma_curvature(data):
    """
    Calcula la curvatura (segunda derivada) de la MA200W
    Positiva = tendencia alcista acelerándose, Negativa = desacelerándose
    """
    ma200 = calculate_200w_ma(data)
    # Primera derivada (pendiente)
    ma_slope = ma200.diff(30)  # Cambio en 30 días
    # Segunda derivada (curvatura)
    curvature = ma_slope.diff(30)
    
    current_slope = ma_slope.iloc[-1] if not pd.isna(ma_slope.iloc[-1]) else 0
    current_curvature = curvature.iloc[-1] if not pd.isna(curvature.iloc[-1]) else 0
    
    # Normalizar para interpretación
    slope_pct = (current_slope / ma200.iloc[-1]) * 100 if ma200.iloc[-1] > 0 else 0
    
    return {
        'slope': slope_pct,
        'curvature': current_curvature,
        'trend': 'ALCISTA FUERTE' if slope_pct > 1 else 'ALCISTA' if slope_pct > 0.2 else 'LATERAL' if slope_pct > -0.2 else 'BAJISTA',
        'acceleration': 'ACELERANDO' if current_curvature > 0 else 'DESACELERANDO',
        'ma_value': ma200.iloc[-1]
    }

def calculate_mvrv_z_score(data, market_cap_data=None):
    """
    Calcula MVRV Z-Score simplificado basado en desviación del precio vs MA200W
    """
    close = ensure_1d_series(data['Close'])
    ma200 = calculate_200w_ma(data)
    
    deviation = (close - ma200) / ma200
    mvrv_z = deviation * 3.5
    
    return mvrv_z

def calculate_puell_multiple(data):
    """
    Calcula Puell Multiple simplificado basado en momentum de emisión
    """
    close = ensure_1d_series(data['Close'])
    sma_365 = close.rolling(window=365).mean()
    puell = close / sma_365
    
    return puell

def calculate_ahr999(data):
    """
    Calcula índice AHR999 simplificado
    Fórmula original: (Precio / 200DMA) / log(200DMA)
    """
    close = ensure_1d_series(data['Close'])
    ma200 = calculate_200w_ma(data)
    ma200_safe = ma200.replace(0, np.nan)
    ahr999 = (close / ma200_safe) / np.log(ma200_safe)
    
    return ahr999

def get_macro_conditions():
    """
    Obtiene condiciones macroeconómicas relevantes
    """
    try:
        dxy = yf.download("DX-Y.NYB", period="1y", interval="1d", progress=False, auto_adjust=True)
        dxy = flatten_columns(dxy)
        dxy_current = float(ensure_1d_series(dxy['Close']).iloc[-1])
        dxy_ma50 = ensure_1d_series(dxy['Close']).rolling(50).mean().iloc[-1]
        
        dxy_score = 50 if pd.isna(dxy_ma50) else (50 - ((dxy_current / dxy_ma50 - 1) * 500))
        dxy_score = max(0, min(100, dxy_score))
        
        tlt = yf.download("TLT", period="1y", interval="1d", progress=False, auto_adjust=True)
        tlt = flatten_columns(tlt)
        tlt_yield = 20 - (float(ensure_1d_series(tlt['Close']).iloc[-1]) / 10)
        
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
    """
    halving_dates = [
        datetime(2012, 11, 28),
        datetime(2016, 7, 9),
        datetime(2020, 5, 11),
        datetime(2024, 4, 19)
    ]
    
    now = datetime.now()
    last_halving = max([h for h in halving_dates if h <= now])
    next_halving = datetime(2028, 4, 1)
    
    days_since = (now - last_halving).days
    days_total = (next_halving - last_halving).days
    progress = days_since / days_total
    
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
        phase = "MERCADO BAJISTA"
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
    """
    close = ensure_1d_series(data['Close'])
    ma200 = calculate_200w_ma(data)
    
    # 1. Score de 200W MA (40%)
    ma_deviation = ((close - ma200) / ma200).iloc[-1]
    ma_score = ((ma_deviation + 0.5) / 1.0) * 100
    ma_score = max(0, min(100, ma_score))
    
    # 2. MVRV Z-Score (30%)
    mvrv = calculate_mvrv_z_score(data).iloc[-1]
    mvrv_score = ((mvrv + 1.5) / 5.0) * 100
    mvrv_score = max(0, min(100, mvrv_score))
    
    # 3. Puell Multiple (20%)
    puell = calculate_puell_multiple(data).iloc[-1]
    puell_score = ((puell - 0.5) / 3.5) * 100
    puell_score = max(0, min(100, puell_score))
    
    # 4. AHR999 (10%)
    ahr = calculate_ahr999(data).iloc[-1]
    ahr_score = ((ahr - 0.5) / 4.5) * 100
    ahr_score = max(0, min(100, ahr_score))
    
    rsu_score = (
        ma_score * 0.40 +
        mvrv_score * 0.30 +
        puell_score * 0.20 +
        ahr_score * 0.10
    )
    
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
# SISTEMA DE ALERTAS PROGRESIVAS
# ───────────────────────────────────────────────────────────────────────────────

def calculate_progressive_alerts(data, zone_data):
    """
    Calcula alertas progresivas de proximidad a zonas y condiciones de mercado
    """
    close = ensure_1d_series(data['Close'])
    current_price = float(close.iloc[-1])
    ma200 = zone_data['ma200']
    levels = zone_data['levels']
    
    alerts = []
    
    # 1. Proximidad a zonas
    if current_price > levels['ma200']:
        distance_to_strong = ((current_price - levels['ma200']) / levels['ma200']) * 100
        if distance_to_strong <= 15:
            alerts.append({
                'type': 'proximity',
                'level': 'info',
                'icon': '📉',
                'message': f"A {distance_to_strong:.1f}% de entrar en COMPRA FUERTE",
                'color': COLORS['alert_info']
            })
    else:
        distance_to_max = ((levels['minus_50'] - current_price) / current_price) * 100 if current_price > 0 else 999
        if 0 < distance_to_max <= 20:
            alerts.append({
                'type': 'proximity',
                'level': 'opportunity',
                'icon': '🔥',
                'message': f"A {distance_to_max:.1f}% de OPORTUNIDAD MÁXIMA",
                'color': COLORS['zone_max']
            })
    
    # 2. Curvatura MA200
    ma_curvature = calculate_ma_curvature(data)
    if ma_curvature['slope'] > 0.5 and ma_curvature['curvature'] > 0:
        alerts.append({
            'type': 'trend',
            'level': 'positive',
            'icon': '📈',
            'message': f"MA200W {ma_curvature['trend']} y {ma_curvature['acceleration']}",
            'color': COLORS['accent_green']
        })
    elif ma_curvature['slope'] < -0.2:
        alerts.append({
            'type': 'trend',
            'level': 'warning',
            'icon': '⚠️',
            'message': f"MA200W mostrando tendencia {ma_curvature['trend']}",
            'color': COLORS['accent_orange']
        })
    
    # 3. Divergencias entre indicadores
    rsu = zone_data['rsu_score']
    if rsu['components']['ma200']['score'] > 60 and rsu['components']['mvrv']['score'] < 40:
        alerts.append({
            'type': 'divergence',
            'level': 'opportunity',
            'icon': '💎',
            'message': "Divergencia: Precio bajo MA200 pero MVRV muestra valoración justa",
            'color': COLORS['accent_cyan']
        })
    
    # 4. Niveles históricos
    all_time_high = close.max()
    drawdown_from_ath = ((current_price - all_time_high) / all_time_high) * 100
    if drawdown_from_ath < -70:
        alerts.append({
            'type': 'historical',
            'level': 'extreme',
            'icon': '🚨',
            'message': f"Drawdown del {drawdown_from_ath:.1f}% desde ATH - Zona histórica de capitulación",
            'color': COLORS['accent_red']
        })
    elif drawdown_from_ath < -50:
        alerts.append({
            'type': 'historical',
            'level': 'opportunity',
            'icon': '💰',
            'message': f"Drawdown del {drawdown_from_ath:.1f}% desde ATH - Considerar acumulación",
            'color': COLORS['zone_agg']
        })
    
    return alerts

# ───────────────────────────────────────────────────────────────────────────────
# SISTEMA DE STRESS TEST
# ─────────────────════════════════════════════════════════════════════════════──

def run_stress_tests(data, zone_data):
    """
    Simula escenarios alternativos y colapsos estructurales para gestión de expectativas
    """
    close = ensure_1d_series(data['Close'])
    current_price = float(close.iloc[-1])
    current_position = zone_data['allocation_pct']
    
    scenarios = []
    
    # Escenario 1: "2017 fue el top" (Bear market perpetuo)
    max_price_2017 = close[close.index.year <= 2017].max() if len(close[close.index.year <= 2017]) > 0 else close.max()
    if current_price > max_price_2017:
        drop_to_2017 = ((current_price - max_price_2017) / current_price) * 100
        pnl_2017_scenario = -(current_position * 2)  # Pérdida acelerada si el modelo falla
        
        scenarios.append({
            'name': 'TOP 2017 DEFINITIVO',
            'description': 'Si 2017 fue el máximo histórico permanente',
            'price_target': max_price_2017,
            'drop_pct': drop_to_2017,
            'pnl_scenario': pnl_2017_scenario,
            'probability': 'BAJA (5%)',
            'hedge': 'Stop loss en -30% o diversificación a 50% stablecoins',
            'severity': 'extreme'
        })
    
    # Escenario 2: Colapso de exchange mayor (FTX 2.0)
    ftx_scenario_drop = 50
    ftx_price = current_price * 0.5
    pnl_ftx = -(current_position * 1.5)
    
    scenarios.append({
        'name': 'COLAPSO EXCHANGE MAYOR',
        'description': 'Evento tipo FTX/Celsius - Pánico sistémico temporal',
        'price_target': ftx_price,
        'drop_pct': ftx_scenario_drop,
        'pnl_scenario': pnl_ftx,
        'probability': 'MEDIA (15%)',
        'hedge': 'Mantener 70% en cold wallet, límite de exposición por exchange',
        'severity': 'high'
    })
    
    # Escenario 3: Regulación severa (Ban China 2.0)
    regulation_drop = 35
    reg_price = current_price * 0.65
    pnl_reg = -(current_position * 1.2)
    
    scenarios.append({
        'name': 'BAN REGULATORIO GLOBAL',
        'description': 'Prohibición amplia en G7 + confiscación parcial',
        'price_target': reg_price,
        'drop_pct': regulation_drop,
        'pnl_scenario': pnl_reg,
        'probability': 'MEDIA-BAJA (10%)',
        'hedge': 'Diversificación geográfica, monederos auto-custodiales',
        'severity': 'high'
    })
    
    # Escenario 4: Ruptura técnica (Quantum/SHA256 roto)
    tech_drop = 80
    tech_price = current_price * 0.2
    pnl_tech = -(current_position * 3)
    
    scenarios.append({
        'name': 'RUPTURA CRIPTOGRÁFICA',
        'description': 'Ataque cuántico o vulnerabilidad SHA256 descubierta',
        'price_target': tech_price,
        'drop_pct': tech_drop,
        'pnl_scenario': pnl_tech,
        'probability': 'MUY BAJA (2%)',
        'hedge': 'Imposible de hedgear - aceptar riesgo de colapso total',
        'severity': 'extreme'
    })
    
    # Escenario 5: Estanflación macro prolongada
    stagflation_drop = 60
    stag_price = current_price * 0.4
    pnl_stag = -(current_position * 1.8)
    
    scenarios.append({
        'name': 'ESTANFLACIÓN 5+ AÑOS',
        'description': 'DXY >120, tasas >10%, recesión global prolongada',
        'price_target': stag_price,
        'drop_pct': stagflation_drop,
        'pnl_scenario': pnl_stag,
        'probability': 'MEDIA (20%)',
        'hedge': 'Oro, bienes raíces, exposición mínima a risk-on assets',
        'severity': 'moderate'
    })
    
    # Calcular métricas agregadas
    max_drawdown = max([s['drop_pct'] for s in scenarios])
    avg_pnl = np.mean([s['pnl_scenario'] for s in scenarios])
    worst_pnl = min([s['pnl_scenario'] for s in scenarios])
    
    return {
        'scenarios': scenarios,
        'summary': {
            'max_drawdown_tested': max_drawdown,
            'avg_pnl_scenario': avg_pnl,
            'worst_case_pnl': worst_pnl,
            'capital_at_risk': current_position
        }
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
            text=f'₿ {symbol}  //  MODELO RSU v2.1  —  ACUMULACIÓN MULTI-INDICADOR',
            font=dict(family='VT323, monospace', size=24, color=COLORS['accent_green']),
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
            'text': "// RSU SCORE //", 
            'font': {'size': 18, 'color': COLORS['accent_green'], 'family': 'VT323, monospace'}
        },
        number={
            'font': {'size': 48, 'color': rsu_data['signal_color'], 'family': 'VT323, monospace'},
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
            text='// DESGLOSE RSU SCORE //',
            font=dict(color=COLORS['accent_green'], family='VT323, monospace', size=18)
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
            'text': "// DESVIACIÓN MA 200S //", 
            'font': {'size': 16, 'color': COLORS['accent_cyan'], 'family': 'VT323, monospace'}
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
            text='// ESTRATEGIA DE ASIGNACIÓN //',
            font=dict(color=COLORS['accent_green'], family='VT323, monospace', size=20)
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

def create_stress_test_chart(stress_data):
    """Visualización de escenarios de stress test"""
    
    scenarios = stress_data['scenarios']
    
    names = [s['name'] for s in scenarios]
    drops = [s['drop_pct'] for s in scenarios]
    pnls = [s['pnl_scenario'] for s in scenarios]
    
    colors = [COLORS['stress_extreme'] if s['severity'] == 'extreme' else COLORS['stress_moderate'] for s in scenarios]
    
    fig = make_subplots(rows=1, cols=2, subplot_titles=('Caída del Precio (%)', 'P&L Escenario (%)'),
                        horizontal_spacing=0.15)
    
    # Gráfico de caídas
    fig.add_trace(
        go.Bar(
            x=names,
            y=drops,
            marker_color=colors,
            text=[f"{d:.0f}%" for d in drops],
            textposition='outside',
            textfont=dict(color='white', family='Courier New, monospace'),
            hovertemplate='<b>%{x}</b><br>Caída: %{y:.1f}%<extra></extra>',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Gráfico de P&L
    fig.add_trace(
        go.Bar(
            x=names,
            y=pnls,
            marker_color=colors,
            text=[f"{p:.0f}%" for p in pnls],
            textposition='outside',
            textfont=dict(color='white', family='Courier New, monospace'),
            hovertemplate='<b>%{x}</b><br>P&L: %{y:.1f}%<extra></extra>',
            showlegend=False
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_panel'],
        font=dict(family='Courier New, monospace', color=COLORS['text']),
        height=400,
        margin=dict(l=60, r=40, t=80, b=100),
        title=dict(
            text='// STRESS TEST — ESCENARIOS EXTREMOS //',
            font=dict(color=COLORS['accent_red'], family='VT323, monospace', size=22),
            x=0.5
        )
    )
    
    fig.update_xaxes(tickangle=45, tickfont=dict(size=9))
    fig.update_yaxes(gridcolor=COLORS['grid'], color=COLORS['text_dim'])
    
    return fig

# ───────────────────────────────────────────────────────────────────────────────
# COMPONENTES UI
# ───────────────────────────────────────────────────────────────────────────────

def render_alerts_panel(alerts):
    """Renderiza el panel de alertas progresivas"""
    
    if not alerts:
        st.info("No hay alertas activas en este momento. El mercado está en rango neutral.")
        return
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-family: 'VT323', monospace; font-size: 1.5rem; color: {COLORS['accent_green']};
                letter-spacing: 3px; text-transform: uppercase; margin-bottom: 15px;">
        🔔 // ALERTAS DE MERCADO
    </div>
    """, unsafe_allow_html=True)
    
    for alert in alerts:
        alert_color = alert['color']
        icon = alert['icon']
        message = alert['message']
        
        st.markdown(f"""
        <div class="phase-box" style="border-left-color: {alert_color}; margin: 8px 0;">
            <span style="font-size: 20px; margin-right: 10px;">{icon}</span>
            <span style="color: {alert_color}; font-family: 'VT323', monospace; font-size: 1.15rem; letter-spacing: 1px;">
                {message}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)

def render_stress_test_panel(stress_data):
    """Renderiza el panel de stress test"""
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-family: 'VT323', monospace; font-size: 1.5rem; color: {COLORS['stress_extreme']};
                letter-spacing: 3px; text-transform: uppercase; margin-bottom: 15px;">
        💥 // STRESS TEST — GESTIÓN DE EXPECTATIVAS
    </div>
    """, unsafe_allow_html=True)
    
    summary = stress_data['summary']
    
    # Resumen ejecutivo
    cols = st.columns(4)
    with cols[0]:
        st.metric("Máx Drawdown Testeado", f"{summary['max_drawdown_tested']:.0f}%", delta=None)
    with cols[1]:
        st.metric("P&L Promedio", f"{summary['avg_pnl_scenario']:.1f}%", delta=None)
    with cols[2]:
        st.metric("Peor Caso P&L", f"{summary['worst_case_pnl']:.1f}%", delta=None)
    with cols[3]:
        st.metric("Capital en Riesgo", f"{summary['capital_at_risk']}%", delta=None)
    
    # Gráfico de stress
    st.plotly_chart(create_stress_test_chart(stress_data), use_container_width=True)
    
    # Detalle de escenarios
    with st.expander("📋 DETALLE DE ESCENARIOS", expanded=False):
        for scenario in stress_data['scenarios']:
            severity_color = COLORS['stress_extreme'] if scenario['severity'] == 'extreme' else COLORS['stress_moderate']
            
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_panel']};
                border: 1px solid {severity_color};
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="color: {severity_color}; margin: 0;">{scenario['name']}</h4>
                    <span style="background: {severity_color}; color: black; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                        {scenario['probability']}
                    </span>
                </div>
                <p style="color: {COLORS['text_dim']}; font-size: 13px; margin: 8px 0;">
                    {scenario['description']}
                </p>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 10px; font-family: monospace; font-size: 12px;">
                    <div>
                        <span style="color: {COLORS['text_dim']};">Objetivo:</span><br>
                        <span style="color: {COLORS['accent_red']};">${scenario['price_target']:,.0f}</span>
                    </div>
                    <div>
                        <span style="color: {COLORS['text_dim']};">Caída:</span><br>
                        <span style="color: {COLORS['accent_red']};">-{scenario['drop_pct']:.0f}%</span>
                    </div>
                    <div>
                        <span style="color: {COLORS['text_dim']};">P&L:</span><br>
                        <span style="color: {COLORS['accent_red']};">{scenario['pnl_scenario']:.0f}%</span>
                    </div>
                </div>
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid {COLORS['grid']};">
                    <span style="color: {COLORS['accent_cyan']}; font-size: 11px;">🛡️ HEDGE:</span>
                    <span style="color: {COLORS['text']}; font-size: 12px;"> {scenario['hedge']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_rsu_dashboard(zone_data, macro_data, halving_data):
    """Renderiza el dashboard principal del RSU Score"""
    
    rsu = zone_data['rsu_score']
    
    st.markdown("---")
    
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
                <div style="color: {COLORS['text_dim']}; font-family: 'VT323', monospace; font-size: 1rem; text-transform: uppercase; letter-spacing: 4px; margin-bottom: 10px;">
                    // RSU SCORE COMPUESTO //
                </div>
                <div style="color: {rsu['signal_color']}; font-size: 5rem; font-family: 'VT323', monospace; text-shadow: 0 0 25px {hex_to_rgba(rsu['signal_color'], 0.8)}; line-height: 1;">
                    {rsu['total_score']:.1f}
                </div>
                <div style="color: {rsu['signal_color']}; font-family: 'VT323', monospace; font-size: 1.5rem; letter-spacing: 3px; margin-top: 10px;">
                    {rsu['signal']}
                </div>
                <div style="color: {COLORS['text_dim']}; font-family: 'Courier New', monospace; font-size: 11px; margin-top: 8px;">
                    Asignación Sugerida: <span style="color: {COLORS['accent_green']}; font-family: 'VT323', monospace; font-size: 1.2rem;">{rsu['allocation']}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        liquidity_color = COLORS['accent_green'] if macro_data['liquidity_score'] > 60 else COLORS['accent_yellow'] if macro_data['liquidity_score'] > 40 else COLORS['accent_red']
        
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_panel']};
            border: 2px solid {COLORS['grid']};
            border-radius: 8px;
            padding: 20px;
            height: 100%;
        ">
            <div style="color: {COLORS['accent_cyan']}; font-family: 'VT323', monospace; font-size: 1rem; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 15px; text-align: center;">
                // CONDICIONES MACRO //
            </div>
            <div style="margin-bottom: 12px;">
                <span style="color: {COLORS['text_dim']}; font-family: 'VT323', monospace; font-size: 0.85rem; letter-spacing: 2px;">LIQUIDEZ:</span><br>
                <span style="color: {liquidity_color}; font-family: 'VT323', monospace; font-size: 1.3rem; letter-spacing: 2px;">{macro_data['status']}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <span style="color: {COLORS['text_dim']}; font-family: 'VT323', monospace; font-size: 0.85rem; letter-spacing: 2px;">DXY:</span><br>
                <span style="color: {COLORS['text']}; font-family: 'VT323', monospace; font-size: 1.3rem;">{macro_data['dxy']:.2f}</span>
            </div>
            <div>
                <span style="color: {COLORS['text_dim']}; font-family: 'VT323', monospace; font-size: 0.85rem; letter-spacing: 2px;">SCORE:</span><br>
                <span style="color: {liquidity_color}; font-family: 'VT323', monospace; font-size: 1.3rem;">{macro_data['liquidity_score']:.0f}/100</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_panel']};
            border: 2px solid {halving_data['phase_color']};
            border-radius: 8px;
            padding: 20px;
            height: 100%;
        ">
            <div style="color: {COLORS['accent_cyan']}; font-family: 'VT323', monospace; font-size: 1rem; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 15px; text-align: center;">
                // CICLO HALVING //
            </div>
            <div style="margin-bottom: 12px;">
                <span style="color: {COLORS['text_dim']}; font-family: 'VT323', monospace; font-size: 0.85rem; letter-spacing: 2px;">FASE:</span><br>
                <span style="color: {halving_data['phase_color']}; font-family: 'VT323', monospace; font-size: 1.3rem; letter-spacing: 2px;">{halving_data['phase']}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <span style="color: {COLORS['text_dim']}; font-family: 'VT323', monospace; font-size: 0.85rem; letter-spacing: 2px;">PROGRESO:</span><br>
                <span style="color: {COLORS['text']}; font-family: 'VT323', monospace; font-size: 1.3rem;">{halving_data['progress_pct']:.1f}%</span>
            </div>
            <div>
                <span style="color: {COLORS['text_dim']}; font-family: 'VT323', monospace; font-size: 0.85rem; letter-spacing: 2px;">PRÓXIMO:</span><br>
                <span style="color: {COLORS['text']}; font-family: 'VT323', monospace; font-size: 1.3rem;">{halving_data['days_to_next']} días</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)

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
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"""<div style="font-family: 'VT323', monospace; color: {COLORS['accent_cyan']}; font-size: 1.2rem; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 15px;">
        // NIVELES DE ZONAS — MA 200 SEMANAS //
    </div>""", unsafe_allow_html=True)
    
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
    
    with st.expander("⚠️ // AVISOS DE RIESGO CRÍTICOS", expanded=True):
        risks = [
            ("01", "RSU SCORE ES UN MODELO PROBABILÍSTICO", "La combinación de indicadores mejora la filtración de falsos positivos, pero no elimina el riesgo. Los mercados pueden comportarse de manera irracional."),
            ("02", "STRESS TEST SON SIMULACIONES", "Los escenarios presentados son hipotéticos. Las probabilidades asignadas son estimaciones subjetivas basadas en eventos históricos similares."),
            ("03", "ALERTAS PROGRESIVAS NO SON SEÑALES DE TRADING", "Las alertas de proximidad a zonas son informativas. No garantizan que el precio alcance dichos niveles."),
            ("04", "CURVATURA MA200 ES REZAGADA", "La detección de tendencia usa medias móviles de 30 días sobre la MA200W, lo que introduce retraso en la señal."),
            ("05", "ESTO NO ES ASESORAMIENTO FINANCIERO", "Nunca inviertas más de lo que puedas permitirte perder."),
        ]
        for num, title, desc in risks:
            st.markdown(f"""
            <div class="risk-box" style="margin-bottom: 10px;">
                <div style="font-family: 'VT323', monospace; color: {COLORS['accent_red']}; font-size: 0.8rem; letter-spacing: 3px; margin-bottom: 4px;">{num} //</div>
                <div style="font-family: 'VT323', monospace; color: {COLORS['accent_orange']}; font-size: 1.1rem; letter-spacing: 2px; margin-bottom: 6px;">{title}</div>
                <div style="font-family: 'Courier New', monospace; color: {COLORS['text_dim']}; font-size: 0.85rem; line-height: 1.6;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ───────────────────────────────────────────────────────────────────────────────

def main():
    # CSS Global — RSU Terminal v3 (roadmap_2026 fusion)
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

    .stApp {{
        background: {COLORS['bg_dark']};
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: 'VT323', monospace !important;
        color: {COLORS['accent_green']} !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    h1 {{
        font-size: 3.2rem !important;
        text-shadow: 0 0 20px {hex_to_rgba(COLORS['accent_green'], 0.4)};
        border-bottom: 2px solid {COLORS['accent_green']};
        padding-bottom: 15px;
    }}
    h2 {{
        font-size: 2rem !important;
        color: {COLORS['accent_cyan']} !important;
        border-left: 4px solid {COLORS['accent_green']};
        padding-left: 15px;
        margin-top: 30px !important;
    }}
    h3 {{
        font-size: 1.6rem !important;
        color: {COLORS['accent_orange']} !important;
    }}

    p, li {{
        font-family: 'Courier New', monospace;
        color: {COLORS['text']} !important;
        line-height: 1.8;
    }}

    strong {{
        color: {COLORS['accent_green']};
    }}

    hr {{
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, {COLORS['accent_green']}, transparent);
        margin: 30px 0;
    }}

    /* Clases reutilizadas de roadmap_2026 */
    .terminal-box {{
        background: linear-gradient(135deg, {COLORS['bg_dark']} 0%, {COLORS['bg_panel']} 100%);
        border: 1px solid {hex_to_rgba(COLORS['accent_green'], 0.27)};
        border-radius: 8px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 0 15px {hex_to_rgba(COLORS['accent_green'], 0.07)};
    }}

    .phase-box {{
        background: {COLORS['bg_dark']};
        border-left: 3px solid {COLORS['accent_green']};
        padding: 20px;
        margin: 15px 0;
        border-radius: 0 8px 8px 0;
    }}

    .highlight-quote {{
        background: {hex_to_rgba(COLORS['accent_green'], 0.07)};
        border: 1px solid {hex_to_rgba(COLORS['accent_green'], 0.2)};
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
        font-family: 'VT323', monospace;
        font-size: 1.2rem;
        color: {COLORS['accent_green']};
        text-align: center;
        letter-spacing: 1px;
    }}

    .risk-box {{
        background: linear-gradient(135deg, #1a0f0f 0%, #261a1a 100%);
        border: 1px solid {hex_to_rgba(COLORS['accent_red'], 0.27)};
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {COLORS['bg_panel']};
        padding: 10px;
        border-radius: 8px;
        border: 1px solid {hex_to_rgba(COLORS['accent_green'], 0.15)};
    }}
    .stTabs [data-baseweb="tab"] {{
        background: {COLORS['bg_dark']};
        color: {COLORS['text_dim']};
        border: 1px solid {COLORS['grid']};
        border-radius: 4px;
        padding: 10px 20px;
        font-family: 'VT323', monospace;
        text-transform: uppercase;
        font-size: 1rem;
        letter-spacing: 2px;
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLORS['bg_panel']};
        color: {COLORS['accent_green']} !important;
        border: 1px solid {COLORS['accent_green']};
        box-shadow: 0 0 10px {hex_to_rgba(COLORS['accent_green'], 0.3)};
        font-family: 'VT323', monospace;
    }}

    /* Botones */
    .stButton>button {{
        background: {COLORS['bg_panel']};
        color: {COLORS['accent_green']};
        border: 1px solid {COLORS['accent_green']};
        border-radius: 4px;
        font-family: 'VT323', monospace;
        text-transform: uppercase;
        letter-spacing: 3px;
        font-size: 1rem;
        transition: all 0.2s ease;
    }}
    .stButton>button:hover {{
        background: {COLORS['accent_green']};
        color: {COLORS['bg_dark']};
        box-shadow: 0 0 20px {hex_to_rgba(COLORS['accent_green'], 0.5)};
    }}

    /* Inputs */
    .stTextInput>div>div>input {{
        background: {COLORS['bg_panel']};
        color: {COLORS['accent_green']};
        border: 1px solid {COLORS['grid']};
        font-family: 'VT323', monospace;
        font-size: 1.1rem;
        letter-spacing: 2px;
    }}

    /* Métricas */
    [data-testid="metric-container"] {{
        background: {COLORS['bg_panel']};
        border: 1px solid {COLORS['grid']};
        border-radius: 8px;
        padding: 15px;
    }}
    [data-testid="metric-container"] label {{
        font-family: 'VT323', monospace !important;
        color: {COLORS['text_dim']} !important;
        letter-spacing: 2px;
        font-size: 0.9rem !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 40px; padding: 30px 20px;">
        <div style="font-family: 'VT323', monospace; font-size: 0.95rem; color: {COLORS['text_dim']}; margin-bottom: 12px; letter-spacing: 3px;">
            [SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]
        </div>
        <div style="font-size: 56px; margin-bottom: 5px; filter: drop-shadow(0 0 15px {hex_to_rgba(COLORS['accent_green'], 0.5)});">₿</div>
        <h1 style="margin: 10px 0; font-size: 3rem; font-family: 'VT323', monospace; letter-spacing: 4px;">
            RSU BITCOIN MODEL v2.1
        </h1>
        <div style="font-family: 'VT323', monospace; color: {COLORS['accent_cyan']}; font-size: 1.1rem; letter-spacing: 3px; margin-top: 8px;">
            PROTOCOLO DE ACUMULACIÓN MULTI-INDICADOR // CICLO HALVING INTEGRADO
        </div>
        <div style="height: 1px; background: linear-gradient(90deg, transparent, {COLORS['accent_green']}, transparent); margin-top: 25px;"></div>
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
            with st.spinner("Calculando RSU Score, alertas y escenarios de stress..."):
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
                    
                    # NUEVO: Calcular alertas progresivas
                    alerts = calculate_progressive_alerts(data, zone_data)
                    
                    # NUEVO: Calcular stress test
                    stress_data = run_stress_tests(data, zone_data)
                    
                    # Dashboard RSU Principal
                    render_rsu_dashboard(zone_data, macro_data, halving_data)
                    
                    # NUEVO: Panel de alertas progresivas
                    render_alerts_panel(alerts)
                    
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
                    
                    # NUEVO: Panel de Stress Test
                    render_stress_test_panel(stress_data)
                    
                    # Niveles de zona clásicos
                    render_zone_levels(zone_data)
                    
                    # Panel clásico para referencia
                    with st.expander("📊 Zonas Clásicas MA200 (Referencia)", expanded=False):
                        render_status_panel(zone_data)
                    
                    # Detalles técnicos
                    with st.expander("🔬 ESPECIFICACIONES TÉCNICAS RSU", expanded=False):
                        rsu = zone_data['rsu_score']
                        ma_curv = calculate_ma_curvature(data)
                        st.code(f"""
╔══════════════════════════════════════════════════════════════════╗
║                    RSU SCORE BREAKDOWN v2.1                      ║
╠══════════════════════════════════════════════════════════════════╣
  ACTIVO: {symbol}
  RANGO:  {data.index[0].strftime('%Y-%m-%d')} a {data.index[-1].strftime('%Y-%m-%d')}
  
┌─ INDICADORES ON-CHAIN ─────────────────────────────────────────┐
│ MA 200S (40%):     Score {rsu['components']['ma200']['score']:.1f} | Raw: {rsu['components']['ma200']['raw']:.3f}
│ MVRV Z (30%):      Score {rsu['components']['mvrv']['score']:.1f} | Raw: {rsu['components']['mvrv']['raw']:.3f}
│ Puell (20%):       Score {rsu['components']['puell']['score']:.1f} | Raw: {rsu['components']['puell']['raw']:.3f}
│ AHR999 (10%):      Score {rsu['components']['ahr999']['score']:.1f} | Raw: {rsu['components']['ahr999']['raw']:.3f}
└────────────────────────────────────────────────────────────────┘

┌─ ANÁLISIS DE TENDENCIA (MA200W) ───────────────────────────────┐
│ Valor MA200:       ${ma_curv['ma_value']:,.2f}
│ Pendiente:         {ma_curv['slope']:.2f}% (30d)
│ Curvatura:         {ma_curv['curvature']:.4f}
│ Tendencia:         {ma_curv['trend']}
│ Aceleración:       {ma_curv['acceleration']}
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
            ### 📚 Metodología RSU v2.1
            
            **1. RSU Score Compuesto (Ponderado)**
            
            El RSU Score combina múltiples indicadores on-chain probados:
            
            - **MA 200S (40%)**: Tendencia a largo plazo, "piso" histórico de Bitcoin
            - **MVRV Z-Score (30%)**: Valor de mercado vs valor realizado
            - **Puell Multiple (20%)**: Ingresos de mineros
            - **AHR999 (10%)**: Índice específico de acumulación
            
            **2. Alertas Progresivas**
            
            El sistema monitorea continuamente:
            
            - **Proximidad a zonas**: Avisa cuando el precio se acerca a umbrales clave (ej: "A 12% de STRONG_BUY")
            - **Curvatura MA200W**: Detecta cambios en la tendencia de la media móvil larga
            - **Divergencias**: Señala cuando indicadores discrepan (ej: precio bajo pero MVRV saludable)
            - **Niveles históricos**: Alerta de drawdowns significativos desde ATH
            
            **3. Stress Test**
            
            Simulación de escenarios extremos para gestión de expectativas:
            
            - **Top 2017 definitivo**: Si el ciclo actual fracasa
            - **Colapso de exchange**: Evento tipo FTX
            - **Ban regulatorio global**: Prohibición amplia
            - **Ruptura criptográfica**: Ataque cuántico
            - **Estanflación prolongada**: Macro adverso extendido
            
            Cada escenario incluye: probabilidad estimada, P&L proyectado, y estrategia de hedge sugerida.
            """)
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(f"""
                **4. Curvatura de MA200W**
                
                Calculada como la segunda derivada de la media móvil:
                
                - **Pendiente > 1%**: Tendencia alcista fuerte
                - **Pendiente 0.2-1%**: Tendencia alcista moderada
                - **Pendiente -0.2 a 0.2**: Lateralización
                - **Pendiente < -0.2%**: Tendencia bajista
                
                **Aceleración positiva**: La tendencia se fortalece
                **Aceleración negativa**: La tendencia se debilita
                
                **5. Ciclo de Halving**
                
                Bitcoin tiene ciclos de ~4 años correlacionados con halvings.
                """)
            with col_m2:
                st.markdown(f"""
                **6. Estrategia de Asignación Dinámica**
                
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
