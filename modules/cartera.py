import streamlit as st
import pandas as pd
import numpy as np

def render():
    # ── CSS: Terminal Hacker Aesthetic (from roadmap_2026) ──────────────────
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp { background: #0c0e12; }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            color: #00ffad !important;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        h1 {
            font-size: 3.5rem !important;
            text-shadow: 0 0 20px #00ffad66;
            border-bottom: 2px solid #00ffad;
            padding-bottom: 15px;
            margin-bottom: 30px !important;
        }
        h2 {
            font-size: 2.2rem !important;
            color: #00d9ff !important;
            border-left: 4px solid #00ffad;
            padding-left: 15px;
            margin-top: 40px !important;
        }
        h3 { font-size: 1.5rem !important; color: #ff9800 !important; }
        h4 { font-size: 1.3rem !important; color: #9c27b0 !important; }

        p, li {
            font-family: 'Courier New', monospace;
            color: #ccc !important;
            line-height: 1.8;
            font-size: 0.95rem;
        }
        strong { color: #00ffad; font-weight: bold; }

        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad, transparent);
            margin: 40px 0;
        }

        /* Metric cards */
        .metric-card {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #00ffad44;
            border-radius: 8px;
            padding: 20px 25px;
            text-align: center;
            box-shadow: 0 0 15px #00ffad11;
        }
        .metric-label {
            font-family: 'VT323', monospace;
            color: #666;
            font-size: 0.85rem;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .metric-value {
            font-family: 'VT323', monospace;
            font-size: 2.2rem;
            color: #00ffad;
            letter-spacing: 1px;
        }
        .metric-value.negative { color: #f23645; }

        /* Terminal box */
        .terminal-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #00ffad44;
            border-radius: 8px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 0 15px #00ffad11;
        }

        /* Phase / activity box */
        .phase-box {
            background: #0c0e12;
            border-left: 3px solid #00ffad;
            padding: 18px 22px;
            margin: 12px 0;
            border-radius: 0 8px 8px 0;
        }
        .phase-box.red  { border-left-color: #f23645; }
        .phase-box.gold { border-left-color: #ff9800; }

        /* Activity row */
        .activity-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #1a1e26;
            font-family: 'Courier New', monospace;
            font-size: 0.88rem;
        }
        .activity-row:last-child { border-bottom: none; }
        .ticker-tag {
            background: #00ffad22;
            color: #00ffad;
            border: 1px solid #00ffad55;
            border-radius: 4px;
            padding: 2px 8px;
            font-family: 'VT323', monospace;
            font-size: 1rem;
            letter-spacing: 1px;
        }
        .pnl-pos { color: #00ffad; font-weight: bold; }
        .pnl-neg { color: #f23645; font-weight: bold; }

        ul { list-style: none; padding-left: 0; }
        ul li::before { content: "▸ "; color: #00ffad; font-weight: bold; margin-right: 8px; }

        /* Streamlit dataframe dark override */
        .stDataFrame { border: 1px solid #00ffad33 !important; border-radius: 8px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

    # ── HEADER ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; margin-bottom:40px;">
        <div style="font-family:'VT323',monospace; font-size:1rem; color:#666; margin-bottom:10px;">
            [SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]
        </div>
        <h1>💼 CARTERA ESTRATÉGICA RSU</h1>
        <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.2rem; letter-spacing:3px;">
            MONITOR DE POSICIONES // LIVE DATA FEED
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        url = st.secrets["URL_CARTERA"]
        df = pd.read_csv(f"{url}&cache_bus={pd.Timestamp.now().timestamp()}").dropna(how='all')
        df.columns = [c.strip() for c in df.columns]

        # ── Limpieza numérica ─────────────────────────────────────────────
        def clean_numeric(value):
            if pd.isna(value): return 0.0
            val_str = str(value).strip().replace('$', '').replace('%', '').replace(' ', '')
            if ',' in val_str:
                val_str = val_str.replace('.', '').replace(',', '.')
            try:
                return float(val_str)
            except:
                return 0.0

        cols_to_fix = ['Precio Compra', 'Precio Actual', 'P&L Terminal (%)', 'Inversión', 'Valor Actual', 'Comisiones']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        # ── Re-cálculo P&L ────────────────────────────────────────────────
        df['P&L Terminal (%)'] = df.apply(
            lambda x: ((x['Precio Actual'] - x['Precio Compra']) / x['Precio Compra'] * 100)
            if x['Precio Compra'] != 0 else 0, axis=1
        )

        # ── Normalización ─────────────────────────────────────────────────
        df['Estado'] = df['Estado'].astype(str).str.strip().str.upper()
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha', 'Ticker'])

        abiertas = df[df['Estado'] == 'ABIERTA'].copy()
        cerradas = df[df['Estado'] == 'CERRADA'].copy()

        # ── MÉTRICAS ─────────────────────────────────────────────────────
        if not abiertas.empty:
            total_inv   = abiertas['Inversión'].sum()
            total_val   = abiertas['Valor Actual'].sum()
            total_comis = abiertas['Comisiones'].sum()
            pnl_neto    = (total_val - total_inv) - total_comis
            pnl_class   = "negative" if pnl_neto < 0 else ""
            pnl_sign    = "+" if pnl_neto >= 0 else ""

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">▸ Capital Invertido</div>
                    <div class="metric-value">${total_inv:,.2f}</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">▸ Valor Mercado</div>
                    <div class="metric-value">${total_val:,.2f}</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">▸ P&L Real (Neto)</div>
                    <div class="metric-value {pnl_class}">{pnl_sign}${pnl_neto:,.2f}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── POSICIONES ACTIVAS ────────────────────────────────────────────
        st.markdown("<h2>01 // POSICIONES ACTIVAS</h2>", unsafe_allow_html=True)

        if not abiertas.empty:
            cols_vista = ['Fecha', 'Ticker', 'Precio Compra', 'Precio Actual', 'P&L Terminal (%)', 'Comentarios']
            st.dataframe(
                abiertas[cols_vista].sort_values(by='Fecha', ascending=False)
                .style.map(
                    lambda x: f"color: {'#00ffad' if x >= 0 else '#f23645'}",
                    subset=['P&L Terminal (%)']
                )
                .format({
                    'Precio Compra':    '${:.2f}',
                    'Precio Actual':    '${:.2f}',
                    'P&L Terminal (%)': '{:.2f}%',
                    'Fecha':            lambda x: x.strftime('%d/%m/%Y')
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.markdown('<div class="phase-box gold"><p>Sin posiciones activas en este momento.</p></div>',
                        unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── ACTIVIDAD RECIENTE ────────────────────────────────────────────
        st.markdown("<h2>02 // ACTIVIDAD RECIENTE</h2>", unsafe_allow_html=True)

        col_izq, col_der = st.columns(2)

        with col_izq:
            st.markdown("<h3>📥 Últimas 5 Entradas</h3>", unsafe_allow_html=True)
            if not abiertas.empty:
                ult_compras = abiertas.sort_values(by='Fecha', ascending=False).head(5)
                rows_html = ""
                for _, row in ult_compras.iterrows():
                    rows_html += f"""
                    <div class="activity-row">
                        <span style="color:#666;">{row['Fecha'].strftime('%d/%m/%Y')}</span>
                        <span class="ticker-tag">{row['Ticker']}</span>
                        <span style="color:#fff;">${row['Precio Compra']:,.2f}</span>
                    </div>"""
                st.markdown(f'<div class="terminal-box" style="padding:15px;">{rows_html}</div>',
                            unsafe_allow_html=True)

        with col_der:
            st.markdown("<h3>📤 Últimas 5 Salidas</h3>", unsafe_allow_html=True)
            if not cerradas.empty:
                ult_ventas = cerradas.sort_values(by='Fecha', ascending=False).head(5)
                rows_html = ""
                for _, row in ult_ventas.iterrows():
                    pnl_val = row['P&L Terminal (%)']
                    pnl_cls = "pnl-pos" if pnl_val >= 0 else "pnl-neg"
                    pnl_sign = "+" if pnl_val >= 0 else ""
                    comment = str(row.get('Comentarios', ''))[:30] if 'Comentarios' in row else ''
                    rows_html += f"""
                    <div class="activity-row">
                        <span style="color:#666;">{row['Fecha'].strftime('%d/%m/%Y')}</span>
                        <span class="ticker-tag">{row['Ticker']}</span>
                        <span class="{pnl_cls}">{pnl_sign}{pnl_val:.2f}%</span>
                    </div>"""
                st.markdown(f'<div class="terminal-box phase-box red" style="padding:15px;">{rows_html}</div>',
                            unsafe_allow_html=True)

        # ── FOOTER ───────────────────────────────────────────────────────
        st.markdown("""
        <hr>
        <div style="text-align:center; padding:20px; border-top:1px solid #1a1e26;">
            <p style="font-family:'VT323',monospace; color:#444; font-size:0.9rem;">
                [END OF TRANSMISSION // CARTERA_RSU_v2.0]<br>
                [STATUS: LIVE] [DATA: GOOGLE SHEETS FEED]
            </p>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.markdown(f"""
        <div style="background:#1a0f0f; border:1px solid #f2364566; border-radius:8px; padding:20px; margin:20px 0;">
            <p style="color:#f23645 !important; font-family:'VT323',monospace; font-size:1.2rem;">
                ⚠️ ERROR DE CONEXIÓN
            </p>
            <p style="color:#ccc !important;">{e}</p>
        </div>
        """, unsafe_allow_html=True)
