# modules/spxl_strategy.py  — v7.0 (6 phases + tiered selling rules + bug fixes)
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import streamlit.components.v1 as components
import os
from datetime import datetime

try:
    from modules.telegram_notifier import (
        send_alert, build_phase_alert,
        build_target_alert, build_cds_alert,
        check_and_notify_phases, check_and_notify_cds,
    )
    TELEGRAM_OK = True
except Exception:
    TELEGRAM_OK = False

# ══════════════════════════════════════════════════════════════════════════════
# STRATEGY CONFIG  ← edit all parameters here
# ══════════════════════════════════════════════════════════════════════════════
CFG = {
    # 6 phases: drops from previous level
    "phase_drops":   [0.15, 0.10, 0.07, 0.10, 0.10, 0.10],
    # 6 phases: capital % per phase (total 90%, 10% reserve)
    "phase_alloc":   [0.20, 0.15, 0.20, 0.20, 0.15, 0.10],
    "reserve_pct":   0.10,   # 10% kept in reserve

    # ── Selling rules (tiered by phases invested) ──────────────────────────
    # Scenario A: ≤3 phases (≤55% invested)
    "sell_a_tp":          0.20,   # +20% → sell 95% of position
    "sell_a_keep":        0.05,   # keep 5% running
    "sell_a_runner_tp":   0.17,   # runner target: +17% additional
    "sell_a_trail_stop":  0.11,   # trailing stop from peak if runner fails

    # Scenario B: ≥4 phases (≥55% invested, ≤5 phases)
    "sell_b_tp":          0.10,   # +10% → sell 80% of position
    "sell_b_keep":        0.20,   # keep 20% running
    "sell_b_trail_be":    0.00,   # initial trail: break-even
    "sell_b_trail_act":   0.14,   # above +14% → trail 11% from peak
    "sell_b_trail_stop":  0.11,
    "sell_b_close_from":  0.10,   # close remaining +10% from first sell price

    # Scenario C: fully invested (all 6 phases, ~100%)
    "sell_c_trim1_pct":   0.65,   # trim 65% at +5%
    "sell_c_trim1_tp":    0.05,
    "sell_c_trail_be":    0.00,   # trail at break-even on remaining 35%
    "sell_c_trim2_pct":   0.15,   # trim 15% more at +10%
    "sell_c_trim2_tp":    0.10,
    "sell_c_final_tp":    0.20,   # close final 20% at +20%

    # dd → phase state thresholds
    "dd_phase_map":  [(15,  "STAND BY", "#333"),
                      (24,  "FASE 1",   "#00ffad"),
                      (29,  "FASE 2",   "#00ffad"),
                      (36,  "FASE 3",   "#ff9800"),
                      (43,  "FASE 4",   "#ff9800"),
                      (49,  "FASE 5",   "#f23645"),
                      (999, "FASE 6",   "#f23645")],
}
# Convenience aliases used by backtest engine
PHASE_DROPS = CFG["phase_drops"]
PHASE_ALLOC = CFG["phase_alloc"]

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
    """NYSE open Mon–Fri 09:30–16:00 ET — DST-aware via pytz."""
    try:
        import pytz
        et = pytz.timezone("America/New_York")
        now_et = datetime.now(pytz.utc).astimezone(et)
        if now_et.weekday() >= 5:
            return False
        t = now_et.hour * 60 + now_et.minute
        return 9 * 60 + 30 <= t < 16 * 60
    except Exception:
        # Fallback: UTC-based approximation (no DST)
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        if now_utc.weekday() >= 5:
            return False
        t = now_utc.hour * 60 + now_utc.minute
        return 13 * 60 + 30 <= t < 20 * 60


def _phase_state(current_price: float, spxl_high: float) -> tuple:
    """Return (phase_label, phase_color) based on drawdown."""
    dd = abs((current_price - spxl_high) / spxl_high * 100)
    for threshold, label, color in CFG["dd_phase_map"]:
        if dd < threshold:
            return label, color
    return "FASE 4", "#f23645"

@st.cache_data(ttl=3600)
def _fetch_cds() -> float | None:
    """Fetch BAMLH0A0HYM2 from FRED public API. Returns latest value or None."""
    try:
        import requests
        url = ("https://fred.stlouisfed.org/graph/fredgraph.csv"
               "?id=BAMLH0A0HYM2")
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        lines = [l for l in r.text.strip().splitlines() if not l.startswith("DATE")]
        # Walk back to find a non-empty value
        for line in reversed(lines):
            parts = line.split(",")
            if len(parts) == 2 and parts[1].strip() not in ("", "."):
                return float(parts[1].strip())
    except Exception:
        pass
    return None


@st.cache_data(ttl=300)
def _fetch_vix_and_bonds() -> dict:
    """Fetch VIX and US 10Y yield."""
    result = {"vix": None, "vix_change": None,
              "bond10y": None, "bond10y_change": None}
    try:
        vix = yf.Ticker("^VIX").history(period="2d")
        if len(vix) >= 2:
            result["vix"]        = float(vix['Close'].iloc[-1])
            result["vix_change"] = float(vix['Close'].iloc[-1]) - float(vix['Close'].iloc[-2])
    except Exception:
        pass
    try:
        tnx = yf.Ticker("^TNX").history(period="2d")
        if len(tnx) >= 2:
            result["bond10y"]        = float(tnx['Close'].iloc[-1])
            result["bond10y_change"] = float(tnx['Close'].iloc[-1]) - float(tnx['Close'].iloc[-2])
    except Exception:
        pass
    return result


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
    """Load real SPXL data from launch date 2008-11-05 to present."""
    spxl    = yf.Ticker("SPXL")
    df_real = spxl.history(start="2008-11-05")[["Close"]].copy()
    df_real.index = df_real.index.tz_localize(None)
    df_real.columns = ["price"]
    df_real = df_real[~df_real.index.duplicated(keep="last")].sort_index().dropna()
    return df_real


