import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import plotly.graph_objects as go
import requests as _requests

# ── Telegram notification helper ────────────────────────────────────────────
def send_telegram(msg: str):
    try:
        token   = st.secrets.get("TELEGRAM_TOKEN", "")
        chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return
        _requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
            timeout=5
        )
    except Exception:
        pass  # Never break the app over a notification

def check_and_notify(df: pd.DataFrame):
    tickers_now = set(df[df["Estado"] == "ABIERTA"]["Ticker"].tolist())
    if "tickers_prev" not in st.session_state:
        st.session_state.tickers_prev = tickers_now
        return
    entradas = tickers_now - st.session_state.tickers_prev
    salidas  = st.session_state.tickers_prev - tickers_now
    for t in sorted(entradas):
        send_telegram(f"🟢 <b>ENTRADA</b>\n📈 Ticker: <code>{t}</code>\n[CARTERA RSU // NUEVA POSICIÓN ABIERTA]")
    for t in sorted(salidas):
        send_telegram(f"🔴 <b>SALIDA</b>\n📉 Ticker: <code>{t}</code>\n[CARTERA RSU // POSICIÓN CERRADA]")
    st.session_state.tickers_prev = tickers_now

# ── Market status helper ──────────────────────────────────────────────────────
def get_market_status():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    weekday = now.weekday()
    hour = now.hour + now.minute / 60
    if weekday >= 5:
        return "CLOSED", "#f23645"
    if 9.5 <= hour < 16.0:
        return "OPEN", "#00ffad"
    if 4.0 <= hour < 9.5 or 16.0 <= hour < 20.0:
        return "PRE/POST", "#ff9800"
    return "CLOSED", "#f23645"

# ── CSV loader with cache ─────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_data(url: str, _cache_key: int = 0) -> pd.DataFrame:
    df = pd.read_csv(url).dropna(how="all")
    df.columns = [c.strip() for c in df.columns]
    return df

# ── Numeric cleaner ───────────────────────────────────────────────────────────
def clean_numeric(value):
    if pd.isna(value):
        return 0.0
    val_str = str(value).strip().replace("$", "").replace("%", "").replace(" ", "")
    if "," in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    try:
        return float(val_str)
    except Exception:
        return 0.0

# ── Required columns ──────────────────────────────────────────────────────────
REQUIRED_COLS = {"Ticker", "Estado", "Fecha", "Precio Compra", "Precio Actual", "Inversión", "Valor Actual", "Comisiones"}

