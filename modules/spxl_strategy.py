# modules/spxl_strategy.py  — v4.0 (optimizations + roadmap title style)
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import streamlit.components.v1 as components
import os
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# STRATEGY CONFIG  ← edit all parameters here
# ══════════════════════════════════════════════════════════════════════════════
CFG = {
    "phase_drops":   [0.15, 0.10, 0.07, 0.10],   # drop from previous level
    "phase_alloc":   [0.20, 0.15, 0.20, 0.20],   # capital % per phase
    "take_profit":   0.20,                         # +20% over avg cost → sell
    "reserve_pct":   0.25,                         # cash kept in reserve
    "dd_phase_map":  [(15, "STAND BY", "#333"),
                      (25, "FASE 1",   "#00ffad"),
                      (32, "FASE 2",   "#00ffad"),
                      (39, "FASE 3",   "#ff9800"),
                      (999,"FASE 4",   "#f23645")],
}
# Convenience aliases used by backtest engine
PHASE_DROPS    = CFG["phase_drops"]
PHASE_ALLOC    = CFG["phase_alloc"]
TAKE_PROFIT_BT = CFG["take_profit"]

# ── Palette ───────────────────────────────────────────────────────────────────
C_GREEN  = "#00ffad"
C_RED    = "#f23645"
C_BLUE   = "#00d9ff"
C_ORANGE = "#ff9800"
C_BG     = "#0a0c10"
C_BG2    = "#0c0e12"

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _tv_widget(symbol: str, container_id: str, height: int = 500,
               interval: str = "D", hide_toolbar: bool = False) -> str:
    """Return a TradingView widget HTML string — DRY helper."""
    return f"""
    <div class="tradingview-widget-container">
      <div id="{container_id}"></div>
      <script src="https://s3.tradingview.com/tv.js"></script>
      <script>
      new TradingView.widget({{
        "width":"100%","height":{height},"symbol":"{symbol}",
        "interval":"{interval}","timezone":"Etc/UTC","theme":"dark","style":"1",
        "locale":"es","enable_publishing":false,
        "hide_side_toolbar":{"true" if hide_toolbar else "false"},
        "allow_symbol_change":false,"container_id":"{container_id}",
        "overrides":{{
            "paneProperties.background":"{C_BG}",
            "paneProperties.vertGridProperties.color":"#0e1116",
            "paneProperties.horzGridProperties.color":"#0e1116"
        }}
      }});
      </script>
    </div>"""


def _is_market_open() -> bool:
    """NYSE open Mon–Fri 13:30–20:00 UTC (ET±5h offset approximation)."""
    from datetime import timezone
    now_utc = datetime.now(timezone.utc)
    if now_utc.weekday() >= 5:          # Sat/Sun
        return False
    h, m = now_utc.hour, now_utc.minute
    open_min  = 13 * 60 + 30            # 09:30 ET → 13:30 UTC
    close_min = 20 * 60                 # 16:00 ET → 20:00 UTC
    return open_min <= h * 60 + m < close_min


def _phase_state(current_price: float, spxl_high: float) -> tuple:
    """Return (phase_label, phase_color) based on drawdown."""
    dd = abs((current_price - spxl_high) / spxl_high * 100)
    for threshold, label, color in CFG["dd_phase_map"]:
        if dd < threshold:
            return label, color
    return "FASE 4", "#f23645"

PLOT_LAYOUT = dict(
    paper_bgcolor=C_BG,
    plot_bgcolor=C_BG2,
    font=dict(family="Share Tech Mono", color="#888", size=11),
    margin=dict(l=50, r=20, t=40, b=40),
    xaxis=dict(gridcolor="#0e1116", showgrid=True, zeroline=False,
               tickfont=dict(family="Share Tech Mono", color="#555")),
    yaxis=dict(gridcolor="#0e1116", showgrid=True, zeroline=False,
               tickfont=dict(family="Share Tech Mono", color="#555")),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1a1e26",
                font=dict(family="Share Tech Mono", color="#888")),
)

# ══════════════════════════════════════════════════════════════════════════════
# BACKTEST ENGINE
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def load_spxl_history():
    spxl    = yf.Ticker("SPXL")
    df_real = spxl.history(start="2008-11-05", end="2025-01-01")[["Close"]].copy()
    df_real.index = df_real.index.tz_localize(None)
    df_real.columns = ["price"]

    spy    = yf.Ticker("SPY")
    df_spy = spy.history(start="2000-01-01", end="2008-11-05")[["Close"]].copy()
    df_spy.index = df_spy.index.tz_localize(None)
    df_spy.columns = ["spy"]

    daily_drag   = (1 - 0.01) ** (1 / 252)
    spy_ret      = df_spy["spy"].pct_change().fillna(0)
    synth_ret    = (spy_ret * 3 * daily_drag).fillna(0)
    first_real   = df_real["price"].iloc[0]
    synth_prices = (1 + synth_ret).cumprod()
    synth_prices = synth_prices * (first_real / synth_prices.iloc[-1])

    df_synth = pd.DataFrame({"price": synth_prices}, index=df_spy.index)
    df = pd.concat([df_synth, df_real])
    df = df[~df.index.duplicated(keep="last")].sort_index().dropna()
    return df


def run_backtest(df, initial_capital=100_000):
    prices        = df["price"].values
    dates         = df.index.values
    cash          = initial_capital
    shares        = 0.0
    avg_cost      = 0.0
    cycle_high    = prices[0]
    phase_entered = [False] * 4
    phase_levels  = [None] * 4
    trades        = []
    equity_curve  = []
    bnh_shares    = (initial_capital * 0.75) / prices[0]
    bnh_cash      = initial_capital * 0.25
    peak_equity   = initial_capital

    for date, price in zip(dates, prices):
        if shares == 0 and price > cycle_high:
            cycle_high    = price
            phase_entered = [False] * 4
            phase_levels  = [None] * 4

        p1     = cycle_high * (1 - PHASE_DROPS[0])
        p2     = p1         * (1 - PHASE_DROPS[1])
        p3     = p2         * (1 - PHASE_DROPS[2])
        p4     = p3         * (1 - PHASE_DROPS[3])
        levels = [p1, p2, p3, p4]

        for ph in range(4):
            if not phase_entered[ph] and price <= levels[ph]:
                alloc_cash = initial_capital * PHASE_ALLOC[ph]
                if cash >= alloc_cash:
                    bought      = alloc_cash / price
                    total_cost  = avg_cost * shares + alloc_cash
                    shares     += bought
                    avg_cost    = total_cost / shares
                    cash       -= alloc_cash
                    phase_entered[ph] = True
                    phase_levels[ph]  = price

        if shares > 0 and avg_cost > 0 and price >= avg_cost * (1 + TAKE_PROFIT_BT):
            trades.append({
                "exit_date":   pd.Timestamp(date),
                "exit_price":  price,
                "avg_cost":    avg_cost,
                "gain_pct":    (price - avg_cost) / avg_cost * 100,
                "profit":      (price - avg_cost) * shares,
                "phases_used": sum(phase_entered),
                "shares":      shares,
            })
            cash         += shares * price
            shares        = 0.0
            avg_cost      = 0.0
            cycle_high    = price
            phase_entered = [False] * 4
            phase_levels  = [None] * 4

        portfolio_val = cash + shares * price
        equity_curve.append({"date": pd.Timestamp(date), "equity": portfolio_val})
        if portfolio_val > peak_equity:
            peak_equity = portfolio_val

    bnh_equity = [{"date": pd.Timestamp(d), "bnh": bnh_cash + bnh_shares * p}
                  for d, p in zip(dates, prices)]

    return trades, pd.DataFrame(equity_curve), pd.DataFrame(bnh_equity)


