# modules/spxl_strategy.py
import streamlit as st
import pandas as pd
import yfinance as yf
import streamlit.components.v1 as components
import os
from datetime import datetime

def render():
    # CSS Global consistente con market.py
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif; }
        
        .main-header {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            padding: 30px;
            border-radius: 15px;
            border: 1px solid #2a3f5f;
            margin-bottom: 25px;
            text-align: center;
        }
        
        .main-title {
            color: #00ffad;
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 0 20px rgba(0, 255, 173, 0.3);
        }
        
        .sub-title {
            color: #888;
            font-size: 0.9rem;
            margin-top: 10px;
            font-weight: 400;
        }
        
        .metric-card {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            border-color: #2a3f5f;
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: white;
            margin: 10px 0;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .positive { color: #00ffad; }
        .negative { color: #f23645; }
        .warning { color: #ff9800; }
        
        .section-container {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        
        .section-header {
            background: #0c0e12;
            padding: 15px 20px;
            border-bottom: 1px solid #1a1e26;
            font-weight: 600;
            color: white;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-content {
            padding: 20px;
        }
        
        .phase-card {
            background: #0c0e12;
            border: 2px solid #1a1e26;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .phase-card.active {
            border-color: #00ffad;
            background: linear-gradient(135deg, #0c0e12 0%, #00ffad11 100%);
            box-shadow: 0 0 20px rgba(0, 255, 173, 0.2);
        }
        
        .phase-card.pending {
            border-color: #2a3f5f;
            opacity: 0.6;
        }
        
        .phase-card.completed {
            border-color: #4caf50;
            opacity: 0.5;
        }
        
        .phase-number {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #1a1e26;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
            color: #888;
        }
        
        .phase-card.active .phase-number { 
            background: #00ffad; 
            color: #0c0e12; 
        }
        
        .phase-card.completed .phase-number { 
            background: #4caf50; 
            color: white; 
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #0c0e12;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
            border: 1px solid #1a1e26;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ffad 0%, #00ffad88 100%);
            transition: width 0.5s ease;
        }
        
        .alert-box {
            padding: 15px 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid;
            font-weight: 500;
        }
        
        .alert-buy {
            background: rgba(0, 255, 173, 0.1);
            border-color: #00ffad;
            color: #00ffad;
        }
        
        .alert-sell {
            background: rgba(242, 54, 69, 0.1);
            border-color: #f23645;
            color: #f23645;
        }
        
        .alert-warning {
            background: rgba(255, 152, 0, 0.1);
            border-color: #ff9800;
            color: #ff9800;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .info-item {
            background: #0c0e12;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #1a1e26;
        }
        
        .info-label {
            color: #666;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        .info-value {
            color: white;
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .chart-container {
            background: #0c0e12;
            border-radius: 10px;
            padding: 15px;
            border: 1px solid #1a1e26;
        }
        
        .cds-gauge {
            width: 100%;
            height: 30px;
            background: linear-gradient(90deg, #00ffad 0%, #ff9800 50%, #f23645 100%);
            border-radius: 15px;
            position: relative;
            margin: 20px 0;
            border: 2px solid #1a1e26;
        }
        
        .cds-marker {
            position: absolute;
            top: -10px;
            width: 4px;
            height: 50px;
            background: white;
            border: 2px solid #fff;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            transition: left 0.5s ease;
        }
        
        .cds-labels {
            display: flex;
            justify-content: space-between;
            color: #888;
            font-size: 0.75rem;
            margin-top: 5px;
        }
        
        .strategy-philosophy {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border-left: 4px solid #00ffad;
            padding: 20px;
            border-radius: 0 10px 10px 0;
            margin: 15px 0;
        }
        
        .rule-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin: 12px 0;
            padding: 12px;
            background: #0c0e12;
            border-radius: 8px;
            border: 1px solid #1a1e26;
        }
        
        .rule-icon {
            width: 24px;
            height: 24px;
            background: #00ffad22;
            color: #00ffad;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.8rem;
            flex-shrink: 0;
        }
        
        .highlight {
            color: #00ffad;
            font-weight: 600;
        }
        
        .danger { color: #f23645; font-weight: 600; }
        .success { color: #00ffad; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

    # === HEADER PRINCIPAL ===
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">📈 ESTRATEGIA SPXL</h1>
        <p class="sub-title">Redistribution Strategy Research Unit (RSU) - Trading System v2.0</p>
    </div>
    """, unsafe_allow_html=True)

    # === OBTENCION DE DATOS ===
    @st.cache_data(ttl=300)
    def get_market_data():
        try:
            spxl = yf.Ticker("SPXL")
            spxl_hist = spxl.history(period="1y")
            spx = yf.Ticker("^GSPC")
            spx_hist = spx.history(period="2d")
            
            if not spxl_hist.empty:
                current_price = spxl_hist['Close'].iloc[-1]
                prev_price = spxl_hist['Close'].iloc[-2]
                yearly_high = spxl_hist['High'].max()
                yearly_low = spxl_hist['Low'].min()
                
                change_pct = ((current_price - prev_price) / prev_price) * 100
                drawdown = ((current_price - yearly_high) / yearly_high) * 100
                
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

    # === METRICAS ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        color = "positive" if data['spxl_change'] >= 0 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">SPXL Actual</div>
            <div class="metric-value">${data['spxl_price']:.2f}</div>
            <div class="{color}" style="font-size: 1.1rem; font-weight: 600;">{data['spxl_change']:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        color2 = "positive" if data['spx_change'] >= 0 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">S&P 500</div>
            <div class="metric-value">{data['spx_price']:,.2f}</div>
            <div class="{color2}" style="font-size: 1.1rem; font-weight: 600;">{data['spx_change']:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        dd_color = "positive" if data['drawdown'] > -10 else "warning" if data['drawdown'] > -15 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Drawdown desde Max</div>
            <div class="metric-value {dd_color}">{data['drawdown']:.2f}%</div>
            <div style="color: #666; font-size: 0.8rem;">Max: ${data['spxl_high']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        current_dd = abs(data['drawdown'])
        if current_dd < 15:
            phase, phase_color = "ESPERANDO", "#888"
        elif current_dd < 25:
            phase, phase_color = "FASE 1 ACTIVA", "#00ffad"
        elif current_dd < 32:
            phase, phase_color = "FASE 2 ACTIVA", "#00ffad"
        elif current_dd < 39:
            phase, phase_color = "FASE 3 ACTIVA", "#00ffad"
        else:
            phase, phase_color = "FASE 4 ACTIVA", "#f23645"
        
        st.markdown(f"""
        <div class="metric-card" style="border-color: {phase_color};">
            <div class="metric-label">Estado Estrategia</div>
            <div class="metric-value" style="color: {phase_color}; font-size: 1.3rem;">{phase}</div>
            <div style="color: #666; font-size: 0.8rem;">Basado en caida actual</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # === TABS ===
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📖 Estrategia", "💰 Calculadora", "⚠️ Riesgo"])

    with tab1:
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown('<div class="section-container"><div class="section-header">📈 Grafico SPXL con Niveles</div><div class="section-content">', unsafe_allow_html=True)
            
            levels = data['buy_levels']
            chart_html = f"""
            <div class="tradingview-widget-container">
              <div id="tradingview_spxl"></div>
              <script src="https://s3.tradingview.com/tv.js"></script>
              <script>
              new TradingView.widget({{
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
                "overrides": {{
                    "paneProperties.background": "#0c0e12",
                    "paneProperties.vertGridProperties.color": "#1a1e26",
                    "paneProperties.horzGridProperties.color": "#1a1e26"
                }}
              }});
              </script>
            </div>
            """
            components.html(chart_html, height=520)
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        with col_right:
            st.markdown('<div class="section-container"><div class="section-header">🔔 Senales</div><div class="section-content">', unsafe_allow_html=True)
            
            current_price = data['spxl_price']
            levels = data['buy_levels']
            
            phases = [
                ("Fase 1: Compra Inicial", levels['phase1'], 0.20, 15, current_price <= levels['phase1']),
                ("Fase 2: Segunda Entrada", levels['phase2'], 0.15, 10, current_price <= levels['phase2']),
                ("Fase 3: Tercera Entrada", levels['phase3'], 0.20, 7, current_price <= levels['phase3']),
                ("Fase 4: Entrada Final", levels['phase4'], 0.20, 10, current_price <= levels['phase4'])
            ]
            
            for i, (name, price, allocation, drop, is_active) in enumerate(phases, 1):
                if is_active:
                    status_class, status_text = "active", "🎯 ACTIVA"
                elif current_price < price:
                    status_class, status_text = "completed", "✓ COMPLETADA"
                else:
                    status_class, status_text = "pending", "⏳ PENDIENTE"
                
                distance = ((current_price - price) / price) * 100
                distance_text = f"{distance:+.1f}%" if distance > 0 else f"{distance:.1f}%"
                distance_color = "positive" if distance <= 0 else "negative"
                
                st.markdown(f"""
                <div class="phase-card {status_class}">
                    <div class="phase-number">{i}</div>
                    <div style="font-weight: 600; color: white; margin-bottom: 5px;">{name}</div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #00ffad; font-size: 1.2rem; font-weight: 700;">${price:.2f}</span>
                        <span style="color: #888; font-size: 0.8rem;">{status_text}</span>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.8rem;">
                        <span style="color: #666;">Alloc: {allocation:.0%}</span> | 
                        <span class="{distance_color}">Dist: {distance_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if current_price <= levels['phase4']:
                st.markdown('<div class="alert-box alert-buy pulse"><strong>🚨 COMPRA MAXIMA</strong><br>Todas las fases disponibles.</div>', unsafe_allow_html=True)
            elif current_price <= levels['phase1']:
                st.markdown('<div class="alert-box alert-buy"><strong>✅ COMPRA ACTIVA</strong></div>', unsafe_allow_html=True)
            else:
                distance_to_p1 = ((current_price - levels['phase1']) / levels['phase1']) * 100
                st.markdown(f'<div class="alert-box alert-warning"><strong>⏳ ESPERA</strong><br>Faltan {distance_to_p1:.1f}% para comprar.</div>', unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-container"><div class="section-header">🎯 Filosofia</div><div class="section-content">', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="strategy-philosophy">
            <h3 style="color: #00ffad; margin-top: 0;">Premisa Fundamental</h3>
            <p style="color: #ccc;">Estrategia basada en que el S&P 500 mantiene <span class="highlight">macro tendencia alcista</span> a largo plazo.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <h3 style="color: white;">📋 Reglas de Entrada</h3>
        <div class="rule-item"><div class="rule-icon">1</div><div><strong>Primera Caida (-15%)</strong><br><span style="color: #888;">Invertir 20% del capital</span></div></div>
        <div class="rule-item"><div class="rule-icon">2</div><div><strong>Segunda Caida (-10%)</strong><br><span style="color: #888;">Invertir 15% del capital</span></div></div>
        <div class="rule-item"><div class="rule-icon">3</div><div><strong>Tercera Caida (-7%)</strong><br><span style="color: #888;">Invertir 20% del capital</span></div></div>
        <div class="rule-item"><div class="rule-icon">4</div><div><strong>Cuarta Caida (-10%)</strong><br><span style="color: #888;">Invertir 20% del capital (75% total)</span></div></div>
        
        <h3 style="color: white; margin-top: 20px;">🎯 Regla de Salida</h3>
        <div class="rule-item" style="border-color: #f23645;"><div class="rule-icon" style="background: #f2364522; color: #f23645;">$</div><div><strong>Take Profit (+20%)</strong><br><span style="color: #888;">Vender todo al alcanzar +20% sobre precio medio</span></div></div>
        """, unsafe_allow_html=True)
        
        pdf_path = "assets/SPXL.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button("📄 Descargar Estrategia PDF", pdf_bytes, "SPXL.pdf", "application/pdf", use_container_width=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="section-container"><div class="section-header">💰 Calculadora</div><div class="section-content">', unsafe_allow_html=True)
        
        col_calc1, col_calc2 = st.columns(2)
        
        with col_calc1:
            capital_total = st.number_input("Capital Total ($):", min_value=1000, value=10000, step=1000)
            tiene_posicion = st.checkbox("Tienes posicion abierta?")
            if tiene_posicion:
                precio_medio = st.number_input("Precio medio ($):", min_value=0.0, value=0.0, step=0.1)
                cantidad_acciones = st.number_input("Acciones:", min_value=0, value=0, step=1)
            else:
                precio_medio, cantidad_acciones = 0, 0
        
        with col_calc2:
            allocations = [("Fase 1", 0.20, levels['phase1']), ("Fase 2", 0.15, levels['phase2']), 
                          ("Fase 3", 0.20, levels['phase3']), ("Fase 4", 0.20, levels['phase4'])]
            
            total_invertido = 0
            for fase, pct, precio in allocations:
                monto = capital_total * pct
                total_invertido += monto
                st.markdown(f"""
                <div style="background: #0c0e12; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #00ffad;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: white;">{fase}</span>
                        <span style="color: #00ffad; font-weight: bold;">${monto:,.2f}</span>
                    </div>
                    <div style="color: #666; font-size: 0.8rem;">@${precio:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            reserva = capital_total * 0.25
            st.markdown(f"""
            <div style="background: #ff980022; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #ff9800;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #888;">Reserva</span>
                    <span style="color: #ff9800; font-weight: bold;">${reserva:,.2f}</span>
                </div>
            </div>
            <div style="background: #00ffad11; padding: 15px; border-radius: 8px; margin-top: 10px; border: 1px solid #00ffad;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: white; font-weight: 600;">Total a invertir:</span>
                    <span style="color: #00ffad; font-size: 1.2rem; font-weight: bold;">${total_invertido:,.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if tiene_posicion and precio_medio > 0:
            st.markdown("---")
            valor_actual = cantidad_acciones * data['spxl_price']
            costo_total = cantidad_acciones * precio_medio
            pnl = valor_actual - costo_total
            pnl_pct = (pnl / costo_total) * 100 if costo_total > 0 else 0
            target_price = precio_medio * 1.20
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Valor Actual", f"${valor_actual:,.2f}", f"{pnl_pct:+.2f}%")
            c2.metric("Objetivo Venta", f"${target_price:.2f}", "+20%")
            c3.metric("Distancia", f"{((target_price - data['spxl_price']) / data['spxl_price'] * 100):.2f}%")
            
            if data['spxl_price'] >= target_price:
                st.balloons()
                st.markdown('<div class="alert-box alert-sell pulse"><strong>🎯 OBJETIVO ALCANZADO!</strong></div>', unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="section-container"><div class="section-header">⚠️ Riesgo Sistemico (CDS)</div><div class="section-content">', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #0c0e12; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <strong style="color: white;">Indice: BAMLH0A0HYM2</strong><br>
            <span style="color: #666;">ICE BofA US High Yield Index Option-Adjusted Spread</span>
        </div>
        
        <div class="cds-gauge">
            <div class="cds-marker" style="left: 30%;"></div>
        </div>
        <div class="cds-labels">
            <span>Normal</span>
            <span>Atencion</span>
            <span>Peligro</span>
            <span style="color: #f23645; font-weight: bold;">CRISIS (>10.7)</span>
        </div>
        """, unsafe_allow_html=True)
        
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
            "container_id": "tradingview_cds"
          });
          </script>
        </div>
        """
        components.html(cds_chart, height=420)
        
        st.markdown('<div class="alert-box alert-warning"><strong>⚠️ STOP DE CRISIS:</strong> Si CDS > 10.7, DETENER TODAS LAS COMPRAS inmediatamente.</div>', unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div style="text-align: center; color: #555; font-size: 0.8rem;"><p>RSU - Redistribution Strategy Research Unit</p></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