def render():
    # ── CSS ──────────────────────────────────────────────────────────────────
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
        .metric-sub {
            font-family: 'VT323', monospace;
            font-size: 1rem;
            color: #00ffad99;
            margin-top: 4px;
            letter-spacing: 1px;
        }
        .metric-sub.negative { color: #f2364599; }

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

        /* Custom HTML table */
        .terminal-table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
        }
        .terminal-table th {
            font-family: 'VT323', monospace;
            color: #00d9ff;
            font-size: 1rem;
            letter-spacing: 2px;
            text-transform: uppercase;
            border-bottom: 1px solid #00ffad44;
            padding: 10px 12px;
            text-align: left;
        }
        .terminal-table td {
            color: #ccc;
            padding: 9px 12px;
            border-bottom: 1px solid #1a1e2688;
        }
        .terminal-table tr:last-child td { border-bottom: none; }
        .terminal-table tr:hover td { background: #00ffad08; }

        /* Concentration bar */
        .conc-bar-bg {
            background: #1a1e26;
            border-radius: 4px;
            height: 10px;
            width: 100%;
            overflow: hidden;
        }
        .conc-bar-fill {
            height: 10px;
            border-radius: 4px;
        }

        ul { list-style: none; padding-left: 0; }
        ul li::before { content: "▸ "; color: #00ffad; font-weight: bold; margin-right: 8px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Market status + last update ──────────────────────────────────────────
    mkt_status, mkt_color = get_market_status()
    last_update = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    st.markdown(f"""
    <div style="text-align:center; margin-bottom:40px;">
        <div style="font-family:'VT323',monospace; font-size:1rem; color:#666; margin-bottom:10px;">
            [SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]
        </div>
        <h1>💼 CARTERA ESTRATÉGICA RSU</h1>
        <div style="display:flex; justify-content:center; align-items:center; gap:30px; flex-wrap:wrap; margin-top:12px;">
            <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.2rem; letter-spacing:3px;">
                MONITOR DE POSICIONES // LIVE DATA FEED
            </div>
            <div style="background:{mkt_color}22; border:1px solid {mkt_color}88; border-radius:6px;
                        padding:4px 16px; font-family:'VT323',monospace; color:{mkt_color};
                        font-size:1rem; letter-spacing:2px;">
                ● MKT: {mkt_status}
            </div>
            <div style="font-family:'VT323',monospace; color:#444; font-size:0.9rem; letter-spacing:1px;">
                LAST UPDATE: {last_update}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        import unicodedata
        def norm_col(s):
            return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()

        url = st.secrets["URL_CARTERA"]
        cache_key = int(pd.Timestamp.now().timestamp() // 300)
        df_raw = load_data(url, _cache_key=cache_key)

        # ── Column validation (accent-tolerant) ───────────────────────────
        col_map = {norm_col(c): c for c in df_raw.columns}
        required_norm = {norm_col(r): r for r in REQUIRED_COLS}
        missing_display = [orig for n, orig in required_norm.items() if n not in col_map]

        if missing_display:
            st.markdown(f"""
            <div class="phase-box red">
                <p style="color:#f23645 !important;">&#9888;&#65039; Columnas faltantes en el feed: <strong>{', '.join(missing_display)}</strong></p>
                <p>Columnas disponibles: {', '.join(df_raw.columns.tolist())}</p>
            </div>""", unsafe_allow_html=True)
            return

        # Remap column names via accent-normalised match
        rename = {col_map[n]: orig for n, orig in required_norm.items() if col_map[n] != orig}
        df = df_raw.rename(columns=rename).copy()

        # ── Numeric cleaning (P&L excluded — recalculated fresh below) ───
        cols_to_fix = ["Precio Compra", "Precio Actual", "Inversion", "Valor Actual", "Comisiones"]
        # Also try accented version
        inv_col = "Inversión" if "Inversión" in df.columns else "Inversion"
        cols_to_fix = ["Precio Compra", "Precio Actual", inv_col, "Valor Actual", "Comisiones"]
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        # Ensure canonical column name
        if inv_col != "Inversión":
            df = df.rename(columns={inv_col: "Inversión"})

        # ── P&L recalculation ─────────────────────────────────────────────
        df["P&L Terminal (%)"] = df.apply(
            lambda x: ((x["Precio Actual"] - x["Precio Compra"]) / x["Precio Compra"] * 100)
            if x["Precio Compra"] != 0 else 0, axis=1
        )

        # ── Normalisation ─────────────────────────────────────────────────
        df["Estado"] = df["Estado"].astype(str).str.strip().str.upper()
        df["Ticker"] = df["Ticker"].astype(str).str.strip()
        df["Fecha"]  = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.dropna(subset=["Fecha", "Ticker"])

        abiertas = df[df["Estado"] == "ABIERTA"].copy()
        cerradas = df[df["Estado"] == "CERRADA"].copy()

        # ── Telegram notifications ────────────────────────────────────────
        check_and_notify(df)

        # ── Guard: only filter zero-investment rows if the column parsed correctly
        if "Inversión" in abiertas.columns and abiertas["Inversión"].sum() > 0:
            abiertas = abiertas[abiertas["Inversión"] > 0]
        if "Inversión" in cerradas.columns and cerradas["Inversión"].sum() > 0:
            cerradas = cerradas[cerradas["Inversión"] > 0]

        # ── MÉTRICAS ──────────────────────────────────────────────────────
        if not abiertas.empty:
            total_inv   = abiertas["Inversión"].sum()
            total_val   = abiertas["Valor Actual"].sum()
            total_comis = abiertas["Comisiones"].sum()
            pnl_neto    = (total_val - total_inv) - total_comis
            pnl_pct     = (pnl_neto / total_inv * 100) if total_inv != 0 else 0
            pnl_class   = "negative" if pnl_neto < 0 else ""
            pnl_sign    = "+" if pnl_neto >= 0 else ""
            pct_sign    = "+" if pnl_pct >= 0 else ""
            val_pct     = ((total_val - total_inv) / total_inv * 100) if total_inv != 0 else 0
            val_sign    = "+" if val_pct >= 0 else ""
            val_class   = "negative" if val_pct < 0 else ""

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">▸ Capital Invertido</div>
                    <div class="metric-value">${total_inv:,.2f}</div>
                    <div class="metric-sub">Base de referencia</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">▸ Valor Mercado</div>
                    <div class="metric-value">${total_val:,.2f}</div>
                    <div class="metric-sub {val_class}">{val_sign}{val_pct:.2f}% vs compra</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">▸ P&L Real (Neto)</div>
                    <div class="metric-value {pnl_class}">{pnl_sign}${pnl_neto:,.2f}</div>
                    <div class="metric-sub {pnl_class}">{pct_sign}{pnl_pct:.2f}% sobre capital</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── POSICIONES ACTIVAS ────────────────────────────────────────────
        st.markdown("<h2>01 // POSICIONES ACTIVAS</h2>", unsafe_allow_html=True)

        if not abiertas.empty:
            sorted_ab = abiertas.sort_values(by="Fecha", ascending=False)
            rows_html = ""
            for _, row in sorted_ab.iterrows():
                pnl = row["P&L Terminal (%)"]
                pnl_color = "#00ffad" if pnl >= 0 else "#f23645"
                pnl_sign = "+" if pnl >= 0 else ""
                comment  = str(row.get("Comentarios", ""))[:40] if "Comentarios" in row.index else "—"
                rows_html += f"""
                <tr>
                    <td style="color:#666;">{row['Fecha'].strftime('%d/%m/%Y')}</td>
                    <td><span class="ticker-tag">{row['Ticker']}</span></td>
                    <td>${row['Precio Compra']:,.2f}</td>
                    <td>${row['Precio Actual']:,.2f}</td>
                    <td style="color:{pnl_color}; font-weight:bold;">{pnl_sign}{pnl:.2f}%</td>
                    <td style="color:#666; font-size:0.8rem;">{comment}</td>
                </tr>"""

            st.markdown(f"""
            <div class="terminal-box" style="padding:10px 20px; max-height:400px; overflow-y:auto;">
                <table class="terminal-table">
                    <thead><tr>
                        <th>Fecha</th><th>Ticker</th><th>P. Compra</th>
                        <th>P. Actual</th><th>P&L %</th><th>Comentarios</th>
                    </tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="phase-box gold"><p>Sin posiciones activas en este momento.</p></div>',
                        unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── ACTIVIDAD RECIENTE ────────────────────────────────────────────
        st.markdown("<h2>02 // ACTIVIDAD RECIENTE</h2>", unsafe_allow_html=True)

        col_izq, col_der = st.columns(2)

        with col_izq:
            st.markdown("<h3>📥 Últimas 5 Entradas</h3>", unsafe_allow_html=True)
            all_trades = df.sort_values(by="Fecha", ascending=False).head(5)
            if not all_trades.empty:
                rows_html = ""
                for _, row in all_trades.iterrows():
                    estado_color = "#00ffad" if row["Estado"] == "ABIERTA" else "#666"
                    rows_html += f"""
                    <div class="activity-row">
                        <span style="color:#666;">{row['Fecha'].strftime('%d/%m/%Y')}</span>
                        <span class="ticker-tag">{row['Ticker']}</span>
                        <span style="color:#fff;">${row['Precio Compra']:,.2f}</span>
                        <span style="font-family:'VT323',monospace; color:{estado_color}; font-size:0.85rem;">{row['Estado']}</span>
                    </div>"""
                st.markdown(f'<div class="terminal-box" style="padding:15px; max-height:300px; overflow-y:auto;">{rows_html}</div>',
                            unsafe_allow_html=True)

        with col_der:
            st.markdown("<h3>📤 Últimas 5 Salidas</h3>", unsafe_allow_html=True)
            if not cerradas.empty:
                ult_ventas = cerradas.sort_values(by="Fecha", ascending=False).head(5)
                rows_html = ""
                for _, row in ult_ventas.iterrows():
                    pnl_val  = row["P&L Terminal (%)"]
                    pnl_color = "#00ffad" if pnl_val >= 0 else "#f23645"
                    pnl_sign = "+" if pnl_val >= 0 else ""
                    rows_html += f"""
                    <div class="activity-row">
                        <span style="color:#666;">{row['Fecha'].strftime('%d/%m/%Y')}</span>
                        <span class="ticker-tag">{row['Ticker']}</span>
                        <span style="color:{pnl_color}; font-weight:bold;">{pnl_sign}{pnl_val:.2f}%</span>
                    </div>"""
                st.markdown(f'<div class="terminal-box phase-box red" style="padding:15px; max-height:300px; overflow-y:auto;">{rows_html}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<div class="phase-box gold"><p>Sin operaciones cerradas aún.</p></div>',
                            unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── HISTORIAL COMPLETO DE CERRADAS ────────────────────────────────
        st.markdown("<h2>04 // HISTORIAL DE OPERACIONES CERRADAS</h2>", unsafe_allow_html=True)

        if not cerradas.empty:
            sorted_cl = cerradas.sort_values(by="Fecha", ascending=False)
            ganadas   = len(cerradas[cerradas["P&L Terminal (%)"] > 0])
            perdidas  = len(cerradas[cerradas["P&L Terminal (%)"] <= 0])
            win_rate  = ganadas / len(cerradas) * 100 if len(cerradas) > 0 else 0
            avg_pnl   = cerradas["P&L Terminal (%)"].mean()
            avg_sign  = "+" if avg_pnl >= 0 else ""
            avg_cls   = "negative" if avg_pnl < 0 else ""

            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">▸ Trades Cerrados</div>
                    <div class="metric-value">{len(cerradas)}</div>
                    <div class="metric-sub">{ganadas}W / {perdidas}L</div>
                </div>""", unsafe_allow_html=True)
            with sc2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">▸ Win Rate</div>
                    <div class="metric-value">{win_rate:.1f}%</div>
                    <div class="metric-sub">Operaciones ganadoras</div>
                </div>""", unsafe_allow_html=True)
            with sc3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">▸ P&L Medio</div>
                    <div class="metric-value {avg_cls}">{avg_sign}{avg_pnl:.2f}%</div>
                    <div class="metric-sub {avg_cls}">Por operación cerrada</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            rows_html = ""
            for _, row in sorted_cl.iterrows():
                pnl      = row["P&L Terminal (%)"]
                pnl_color = "#00ffad" if pnl >= 0 else "#f23645"
                pnl_sign = "+" if pnl >= 0 else ""
                comment  = str(row.get("Comentarios", ""))[:40] if "Comentarios" in row.index else "—"
                rows_html += f"""
                <tr>
                    <td style="color:#666;">{row['Fecha'].strftime('%d/%m/%Y')}</td>
                    <td><span class="ticker-tag">{row['Ticker']}</span></td>
                    <td>${row['Precio Compra']:,.2f}</td>
                    <td>${row['Precio Actual']:,.2f}</td>
                    <td style="color:{pnl_color}; font-weight:bold;">{pnl_sign}{pnl:.2f}%</td>
                    <td style="color:#666; font-size:0.8rem;">{comment}</td>
                </tr>"""

            st.markdown(f"""
            <div class="terminal-box" style="padding:10px 20px; max-height:400px; overflow-y:auto;">
                <table class="terminal-table">
                    <thead><tr>
                        <th>Fecha</th><th>Ticker</th><th>P. Compra</th>
                        <th>P. Salida</th><th>P&L %</th><th>Comentarios</th>
                    </tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="phase-box gold"><p>Sin operaciones cerradas en el historial.</p></div>',
                        unsafe_allow_html=True)

        # ── ESTRATEGIA DE CARTERA ─────────────────────────────────────────
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h2>04 // ESTRATEGIA DE ASIGNACIÓN</h2>", unsafe_allow_html=True)
        st.markdown(
            """<div style="font-family:'VT323',monospace; color:#666; font-size:0.85rem;
                letter-spacing:2px; margin-bottom:20px;">
                [ALLOCATION_FRAMEWORK_v1.0 // REFERENCIA ESTRATÉGICA — AJUSTAR SEGÚN PERFIL]
            </div>""",
            unsafe_allow_html=True
        )

        # Donut chart + legend side by side
        buckets = [
            ("SPXL Strategy", 40, "#00ffad", "#1a6b4a",
             "Núcleo de la cartera. Exposición apalancada 3x al S&P 500 mediante SPXL. "
             "Estrategia de largo plazo orientada a capturar la tendencia estructural alcista "
             "del índice. Requiere horizonte amplio y tolerancia a drawdowns pronunciados."),
            ("RSU Stocks",    30, "#00d9ff", "#1a4a6b",
             "Acciones recibidas como compensación RSU (Restricted Stock Units). "
             "Se mantienen o liquidan según criterios fiscales y de concentración. "
             "El objetivo es reducir exposición a un solo empleador diversificando "
             "progresivamente hacia otros activos del portfolio."),
            ("Cryptos",       20, "#ff9800", "#4a3a1a",
             "Asignación especulativa de alta volatilidad. Exposición principalmente "
             "a BTC y ETH como activos de reserva digital, con posiciones menores "
             "en altcoins selectivas. Alta asimetría riesgo/recompensa. Gestión "
             "activa de posición según ciclo de mercado."),
            ("Beta Stocks",   10, "#b044ff", "#2a1a4a",
             "Selección táctica de acciones de alto beta para capturar movimientos "
             "de mercado amplificados. Posiciones más activas y de menor duración. "
             "Complementan el núcleo aportando alfa potencial en fases de expansión."),
        ]

        labels = [b[0] for b in buckets]
        values = [b[1] for b in buckets]
        colors = [b[2] for b in buckets]

        fig = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(
                colors=colors,
                line=dict(color="#0c0e12", width=3)
            ),
            textinfo="percent",
            textfont=dict(family="VT323, monospace", size=18, color="#0c0e12"),
            hovertemplate="<b>%{label}</b><br>%{value}%<extra></extra>",
            sort=False,
            direction="clockwise",
        ))
        fig.add_annotation(
            text="RSU<br>PORTFOLIO",
            x=0.5, y=0.5,
            font=dict(family="VT323, monospace", size=20, color="#00ffad"),
            showarrow=False
        )
        fig.update_layout(
            paper_bgcolor="#0c0e12",
            plot_bgcolor="#0c0e12",
            margin=dict(t=20, b=20, l=20, r=20),
            height=320,
            showlegend=False,
            font=dict(family="VT323, monospace", color="#ccc"),
        )

        col_chart, col_legend = st.columns([1, 1])
        with col_chart:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                """<div style="text-align:center; font-family:'VT323',monospace;
                    color:#444; font-size:0.8rem; margin-top:-10px; letter-spacing:2px;">
                    Estrategia RSU · Asignación objetivo</div>""",
                unsafe_allow_html=True
            )

        with col_legend:
            for (name, pct, color, border, desc) in buckets:
                st.markdown(
                    f'''<div style="display:flex; align-items:flex-start; gap:12px;
                        padding:10px 0; border-bottom:1px solid #1a1e26;">
                        <div style="min-width:12px; height:12px; background:{color};
                            border-radius:2px; margin-top:4px;"></div>
                        <div>
                            <span style="font-family:'VT323',monospace; color:{color};
                                font-size:1rem; letter-spacing:1px;">{name}</span>
                            <span style="font-family:'VT323',monospace; color:{color};
                                font-size:1.1rem; margin-left:10px;">{pct}%</span>
                            <p style="font-size:0.78rem; color:#666 !important;
                                margin:4px 0 0 0; line-height:1.5;">{desc}</p>
                        </div>
                    </div>''',
                    unsafe_allow_html=True
                )

        st.markdown(
            """<div style="margin-top:20px; padding:14px 18px; border:1px solid #1a1e26;
                border-radius:6px; font-family:'Courier New',monospace; font-size:0.78rem;
                color:#555; line-height:1.7;">
                &#9888; Los porcentajes son orientativos y deben ajustarse según perfil de riesgo,
                horizonte temporal y circunstancias fiscales individuales. Rebalancear cuando algún
                bucket se desvíe más de ±5% del objetivo. Este framework no constituye asesoramiento financiero.
            </div>""",
            unsafe_allow_html=True
        )

        # ── FOOTER ───────────────────────────────────────────────────────
        st.markdown(f"""
        <hr>
        <div style="text-align:center; padding:20px;">
            <p style="font-family:'VT323',monospace; color:#444; font-size:0.9rem;">
                [END OF TRANSMISSION // CARTERA_RSU_v3.0]<br>
                [STATUS: LIVE] [DATA: GOOGLE SHEETS FEED] [CACHE TTL: 300s]<br>
                [LAST FETCH: {last_update}]
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