def compute_stats(trades, eq_df, bnh_df, initial_capital):
    if not trades:
        return {}
    t            = pd.DataFrame(trades)
    final_equity = eq_df["equity"].iloc[-1]
    final_bnh    = bnh_df["bnh"].iloc[-1]
    years        = (eq_df["date"].iloc[-1] - eq_df["date"].iloc[0]).days / 365.25
    cagr         = ((final_equity / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
    bnh_cagr     = ((final_bnh / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
    strat_dd     = ((eq_df["equity"] - eq_df["equity"].cummax()) / eq_df["equity"].cummax() * 100).min()
    bnh_dd       = ((bnh_df["bnh"]   - bnh_df["bnh"].cummax())   / bnh_df["bnh"].cummax()   * 100).min()
    return {
        "n_trades":     len(t),
        "win_rate":     (t["gain_pct"] > 0).mean() * 100,
        "avg_gain":     t["gain_pct"].mean(),
        "best_trade":   t["gain_pct"].max(),
        "worst_trade":  t["gain_pct"].min(),
        "total_return": (final_equity - initial_capital) / initial_capital * 100,
        "cagr":         cagr,
        "max_dd":       strat_dd,
        "bnh_return":   (final_bnh - initial_capital) / initial_capital * 100,
        "bnh_cagr":     bnh_cagr,
        "bnh_max_dd":   bnh_dd,
        "final_equity": final_equity,
        "final_bnh":    final_bnh,
        "avg_phases":   t["phases_used"].mean(),
    }


def chart_equity(eq_df, bnh_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bnh_df["date"], y=bnh_df["bnh"],
        name="BUY & HOLD SPXL", line=dict(color="#333", width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(x=eq_df["date"], y=eq_df["equity"],
        name="ESTRATEGIA RSU", line=dict(color=C_GREEN, width=2),
        fill="tozeroy", fillcolor="rgba(0,255,173,0.04)"))
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="CURVA DE EQUITY // ESTRATEGIA vs BUY & HOLD",
                   font=dict(family="VT323", size=18, color=C_GREEN), x=0.01),
        yaxis_title="USD", height=380)
    return fig


def chart_drawdown(eq_df, bnh_df):
    bnh_dd   = (bnh_df["bnh"]   - bnh_df["bnh"].cummax())   / bnh_df["bnh"].cummax()   * 100
    strat_dd = (eq_df["equity"] - eq_df["equity"].cummax()) / eq_df["equity"].cummax() * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bnh_df["date"], y=bnh_dd, name="BUY & HOLD",
        line=dict(color="#555", width=1, dash="dot"),
        fill="tozeroy", fillcolor="rgba(242,54,69,0.04)"))
    fig.add_trace(go.Scatter(x=eq_df["date"], y=strat_dd, name="ESTRATEGIA RSU",
        line=dict(color=C_ORANGE, width=1.5),
        fill="tozeroy", fillcolor="rgba(255,152,0,0.06)"))
    for yr, lbl, col in [("2002-10-09","DOT-COM","#f23645"),("2009-03-09","GFC 2008","#f23645"),
                          ("2020-03-23","COVID","#ff9800"),("2022-10-12","BEAR 22","#ff9800")]:
        fig.add_vline(x=yr, line_width=1, line_dash="dash", line_color=col, opacity=0.4,
                      annotation_text=lbl,
                      annotation_font=dict(family="VT323", size=12, color=col),
                      annotation_position="top right")
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="DRAWDOWN COMPARADO // ESTRATEGIA vs BUY & HOLD",
                   font=dict(family="VT323", size=18, color=C_ORANGE), x=0.01),
        yaxis_title="%", height=320)
    return fig


def chart_trades(trades):
    if not trades:
        return None
    t      = pd.DataFrame(trades).sort_values("exit_date")
    colors = [C_GREEN if g > 0 else C_RED for g in t["gain_pct"]]
    fig    = go.Figure()
    fig.add_trace(go.Bar(x=t["exit_date"], y=t["gain_pct"],
        marker_color=colors, marker_line_color="rgba(0,0,0,0)"))
    fig.add_hline(y=TAKE_PROFIT_BT * 100, line_dash="dot", line_color=C_GREEN, opacity=0.5,
                  annotation_text="TARGET +20%",
                  annotation_font=dict(family="VT323", size=12, color=C_GREEN))
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="OPERACIONES COMPLETADAS // GANANCIA POR TRADE",
                   font=dict(family="VT323", size=18, color=C_BLUE), x=0.01),
        yaxis_title="%", height=300, bargap=0.3)
    return fig


def chart_phases(trades):
    if not trades:
        return None
    t            = pd.DataFrame(trades)
    phase_counts = t["phases_used"].value_counts().sort_index()
    fig = go.Figure(go.Bar(
        x=[f"FASES {p}" for p in phase_counts.index],
        y=phase_counts.values,
        marker_color=[C_GREEN, C_BLUE, C_ORANGE, C_RED][:len(phase_counts)],
        text=phase_counts.values,
        textfont=dict(family="VT323", color="white", size=16),
        textposition="outside"))
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="FASES ACTIVADAS POR OPERACIÓN",
                   font=dict(family="VT323", size=18, color=C_BLUE), x=0.01),
        yaxis_title="Nº OPERACIONES", height=280)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════
