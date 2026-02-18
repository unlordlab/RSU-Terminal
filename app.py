
# modules/btc_stratum.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def render():
    """
    Renderiza la sección BTC STRATUM - Estrategia de trading para Bitcoin
    con estética hacker/dark theme acorde al resto de la plataforma RSU.
    """
    
    # Título principal con estética RSU
    st.markdown("""
        <h1 style='
            color: #00ffad;
            font-family: "Courier New", monospace;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            text-shadow: 0 0 10px rgba(0, 255, 173, 0.3);
        '>
            ₿ BTC STRATUM
        </h1>
        <p style='
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 2rem;
            border-left: 2px solid #00ffad;
            padding-left: 10px;
        '>
            Protocolo de análisis estratigráfico para Bitcoin. 
            Layers de liquidez, zonas de acumulación y distribución.
        </p>
    """, unsafe_allow_html=True)
    
    # Layout de columnas
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Precio actual simulado (reemplazar con datos reales)
        st.markdown("""
            <div style='
                background: linear-gradient(135deg, #11141a 0%, #0c0e12 100%);
                border: 1px solid #1a1e26;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            '>
                <div style='color: #666; font-size: 0.7rem; letter-spacing: 1px;'>BTC/USD</div>
                <div style='
                    color: #00ffad;
                    font-size: 1.8rem;
                    font-family: "Courier New", monospace;
                    font-weight: bold;
                '>
                    $67,245.00 <span style='color: #f23645; font-size: 0.9rem;'>▼ 2.4%</span>
                </div>
                <div style='color: #555; font-size: 0.65rem; margin-top: 5px;'>
                    Vol: 24.5B | Cap: 1.32T
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='
                background: rgba(0, 255, 173, 0.05);
                border: 1px solid rgba(0, 255, 173, 0.2);
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            '>
                <div style='color: #666; font-size: 0.65rem;'>FEAR & GREED</div>
                <div style='
                    color: #00ffad;
                    font-size: 1.4rem;
                    font-weight: bold;
                '>65</div>
                <div style='color: #888; font-size: 0.6rem;'>GREED</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='
                background: rgba(242, 54, 69, 0.05);
                border: 1px solid rgba(242, 54, 69, 0.2);
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            '>
                <div style='color: #666; font-size: 0.65rem;'>DOMINANCE</div>
                <div style='
                    color: #f23645;
                    font-size: 1.4rem;
                    font-weight: bold;
                '>52.4%</div>
                <div style='color: #888; font-size: 0.6rem;'>BTC.D</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["📊 STRATUM CHART", "🎯 ZONAS CLAVE", "⚙️ CONFIGURACIÓN"])
    
    with tab1:
        st.markdown("#### Análisis Estratigráfico de Bitcoin")
        
        # Placeholder para gráfico de trading
        fig = go.Figure()
        
        # Simulación de datos de precio
        dates = pd.date_range(end=datetime.now(), periods=100, freq='H')
        prices = 65000 + (pd.Series(range(100)).apply(lambda x: x * 50 + (x % 10) * 100))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name='BTC/USD',
            line=dict(color='#00ffad', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 173, 0.1)'
        ))
        
        # Zonas de liquidez (simuladas)
        fig.add_hrect(y0=64000, y1=65000, 
                      fillcolor="rgba(0, 255, 173, 0.2)", 
                      line_width=0, 
                      annotation_text="ZONA DE ACUMULACIÓN", 
                      annotation_position="left",
                      annotation_font_size=10,
                      annotation_font_color="#00ffad")
        
        fig.add_hrect(y0=68000, y1=69000, 
                      fillcolor="rgba(242, 54, 69, 0.2)", 
                      line_width=0,
                      annotation_text="RESISTENCIA CLAVE", 
                      annotation_position="left",
                      annotation_font_size=10,
                      annotation_font_color="#f23645")
        
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='#0c0e12',
            font=dict(family="Courier New, monospace", color="#888"),
            xaxis=dict(gridcolor='#1a1e26', showgrid=True),
            yaxis=dict(gridcolor='#1a1e26', showgrid=True),
            margin=dict(l=40, r=40, t=40, b=40),
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas en grid
        metric_cols = st.columns(4)
        metrics = [
            ("SOPR", "1.02", "neutral"),
            ("MVRV Z-Score", "2.1", "bull"),
            ("NUPL", "0.45", "bull"),
            ("Hash Ribbons", "COMPRA", "signal")
        ]
        
        for i, (label, value, status) in enumerate(metrics):
            color = "#00ffad" if status in ["bull", "signal"] else "#f23645" if status == "bear" else "#888"
            with metric_cols[i]:
                st.markdown(f"""
                    <div style='
                        background: #11141a;
                        border: 1px solid #1a1e26;
                        border-radius: 6px;
                        padding: 10px;
                        text-align: center;
                    '>
                        <div style='color: #555; font-size: 0.6rem;'>{label}</div>
                        <div style='color: {color}; font-size: 1.1rem; font-weight: bold;'>{value}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("#### Zonas de Interés Estratégico")
        
        zones_data = [
            {"rango": "62,000 - 64,000", "tipo": "SOPORTE FUERTE", "prob": "85%", "color": "#00ffad"},
            {"rango": "64,000 - 66,000", "tipo": "ZONA ÓPTIMA", "prob": "72%", "color": "#00ffad"},
            {"rango": "66,000 - 68,000", "tipo": "RESISTENCIA", "prob": "45%", "color": "#f2c94c"},
            {"rango": "68,000 - 70,000", "tipo": "SUPPLY ZONE", "prob": "28%", "color": "#f23645"},
            {"rango": "70,000 - 72,000", "tipo": "TARGET 1", "prob": "15%", "color": "#f23645"},
        ]
        
        for zone in zones_data:
            st.markdown(f"""
                <div style='
                    background: linear-gradient(90deg, {zone["color"]}20 0%, #11141a 100%);
                    border-left: 3px solid {zone["color"]};
                    border-radius: 0 6px 6px 0;
                    padding: 12px 15px;
                    margin-bottom: 8px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                '>
                    <div>
                        <div style='color: {zone["color"]}; font-size: 0.75rem; font-weight: bold;'>
                            {zone["tipo"]}
                        </div>
                        <div style='color: #888; font-size: 0.8rem; font-family: "Courier New", monospace;'>
                            {zone["rango"]}
                        </div>
                    </div>
                    <div style='
                        background: {zone["color"]}30;
                        color: {zone["color"]};
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 0.7rem;
                        font-weight: bold;
                    '>
                        {zone["prob"]}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("#### Parámetros del Algoritmo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.selectbox("Timeframe Principal", ["4H", "1D", "1W"], index=1)
            st.slider("Zona de Compra (%)", 0, 20, 5)
            st.toggle("Alertas de Stratum", value=True)
        
        with col2:
            st.selectbox("Indicador Principal", ["RSI + EMA", "MACD", "Bollinger", "Custom"], index=0)
            st.slider("Zona de Venta (%)", 10, 50, 20)
            st.toggle("Auto-Trading", value=False, disabled=True)
        
        st.markdown("""
            <div style='
                background: rgba(242, 54, 69, 0.05);
                border: 1px solid rgba(242, 54, 69, 0.2);
                border-radius: 6px;
                padding: 10px;
                margin-top: 15px;
                font-size: 0.75rem;
                color: #f23645;
            '>
                ⚠️ <strong>MODO SIMULACIÓN ACTIVO</strong><br>
                Las señales son generadas por algoritmo histórico. No constituyen asesoramiento financiero.
            </div>
        """, unsafe_allow_html=True)
    
    # Footer de la sección
    st.markdown("""
        <div style='
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #1a1e26;
            text-align: center;
            color: #444;
            font-size: 0.65rem;
            font-family: "Courier New", monospace;
        '>
            BTC STRATUM v1.0 | RSU TRADING PLATFORM | Última actualización: {datetime.now().strftime('%H:%M:%S')}
        </div>
    """.format(datetime=datetime), unsafe_allow_html=True)