def run_backtest(df, initial_capital=100_000):
    initial_capital  = float(initial_capital)
    prices           = df["price"].values
    dates            = df.index.values
    cash             = initial_capital
    shares           = 0.0
    avg_cost         = 0.0
    cycle_high       = prices[0]
    phase_entered    = [False] * 6
    trades           = []
    equity_curve     = []
    bnh_shares       = (initial_capital * (1 - CFG["reserve_pct"])) / prices[0]
    bnh_cash         = initial_capital * CFG["reserve_pct"]
    peak_equity      = initial_capital

    # Runner tracking (partial exit state)
    runner_shares    = 0.0   # shares kept after first trim
    runner_cost      = 0.0   # avg cost of runner (= original avg_cost)
    runner_peak      = 0.0   # peak price seen after trim (for trailing stop)
    first_sell_px    = 0.0   # price at first trim (B/C targets measured from here)
    trim_stage       = 0     # 0=none, 1=first trim done, 2=second trim done
    active_scenario  = ""    # "A", "B" or "C" — set at first trim, guards runner logic
    cycle_equity     = initial_capital  # equity at cycle start for compounding
    phases_at_entry  = 0     # FIX phases_in snapshot at first sell — runner trades use this
    cycle_entry_date = None  # date of first phase buy in this cycle (for entry markers)

    for date, price in zip(dates, prices):
        phases_in = sum(phase_entered)

        # ── Update cycle high when fully flat ────────────────────────────────
        if shares == 0 and runner_shares == 0 and price > cycle_high:
            cycle_high    = price
            phase_entered = [False] * 6
            # FIX #3: snapshot equity at start of new cycle for compounding alloc
            cycle_equity  = cash

        # ── Compute 6 entry levels from current cycle high ───────────────────
        lvl = [0.0] * 6
        lvl[0] = cycle_high * (1 - PHASE_DROPS[0])
        for i in range(1, 6):
            lvl[i] = lvl[i-1] * (1 - PHASE_DROPS[i])

        # ── Phase entries ─────────────────────────────────────────────────────
        for ph in range(6):
            if not phase_entered[ph] and price <= lvl[ph]:
                # FIX #3: use cycle_equity (compounding) instead of fixed initial_capital
                alloc_cash = cycle_equity * PHASE_ALLOC[ph]
                if cash >= alloc_cash * 0.99:          # 1% tolerance for float rounding
                    alloc_cash  = min(alloc_cash, cash)
                    bought      = alloc_cash / price
                    total_cost  = avg_cost * shares + alloc_cash
                    shares     += bought
                    avg_cost    = total_cost / shares if shares > 0 else 0
                    cash       -= alloc_cash
                    phase_entered[ph] = True
                    # Record date of first buy in this cycle for entry markers
                    if cycle_entry_date is None:
                        cycle_entry_date = date

        # ── Selling logic (tiered) ────────────────────────────────────────────
        phases_in = sum(phase_entered)   # recount after potential new entries

        if shares > 0 and avg_cost > 0:
            gain = (price - avg_cost) / avg_cost

            # ── Scenario C: fully invested (all 6 phases), no trim yet ────────
            if phases_in == 6 and trim_stage == 0:
                if gain >= CFG["sell_c_trim1_tp"]:
                    trim_qty        = shares * CFG["sell_c_trim1_pct"]
                    cash           += trim_qty * price
                    runner_shares   = shares - trim_qty
                    runner_cost     = avg_cost
                    runner_peak     = price
                    first_sell_px   = price
                    shares          = 0.0
                    trim_stage      = 1
                    active_scenario = "C"
                    phases_at_entry = phases_in   # snapshot for runner trades
                    trades.append(_make_trade(date, price, avg_cost, trim_qty, phases_at_entry, "C-TRIM1", cycle_entry_date))

            # ── Scenario C runner: trim_stage 1 ───────────────────────────────
            elif trim_stage == 1 and active_scenario == "C" and runner_shares > 0:
                runner_peak  = max(runner_peak, price)
                rg_from_sell = (price - first_sell_px) / first_sell_px
                if rg_from_sell >= CFG["sell_c_trim2_tp"]:
                    trim2_frac    = CFG["sell_c_trim2_pct"] / (1 - CFG["sell_c_trim1_pct"])
                    trim2_qty     = runner_shares * trim2_frac
                    cash         += trim2_qty * price
                    runner_shares -= trim2_qty
                    trim_stage    = 2
                    trades.append(_make_trade(date, price, runner_cost, trim2_qty, phases_at_entry, "C-TRIM2", cycle_entry_date, ref_price=first_sell_px))
                elif price <= runner_cost:
                    cash         += runner_shares * price
                    trades.append(_make_trade(date, price, runner_cost, runner_shares, phases_at_entry, "C-BE1", cycle_entry_date, ref_price=first_sell_px))
                    runner_shares = 0.0; trim_stage = 0; active_scenario = ""
                    cycle_high = price; phase_entered = [False] * 6; cycle_entry_date = None

            # ── Scenario C runner: trim_stage 2 ───────────────────────────────
            elif trim_stage == 2 and active_scenario == "C" and runner_shares > 0:
                rg_from_sell = (price - first_sell_px) / first_sell_px
                if rg_from_sell >= CFG["sell_c_final_tp"]:
                    cash         += runner_shares * price
                    trades.append(_make_trade(date, price, runner_cost, runner_shares, phases_at_entry, "C-FINAL", cycle_entry_date, ref_price=first_sell_px))
                    runner_shares = 0.0; trim_stage = 0; active_scenario = ""
                    cycle_high = price; phase_entered = [False] * 6; cycle_entry_date = None
                elif price <= runner_cost:
                    cash         += runner_shares * price
                    trades.append(_make_trade(date, price, runner_cost, runner_shares, phases_at_entry, "C-BE2", cycle_entry_date, ref_price=first_sell_px))
                    runner_shares = 0.0; trim_stage = 0; active_scenario = ""
                    cycle_high = price; phase_entered = [False] * 6; cycle_entry_date = None

            # ── Scenario B: 4–5 phases, no trim yet ──────────────────────────
            elif phases_in >= 4 and trim_stage == 0:
                if gain >= CFG["sell_b_tp"]:
                    main_qty        = shares * (1 - CFG["sell_b_keep"])
                    cash           += main_qty * price
                    runner_shares   = shares * CFG["sell_b_keep"]
                    runner_cost     = avg_cost
                    runner_peak     = price
                    first_sell_px   = price
                    shares          = 0.0
                    trim_stage      = 1
                    active_scenario = "B"
                    phases_at_entry = phases_in   # snapshot for runner trades
                    trades.append(_make_trade(date, price, avg_cost, main_qty, phases_at_entry, "B-MAIN", cycle_entry_date))

            # ── Scenario B runner: trim_stage 1 ───────────────────────────────
            elif trim_stage == 1 and active_scenario == "B" and runner_shares > 0:
                runner_peak   = max(runner_peak, price)
                rg_from_entry = (price - runner_cost) / runner_cost
                close_target  = first_sell_px * (1 + CFG["sell_b_close_from"])
                if price >= close_target:
                    cash         += runner_shares * price
                    trades.append(_make_trade(date, price, runner_cost, runner_shares, phases_at_entry, "B-CLOSE", cycle_entry_date, ref_price=first_sell_px))
                    runner_shares = 0.0; trim_stage = 0; active_scenario = ""
                    cycle_high = price; phase_entered = [False] * 6; cycle_entry_date = None
                elif rg_from_entry >= CFG["sell_b_trail_act"]:
                    trail_stop_px = runner_peak * (1 - CFG["sell_b_trail_stop"])
                    if price <= trail_stop_px:
                        exec_px = trail_stop_px
                        cash         += runner_shares * exec_px
                        trades.append(_make_trade(date, exec_px, runner_cost, runner_shares, phases_at_entry, "B-TSL", cycle_entry_date, ref_price=first_sell_px))
                        runner_shares = 0.0; trim_stage = 0; active_scenario = ""
                        cycle_high = exec_px; phase_entered = [False] * 6; cycle_entry_date = None
                elif price <= runner_cost:
                    cash         += runner_shares * price
                    trades.append(_make_trade(date, price, runner_cost, runner_shares, phases_at_entry, "B-BE", cycle_entry_date, ref_price=first_sell_px))
                    runner_shares = 0.0; trim_stage = 0; active_scenario = ""
                    cycle_high = price; phase_entered = [False] * 6; cycle_entry_date = None

            # ── Scenario A: ≤3 phases, no trim yet ────────────────────────────
            elif phases_in <= 3 and trim_stage == 0:
                if gain >= CFG["sell_a_tp"]:
                    main_qty        = shares * (1 - CFG["sell_a_keep"])
                    cash           += main_qty * price
                    runner_shares   = shares * CFG["sell_a_keep"]
                    runner_cost     = avg_cost
                    runner_peak     = price
                    first_sell_px   = price
                    shares          = 0.0
                    trim_stage      = 1
                    active_scenario = "A"
                    phases_at_entry = phases_in   # snapshot for runner trades
                    trades.append(_make_trade(date, price, avg_cost, main_qty, phases_at_entry, "A-MAIN", cycle_entry_date))

            # ── Scenario A runner: trim_stage 1 ───────────────────────────────
            elif trim_stage == 1 and active_scenario == "A" and runner_shares > 0:
                runner_peak   = max(runner_peak, price)
                runner_target = first_sell_px * (1 + CFG["sell_a_runner_tp"])
                trail_stop_px = runner_peak * (1 - CFG["sell_a_trail_stop"])
                if price >= runner_target:
                    cash         += runner_shares * price
                    trades.append(_make_trade(date, price, runner_cost, runner_shares, phases_at_entry, "A-RUNNER", cycle_entry_date, ref_price=first_sell_px))
                    runner_shares = 0.0; trim_stage = 0; active_scenario = ""
                    cycle_high = price; phase_entered = [False] * 6; cycle_entry_date = None
                elif price <= trail_stop_px:
                    # Use theoretical stop price (not close) to avoid gap distortion
                    exec_px = trail_stop_px
                    cash         += runner_shares * exec_px
                    trades.append(_make_trade(date, exec_px, runner_cost, runner_shares, phases_at_entry, "A-TSL", cycle_entry_date, ref_price=first_sell_px))
                    runner_shares = 0.0; trim_stage = 0; active_scenario = ""
                    cycle_high = exec_px; phase_entered = [False] * 6; cycle_entry_date = None
                    runner_shares = 0.0; trim_stage = 0; active_scenario = ""
                    cycle_high = price; phase_entered = [False] * 6; cycle_entry_date = None

        portfolio_val = cash + shares * price + runner_shares * price
        equity_curve.append({"date": pd.Timestamp(date), "equity": portfolio_val})
        if portfolio_val > peak_equity:
            peak_equity = portfolio_val

    bnh_equity = [{"date": pd.Timestamp(d), "bnh": bnh_cash + bnh_shares * p}
                  for d, p in zip(dates, prices)]

    return trades, pd.DataFrame(equity_curve), pd.DataFrame(bnh_equity)


