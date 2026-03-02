
# modules/rsu_algoritmo_pro.py
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import yfinance as yf
import numpy as np
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import set_style

# ─── Constantes ────────────────────────────────────────────────────────────────
SECTOR_ETFS = ['XLK', 'XLF', 'XLV', 'XLY', 'XLP', 'XLI', 'XLB', 'XLRE', 'XLU']
VENTANA_CONDICIONES = 10  # días

# ─── CSS GLOBAL UNIFICADO (estética terminal/hacker de roadmap_2026) ───────────
RSU_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

    /* ── Base ── */
    .stApp { background: #0c0e12; }

    /* ── Tipografía ── */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'VT323', monospace !important;
        color: #00ffad !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    h1 {
        font-size: 3rem !important;
        text-shadow: 0 0 20px #00ffad66;
        border-bottom: 2px solid #00ffad;
        padding-bottom: 12px;
        margin-bottom: 25px !important;
    }
    h2 {
        font-size: 1.6rem !important;
        color: #00d9ff !important;
        border-left: 4px solid #00ffad;
        padding-left: 12px;
        margin-top: 30px !important;
    }
    h3 {
        font-size: 1.3rem !important;
        color: #ff9800 !important;
        margin-top: 20px !important;
    }
    p, li {
        font-family: 'Courier New', monospace;
        color: #ccc !important;
        line-height: 1.7;
        font-size: 0.92rem;
    }
    strong { color: #00ffad; }
    blockquote {
        border-left: 3px solid #ff9800;
        margin: 15px 0;
        padding-left: 15px;
        color: #ff9800 !important;
    }

    /* ── Layout / Contenedores ── */
    .terminal-box {
        background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
        border: 1px solid #00ffad44;
        border-radius: 8px;
        padding: 20px 25px;
        margin: 15px 0;
        box-shadow: 0 0 15px #00ffad11;
    }
    .rsu-box {
        background: #11141a;
        border: 1px solid #1a1e26;
        border-radius: 10px;
        margin-bottom: 20px;
        overflow: hidden;
        box-shadow: 0 0 20px #00ffad08;
    }
    .rsu-head {
        background: #0c0e12;
        padding: 12px 20px;
        border-bottom: 1px solid #00ffad33;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .rsu-title {
        font-family: 'VT323', monospace !important;
        color: #00ffad !important;
        font-size: 1.3rem !important;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin: 0;
    }
    .rsu-body { padding: 20px; }
    .rsu-center { text-align: center; }

    /* ── Semáforo ── */
    .rsu-luz {
        width: 80px; height: 80px;
        border-radius: 50%;
        border: 4px solid #1a1e26;
        background: #0c0e12;
        margin: 10px auto;
        transition: all 0.4s ease;
    }
    .rsu-luz.on { transform: scale(1.15); }
    .rsu-luz.red.on  { background: radial-gradient(circle at 30% 30%, #ff6b6b, #f23645); border-color: #f23645; box-shadow: 0 0 30px #f2364588; }
    .rsu-luz.yel.on  { background: radial-gradient(circle at 30% 30%, #ffb74d, #ff9800); border-color: #ff9800; box-shadow: 0 0 30px #ff980088; }
    .rsu-luz.grn.on  { background: radial-gradient(circle at 30% 30%, #69f0ae, #00ffad); border-color: #00ffad; box-shadow: 0 0 30px #00ffad88; }

    /* ── Score ── */
    .score-big {
        font-family: 'VT323', monospace;
        font-size: 4.5rem;
        font-weight: bold;
        color: white;
        text-align: center;
        margin: 8px 0;
        line-height: 1;
    }
    .score-label {
        color: #555;
        font-size: 10px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-family: 'Courier New', monospace;
    }

    /* ── Badge de señal ── */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 20px;
        border-radius: 20px;
        font-family: 'VT323', monospace;
        font-weight: bold;
        font-size: 1.3rem;
        letter-spacing: 2px;
        margin-top: 12px;
    }

    /* ── Métricas de medias móviles ── */
    .metric-card {
        background: #0c0e12;
        border: 1px solid #1a1e26;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        transition: border-color 0.3s;
    }
    .metric-card:hover { border-color: #00ffad44; }
    .metric-value { font-family: 'VT323', monospace; font-size: 1.6rem; color: white; }
    .metric-label { font-family: 'Courier New', monospace; font-size: 0.75rem; color: #555; margin-top: 4px; }

    /* ── Ventana badge ── */
    .ventana-badge {
        display: inline-block;
        background: #00ffad18;
        color: #00ffad;
        border: 1px solid #00ffad44;
        padding: 3px 10px;
        border-radius: 12px;
        font-family: 'Courier New', monospace;
        font-size: 11px;
        margin-left: 10px;
        letter-spacing: 1px;
    }

    /* ── Recomendación ── */
    .recommendation-box {
        background: rgba(0, 255, 173, 0.04);
        border-left: 4px solid #00ffad;
        padding: 15px 20px;
        margin-top: 20px;
        border-radius: 0 8px 8px 0;
        font-family: 'Courier New', monospace;
    }
    .rec-label {
        font-family: 'VT323', monospace;
        color: #00ffad;
        font-size: 1.1rem;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }

    /* ── Advertencias ── */
    .warning-box {
        background: rgba(255, 152, 0, 0.08);
        border-left: 3px solid #ff9800;
        padding: 9px 14px;
        margin: 6px 0;
        border-radius: 0 5px 5px 0;
        font-family: 'Courier New', monospace;
        font-size: 11.5px;
        color: #ff9800;
    }
    .warning-box.danger {
        background: rgba(242, 54, 69, 0.08);
        border-left-color: #f23645;
        color: #f23645;
    }

    /* ── Detalles técnicos ── */
    .detail-item {
        padding: 7px 0;
        border-bottom: 1px solid #1a1e26;
        font-family: 'Courier New', monospace;
        font-size: 12.5px;
    }
    .detail-item:last-child { border-bottom: none; }

    /* ── Separador ── */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #00ffad55, transparent);
        margin: 35px 0;
    }

    /* ── Factor bars (para components.html) ── */
    /* (Se define también en el HTML embebido) */
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CÁLCULO (sin cambios)
# ══════════════════════════════════════════════════════════════════════════════

def calcular_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def detectar_divergencia_bullish(df, lookback=30):
    """Detecta divergencia alcista regular: precio lower low, RSI higher low. +15 pts."""
    if len(df) < lookback + 14:
        return 0, None

    rsi = calcular_rsi(df['Close'], 14)
    price = df['Close'].iloc[-lookback:]
    rsi_series = rsi.iloc[-lookback:]

    price_lows, rsi_lows = [], []
    for i in range(2, len(price)-2):
        if price.iloc[i] == price.iloc[i-2:i+3].min() and price.iloc[i] < price.iloc[i-1] and price.iloc[i] < price.iloc[i+1]:
            price_lows.append((i, price.iloc[i]))
        if rsi_series.iloc[i] == rsi_series.iloc[i-2:i+3].min() and rsi_series.iloc[i] < rsi_series.iloc[i-1] and rsi_series.iloc[i] < rsi_series.iloc[i+1]:
            rsi_lows.append((i, rsi_series.iloc[i]))

    if len(price_lows) >= 2 and len(rsi_lows) >= 2:
        last_price_low, prev_price_low = price_lows[-1], price_lows[-2]
        last_rsi_low, prev_rsi_low = rsi_lows[-1], rsi_lows[-2]
        if last_price_low[1] < prev_price_low[1] and last_rsi_low[1] > prev_rsi_low[1]:
            return 15, {
                'tipo': 'Bullish Regular',
                'precio_prev': prev_price_low[1],
                'precio_last': last_price_low[1],
                'rsi_prev': prev_rsi_low[1],
                'rsi_last': last_rsi_low[1],
                'bonus': 15
            }
    return 0, None


def calcular_mcclellan_proxy_mejorado(df_spy, sector_data=None):
    """McClellan Proxy mejorado usando sectores + SPY con fallback."""
    if df_spy is None or len(df_spy) < 50:
        return None, "Datos insuficientes"

    if sector_data and len(sector_data) > 0:
        try:
            sector_returns = {}
            valid_sectors = 0
            for sector, df in sector_data.items():
                if df is not None and len(df) > 1:
                    sector_returns[sector] = df['Close'].pct_change()
                    valid_sectors += 1

            if valid_sectors >= 3:
                returns_df = pd.DataFrame(sector_returns)
                advancers = (returns_df > 0).sum(axis=1)
                decliners = (returns_df < 0).sum(axis=1)
                total = (advancers + decliners).replace(0, np.nan)
                net_advances = ((advancers - decliners) / total) * 1000
                ema_19 = net_advances.ewm(span=19, adjust=False).mean()
                ema_39 = net_advances.ewm(span=39, adjust=False).mean()
                mcclellan = ema_19 - ema_39
                valor_actual = mcclellan.iloc[-1] if not pd.isna(mcclellan.iloc[-1]) else 0
                return valor_actual, f"Amplitud sectorial ({valid_sectors} ETFs)"
        except Exception:
            pass

    # Fallback SPY
    returns = df_spy['Close'].pct_change()
    advancers = (returns > 0).rolling(window=19).sum()
    decliners = (returns < 0).rolling(window=19).sum()
    total = (advancers + decliners).replace(0, np.nan)
    net_advances = ((advancers - decliners) / total) * 1000
    ema_19 = net_advances.ewm(span=19, adjust=False).mean()
    ema_39 = net_advances.ewm(span=39, adjust=False).mean()
    mcclellan = ema_19 - ema_39
    valor_actual = mcclellan.iloc[-1] if not pd.isna(mcclellan.iloc[-1]) else 0
    return valor_actual, "Proxy SPY (fallback)"


def calcular_medias_moviles(df):
    """Calcula SMA 50, 200 y EMA 21."""
    sma_50  = df['Close'].rolling(window=50, min_periods=50).mean().iloc[-1] if len(df) >= 50 else df['Close'].mean()
    sma_200 = df['Close'].rolling(window=200, min_periods=200).mean().iloc[-1] if len(df) >= 200 else df['Close'].mean()
    ema_21  = df['Close'].ewm(span=21, adjust=False, min_periods=21).mean().iloc[-1] if len(df) >= 21 else df['Close'].mean()
    return {'sma_50': sma_50, 'sma_200': sma_200, 'ema_21': ema_21, 'price': df['Close'].iloc[-1]}


def calcular_atr(df, periodo=14):
    """Average True Range."""
    high, low, close = df['High'], df['Low'], df['Close']
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    return tr.rolling(window=periodo).mean()


def verificar_ftd_follow_through(df, ftd_idx, dias_verificacion=3):
    if ftd_idx is None or ftd_idx >= len(df) - 1:
        return True
    precio_ftd_max = df['High'].iloc[ftd_idx]
    dias_disponibles = min(dias_verificacion, len(df) - ftd_idx - 1)
    for i in range(1, dias_disponibles + 1):
        if df['High'].iloc[ftd_idx + i] > precio_ftd_max:
            return True
    return False


def detectar_follow_through_day(df_daily):
    """FTD detection con índice de retorno."""
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
        return {'estado': 'NO_CONTEXT', 'signal': None, 'dias_rally': 0, 'index': None}

    min_idx_pos = recent.index.get_loc(recent_low_idx)
    if min_idx_pos >= len(recent) - 2:
        return {'estado': 'RALLY_TOO_RECENT', 'signal': None, 'dias_rally': 0, 'index': None}

    post_low = recent.iloc[min_idx_pos:].copy()
    rally_start_idx = next((i for i in range(1, len(post_low)) if post_low['price_up'].iloc[i]), None)
    if rally_start_idx is None:
        return {'estado': 'NO_RALLY', 'signal': None, 'dias_rally': 0, 'index': None}

    dias_rally = len(post_low) - rally_start_idx
    low_dia_1 = post_low.iloc[rally_start_idx]['Low']
    for i in range(rally_start_idx + 1, len(post_low)):
        if post_low.iloc[i]['Low'] < low_dia_1:
            return {'estado': 'RALLY_FAILED', 'signal': 'invalidated', 'dias_rally': dias_rally, 'index': None}

    if 4 <= dias_rally <= 10:
        ultimo_dia = post_low.iloc[-1]
        ret_ultimo = ultimo_dia['returns'] * 100
        if ret_ultimo >= 1.5 and ultimo_dia['volume_increase']:
            idx_real = df.index.get_loc(post_low.index[-1])
            return {
                'estado': 'FTD_CONFIRMED', 'signal': 'confirmed',
                'dias_rally': dias_rally, 'retorno': ret_ultimo,
                'color': '#00ffad', 'index': idx_real, 'date': post_low.index[-1]
            }

    if dias_rally < 4:
        return {'estado': 'RALLY_EARLY', 'signal': 'early', 'dias_rally': dias_rally, 'index': None}
    return {'estado': 'RALLY_ACTIVE', 'signal': 'active', 'dias_rally': dias_rally, 'index': None}


def detectar_fondo_comprehensivo(df_spy, df_vix=None, sector_data=None):
    """Sistema de detección de fondos multi-factor V2.1 – MÁS PERMISIVO."""
    score = 0
    max_score = 100
    detalles, advertencias = [], []
    metricas = {}

    mm = calcular_medias_moviles(df_spy)
    price = mm['price']

    # 1. Divergencia Bullish (+15)
    div_score, div_data = detectar_divergencia_bullish(df_spy)
    if div_score > 0:
        score += div_score
        detalles.append(f"✓ Divergencia Alcista detectada (+{div_score})")
        metricas['Divergencia'] = {'score': div_score, 'max': 15, 'color': '#ffd700', 'raw_value': div_data}
    else:
        detalles.append("• Sin divergencia detectada (0)")
        metricas['Divergencia'] = {'score': 0, 'max': 15, 'color': '#ffd700'}

    # 2. FTD Detection (+35)
    ftd_data = detectar_follow_through_day(df_spy)
    ftd_score, ftd_idx = 0, None
    if ftd_data:
        if ftd_data.get('signal') == 'confirmed':
            ftd_score = 35
            ftd_idx = ftd_data.get('index')
            detalles.append("✓ FTD Confirmado (+35)")
            if price < mm['ema_21']:
                advertencias.append("⚠️ FTD bajo EMA21 – Posible trampa para toros")
            if ftd_idx and not verificar_ftd_follow_through(df_spy, ftd_idx, 3):
                advertencias.append("⚠️ FTD sin seguimiento en 3 días – Confirmación débil")
        elif ftd_data.get('signal') in ['potential', 'early']:
            ftd_score = 15
            detalles.append("~ FTD en desarrollo (+15)")
        elif ftd_data.get('signal') == 'active':
            ftd_score = 5
            detalles.append("• Rally activo sin FTD (+5)")
        else:
            detalles.append("✗ Sin FTD (0)")
    else:
        detalles.append("✗ Sin datos FTD (0)")
    score += ftd_score
    metricas['FTD'] = {'score': max(0, ftd_score), 'max': 35, 'color': '#2962ff', 'raw_value': ftd_data}

    # 3. RSI (+15, ventana 10d)
    rsi_series = calcular_rsi(df_spy['Close'], 14)
    rsi_ventana = rsi_series.tail(VENTANA_CONDICIONES)
    rsi_minimo = rsi_ventana.min()
    rsi_actual = rsi_series.iloc[-1]
    rsi_fecha_min = rsi_ventana.idxmin()
    rsi_score = 0
    if rsi_minimo < 25:
        rsi_score = 15; detalles.append(f"✓ RSI mínimo {rsi_minimo:.1f} < 25 en últimos {VENTANA_CONDICIONES}d (+15)")
    elif rsi_minimo < 35:
        rsi_score = 12; detalles.append(f"✓ RSI mínimo {rsi_minimo:.1f} < 35 en últimos {VENTANA_CONDICIONES}d (+12)")
    elif rsi_minimo < 45:
        rsi_score = 5;  detalles.append(f"~ RSI mínimo {rsi_minimo:.1f} < 45 en últimos {VENTANA_CONDICIONES}d (+5)")
    elif rsi_actual > 75:
        rsi_score = -5; detalles.append(f"✗ RSI actual {rsi_actual:.1f} > 75 (Sobrecompra) (-5)")
    else:
        detalles.append("• RSI en rango neutral (0)")
    score += rsi_score
    metricas['RSI'] = {
        'score': max(0, rsi_score), 'max': 15, 'color': '#00ffad', 'raw_value': rsi_actual,
        'minimo_reciente': rsi_minimo,
        'fecha_minimo': rsi_fecha_min.strftime('%Y-%m-%d') if pd.notna(rsi_fecha_min) else 'N/A'
    }

    # 4. VIX / Volatilidad (+20, ventana 10d)
    vix_score = 0
    if df_vix is not None and len(df_vix) > 20:
        vix_ventana = df_vix['Close'].tail(VENTANA_CONDICIONES)
        vix_maximo = vix_ventana.max()
        vix_actual = df_vix['Close'].iloc[-1]
        vix_fecha_max = vix_ventana.idxmax()
        if vix_maximo > 35:
            vix_score = 20; detalles.append(f"✓ VIX máx {vix_maximo:.1f} > 35 en últimos {VENTANA_CONDICIONES}d (+20)")
        elif vix_maximo > 30:
            vix_score = 15; detalles.append(f"✓ VIX máx {vix_maximo:.1f} > 30 en últimos {VENTANA_CONDICIONES}d (+15)")
        elif vix_maximo > 25:
            vix_score = 10; detalles.append(f"~ VIX máx {vix_maximo:.1f} > 25 en últimos {VENTANA_CONDICIONES}d (+10)")
        else:
            detalles.append("• VIX sin spike significativo (0)")
        if score > 50 and vix_actual < 20:
            advertencias.append(f"⚠️ VIX actual bajo ({vix_actual:.1f}) – Posible complacencia post-pánico")
        metricas['VIX'] = {
            'score': vix_score, 'max': 20, 'color': '#ff9800', 'raw_value': vix_actual,
            'maximo_reciente': vix_maximo,
            'fecha_maximo': vix_fecha_max.strftime('%Y-%m-%d') if pd.notna(vix_fecha_max) else 'N/A'
        }
    else:
        atr = calcular_atr(df_spy).iloc[-1]
        atr_medio = calcular_atr(df_spy).rolling(20).mean().iloc[-1]
        ratio_atr = atr / atr_medio if atr_medio > 0 else 1
        atr_series = calcular_atr(df_spy)
        atr_ventana = atr_series.tail(VENTANA_CONDICIONES)
        atr_max = atr_ventana.max()
        atr_medio_ventana = atr_series.rolling(20).mean().tail(VENTANA_CONDICIONES).mean()
        ratio_max = atr_max / atr_medio_ventana if atr_medio_ventana > 0 else 1
        if ratio_max > 2.0:
            vix_score = 15; detalles.append(f"~ ATR máx {ratio_max:.1f}x normal en {VENTANA_CONDICIONES}d (+15)")
        elif ratio_max > 1.5:
            vix_score = 10; detalles.append(f"~ ATR máx {ratio_max:.1f}x normal en {VENTANA_CONDICIONES}d (+10)")
        else:
            detalles.append("• Volatilidad normal (0)")
        metricas['VIX'] = {
            'score': vix_score, 'max': 20, 'color': '#ff9800',
            'raw_value': ratio_atr, 'is_proxy': True, 'maximo_reciente': ratio_max
        }
    score += vix_score

    # 5. McClellan (+20)
    mcclellan, metodo = calcular_mcclellan_proxy_mejorado(df_spy, sector_data)
    mcclellan_valor = mcclellan.iloc[-1] if hasattr(mcclellan, 'iloc') else (mcclellan or 0)
    breadth_score = 0
    if mcclellan_valor < -80:
        breadth_score = 20; detalles.append(f"✓ McClellan {mcclellan_valor:.0f} < -80 (Oversold extremo) (+20) [{metodo}]")
    elif mcclellan_valor < -50:
        breadth_score = 15; detalles.append(f"~ McClellan {mcclellan_valor:.0f} < -50 (Oversold) (+15) [{metodo}]")
    elif mcclellan_valor < -20:
        breadth_score = 5;  detalles.append(f"• McClellan {mcclellan_valor:.0f} < -20 (Débil) (+5) [{metodo}]")
    else:
        detalles.append(f"• McClellan {mcclellan_valor:.0f} neutral (0) [{metodo}]")
    score += breadth_score
    metricas['Breadth'] = {'score': breadth_score, 'max': 20, 'color': '#9c27b0', 'raw_value': mcclellan_valor, 'metodo': metodo}

    # 6. Volume (+10, ventana 10d)
    vol_ventana = df_spy['Volume'].tail(VENTANA_CONDICIONES)
    vol_maximo = vol_ventana.max()
    vol_media = df_spy['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio_max = vol_maximo / vol_media if vol_media > 0 else 1
    vol_actual = df_spy['Volume'].iloc[-1]
    vol_ratio_actual = vol_actual / vol_media if vol_media > 0 else 1
    vol_score = 0
    if vol_ratio_max > 2.0:
        vol_score = 10; detalles.append(f"✓ Volumen máx {vol_ratio_max:.1f}x media (Capitulación) (+10)")
    elif vol_ratio_max > 1.5:
        vol_score = 7;  detalles.append(f"~ Volumen máx {vol_ratio_max:.1f}x media (Alto) (+7)")
    elif vol_ratio_max > 1.2:
        vol_score = 3;  detalles.append(f"• Volumen máx {vol_ratio_max:.1f}x media (+3)")
    else:
        detalles.append("• Volumen sin spike significativo (0)")
    score += vol_score
    metricas['Volume'] = {
        'score': vol_score, 'max': 10, 'color': '#f23645',
        'raw_value': vol_ratio_actual, 'maximo_reciente': vol_ratio_max
    }

    # 7. SMA200 contexto (sin penalización)
    if price < mm['sma_200']:
        distancia_sma200 = (price - mm['sma_200']) / mm['sma_200'] * 100
        advertencias.append(f"⚠️ Precio {distancia_sma200:.1f}% bajo SMA200 – Fondo en mercado bajista")
        detalles.append("• Bajo SMA200 (Contexto: Mercado bajista)")
    else:
        detalles.append("• Sobre SMA200 (Contexto: Tendencia alcista)")

    metricas['SMA200'] = {
        'score': 0, 'max': 0,
        'color': '#ff9800' if price < mm['sma_200'] else '#00ffad',
        'raw_value': price - mm['sma_200'],
        'distancia_pct': (price - mm['sma_200']) / mm['sma_200'] * 100 if mm['sma_200'] != 0 else 0,
        'advertencia': price < mm['sma_200']
    }
    if price < mm['ema_21']:
        advertencias.append("📉 Precio bajo EMA21 – Resistencia dinámica cercana")

    # Estado final
    volumen_confirmado = vol_score >= 3
    if score >= 70:
        if volumen_confirmado:
            estado, senal, color = "VERDE", "FONDO PROBABLE", "#00ffad"
            recomendacion = (f"Setup óptimo detectado. Score: {score}/100. " +
                             (f"⚠️ {len(advertencias)} advertencia(s): Revisar antes de entrar." if advertencias
                              else "Múltiples factores alineados. Entrada gradual (25%) con stop -7%."))
        else:
            estado, senal, color = "VERDE-VOL", "SETUP SIN VOLUMEN", "#00ffad"
            recomendacion = f"Score alto ({score}) pero volumen insuficiente. Reducir posición (10-15%)."
    elif score >= 50:
        estado, senal, color = "AMBAR", "DESARROLLANDO", "#ff9800"
        recomendacion = "Condiciones mejorando. Preparar watchlist o entrada parcial (10-15%)."
    elif score >= 30:
        estado, senal, color = "AMBAR-BAJO", "PRE-SETUP", "#ff9800"
        recomendacion = "Algunos factores presentes pero insuficientes. Mantener liquidez."
    else:
        estado, senal, color = "ROJO", "SIN FONDO", "#f23645"
        recomendacion = "Sin condiciones de fondo detectadas. Preservar capital."

    return {
        'score': score, 'max_score': max_score, 'estado': estado, 'senal': senal,
        'color': color, 'recomendacion': recomendacion, 'detalles': detalles,
        'advertencias': advertencias, 'ftd_data': ftd_data, 'metricas': metricas,
        'medias_moviles': mm, 'divergencia_data': div_data, 'ventana_dias': VENTANA_CONDICIONES
    }


def calcular_max_drawdown(precios, precio_entrada):
    if len(precios) < 2:
        return 0.0
    running_max = precios.expanding().max()
    drawdowns = (precios - running_max) / running_max * 100
    max_dd = drawdowns.min()
    return max_dd if max_dd < 0 else 0.0


def descargar_datos_sectores():
    sector_data = {}
    with st.spinner('🔄 Cargando datos sectoriales para análisis de amplitud...'):
        for etf in SECTOR_ETFS:
            try:
                df = yf.Ticker(etf).history(period="3mo", interval="1d")
                if not df.empty:
                    sector_data[etf] = df
            except Exception:
                continue
    return sector_data


def backtest_strategy(ticker_symbol="SPY", years=2, umbral_señal=50, usar_sectores=False):
    """Backtesting robusto con umbral configurable, drawdown y win rates 5/20/60d."""
    try:
        df_hist = yf.Ticker(ticker_symbol).history(period=f"{years}y", interval="1d")
        if df_hist.empty or len(df_hist) < 100:
            return None, "Datos insuficientes"
        try:
            vix_hist = yf.Ticker("^VIX").history(period=f"{years}y", interval="1d")
        except Exception:
            vix_hist = None

        sectores_hist = {}
        if usar_sectores:
            st.info("Modo preciso: Descargando datos sectoriales...")
            for etf in SECTOR_ETFS:
                try:
                    sectores_hist[etf] = yf.Ticker(etf).history(period=f"{years}y", interval="1d")
                except Exception:
                    continue

        señales = []
        for i in range(60, len(df_hist) - 60):
            ventana_df = df_hist.iloc[:i]
            vix_window = vix_hist.iloc[:i] if vix_hist is not None else None
            sector_window = None
            if usar_sectores and sectores_hist:
                sector_window = {etf: df_sec.iloc[:i] for etf, df_sec in sectores_hist.items() if len(df_sec) >= i}

            resultado = detectar_fondo_comprehensivo(ventana_df, vix_window, sector_window)
            if resultado['score'] >= umbral_señal:
                pe = df_hist['Close'].iloc[i]
                ps5  = df_hist['Close'].iloc[min(i+5,  len(df_hist)-1)]
                ps10 = df_hist['Close'].iloc[min(i+10, len(df_hist)-1)]
                ps20 = df_hist['Close'].iloc[min(i+20, len(df_hist)-1)]
                ps60 = df_hist['Close'].iloc[min(i+60, len(df_hist)-1)]
                r5  = (ps5  - pe) / pe * 100
                r10 = (ps10 - pe) / pe * 100
                r20 = (ps20 - pe) / pe * 100
                r60 = (ps60 - pe) / pe * 100
                precios_60d = df_hist['Close'].iloc[i:min(i+61, len(df_hist))]
                max_dd = calcular_max_drawdown(precios_60d, pe)
                señales.append({
                    'fecha': df_hist.index[i].strftime('%Y-%m-%d'),
                    'score': resultado['score'], 'estado': resultado['estado'],
                    'advertencias': len(resultado['advertencias']),
                    'precio_entrada': round(pe, 2),
                    'retorno_5d':  round(r5,  2), 'retorno_10d': round(r10, 2),
                    'retorno_20d': round(r20, 2), 'retorno_60d': round(r60, 2),
                    'max_drawdown_60d': round(max_dd, 2),
                    'exito_5d': r5>0, 'exito_10d': r10>0, 'exito_20d': r20>0, 'exito_60d': r60>0,
                    'umbral_usado': umbral_señal
                })

        if not señales:
            return None, f"No se generaron señales con score >= {umbral_señal}"

        df_res = pd.DataFrame(señales)
        metricas = {
            'total_señales': len(señales), 'umbral_aplicado': umbral_señal,
            'score_promedio': df_res['score'].mean(),
            'win_rate_5d':  df_res['exito_5d'].mean()  * 100,
            'win_rate_10d': df_res['exito_10d'].mean() * 100,
            'win_rate_20d': df_res['exito_20d'].mean() * 100,
            'win_rate_60d': df_res['exito_60d'].mean() * 100,
            'retorno_medio_5d':  df_res['retorno_5d'].mean(),
            'retorno_medio_10d': df_res['retorno_10d'].mean(),
            'retorno_medio_20d': df_res['retorno_20d'].mean(),
            'retorno_medio_60d': df_res['retorno_60d'].mean(),
            'retorno_total_20d': df_res['retorno_20d'].sum(),
            'retorno_total_60d': df_res['retorno_60d'].sum(),
            'max_drawdown_promedio': df_res['max_drawdown_60d'].mean(),
            'peor_drawdown': df_res['max_drawdown_60d'].min(),
            'mejor_señal': df_res.loc[df_res['retorno_20d'].idxmax()].to_dict() if len(df_res) > 0 else None,
            'peor_señal':  df_res.loc[df_res['retorno_20d'].idxmin()].to_dict() if len(df_res) > 0 else None,
            'detalle': df_res
        }
        return metricas, None
    except Exception as e:
        return None, f"Error en backtest: {str(e)}"


def crear_grafico_acumulacion(df, resultado):
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        ventana = min(60, len(df))
        scores_historicos, fechas = [], []
        for i in range(ventana, 0, -1):
            idx = len(df) - i
            ventana_df = df.iloc[:idx]
            rsi = calcular_rsi(ventana_df['Close'], 14).iloc[-1]
            vol_ratio = ventana_df['Volume'].iloc[-1] / ventana_df['Volume'].rolling(20).mean().iloc[-1]
            score_simple = (40 if rsi < 35 else 20 if rsi < 45 else 0) + (20 if vol_ratio > 1.5 else 0)
            scores_historicos.append(score_simple)
            fechas.append(df.index[idx])

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])

        fig.add_trace(go.Candlestick(
            x=df.index[-ventana:],
            open=df['Open'].iloc[-ventana:], high=df['High'].iloc[-ventana:],
            low=df['Low'].iloc[-ventana:],   close=df['Close'].iloc[-ventana:],
            name='SPY', increasing_line_color='#00ffad', decreasing_line_color='#f23645'
        ), row=1, col=1)

        for i, (fecha, score) in enumerate(zip(fechas, scores_historicos)):
            if score >= 70:
                fig.add_vrect(
                    x0=fecha, x1=df.index[min(len(df)-ventana+i+1, len(df)-1)],
                    fillcolor="rgba(0, 255, 173, 0.15)", layer="below", line_width=0, row=1, col=1
                )

        ema21  = df['Close'].ewm(span=21).mean()
        sma200 = df['Close'].rolling(window=200).mean()
        fig.add_trace(go.Scatter(x=df.index[-ventana:], y=ema21.iloc[-ventana:],
                                 mode='lines', name='EMA21', line=dict(color='#ff9800', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index[-ventana:], y=sma200.iloc[-ventana:],
                                 mode='lines', name='SMA200', line=dict(color='#f23645', width=1.5, dash='dash')), row=1, col=1)

        colors = ['#00ffad' if df['Close'].iloc[i] > df['Open'].iloc[i] else '#f23645'
                  for i in range(len(df)-ventana, len(df))]
        fig.add_trace(go.Bar(x=df.index[-ventana:], y=df['Volume'].iloc[-ventana:],
                             marker_color=colors, name='Volumen', opacity=0.7), row=2, col=1)

        fig.update_layout(
            title={
                'text': "<span style='font-family:monospace;letter-spacing:2px;'>ZONAS DE ACUMULACIÓN // SCORE > 70</span>",
                'font': dict(color='#00ffad', size=14)
            },
            yaxis_title='Precio ($)', yaxis2_title='Volumen',
            xaxis_rangeslider_visible=False,
            template='plotly_dark',
            paper_bgcolor='#0c0e12', plot_bgcolor='#0c0e12',
            font=dict(color='#888', family='Courier New'),
            showlegend=True, height=600,
            legend=dict(bgcolor='#11141a', bordercolor='#1a1e26', borderwidth=1)
        )
        fig.update_xaxes(gridcolor='#1a1e26', showgrid=True)
        fig.update_yaxes(gridcolor='#1a1e26', showgrid=True)
        return fig
    except Exception as e:
        st.error(f"Error al crear gráfico: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# RENDER PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def render():
    set_style()
    st.markdown(RSU_CSS, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center; margin-bottom:30px;">
        <div style="font-family:'Courier New',monospace; font-size:0.8rem; color:#444; margin-bottom:8px; letter-spacing:2px;">
            [SISTEMA ACTIVO // DETECCIÓN MULTI-FACTOR // v2.1]
        </div>
        <h1>🚦 RSU ALGORITMO PRO</h1>
        <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.1rem; letter-spacing:3px;">
            MOTOR DE DETECCIÓN DE FONDOS
            <span class="ventana-badge">VENTANA: {VENTANA_CONDICIONES} DÍAS</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊 Análisis Actual", "📈 Backtesting", "ℹ️ Metodología"])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: ANÁLISIS ACTUAL
    # ─────────────────────────────────────────────────────────────────────────
    with tab1:
        with st.spinner('🔄 Analizando múltiples factores de mercado...'):
            try:
                df_daily = yf.Ticker("SPY").history(interval="1d", period="6mo")
                try:
                    df_vix = yf.Ticker("^VIX").history(interval="1d", period="6mo")
                except Exception:
                    df_vix = None
                sector_data = descargar_datos_sectores()
                if df_daily.empty:
                    st.error("No se pudieron obtener datos de SPY"); st.stop()
                resultado = detectar_fondo_comprehensivo(df_daily, df_vix, sector_data)
            except Exception as e:
                st.error(f"Error al obtener datos: {e}"); st.stop()

        col_left, col_right = st.columns([1, 1])

        # ── Columna izquierda: Semáforo + Métricas ──
        with col_left:
            luz_r = "on" if resultado['estado'] == "ROJO" else ""
            luz_a = "on" if resultado['estado'] in ["AMBAR", "AMBAR-BAJO"] else ""
            luz_v = "on" if resultado['estado'] in ["VERDE", "VERDE-VOL"] else ""

            st.markdown(f"""
            <div class="rsu-box">
                <div class="rsu-head">
                    <span class="rsu-title">// Señal Integrada</span>
                    <span style="font-family:'VT323',monospace; color:{resultado['color']}; font-size:1rem; letter-spacing:2px;">
                        ● {resultado['estado']}
                    </span>
                </div>
                <div class="rsu-body rsu-center">
                    <div class="rsu-luz red {luz_r}"></div>
                    <div class="rsu-luz yel {luz_a}"></div>
                    <div class="rsu-luz grn {luz_v}"></div>
                    <div class="score-big" style="color:{resultado['color']}; text-shadow: 0 0 25px {resultado['color']}66;">
                        {resultado['score']}
                    </div>
                    <div class="score-label">PUNTUACIÓN DE CONFIANZA // MÁX {resultado['max_score']}</div>
                    <div class="badge" style="background:{resultado['color']}18; border:2px solid {resultado['color']}; color:{resultado['color']}; margin-top:12px;">
                        {resultado['senal']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Medias móviles
            mm = resultado['medias_moviles']
            col_mm1, col_mm2, col_mm3 = st.columns(3)
            def _mm_card(col, valor, label, price, nombre):
                dist = (price - valor) / valor * 100 if valor != 0 else 0
                color = '#00ffad' if price > valor else '#f23645'
                col.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:{color};">{valor:.1f}</div>
                    <div class="metric-label">{nombre} ({dist:+.1f}%)</div>
                </div>
                """, unsafe_allow_html=True)
            _mm_card(col_mm1, mm['ema_21'],  "ema21",  mm['price'], "EMA 21")
            _mm_card(col_mm2, mm['sma_50'],  "sma50",  mm['price'], "SMA 50")
            _mm_card(col_mm3, mm['sma_200'], "sma200", mm['price'], "SMA 200")

            # Recomendación
            st.markdown(f"""
            <div class="recommendation-box">
                <div class="rec-label">▸ RECOMENDACIÓN ESTRATÉGICA</div>
                <div style="color:#aaa; font-size:12.5px; line-height:1.7;">{resultado['recomendacion']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Advertencias
            if resultado['advertencias']:
                st.markdown("<div style='margin-top:15px; font-family:VT323,monospace; color:#ff9800; font-size:1rem; letter-spacing:1px;'>⚠ ADVERTENCIAS DE CONTEXTO:</div>", unsafe_allow_html=True)
                for adv in resultado['advertencias']:
                    clase = "danger" if any(k in adv for k in ["bajo SMA200","trampa"]) else ""
                    st.markdown(f'<div class="warning-box {clase}">{adv}</div>', unsafe_allow_html=True)

        # ── Columna derecha: Panel de factores ──
        with col_right:
            NOMBRES_DISPLAY = {
                'FTD':        'Follow-Through Day',
                'RSI':        f'RSI (Ventana {VENTANA_CONDICIONES}d)',
                'VIX':        f'VIX / Volatilidad (Ventana {VENTANA_CONDICIONES}d)',
                'Breadth':    'Breadth (McClellan)',
                'Volume':     f'Volumen (Ventana {VENTANA_CONDICIONES}d)',
                'Divergencia':'Divergencia Alcista',
                'SMA200':     'Contexto SMA200'
            }
            ORDEN = ['FTD','RSI','VIX','Breadth','Volume','Divergencia','SMA200']

            factores_html = ""
            for fk in ORDEN:
                if fk not in resultado['metricas']:
                    continue
                m = resultado['metricas'][fk]
                nombre = NOMBRES_DISPLAY.get(fk, fk)
                pct = (m['score'] / m['max']) * 100 if m.get('max', 0) > 0 else 0
                rv  = m.get('raw_value', 0)
                bar_color = '#ff9800' if (fk == 'SMA200' and m.get('advertencia')) else m['color']

                # Sub-texto con info de ventana
                if fk == 'RSI':
                    sub = f"Actual: {rv:.1f} | Mín: {m.get('minimo_reciente',rv):.1f} ({m.get('fecha_minimo','N/A')})"
                elif fk == 'VIX':
                    sub = f"Actual: {rv:.1f} | Máx: {m.get('maximo_reciente',rv):.1f} ({m.get('fecha_maximo','N/A')})"
                elif fk == 'Breadth':
                    sub = f"{rv:.0f} ({m.get('metodo','Proxy')})"
                elif fk == 'Volume':
                    sub = f"Actual: {rv:.1f}x | Máx: {m.get('maximo_reciente',rv):.1f}x"
                elif fk == 'Divergencia':
                    sub = "Detectada" if m['score'] > 0 else "No detectada"
                elif fk == 'SMA200':
                    sub = f"Distancia: {m.get('distancia_pct',0):+.1f}%"
                else:
                    sub = ""

                sub_html = f'<div style="color:#555;font-size:10.5px;margin-top:5px;font-family:Courier New,monospace;">{sub}</div>' if sub else ''

                factores_html += f"""
                <div class="fc">
                    <div class="fh">
                        <span class="fn">{nombre} (max {m['max']} pts)</span>
                        <span class="fs" style="color:{bar_color};">{m['score']}/{m['max']}</span>
                    </div>
                    <div class="pb"><div class="pf" style="width:{pct}%;background:{bar_color};"></div></div>
                    {sub_html}
                </div>"""

            components.html(f"""<!DOCTYPE html><html><head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
                body{{margin:0;padding:0;background:#0c0e12;font-family:sans-serif;}}
                .wrap{{background:#11141a;border:1px solid #1a1e26;border-radius:10px;overflow:hidden;box-shadow:0 0 20px #00ffad08;}}
                .head{{background:#0c0e12;padding:12px 20px;border-bottom:1px solid #00ffad33;}}
                .htit{{font-family:'VT323',monospace;color:#00ffad;font-size:1.3rem;letter-spacing:2px;text-transform:uppercase;margin:0;}}
                .body{{padding:15px 20px;}}
                .fc{{background:#0c0e12;border-radius:6px;padding:12px 15px;margin:10px 0;border:1px solid #1a1e26;transition:border-color 0.2s;}}
                .fc:hover{{border-color:#00ffad22;}}
                .fh{{display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;}}
                .fn{{color:#555;font-size:10px;text-transform:uppercase;font-weight:bold;letter-spacing:1px;font-family:Courier New,monospace;}}
                .fs{{font-family:'VT323',monospace;font-size:1.2rem;}}
                .pb{{width:100%;height:6px;background:#1a1e26;border-radius:3px;overflow:hidden;}}
                .pf{{height:100%;border-radius:3px;transition:width 0.6s ease;}}
            </style></head><body>
            <div class="wrap">
                <div class="head"><span class="htit">// Desglose de Factores v2.1</span></div>
                <div class="body">{factores_html}</div>
            </div>
            </body></html>""", height=600, scrolling=True)

        # ── Gráfico de acumulación ──
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h2>📊 ZONAS DE ACUMULACIÓN</h2>", unsafe_allow_html=True)
        try:
            fig = crear_grafico_acumulacion(df_daily, resultado)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error al generar gráfico: {e}")

        # ── Detalles técnicos expandibles ──
        with st.expander("🔍 Ver detalles técnicos completos", expanded=False):
            col_det1, col_det2 = st.columns(2)
            with col_det1:
                st.markdown("<h3>Análisis de Factores:</h3>", unsafe_allow_html=True)
                for detalle in resultado['detalles']:
                    color = '#00ffad' if detalle.startswith('✓') else '#ff9800' if detalle.startswith('~') else '#f23645' if detalle.startswith('✗') else '#555'
                    st.markdown(f'<div class="detail-item" style="color:{color};">{detalle}</div>', unsafe_allow_html=True)

            with col_det2:
                if resultado['divergencia_data']:
                    div = resultado['divergencia_data']
                    st.markdown("<h3>Detalle Divergencia:</h3>", unsafe_allow_html=True)
                    st.write(f"**Tipo**: {div['tipo']}")
                    st.write(f"**Precio prev/last**: {div['precio_prev']:.2f} → {div['precio_last']:.2f}")
                    st.write(f"**RSI prev/last**: {div['rsi_prev']:.2f} → {div['rsi_last']:.2f}")

                if resultado['ftd_data'] and resultado['ftd_data'].get('signal') == 'confirmed':
                    ftd = resultado['ftd_data']
                    st.markdown("<h3>Estado FTD:</h3>", unsafe_allow_html=True)
                    st.write(f"**Estado**: {ftd.get('estado')} | **Días rally**: {ftd.get('dias_rally')}")
                    st.write(f"**Retorno FTD**: {ftd.get('retorno','N/A')}%")
                    if ftd.get('date'):
                        st.write(f"**Fecha FTD**: {ftd['date'].strftime('%Y-%m-%d')}")

                st.markdown("<h3>Medias Móviles:</h3>", unsafe_allow_html=True)
                for nombre, val in [("EMA21", mm['ema_21']), ("SMA50", mm['sma_50']), ("SMA200", mm['sma_200'])]:
                    dist = (mm['price'] - val) / val * 100 if val != 0 else 0
                    st.write(f"**{nombre}**: {dist:+.2f}%")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: BACKTESTING
    # ─────────────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown(f"""
        <div class="terminal-box">
            <h2 style="margin-top:0; border:none; padding:0; font-size:1.4rem !important;">// BACKTESTING HISTÓRICO v2.1</h2>
            <p>Análisis con ventana de <strong>{VENTANA_CONDICIONES} días</strong>.
            Las condiciones pueden haberse producido en cualquier día de la ventana, no sólo en el día de la señal.</p>
        </div>
        """, unsafe_allow_html=True)

        col_bt1, col_bt2, col_bt3 = st.columns([1, 1, 2])
        with col_bt1:
            umbral_bt = st.slider("Umbral de señal", 30, 85, 50, 5, help="Score mínimo para considerar entrada.")
            años_bt = st.selectbox("Período (años)", [1, 2, 3, 5], index=3)
        with col_bt2:
            modo_preciso     = st.checkbox("Modo Preciso (Sectores)", value=False, help="Descarga datos sectoriales (lento).")
            comparar_umbrales = st.checkbox("Comparar umbrales 50/70/80", value=False)
        with col_bt3:
            if st.button("🚀 Ejecutar Backtest", type="primary", use_container_width=True):
                if comparar_umbrales:
                    umbrales = [50, 70, 80]
                    resultados_comparativa = []
                    progress_bar = st.progress(0)
                    for idx, umb in enumerate(umbrales):
                        with st.spinner(f'Analizando umbral {umb}... ({idx+1}/3)'):
                            res, err = backtest_strategy(years=años_bt, umbral_señal=umb, usar_sectores=False)
                            if res:
                                resultados_comparativa.append({
                                    'Umbral': umb, 'Señales': res['total_señales'],
                                    'Win Rate 5d': f"{res['win_rate_5d']:.1f}%",
                                    'Win Rate 20d': f"{res['win_rate_20d']:.1f}%",
                                    'Win Rate 60d': f"{res['win_rate_60d']:.1f}%",
                                    'Max DD Prom': f"{res['max_drawdown_promedio']:.1f}%",
                                    'Retorno Medio 60d': f"{res['retorno_medio_60d']:.2f}%"
                                })
                        progress_bar.progress((idx + 1) / 3)
                    if resultados_comparativa:
                        st.success("✅ Comparativa completada")
                        st.dataframe(pd.DataFrame(resultados_comparativa), use_container_width=True, hide_index=True)
                else:
                    with st.spinner(f'Analizando {años_bt} años con umbral {umbral_bt}...'):
                        resultados_bt, error = backtest_strategy(years=años_bt, umbral_señal=umbral_bt, usar_sectores=modo_preciso)
                        if error:
                            st.warning(error)
                        elif resultados_bt:
                            st.success(f"✅ Backtest completado: {resultados_bt['total_señales']} señales (Umbral: {resultados_bt['umbral_aplicado']})")

                            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                            m_col1.metric("Win Rate 5d",  f"{resultados_bt['win_rate_5d']:.1f}%")
                            m_col2.metric("Win Rate 20d", f"{resultados_bt['win_rate_20d']:.1f}%")
                            m_col3.metric("Win Rate 60d", f"{resultados_bt['win_rate_60d']:.1f}%")
                            m_col4.metric("Max DD Promedio", f"{resultados_bt['max_drawdown_promedio']:.1f}%",
                                          delta=f"Peor: {resultados_bt['peor_drawdown']:.1f}%", delta_color="inverse")

                            m_col5, m_col6, m_col7, m_col8 = st.columns(4)
                            m_col5.metric("Total Señales",    resultados_bt['total_señales'])
                            m_col6.metric("Score Promedio",   f"{resultados_bt['score_promedio']:.1f}")
                            m_col7.metric("Retorno Medio 60d",f"{resultados_bt['retorno_medio_60d']:.2f}%")
                            m_col8.metric("Retorno Total 60d",f"{resultados_bt['retorno_total_60d']:.2f}%")

                            st.markdown("<h3>Distribución de Retornos</h3>", unsafe_allow_html=True)
                            chart_data = resultados_bt['detalle'][['retorno_5d','retorno_20d','retorno_60d']].rename(
                                columns={'retorno_5d':'5 días','retorno_20d':'20 días','retorno_60d':'60 días'})
                            st.bar_chart(chart_data.mean())

                            st.markdown("<h3>Análisis de Drawdown (60 días)</h3>", unsafe_allow_html=True)
                            dd_data = resultados_bt['detalle']['max_drawdown_60d']
                            col_dd1, col_dd2, col_dd3 = st.columns(3)
                            col_dd1.metric("Drawdown Promedio", f"{dd_data.mean():.2f}%")
                            col_dd2.metric("Peor Drawdown",     f"{dd_data.min():.2f}%")
                            col_dd3.metric("Señales DD > -10%", f"{(dd_data < -10).sum()}/{len(dd_data)}")
                            st.bar_chart(dd_data.value_counts(bins=10).sort_index())

                            with st.expander("Ver tabla detallada"):
                                st.dataframe(resultados_bt['detalle'].sort_values('fecha', ascending=False),
                                             use_container_width=True, hide_index=True)

                            st.markdown("<h3>Distribución Temporal</h3>", unsafe_allow_html=True)
                            resultados_bt['detalle']['año'] = pd.to_datetime(resultados_bt['detalle']['fecha']).dt.year
                            st.bar_chart(resultados_bt['detalle'].groupby('año').size())

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: METODOLOGÍA
    # ─────────────────────────────────────────────────────────────────────────
    with tab3:
        st.markdown(f"""
        <div class="terminal-box">
            <h2 style="margin-top:0; border:none; padding:0; font-size:1.5rem !important;">// METODOLOGÍA CIENTÍFICA v2.1</h2>
            <p>Sistema <strong>más permisivo</strong>: permite condiciones en ventana de <strong>{VENTANA_CONDICIONES} días</strong>.</p>
        </div>

        <h2>01 // PROBLEMA DE LA VERSIÓN ANTERIOR</h2>
        <p>El algoritmo anterior requería que RSI &lt; 35, VIX &gt; 30, etc., ocurrieran <strong>exactamente el mismo día</strong>.
        Esto es irrealista: el pánico (VIX alto) suele ocurrir 2–5 días antes que el RSI toque fondo.</p>

        <h2>02 // SOLUCIÓN: CONDICIONES EN VENTANA</h2>
        <p>El motor ahora busca:</p>
        <ul>
            <li><strong>RSI</strong>: Mínimo en últimos {VENTANA_CONDICIONES} días &lt; 35 (no solo hoy)</li>
            <li><strong>VIX</strong>: Máximo en últimos {VENTANA_CONDICIONES} días &gt; 30 (captura spike reciente)</li>
            <li><strong>Volumen</strong>: Máximo en últimos {VENTANA_CONDICIONES} días &gt; 1.5× media</li>
        </ul>
        <p>Esto captura la <strong>confluencia temporal</strong> de factores, no sólo la instantánea.</p>

        <h2>03 // SISTEMA DE ADVERTENCIAS (NO PENALIZACIONES)</h2>
        <p><strong>Antes</strong>: Restar –10 pts por estar bajo SMA200.<br>
        <strong>Ahora</strong>: Mostrar advertencia naranja/roja pero mantener score.</p>
        <blockquote>Los fondos naturalmente ocurren bajo las medias móviles. Penalizar esto es contraproducente.</blockquote>

        <h2>04 // PUNTUACIÓN DE FACTORES</h2>

        | Factor | Peso | Tipo | Lógica |
        |--------|------|------|--------|
        | **FTD** | 35 | Binario | Confirmado o no |
        | **RSI** | 15 | Ventana {VENTANA_CONDICIONES}d | Mínimo &lt; 35 |
        | **VIX** | 20 | Ventana {VENTANA_CONDICIONES}d | Máximo &gt; 30 |
        | **Breadth** | 20 | Actual | McClellan &lt; –50 |
        | **Volumen** | 10 | Ventana {VENTANA_CONDICIONES}d | Máximo &gt; 1.5× |
        | **Divergencia** | 15 | Binario | RSI vs Precio |

        <h2>05 // UMBRALES DE DECISIÓN</h2>
        <ul>
            <li><strong style="color:#00ffad">Score 70+</strong>: 🟢 VERDE – Fondo probable</li>
            <li><strong style="color:#ff9800">Score 50–69</strong>: 🟡 AMBAR – Desarrollando</li>
            <li><strong style="color:#f23645">Score &lt; 50</strong>: 🔴 ROJO – Sin fondo</li>
        </ul>

        <h2>06 // GESTIÓN DE RIESGO CON ADVERTENCIAS</h2>
        <ul>
            <li>Reducir tamaño de posición (15% en lugar de 25%)</li>
            <li>Stop-loss más ajustado (–5% en lugar de –7%)</li>
            <li>Esperar confirmación adicional (cierre sobre EMA21)</li>
        </ul>

        <h2>07 // REFERENCIAS</h2>
        <ul>
            <li>O'Neil, W. (2009). <em>How to Make Money in Stocks</em></li>
            <li>McClellan, S. & M. (1998). <em>Patterns for Profit</em></li>
            <li>Bulkowski, T. (2010). <em>Encyclopedia of Candlestick Charts</em></li>
        </ul>

        <div style="text-align:center; margin-top:40px; padding:20px; border-top:1px solid #1a1e26;">
            <p style="font-family:'VT323',monospace; color:#333; font-size:0.95rem; letter-spacing:2px;">
                [END OF TRANSMISSION // RSU_ALGORITMO_PRO_v2.1]<br>
                [STATUS: ACTIVE // MULTI-FACTOR ENGINE ONLINE]
            </p>
        </div>
        """, unsafe_allow_html=True)
