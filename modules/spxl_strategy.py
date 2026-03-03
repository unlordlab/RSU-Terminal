# modules/spxl_strategy.py
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

        /* ── BASE ────────────────────────────────── */
        .stApp { background: #0a0c10; }

        * { box-sizing: border-box; }

        /* ── HEADINGS ────────────────────────────── */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            text-transform: uppercase;
            letter-spacing: 3px;
        }

        /* ── BODY TEXT ───────────────────────────── */
        p, li, span, div {
            font-family: 'Share Tech Mono', monospace;
        }

        /* ── MAIN HEADER ─────────────────────────── */
        .main-header {
            background: #0a0c10;
            border: 1px solid #00ffad44;
            border-radius: 4px;
            padding: 35px 30px 25px;
            margin-bottom: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
            box-shadow: 0 0 40px #00ffad0a, inset 0 0 60px #00ffad04;
        }

        .main-header::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00ffad, transparent);
        }

        .main-header::after {
            content: "";
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad44, transparent);
        }

        .header-pre {
            font-family: 'VT323', monospace;
            font-size: 0.85rem;
            color: #444;
            letter-spacing: 3px;
            margin-bottom: 8px;
        }

        .main-title {
            font-family: 'VT323', monospace !important;
            color: #00ffad;
            font-size: 3.8rem;
            font-weight: 400;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 6px;
            text-shadow: 0 0 30px #00ffad55, 0 0 60px #00ffad22;
            line-height: 1;
        }

        .sub-title {
            font-family: 'VT323', monospace;
            color: #00d9ff;
            font-size: 1rem;
            margin-top: 12px;
            letter-spacing: 4px;
        }

        .header-post {
            font-family: 'VT323', monospace;
            font-size: 0.75rem;
            color: #333;
            margin-top: 15px;
            letter-spacing: 2px;
        }

        /* ── METRIC CARDS ────────────────────────── */
        .metric-card {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-top: 2px solid #00ffad33;
            border-radius: 4px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
        }

        .metric-card:hover {
            border-color: #00ffad55;
            box-shadow: 0 0 20px #00ffad11;
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
            color: #444;
            font-size: 0.7rem;
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

        /* ── SECTION CONTAINERS ──────────────────── */
        .terminal-box {
            background: linear-gradient(135deg, #0c0e12 0%, #0e1116 100%);
            border: 1px solid #00ffad22;
            border-radius: 4px;
            padding: 25px;
            margin: 15px 0;
            box-shadow: 0 0 15px #00ffad08;
            position: relative;
        }

        .terminal-box::before {
            content: "//";
            position: absolute;
            top: 10px; left: 15px;
            font-family: 'VT323', monospace;
            color: #00ffad33;
            font-size: 0.85rem;
        }

        .section-header-bar {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-left: 3px solid #00ffad;
            padding: 12px 20px;
            margin-bottom: 15px;
            border-radius: 0 4px 4px 0;
            font-family: 'VT323', monospace;
            color: #00ffad;
            font-size: 1.2rem;
            letter-spacing: 3px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* ── PHASE CARDS ─────────────────────────── */
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
        }

        .phase-card.active {
            border-color: #00ffad44;
            background: linear-gradient(135deg, #0c0e12 0%, #00ffad08 100%);
            box-shadow: 0 0 20px #00ffad11;
        }

        .phase-card.active::before { background: #00ffad; }
        .phase-card.pending::before { background: #2a3f5f; opacity: 0.4; }
        .phase-card.completed::before { background: #4caf50; opacity: 0.5; }

        .phase-card.pending { opacity: 0.55; }
        .phase-card.completed { opacity: 0.45; }

        .phase-number {
            position: absolute;
            top: 10px; right: 12px;
            font-family: 'VT323', monospace;
            font-size: 1.4rem;
            color: #2a3f5f;
            letter-spacing: 1px;
        }

        .phase-card.active .phase-number { color: #00ffad; }
        .phase-card.completed .phase-number { color: #4caf50; }

        /* ── ALERT BOXES ─────────────────────────── */
        .alert-box {
            padding: 15px 20px;
            border-radius: 4px;
            margin: 12px 0;
            border: 1px solid;
            font-family: 'VT323', monospace;
            font-size: 1.1rem;
            letter-spacing: 2px;
            position: relative;
        }

        .alert-buy {
            background: #00ffad08;
            border-color: #00ffad55;
            color: #00ffad;
        }

        .alert-sell {
            background: #f2364508;
            border-color: #f2364555;
            color: #f23645;
        }

        .alert-warning {
            background: #ff980008;
            border-color: #ff980055;
            color: #ff9800;
        }

        /* ── HIGHLIGHT QUOTE ─────────────────────── */
        .highlight-quote {
            background: #00ffad08;
            border: 1px solid #00ffad22;
            border-radius: 4px;
            padding: 20px;
            margin: 20px 0;
            font-family: 'VT323', monospace;
            font-size: 1.25rem;
            color: #00ffad;
            text-align: center;
            letter-spacing: 2px;
        }

        /* ── RISK BOX ────────────────────────────── */
        .risk-box {
            background: linear-gradient(135deg, #120a0a 0%, #1a0e0e 100%);
            border: 1px solid #f2364522;
            border-radius: 4px;
            padding: 20px;
            margin: 15px 0;
        }

        /* ── STRATEGY GRID ───────────────────────── */
        .strategy-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin: 15px 0;
        }

        .strategy-card {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-top: 2px solid #00ffad33;
            border-radius: 4px;
            padding: 15px;
            font-family: 'VT323', monospace;
            font-size: 1.05rem;
            color: #00ffad;
            letter-spacing: 1px;
        }

        /* ── RULE ITEMS ──────────────────────────── */
        .rule-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin: 10px 0;
            padding: 14px;
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 4px;
            font-family: 'Share Tech Mono', monospace;
        }

        .rule-icon {
            width: 26px;
            height: 26px;
            background: #00ffad15;
            color: #00ffad;
            border: 1px solid #00ffad33;
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'VT323', monospace;
            font-size: 1rem;
            flex-shrink: 0;
        }

        /* ── CDS GAUGE ───────────────────────────── */
        .cds-gauge {
            width: 100%;
            height: 24px;
            background: linear-gradient(90deg, #00ffad 0%, #ff9800 50%, #f23645 100%);
            border-radius: 2px;
            position: relative;
            margin: 20px 0 8px;
            border: 1px solid #1a1e26;
        }

        .cds-marker {
            position: absolute;
            top: -8px;
            width: 3px;
            height: 40px;
            background: white;
            box-shadow: 0 0 8px rgba(255,255,255,0.8);
            transition: left 0.5s ease;
        }

        .cds-labels {
            display: flex;
            justify-content: space-between;
            font-family: 'VT323', monospace;
            color: #555;
            font-size: 0.85rem;
            letter-spacing: 1px;
            margin-top: 4px;
        }

        /* ── HORIZONTAL RULE ─────────────────────── */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad44, transparent);
            margin: 25px 0;
        }

        /* ── PROGRESS BAR ────────────────────────── */
        .progress-bar {
            width: 100%;
            height: 6px;
            background: #0c0e12;
            border-radius: 2px;
            overflow: hidden;
            margin: 8px 0;
            border: 1px solid #1a1e26;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ffad 0%, #00ffad66 100%);
            transition: width 0.5s ease;
        }

        /* ── CALC ITEMS ──────────────────────────── */
        .calc-item {
            background: #0c0e12;
            padding: 12px 15px;
            border-radius: 4px;
            margin: 6px 0;
            border-left: 3px solid #00ffad;
            display: flex;
            justify-content: space-between;
            font-family: 'Share Tech Mono', monospace;
        }

        .calc-reserve {
            background: #ff980008;
            border-left-color: #ff9800;
        }

        .calc-total {
            background: #00ffad08;
            border: 1px solid #00ffad33;
            border-radius: 4px;
            padding: 14px 15px;
            margin-top: 10px;
            display: flex;
            justify-content: space-between;
            font-family: 'VT323', monospace;
            font-size: 1.2rem;
        }

        /* ── FOOTER ──────────────────────────────── */
        .footer {
            text-align: center;
            padding: 20px;
            border-top: 1px solid #1a1e26;
            margin-top: 30px;
        }

        .footer p {
            font-family: 'VT323', monospace;
            color: #333;
            font-size: 0.85rem;
            letter-spacing: 2px;
        }

        /* ── STREAMLIT OVERRIDES ──────────────────── */
        .stTabs [data-baseweb="tab"] {
            font-family: 'VT323', monospace !important;
            letter-spacing: 2px;
            font-size: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # === HEADER ===
    st.markdown("""
    <div class="main-header">
        <div class="header-pre">[SECURE CONNECTION ESTABLISHED // RSU TRADING SYSTEM v2.0]</div>
        <h1 class="main-title">📈 ESTRATEGIA SPXL</h1>
        <div class="sub-title">REDISTRIBUTION STRATEGY RESEARCH UNIT // SISTEMA ACTIVO</div>
        <div class="header-post">[TIMESTAMP: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """] [STATUS: LIVE]</div>
    </div>
    """, unsafe_allow_html=True)

    # === DATOS ===
    @st.cache_data(ttl=300)
    def get_market_data():
        try:
            spxl = yf.Ticker("SPXL")
            spxl_hist = spxl.history(period="1y")
            spx = yf.Ticker("^GSPC")
            spx_hist = spx.history(period="2d")

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
                    'spxl_price': current_price,
                    'spxl_change': change_pct,
                    'spxl_high': yearly_high,
                    'spxl_low': yearly_low,
                    'drawdown': drawdown,
                    'spx_price': spx_hist['Close'].iloc[-1] if not spx_hist.empty else 0,
                    'spx_change': ((spx_hist['Close'].iloc[-1] - spx_hist['Close'].iloc[-2]) / spx_hist['Close'].iloc[-2] * 100) if len(spx_hist) >= 2 else 0,
                    'buy_levels': {'phase1': p1, 'phase2': p2, 'phase3': p3, 'phase4': p4}
                }
        except Exception as e:
            st.error(f"Error obteniendo datos: {e}")
        return None

    data = get_market_data()
    if data is None:
        st.error("No se pudieron obtener datos del mercado")
        return

    # === MÉTRICAS ===
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
            <div class="metric-change" style="color:#444;">MAX: ${data['spxl_high']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        current_dd = abs(data['drawdown'])
        if current_dd < 15:
            phase, phase_color = "STAND BY", "#555"
        elif current_dd < 25:
            phase, phase_color = "FASE 1 //", "#00ffad"
        elif current_dd < 32:
            phase, phase_color = "FASE 2 //", "#00ffad"
        elif current_dd < 39:
            phase, phase_color = "FASE 3 //", "#ff9800"
        else:
            phase, phase_color = "FASE 4 //", "#f23645"

        st.markdown(f"""
        <div class="metric-card" style="border-top-color: {phase_color}55;">
            <div class="metric-label">// ESTADO</div>
            <div class="metric-value" style="color: {phase_color}; font-size: 1.8rem;">{phase}</div>
            <div class="metric-change" style="color:#444;">DD: {current_dd:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # === TABS ===
    tab1, tab2, tab3, tab4 = st.tabs(["DASHBOARD", "ESTRATEGIA", "CALCULADORA", "RIESGO_CDS"])

    # ── TAB 1: DASHBOARD ────────────────────────────────────────────────────
    with tab1:
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.markdown('<div class="section-header-bar">▸ GRAFICO SPXL // NIVELES</div>', unsafe_allow_html=True)
            chart_html = """
            <div class="tradingview-widget-container">
              <div id="tradingview_spxl"></div>
              <script src="https://s3.tradingview.com/tv.js"></script>
              <script>
              new TradingView.widget({
                "width": "100%",
                "height": 500,
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
            st.markdown('<div class="section-header-bar">▸ SEÑALES // FASES</div>', unsafe_allow_html=True)

            current_price = data['spxl_price']
            levels = data['buy_levels']

            phases = [
                ("FASE 1: COMPRA INICIAL",  levels['phase1'], 0.20, 15, current_price <= levels['phase1']),
                ("FASE 2: SEGUNDA ENTRADA", levels['phase2'], 0.15, 10, current_price <= levels['phase2']),
                ("FASE 3: TERCERA ENTRADA", levels['phase3'], 0.20,  7, current_price <= levels['phase3']),
                ("FASE 4: ENTRADA FINAL",   levels['phase4'], 0.20, 10, current_price <= levels['phase4']),
            ]

            for i, (name, price, allocation, drop, is_active) in enumerate(phases, 1):
                if is_active:
                    status_class, status_text = "active", ">> ACTIVA"
                elif current_price < price:
                    status_class, status_text = "completed", "// DONE"
                else:
                    status_class, status_text = "pending", "__ ESPERA"

                distance = ((current_price - price) / price) * 100
                dist_color = "#00ffad" if distance <= 0 else "#f23645"

                st.markdown(f"""
                <div class="phase-card {status_class}">
                    <div class="phase-number">[{i}]</div>
                    <div style="font-family:'VT323',monospace; color:#00ffad; font-size:0.95rem; letter-spacing:2px; margin-bottom:6px;">{name}</div>
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <span style="font-family:'VT323',monospace; color:white; font-size:1.6rem; letter-spacing:2px;">${price:.2f}</span>
                        <span style="font-family:'VT323',monospace; color:#444; font-size:0.85rem;">{status_text}</span>
                    </div>
                    <div style="margin-top:8px; font-family:'Share Tech Mono',monospace; font-size:0.75rem; display:flex; gap:12px;">
                        <span style="color:#444;">ALLOC: {allocation:.0%}</span>
                        <span style="color:{dist_color};">DIST: {distance:+.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if current_price <= levels['phase4']:
                st.markdown('<div class="alert-box alert-sell">🚨 COMPRA MÁXIMA ACTIVA<br>TODAS LAS FASES DISPONIBLES</div>', unsafe_allow_html=True)
            elif current_price <= levels['phase1']:
                st.markdown('<div class="alert-box alert-buy">✅ COMPRA ACTIVA<br>EJECUTAR PROTOCOLO</div>', unsafe_allow_html=True)
            else:
                d = ((current_price - levels['phase1']) / levels['phase1']) * 100
                st.markdown(f'<div class="alert-box alert-warning">⏳ STAND BY<br>FALTAN {d:.1f}% PARA FASE 1</div>', unsafe_allow_html=True)

    # ── TAB 2: ESTRATEGIA ────────────────────────────────────────────────────
    with tab2:
        st.markdown("""
        <div class="terminal-box">
            <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.4rem; letter-spacing:3px; margin-bottom:12px;">
                PREMISA FUNDAMENTAL
            </div>
            <p style="color:#ccc; font-size:0.95rem; line-height:1.8;">
                Estrategia basada en que el S&P 500 mantiene 
                <span style="color:#00ffad;">macro tendencia alcista</span> a largo plazo.
                SPXL amplifica ese movimiento 3x. La estrategia explota correcciones
                para acumular posición escalonada.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-header-bar">▸ REGLAS DE ENTRADA</div>', unsafe_allow_html=True)

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
                    <div style="color:white; font-size:0.9rem; margin-bottom:4px;">{title}</div>
                    <div style="color:#555; font-size:0.8rem;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-header-bar" style="margin-top:20px;">▸ REGLA DE SALIDA</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="rule-item" style="border-left: 3px solid #f23645;">
            <div class="rule-icon" style="border-color:#f2364533; color:#f23645; background:#f2364511;">$</div>
            <div>
                <div style="color:white; font-size:0.9rem; margin-bottom:4px;">TAKE PROFIT (+20% sobre precio medio)</div>
                <div style="color:#555; font-size:0.8rem;">Vender toda la posición al alcanzar objetivo. Sin parciales.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="highlight-quote" style="margin-top:25px;">
            "LA CAÍDA NO ES EL PROBLEMA. ES LA OPORTUNIDAD."
        </div>
        """, unsafe_allow_html=True)

        pdf_path = "assets/SPXL.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button("▸ DESCARGAR ESTRATEGIA PDF", pdf_bytes, "SPXL.pdf", "application/pdf", use_container_width=True)

    # ── TAB 3: CALCULADORA ───────────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="section-header-bar">▸ CALCULADORA DE CAPITAL</div>', unsafe_allow_html=True)

        col_calc1, col_calc2 = st.columns(2)
        levels = data['buy_levels']

        with col_calc1:
            st.markdown("""
            <div style="font-family:'VT323',monospace; color:#444; font-size:0.85rem; letter-spacing:2px; margin-bottom:10px;">
                // INPUT PARAMETERS
            </div>
            """, unsafe_allow_html=True)
            capital_total = st.number_input("Capital Total ($):", min_value=1000, value=10000, step=1000)
            tiene_posicion = st.checkbox("¿Tienes posición abierta?")
            if tiene_posicion:
                precio_medio      = st.number_input("Precio medio ($):", min_value=0.0, value=0.0, step=0.1)
                cantidad_acciones = st.number_input("Nº Acciones:", min_value=0, value=0, step=1)
            else:
                precio_medio, cantidad_acciones = 0, 0

        with col_calc2:
            st.markdown("""
            <div style="font-family:'VT323',monospace; color:#444; font-size:0.85rem; letter-spacing:2px; margin-bottom:10px;">
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
                    <span style="color:white;">{fase}</span>
                    <div style="text-align:right;">
                        <span style="color:#00ffad; font-family:'VT323',monospace; font-size:1.2rem;">${monto:,.0f}</span>
                        <span style="color:#333; font-size:0.75rem; margin-left:8px;">@ ${precio:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            reserva = capital_total * 0.25
            st.markdown(f"""
            <div class="calc-item calc-reserve">
                <span style="color:#666;">RESERVA (25%)</span>
                <span style="color:#ff9800; font-family:'VT323',monospace; font-size:1.2rem;">${reserva:,.0f}</span>
            </div>
            <div class="calc-total">
                <span style="color:white;">TOTAL A DESPLEGAR</span>
                <span style="color:#00ffad;">${total_invertido:,.0f}</span>
            </div>
            """, unsafe_allow_html=True)

        if tiene_posicion and precio_medio > 0:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="section-header-bar">▸ ESTADO POSICIÓN ACTUAL</div>', unsafe_allow_html=True)

            valor_actual = cantidad_acciones * data['spxl_price']
            costo_total  = cantidad_acciones * precio_medio
            pnl          = valor_actual - costo_total
            pnl_pct      = (pnl / costo_total) * 100 if costo_total > 0 else 0
            target_price = precio_medio * 1.20

            c1, c2, c3 = st.columns(3)
            c1.metric("Valor Actual",    f"${valor_actual:,.2f}", f"{pnl_pct:+.2f}%")
            c2.metric("Objetivo Venta",  f"${target_price:.2f}", "+20%")
            c3.metric("Distancia Target", f"{((target_price - data['spxl_price']) / data['spxl_price'] * 100):.2f}%")

            if data['spxl_price'] >= target_price:
                st.balloons()
                st.markdown('<div class="alert-box alert-sell">🎯 OBJETIVO ALCANZADO // EJECUTAR SALIDA TOTAL</div>', unsafe_allow_html=True)
            else:
                remaining = ((target_price - data['spxl_price']) / data['spxl_price']) * 100
                st.markdown(f'<div class="alert-box alert-warning">⏳ EN POSICIÓN // FALTAN {remaining:.1f}% PARA TARGET</div>', unsafe_allow_html=True)

    # ── TAB 4: RIESGO CDS ────────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="section-header-bar">▸ RIESGO SISTÉMICO // CDS MONITOR</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="terminal-box">
            <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1rem; letter-spacing:2px; margin-bottom:8px;">
                INDICE: BAMLH0A0HYM2
            </div>
            <div style="font-family:'Share Tech Mono',monospace; color:#555; font-size:0.8rem;">
                ICE BofA US High Yield Index Option-Adjusted Spread
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="margin: 20px 0 5px; font-family:'VT323',monospace; color:#444; font-size:0.85rem; letter-spacing:2px;">
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
            "width": "100%",
            "height": 400,
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
            <div style="font-family:'VT323',monospace; color:#f23645; font-size:1.2rem; letter-spacing:2px; margin-bottom:10px;">
                ⚠️ PROTOCOLO DE CRISIS
            </div>
            <div style="font-family:'Share Tech Mono',monospace; color:#888; font-size:0.85rem; line-height:1.8;">
                Si CDS &gt; 10.7 → DETENER TODAS LAS COMPRAS INMEDIATAMENTE<br>
                No importa en qué fase esté la corrección.<br>
                El stop sistémico tiene prioridad absoluta sobre cualquier nivel técnico.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # === FOOTER ===
    st.markdown("""
    <div class="footer">
        <p>
            [END OF TRANSMISSION // RSU TRADING SYSTEM v2.0]<br>
            [REDISTRIBUTION STRATEGY RESEARCH UNIT // ALL RIGHTS RESERVED]
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render()
