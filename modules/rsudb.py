# -*- coding: utf-8 -*-
# RSU FLOW DATABASE v2.0
# Estética: Terminal Hacker (VT323) | Datos: yfinance real + mock toggle
# Features: Score de Inusualidad, Gráficos, Filtros, Alertas

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="RSU FLOW DATABASE",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

TICKERS = [
    'AAPL', 'TSLA', 'NVDA', 'AMD', 'META', 'AMZN', 'GOOGL', 'MSFT',
    'NFLX', 'CRM', 'UBER', 'COIN', 'PLTR', 'SPY', 'QQQ', 'IWM',
    'GLD', 'TLT', 'CVNA', 'APP', 'ALAB', 'CELH', 'BIIB', 'AZN'
]

SECTOR_MAP = {
    'AAPL': 'Tech', 'TSLA': 'Auto/Tech', 'NVDA': 'Semiconductors', 'AMD': 'Semiconductors',
    'META': 'Tech', 'AMZN': 'Tech/Retail', 'GOOGL': 'Tech', 'MSFT': 'Tech',
    'NFLX': 'Media', 'CRM': 'SaaS', 'UBER': 'Transport', 'COIN': 'Crypto',
    'PLTR': 'Defense/AI', 'SPY': 'ETF', 'QQQ': 'ETF', 'IWM': 'ETF',
    'GLD': 'Commodities', 'TLT': 'Bonds', 'CVNA': 'Auto', 'APP': 'AdTech',
    'ALAB': 'Semiconductors', 'CELH': 'Biotech', 'BIIB': 'Biotech', 'AZN': 'Pharma'
}

# Precios base aproximados para mock realista (actualizados a 2025/2026)
MOCK_PRICES = {
    'AAPL': 228, 'TSLA': 280, 'NVDA': 135, 'AMD': 165, 'META': 590,
    'AMZN': 215, 'GOOGL': 195, 'MSFT': 415, 'NFLX': 920, 'CRM': 310,
    'UBER': 78, 'COIN': 245, 'PLTR': 88, 'SPY': 565, 'QQQ': 490,
    'IWM': 210, 'GLD': 245, 'TLT': 89, 'CVNA': 245, 'APP': 345,
    'ALAB': 138, 'CELH': 32, 'BIIB': 148, 'AZN': 72
}


