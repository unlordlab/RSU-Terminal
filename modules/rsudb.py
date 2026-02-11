# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def load_css():
    st.markdown("""
    <style>
        .stApp { background: #0c0e12; }
        h1, h2, h3 { color: white !important; font-family: 'Segoe UI', sans-serif; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; background: #0c0e12; padding: 10px; border-radius: 10px; }
        .stTabs [data-baseweb="tab"] { background: #11141a; color: #888; border: 1px solid #1a1e26; border-radius: 8px; padding: 10px 20px; font-weight: 600; }
        .stTabs [aria-selected="true"] { background: #1a1e26; color: #00ffad; border: 1px solid #00ffad; box-shadow: 0 0 10px rgba(0, 255, 173, 0.3); }
        .dataframe { background: #11141a !important; border: 1px solid #1a1e26 !important; border-radius: 10px !important; }
        .dataframe th { background: #0c0e12 !important; color: #00ffad !important; font-weight: bold !important; border-bottom: 2px solid #1a1e26 !important; padding: 12px !important; }
        .dataframe td { background: #11141a !important; color: #ccc !important; border-bottom: 1px solid #1a1e26 !important; padding: 10px !important; }
        .dataframe tr:hover td { background: #1a1e26 !important; }
        .stat-card { background: linear-gradient(135deg, #11141a 0%, #0c0e12 100%); border: 1px solid #1a1e26; border-radius: 12px; padding: 20px; text-align: center; }
        .stat-value { font-size: 32px; font-weight: bold; margin: 10px 0; }
        .stat-label { color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
        .filter-container { background: #11141a; border: 1px solid #1a1e26; border-radius: 10px; padding: 15px; margin-bottom: 20px; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
        .live-indicator { animation: pulse 2s infinite; color: #00ffad; }
    </style>
    """, unsafe_allow_html=True)

def generate_mock_options_flow():
    tickers = ['AAPL', 'TSLA', 'NVDA', 'AMD', 'META', 'AMZN', 'GOOGL', 'MSFT', 
               'NFLX', 'CRM', 'BABA', 'UBER', 'COIN', 'PLTR', 'ARKK', 'IWM',
               'SPY', 'QQQ', 'VIX', 'GLD', 'SLV', 'TLT', 'HYG', 'LQD', 'CVNA',
               'CRWV', 'COP', 'GSHR', 'CIBR', 'CG', 'CELH', 'BIIB', 'AZN', 'APP',
               'APLD', 'AMPL', 'ALAB']
    data = []
    base_date = datetime.now()
    for ticker in tickers:
        num_trades = np.random.randint(1, 4)
        for _ in range(num_trades):
            flow_types = ['CALL_BOUGHT', 'CALL_SOLD', 'PUT_BOUGHT', 'PUT_SOLD']
            flow_type = np.random.choice(flow_types, p=[0.35, 0.15, 0.35, 0.15])
            base_price = np.random.uniform(50, 500)
            strike_offset = np.random.uniform(-0.2, 0.5)
            strike = round(base_price * (1 + strike_offset), 2)
            days_to_exp = np.random.choice([2, 7, 14, 21, 30, 60, 90, 180, 365])
            exp_date = base_date + timedelta(days=int(days_to_exp))
            rand = np.random.random()
            if rand < 0.4:
                premium = np.random.uniform(50, 300) * 1000
            elif rand < 0.7:
                premium = np.random.uniform(300, 1000) * 1000
            elif rand < 0.9:
                premium = np.random.uniform(1, 5) * 1000000
            else:
                premium = np.random.uniform(5, 25) * 1000000
            volume = int(premium / (strike * 0.5))
            open_interest = int(volume * np.random.uniform(0.3, 4))
            is_sweep = np.random.random() < 0.25
            is_block = premium > 1000000
            data.append({
                'ticker': ticker, 'flow_type': flow_type, 'strike': strike,
                'expiration': exp_date.strftime('%m/%d/%y'), 'days_to_exp': days_to_exp,
                'premium': premium, 'premium_formatted': format_premium(premium),
                'volume': volume, 'open_interest': open_interest,
                'volume_oi_ratio': round(volume / open_interest, 2) if open_interest > 0 else 0,
                'is_sweep': is_sweep, 'is_block': is_block,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'sentiment': 'BULLISH' if flow_type in ['CALL_BOUGHT', 'PUT_SOLD'] else 'BEARISH'
            })
    return pd.DataFrame(data)