def _make_trade(date, exit_price, avg_cost, qty, phases_used, scenario, entry_date=None, ref_price=None):
    """
    Helper to build a trade dict.
    ref_price: for runner trades, pass first_sell_px so gain_pct reflects
               runner performance from the separation point, not original avg_cost.
               avg_cost is still stored for reference.
    """
    cost_for_gain = ref_price if ref_price is not None else avg_cost
    return {
        "exit_date":   pd.Timestamp(date),
        "entry_date":  pd.Timestamp(entry_date) if entry_date else None,
        "exit_price":  float(exit_price),
        "avg_cost":    float(avg_cost),
        "ref_price":   float(cost_for_gain),
        "gain_pct":    (float(exit_price) - float(cost_for_gain)) / float(cost_for_gain) * 100,
        "profit":      (float(exit_price) - float(avg_cost)) * float(qty),
        "phases_used": int(phases_used),
        "shares":      float(qty),
        "scenario":    scenario,
    }


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

    # ── Cycle-level stats (group all trades sharing the same entry_date) ─────
    # This gives meaningful win rate & avg_gain: one cycle = one investment decision.
    # Cycle profit = sum of (exit_price - avg_cost) * shares across all sub-trades.
    cycles = t.groupby("entry_date").apply(
        lambda g: pd.Series({
            "total_profit":  g["profit"].sum(),
            "avg_cost":      g["avg_cost"].iloc[0],
            "phases_used":   g["phases_used"].iloc[0],
            "exit_date":     g["exit_date"].max(),
        })
    ).reset_index()

    # Cycle gain % = total_profit / (avg_cost * total_shares_bought)
    # Approximate via profit / (avg_cost * total_shares)
    t_shares = t.groupby("entry_date")["shares"].sum().reset_index(name="total_shares")
    cycles   = cycles.merge(t_shares, on="entry_date")
    cycles["cycle_gain_pct"] = (
        cycles["total_profit"] / (cycles["avg_cost"] * cycles["total_shares"]) * 100
    )

    n_cycles   = len(cycles)
    win_rate   = (cycles["cycle_gain_pct"] > 0).mean() * 100
    avg_gain   = cycles["cycle_gain_pct"].mean()
    best_cycle = cycles["cycle_gain_pct"].max()
    worst_cycle= cycles["cycle_gain_pct"].min()
    avg_phases = cycles["phases_used"].mean()

    return {
        "n_trades":     n_cycles,           # show cycles, not sub-trades
        "n_subtrades":  len(t),             # total individual trade records
        "win_rate":     win_rate,
        "avg_gain":     avg_gain,
        "best_trade":   best_cycle,
        "worst_trade":  worst_cycle,
        "total_return": (final_equity - initial_capital) / initial_capital * 100,
        "cagr":         cagr,
        "max_dd":       strat_dd,
        "bnh_return":   (final_bnh - initial_capital) / initial_capital * 100,
        "bnh_cagr":     bnh_cagr,
        "bnh_max_dd":   bnh_dd,
        "final_equity": final_equity,
        "final_bnh":    final_bnh,
        "avg_phases":   avg_phases,
    }


def chart_equity(eq_df, bnh_df, trades=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bnh_df["date"], y=bnh_df["bnh"],
        name="BUY & HOLD SPXL", line=dict(color="#333", width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(x=eq_df["date"], y=eq_df["equity"],
        name="ESTRATEGIA RSU", line=dict(color=C_GREEN, width=2),
        fill="tozeroy", fillcolor="rgba(0,255,173,0.04)"))

    if trades:
        eq_map = dict(zip(eq_df["date"], eq_df["equity"]))

        # Exit markers — one per trade, label = scenario + gain
        exit_dates  = [t["exit_date"] for t in trades]
        exit_equity = [eq_map.get(t["exit_date"], t["exit_price"]) for t in trades]
        exit_labels = [f"{t['scenario']} {t['gain_pct']:+.1f}%" for t in trades]
        exit_colors = []
        for t in trades:
            sc = t.get("scenario", "")
            if "TSL" in sc or "BE" in sc:
                exit_colors.append(C_ORANGE)
            elif t["gain_pct"] >= 0:
                exit_colors.append(C_GREEN)
            else:
                exit_colors.append(C_RED)

        fig.add_trace(go.Scatter(
            x=exit_dates, y=exit_equity,
            mode="markers+text", name="SALIDAS",
            marker=dict(color=exit_colors, size=9, symbol="triangle-up",
                        line=dict(color="rgba(255,255,255,0.2)", width=1)),
            text=exit_labels,
            textposition="top center",
            textfont=dict(family="VT323", size=10, color=C_RED),
            hovertemplate="<b>SALIDA</b><br>%{x}<br>%{text}<extra></extra>",
        ))

        # FIX #6: Entry markers use real entry_date stored per trade
        entry_trades = [t for t in trades if t.get("entry_date")]
        if entry_trades:
            e_dates  = [t["entry_date"] for t in entry_trades]
            e_equity = [eq_map.get(t["entry_date"], t["avg_cost"]) for t in entry_trades]
            e_labels = [f"F{t['phases_used']}" for t in entry_trades]
            fig.add_trace(go.Scatter(
                x=e_dates, y=e_equity,
                mode="markers+text", name="ENTRADAS",
                marker=dict(color=C_GREEN, size=8, symbol="triangle-down",
                            line=dict(color="rgba(0,255,173,0.3)", width=1)),
                text=e_labels,
                textposition="bottom center",
                textfont=dict(family="VT323", size=10, color=C_GREEN),
                hovertemplate="<b>ENTRADA</b><br>%{x}<br>Fases: %{text}<extra></extra>",
            ))

    # FIX #4: clamp X axis to actual backtest period
    x_min = eq_df["date"].iloc[0]
    x_max = eq_df["date"].iloc[-1]
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="CURVA DE EQUITY // ESTRATEGIA vs BUY & HOLD",
                   font=dict(family="VT323", size=18, color=C_GREEN), x=0.01),
        yaxis_title="USD", height=420)
    fig.update_xaxes(range=[x_min, x_max])
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

    # FIX #4: only show vlines that fall within the actual backtest range
    x_min = eq_df["date"].iloc[0]
    x_max = eq_df["date"].iloc[-1]
    for yr, lbl, col in [("2009-03-09","GFC 2008","#f23645"),
                          ("2020-03-23","COVID","#ff9800"),
                          ("2022-10-12","BEAR 22","#ff9800")]:
        vl_ts = pd.Timestamp(yr)
        if x_min <= vl_ts <= x_max:
            fig.add_vline(x=vl_ts.timestamp() * 1000,
                          line_width=1, line_dash="dash", line_color=col, opacity=0.4,
                          annotation_text=lbl,
                          annotation_font=dict(family="VT323", size=12, color=col),
                          annotation_position="top right")

    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="DRAWDOWN COMPARADO // ESTRATEGIA vs BUY & HOLD",
                   font=dict(family="VT323", size=18, color=C_ORANGE), x=0.01),
        yaxis_title="%", height=320)
    fig.update_xaxes(range=[x_min, x_max])
    return fig


def chart_trades(trades):
    if not trades:
        return None
    t      = pd.DataFrame(trades).sort_values("exit_date")
    sc_colors = {"A-MAIN": C_GREEN, "A-RUNNER": "#7dff6b", "A-TSL": C_ORANGE,
                 "B-MAIN": C_BLUE,  "B-CLOSE":  C_BLUE,   "B-TSL": C_ORANGE, "B-BE": "#ff5555",
                 "C-TRIM1": C_GREEN,"C-TRIM2":  "#7dff6b", "C-FINAL": C_GREEN,
                 "C-BE1": "#ff5555","C-BE2":    "#ff5555"}
    colors = [sc_colors.get(tr.get("scenario",""), C_GREEN if g > 0 else C_RED)
              for tr, g in zip(t.to_dict("records"), t["gain_pct"])]
    labels = [tr.get("scenario","") for tr in t.to_dict("records")]
    fig    = go.Figure()
    fig.add_trace(go.Bar(x=t["exit_date"], y=t["gain_pct"],
        marker_color=colors, marker_line_color="rgba(0,0,0,0)",
        text=labels, textposition="outside",
        textfont=dict(family="VT323", size=9, color="#555")))
    fig.add_hline(y=20, line_dash="dot", line_color=C_GREEN, opacity=0.4,
                  annotation_text="A: +20%",
                  annotation_font=dict(family="VT323", size=11, color=C_GREEN))
    fig.add_hline(y=10, line_dash="dot", line_color=C_BLUE, opacity=0.4,
                  annotation_text="B: +10%",
                  annotation_font=dict(family="VT323", size=11, color=C_BLUE))
    fig.add_hline(y=5, line_dash="dot", line_color=C_ORANGE, opacity=0.35,
                  annotation_text="C: +5%",
                  annotation_font=dict(family="VT323", size=11, color=C_ORANGE))
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="OPERACIONES COMPLETADAS // GANANCIA POR TRADE",
                   font=dict(family="VT323", size=18, color=C_BLUE), x=0.01),
        yaxis_title="%", height=300, bargap=0.3)
    return fig