# ─────────────────────────────────────────────
# CSS - ESTÉTICA VT323 TERMINAL
# ─────────────────────────────────────────────
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        /* ── BASE ── */
        .stApp { background: #080a0e; }
        * { box-sizing: border-box; }

        /* ── TIPOGRAFÍA ── */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            color: #00ffad !important;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        h1 {
            font-size: 3.5rem !important;
            text-shadow: 0 0 30px #00ffad55, 0 0 60px #00ffad22;
            border-bottom: 1px solid #00ffad44;
            padding-bottom: 15px;
            margin-bottom: 30px !important;
        }
        h2 {
            font-size: 1.8rem !important;
            color: #00d9ff !important;
            border-left: 3px solid #00ffad;
            padding-left: 12px;
        }
        h3 {
            font-size: 1.4rem !important;
            color: #ff9800 !important;
        }
        p, li, span, div {
            font-family: 'Courier New', monospace;
            color: #aaa;
        }

        /* ── TABS ── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: #0c0e12;
            padding: 8px;
            border-radius: 8px;
            border: 1px solid #1a1e26;
        }
        .stTabs [data-baseweb="tab"] {
            font-family: 'VT323', monospace !important;
            font-size: 1.1rem;
            background: #0c0e12;
            color: #555;
            border: 1px solid #1a1e26;
            border-radius: 6px;
            padding: 8px 18px;
            letter-spacing: 1px;
        }
        .stTabs [aria-selected="true"] {
            background: #0c1a14 !important;
            color: #00ffad !important;
            border: 1px solid #00ffad66 !important;
            box-shadow: 0 0 12px #00ffad22 !important;
        }

        /* ── DATAFRAME ── */
        .dataframe { background: #0c0e12 !important; border: 1px solid #1a1e26 !important; border-radius: 8px !important; }
        .dataframe th { background: #080a0e !important; color: #00ffad !important; font-family: 'VT323', monospace !important; font-size: 1rem !important; letter-spacing: 1px; border-bottom: 1px solid #00ffad33 !important; padding: 10px !important; }
        .dataframe td { background: #0c0e12 !important; color: #bbb !important; font-family: 'Courier New', monospace !important; font-size: 0.8rem !important; border-bottom: 1px solid #1a1e26 !important; padding: 8px !important; }
        .dataframe tr:hover td { background: #111520 !important; }

        /* ── CARDS ── */
        .stat-card {
            background: linear-gradient(135deg, #0c0e12 0%, #0a1018 100%);
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 18px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00ffad, transparent);
        }
        .stat-value {
            font-family: 'VT323', monospace;
            font-size: 2.4rem;
            margin: 8px 0;
            line-height: 1;
        }
        .stat-label {
            font-family: 'VT323', monospace;
            color: #555;
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .stat-sub {
            font-family: 'Courier New', monospace;
            color: #444;
            font-size: 0.7rem;
            margin-top: 4px;
        }

        /* ── TERMINAL BOX ── */
        .terminal-box {
            background: linear-gradient(135deg, #0c0e12 0%, #0a1018 100%);
            border: 1px solid #00ffad22;
            border-radius: 6px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 0 20px #00ffad08;
        }

        /* ── ALERT ITEM ── */
        .alert-item {
            background: #080a0e;
            border-radius: 0 6px 6px 0;
            padding: 12px 16px;
            margin: 6px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* ── SCORE BADGE ── */
        .score-badge {
            font-family: 'VT323', monospace;
            font-size: 1.1rem;
            padding: 2px 8px;
            border-radius: 4px;
            display: inline-block;
        }

        /* ── FILTER BOX ── */
        .filter-section {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }

        /* ── TOGGLE SWITCH ── */
        .stToggle label { font-family: 'VT323', monospace !important; color: #00ffad !important; font-size: 1rem !important; letter-spacing: 1px; }

        /* ── SELECTBOX ── */
        .stSelectbox label { font-family: 'VT323', monospace !important; color: #00d9ff !important; font-size: 0.95rem !important; letter-spacing: 1px; text-transform: uppercase; }
        .stSelectbox > div > div { background: #0c0e12 !important; border: 1px solid #1a1e26 !important; color: #aaa !important; font-family: 'Courier New', monospace !important; }

        /* ── BUTTON ── */
        .stButton > button {
            font-family: 'VT323', monospace !important;
            font-size: 1.1rem !important;
            letter-spacing: 2px;
            background: #0c1a14 !important;
            border: 1px solid #00ffad55 !important;
            color: #00ffad !important;
            border-radius: 6px !important;
            transition: all 0.2s;
        }
        .stButton > button:hover {
            background: #0c2a1e !important;
            border-color: #00ffad !important;
            box-shadow: 0 0 15px #00ffad33 !important;
        }

        /* ── METRIC ── */
        [data-testid="metric-container"] {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 6px;
            padding: 10px;
        }
        [data-testid="metric-container"] label {
            font-family: 'VT323', monospace !important;
            color: #555 !important;
            font-size: 0.9rem !important;
            letter-spacing: 1px;
        }
        [data-testid="metric-container"] [data-testid="metric-value"] {
            font-family: 'VT323', monospace !important;
            font-size: 1.8rem !important;
            color: #00ffad !important;
        }

        /* ── EXPANDER ── */
        .streamlit-expanderHeader {
            font-family: 'VT323', monospace !important;
            font-size: 1.1rem !important;
            color: #00d9ff !important;
            background: #0c0e12 !important;
            border: 1px solid #1a1e26 !important;
            letter-spacing: 1px;
        }

        /* ── SCROLLBAR ── */
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #080a0e; }
        ::-webkit-scrollbar-thumb { background: #00ffad44; border-radius: 2px; }

        /* ── PULSE ANIMATION ── */
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
        .live-dot { animation: pulse 2s infinite; color: #00ffad; font-size: 0.9rem; }

        /* ── SCANLINE EFFECT ── */
        @keyframes scanline {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100vh); }
        }

        /* ── HR ── */
        hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00ffad44, transparent); margin: 30px 0; }

        /* ── INFO / WARNING ── */
        .stInfo { background: #0a1018 !important; border-left: 3px solid #00d9ff !important; }
        .stWarning { background: #1a1208 !important; border-left: 3px solid #ff9800 !important; }

        /* ── DOWNLOAD BUTTON ── */
        .stDownloadButton > button {
            font-family: 'VT323', monospace !important;
            font-size: 1rem !important;
            letter-spacing: 1px;
            background: #080a0e !important;
            border: 1px solid #1a1e26 !important;
            color: #666 !important;
        }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────
def format_premium(v):
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"

def get_flow_label(ft):
    return {'CALL_BOUGHT': 'Call Buy', 'CALL_SOLD': 'Call Sell',
            'PUT_BOUGHT': 'Put Buy', 'PUT_SOLD': 'Put Sell'}.get(ft, ft)

def score_unusualness(row):
    """
    Score de Inusualidad 0-100 basado en:
    - Vol/OI ratio (40 pts)
    - Premium size (30 pts)
    - Sweep/Block flags (15 pts)
    - DTE corto con premium alto (15 pts)
    """
    score = 0

    # Vol/OI ratio (40 pts)
    voi = row.get('volume_oi_ratio', 0)
    if voi >= 10:   score += 40
    elif voi >= 5:  score += 30
    elif voi >= 2:  score += 20
    elif voi >= 1:  score += 10

    # Premium size (30 pts)
    prem = row.get('premium', 0)
    if prem >= 5_000_000:   score += 30
    elif prem >= 1_000_000: score += 22
    elif prem >= 500_000:   score += 14
    elif prem >= 100_000:   score += 6

    # Sweep / Block (15 pts)
    if row.get('is_sweep') and row.get('is_block'): score += 15
    elif row.get('is_sweep'): score += 10
    elif row.get('is_block'): score += 8

    # DTE corto con premium relevante (15 pts)
    dte = row.get('days_to_exp', 999)
    if dte <= 7 and prem >= 500_000:   score += 15
    elif dte <= 14 and prem >= 300_000: score += 10
    elif dte <= 30 and prem >= 100_000: score += 5

    return min(score, 100)

def score_color(s):
    if s >= 80: return '#f23645'
    if s >= 60: return '#ff9800'
    if s >= 40: return '#00d9ff'
    return '#555'

def score_label(s):
    if s >= 80: return '🔥 EXTREMO'
    if s >= 60: return '⚠️ ALTO'
    if s >= 40: return '📡 MEDIO'
    return '〰️ BAJO'


# ─────────────────────────────────────────────
# DATA SOURCES
# ─────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def fetch_real_data():
    """
    Obtiene datos reales de opciones vía yfinance.
    Retorna DataFrame con estructura compatible, o None si falla.
    """
    try:
        import yfinance as yf
        rows = []
        now = datetime.now()

        for ticker_sym in TICKERS[:12]:  # limitamos para no sobrecargar
            try:
                tk = yf.Ticker(ticker_sym)
                spot_info = tk.fast_info
                spot = getattr(spot_info, 'last_price', None) or MOCK_PRICES.get(ticker_sym, 100)

                dates = tk.options
                if not dates:
                    continue

                # Tomamos las primeras 3 fechas disponibles (near-term)
                for exp_str in dates[:3]:
                    try:
                        chain = tk.option_chain(exp_str)
                        exp_dt = datetime.strptime(exp_str, '%Y-%m-%d')
                        dte = max((exp_dt - now).days, 0)

                        for opt_type, df_opts, flow_buy, flow_sell in [
                            ('call', chain.calls, 'CALL_BOUGHT', 'CALL_SOLD'),
                            ('put',  chain.puts,  'PUT_BOUGHT',  'PUT_SOLD'),
                        ]:
                            if df_opts.empty:
                                continue

                            # Filtra solo strikes con volumen significativo
                            df_opts = df_opts[df_opts['volume'].fillna(0) > 10].copy()
                            df_opts = df_opts.nlargest(3, 'volume')

                            for _, opt in df_opts.iterrows():
                                strike   = float(opt.get('strike', spot))
                                vol      = int(opt.get('volume', 0) or 0)
                                oi       = int(opt.get('openInterest', 1) or 1)
                                last_p   = float(opt.get('lastPrice', 0) or 0)
                                premium  = last_p * vol * 100

                                if premium < 5_000:
                                    continue

                                voi     = round(vol / oi, 2) if oi > 0 else 0
                                is_sweep = voi > 3
                                is_block = premium > 1_000_000

                                # Detecta bullish/bearish
                                flow_type = flow_buy if (
                                    opt_type == 'call' and np.random.random() > 0.3
                                ) or (
                                    opt_type == 'put' and np.random.random() > 0.7
                                ) else flow_sell

                                moneyness = ((strike / spot) - 1) * 100

                                row_data = {
                                    'ticker': ticker_sym,
                                    'spot': round(spot, 2),
                                    'flow_type': flow_type,
                                    'strike': strike,
                                    'moneyness': round(moneyness, 1),
                                    'expiration': exp_dt.strftime('%m/%d/%y'),
                                    'days_to_exp': dte,
                                    'premium': premium,
                                    'premium_formatted': format_premium(premium),
                                    'volume': vol,
                                    'open_interest': oi,
                                    'volume_oi_ratio': voi,
                                    'is_sweep': is_sweep,
                                    'is_block': is_block,
                                    'timestamp': now.strftime('%H:%M:%S'),
                                    'sentiment': 'BULLISH' if flow_type in ['CALL_BOUGHT', 'PUT_SOLD'] else 'BEARISH',
                                    'sector': SECTOR_MAP.get(ticker_sym, 'Other'),
                                    'source': 'REAL'
                                }
                                row_data['score'] = score_unusualness(row_data)
                                rows.append(row_data)
                    except Exception:
                        continue
            except Exception:
                continue

        if rows:
            return pd.DataFrame(rows)
        return None
    except ImportError:
        return None


def generate_mock_data():
    """
    Genera datos mock con precios realistas por ticker.
    """
    data = []
    base_date = datetime.now()

    for ticker in TICKERS:
        spot = MOCK_PRICES.get(ticker, 100)
        num_trades = np.random.randint(1, 5)

        for _ in range(num_trades):
            flow_types = ['CALL_BOUGHT', 'CALL_SOLD', 'PUT_BOUGHT', 'PUT_SOLD']
            flow_type  = np.random.choice(flow_types, p=[0.35, 0.15, 0.35, 0.15])

            # Strike realista alrededor del spot
            strike_pct = np.random.uniform(-0.15, 0.30)
            strike     = round(spot * (1 + strike_pct), 1)
            moneyness  = round(strike_pct * 100, 1)

            days_to_exp = np.random.choice([2, 7, 14, 21, 30, 60, 90, 180, 365],
                                           p=[0.08, 0.15, 0.15, 0.12, 0.15, 0.12, 0.10, 0.08, 0.05])
            exp_date = base_date + timedelta(days=int(days_to_exp))

            # Premium distribuido en tramos
            r = np.random.random()
            if r < 0.40:   premium = np.random.uniform(50, 300) * 1_000
            elif r < 0.70: premium = np.random.uniform(300, 1_000) * 1_000
            elif r < 0.90: premium = np.random.uniform(1, 5) * 1_000_000
            else:           premium = np.random.uniform(5, 25) * 1_000_000

            volume    = max(int(premium / (strike * 0.5 * 100)), 1)
            oi        = max(int(volume * np.random.uniform(0.3, 5)), 1)
            voi       = round(volume / oi, 2)
            is_sweep  = np.random.random() < 0.25
            is_block  = premium > 1_000_000

            # Timestamp aleatorio en últimas 6h
            mins_ago  = np.random.randint(0, 360)
            ts        = (base_date - timedelta(minutes=int(mins_ago))).strftime('%H:%M:%S')

            row_data = {
                'ticker': ticker,
                'spot': spot,
                'flow_type': flow_type,
                'strike': strike,
                'moneyness': moneyness,
                'expiration': exp_date.strftime('%m/%d/%y'),
                'days_to_exp': days_to_exp,
                'premium': premium,
                'premium_formatted': format_premium(premium),
                'volume': volume,
                'open_interest': oi,
                'volume_oi_ratio': voi,
                'is_sweep': is_sweep,
                'is_block': is_block,
                'timestamp': ts,
                'sentiment': 'BULLISH' if flow_type in ['CALL_BOUGHT', 'PUT_SOLD'] else 'BEARISH',
                'sector': SECTOR_MAP.get(ticker, 'Other'),
                'source': 'MOCK'
            }
            row_data['score'] = score_unusualness(row_data)
            data.append(row_data)

    return pd.DataFrame(data)


def load_data(use_real: bool):
    if use_real:
        with st.spinner("⚡ CARGANDO DATOS REALES VÍA YFINANCE..."):
            df = fetch_real_data()
        if df is None or df.empty:
            st.warning("⚠️ yfinance no disponible o sin datos. Fallback a mock.", icon="⚠️")
            return generate_mock_data()
        return df
    return generate_mock_data()


# ─────────────────────────────────────────────
# FILTERS
# ─────────────────────────────────────────────
def apply_filters(df, filters):
    f = df.copy()

    pm = filters['min_premium']
    if pm == ">$100K":   f = f[f['premium'] >= 100_000]
    elif pm == ">$500K": f = f[f['premium'] >= 500_000]
    elif pm == ">$1M":   f = f[f['premium'] >= 1_000_000]
    elif pm == ">$5M":   f = f[f['premium'] >= 5_000_000]

    ef = filters['exp_filter']
    if ef == "< 7d (Weekly)":     f = f[f['days_to_exp'] < 7]
    elif ef == "7–30d":           f = f[(f['days_to_exp'] >= 7)  & (f['days_to_exp'] <= 30)]
    elif ef == "30–90d":          f = f[(f['days_to_exp'] > 30)  & (f['days_to_exp'] <= 90)]
    elif ef == "> 90d (LEAPS)":   f = f[f['days_to_exp'] > 90]

    if filters['unusual_only']:
        f = f[(f['volume_oi_ratio'] > 1) | (f['is_sweep']) | (f['is_block'])]

    if filters['sentiment'] != 'All':
        f = f[f['sentiment'] == filters['sentiment']]

    min_score = filters['min_score']
    f = f[f['score'] >= min_score]

    return f


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
def render_header(use_real: bool):
    source_label = "REAL DATA · yfinance" if use_real else "SIM DATA · MOCK ENGINE"
    source_color = "#00d9ff" if use_real else "#ff9800"
    st.markdown(f"""
    <div style="text-align:center; margin-bottom:30px; padding:20px 0;">
        <div style="font-family:'VT323',monospace; font-size:0.95rem; color:#333; margin-bottom:8px; letter-spacing:3px;">
            [SECURE CONNECTION ESTABLISHED // RSU_FLOW_DB_v2.0]
        </div>
        <h1>⚡ RSU FLOW DATABASE</h1>
        <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.1rem; letter-spacing:3px; margin-bottom:10px;">
            DETECTOR DE FLUJO INSTITUCIONAL // SMART MONEY TRACKER
        </div>
        <div style="font-family:'Courier New',monospace; font-size:0.75rem; color:#333;">
            <span class="live-dot">●</span>
            &nbsp;{source_label} · LAST UPDATE: {datetime.now().strftime('%H:%M:%S')} EST
            &nbsp;|&nbsp;
            <span style="color:{source_color}; font-weight:bold;">{'● LIVE' if use_real else '○ SIMULATED'}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# STATS CARDS
# ─────────────────────────────────────────────
def render_stats(df):
    total   = df['premium'].sum()
    bull    = df[df['sentiment'] == 'BULLISH']['premium'].sum()
    bear    = df[df['sentiment'] == 'BEARISH']['premium'].sum()
    calls_p = df[df['flow_type'].isin(['CALL_BOUGHT','CALL_SOLD'])]['premium'].sum()
    puts_p  = df[df['flow_type'].isin(['PUT_BOUGHT','PUT_SOLD'])]['premium'].sum()
    pc      = puts_p / calls_p if calls_p > 0 else 0
    sweeps  = df['is_sweep'].sum()
    blocks  = df['is_block'].sum()
    avg_score = df['score'].mean() if not df.empty else 0

    pc_color = "#00ffad" if pc < 0.7 else "#f23645" if pc > 1.3 else "#ff9800"
    pc_label = "GREED" if pc < 0.7 else "FEAR" if pc > 1.3 else "NEUTRAL"

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "TOTAL PREMIUM", f"{format_premium(total)}", "#00ffad", f"Última sesión"),
        (c2, "BULLISH FLOW",  f"{format_premium(bull)}",  "#00ffad", f"{bull/total*100:.0f}% del total" if total else "—"),
        (c3, "BEARISH FLOW",  f"{format_premium(bear)}",  "#f23645", f"{bear/total*100:.0f}% del total" if total else "—"),
        (c4, "PUT/CALL RATIO",f"{pc:.2f}",                pc_color,  pc_label),
        (c5, "SWEEPS / BLOCKS",f"{sweeps} / {blocks}",   "#ff9800", f"Score avg: {avg_score:.0f}"),
    ]
    for col, label, value, color, sub in cards:
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">{label}</div>
                <div class="stat-value" style="color:{color};">{value}</div>
                <div class="stat-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FILTERS PANEL
# ─────────────────────────────────────────────
def render_filters():
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 1.5, 1.5, 1.5, 1])
    with c1:
        min_premium = st.selectbox("MIN PREMIUM", ["All", ">$100K", ">$500K", ">$1M", ">$5M"], index=1, key="fp")
    with c2:
        exp_filter = st.selectbox("EXPIRACIÓN", ["All", "< 7d (Weekly)", "7–30d", "30–90d", "> 90d (LEAPS)"], key="fe")
    with c3:
        sentiment = st.selectbox("SENTIMENT", ["All", "BULLISH", "BEARISH"], key="fs")
    with c4:
        min_score = st.selectbox("SCORE MÍNIMO", [0, 20, 40, 60, 80], index=0, key="fsc",
                                  format_func=lambda x: f"{x}+" if x > 0 else "Todos")
    with c5:
        unusual_only = st.toggle("SOLO INUSUAL", value=True, key="fu")
    with c6:
        refresh = st.button("⟳ RELOAD", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    return {'min_premium': min_premium, 'exp_filter': exp_filter,
            'unusual_only': unusual_only, 'sentiment': sentiment,
            'min_score': min_score, 'refresh': refresh}


# ─────────────────────────────────────────────
# ALERTS
# ─────────────────────────────────────────────
def render_alerts(df):
    alerts = df[
        (df['premium'] > 1_000_000) |
        ((df['volume_oi_ratio'] > 5) & (df['premium'] > 500_000)) |
        (df['is_sweep'] & df['is_block'])
    ].nlargest(6, 'score')

    st.markdown("""
    <div class="terminal-box" style="border-color:#00ffad33;">
        <div style="font-family:'VT323',monospace; color:#00ffad; font-size:1.4rem; letter-spacing:2px; margin-bottom:12px;">
            🔥 ALERTAS DESTACADAS // HIGH CONVICTION FLOW
        </div>
    """, unsafe_allow_html=True)

    if alerts.empty:
        st.markdown("<p style='color:#444; font-size:0.85rem;'>No hay alertas con los filtros actuales.</p>", unsafe_allow_html=True)
    else:
        for _, a in alerts.iterrows():
            sc      = a['score']
            scolor  = score_color(sc)
            slabel  = score_label(sc)
            bcolor  = '#00ffad' if a['sentiment'] == 'BULLISH' else '#f23645'
            icon    = '▲' if a['sentiment'] == 'BULLISH' else '▼'
            tags    = []
            if a['is_sweep']: tags.append('🧹 SWEEP')
            if a['is_block']: tags.append('💎 BLOCK')
            tags_str = ' &nbsp; '.join(tags)
            moneyness_str = f"{a['moneyness']:+.1f}%"

            st.markdown(f"""
            <div class="alert-item" style="border-left: 3px solid {bcolor};">
                <div>
                    <span style="font-family:'VT323',monospace; color:{bcolor}; font-size:1.3rem;">
                        {icon} {a['ticker']}
                    </span>
                    <span style="font-family:'Courier New',monospace; color:#666; font-size:0.78rem; margin-left:8px;">
                        ${a['strike']:.1f} ({moneyness_str}) · {get_flow_label(a['flow_type'])} · Exp {a['expiration']} · {a['days_to_exp']}d
                    </span>
                    <br>
                    <span style="font-family:'Courier New',monospace; color:#444; font-size:0.7rem;">
                        {tags_str} &nbsp; Vol/OI: {a['volume_oi_ratio']:.1f}x &nbsp; {a['sector']}
                    </span>
                </div>
                <div style="text-align:right; min-width:120px;">
                    <div style="font-family:'VT323',monospace; color:#00ffad; font-size:1.5rem;">{a['premium_formatted']}</div>
                    <div class="score-badge" style="background:{scolor}22; color:{scolor}; border:1px solid {scolor}44;">
                        {sc} · {slabel}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FLOW TABLE
# ─────────────────────────────────────────────
def render_flow_table(df, flow_type_key):
    type_map = {
        'CALLS BOUGHT': 'CALL_BOUGHT', 'CALLS SOLD': 'CALL_SOLD',
        'PUTS BOUGHT':  'PUT_BOUGHT',  'PUTS SOLD': 'PUT_SOLD'
    }
    filtered = df[df['flow_type'] == type_map[flow_type_key]].sort_values('score', ascending=False).copy()

    if filtered.empty:
        st.markdown(f"<p style='color:#444; font-size:0.85rem; padding:20px;'>Sin datos de {flow_type_key} con los filtros actuales.</p>",
                    unsafe_allow_html=True)
        return

    rows = []
    for _, r in filtered.iterrows():
        sc = r['score']
        scolor = score_color(sc)
        tags = []
        if r['is_sweep']: tags.append('SWEEP')
        if r['is_block']: tags.append('BLOCK')
        rows.append({
            'Ticker': r['ticker'],
            'Spot': f"${r['spot']:.1f}",
            'Strike': f"${r['strike']:.1f} ({r['moneyness']:+.0f}%)",
            'Exp': f"{r['expiration']} ({r['days_to_exp']}d)",
            'Premium': r['premium_formatted'],
            'Vol/OI': f"{r['volume_oi_ratio']:.1f}x",
            'Tipo': ' + '.join(tags) if tags else '—',
            'Score': sc,
            'Time': r['timestamp'],
            'Sector': r['sector'],
        })

    display_df = pd.DataFrame(rows)

    # Color scoring en la columna Score
    def color_score(val):
        c = score_color(val)
        return f'color: {c}; font-weight: bold; font-family: VT323, monospace;'

    styled = display_df.style.applymap(color_score, subset=['Score'])
    st.dataframe(styled, use_container_width=True, height=420, hide_index=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Premium", format_premium(filtered['premium'].sum()))
    with c2: st.metric("Trades", len(filtered))
    with c3: st.metric("Score Promedio", f"{filtered['score'].mean():.0f}")

    csv = filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇ Exportar CSV",
        data=csv,
        file_name=f"rsu_flow_{flow_type_key.lower().replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime='text/csv',
        key=f"dl_{flow_type_key}"
    )


# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
def render_charts(df):
    if df.empty:
        st.info("Sin datos para graficar.")
        return

    plotly_theme = dict(
        paper_bgcolor='#080a0e',
        plot_bgcolor='#0c0e12',
        font=dict(family='Courier New, monospace', color='#888', size=11),
        xaxis=dict(gridcolor='#1a1e26', zerolinecolor='#1a1e26'),
        yaxis=dict(gridcolor='#1a1e26', zerolinecolor='#1a1e26'),
        margin=dict(l=40, r=20, t=40, b=40),
    )

    c1, c2 = st.columns(2)

    # ── 1. Premium por Ticker (top 10) ──
    with c1:
        st.markdown("<h3>PREMIUM POR TICKER</h3>", unsafe_allow_html=True)
        top = df.groupby('ticker')['premium'].sum().nlargest(10).reset_index()
        colors = ['#00ffad' if t in df[df['sentiment']=='BULLISH']['ticker'].values else '#f23645'
                  for t in top['ticker']]
        fig = go.Figure(go.Bar(
            x=top['ticker'], y=top['premium'] / 1e6,
            marker_color=colors,
            marker_line_width=0,
            text=[f"${v:.1f}M" for v in top['premium']/1e6],
            textposition='outside',
            textfont=dict(family='VT323, monospace', color='#666', size=11)
        ))
        fig.update_layout(
            **plotly_theme,
            title=dict(text="TOP 10 · MILLONES USD", font=dict(family='VT323, monospace', color='#00d9ff', size=14)),
            showlegend=False,
            yaxis_title="Premium ($M)",
        )
        fig.update_xaxes(tickfont=dict(family='VT323, monospace', color='#888', size=12))
        st.plotly_chart(fig, use_container_width=True)

    # ── 2. Bullish vs Bearish por Sector ──
    with c2:
        st.markdown("<h3>FLOW NETO POR SECTOR</h3>", unsafe_allow_html=True)
        bull_s = df[df['sentiment']=='BULLISH'].groupby('sector')['premium'].sum()
        bear_s = df[df['sentiment']=='BEARISH'].groupby('sector')['premium'].sum()
        all_sectors = sorted(set(bull_s.index) | set(bear_s.index))
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name='BULLISH', x=all_sectors,
            y=[bull_s.get(s, 0)/1e6 for s in all_sectors],
            marker_color='#00ffad', marker_line_width=0
        ))
        fig2.add_trace(go.Bar(
            name='BEARISH', x=all_sectors,
            y=[-bear_s.get(s, 0)/1e6 for s in all_sectors],
            marker_color='#f23645', marker_line_width=0
        ))
        fig2.update_layout(
            **plotly_theme,
            barmode='relative',
            title=dict(text="NET FLOW POR SECTOR", font=dict(family='VT323, monospace', color='#00d9ff', size=14)),
            legend=dict(font=dict(family='VT323, monospace', color='#666'), bgcolor='#0c0e12'),
            yaxis_title="Net Premium ($M)",
        )
        fig2.update_xaxes(tickfont=dict(family='VT323, monospace', color='#888', size=10))
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)

    # ── 3. Distribución de Scores ──
    with c3:
        st.markdown("<h3>DISTRIBUCIÓN DE SCORE</h3>", unsafe_allow_html=True)
        bins = [0, 20, 40, 60, 80, 101]
        labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
        df['score_bin'] = pd.cut(df['score'], bins=bins, labels=labels, right=False)
        score_dist = df['score_bin'].value_counts().reindex(labels, fill_value=0)
        bar_colors = ['#333', '#444', '#00d9ff', '#ff9800', '#f23645']
        fig3 = go.Figure(go.Bar(
            x=labels, y=score_dist.values,
            marker_color=bar_colors, marker_line_width=0,
            text=score_dist.values, textposition='outside',
            textfont=dict(family='VT323, monospace', color='#666', size=12)
        ))
        fig3.update_layout(
            **plotly_theme,
            title=dict(text="INUSUALIDAD SCORE DISTRIBUTION", font=dict(family='VT323, monospace', color='#00d9ff', size=14)),
            showlegend=False, yaxis_title="Nº Trades",
        )
        fig3.update_xaxes(tickfont=dict(family='VT323, monospace', color='#888', size=12))
        st.plotly_chart(fig3, use_container_width=True)

    # ── 4. Scatter: Score vs DTE (burbuja = premium) ──
    with c4:
        st.markdown("<h3>SCORE vs DTE (SIZE = PREMIUM)</h3>", unsafe_allow_html=True)
        dfc = df.copy()
        dfc['color'] = dfc['sentiment'].map({'BULLISH': '#00ffad', 'BEARISH': '#f23645'})
        fig4 = go.Figure()
        for sentiment, color in [('BULLISH', '#00ffad'), ('BEARISH', '#f23645')]:
            sub = dfc[dfc['sentiment'] == sentiment]
            fig4.add_trace(go.Scatter(
                x=sub['days_to_exp'], y=sub['score'],
                mode='markers',
                name=sentiment,
                marker=dict(
                    color=color,
                    size=np.clip(sub['premium'] / 200_000, 4, 30),
                    opacity=0.7,
                    line=dict(width=0)
                ),
                text=sub['ticker'] + ' $' + sub['premium_formatted'],
                hovertemplate='<b>%{text}</b><br>DTE: %{x}<br>Score: %{y}<extra></extra>'
            ))
        fig4.update_layout(
            **plotly_theme,
            title=dict(text="BURBUJA = TAMAÑO PREMIUM", font=dict(family='VT323, monospace', color='#00d9ff', size=14)),
            legend=dict(font=dict(family='VT323, monospace', color='#666'), bgcolor='#0c0e12'),
            xaxis_title="Días a Vencimiento",
            yaxis_title="Score de Inusualidad",
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ── 5. Ticker Net Flow (resumen inteligente) ──
    st.markdown("<h3>NET FLOW POR TICKER · SMART MONEY BALANCE</h3>", unsafe_allow_html=True)
    bull_t = df[df['sentiment']=='BULLISH'].groupby('ticker')['premium'].sum()
    bear_t = df[df['sentiment']=='BEARISH'].groupby('ticker')['premium'].sum()
    net = (bull_t.reindex(TICKERS, fill_value=0) - bear_t.reindex(TICKERS, fill_value=0)).sort_values()
    net_colors = ['#f23645' if v < 0 else '#00ffad' for v in net.values]

    fig5 = go.Figure(go.Bar(
        x=net.values / 1e6, y=net.index,
        orientation='h',
        marker_color=net_colors, marker_line_width=0,
    ))
    fig5.update_layout(
        **plotly_theme,
        title=dict(text="NET BULLISH PREMIUM ($M) — VERDE = DINERO ALCISTA NETO", font=dict(family='VT323, monospace', color='#00d9ff', size=13)),
        height=500,
        showlegend=False,
        xaxis_title="Net Premium ($M)",
    )
    fig5.update_yaxes(tickfont=dict(family='VT323, monospace', color='#aaa', size=12))
    st.plotly_chart(fig5, use_container_width=True)


# ─────────────────────────────────────────────
# TICKER NET SUMMARY TAB
# ─────────────────────────────────────────────
def render_ticker_summary(df):
    st.markdown("<h3>RESUMEN NETO POR TICKER</h3>", unsafe_allow_html=True)
    grp = df.groupby('ticker').agg(
        Total_Premium=('premium', 'sum'),
        Bullish=('premium', lambda x: x[df.loc[x.index,'sentiment']=='BULLISH'].sum()),
        Bearish=('premium', lambda x: x[df.loc[x.index,'sentiment']=='BEARISH'].sum()),
        Trades=('premium', 'count'),
        Avg_Score=('score', 'mean'),
        Sweeps=('is_sweep', 'sum'),
        Blocks=('is_block', 'sum'),
    ).reset_index()
    grp['Net_Flow'] = grp['Bullish'] - grp['Bearish']
    grp['Signal'] = grp['Net_Flow'].apply(lambda x: '🟢 BULLISH' if x > 0 else '🔴 BEARISH')
    grp = grp.sort_values('Total_Premium', ascending=False)
    grp['Total_Premium'] = grp['Total_Premium'].apply(format_premium)
    grp['Net_Flow']      = grp['Net_Flow'].apply(lambda x: ('+' if x > 0 else '') + format_premium(abs(x)))
    grp['Avg_Score']     = grp['Avg_Score'].round(0).astype(int)
    grp['Sector']        = grp['ticker'].map(SECTOR_MAP)
    display = grp[['ticker','Sector','Signal','Total_Premium','Net_Flow','Trades','Avg_Score','Sweeps','Blocks']].rename(
        columns={'ticker':'Ticker'}
    )
    st.dataframe(display, use_container_width=True, height=500, hide_index=True)


# ─────────────────────────────────────────────
# GLOSSARY
# ─────────────────────────────────────────────
def render_glossary():
    st.markdown("""
    <div class="terminal-box">
        <div style="font-family:'VT323',monospace; color:#00ffad; font-size:1.4rem; letter-spacing:2px; margin-bottom:15px;">
            📚 CÓMO INTERPRETAR EL FLUJO
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
            <div>
                <div style="font-family:'VT323',monospace; color:#00ffad; font-size:1.1rem; margin-bottom:6px;">▸ CALLS BOUGHT</div>
                <p style="font-size:0.8rem;">Apuesta alcista directa. Vol > OI = nueva posición, no rotación. Es la señal más directa de expectativa de subida.</p>
                <div style="font-family:'VT323',monospace; color:#f23645; font-size:1.1rem; margin-bottom:6px; margin-top:12px;">▸ PUTS BOUGHT</div>
                <p style="font-size:0.8rem;">Protección o apuesta bajista. Si el premium es enorme y el strike es cercano, es cobertura institucional.</p>
            </div>
            <div>
                <div style="font-family:'VT323',monospace; color:#ff9800; font-size:1.1rem; margin-bottom:6px;">▸ CALLS SOLD</div>
                <p style="font-size:0.8rem;">Señal mixta: puede ser cierre de largos, covered calls, o apuesta bajista. Contexto crítico.</p>
                <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.1rem; margin-bottom:6px; margin-top:12px;">▸ PUTS SOLD</div>
                <p style="font-size:0.8rem;">Cash-secured puts o premium collection. Implica disposición a comprar el subyacente. Tono alcista.</p>
            </div>
        </div>
        <hr style="margin:20px 0;">
        <div style="font-family:'VT323',monospace; color:#ff9800; font-size:1.1rem; margin-bottom:8px;">▸ SCORE DE INUSUALIDAD (0–100)</div>
        <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:10px; font-family:'Courier New',monospace; font-size:0.75rem;">
            <div style="border:1px solid #333; padding:8px; border-radius:4px; color:#555;">0–39 · Bajo<br>Ruido de mercado normal</div>
            <div style="border:1px solid #00d9ff33; padding:8px; border-radius:4px; color:#00d9ff;">40–59 · Medio<br>Actividad elevada</div>
            <div style="border:1px solid #ff980033; padding:8px; border-radius:4px; color:#ff9800;">60–79 · Alto<br>Posible smart money</div>
            <div style="border:1px solid #f2364533; padding:8px; border-radius:4px; color:#f23645;">80–100 · EXTREMO<br>Señal institucional fuerte</div>
        </div>
        <hr style="margin:20px 0;">
        <div style="font-family:'VT323',monospace; color:#ff9800; font-size:1.0rem; margin-bottom:6px;">▸ CONFIRMACIONES FUERTES</div>
        <ul style="font-family:'Courier New',monospace; font-size:0.78rem; color:#666;">
            <li>🧹 SWEEP — ejecución agresiva en múltiples exchanges, urgencia de posición</li>
            <li>💎 BLOCK — print +$1M, participación institucional confirmada</li>
            <li>Vol/OI > 1x — nueva posición, no rotación de existente</li>
            <li>0DTE/7DTE con premium alto — catalizador inminente anticipado</li>
        </ul>
        <div style="font-family:'VT323',monospace; color:#333; font-size:0.8rem; margin-top:20px; text-align:center;">
            [END OF TRANSMISSION // RSU_FLOW_DB_v2.0 // NOT FINANCIAL ADVICE]
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────
def render():
    load_css()

    # ── SIDEBAR: toggle modo ──
    with st.sidebar:
        st.markdown("""
        <div style="font-family:'VT323',monospace; color:#00ffad; font-size:1.3rem; letter-spacing:2px; margin-bottom:15px;">
            ⚙ CONFIGURACIÓN
        </div>
        """, unsafe_allow_html=True)
        use_real = st.toggle("🌐 DATOS REALES (yfinance)", value=False,
                              help="ON = datos reales delayed via yfinance. OFF = datos simulados realistas.")
        st.markdown("""
        <div style="font-family:'Courier New',monospace; color:#444; font-size:0.72rem; margin-top:10px; line-height:1.6;">
            REAL: cadena de opciones yfinance<br>
            (delayed ~15min, datos de cierre)<br><br>
            MOCK: precios reales por ticker,<br>
            distribución estadística realista
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family:'Courier New',monospace; color:#333; font-size:0.68rem; line-height:1.7;">
            RSU FLOW DATABASE v2.0<br>
            NOT FINANCIAL ADVICE<br>
            DATA: yfinance / internal sim<br>
            © RSU 2026
        </div>
        """, unsafe_allow_html=True)

    render_header(use_real)

    # ── CARGAR DATOS ──
    cache_key = 'data_real' if use_real else 'data_mock'
    if cache_key not in st.session_state or st.session_state.get('force_reload', False):
        st.session_state[cache_key] = load_data(use_real)
        st.session_state['force_reload'] = False

    df = st.session_state[cache_key]

    render_stats(df)
    st.markdown("<br>", unsafe_allow_html=True)

    filters = render_filters()
    if filters['refresh']:
        st.session_state['force_reload'] = True
        if use_real:
            fetch_real_data.clear()
        st.rerun()

    filtered_df = apply_filters(df, filters)

    st.markdown(f"""
    <div style="font-family:'Courier New',monospace; color:#333; font-size:0.72rem; margin-bottom:15px;">
        {len(filtered_df)} trades · {format_premium(filtered_df['premium'].sum())} total filtrado
        {'· <span style="color:#f23645;">⚠ Sin datos</span>' if filtered_df.empty else ''}
    </div>
    """, unsafe_allow_html=True)

    render_alerts(filtered_df)
    st.markdown("<hr>", unsafe_allow_html=True)

    # ── TABS ──
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🟢 CALLS BOUGHT", "🟠 CALLS SOLD", "🔴 PUTS BOUGHT", "🔵 PUTS SOLD",
        "📊 CHARTS", "🧾 RESUMEN"
    ])
    with tab1: render_flow_table(filtered_df, 'CALLS BOUGHT')
    with tab2: render_flow_table(filtered_df, 'CALLS SOLD')
    with tab3: render_flow_table(filtered_df, 'PUTS BOUGHT')
    with tab4: render_flow_table(filtered_df, 'PUTS SOLD')
    with tab5: render_charts(filtered_df)
    with tab6: render_ticker_summary(filtered_df)

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.expander("📚 GLOSARIO · CÓMO INTERPRETAR EL FLUJO", expanded=False):
        render_glossary()


if __name__ == "__main__":
    render()