def render():

    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

        /* ══ BASE ══════════════════════════════════════ */
        .stApp { background: #0a0c10; }
        * { box-sizing: border-box; }

        /* Scanline overlay */
        .stApp::before {
            content: "";
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0,255,173,0.012) 2px,
                rgba(0,255,173,0.012) 4px
            );
            pointer-events: none;
            z-index: 9999;
        }

        /* ══ TYPOGRAPHY ════════════════════════════════ */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            text-transform: uppercase;
            letter-spacing: 3px;
        }
        p, li, span, div { font-family: 'Share Tech Mono', monospace; }

        /* ══ ANIMATIONS ════════════════════════════════ */
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50%       { opacity: 0.2; }
        }
        @keyframes scanBeam {
            0%   { opacity: 0.5; left: -100%; }
            100% { opacity: 1;   left: 200%;  }
        }
        @keyframes titleFlicker {
            0%, 96%, 100% { opacity: 1; }
            97%  { opacity: 0.82; }
            98%  { opacity: 1; }
            99%  { opacity: 0.88; }
        }
        @keyframes phaseGlow {
            0%, 100% { box-shadow: 0 0 15px #00ffad08; }
            50%       { box-shadow: 0 0 30px #00ffad20; }
        }
        @keyframes fadeSlideIn {
            from { opacity: 0; transform: translateY(6px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* ══ MAIN HEADER ═══════════════════════════════ */
        .main-header {
            background: #0a0c10;
            border: 1px solid #00ffad44;
            border-radius: 4px;
            padding: 40px 30px 28px;
            margin-bottom: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
            box-shadow: 0 0 60px #00ffad08, inset 0 0 80px #00ffad04;
        }
        .main-header::before {
            content: "";
            position: absolute;
            top: 0; height: 2px; width: 40%;
            background: linear-gradient(90deg, transparent, #00ffad, transparent);
            animation: scanBeam 5s ease-in-out infinite;
        }
        .main-header::after {
            content: "";
            position: absolute;
            bottom: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad33, transparent);
        }
        .header-corner-tl, .header-corner-tr,
        .header-corner-bl, .header-corner-br {
            position: absolute;
            width: 14px; height: 14px;
            border-color: #00ffad55; border-style: solid;
        }
        .header-corner-tl { top:8px; left:8px;    border-width: 2px 0 0 2px; }
        .header-corner-tr { top:8px; right:8px;   border-width: 2px 2px 0 0; }
        .header-corner-bl { bottom:8px; left:8px;  border-width: 0 0 2px 2px; }
        .header-corner-br { bottom:8px; right:8px; border-width: 0 2px 2px 0; }

        .header-pre {
            font-family: 'VT323', monospace;
            font-size: 0.82rem; color: #3a3a3a;
            letter-spacing: 3px; margin-bottom: 10px;
        }
        .main-title {
            font-family: 'VT323', monospace !important;
            color: #00ffad;
            font-size: 3.5rem;
            font-weight: 400;
            margin: 0 auto;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 6px;
            text-shadow: 0 0 20px #00ffad66;
            line-height: 1.15;
            border-bottom: 2px solid #00ffad;
            padding-bottom: 12px;
            animation: titleFlicker 8s ease-in-out infinite;
        }
        .sub-title {
            font-family: 'VT323', monospace;
            color: #00d9ff; font-size: 0.95rem;
            margin-top: 14px; letter-spacing: 5px; opacity: 0.85;
        }
        .header-post {
            font-family: 'VT323', monospace;
            font-size: 0.72rem; color: #2a2a2a;
            margin-top: 16px; letter-spacing: 2px;
        }
        .market-status {
            display: inline-flex; align-items: center; gap: 6px;
            font-family: 'VT323', monospace;
            font-size: 0.78rem; letter-spacing: 2px; margin-top: 10px;
        }
        .status-dot {
            width: 7px; height: 7px; border-radius: 50%;
            background: #00ffad; box-shadow: 0 0 8px #00ffad;
            animation: blink 1.4s ease-in-out infinite;
        }
        .status-dot.closed {
            background: #f23645; box-shadow: 0 0 8px #f23645; animation: none;
        }

        /* ══ METRIC CARDS ══════════════════════════════ */
        .metric-card {
            background: #0c0e12;
            border: 1px solid #1a1e26; border-top: 2px solid #00ffad33;
            border-radius: 4px; padding: 20px; text-align: center;
            transition: border-color .3s, box-shadow .3s, transform .2s;
            position: relative;
            animation: fadeSlideIn 0.4s ease both;
        }
        .metric-card:hover {
            border-color: #00ffad66;
            box-shadow: 0 0 25px #00ffad14, 0 4px 16px rgba(0,0,0,.4);
            transform: translateY(-2px);
        }
        .metric-card::after {
            content: "";
            position: absolute; top: 6px; right: 6px;
            width: 6px; height: 6px;
            border-top: 1px solid #00ffad44; border-right: 1px solid #00ffad44;
        }
        .metric-value {
            font-family: 'VT323', monospace;
            font-size: 2.4rem; color: white; margin: 8px 0; letter-spacing: 2px;
        }
        .metric-label {
            font-family: 'Share Tech Mono', monospace;
            color: #3a3a3a; font-size: 0.68rem;
            text-transform: uppercase; letter-spacing: 2px;
        }
        .metric-change { font-family: 'VT323', monospace; font-size: 1.3rem; letter-spacing: 1px; }
        .positive { color: #00ffad; }
        .negative { color: #f23645; }
        .warning  { color: #ff9800; }

        /* ══ SECTION CONTAINERS ════════════════════════ */
        .terminal-box {
            background: linear-gradient(135deg, #0c0e12 0%, #0e1116 100%);
            border: 1px solid #00ffad1a; border-radius: 4px;
            padding: 25px 25px 20px; margin: 15px 0;
            box-shadow: 0 0 20px #00ffad06; position: relative;
        }
        .terminal-box::before {
            content: "//"; position: absolute; top: 10px; left: 15px;
            font-family: 'VT323', monospace; color: #00ffad22; font-size: 0.85rem;
        }
        .section-header-bar {
            background: #0c0e12;
            border: 1px solid #1a1e26; border-left: 3px solid #00ffad;
            padding: 11px 20px; margin-bottom: 15px;
            border-radius: 0 4px 4px 0;
            font-family: 'VT323', monospace; color: #00ffad;
            font-size: 1.15rem; letter-spacing: 3px;
            display: flex; align-items: center; gap: 10px;
            position: relative; overflow: hidden;
        }
        .section-header-bar::after {
            content: ""; position: absolute;
            top: 0; right: 0; bottom: 0; width: 40%;
            background: linear-gradient(90deg, transparent, #00ffad05);
            pointer-events: none;
        }

        /* ══ PHASE CARDS ═══════════════════════════════ */
        .phase-card {
            background: #0c0e12; border: 1px solid #1a1e26;
            border-radius: 4px; padding: 15px; margin-bottom: 10px;
            transition: all .3s; position: relative; overflow: hidden;
            font-family: 'Share Tech Mono', monospace;
        }
        .phase-card::before {
            content: ""; position: absolute;
            left: 0; top: 0; bottom: 0; width: 3px;
            background: #1a1e26; transition: background .3s;
        }
        .phase-card.active {
            border-color: #00ffad33;
            background: linear-gradient(135deg, #0c0e12 0%, #00ffad07 100%);
            animation: phaseGlow 2.5s ease-in-out infinite;
        }
        .phase-card.active::before    { background: #00ffad; }
        .phase-card.pending::before   { background: #2a3f5f; opacity: .4; }
        .phase-card.completed::before { background: #4caf50; opacity: .5; }
        .phase-card.pending    { opacity: .5; }
        .phase-card.completed  { opacity: .4; }
        .phase-number {
            position: absolute; top: 10px; right: 12px;
            font-family: 'VT323', monospace; font-size: 1.4rem;
            color: #222; letter-spacing: 1px;
        }
        .phase-card.active .phase-number    { color: #00ffad55; }
        .phase-card.completed .phase-number { color: #4caf5066; }

        /* ══ ALERT BOXES ═══════════════════════════════ */
        .alert-box {
            padding: 14px 20px; border-radius: 4px; margin: 12px 0;
            border: 1px solid; font-family: 'VT323', monospace;
            font-size: 1.1rem; letter-spacing: 2px;
            position: relative; overflow: hidden;
        }
        .alert-box::before {
            content: ""; position: absolute;
            left: 0; top: 0; bottom: 0; width: 3px;
        }
        .alert-buy    { background:#00ffad07; border-color:#00ffad44; color:#00ffad; }
        .alert-buy::before    { background: #00ffad; }
        .alert-sell   { background:#f2364506; border-color:#f2364544; color:#f23645; }
        .alert-sell::before   { background: #f23645; }
        .alert-warning{ background:#ff980007; border-color:#ff980044; color:#ff9800; }
        .alert-warning::before{ background: #ff9800; }

        /* ══ HIGHLIGHT QUOTE ═══════════════════════════ */
        .highlight-quote {
            background: #00ffad06; border: 1px solid #00ffad1a;
            border-radius: 4px; padding: 22px 30px; margin: 22px 0;
            font-family: 'VT323', monospace; font-size: 1.3rem;
            color: #00ffad; text-align: center; letter-spacing: 3px;
            position: relative;
        }
        .highlight-quote::before {
            content: "❝"; position: absolute; top: -1px; left: 14px;
            font-size: 1.8rem; color: #00ffad22; line-height: 1;
        }

        /* ══ RISK BOX ══════════════════════════════════ */
        .risk-box {
            background: linear-gradient(135deg, #110909 0%, #180d0d 100%);
            border: 1px solid #f2364520; border-left: 3px solid #f23645;
            border-radius: 0 4px 4px 0; padding: 20px; margin: 15px 0;
        }

        /* ══ STRATEGY GRID ═════════════════════════════ */
        .strategy-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px; margin: 15px 0;
        }
        .strategy-card {
            background: #0c0e12; border: 1px solid #1a1e26;
            border-top: 2px solid #00ffad2a; border-radius: 4px;
            padding: 15px; font-family: 'VT323', monospace;
            font-size: 1.05rem; color: #00ffad; letter-spacing: 1px;
            transition: border-top-color .3s, box-shadow .3s;
        }
        .strategy-card:hover { border-top-color:#00ffad88; box-shadow:0 0 16px #00ffad0a; }

        /* ══ RULE ITEMS ════════════════════════════════ */
        .rule-item {
            display: flex; align-items: flex-start; gap: 14px;
            margin: 10px 0; padding: 14px 16px;
            background: #0c0e12; border: 1px solid #1a1e26;
            border-radius: 4px; font-family: 'Share Tech Mono', monospace;
            transition: border-color .2s, background .2s;
        }
        .rule-item:hover { border-color:#00ffad22; background:#0d1015; }
        .rule-icon {
            width: 28px; height: 28px; background: #00ffad0f;
            color: #00ffad; border: 1px solid #00ffad2a; border-radius: 2px;
            display: flex; align-items: center; justify-content: center;
            font-family: 'VT323', monospace; font-size: 1.1rem; flex-shrink: 0;
            transition: background .2s;
        }
        .rule-item:hover .rule-icon { background: #00ffad1a; }

        /* ══ CDS GAUGE ═════════════════════════════════ */
        .cds-gauge {
            width: 100%; height: 22px;
            background: linear-gradient(90deg, #00ffad 0%, #7dff6b 20%, #ff9800 55%, #f23645 100%);
            border-radius: 2px; position: relative;
            margin: 20px 0 8px; border: 1px solid #1a1e26;
            box-shadow: inset 0 1px 3px rgba(0,0,0,.5);
        }
        .cds-gauge::before {
            content: ""; position: absolute; inset: 0;
            background: repeating-linear-gradient(90deg,
                transparent, transparent 12.5%,
                rgba(0,0,0,.3) 12.5%, rgba(0,0,0,.3) calc(12.5% + 1px));
            pointer-events: none;
        }
        .cds-marker {
            position: absolute; top: -9px; width: 3px; height: 40px;
            background: white;
            box-shadow: 0 0 10px rgba(255,255,255,.9), 0 0 20px rgba(255,255,255,.4);
            transition: left .6s cubic-bezier(.34,1.56,.64,1);
        }
        .cds-marker::after {
            content: ""; position: absolute; bottom: -5px; left: -4px;
            border-left: 5px solid transparent; border-right: 5px solid transparent;
            border-top: 5px solid white;
        }
        .cds-labels {
            display: flex; justify-content: space-between;
            font-family: 'VT323', monospace; color: #444;
            font-size: 0.82rem; letter-spacing: 1px; margin-top: 6px;
        }

        /* ══ HORIZONTAL RULE ═══════════════════════════ */
        hr {
            border: none; height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad33, transparent);
            margin: 28px 0;
        }

        /* ══ PROGRESS BAR ══════════════════════════════ */
        .progress-bar {
            width: 100%; height: 5px; background: #0c0e12;
            border-radius: 2px; overflow: hidden; margin: 8px 0;
            border: 1px solid #1a1e26;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ffad88 0%, #00ffad 100%);
            transition: width .6s cubic-bezier(.34,1.56,.64,1);
        }

        /* ══ CALC ITEMS ════════════════════════════════ */
        .calc-item {
            background: #0c0e12; padding: 12px 15px; border-radius: 4px;
            margin: 6px 0; border-left: 3px solid #00ffad;
            display: flex; justify-content: space-between; align-items: center;
            font-family: 'Share Tech Mono', monospace; transition: background .2s;
        }
        .calc-item:hover { background: #0e1015; }
        .calc-reserve { background: #ff980007; border-left-color: #ff9800; }
        .calc-total {
            background: #00ffad07; border: 1px solid #00ffad2a;
            border-radius: 4px; padding: 14px 15px; margin-top: 10px;
            display: flex; justify-content: space-between; align-items: center;
            font-family: 'VT323', monospace; font-size: 1.25rem;
        }

        /* ══ BACKTEST CARDS ════════════════════════════ */
        .bt-stat-card {
            background: #0c0e12; border: 1px solid #1a1e26;
            border-top: 2px solid #00ffad33; border-radius: 4px;
            padding: 16px 20px; text-align: center;
            transition: border-color .3s, box-shadow .3s, transform .2s;
        }
        .bt-stat-card:hover {
            border-color: #00ffad55;
            box-shadow: 0 0 20px #00ffad11;
            transform: translateY(-2px);
        }
        .bt-stat-val {
            font-family: 'VT323', monospace; font-size: 2rem;
            color: white; letter-spacing: 2px; margin: 4px 0;
        }
        .bt-stat-label {
            font-family: 'Share Tech Mono', monospace; color: #444;
            font-size: 0.68rem; text-transform: uppercase; letter-spacing: 2px;
        }
        .bt-positive { color: #00ffad !important; }
        .bt-negative { color: #f23645 !important; }
        .bt-warning  { color: #ff9800 !important; }
        .bt-neutral  { color: #00d9ff !important; }
        .bt-vs-box {
            background: linear-gradient(135deg, #0c0e12 0%, #0e1116 100%);
            border: 1px solid #00ffad1a; border-radius: 4px;
            padding: 20px 25px; margin: 15px 0;
        }
        .bt-disclaimer {
            font-family: 'Share Tech Mono', monospace; font-size: 0.72rem;
            color: #333; border: 1px solid #1a1e26; border-radius: 4px;
            padding: 12px 16px; margin-top: 20px; line-height: 1.8;
        }
        .bt-trade-row {
            display: grid;
            grid-template-columns: 1.5fr 1fr 1fr 1fr 0.8fr;
            gap: 8px; padding: 10px 14px;
            background: #0c0e12; border: 1px solid #1a1e26;
            border-radius: 4px; margin: 4px 0;
            font-family: 'Share Tech Mono', monospace; font-size: 0.78rem;
            transition: background .15s;
        }
        .bt-trade-row:hover { background: #0e1015; }
        .bt-trade-header {
            color: #444; border-bottom: 1px solid #1a1e26;
            padding-bottom: 8px; margin-bottom: 4px; letter-spacing: 1px;
        }

        /* ══ FOOTER ════════════════════════════════════ */
        .footer {
            text-align: center; padding: 24px 20px;
            border-top: 1px solid #151820; margin-top: 35px; position: relative;
        }
        .footer::before {
            content: ""; position: absolute;
            top: 0; left: 25%; right: 25%; height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad22, transparent);
        }
        .footer p {
            font-family: 'VT323', monospace; color: #252525;
            font-size: 0.82rem; letter-spacing: 3px; margin: 0; line-height: 1.8;
        }

        /* ══ STREAMLIT OVERRIDES ═══════════════════════ */
        .stTabs [data-baseweb="tab-list"] {
            background: #0c0e12 !important;
            border-bottom: 1px solid #1a1e26 !important; gap: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            font-family: 'VT323', monospace !important;
            letter-spacing: 3px; font-size: 1rem !important;
            color: #444 !important; background: transparent !important;
            border-radius: 2px 2px 0 0 !important; padding: 10px 20px !important;
            transition: color .2s, background .2s !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #00ffad88 !important; background: #00ffad08 !important;
        }
        .stTabs [aria-selected="true"] {
            color: #00ffad !important; background: #00ffad0a !important;
            border-bottom: 2px solid #00ffad !important;
        }
        .stNumberInput input, .stSelectbox select, .stTextInput input {
            background: #0c0e12 !important; border: 1px solid #1a1e26 !important;
            color: #00ffad !important; font-family: 'Share Tech Mono', monospace !important;
            border-radius: 4px !important;
        }
        .stNumberInput input:focus, .stTextInput input:focus {
            border-color: #00ffad44 !important; box-shadow: 0 0 10px #00ffad11 !important;
        }
        .stCheckbox label {
            font-family: 'Share Tech Mono', monospace !important;
            color: #666 !important; font-size: 0.85rem !important;
        }
        .stDownloadButton button {
            background: #0c0e12 !important; border: 1px solid #00ffad44 !important;
            color: #00ffad !important; font-family: 'VT323', monospace !important;
            letter-spacing: 2px !important; font-size: 1rem !important;
            transition: all .2s !important; border-radius: 4px !important;
        }
        .stDownloadButton button:hover {
            background: #00ffad0f !important; border-color: #00ffad88 !important;
            box-shadow: 0 0 16px #00ffad18 !important;
        }
        .stSpinner > div { border-top-color: #00ffad !important; }
        [data-testid="stMetricValue"] { font-family:'VT323',monospace !important; color:white !important; }
        [data-testid="stMetricLabel"] { font-family:'Share Tech Mono',monospace !important; color:#444 !important; font-size:0.75rem !important; }
        [data-testid="stMetricDelta"] { font-family:'VT323',monospace !important; }
        ::-webkit-scrollbar       { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0a0c10; }
        ::-webkit-scrollbar-thumb { background: #1a1e26; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #00ffad33; }
    </style>
    """, unsafe_allow_html=True)

    # ── HEADER ────────────────────────────────────────────────────────────────
    now         = datetime.now()
    market_open = _is_market_open()
    dot_cls     = "status-dot" if market_open else "status-dot closed"
    status_txt  = "MERCADO ABIERTO" if market_open else "MERCADO CERRADO"

    st.markdown(f"""
    <div class="main-header">
        <div class="header-corner-tl"></div>
        <div class="header-corner-tr"></div>
        <div class="header-corner-bl"></div>
        <div class="header-corner-br"></div>
        <div class="header-pre">[SECURE CONNECTION ESTABLISHED // RSU TRADING SYSTEM v4.0]</div>
        <h1 class="main-title">📈 ESTRATEGIA SPXL</h1>
        <div class="sub-title">REDISTRIBUTION STRATEGY RESEARCH UNIT // SISTEMA ACTIVO</div>
        <div class="market-status">
            <div class="{dot_cls}"></div>
            <span style="color:#333;">{status_txt} //</span>
            <span style="color:#2a2a2a;">{now.strftime('%Y-%m-%d %H:%M UTC')}</span>
        </div>
        <div class="header-post">[NODE: RSU-ALPHA // ENCRYPTION: AES-256 // LATENCY: &lt;1ms]</div>
    </div>
    """, unsafe_allow_html=True)

    # ── MARKET DATA  (split fetchers so one failure doesn't break both) ───────
    @st.cache_data(ttl=300)
    def _fetch_spxl():
        hist = yf.Ticker("SPXL").history(period="1y")
        if hist.empty:
            return None
        cur  = float(hist['Close'].iloc[-1])
        prev = float(hist['Close'].iloc[-2])
        high = float(hist['High'].max())
        low  = float(hist['Low'].min())
        d    = CFG["phase_drops"]
        p1   = high * (1 - d[0])
        p2   = p1   * (1 - d[1])
        p3   = p2   * (1 - d[2])
        p4   = p3   * (1 - d[3])
        return {
            "price":    cur,
            "change":   (cur - prev) / prev * 100,
            "high":     high,
            "low":      low,
            "drawdown": (cur - high) / high * 100,
            "levels":   {"phase1": p1, "phase2": p2, "phase3": p3, "phase4": p4},
        }

    @st.cache_data(ttl=300)
    def _fetch_spx():
        hist = yf.Ticker("^GSPC").history(period="2d")
        if len(hist) < 2:
            return {"price": 0, "change": 0}
        return {
            "price":  float(hist['Close'].iloc[-1]),
            "change": (float(hist['Close'].iloc[-1]) - float(hist['Close'].iloc[-2])) /
                       float(hist['Close'].iloc[-2]) * 100,
        }

    with st.spinner("// SINCRONIZANDO DATOS DE MERCADO..."):
        try:
            spxl_data = _fetch_spxl()
            spx_data  = _fetch_spx()
        except Exception as e:
            st.error(f"Error obteniendo datos de mercado: {e}")
            return

    if spxl_data is None:
        st.error("No se pudieron obtener datos de SPXL")
        return

    # Unified dict for the rest of the UI (keeps existing variable names)
    data = {
        "spxl_price":  spxl_data["price"],
        "spxl_change": spxl_data["change"],
        "spxl_high":   spxl_data["high"],
        "spxl_low":    spxl_data["low"],
        "drawdown":    spxl_data["drawdown"],
        "spx_price":   spx_data["price"],
        "spx_change":  spx_data["change"],
        "buy_levels":  spxl_data["levels"],
    }

    # ── METRIC CARDS ──────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        c = "positive" if data['spxl_change'] >= 0 else "negative"
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">// SPXL ACTUAL</div>
            <div class="metric-value">${data['spxl_price']:.2f}</div>
            <div class="metric-change {c}">{data['spxl_change']:+.2f}%</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        c2 = "positive" if data['spx_change'] >= 0 else "negative"
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">// S&amp;P 500</div>
            <div class="metric-value">{data['spx_price']:,.0f}</div>
            <div class="metric-change {c2}">{data['spx_change']:+.2f}%</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        ddc = "positive" if data['drawdown'] > -10 else "warning" if data['drawdown'] > -15 else "negative"
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">// DRAWDOWN vs MAX</div>
            <div class="metric-value {ddc}">{data['drawdown']:.1f}%</div>
            <div class="metric-change" style="color:#2a2a2a;">MAX: ${data['spxl_high']:.2f}</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        ph, phc = _phase_state(data['spxl_price'], data['spxl_high'])
        dd = abs(data['drawdown'])
        st.markdown(f"""<div class="metric-card" style="border-top-color:{phc}44;">
            <div class="metric-label">// ESTADO</div>
            <div class="metric-value" style="color:{phc}; font-size:1.9rem;">{ph}</div>
            <div class="metric-change" style="color:#2a2a2a;">DD: {dd:.1f}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "DASHBOARD", "ESTRATEGIA", "CALCULADORA", "RIESGO CDS", "BACKTEST"
    ])

    # ════════════════════════════════════════════
    # TAB 1: DASHBOARD
    # ════════════════════════════════════════════
    with tab1:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.markdown('<div class="section-header-bar">▸ GRÁFICO SPXL // NIVELES</div>',
                        unsafe_allow_html=True)
            components.html(_tv_widget("AMEX:SPXL", "tv_spxl", height=500), height=520)

        with col_right:
            st.markdown('<div class="section-header-bar">▸ SEÑALES // FASES</div>',
                        unsafe_allow_html=True)
            cur    = data['spxl_price']
            levels = data['buy_levels']
            phases = [
                ("FASE 1: COMPRA INICIAL",  levels['phase1'], 0.20, cur <= levels['phase1']),
                ("FASE 2: SEGUNDA ENTRADA", levels['phase2'], 0.15, cur <= levels['phase2']),
                ("FASE 3: TERCERA ENTRADA", levels['phase3'], 0.20, cur <= levels['phase3']),
                ("FASE 4: ENTRADA FINAL",   levels['phase4'], 0.20, cur <= levels['phase4']),
            ]
            for i, (name, price, alloc, is_active) in enumerate(phases, 1):
                if is_active:
                    sc, st_txt = "active",    ">> ACTIVA"
                elif cur > price:
                    sc, st_txt = "pending",   "__ ESPERA"
                else:
                    sc, st_txt = "completed", "// DONE"
                dist  = (cur - price) / price * 100
                dcol  = "#00ffad" if dist <= 0 else "#f23645"
                prog  = min(100, max(0, (data['spxl_high'] - cur) /
                            (data['spxl_high'] - price) * 100)) if data['spxl_high'] > price else 0
                st.markdown(f"""
                <div class="phase-card {sc}">
                    <div class="phase-number">[{i}]</div>
                    <div style="font-family:'VT323',monospace;color:#00ffad;font-size:.9rem;
                                letter-spacing:2px;margin-bottom:6px;">{name}</div>
                    <div style="display:flex;justify-content:space-between;align-items:baseline;">
                        <span style="font-family:'VT323',monospace;color:white;font-size:1.55rem;
                                     letter-spacing:2px;">${price:.2f}</span>
                        <span style="font-family:'VT323',monospace;color:#333;font-size:.8rem;">{st_txt}</span>
                    </div>
                    <div class="progress-bar"><div class="progress-fill" style="width:{prog:.0f}%"></div></div>
                    <div style="margin-top:6px;font-family:'Share Tech Mono',monospace;
                                font-size:.72rem;display:flex;gap:12px;">
                        <span style="color:#333;">ALLOC: {alloc:.0%}</span>
                        <span style="color:{dcol};">DIST: {dist:+.1f}%</span>
                    </div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if cur <= levels['phase4']:
                st.markdown('<div class="alert-box alert-sell">🚨 COMPRA MÁXIMA ACTIVA<br>TODAS LAS FASES DISPONIBLES</div>', unsafe_allow_html=True)
            elif cur <= levels['phase1']:
                st.markdown('<div class="alert-box alert-buy">✅ COMPRA ACTIVA<br>EJECUTAR PROTOCOLO</div>', unsafe_allow_html=True)
            else:
                d = (cur - levels['phase1']) / levels['phase1'] * 100
                st.markdown(f'<div class="alert-box alert-warning">⏳ STAND BY<br>FALTAN {d:.1f}% PARA FASE 1</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════
    # TAB 2: ESTRATEGIA
    # ════════════════════════════════════════════
    with tab2:
        st.markdown("""
        <div class="terminal-box">
            <div style="font-family:'VT323',monospace;color:#00d9ff;font-size:1.35rem;
                        letter-spacing:3px;margin-bottom:12px;">PREMISA FUNDAMENTAL</div>
            <p style="color:#aaa;font-size:.9rem;line-height:1.9;margin:0;">
                Estrategia basada en que el S&amp;P 500 mantiene
                <span style="color:#00ffad;">macro tendencia alcista</span> a largo plazo.
                SPXL amplifica ese movimiento 3x. La estrategia explota correcciones
                para acumular posición escalonada.
            </p>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header-bar">▸ REGLAS DE ENTRADA</div>', unsafe_allow_html=True)
        for icon, title, desc in [
            ("1","PRIMERA CAÍDA (-15% desde máximo)","Invertir 20% del capital asignado"),
            ("2","SEGUNDA CAÍDA (-10% desde Fase 1)", "Invertir 15% del capital asignado"),
            ("3","TERCERA CAÍDA (-7% desde Fase 2)",  "Invertir 20% del capital asignado"),
            ("4","CUARTA CAÍDA  (-10% desde Fase 3)", "Invertir 20% del capital // 75% total"),
        ]:
            st.markdown(f"""
            <div class="rule-item">
                <div class="rule-icon">{icon}</div>
                <div>
                    <div style="color:white;font-size:.88rem;margin-bottom:4px;">{title}</div>
                    <div style="color:#444;font-size:.78rem;">{desc}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header-bar" style="margin-top:22px;">▸ REGLA DE SALIDA</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="rule-item" style="border-left:3px solid #f23645;">
            <div class="rule-icon" style="border-color:#f2364522;color:#f23645;background:#f2364509;">$</div>
            <div>
                <div style="color:white;font-size:.88rem;margin-bottom:4px;">TAKE PROFIT (+20% sobre precio medio)</div>
                <div style="color:#444;font-size:.78rem;">Vender toda la posición al alcanzar objetivo. Sin parciales.</div>
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="highlight-quote" style="margin-top:28px;">"LA CAÍDA NO ES EL PROBLEMA. ES LA OPORTUNIDAD."</div>', unsafe_allow_html=True)

        pdf_path = "assets/SPXL.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button("▸ DESCARGAR ESTRATEGIA PDF", pdf_bytes,
                               "SPXL.pdf", "application/pdf", use_container_width=True)

    # ════════════════════════════════════════════
    # TAB 3: CALCULADORA
    # ════════════════════════════════════════════
    with tab3:
        st.markdown('<div class="section-header-bar">▸ CALCULADORA DE CAPITAL</div>', unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        lv = data['buy_levels']

        with col_c1:
            st.markdown('<div style="font-family:\'VT323\',monospace;color:#333;font-size:.82rem;letter-spacing:2px;margin-bottom:10px;">// INPUT PARAMETERS</div>', unsafe_allow_html=True)
            capital_total     = st.number_input("Capital Total ($):", min_value=1000, value=10000, step=1000)
            tiene_posicion    = st.checkbox("¿Tienes posición abierta?")
            if tiene_posicion:
                precio_medio      = st.number_input("Precio medio ($):", min_value=0.0, value=0.0, step=0.1)
                cantidad_acciones = st.number_input("Nº Acciones:", min_value=0, value=0, step=1)
            else:
                precio_medio, cantidad_acciones = 0, 0

        with col_c2:
            st.markdown('<div style="font-family:\'VT323\',monospace;color:#333;font-size:.82rem;letter-spacing:2px;margin-bottom:10px;">// ALLOCATION OUTPUT</div>', unsafe_allow_html=True)
            total_inv = 0
            for fase, pct, precio in [("FASE 1",0.20,lv['phase1']),("FASE 2",0.15,lv['phase2']),
                                       ("FASE 3",0.20,lv['phase3']),("FASE 4",0.20,lv['phase4'])]:
                monto = capital_total * pct
                total_inv += monto
                st.markdown(f"""
                <div class="calc-item">
                    <span style="color:#888;font-size:.85rem;">{fase}</span>
                    <div style="text-align:right;">
                        <span style="color:#00ffad;font-family:'VT323',monospace;font-size:1.25rem;">${monto:,.0f}</span>
                        <span style="color:#2a2a2a;font-size:.72rem;margin-left:8px;">@ ${precio:.2f}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
            reserva = capital_total * 0.25
            st.markdown(f"""
            <div class="calc-item calc-reserve">
                <span style="color:#555;font-size:.85rem;">RESERVA (25%)</span>
                <span style="color:#ff9800;font-family:'VT323',monospace;font-size:1.25rem;">${reserva:,.0f}</span>
            </div>
            <div class="calc-total">
                <span style="color:#888;">TOTAL A DESPLEGAR</span>
                <span style="color:#00ffad;">${total_inv:,.0f}</span>
            </div>""", unsafe_allow_html=True)

        if tiene_posicion and precio_medio > 0:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="section-header-bar">▸ ESTADO POSICIÓN ACTUAL</div>', unsafe_allow_html=True)
            valor_actual = cantidad_acciones * data['spxl_price']
            costo_total  = cantidad_acciones * precio_medio
            pnl_pct      = (valor_actual - costo_total) / costo_total * 100 if costo_total > 0 else 0
            target_price = precio_medio * 1.20
            c1, c2, c3   = st.columns(3)
            c1.metric("Valor Actual",    f"${valor_actual:,.2f}", f"{pnl_pct:+.2f}%")
            c2.metric("Objetivo Venta",  f"${target_price:.2f}", "+20%")
            c3.metric("Distancia Target",f"{((target_price - data['spxl_price']) / data['spxl_price'] * 100):.2f}%")
            if data['spxl_price'] >= target_price:
                st.balloons()
                st.markdown('<div class="alert-box alert-sell">🎯 OBJETIVO ALCANZADO // EJECUTAR SALIDA TOTAL</div>', unsafe_allow_html=True)
            else:
                rem = (target_price - data['spxl_price']) / data['spxl_price'] * 100
                st.markdown(f'<div class="alert-box alert-warning">⏳ EN POSICIÓN // FALTAN {rem:.1f}% PARA TARGET</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════
    # TAB 4: RIESGO CDS
    # ════════════════════════════════════════════
    with tab4:
        st.markdown('<div class="section-header-bar">▸ RIESGO SISTÉMICO // CDS MONITOR</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="terminal-box">
            <div style="font-family:'VT323',monospace;color:#00d9ff;font-size:1rem;letter-spacing:2px;margin-bottom:6px;">
                ÍNDICE: BAMLH0A0HYM2</div>
            <div style="font-family:'Share Tech Mono',monospace;color:#444;font-size:.78rem;">
                ICE BofA US High Yield Index Option-Adjusted Spread</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("""
        <div style="margin:22px 0 5px;font-family:'VT323',monospace;color:#333;font-size:.82rem;letter-spacing:2px;">
            // NIVEL DE ESTRÉS SISTÉMICO</div>
        <div class="cds-gauge"><div class="cds-marker" style="left:30%;"></div></div>
        <div class="cds-labels">
            <span style="color:#00ffad;">NORMAL</span>
            <span>ATENCIÓN</span><span>PELIGRO</span>
            <span style="color:#f23645;">CRISIS &gt;10.7</span>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        components.html(
            _tv_widget("FRED:BAMLH0A0HYM2", "tv_cds", height=400,
                       interval="W", hide_toolbar=True),
            height=420)
        st.markdown("""
        <div class="risk-box" style="margin-top:20px;">
            <div style="font-family:'VT323',monospace;color:#f23645;font-size:1.15rem;letter-spacing:2px;margin-bottom:10px;">
                ⚠ PROTOCOLO DE CRISIS</div>
            <div style="font-family:'Share Tech Mono',monospace;color:#777;font-size:.82rem;line-height:1.9;">
                Si CDS &gt; 10.7 → DETENER TODAS LAS COMPRAS INMEDIATAMENTE<br>
                No importa en qué fase esté la corrección.<br>
                El stop sistémico tiene prioridad absoluta sobre cualquier nivel técnico.
            </div>
        </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════
    # TAB 5: BACKTEST
    # ════════════════════════════════════════════
    with tab5:
        st.markdown('<div class="section-header-bar">▸ BACKTEST ENGINE // SIMULACIÓN 2000-2024</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="bt-disclaimer">
            // NOTA METODOLÓGICA: SPXL fue lanzado en 2008. Los datos previos (2000-2008) son
            sintéticos — calculados replicando los retornos diarios del SPY × 3 con un ajuste de
            1% anual de coste de apalancamiento. Método estándar académico para backtesting de
            ETFs apalancados. Los resultados históricos no garantizan rendimientos futuros.
        </div>""", unsafe_allow_html=True)

        with st.spinner("// CARGANDO DATOS HISTÓRICOS..."):
            try:
                df_hist = load_spxl_history()
            except Exception as e:
                st.error(f"Error cargando datos: {e}")
                st.stop()

        cfg1, cfg2, _ = st.columns([1, 1, 2])
        with cfg1:
            bt_capital = st.number_input("Capital inicial ($):", min_value=10_000,
                                         max_value=10_000_000, value=100_000, step=10_000,
                                         key="bt_capital")
        with cfg2:
            bt_year = st.selectbox("Año de inicio:", [2000, 2005, 2008, 2010, 2015],
                                   index=0, key="bt_year")

        df_bt  = df_hist[df_hist.index.year >= bt_year].copy()
        trades, eq_df, bnh_df = run_backtest(df_bt, bt_capital)
        stats  = compute_stats(trades, eq_df, bnh_df, bt_capital)

        if not stats:
            st.warning("No se completaron operaciones en el período seleccionado.")
        else:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="section-header-bar" style="margin-bottom:12px;">▸ RESULTADOS ESTRATEGIA RSU</div>', unsafe_allow_html=True)

            # Row 1
            r1 = st.columns(5)
            for col, val, lbl, cls in [
                (r1[0], f"${stats['final_equity']:,.0f}", "CAPITAL FINAL",  "bt-positive"),
                (r1[1], f"{stats['total_return']:+.1f}%", "RETORNO TOTAL",
                         "bt-positive" if stats['total_return'] > 0 else "bt-negative"),
                (r1[2], f"{stats['cagr']:+.1f}%",          "CAGR ANUAL",
                         "bt-positive" if stats['cagr'] > 0 else "bt-negative"),
                (r1[3], f"{stats['max_dd']:.1f}%",          "MAX DRAWDOWN",  "bt-warning"),
                (r1[4], f"{stats['n_trades']}",              "OPERACIONES",   "bt-neutral"),
            ]:
                with col:
                    st.markdown(f'<div class="bt-stat-card"><div class="bt-stat-label">{lbl}</div><div class="bt-stat-val {cls}">{val}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Row 2
            r2 = st.columns(5)
            for col, val, lbl, cls in [
                (r2[0], f"{stats['win_rate']:.0f}%",      "WIN RATE",        "bt-positive"),
                (r2[1], f"{stats['avg_gain']:+.1f}%",      "GANANCIA MEDIA",  "bt-positive"),
                (r2[2], f"{stats['best_trade']:+.1f}%",    "MEJOR TRADE",     "bt-positive"),
                (r2[3], f"{stats['worst_trade']:+.1f}%",   "PEOR TRADE",
                         "bt-negative" if stats['worst_trade'] < 0 else "bt-positive"),
                (r2[4], f"{stats['avg_phases']:.1f}",       "FASES MEDIAS/OP","bt-neutral"),
            ]:
                with col:
                    st.markdown(f'<div class="bt-stat-card"><div class="bt-stat-label">{lbl}</div><div class="bt-stat-val {cls}">{val}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header-bar">▸ COMPARATIVA VS BUY &amp; HOLD SPXL</div>', unsafe_allow_html=True)

            vs = st.columns(4)
            for col, bv, rv, lbl in [
                (vs[0], f"${stats['final_bnh']:,.0f}",   f"${stats['final_equity']:,.0f}",  "CAPITAL FINAL"),
                (vs[1], f"{stats['bnh_return']:+.1f}%",  f"{stats['total_return']:+.1f}%",  "RETORNO TOTAL"),
                (vs[2], f"{stats['bnh_cagr']:+.1f}%",    f"{stats['cagr']:+.1f}%",          "CAGR ANUAL"),
                (vs[3], f"{stats['bnh_max_dd']:.1f}%",   f"{stats['max_dd']:.1f}%",         "MAX DRAWDOWN"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="bt-vs-box">
                        <div class="bt-stat-label" style="margin-bottom:8px;">{lbl}</div>
                        <div style="display:flex;justify-content:space-between;align-items:baseline;">
                            <div>
                                <div class="bt-stat-label" style="color:#333;">BUY&amp;HOLD</div>
                                <div style="font-family:'VT323',monospace;font-size:1.4rem;color:#555;">{bv}</div>
                            </div>
                            <div style="font-family:'VT323',monospace;color:#1a1e26;font-size:1.2rem;">vs</div>
                            <div style="text-align:right;">
                                <div class="bt-stat-label" style="color:#00ffad88;">RSU</div>
                                <div style="font-family:'VT323',monospace;font-size:1.4rem;color:#00ffad;">{rv}</div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)

            # Charts
            st.markdown('<div class="section-header-bar">▸ CURVA DE EQUITY</div>', unsafe_allow_html=True)
            st.plotly_chart(chart_equity(eq_df, bnh_df), use_container_width=True)

            st.markdown('<div class="section-header-bar">▸ ANÁLISIS DE DRAWDOWN</div>', unsafe_allow_html=True)
            st.plotly_chart(chart_drawdown(eq_df, bnh_df), use_container_width=True)

            ch1, ch2 = st.columns([2, 1])
            with ch1:
                st.markdown('<div class="section-header-bar">▸ GANANCIA POR OPERACIÓN</div>', unsafe_allow_html=True)
                ft = chart_trades(trades)
                if ft: st.plotly_chart(ft, use_container_width=True)
            with ch2:
                st.markdown('<div class="section-header-bar">▸ FASES ACTIVADAS</div>', unsafe_allow_html=True)
                fp = chart_phases(trades)
                if fp: st.plotly_chart(fp, use_container_width=True)

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="section-header-bar">▸ REGISTRO DE OPERACIONES</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bt-trade-row bt-trade-header">
                <span>FECHA SALIDA</span><span>PRECIO SALIDA</span>
                <span>COSTE MEDIO</span><span>GANANCIA</span><span>FASES</span>
            </div>""", unsafe_allow_html=True)

            for tr in sorted(trades, key=lambda x: x["exit_date"], reverse=True)[:60]:
                gc = C_GREEN if tr["gain_pct"] > 0 else C_RED
                st.markdown(f"""
                <div class="bt-trade-row">
                    <span style="color:#888;">{tr['exit_date'].strftime('%Y-%m-%d')}</span>
                    <span style="color:white;font-family:'VT323',monospace;font-size:1rem;">${tr['exit_price']:.2f}</span>
                    <span style="color:#555;">${tr['avg_cost']:.2f}</span>
                    <span style="color:{gc};font-family:'VT323',monospace;font-size:1rem;">{tr['gain_pct']:+.1f}%</span>
                    <span style="color:#00d9ff;">{'▪' * int(tr['phases_used'])}</span>
                </div>""", unsafe_allow_html=True)

            if len(trades) > 60:
                st.markdown(f'<div style="font-family:\'VT323\',monospace;color:#333;font-size:.85rem;text-align:center;padding:12px;letter-spacing:2px;">// MOSTRANDO ÚLTIMAS 60 DE {len(trades)} OPERACIONES</div>', unsafe_allow_html=True)

            st.markdown("""
            <div class="bt-disclaimer" style="margin-top:30px;">
                ⚠ ADVERTENCIA: Simulación con supuestos simplificados. No incluye slippage,
                comisiones, impacto de mercado ni volatility drag completo del apalancamiento diario.
                Exclusivamente educativo — no constituye asesoramiento financiero.
            </div>""", unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="footer">
        <p>
            [END OF TRANSMISSION // RSU TRADING SYSTEM v4.0]<br>
            [REDISTRIBUTION STRATEGY RESEARCH UNIT // ALL RIGHTS RESERVED]
        </p>
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    render()
