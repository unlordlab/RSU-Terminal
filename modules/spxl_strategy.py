# modules/spxl_strategy.py  — v3.0 AESTHETIC UPGRADE
import streamlit as st
import pandas as pd
import yfinance as yf
import streamlit.components.v1 as components
import os
from datetime import datetime

def render():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

        /* ══════════════════════════════════════════════
           BASE
        ══════════════════════════════════════════════ */
        .stApp {
            background: #0a0c10;
        }

        * { box-sizing: border-box; }

        /* ── Scanline overlay ───────────────────────── */
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

        /* ── HEADINGS ───────────────────────────────── */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            text-transform: uppercase;
            letter-spacing: 3px;
        }

        /* ── BODY TEXT ──────────────────────────────── */
        p, li, span, div {
            font-family: 'Share Tech Mono', monospace;
        }

        /* ══════════════════════════════════════════════
           MAIN HEADER
        ══════════════════════════════════════════════ */
        .main-header {
            background: #0a0c10;
            border: 1px solid #00ffad44;
            border-radius: 4px;
            padding: 40px 30px 28px;
            margin-bottom: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
            box-shadow:
                0 0 60px #00ffad08,
                inset 0 0 80px #00ffad04;
        }

        /* top glow line */
        .main-header::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00ffad, transparent);
            animation: scanBeam 4s ease-in-out infinite;
        }

        /* bottom faint line */
        .main-header::after {
            content: "";
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad33, transparent);
        }

        /* corner brackets */
        .header-corner-tl,
        .header-corner-tr,
        .header-corner-bl,
        .header-corner-br {
            position: absolute;
            width: 14px;
            height: 14px;
            border-color: #00ffad66;
            border-style: solid;
        }
        .header-corner-tl { top: 8px;  left: 8px;  border-width: 2px 0 0 2px; }
        .header-corner-tr { top: 8px;  right: 8px; border-width: 2px 2px 0 0; }
        .header-corner-bl { bottom: 8px; left: 8px;  border-width: 0 0 2px 2px; }
        .header-corner-br { bottom: 8px; right: 8px; border-width: 0 2px 2px 0; }

        .header-pre {
            font-family: 'VT323', monospace;
            font-size: 0.82rem;
            color: #3a3a3a;
            letter-spacing: 3px;
            margin-bottom: 10px;
        }

        .main-title {
            font-family: 'VT323', monospace !important;
            color: #00ffad;
            font-size: 4.2rem;
            font-weight: 400;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 8px;
            text-shadow:
                0 0 20px #00ffad88,
                0 0 60px #00ffad33,
                0 0 120px #00ffad11;
            line-height: 1;
            animation: titleFlicker 8s ease-in-out infinite;
        }

        .sub-title {
            font-family: 'VT323', monospace;
            color: #00d9ff;
            font-size: 0.95rem;
            margin-top: 14px;
            letter-spacing: 5px;
            opacity: 0.85;
        }

        .header-post {
            font-family: 'VT323', monospace;
            font-size: 0.72rem;
            color: #2a2a2a;
            margin-top: 16px;
            letter-spacing: 2px;
        }

        /* ── Market status dot ──────────────────────── */
        .market-status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-family: 'VT323', monospace;
            font-size: 0.78rem;
            letter-spacing: 2px;
            margin-top: 10px;
        }
        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #00ffad;
            box-shadow: 0 0 8px #00ffad;
            animation: blink 1.4s ease-in-out infinite;
        }
        .status-dot.closed {
            background: #f23645;
            box-shadow: 0 0 8px #f23645;
            animation: none;
        }

        /* ══════════════════════════════════════════════
           ANIMATIONS
        ══════════════════════════════════════════════ */
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50%       { opacity: 0.2; }
        }

        @keyframes scanBeam {
            0%   { background-position: -100% 0; opacity: 0.6; }
            50%  { background-position: 200% 0;  opacity: 1;   }
            100% { background-position: -100% 0; opacity: 0.6; }
        }

        @keyframes titleFlicker {
            0%, 96%, 100% { opacity: 1; }
            97%           { opacity: 0.85; }
            98%           { opacity: 1; }
            99%           { opacity: 0.9; }
        }

        @keyframes phaseGlow {
            0%, 100% { box-shadow: 0 0 15px #00ffad0a; }
            50%       { box-shadow: 0 0 30px #00ffad22; }
        }

        @keyframes fadeSlideIn {
            from { opacity: 0; transform: translateY(6px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* ══════════════════════════════════════════════
           METRIC CARDS
        ══════════════════════════════════════════════ */
        .metric-card {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-top: 2px solid #00ffad33;
            border-radius: 4px;
            padding: 20px;
            text-align: center;
            transition: border-color 0.3s ease, box-shadow 0.3s ease, transform 0.2s ease;
            position: relative;
            animation: fadeSlideIn 0.4s ease both;
        }

        .metric-card:hover {
            border-color: #00ffad66;
            box-shadow: 0 0 25px #00ffad14, 0 4px 16px rgba(0,0,0,0.4);
            transform: translateY(-2px);
        }

        /* tiny corner decoration on cards */
        .metric-card::after {
            content: "";
            position: absolute;
            top: 6px; right: 6px;
            width: 6px; height: 6px;
            border-top: 1px solid #00ffad44;
            border-right: 1px solid #00ffad44;
        }

        .metric-value {
            font-family: 'VT323', monospace;
            font-size: 2.4rem;
            color: white;
            margin: 8px 0;
            letter-spacing: 2px;
        }

        .metric-label {
            font-family: 'Share Tech Mono', monospace;
            color: #3a3a3a;
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .metric-change {
            font-family: 'VT323', monospace;
            font-size: 1.3rem;
            letter-spacing: 1px;
        }

        .positive { color: #00ffad; }
        .negative { color: #f23645; }
        .warning  { color: #ff9800; }

        /* ══════════════════════════════════════════════
           SECTION CONTAINERS
        ══════════════════════════════════════════════ */
        .terminal-box {
            background: linear-gradient(135deg, #0c0e12 0%, #0e1116 100%);
            border: 1px solid #00ffad1a;
            border-radius: 4px;
            padding: 25px 25px 20px;
            margin: 15px 0;
            box-shadow: 0 0 20px #00ffad06;
            position: relative;
        }

        .terminal-box::before {
            content: "//";
            position: absolute;
            top: 10px; left: 15px;
            font-family: 'VT323', monospace;
            color: #00ffad22;
            font-size: 0.85rem;
        }

        .section-header-bar {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-left: 3px solid #00ffad;
            padding: 11px 20px;
            margin-bottom: 15px;
            border-radius: 0 4px 4px 0;
            font-family: 'VT323', monospace;
            color: #00ffad;
            font-size: 1.15rem;
            letter-spacing: 3px;
            display: flex;
            align-items: center;
            gap: 10px;
            position: relative;
            overflow: hidden;
        }

        /* subtle shimmer on section bars */
        .section-header-bar::after {
            content: "";
            position: absolute;
            top: 0; right: 0; bottom: 0;
            width: 40%;
            background: linear-gradient(90deg, transparent, #00ffad05);
            pointer-events: none;
        }

        /* ══════════════════════════════════════════════
           PHASE CARDS
        ══════════════════════════════════════════════ */
        .phase-card {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 10px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            font-family: 'Share Tech Mono', monospace;
        }

        .phase-card::before {
            content: "";
            position: absolute;
            left: 0; top: 0; bottom: 0;
            width: 3px;
            background: #1a1e26;
            transition: background 0.3s ease;
        }

        .phase-card.active {
            border-color: #00ffad33;
            background: linear-gradient(135deg, #0c0e12 0%, #00ffad07 100%);
            animation: phaseGlow 2.5s ease-in-out infinite;
        }

        .phase-card.active::before  { background: #00ffad; }
        .phase-card.pending::before { background: #2a3f5f; opacity: 0.4; }
        .phase-card.completed::before { background: #4caf50; opacity: 0.5; }

        .phase-card.pending   { opacity: 0.5; }
        .phase-card.completed { opacity: 0.4; }

        .phase-number {
            position: absolute;
            top: 10px; right: 12px;
            font-family: 'VT323', monospace;
            font-size: 1.4rem;
            color: #222;
            letter-spacing: 1px;
        }

        .phase-card.active .phase-number    { color: #00ffad55; }
        .phase-card.completed .phase-number { color: #4caf5066; }

        /* ══════════════════════════════════════════════
           ALERT BOXES
        ══════════════════════════════════════════════ */
        .alert-box {
            padding: 14px 20px;
            border-radius: 4px;
            margin: 12px 0;
            border: 1px solid;
            font-family: 'VT323', monospace;
            font-size: 1.1rem;
            letter-spacing: 2px;
            position: relative;
            overflow: hidden;
        }

        /* left accent stripe on alerts */
        .alert-box::before {
            content: "";
            position: absolute;
            left: 0; top: 0; bottom: 0;
            width: 3px;
        }

        .alert-buy {
            background: #00ffad07;
            border-color: #00ffad44;
            color: #00ffad;
        }
        .alert-buy::before { background: #00ffad; }

        .alert-sell {
            background: #f2364506;
            border-color: #f2364544;
            color: #f23645;
        }
        .alert-sell::before { background: #f23645; }

        .alert-warning {
            background: #ff980007;
            border-color: #ff980044;
            color: #ff9800;
        }
        .alert-warning::before { background: #ff9800; }

        /* ══════════════════════════════════════════════
           HIGHLIGHT QUOTE
        ══════════════════════════════════════════════ */
        .highlight-quote {
            background: #00ffad06;
            border: 1px solid #00ffad1a;
            border-radius: 4px;
            padding: 22px 30px;
            margin: 22px 0;
            font-family: 'VT323', monospace;
            font-size: 1.3rem;
            color: #00ffad;
            text-align: center;
            letter-spacing: 3px;
            position: relative;
        }

        .highlight-quote::before {
            content: "❝";
            position: absolute;
            top: -1px; left: 14px;
            font-size: 1.8rem;
            color: #00ffad22;
            line-height: 1;
        }

        /* ══════════════════════════════════════════════
           RISK BOX
        ══════════════════════════════════════════════ */
        .risk-box {
            background: linear-gradient(135deg, #110909 0%, #180d0d 100%);
            border: 1px solid #f2364520;
            border-left: 3px solid #f23645;
            border-radius: 0 4px 4px 0;
            padding: 20px;
            margin: 15px 0;
        }

        /* ══════════════════════════════════════════════
           STRATEGY GRID
        ══════════════════════════════════════════════ */
        .strategy-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin: 15px 0;
        }

        .strategy-card {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-top: 2px solid #00ffad2a;
            border-radius: 4px;
            padding: 15px;
            font-family: 'VT323', monospace;
            font-size: 1.05rem;
            color: #00ffad;
            letter-spacing: 1px;
            transition: border-top-color 0.3s ease, box-shadow 0.3s ease;
        }

        .strategy-card:hover {
            border-top-color: #00ffad88;
            box-shadow: 0 0 16px #00ffad0a;
        }

        /* ══════════════════════════════════════════════
           RULE ITEMS
        ══════════════════════════════════════════════ */
        .rule-item {
            display: flex;
            align-items: flex-start;
            gap: 14px;
            margin: 10px 0;
            padding: 14px 16px;
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 4px;
            font-family: 'Share Tech Mono', monospace;
            transition: border-color 0.2s ease, background 0.2s ease;
        }

        .rule-item:hover {
            border-color: #00ffad22;
            background: #0d1015;
        }

        .rule-icon {
            width: 28px;
            height: 28px;
            background: #00ffad0f;
            color: #00ffad;
            border: 1px solid #00ffad2a;
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'VT323', monospace;
            font-size: 1.1rem;
            flex-shrink: 0;
            transition: background 0.2s ease;
        }

        .rule-item:hover .rule-icon {
            background: #00ffad1a;
        }

        /* ══════════════════════════════════════════════
           CDS GAUGE
        ══════════════════════════════════════════════ */
        .cds-gauge {
            width: 100%;
            height: 22px;
            background: linear-gradient(90deg,
                #00ffad 0%,
                #7dff6b 20%,
                #ff9800 55%,
                #f23645 100%
            );
            border-radius: 2px;
            position: relative;
            margin: 20px 0 8px;
            border: 1px solid #1a1e26;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
        }

        /* tick marks on gauge */
        .cds-gauge::before {
            content: "";
            position: absolute;
            inset: 0;
            background: repeating-linear-gradient(
                90deg,
                transparent,
                transparent 12.5%,
                rgba(0,0,0,0.3) 12.5%,
                rgba(0,0,0,0.3) calc(12.5% + 1px)
            );
            pointer-events: none;
        }

        .cds-marker {
            position: absolute;
            top: -9px;
            width: 3px;
            height: 40px;
            background: white;
            box-shadow: 0 0 10px rgba(255,255,255,0.9), 0 0 20px rgba(255,255,255,0.4);
            transition: left 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        /* marker arrow */
        .cds-marker::after {
            content: "";
            position: absolute;
            bottom: -5px;
            left: -4px;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
        }

        .cds-labels {
            display: flex;
            justify-content: space-between;
            font-family: 'VT323', monospace;
            color: #444;
            font-size: 0.82rem;
            letter-spacing: 1px;
            margin-top: 6px;
        }

        /* ══════════════════════════════════════════════
           HORIZONTAL RULE
        ══════════════════════════════════════════════ */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad33, transparent);
            margin: 28px 0;
        }

        /* ══════════════════════════════════════════════
           PROGRESS BAR
        ══════════════════════════════════════════════ */
        .progress-bar {
            width: 100%;
            height: 5px;
            background: #0c0e12;
            border-radius: 2px;
            overflow: hidden;
            margin: 8px 0;
            border: 1px solid #1a1e26;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ffad88 0%, #00ffad 100%);
            transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        /* ══════════════════════════════════════════════
           CALC ITEMS
        ══════════════════════════════════════════════ */
        .calc-item {
            background: #0c0e12;
            padding: 12px 15px;
            border-radius: 4px;
            margin: 6px 0;
            border-left: 3px solid #00ffad;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: 'Share Tech Mono', monospace;
            transition: background 0.2s ease;
        }

        .calc-item:hover { background: #0e1015; }

        .calc-reserve {
            background: #ff980007;
            border-left-color: #ff9800;
        }

        .calc-total {
            background: #00ffad07;
            border: 1px solid #00ffad2a;
            border-radius: 4px;
            padding: 14px 15px;
            margin-top: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: 'VT323', monospace;
            font-size: 1.25rem;
        }

        /* ══════════════════════════════════════════════
           FOOTER
        ══════════════════════════════════════════════ */
        .footer {
            text-align: center;
            padding: 24px 20px;
            border-top: 1px solid #151820;
            margin-top: 35px;
            position: relative;
        }

        .footer::before {
            content: "";
            position: absolute;
            top: 0; left: 25%; right: 25%;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad22, transparent);
        }

        .footer p {
            font-family: 'VT323', monospace;
            color: #252525;
            font-size: 0.82rem;
            letter-spacing: 3px;
            margin: 0;
            line-height: 1.8;
        }

        /* ══════════════════════════════════════════════
           STREAMLIT NATIVE OVERRIDES
        ══════════════════════════════════════════════ */
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background: #0c0e12 !important;
            border-bottom: 1px solid #1a1e26 !important;
            gap: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            font-family: 'VT323', monospace !important;
            letter-spacing: 3px;
            font-size: 1rem !important;
            color: #444 !important;
            background: transparent !important;
            border-radius: 2px 2px 0 0 !important;
            padding: 10px 20px !important;
            transition: color 0.2s ease, background 0.2s ease !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #00ffad88 !important;
            background: #00ffad08 !important;
        }

        .stTabs [aria-selected="true"] {
            color: #00ffad !important;
            background: #00ffad0a !important;
            border-bottom: 2px solid #00ffad !important;
        }

        /* Inputs */
        .stNumberInput input,
        .stSelectbox select,
        .stTextInput input {
            background: #0c0e12 !important;
            border: 1px solid #1a1e26 !important;
            color: #00ffad !important;
            font-family: 'Share Tech Mono', monospace !important;
            border-radius: 4px !important;
        }

        .stNumberInput input:focus,
        .stTextInput input:focus {
            border-color: #00ffad44 !important;
            box-shadow: 0 0 10px #00ffad11 !important;
        }

        /* Checkbox */
        .stCheckbox label {
            font-family: 'Share Tech Mono', monospace !important;
            color: #666 !important;
            font-size: 0.85rem !important;
        }

        /* Download button */
        .stDownloadButton button {
            background: #0c0e12 !important;
            border: 1px solid #00ffad44 !important;
            color: #00ffad !important;
            font-family: 'VT323', monospace !important;
            letter-spacing: 2px !important;
            font-size: 1rem !important;
            transition: all 0.2s ease !important;
            border-radius: 4px !important;
        }

        .stDownloadButton button:hover {
            background: #00ffad0f !important;
            border-color: #00ffad88 !important;
            box-shadow: 0 0 16px #00ffad18 !important;
        }

        /* Spinner */
        .stSpinner > div {
            border-top-color: #00ffad !important;
        }

        /* Metric widgets (native st.metric) */
        [data-testid="stMetricValue"] {
            font-family: 'VT323', monospace !important;
            color: white !important;
        }
        [data-testid="stMetricLabel"] {
            font-family: 'Share Tech Mono', monospace !important;
            color: #444 !important;
            font-size: 0.75rem !important;
        }
        [data-testid="stMetricDelta"] {
            font-family: 'VT323', monospace !important;
        }

        /* Scrollbar */
        ::-webkit-scrollbar       { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0a0c10; }
        ::-webkit-scrollbar-thumb { background: #1a1e26; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #00ffad33; }
    </style>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════════════════════
    now = datetime.now()
    # NYSE hours: Mon–Fri 09:30–16:00 ET (simple heuristic, no timezone lib needed)
    weekday = now.weekday()        # 0=Mon … 6=Sun
    hour    = now.hour             # UTC; NYSE ET = UTC-4/5; rough check
    market_open = (weekday < 5)    # crude: just weekdays flagged as potentially open
    dot_class   = "status-dot" if market_open else "status-dot closed"
    status_text = "MERCADO ACTIVO" if market_open else "MERCADO CERRADO"

    st.markdown(f"""
    <div class="main-header">
        <div class="header-corner-tl"></div>
        <div class="header-corner-tr"></div>
        <div class="header-corner-bl"></div>
        <div class="header-corner-br"></div>
        <div class="header-pre">[SECURE CONNECTION ESTABLISHED // RSU TRADING SYSTEM v3.0]</div>
        <h1 class="main-title">ESTRATEGIA SPXL</h1>
        <div class="sub-title">REDISTRIBUTION STRATEGY RESEARCH UNIT // SISTEMA ACTIVO</div>
        <div class="market-status">
            <div class="{dot_class}"></div>
            <span style="color:#333;">{status_text} //</span>
            <span style="color:#2a2a2a;">{now.strftime('%Y-%m-%d %H:%M UTC')}</span>
        </div>
        <div class="header-post">[NODE: RSU-ALPHA // ENCRYPTION: AES-256 // LATENCY: &lt;1ms]</div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # DATA
    # ══════════════════════════════════════════════════════════════════════════
    @st.cache_data(ttl=300)
    def get_market_data():
        try:
            spxl      = yf.Ticker("SPXL")
            spxl_hist = spxl.history(period="1y")
            spx       = yf.Ticker("^GSPC")
            spx_hist  = spx.history(period="2d")

            if not spxl_hist.empty:
                current_price = spxl_hist['Close'].iloc[-1]
                prev_price    = spxl_hist['Close'].iloc[-2]
                yearly_high   = spxl_hist['High'].max()
                yearly_low    = spxl_hist['Low'].min()

                change_pct = ((current_price - prev_price) / prev_price) * 100
                drawdown   = ((current_price - yearly_high) / yearly_high) * 100

                p1 = yearly_high * 0.85
                p2 = p1 * 0.90
                p3 = p2 * 0.93
                p4 = p3 * 0.90

                return {
                    'spxl_price':  current_price,
                    'spxl_change': change_pct,
                    'spxl_high':   yearly_high,
                    'spxl_low':    yearly_low,
                    'drawdown':    drawdown,
                    'spx_price':   spx_hist['Close'].iloc[-1] if not spx_hist.empty else 0,
                    'spx_change':  ((spx_hist['Close'].iloc[-1] - spx_hist['Close'].iloc[-2]) /
                                    spx_hist['Close'].iloc[-2] * 100) if len(spx_hist) >= 2 else 0,
                    'buy_levels':  {'phase1': p1, 'phase2': p2, 'phase3': p3, 'phase4': p4}
                }
        except Exception as e:
            st.error(f"Error obteniendo datos: {e}")
        return None

    with st.spinner("// SINCRONIZANDO DATOS DE MERCADO..."):
        data = get_market_data()

    if data is None:
        st.error("No se pudieron obtener datos del mercado")
        return

    # ══════════════════════════════════════════════════════════════════════════
    # METRIC CARDS
    # ══════════════════════════════════════════════════════════════════════════
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        color = "positive" if data['spxl_change'] >= 0 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">// SPXL ACTUAL</div>
            <div class="metric-value">${data['spxl_price']:.2f}</div>
            <div class="metric-change {color}">{data['spxl_change']:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        color2 = "positive" if data['spx_change'] >= 0 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">// S&P 500</div>
            <div class="metric-value">{data['spx_price']:,.0f}</div>
            <div class="metric-change {color2}">{data['spx_change']:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        dd_color = "positive" if data['drawdown'] > -10 else "warning" if data['drawdown'] > -15 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">// DRAWDOWN vs MAX</div>
            <div class="metric-value {dd_color}">{data['drawdown']:.1f}%</div>
            <div class="metric-change" style="color:#2a2a2a;">MAX: ${data['spxl_high']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        current_dd = abs(data['drawdown'])
        if current_dd < 15:
            phase, phase_color = "STAND BY", "#333"
        elif current_dd < 25:
            phase, phase_color = "FASE 1", "#00ffad"
        elif current_dd < 32:
            phase, phase_color = "FASE 2", "#00ffad"
        elif current_dd < 39:
            phase, phase_color = "FASE 3", "#ff9800"
        else:
            phase, phase_color = "FASE 4", "#f23645"

        st.markdown(f"""
        <div class="metric-card" style="border-top-color: {phase_color}44;">
            <div class="metric-label">// ESTADO</div>
            <div class="metric-value" style="color: {phase_color}; font-size: 1.9rem;">{phase}</div>
            <div class="metric-change" style="color:#2a2a2a;">DD: {current_dd:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TABS
    # ══════════════════════════════════════════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs(["DASHBOARD", "ESTRATEGIA", "CALCULADORA", "RIESGO CDS"])

    # ── TAB 1: DASHBOARD ──────────────────────────────────────────────────────
    with tab1:
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.markdown('<div class="section-header-bar">▸ GRÁFICO SPXL // NIVELES</div>',
                        unsafe_allow_html=True)
            chart_html = """
            <div class="tradingview-widget-container">
              <div id="tradingview_spxl"></div>
              <script src="https://s3.tradingview.com/tv.js"></script>
              <script>
              new TradingView.widget({
                "width": "100%", "height": 500,
                "symbol": "AMEX:SPXL",
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "es",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": false,
                "container_id": "tradingview_spxl",
                "overrides": {
                    "paneProperties.background": "#0a0c10",
                    "paneProperties.vertGridProperties.color": "#0e1116",
                    "paneProperties.horzGridProperties.color": "#0e1116"
                }
              });
              </script>
            </div>
            """
            components.html(chart_html, height=520)

        with col_right:
            st.markdown('<div class="section-header-bar">▸ SEÑALES // FASES</div>',
                        unsafe_allow_html=True)

            current_price = data['spxl_price']
            levels        = data['buy_levels']

            phases = [
                ("FASE 1: COMPRA INICIAL",  levels['phase1'], 0.20, 15, current_price <= levels['phase1']),
                ("FASE 2: SEGUNDA ENTRADA", levels['phase2'], 0.15, 10, current_price <= levels['phase2']),
                ("FASE 3: TERCERA ENTRADA", levels['phase3'], 0.20,  7, current_price <= levels['phase3']),
                ("FASE 4: ENTRADA FINAL",   levels['phase4'], 0.20, 10, current_price <= levels['phase4']),
            ]

            for i, (name, price, allocation, drop, is_active) in enumerate(phases, 1):
                if is_active:
                    status_class, status_text_ph = "active", ">> ACTIVA"
                elif current_price > price:
                    status_class, status_text_ph = "pending", "__ ESPERA"
                else:
                    status_class, status_text_ph = "completed", "// DONE"

                distance  = ((current_price - price) / price) * 100
                dist_color = "#00ffad" if distance <= 0 else "#f23645"

                # mini progress bar: how far into the drop are we
                progress = min(100, max(0, (data['spxl_high'] - current_price) /
                                           (data['spxl_high'] - price) * 100)) if data['spxl_high'] > price else 0

                st.markdown(f"""
                <div class="phase-card {status_class}">
                    <div class="phase-number">[{i}]</div>
                    <div style="font-family:'VT323',monospace; color:#00ffad; font-size:0.9rem;
                                letter-spacing:2px; margin-bottom:6px;">{name}</div>
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <span style="font-family:'VT323',monospace; color:white; font-size:1.55rem;
                                     letter-spacing:2px;">${price:.2f}</span>
                        <span style="font-family:'VT323',monospace; color:#333; font-size:0.8rem;">
                            {status_text_ph}
                        </span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width:{progress:.0f}%"></div>
                    </div>
                    <div style="margin-top:6px; font-family:'Share Tech Mono',monospace;
                                font-size:0.72rem; display:flex; gap:12px;">
                        <span style="color:#333;">ALLOC: {allocation:.0%}</span>
                        <span style="color:{dist_color};">DIST: {distance:+.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if current_price <= levels['phase4']:
                st.markdown(
                    '<div class="alert-box alert-sell">🚨 COMPRA MÁXIMA ACTIVA<br>'
                    'TODAS LAS FASES DISPONIBLES</div>',
                    unsafe_allow_html=True)
            elif current_price <= levels['phase1']:
                st.markdown(
                    '<div class="alert-box alert-buy">✅ COMPRA ACTIVA<br>'
                    'EJECUTAR PROTOCOLO</div>',
                    unsafe_allow_html=True)
            else:
                d = ((current_price - levels['phase1']) / levels['phase1']) * 100
                st.markdown(
                    f'<div class="alert-box alert-warning">⏳ STAND BY<br>'
                    f'FALTAN {d:.1f}% PARA FASE 1</div>',
                    unsafe_allow_html=True)

    # ── TAB 2: ESTRATEGIA ─────────────────────────────────────────────────────
    with tab2:
        st.markdown("""
        <div class="terminal-box">
            <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.35rem;
                        letter-spacing:3px; margin-bottom:12px;">
                PREMISA FUNDAMENTAL
            </div>
            <p style="color:#aaa; font-size:0.9rem; line-height:1.9; margin:0;">
                Estrategia basada en que el S&P 500 mantiene
                <span style="color:#00ffad;">macro tendencia alcista</span> a largo plazo.
                SPXL amplifica ese movimiento 3x. La estrategia explota correcciones
                para acumular posición escalonada.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-header-bar">▸ REGLAS DE ENTRADA</div>',
                    unsafe_allow_html=True)

        rules = [
            ("1", "PRIMERA CAÍDA (-15% desde máximo)", "Invertir 20% del capital asignado"),
            ("2", "SEGUNDA CAÍDA (-10% desde Fase 1)",  "Invertir 15% del capital asignado"),
            ("3", "TERCERA CAÍDA (-7% desde Fase 2)",   "Invertir 20% del capital asignado"),
            ("4", "CUARTA CAÍDA  (-10% desde Fase 3)",  "Invertir 20% del capital // 75% total"),
        ]

        for icon, title, desc in rules:
            st.markdown(f"""
            <div class="rule-item">
                <div class="rule-icon">{icon}</div>
                <div>
                    <div style="color:white; font-size:0.88rem; margin-bottom:4px;">{title}</div>
                    <div style="color:#444; font-size:0.78rem;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-header-bar" style="margin-top:22px;">▸ REGLA DE SALIDA</div>',
                    unsafe_allow_html=True)

        st.markdown("""
        <div class="rule-item" style="border-left: 3px solid #f23645;">
            <div class="rule-icon" style="border-color:#f2364522; color:#f23645; background:#f2364509;">$</div>
            <div>
                <div style="color:white; font-size:0.88rem; margin-bottom:4px;">
                    TAKE PROFIT (+20% sobre precio medio)
                </div>
                <div style="color:#444; font-size:0.78rem;">
                    Vender toda la posición al alcanzar objetivo. Sin parciales.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="highlight-quote" style="margin-top:28px;">
            "LA CAÍDA NO ES EL PROBLEMA. ES LA OPORTUNIDAD."
        </div>
        """, unsafe_allow_html=True)

        pdf_path = "assets/SPXL.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                "▸ DESCARGAR ESTRATEGIA PDF",
                pdf_bytes, "SPXL.pdf", "application/pdf",
                use_container_width=True)

    # ── TAB 3: CALCULADORA ────────────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="section-header-bar">▸ CALCULADORA DE CAPITAL</div>',
                    unsafe_allow_html=True)

        col_calc1, col_calc2 = st.columns(2)
        levels = data['buy_levels']

        with col_calc1:
            st.markdown("""
            <div style="font-family:'VT323',monospace; color:#333; font-size:0.82rem;
                        letter-spacing:2px; margin-bottom:10px;">
                // INPUT PARAMETERS
            </div>
            """, unsafe_allow_html=True)
            capital_total     = st.number_input("Capital Total ($):", min_value=1000,
                                                value=10000, step=1000)
            tiene_posicion    = st.checkbox("¿Tienes posición abierta?")
            if tiene_posicion:
                precio_medio      = st.number_input("Precio medio ($):",
                                                    min_value=0.0, value=0.0, step=0.1)
                cantidad_acciones = st.number_input("Nº Acciones:", min_value=0,
                                                    value=0, step=1)
            else:
                precio_medio, cantidad_acciones = 0, 0

        with col_calc2:
            st.markdown("""
            <div style="font-family:'VT323',monospace; color:#333; font-size:0.82rem;
                        letter-spacing:2px; margin-bottom:10px;">
                // ALLOCATION OUTPUT
            </div>
            """, unsafe_allow_html=True)

            allocations = [
                ("FASE 1", 0.20, levels['phase1']),
                ("FASE 2", 0.15, levels['phase2']),
                ("FASE 3", 0.20, levels['phase3']),
                ("FASE 4", 0.20, levels['phase4']),
            ]

            total_invertido = 0
            for fase, pct, precio in allocations:
                monto = capital_total * pct
                total_invertido += monto
                st.markdown(f"""
                <div class="calc-item">
                    <span style="color:#888; font-size:0.85rem;">{fase}</span>
                    <div style="text-align:right;">
                        <span style="color:#00ffad; font-family:'VT323',monospace;
                                     font-size:1.25rem;">${monto:,.0f}</span>
                        <span style="color:#2a2a2a; font-size:0.72rem;
                                     margin-left:8px;">@ ${precio:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            reserva = capital_total * 0.25
            st.markdown(f"""
            <div class="calc-item calc-reserve">
                <span style="color:#555; font-size:0.85rem;">RESERVA (25%)</span>
                <span style="color:#ff9800; font-family:'VT323',monospace;
                             font-size:1.25rem;">${reserva:,.0f}</span>
            </div>
            <div class="calc-total">
                <span style="color:#888;">TOTAL A DESPLEGAR</span>
                <span style="color:#00ffad;">${total_invertido:,.0f}</span>
            </div>
            """, unsafe_allow_html=True)

        if tiene_posicion and precio_medio > 0:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="section-header-bar">▸ ESTADO POSICIÓN ACTUAL</div>',
                        unsafe_allow_html=True)

            valor_actual = cantidad_acciones * data['spxl_price']
            costo_total  = cantidad_acciones * precio_medio
            pnl          = valor_actual - costo_total
            pnl_pct      = (pnl / costo_total) * 100 if costo_total > 0 else 0
            target_price = precio_medio * 1.20

            c1, c2, c3 = st.columns(3)
            c1.metric("Valor Actual",     f"${valor_actual:,.2f}", f"{pnl_pct:+.2f}%")
            c2.metric("Objetivo Venta",   f"${target_price:.2f}", "+20%")
            c3.metric("Distancia Target",
                      f"{((target_price - data['spxl_price']) / data['spxl_price'] * 100):.2f}%")

            if data['spxl_price'] >= target_price:
                st.balloons()
                st.markdown(
                    '<div class="alert-box alert-sell">🎯 OBJETIVO ALCANZADO // EJECUTAR SALIDA TOTAL</div>',
                    unsafe_allow_html=True)
            else:
                remaining = ((target_price - data['spxl_price']) / data['spxl_price']) * 100
                st.markdown(
                    f'<div class="alert-box alert-warning">⏳ EN POSICIÓN // FALTAN {remaining:.1f}% PARA TARGET</div>',
                    unsafe_allow_html=True)

    # ── TAB 4: RIESGO CDS ─────────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="section-header-bar">▸ RIESGO SISTÉMICO // CDS MONITOR</div>',
                    unsafe_allow_html=True)

        st.markdown("""
        <div class="terminal-box">
            <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1rem;
                        letter-spacing:2px; margin-bottom:6px;">
                ÍNDICE: BAMLH0A0HYM2
            </div>
            <div style="font-family:'Share Tech Mono',monospace; color:#444; font-size:0.78rem;">
                ICE BofA US High Yield Index Option-Adjusted Spread
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="margin: 22px 0 5px; font-family:'VT323',monospace; color:#333;
                    font-size:0.82rem; letter-spacing:2px;">
            // NIVEL DE ESTRÉS SISTÉMICO
        </div>
        <div class="cds-gauge">
            <div class="cds-marker" style="left: 30%;"></div>
        </div>
        <div class="cds-labels">
            <span style="color:#00ffad;">NORMAL</span>
            <span>ATENCIÓN</span>
            <span>PELIGRO</span>
            <span style="color:#f23645;">CRISIS &gt;10.7</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        cds_chart = """
        <div class="tradingview-widget-container">
          <div id="tradingview_cds"></div>
          <script src="https://s3.tradingview.com/tv.js"></script>
          <script>
          new TradingView.widget({
            "width": "100%", "height": 400,
            "symbol": "FRED:BAMLH0A0HYM2",
            "interval": "W",
            "theme": "dark",
            "style": "1",
            "locale": "es",
            "enable_publishing": false,
            "hide_side_toolbar": true,
            "container_id": "tradingview_cds",
            "overrides": {
                "paneProperties.background": "#0a0c10",
                "paneProperties.vertGridProperties.color": "#0e1116",
                "paneProperties.horzGridProperties.color": "#0e1116"
            }
          });
          </script>
        </div>
        """
        components.html(cds_chart, height=420)

        st.markdown("""
        <div class="risk-box" style="margin-top:20px;">
            <div style="font-family:'VT323',monospace; color:#f23645; font-size:1.15rem;
                        letter-spacing:2px; margin-bottom:10px;">
                ⚠ PROTOCOLO DE CRISIS
            </div>
            <div style="font-family:'Share Tech Mono',monospace; color:#777;
                        font-size:0.82rem; line-height:1.9;">
                Si CDS &gt; 10.7 → DETENER TODAS LAS COMPRAS INMEDIATAMENTE<br>
                No importa en qué fase esté la corrección.<br>
                El stop sistémico tiene prioridad absoluta sobre cualquier nivel técnico.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="footer">
        <p>
            [END OF TRANSMISSION // RSU TRADING SYSTEM v3.0]<br>
            [REDISTRIBUTION STRATEGY RESEARCH UNIT // ALL RIGHTS RESERVED]
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render()