def format_premium(premium):
    if premium >= 1000000:
        return f"{premium/1000000:.1f}M"
    elif premium >= 1000:
        return f"{premium/1000:.1f}K"
    return f"{premium:.0f}"

def get_flow_label(flow_type):
    labels = {'CALL_BOUGHT': 'Call Buy', 'CALL_SOLD': 'Call Sell', 'PUT_BOUGHT': 'Put Buy', 'PUT_SOLD': 'Put Sell'}
    return labels.get(flow_type, flow_type)

def render_header():
    st.markdown("""
    <div style="text-align:center; margin-bottom:30px; padding:20px;">
        <h1 style="font-size:2.5rem; margin-bottom:10px; color:#00ffad;">⚡ RSU FLOW DATABASE</h1>
        <p style="color:#888; font-size:1.1rem; max-width:600px; margin:0 auto;">
            Detector de Flujo Inusual en Opciones · Smart Money Tracker
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_stats_cards(df):
    total_premium = df['premium'].sum()
    bullish_flow = df[df['sentiment'] == 'BULLISH']['premium'].sum()
    bearish_flow = df[df['sentiment'] == 'BEARISH']['premium'].sum()
    call_premium = df[df['flow_type'].isin(['CALL_BOUGHT', 'CALL_SOLD'])]['premium'].sum()
    put_premium = df[df['flow_type'].isin(['PUT_BOUGHT', 'PUT_SOLD'])]['premium'].sum()
    pc_ratio = put_premium / call_premium if call_premium > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Premium</div>
            <div class="stat-value" style="color:#00ffad;">${format_premium(total_premium)}</div>
            <div style="color:#666; font-size:11px;">Última hora</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Bullish Flow</div>
            <div class="stat-value" style="color:#00ffad;">${format_premium(bullish_flow)}</div>
            <div style="color:#666; font-size:11px;">{bullish_flow/total_premium*100:.1f}% del total</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Bearish Flow</div>
            <div class="stat-value" style="color:#f23645;">${format_premium(bearish_flow)}</div>
            <div style="color:#666; font-size:11px;">{bearish_flow/total_premium*100:.1f}% del total</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        color = "#00ffad" if pc_ratio < 0.7 else "#f23645" if pc_ratio > 1.3 else "#ff9800"
        sentiment = "Greed" if pc_ratio < 0.7 else "Fear" if pc_ratio > 1.3 else "Neutral"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Put/Call Ratio</div>
            <div class="stat-value" style="color:{color};">{pc_ratio:.2f}</div>
            <div style="color:#666; font-size:11px;">{sentiment}</div>
        </div>
        """, unsafe_allow_html=True)