def chart_phases(trades):
    if not trades:
        return None
    t = pd.DataFrame(trades)
    # FIX #5: filter phases_used==0 and group by scenario prefix (A/B/C)
    t = t[t["phases_used"] > 0].copy()
    t["sc_group"] = t["scenario"].str.split("-").str[0]
    sc_counts = t.groupby("sc_group").size().reindex(["A","B","C"], fill_value=0)
    sc_counts = sc_counts[sc_counts > 0]
    sc_color_map = {"A": C_GREEN, "B": C_BLUE, "C": C_ORANGE}
    sc_labels    = {"A": "ESC. A (≤3f)", "B": "ESC. B (4-5f)", "C": "ESC. C (6f)"}
    fig = go.Figure(go.Bar(
        x=[sc_labels.get(k, k) for k in sc_counts.index],
        y=sc_counts.values,
        marker_color=[sc_color_map.get(k, C_GREEN) for k in sc_counts.index],
        text=sc_counts.values,
        textfont=dict(family="VT323", color="white", size=16),
        textposition="outside"))
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="ESCENARIOS ACTIVADOS",
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
        /* ══ PIXEL TITLE ════════════════════════════════ */
        .pixel-title-wrap {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
            padding: 14px 28px 12px;
            margin: 0 auto 4px;
            border-bottom: 2px solid #00ffad;
            width: 100%;
        }
        .pixel-title {
            font-family: 'VT323', monospace;
            font-size: 3.2rem;
            font-weight: 400;
            color: #00ffad;
            letter-spacing: 8px;
            text-transform: uppercase;
            text-shadow:
                0 0 6px  #00ffadcc,
                0 0 14px #00ffad66,
                0 0 28px #00ffad22;
            line-height: 1;
            animation: pixelFlicker 12s ease-in-out infinite;
        }
        @keyframes pixelFlicker {
            0%, 95%, 100% { opacity: 1; }
            96%  { opacity: 0.85; }
            97%  { opacity: 1;    }
            98%  { opacity: 0.9;  }
        }
        .main-title { display: none; }
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
            grid-template-columns: 1.4fr 1.1fr 1fr 1fr 0.9fr 0.7fr;
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
        /* ══ MACRO ROW ═════════════════════════════════ */
        .macro-card {
            background: #0c0e12; border: 1px solid #1a1e26;
            border-top: 2px solid #00d9ff33; border-radius: 4px;
            padding: 14px 18px; text-align: center;
            transition: border-color .3s, transform .2s;
        }
        .macro-card:hover { border-color:#00d9ff55; transform:translateY(-1px); }
        .macro-val  { font-family:'VT323',monospace; font-size:2rem; color:white; letter-spacing:2px; }
        .macro-lbl  { font-family:'Share Tech Mono',monospace; color:#3a3a3a; font-size:.65rem;
                      text-transform:uppercase; letter-spacing:2px; margin-bottom:4px; }
        .macro-chg  { font-family:'VT323',monospace; font-size:1.1rem; }

        /* ══ PRICE TIMESTAMP BADGE ═════════════════════ */
        .price-badge {
            display:inline-flex; align-items:center; gap:6px;
            font-family:'Share Tech Mono',monospace; font-size:.7rem;
            color:#444; border:1px solid #1a1e26; border-radius:3px;
            padding:3px 10px; margin-top:6px;
        }
        .price-badge.stale { border-color:#ff980044; color:#ff9800; }

        /* ══ SESSION STATE PANEL ═══════════════════════ */
        .ref-panel {
            background: #0c0e12; border:1px solid #00ffad22;
            border-left:3px solid #00ffad; border-radius:0 4px 4px 0;
            padding:16px 20px; margin:12px 0;
        }
        .ref-panel-title {
            font-family:'VT323',monospace; color:#00ffad;
            font-size:1rem; letter-spacing:3px; margin-bottom:10px;
        }
        .ref-stat { display:flex; justify-content:space-between; align-items:baseline;
                    font-family:'Share Tech Mono',monospace; font-size:.78rem;
                    color:#555; margin:4px 0; }
        .ref-stat span:last-child { color:#00ffad; font-family:'VT323',monospace;
                                     font-size:1.1rem; }

        /* ══ PHASE EXECUTION TRACKER ════════════════════ */
        .exec-row {
            display:flex; justify-content:space-between; align-items:center;
            padding:8px 14px; margin:4px 0;
            background:#0c0e12; border:1px solid #1a1e26; border-radius:4px;
            font-family:'Share Tech Mono',monospace; font-size:.78rem; color:#555;
            transition:background .2s;
        }
        .exec-row.done { border-left:3px solid #00ffad; color:#888; background:#00ffad05; }
        .exec-row .exec-phase { font-family:'VT323',monospace; font-size:1rem; color:#00ffad; }
        .exec-row .exec-price { color:white; font-family:'VT323',monospace; font-size:1rem; }

        /* ══ SIMULATOR BOX ══════════════════════════════ */
        .sim-box {
            background: linear-gradient(135deg, #0c0e12 0%, #0e1116 100%);
            border:1px solid #00d9ff22; border-radius:4px; padding:20px; margin:15px 0;
        }
        .sim-result-val {
            font-family:'VT323',monospace; font-size:2.2rem; color:#00d9ff;
            letter-spacing:2px; text-align:center; margin:10px 0;
        }
        .sim-result-lbl {
            font-family:'Share Tech Mono',monospace; font-size:.7rem;
            color:#444; text-transform:uppercase; letter-spacing:2px; text-align:center;
        }

        /* ══ CDS LIVE VALUE ═════════════════════════════ */
        .cds-live {
            font-family:'VT323',monospace; font-size:3rem; text-align:center;
            letter-spacing:3px; margin:10px 0;
        }
        .cds-live.safe     { color:#00ffad; text-shadow:0 0 20px #00ffad44; }
        .cds-live.warning  { color:#ff9800; text-shadow:0 0 20px #ff980044; }
        .cds-live.danger   { color:#f23645; text-shadow:0 0 20px #f2364544; }

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
        <div class="header-pre">[SECURE CONNECTION ESTABLISHED // RSU TRADING SYSTEM v7.0]</div>
        <div class="pixel-title-wrap">
            <span style="font-size:2.4rem;">📈</span>
            <span class="pixel-title">ESTRATEGIA SPXL</span>
        </div>
        <div class="sub-title">REDISTRIBUTION STRATEGY RESEARCH UNIT // SISTEMA ACTIVO</div>
        <div class="market-status">
            <div class="{dot_cls}"></div>
            <span style="color:#333;">{status_txt} //</span>
            <span style="color:#2a2a2a;">{now.strftime('%Y-%m-%d %H:%M UTC')}</span>
        </div>
        <div class="header-post">[NODE: RSU-ALPHA // ENCRYPTION: AES-256 // LATENCY: &lt;1ms]</div>
    </div>
    """, unsafe_allow_html=True)

    # ── MARKET DATA ───────────────────────────────────────────────────────────
    @st.cache_data(ttl=300)
    def _fetch_spxl():
        hist = yf.Ticker("SPXL").history(period="1y")
        if hist.empty:
            return None
        cur   = float(hist['Close'].iloc[-1])
        prev  = float(hist['Close'].iloc[-2])
        high  = float(hist['High'].max())
        low   = float(hist['Low'].min())
        # Try to get the timestamp of last price
        try:
            last_ts = hist.index[-1].to_pydatetime()
        except Exception:
            last_ts = None
        d  = CFG["phase_drops"]
        p1 = high * (1 - d[0])
        p2 = p1   * (1 - d[1])
        p3 = p2   * (1 - d[2])
        p4 = p3   * (1 - d[3])
        return {
            "price":    cur, "change": (cur - prev) / prev * 100,
            "high":     high, "low": low,
            "drawdown": (cur - high) / high * 100,
            "last_ts":  last_ts,
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
            spxl_data  = _fetch_spxl()
            spx_data   = _fetch_spx()
            macro_data = _fetch_vix_and_bonds()
            cds_value  = _fetch_cds()
        except Exception as e:
            st.error(f"Error obteniendo datos de mercado: {e}")
            return

    if spxl_data is None:
        st.error("No se pudieron obtener datos de SPXL")
        return

    data = {
        "spxl_price":  spxl_data["price"],
        "spxl_change": spxl_data["change"],
        "spxl_high":   spxl_data["high"],
        "spxl_low":    spxl_data["low"],
        "drawdown":    spxl_data["drawdown"],
        "last_ts":     spxl_data.get("last_ts"),
        "spx_price":   spx_data["price"],
        "spx_change":  spx_data["change"],
        "buy_levels":  spxl_data["levels"],
    }

    # ── SESSION STATE: reference high & phase execution tracker ───────────────
    if "ref_high" not in st.session_state:
        st.session_state["ref_high"]       = data["spxl_high"]
        st.session_state["ref_high_date"]  = datetime.now().strftime("%Y-%m-%d")
        st.session_state["ref_high_price"] = data["spxl_price"]
    if "phases_executed" not in st.session_state:
        st.session_state["phases_executed"] = {i: None for i in range(1, 7)}

    # Recompute levels from FIXED reference high
    ref_high = st.session_state["ref_high"]
    d = CFG["phase_drops"]
    lvl = [0.0] * 6
    lvl[0] = ref_high * (1 - d[0])
    for i in range(1, 6):
        lvl[i] = lvl[i-1] * (1 - d[i])
    data["fixed_levels"] = {f"phase{i+1}": lvl[i] for i in range(6)}
    data["ref_high"] = ref_high

    # ── PRICE TIMESTAMP BADGE ─────────────────────────────────────────────────
    market_open = _is_market_open()
    last_ts     = data.get("last_ts")
    if last_ts:
        ts_str   = last_ts.strftime("%Y-%m-%d %H:%M UTC")
        is_stale = not market_open
        badge_cls = "price-badge stale" if is_stale else "price-badge"
        badge_txt = "⚠ PRECIO DE CIERRE ANTERIOR" if is_stale else "● PRECIO EN TIEMPO REAL"
        st.markdown(
            f'<div class="{badge_cls}">{badge_txt} &nbsp;|&nbsp; {ts_str}</div>',
            unsafe_allow_html=True)

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

    # ── MACRO ROW: VIX + 10Y ──────────────────────────────────────────────────
    vix    = macro_data.get("vix")
    vixchg = macro_data.get("vix_change")
    b10y   = macro_data.get("bond10y")
    b10chg = macro_data.get("bond10y_change")

    mc1, mc2, mc3, mc4 = st.columns(4)

    with mc1:
        if vix is not None:
            vix_color = "#00ffad" if vix < 20 else "#ff9800" if vix < 30 else "#f23645"
            vix_label = "CALMA" if vix < 20 else "ALERTA" if vix < 30 else "PÁNICO"
            vc_str    = f"{vixchg:+.2f}" if vixchg is not None else "—"
            vc_color  = "#f23645" if (vixchg or 0) > 0 else "#00ffad"
            st.markdown(f"""<div class="macro-card" style="border-top-color:{vix_color}44;">
                <div class="macro-lbl">// VIX · {vix_label}</div>
                <div class="macro-val" style="color:{vix_color};">{vix:.1f}</div>
                <div class="macro-chg" style="color:{vc_color};">{vc_str}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="macro-card"><div class="macro-lbl">// VIX</div><div class="macro-val" style="color:#333;">—</div></div>', unsafe_allow_html=True)

    with mc2:
        if b10y is not None:
            bc_str   = f"{b10chg:+.2f}%" if b10chg is not None else "—"
            bc_color = "#f23645" if (b10chg or 0) > 0 else "#00ffad"
            st.markdown(f"""<div class="macro-card" style="border-top-color:#00d9ff33;">
                <div class="macro-lbl">// BONO 10Y USA</div>
                <div class="macro-val" style="color:#00d9ff;">{b10y:.2f}%</div>
                <div class="macro-chg" style="color:{bc_color};">{bc_str}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="macro-card"><div class="macro-lbl">// BONO 10Y</div><div class="macro-val" style="color:#333;">—</div></div>', unsafe_allow_html=True)

    with mc3:
        cds_disp = f"{cds_value:.2f}" if cds_value is not None else "N/D"
        cds_color = "#00ffad" if (cds_value or 0) < 5 else "#ff9800" if (cds_value or 0) < 10.7 else "#f23645"
        cds_lbl   = "NORMAL" if (cds_value or 0) < 5 else "ATENCIÓN" if (cds_value or 0) < 10.7 else "⚠ STOP"
        st.markdown(f"""<div class="macro-card" style="border-top-color:{cds_color}44;">
            <div class="macro-lbl">// CDS HY · {cds_lbl}</div>
            <div class="macro-val" style="color:{cds_color};">{cds_disp}</div>
            <div class="macro-chg" style="color:#333;">BAMLH0A0HYM2</div>
        </div>""", unsafe_allow_html=True)

    with mc4:
        ref_dd = (data['spxl_price'] - ref_high) / ref_high * 100
        rph, rphc = _phase_state(data['spxl_price'], ref_high)
        st.markdown(f"""<div class="macro-card" style="border-top-color:{rphc}44;">
            <div class="macro-lbl">// DD vs REF FIJO</div>
            <div class="macro-val" style="color:{rphc};">{ref_dd:.1f}%</div>
            <div class="macro-chg" style="color:#2a2a2a;">REF: ${ref_high:.2f}</div>
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

            # ── SIMULATOR ─────────────────────────────────────────────────────
            st.markdown('<div class="section-header-bar" style="margin-top:20px;">▸ SIMULADOR ¿QUÉ PASA SI COMPRO HOY?</div>',
                        unsafe_allow_html=True)
            sim_col1, sim_col2, sim_col3 = st.columns(3)
            with sim_col1:
                sim_fase = st.selectbox("Fase de entrada:", [1, 2, 3, 4, 5, 6], key="sim_fase")
            with sim_col2:
                fixed_lvls = data["fixed_levels"]
                phase_key  = f"phase{sim_fase}"
                default_px = round(fixed_lvls[phase_key], 2)
                sim_price  = st.number_input("Precio de compra ($):", min_value=0.01,
                                              value=float(default_px), step=0.5, key="sim_price")
            with sim_col3:
                sim_capital = st.number_input("Capital total ($):", min_value=1000,
                                               value=10000, step=1000, key="sim_cap")

            alloc_pcts    = CFG["phase_alloc"]
            sim_fase_idx  = int(sim_fase) - 1
            sim_capital_f = float(sim_capital)
            sim_price_f   = float(sim_price) if float(sim_price) > 0 else 1.0
            sim_alloc     = sim_capital_f * alloc_pcts[sim_fase_idx]
            sim_shares    = sim_alloc / sim_price_f

            phases_so_far = int(sim_fase)
            if phases_so_far == 6:
                sc_label   = "ESCENARIO C"
                sim_target = sim_price_f * (1 + CFG["sell_c_trim1_tp"])
                tp_label   = f"+{CFG['sell_c_trim1_tp']:.0%} → trim 65%"
            elif phases_so_far >= 4:
                sc_label   = "ESCENARIO B"
                sim_target = sim_price_f * (1 + CFG["sell_b_tp"])
                tp_label   = f"+{CFG['sell_b_tp']:.0%} → vender 80%"
            else:
                sc_label   = "ESCENARIO A"
                sim_target = sim_price_f * (1 + CFG["sell_a_tp"])
                tp_label   = f"+{CFG['sell_a_tp']:.0%} → vender 95%"

            sim_needed      = ((sim_target - data['spxl_price']) / data['spxl_price'] * 100
                                if data['spxl_price'] > 0 else 0)
            sim_gain_abs    = sim_shares * (sim_target - sim_price_f)
            sim_gain_on_cap = sim_gain_abs / sim_capital_f * 100   # % sobre capital total

            sr1, sr2, sr3, sr4 = st.columns(4)
            for col, val, sub, lbl in [
                (sr1, f"${sim_price:.2f}",
                      f"Desplegado: ${sim_alloc:,.0f} ({alloc_pcts[sim_fase_idx]:.0%})",
                      "PRECIO ENTRADA"),
                (sr2, f"${sim_target:.2f}",
                      tp_label,
                      "TARGET"),
                (sr3, f"{sim_needed:+.1f}%",
                      "desde precio actual",
                      "SPXL NECESITA SUBIR"),
                (sr4, f"${sim_gain_abs:,.0f}",
                      f"+{sim_gain_on_cap:.1f}% s/ capital total",
                      "GANANCIA ESTIMADA"),
            ]:
                with col:
                    color = "#00d9ff" if "GANANCIA" in lbl else "#00ffad" if sim_needed <= 0 else "#ff9800"
                    st.markdown(f"""<div class="sim-box" style="padding:14px;margin:6px 0;">
                        <div class="sim-result-lbl">{lbl}</div>
                        <div class="sim-result-val" style="color:{color};font-size:1.6rem;">{val}</div>
                        <div style="font-family:'Share Tech Mono',monospace;font-size:.65rem;
                                    color:#333;margin-top:4px;letter-spacing:1px;">{sub}</div>
                    </div>""", unsafe_allow_html=True)

            # Context bar: capital breakdown
            st.markdown(f"""
            <div style="display:flex;gap:8px;margin-top:8px;font-family:'Share Tech Mono',monospace;
                        font-size:.72rem;color:#444;justify-content:center;letter-spacing:1px;">
                <span>// {sc_label}</span>
                <span style="color:#1a1e26;">|</span>
                <span>CAPITAL TOTAL: <span style="color:#888;">${sim_capital_f:,.0f}</span></span>
                <span style="color:#1a1e26;">|</span>
                <span>FASE {sim_fase} DESPLIEGA: <span style="color:#00ffad;">${sim_alloc:,.0f}</span>
                      ({alloc_pcts[sim_fase_idx]:.0%})</span>
                <span style="color:#1a1e26;">|</span>
                <span>RETORNO SOBRE DESPLEGADO: <span style="color:#00ffad;">+{(sim_gain_abs/sim_alloc*100) if sim_alloc > 0 else 0:.1f}%</span></span>
            </div>""", unsafe_allow_html=True)

            if sim_needed <= 0:
                st.markdown('<div class="alert-box alert-buy">✅ PRECIO ACTUAL YA ESTÁ SOBRE EL TARGET — revisa el precio de entrada</div>', unsafe_allow_html=True)

        with col_right:
            # ── REFERENCE HIGH PANEL ──────────────────────────────────────────
            st.markdown(f"""
            <div class="ref-panel">
                <div class="ref-panel-title">▸ MÁXIMO DE REFERENCIA</div>
                <div class="ref-stat"><span>Fijado el:</span>
                    <span>{st.session_state['ref_high_date']}</span></div>
                <div class="ref-stat"><span>Precio al fijar:</span>
                    <span>${st.session_state['ref_high_price']:.2f}</span></div>
                <div class="ref-stat"><span>Máximo ref:</span>
                    <span>${ref_high:.2f}</span></div>
                <div class="ref-stat"><span>DD desde ref:</span>
                    <span>{(data['spxl_price'] - ref_high) / ref_high * 100:.1f}%</span></div>
            </div>""", unsafe_allow_html=True)

            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button("🔒 FIJAR MÁXIMO AHORA", use_container_width=True, key="fix_high"):
                    st.session_state["ref_high"]       = data["spxl_high"]
                    st.session_state["ref_high_date"]  = datetime.now().strftime("%Y-%m-%d")
                    st.session_state["ref_high_price"] = data["spxl_price"]
                    st.session_state["phases_executed"] = {i: None for i in range(1, 7)}
                    # Clear stale Telegram alert keys so new levels re-trigger
                    for k in list(st.session_state.keys()):
                        if k.startswith("tg_ph"):
                            del st.session_state[k]
                    st.rerun()
            with rc2:
                if st.button("♻ RESET CICLO", use_container_width=True, key="reset_cycle"):
                    st.session_state["phases_executed"] = {i: None for i in range(1, 7)}
                    for k in list(st.session_state.keys()):
                        if k.startswith("tg_ph"):
                            del st.session_state[k]
                    st.rerun()

            st.markdown('<div class="section-header-bar" style="margin-top:16px;">▸ SEÑALES // FASES</div>',
                        unsafe_allow_html=True)

            cur    = data['spxl_price']
            levels = data["fixed_levels"]
            phases_cfg = [
                (f"FASE {i+1}", levels[f"phase{i+1}"], CFG["phase_alloc"][i])
                for i in range(6)
            ]
            phase_names = [
                "PRIMERA CAÍDA",  "SEGUNDA CAÍDA",  "TERCERA CAÍDA",
                "CUARTA CAÍDA",   "QUINTA CAÍDA",   "SEXTA CAÍDA",
            ]
            for i, (name, price, alloc) in enumerate(phases_cfg, 1):
                executed = st.session_state["phases_executed"].get(i)
                level_hit = cur <= price
                if executed:
                    sc, st_txt = "completed", "// EJECUTADA"
                elif level_hit:
                    sc, st_txt = "active", ">> ACTIVA"
                else:
                    sc, st_txt = "pending", "__ ESPERA"
                dist  = (cur - price) / price * 100
                dcol  = "#00ffad" if dist <= 0 else "#f23645"
                prog  = min(100, max(0, (ref_high - cur) /
                            (ref_high - price) * 100)) if ref_high > price else 0
                exec_info = f"@ ${executed:.2f}" if executed else ""
                st.markdown(f"""
                <div class="phase-card {sc}">
                    <div class="phase-number">[{i}]</div>
                    <div style="font-family:'VT323',monospace;color:#00ffad;font-size:.9rem;
                                letter-spacing:2px;margin-bottom:6px;">{phase_names[i-1]} · {name}</div>
                    <div style="display:flex;justify-content:space-between;align-items:baseline;">
                        <span style="font-family:'VT323',monospace;color:white;font-size:1.55rem;
                                     letter-spacing:2px;">${price:.2f}</span>
                        <span style="font-family:'VT323',monospace;color:#333;font-size:.8rem;">{st_txt} {exec_info}</span>
                    </div>
                    <div class="progress-bar"><div class="progress-fill" style="width:{prog:.0f}%"></div></div>
                    <div style="margin-top:6px;font-family:'Share Tech Mono',monospace;
                                font-size:.72rem;display:flex;gap:12px;">
                        <span style="color:#333;">ALLOC: {alloc:.0%}</span>
                        <span style="color:{dcol};">DIST: {dist:+.1f}%</span>
                    </div>
                </div>""", unsafe_allow_html=True)

                # Checkbox to mark phase as executed
                if level_hit and not executed:
                    if st.checkbox(f"✓ Marcar Fase {i} como ejecutada", key=f"exec_ph_{i}"):
                        st.session_state["phases_executed"][i] = cur
                        st.rerun()

            # ── ALERT BOX ─────────────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            phases_active = sum(1 for i in range(1,7) if cur <= levels[f"phase{i}"])
            if cur <= levels['phase6']:
                st.markdown('<div class="alert-box alert-sell">🚨 FASE 6 ACTIVA — INVERSIÓN MÁXIMA</div>', unsafe_allow_html=True)
            elif cur <= levels['phase1']:
                st.markdown('<div class="alert-box alert-buy">✅ COMPRA ACTIVA — EJECUTAR PROTOCOLO</div>', unsafe_allow_html=True)
            else:
                d_to_f1 = (cur - levels['phase1']) / levels['phase1'] * 100
                st.markdown(f'<div class="alert-box alert-warning">⏳ STAND BY — FALTAN {d_to_f1:.1f}% PARA FASE 1</div>', unsafe_allow_html=True)

            # ── TELEGRAM ALERTS (Gist-persisted, dedup across sessions) ───────
            if TELEGRAM_OK:
                # Capital del usuario si lo ha introducido en la calculadora
                _cap = float(st.session_state.get("calc_capital", 0))

                triggered = check_and_notify_phases(
                    current_price=cur,
                    levels=levels,
                    alloc_cfg=CFG["phase_alloc"],
                    ref_high=ref_high,
                    capital=_cap,
                )
                if triggered:
                    st.toast(
                        f"📲 Telegram: Fase(s) {triggered} notificada(s)",
                        icon="✅",
                    )

                # CDS stop alert — re-alerta cada 24h mientras persista
                if cds_value is not None:
                    check_and_notify_cds(cds_value, threshold=10.7, ttl_hours=24.0)

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
                para acumular posición escalonada en 6 fases, con salidas parciales
                adaptadas según el nivel de inversión alcanzado.
            </p>
        </div>""", unsafe_allow_html=True)

        # ── BUYING RULES ─────────────────────────────────────────────────────
        st.markdown('<div class="section-header-bar">▸ REGLAS DE ENTRADA // 6 FASES</div>', unsafe_allow_html=True)
        buy_rules = [
            ("1", "PRIMERA CAÍDA  (−15% desde máximo)",    "Invertir 20% del capital"),
            ("2", "SEGUNDA CAÍDA  (−10% desde Fase 1)",    "Invertir 15% del capital"),
            ("3", "TERCERA CAÍDA  (−7% desde Fase 2)",     "Invertir 20% del capital"),
            ("4", "CUARTA CAÍDA   (−10% desde Fase 3)",    "Invertir 20% del capital"),
            ("5", "QUINTA CAÍDA   (−10% desde Fase 4)",    "Invertir 15% del capital"),
            ("6", "SEXTA CAÍDA    (−10% desde Fase 5)",    "Invertir 10% del capital — MÁXIMA INVERSIÓN"),
        ]
        for icon, title, desc in buy_rules:
            bold = "color:white" if icon in ("1","2","3","4") else "color:#888"
            st.markdown(f"""
            <div class="rule-item">
                <div class="rule-icon">{icon}</div>
                <div>
                    <div style="{bold};font-size:.88rem;margin-bottom:4px;">{title}</div>
                    <div style="color:#444;font-size:.78rem;">{desc}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        # ── SELLING RULES ─────────────────────────────────────────────────────
        st.markdown('<div class="section-header-bar" style="margin-top:28px;">▸ REGLAS DE SALIDA // ESCALONADA POR EXPOSICIÓN</div>', unsafe_allow_html=True)

        # Scenario A
        st.markdown("""
        <div class="terminal-box" style="border-left:3px solid #00ffad;margin-bottom:12px;">
            <div style="font-family:'VT323',monospace;color:#00ffad;font-size:1.1rem;letter-spacing:3px;margin-bottom:10px;">
                ESCENARIO A — HASTA 3 FASES INVERTIDAS (≤55% capital)</div>
            <div class="rule-item" style="border:none;padding:6px 0;background:transparent;">
                <div class="rule-icon" style="background:#00ffad0a;border-color:#00ffad22;">$</div>
                <div style="color:#aaa;font-size:.83rem;line-height:1.8;">
                    Al <span style="color:#00ffad;">+20%</span> sobre precio medio →
                    vender <span style="color:#00ffad;">95%</span> de la posición.<br>
                    Dejar <span style="color:#00ffad;">5%</span> como <i>runner</i> buscando
                    <span style="color:#00ffad;">+17%</span> adicional desde el precio de venta.<br>
                    Si no alcanza el +17%: <span style="color:#ff9800;">trailing stop −11%</span>
                    desde el máximo que haya alcanzado.
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Scenario B
        st.markdown("""
        <div class="terminal-box" style="border-left:3px solid #00d9ff;margin-bottom:12px;">
            <div style="font-family:'VT323',monospace;color:#00d9ff;font-size:1.1rem;letter-spacing:3px;margin-bottom:10px;">
                ESCENARIO B — 4 O MÁS FASES INVERTIDAS (≥55% capital)</div>
            <div class="rule-item" style="border:none;padding:6px 0;background:transparent;">
                <div class="rule-icon" style="background:#00d9ff0a;border-color:#00d9ff22;color:#00d9ff;">$</div>
                <div style="color:#aaa;font-size:.83rem;line-height:1.8;">
                    Al <span style="color:#00d9ff;">+10%</span> → vender
                    <span style="color:#00d9ff;">80%</span> de la posición.<br>
                    Dejar <span style="color:#00d9ff;">20%</span> con trailing stop en
                    <span style="color:#00d9ff;">break-even</span> inicialmente.<br>
                    Si sube al <span style="color:#00d9ff;">+14%</span> → activar trail
                    <span style="color:#ff9800;">−11%</span> desde máximo.<br>
                    Cerrar el runner cuando suba
                    <span style="color:#00d9ff;">+10%</span> desde el precio de la primera venta.
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Scenario C
        st.markdown("""
        <div class="terminal-box" style="border-left:3px solid #f23645;margin-bottom:12px;">
            <div style="font-family:'VT323',monospace;color:#f23645;font-size:1.1rem;letter-spacing:3px;margin-bottom:10px;">
                ESCENARIO C — TOTALMENTE INVERTIDO (6 FASES / ~100% capital)</div>
            <div class="rule-item" style="border:none;padding:6px 0;background:transparent;">
                <div class="rule-icon" style="background:#f236450a;border-color:#f2364522;color:#f23645;">$</div>
                <div style="color:#aaa;font-size:.83rem;line-height:1.8;">
                    Al <span style="color:#ff9800;">+5%</span> →
                    vender <span style="color:#f23645;">65%</span> de la posición.<br>
                    Dejar <span style="color:#f23645;">35%</span> con stop en
                    <span style="color:#f23645;">break-even</span>.<br>
                    Al <span style="color:#ff9800;">+10%</span> desde primera venta →
                    vender <span style="color:#f23645;">15%</span> más.<br>
                    Al <span style="color:#ff9800;">+20%</span> desde primera venta →
                    cerrar el <span style="color:#f23645;">20%</span> final.
                </div>
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
        lv = data['fixed_levels']   # ← uses fixed reference high

        with col_c1:
            st.markdown('<div style="font-family:\'VT323\',monospace;color:#333;font-size:.82rem;letter-spacing:2px;margin-bottom:10px;">// INPUT PARAMETERS</div>', unsafe_allow_html=True)
            capital_total     = float(st.number_input("Capital Total ($):", min_value=1000, value=10000, step=1000))
            tiene_posicion    = st.checkbox("¿Tienes posición abierta?")
            if tiene_posicion:
                precio_medio      = float(st.number_input("Precio medio ($):", min_value=0.0, value=0.0, step=0.1))
                cantidad_acciones = int(st.number_input("Nº Acciones:", min_value=0, value=0, step=1))
            else:
                precio_medio, cantidad_acciones = 0, 0

        with col_c2:
            st.markdown('<div style="font-family:\'VT323\',monospace;color:#333;font-size:.82rem;letter-spacing:2px;margin-bottom:10px;">// ALLOCATION OUTPUT</div>', unsafe_allow_html=True)
            total_inv = 0
            fase_data = [
                (f"FASE {i+1}", CFG["phase_alloc"][i], lv[f"phase{i+1}"])
                for i in range(6)
            ]
            for fase, pct, precio in fase_data:
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
            reserva = capital_total * CFG["reserve_pct"]
            st.markdown(f"""
            <div class="calc-item calc-reserve">
                <span style="color:#555;font-size:.85rem;">RESERVA ({CFG['reserve_pct']:.0%})</span>
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

            # Let user specify how many phases are invested to show correct scenario
            n_phases_inv = int(st.selectbox("Fases invertidas actualmente:", [1,2,3,4,5,6], index=2))
            if n_phases_inv == 6:
                target_price = precio_medio * (1 + CFG["sell_c_trim1_tp"])
                sc_txt = f"Escenario C: trim 65% al +{CFG['sell_c_trim1_tp']:.0%}"
            elif n_phases_inv >= 4:
                target_price = precio_medio * (1 + CFG["sell_b_tp"])
                sc_txt = f"Escenario B: vender 80% al +{CFG['sell_b_tp']:.0%}"
            else:
                target_price = precio_medio * (1 + CFG["sell_a_tp"])
                sc_txt = f"Escenario A: vender 95% al +{CFG['sell_a_tp']:.0%}"

            c1, c2, c3   = st.columns(3)
            c1.metric("Valor Actual",    f"${valor_actual:,.2f}", f"{pnl_pct:+.2f}%")
            c2.metric("Objetivo Venta",  f"${target_price:.2f}", sc_txt)
            c3.metric("Distancia Target",f"{((target_price - data['spxl_price']) / data['spxl_price'] * 100):.2f}%")
            if data['spxl_price'] >= target_price:
                st.balloons()
                st.markdown('<div class="alert-box alert-sell">🎯 OBJETIVO ALCANZADO // EJECUTAR SALIDA PARCIAL</div>', unsafe_allow_html=True)
                if TELEGRAM_OK:
                    tp_key = f"tg_tp_{target_price:.2f}"
                    if tp_key not in st.session_state:
                        scenario_lbl = "C" if n_phases_inv == 6 else "B" if n_phases_inv >= 4 else "A"
                        send_alert(build_target_alert(
                            scenario=scenario_lbl,
                            current_price=data['spxl_price'],
                            avg_cost=precio_medio,
                            target_price=target_price,
                            gain_pct=pnl_pct,
                            action=sc_txt,
                        ))
                        st.session_state[tp_key] = True
            else:
                rem = (target_price - data['spxl_price']) / data['spxl_price'] * 100
                st.markdown(f'<div class="alert-box alert-warning">⏳ EN POSICIÓN // FALTAN {rem:.1f}% PARA TARGET</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════
    # TAB 4: RIESGO CDS
    # ════════════════════════════════════════════
    with tab4:
        st.markdown('<div class="section-header-bar">▸ RIESGO SISTÉMICO // CDS MONITOR</div>', unsafe_allow_html=True)

        # Live CDS value
        cds_cls  = "safe" if (cds_value or 0) < 5 else "warning" if (cds_value or 0) < 10.7 else "danger"
        cds_disp = f"{cds_value:.2f}" if cds_value is not None else "N/D"
        cds_lbl  = "NIVEL NORMAL" if (cds_value or 0) < 5 else "ZONA DE ATENCIÓN" if (cds_value or 0) < 10.7 else "⚠ STOP SISTÉMICO ACTIVO"
        cds_src  = "FRED API" if cds_value is not None else "sin datos — usando gráfico TradingView"

        cv1, cv2, cv3 = st.columns([1, 2, 1])
        with cv2:
            st.markdown(f"""
            <div class="terminal-box" style="text-align:center;">
                <div class="macro-lbl" style="font-size:.75rem;">BAMLH0A0HYM2 // {cds_src}</div>
                <div class="cds-live {cds_cls}">{cds_disp}</div>
                <div style="font-family:'VT323',monospace;font-size:1rem;
                            letter-spacing:3px;color:#555;">{cds_lbl}</div>
                <div style="font-family:'Share Tech Mono',monospace;font-size:.68rem;
                            color:#2a2a2a;margin-top:6px;">UMBRAL DE STOP: 10.70</div>
            </div>""", unsafe_allow_html=True)

        # Gauge — marker position driven by real data
        if cds_value is not None:
            # Scale: 0=0%, 10.7=100% crisis, cap display at 15
            gauge_pct = min(95, max(2, cds_value / 15 * 100))
        else:
            gauge_pct = 30  # fallback
        st.markdown(f"""
        <div style="margin:22px 0 5px;font-family:'VT323',monospace;color:#333;font-size:.82rem;letter-spacing:2px;">
            // NIVEL DE ESTRÉS SISTÉMICO</div>
        <div class="cds-gauge"><div class="cds-marker" style="left:{gauge_pct:.1f}%;"></div></div>
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
        st.markdown('<div class="section-header-bar">▸ BACKTEST ENGINE // SIMULACIÓN DESDE 2008 (LANZAMIENTO SPXL)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="bt-disclaimer">
            // NOTA: SPXL fue lanzado el 05/11/2008. El backtest usa datos reales desde esa fecha.
            El año de inicio 2010/2015/2020 permiten comparar rendimientos en diferentes ciclos.
            Los resultados históricos no garantizan rendimientos futuros. Simulación sin comisiones ni slippage.
        </div>""", unsafe_allow_html=True)

        with st.spinner("// CARGANDO DATOS HISTÓRICOS..."):
            try:
                df_hist = load_spxl_history()
            except Exception as e:
                st.error(f"Error cargando datos: {e}")
                st.stop()

        cfg1, cfg2, _ = st.columns([1, 1, 2])
        with cfg1:
            bt_capital = float(st.number_input(
                "Capital inicial ($):", min_value=100,
                value=10_000, step=1_000, key="bt_capital",
                help="Sin límite máximo. Introduce cualquier cifra."))
        with cfg2:
            bt_year = int(st.number_input(
                "Año de inicio:", min_value=2008,
                max_value=datetime.now().year - 1,
                value=2008, step=1, key="bt_year",
                help="Desde 2008 — lanzamiento real de SPXL"))

        df_bt  = df_hist[df_hist.index.year >= int(bt_year)].copy()
        trades, eq_df, bnh_df = run_backtest(df_bt, bt_capital)
        stats  = compute_stats(trades, eq_df, bnh_df, bt_capital)

        # FIX #5: warn when period is too short for meaningful comparison
        years_bt = (datetime.now().year - int(bt_year))
        if years_bt < 5:
            st.markdown(f"""
            <div class="alert-box alert-warning">
                ⚠ PERIODO CORTO ({years_bt} año{'s' if years_bt != 1 else ''}) — La estrategia está diseñada para capturar
                correcciones que pueden tardar años en producirse. En periodos alcistas continuos sin correcciones
                significativas, el capital permanece en cash y el Buy&amp;Hold superará ampliamente a la estrategia.
                Para una comparativa representativa usa desde <b>2008</b> (incluye GFC, COVID y Bear 2022).
            </div>""", unsafe_allow_html=True)

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
                (r1[4], f"{stats['n_trades']}",              "CICLOS",        "bt-neutral"),
            ]:
                with col:
                    st.markdown(f'<div class="bt-stat-card"><div class="bt-stat-label">{lbl}</div><div class="bt-stat-val {cls}">{val}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Row 2
            r2 = st.columns(5)
            for col, val, lbl, cls in [
                (r2[0], f"{stats['win_rate']:.0f}%",      "WIN RATE CICLOS", "bt-positive"),
                (r2[1], f"{stats['avg_gain']:+.1f}%",      "GANANCIA MEDIA",  "bt-positive"),
                (r2[2], f"{stats['best_trade']:+.1f}%",    "MEJOR CICLO",     "bt-positive"),
                (r2[3], f"{stats['worst_trade']:+.1f}%",   "PEOR CICLO",
                         "bt-negative" if stats['worst_trade'] < 0 else "bt-positive"),
                (r2[4], f"{stats['avg_phases']:.1f}",       "FASES MEDIAS/OP","bt-neutral"),
            ]:
                with col:
                    st.markdown(f'<div class="bt-stat-card"><div class="bt-stat-label">{lbl}</div><div class="bt-stat-val {cls}">{val}</div></div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div style="font-family:'Share Tech Mono',monospace;font-size:.68rem;color:#333;
                        text-align:right;margin-top:4px;letter-spacing:1px;">
                // CICLOS = grupos de entrada+salida completos &nbsp;|&nbsp;
                REGISTROS INDIVIDUALES EN TABLA: {stats.get('n_subtrades', stats['n_trades'])}
            </div>""", unsafe_allow_html=True)

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
            st.markdown('<div class="section-header-bar">▸ CURVA DE EQUITY // PUNTOS DE ENTRADA Y SALIDA</div>', unsafe_allow_html=True)
            st.plotly_chart(chart_equity(eq_df, bnh_df, trades), use_container_width=True)

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
                <span>FECHA SALIDA</span><span>ESCENARIO</span>
                <span>PRECIO SALIDA</span><span>COSTE / REF</span>
                <span>GANANCIA</span><span>FASES</span>
            </div>""", unsafe_allow_html=True)

            sc_label_colors = {
                "A-MAIN": C_GREEN,  "A-RUNNER": "#7dff6b", "A-TSL": C_ORANGE,
                "B-MAIN": C_BLUE,   "B-CLOSE":  C_BLUE,    "B-TSL": C_ORANGE,  "B-BE": "#ff5555",
                "C-TRIM1": C_GREEN, "C-TRIM2":  "#7dff6b", "C-FINAL": C_GREEN,
                "C-BE1":  "#ff5555","C-BE2":    "#ff5555",
            }
            # Runner scenarios — show ref_price (first_sell_px) instead of avg_cost
            runner_scenarios = {"A-RUNNER","A-TSL","B-CLOSE","B-TSL","B-BE","C-TRIM2","C-FINAL","C-BE1","C-BE2"}
            for tr in sorted(trades, key=lambda x: x["exit_date"], reverse=True)[:60]:
                gc   = C_GREEN if tr["gain_pct"] > 0 else C_RED
                sc   = tr.get("scenario", "—")
                scc  = sc_label_colors.get(sc, "#888")
                dots = tr['phases_used']
                is_runner = sc in runner_scenarios
                cost_val  = tr.get("ref_price", tr["avg_cost"]) if is_runner else tr["avg_cost"]
                cost_lbl  = f'<span style="font-size:.65rem;color:#333;"> REF</span>' if is_runner else ""
                st.markdown(f"""
                <div class="bt-trade-row">
                    <span style="color:#888;">{tr['exit_date'].strftime('%Y-%m-%d')}</span>
                    <span style="color:{scc};font-family:'VT323',monospace;font-size:.95rem;letter-spacing:1px;">{sc}</span>
                    <span style="color:white;font-family:'VT323',monospace;font-size:1rem;">${tr['exit_price']:.2f}</span>
                    <span style="color:#555;">${cost_val:.2f}{cost_lbl}</span>
                    <span style="color:{gc};font-family:'VT323',monospace;font-size:1rem;">{tr['gain_pct']:+.1f}%</span>
                    <span style="color:#00d9ff;">{'▪' * max(1, int(dots))}</span>
                </div>""", unsafe_allow_html=True)

            if len(trades) > 60:
                st.markdown(f'<div style="font-family:\'VT323\',monospace;color:#333;font-size:.85rem;text-align:center;padding:12px;letter-spacing:2px;">// MOSTRANDO ÚLTIMAS 60 DE {len(trades)} OPERACIONES</div>', unsafe_allow_html=True)

            st.markdown("""
            <div class="bt-disclaimer" style="margin-top:30px;">
                ⚠ ADVERTENCIA: Simulación con supuestos simplificados. No incluye slippage,
                comisiones, impacto de mercado ni volatility drag completo del apalancamiento diario.
                Exclusivamente educativo — no constituye asesoramiento financiero.
            </div>""", unsafe_allow_html=True)

    # ── SIDEBAR: TELEGRAM TEST ────────────────────────────────────────────────
    if TELEGRAM_OK:
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            '<div style="font-family:\'VT323\',monospace;color:#444;'
            'font-size:.8rem;letter-spacing:2px;">// TELEGRAM ALERTS</div>',
            unsafe_allow_html=True)
        if st.sidebar.button("📲 TEST NOTIFICACIÓN", use_container_width=True):
            ok = send_alert(
                "✅ <b>SPXL Bot conectado.</b>\n"
                f"Precio actual: <code>${data['spxl_price']:.2f}</code>\n"
                f"Estado: <code>{_phase_state(data['spxl_price'], ref_high)[0]}</code>")
            st.sidebar.success("✓ Enviado") if ok else st.sidebar.error("✗ Error — revisa secrets")
    else:
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            '<div style="font-family:\'VT323\',monospace;color:#333;'
            'font-size:.78rem;letter-spacing:2px;">// TELEGRAM: módulo no disponible</div>',
            unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="footer">
        <p>
            [END OF TRANSMISSION // RSU TRADING SYSTEM v7.0]<br>
            [REDISTRIBUTION STRATEGY RESEARCH UNIT // ALL RIGHTS RESERVED]
        </p>
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    render()