def render_filters():
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        min_premium = st.selectbox("Min Premium", ["All", ">$100K", ">$500K", ">$1M", ">$5M"], index=1)
    with col2:
        exp_filter = st.selectbox("Expiración", ["All", "< 7 days (Weekly)", "7-30 days", "30-90 days", "> 90 days (LEAPS)"])
    with col3:
        unusual_only = st.toggle("Solo Inusual", value=True, help="Filtra solo trades con volumen > OI o sweeps")
    with col4:
        refresh = st.button("🔄 Actualizar", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    return {'min_premium': min_premium, 'exp_filter': exp_filter, 'unusual_only': unusual_only, 'refresh': refresh}

def apply_filters(df, filters):
    filtered = df.copy()
    if filters['min_premium'] == ">$100K":
        filtered = filtered[filtered['premium'] >= 100000]
    elif filters['min_premium'] == ">$500K":
        filtered = filtered[filtered['premium'] >= 500000]
    elif filters['min_premium'] == ">$1M":
        filtered = filtered[filtered['premium'] >= 1000000]
    elif filters['min_premium'] == ">$5M":
        filtered = filtered[filtered['premium'] >= 5000000]
    if filters['exp_filter'] == "< 7 days (Weekly)":
        filtered = filtered[filtered['days_to_exp'] < 7]
    elif filters['exp_filter'] == "7-30 days":
        filtered = filtered[(filtered['days_to_exp'] >= 7) & (filtered['days_to_exp'] <= 30)]
    elif filters['exp_filter'] == "30-90 days":
        filtered = filtered[(filtered['days_to_exp'] > 30) & (filtered['days_to_exp'] <= 90)]
    elif filters['exp_filter'] == "> 90 days (LEAPS)":
        filtered = filtered[filtered['days_to_exp'] > 90]
    if filters['unusual_only']:
        filtered = filtered[(filtered['volume_oi_ratio'] > 1) | (filtered['is_sweep']) | (filtered['is_block'])]
    return filtered

def render_flow_table(df, flow_type):
    type_map = {'Calls Bought': 'CALL_BOUGHT', 'Calls Sold': 'CALL_SOLD', 'Puts Bought': 'PUT_BOUGHT', 'Puts Sold': 'PUT_SOLD'}
    filtered = df[df['flow_type'] == type_map.get(flow_type, flow_type)].copy()
    if filtered.empty:
        st.info(f"No hay datos de {flow_type} con los filtros actuales")
        return
    filtered = filtered.sort_values('premium', ascending=False)
    display_data = []
    for _, row in filtered.iterrows():
        distance = ((row['strike'] / 150) - 1) * 100 if row['strike'] > 0 else 0
        display_data.append({
            'Ticker': row['ticker'],
            'Strike': f"{row['strike']:.2f} ({distance:+.0f}%)",
            'Exp': row['expiration'],
            'Premium': row['premium_formatted'],
            'Details': f"{'🧹 ' if row['is_sweep'] else ''}{'💎 ' if row['is_block'] else ''}{get_flow_label(row['flow_type'])}",
            'Vol/OI': f"{row['volume_oi_ratio']:.1f}x",
            'Time': row['timestamp']
        })
    display_df = pd.DataFrame(display_data)
    st.dataframe(display_df, use_container_width=True, height=500, hide_index=True)
    total_type = filtered['premium'].sum()
    count = len(filtered)
    avg_premium = filtered['premium'].mean()
    cols = st.columns(3)
    with cols[0]:
        st.metric("Total Premium", f"${format_premium(total_type)}")
    with cols[1]:
        st.metric("Trades", count)
    with cols[2]:
        st.metric("Promedio", f"${format_premium(avg_premium)}")

def render_alerts_section(df):
    st.markdown("""
    <div style="background: linear-gradient(135deg, #11141a 0%, #0c0e12 100%); border: 1px solid #1a1e26; border-radius: 12px; padding: 20px; margin: 20px 0;">
        <h3 style="color:#00ffad; margin-bottom:15px;">🔥 Alertas Destacadas</h3>
    """, unsafe_allow_html=True)
    alerts = df[(df['premium'] > 1000000) | ((df['volume_oi_ratio'] > 5) & (df['premium'] > 500000)) | (df['is_sweep'] & df['is_block'])].head(5)
    if not alerts.empty:
        for _, alert in alerts.iterrows():
            sentiment_color = '#00ffad' if alert['sentiment'] == 'BULLISH' else '#f23645'
            icon = '🚀' if alert['sentiment'] == 'BULLISH' else '🔻'
            st.markdown(f"""
            <div style="background: #0c0e12; border-left: 3px solid {sentiment_color}; padding: 12px; margin: 8px 0; border-radius: 0 8px 8px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="color:{sentiment_color}; font-weight:bold; font-size:16px;">{icon} {alert['ticker']} ${alert['strike']:.2f} {get_flow_label(alert['flow_type'])}</span>
                        <span style="color:#888; margin-left:10px; font-size:12px;">Exp: {alert['expiration']}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#00ffad; font-weight:bold; font-size:18px;">${alert['premium_formatted']}</div>
                        <div style="color:#666; font-size:11px;">Vol/OI: {alert['volume_oi_ratio']:.1f}x {'🧹 Sweep' if alert['is_sweep'] else ''}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#666;'>No hay alertas destacadas</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render():
    load_css()
    render_header()
    st.markdown(f"""
    <div style="text-align:center; color:#555; font-size:12px; margin-bottom:20px; font-family:'Courier New', monospace;">
        <span class="live-indicator">●</span> LIVE DATA · Last Update: {datetime.now().strftime('%H:%M:%S')} EST
    </div>
    """, unsafe_allow_html=True)

    if 'options_data' not in st.session_state or st.session_state.get('refresh_data', False):
        st.session_state.options_data = generate_mock_options_flow()
        st.session_state.refresh_data = False

    df = st.session_state.options_data
    render_stats_cards(df)
    st.markdown("<br>", unsafe_allow_html=True)

    filters = render_filters()
    if filters['refresh']:
        st.session_state.refresh_data = True
        st.rerun()

    filtered_df = apply_filters(df, filters)
    render_alerts_section(filtered_df)

    tab1, tab2, tab3, tab4 = st.tabs(["🟢 Calls Bought", "🟠 Calls Sold", "🔴 Puts Bought", "🔵 Puts Sold"])
    with tab1:
        render_flow_table(filtered_df, 'Calls Bought')
    with tab2:
        render_flow_table(filtered_df, 'Calls Sold')
    with tab3:
        render_flow_table(filtered_df, 'Puts Bought')
    with tab4:
        render_flow_table(filtered_df, 'Puts Sold')

    with st.expander("📚 CÓMO INTERPRETAR EL FLUJO DE OPCIONES", expanded=False):
        st.markdown("""
        <div style="background:#0c0e12; padding:20px; border-radius:10px; border:1px solid #1a1e26;">
            <h4 style="color:#00ffad;">🟢 Calls Bought (Señal Alcista)</h4>
            <p style="color:#aaa; font-size:13px;">Compra de calls indica expectativa de subida. Volumen > OI sugiere nueva posición.</p>
            <h4 style="color:#f23645;">🔴 Puts Bought (Señal Bajista)</h4>
            <p style="color:#aaa; font-size:13px;">Compra de puts indica protección o apuesta a la baja.</p>
            <h4 style="color:#ff9800;">🟠 Calls Sold (Neutral/Bajista)</h4>
            <p style="color:#aaa; font-size:13px;">Ventas de calls: cierre de largos, apertura de cortos, o covered calls.</p>
            <h4 style="color:#2196f3;">🔵 Puts Sold (Neutral/Alcista)</h4>
            <p style="color:#aaa; font-size:13px;">Ventas de puts: cierre de cortos, cash secured puts (bullish), o premium collection.</p>
            <div style="background:#1a1e26; padding:15px; border-radius:8px; margin-top:15px;">
                <h5 style="color:#ff9800; margin-top:0;">⚠️ Señales de Confirmación Fuerte</h5>
                <ul style="color:#aaa; font-size:12px; margin:0;">
                    <li><strong>Sweeps:</strong> Múltiples exchanges, ejecución agresiva</li>
                    <li><strong>Size > OI:</strong> Nueva posición, no rotación</li>
                    <li><strong>Premium > $1M:</strong> Participación institucional</li>
                    <li><strong>0DTE/7DTE:</strong> Evento catalizador inminente</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
