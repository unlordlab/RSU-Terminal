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

    # === OBTENCIÓN DE DATOS DE MERCADO ===
    @st.cache_data(ttl=300)
    def get_market_data():
        try:
            # Datos SPXL
            spxl = yf.Ticker("SPXL")
            spxl_hist = spxl.history(period="1y")
            
            # Datos S&P 500
            spx = yf.Ticker("^GSPC")
            spx_hist = spx.history(period="2d")
            
            if not spxl_hist.empty:
                current_price = spxl_hist['Close'].iloc[-1]
                prev_price = spxl_hist['Close'].iloc[-2]
                yearly_high = spxl_hist['High'].max()
                yearly_low = spxl_hist['Low'].min()
                
                change_pct = ((current_price - prev_price) / prev_price) * 100
                drawdown = ((current_price - yearly_high) / yearly_high) * 100
                
                # Calcular niveles de compra según estrategia
                p1 = yearly_high * 0.85  # -15%
                p2 = p1 * 0.90           # -10% adicional
                p3 = p2 * 0.93           # -7% adicional
                p4 = p3 * 0.90           # -10% adicional
                
                return {
                    'spxl_price': current_price,
                    'spxl_change': change_pct,
                    'spxl_high': yearly_high,
                    'spxl_low': yearly_low,
                    'drawdown': drawdown,
                    'spx_price': spx_hist['Close'].iloc[-1] if not spx_hist.empty else 0,
                    'spx_change': ((spx_hist['Close'].iloc[-1] - spx_hist['Close'].iloc[-2]) / spx_hist['Close'].iloc[-2] * 100) if len(spx_hist) >= 2 else 0,
                    'buy_levels': {
                        'phase1': p1, 'phase2': p2, 'phase3': p3, 'phase4': p4
                    }
                }
        except Exception as e:
            st.error(f"Error obteniendo datos: {e}")
        
        return None

    data = get_market_data()
    
    if data is None:
        st.error("No se pudieron obtener datos del mercado")
        return

    # === MÉTRICAS PRINCIPALES ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        color = "positive" if data['spxl_change'] >= 0 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">SPXL Actual</div>
            <div class="metric-value">${data['spxl_price']:.2f}</div>
            <div class="{color}" style="font-size: 1.1rem; font-weight: 600;">
                {data['spxl_change']:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">S&P 500</div>
            <div class="metric-value">{data['spx_price']:,.2f}</div>
            <div class="{'positive' if data['spx_change'] >= 0 else 'negative'}" style="font-size: 1.1rem; font-weight: 600;">
                {data['spx_change']:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        dd_color = "positive" if data['drawdown'] > -10 else "warning" if data['drawdown'] > -15 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Drawdown desde Máx</div>
            <div class="metric-value {dd_color}">{data['drawdown']:.2f}%</div>
            <div style="color: #666; font-size: 0.8rem;">Máx: ${data['spxl_high']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Determinar fase actual
        current_dd = abs(data['drawdown'])
        if current_dd < 15:
            phase = "ESPERANDO"
            phase_color = "#888"
        elif current_dd < 25:
            phase = "FASE 1 ACTIVA"
            phase_color = "#00ffad"
        elif current_dd < 32:
            phase = "FASE 2 ACTIVA"
            phase_color = "#00ffad"
        elif current_dd < 39:
            phase = "FASE 3 ACTIVA"
            phase_color = "#00ffad"
        else:
            phase = "FASE 4 ACTIVA"
            phase_color = "#f23645"
        
        st.markdown(f"""
        <div class="metric-card" style="border-color: {phase_color};">
            <div class="metric-label">Estado Estrategia</div>
            <div class="metric-value" style="color: {phase_color}; font-size: 1.3rem;">{phase}</div>
            <div style="color: #666; font-size: 0.8rem;">Basado en caída actual</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # === TABS PRINCIPALES ===
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📖 Estrategia", "💰 Calculadora", "⚠️ Riesgo"])

    # === TAB 1: DASHBOARD ===
    with tab1:
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("""
            <div class="section-container">
                <div class="section-header">📈 Gráfico SPXL con Niveles de Compra</div>
                <div class="section-content">
            """, unsafe_allow_html=True)
            
            # Gráfico de TradingView con líneas de niveles
            levels = data['buy_levels']
            chart_html = f"""
            <div class="tradingview-widget-container">
              <div id="tradingview_spxl"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({
                "width": "100%",
                "height": 500,
                "symbol": "AMEX:SPXL",
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "es",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": false,
                "container_id": "tradingview_spxl",
                "studies": [],
                "overrides": {{
                    "mainSeriesProperties.style": 1,
                    "paneProperties.background": "#0c0e12",
                    "paneProperties.vertGridProperties.color": "#1a1e26",
                    "paneProperties.horzGridProperties.color": "#1a1e26"
                }},
                "lineTools": [
                    {{"type": "horizontalLine", "price": {levels['phase1']}, "color": "#00ffad", "linewidth": 2, "text": "COMPRA 1 (-15%)"}},
                    {{"type": "horizontalLine", "price": {levels['phase2']}, "color": "#ff9800", "linewidth": 2, "text": "COMPRA 2 (-10%)"}},
                    {{"type": "horizontalLine", "price": {levels['phase3']}, "color": "#f23645", "linewidth": 2, "text": "COMPRA 3 (-7%)"}},
                    {{"type": "horizontalLine", "price": {levels['phase4']}, "color": "#9c27b0", "linewidth": 2, "text": "COMPRA 4 (-10%)"}}
                ]
              });
              </script>
            </div>
            """
            components.html(chart_html, height=520)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        with col_right:
            # Panel de señales
            st.markdown("""
            <div class="section-container">
                <div class="section-header">🔔 Señales en Tiempo Real</div>
                <div class="section-content">
            """, unsafe_allow_html=True)
            
            current_price = data['spxl_price']
            levels = data['buy_levels']
            
            # Determinar qué fases están activas/completadas
            phases = [
                ("Fase 1: Compra Inicial", levels['phase1'], 0.20, 15, current_price <= levels['phase1']),
                ("Fase 2: Segunda Entrada", levels['phase2'], 0.15, 10, current_price <= levels['phase2']),
                ("Fase 3: Tercera Entrada", levels['phase3'], 0.20, 7, current_price <= levels['phase3']),
                ("Fase 4: Entrada Final", levels['phase4'], 0.20, 10, current_price <= levels['phase4'])
            ]
            
            for i, (name, price, allocation, drop, is_active) in enumerate(phases, 1):
                if is_active:
                    status_class = "active"
                    status_text = "🎯 ACTIVA"
                elif current_price < price:
                    status_class = "completed"
                    status_text = "✓ COMPLETADA"
                else:
                    status_class = "pending"
                    status_text = "⏳ PENDIENTE"
                
                distance = ((current_price - price) / price) * 100
                distance_text = f"{distance:+.1f}%" if distance > 0 else f"{distance:.1f}%"
                distance_color = "positive" if distance <= 0 else "negative"
                
                st.markdown(f"""
                <div class="phase-card {status_class}">
                    <div class="phase-number">{i}</div>
                    <div style="font-weight: 600; color: white; margin-bottom: 5px;">{name}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #00ffad; font-size: 1.2rem; font-weight: 700;">${price:.2f}</span>
                        <span style="color: #888; font-size: 0.8rem;">{status_text}</span>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.8rem;">
                        <span style="color: #666;">Alloc: {allocation:.0%}</span> | 
                        <span style="color: #666;">Drop: -{drop}%</span> | 
                        <span class="{distance_color}">Dist: {distance_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Alerta de compra o espera
            if current_price <= levels['phase4']:
                st.markdown("""
                <div class="alert-box alert-buy pulse">
                    <strong>🚨 COMPRA MÁXIMA ACTIVADA</strong><br>
                    Todas las fases disponibles. Invertir 75% del capital.
                </div>
                """, unsafe_allow_html=True)
            elif current_price <= levels['phase1']:
                st.markdown("""
                <div class="alert-box alert-buy">
                    <strong>✅ SEÑAL DE COMPRA ACTIVA</strong><br>
                    El precio ha alcanzado niveles de compra.
                </div>
                """, unsafe_allow_html=True)
            else:
                distance_to_p1 = ((current_price - levels['phase1']) / levels['phase1']) * 100
                st.markdown(f"""
                <div class="alert-box alert-warning">
                    <strong>⏳ EN ZONA DE ESPERA</strong><br>
                    Faltan {distance_to_p1:.1f}% para activar compras.
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)

    # === TAB 2: ESTRATEGIA ===
    with tab2:
        st.markdown("""
        <div class="section-container">
            <div class="section-header">🎯 Filosofía de la Estrategia</div>
            <div class="section-content">
                <div class="strategy-philosophy">
                    <h3 style="color: #00ffad; margin-top: 0;">Premisa Fundamental</h3>
                    <p style="color: #ccc; line-height: 1.6;">
                        Esta estrategia se basa estrictamente en la premisa de que el mercado de EE.UU. 
                        (<strong>S&P 500 / US500</strong>) mantendrá su <span class="highlight">macro tendencia alcista</span> 
                        a largo plazo, recuperándose históricamente de todas sus correcciones.
                    </p>
                </div>
                
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Instrumento</div>
                        <div class="info-value" style="color: #00ffad;">SPXL (3x Leveraged)</div>
                        <div style="color: #666; font-size: 0.8rem; margin-top: 5px;">
                            ETF que multiplica x3 los movimientos diarios del S&P 500
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Objetivo de Venta</div>
                        <div class="info-value" style="color: #00ffad;">+20% Beneficio</div>
                        <div style="color: #666; font-size: 0.8rem; margin-top: 5px;">
                            Sobre el precio medio de entrada ponderado
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Protección</div>
                        <div class="info-value" style="color: #f23645;">CDS Monitor</div>
                        <div style="color: #666; font-size: 0.8rem; margin-top: 5px;">
                            Freno de emergencia ante crisis sistémicas (>10.7)
                        </div>
                    </div>
                </div>
                
                <h3 style="color: white; margin-top: 30px; margin-bottom: 15px;">📋 Reglas de Entrada (Escalado)</h3>
                
                <div class="rule-item">
                    <div class="rule-icon">1</div>
                    <div>
                        <strong style="color: white;">Primera Caída (-15% desde máximos)</strong><br>
                        <span style="color: #888; font-size: 0.9rem;">
                            Cuando SPXL cae 15% desde su máximo anual, invertir <span class="highlight">20% del capital</span>.
                            Esto equivale a ~5% de caída en S&P 500, una corrección común y saludable.
                        </span>
                    </div>
                </div>
                
                <div class="rule-item">
                    <div class="rule-icon">2</div>
                    <div>
                        <strong style="color: white;">Segunda Caída (-10% adicional)</strong><br>
                        <span style="color: #888; font-size: 0.9rem;">
                            Si tras la primera compra cae un 10% más, invertir <span class="highlight">15% del capital</span>.
                            Total acumulado: 35% invertido.
                        </span>
                    </div>
                </div>
                
                <div class="rule-item">
                    <div class="rule-icon">3</div>
                    <div>
                        <strong style="color: white;">Tercera Caída (-7% adicional)</strong><br>
                        <span style="color: #888; font-size: 0.9rem;">
                            Si continúa cayendo un 7% más, invertir <span class="highlight">20% del capital</span>.
                            Total acumulado: 55% invertido.
                        </span>
                    </div>
                </div>
                
                <div class="rule-item">
                    <div class="rule-icon">4</div>
                    <div>
                        <strong style="color: white;">Cuarta Caída (-10% adicional)</strong><br>
                        <span style="color: #888; font-size: 0.9rem;">
                            Caída profunda del 10% adicional, invertir <span class="highlight">20% del capital</span>.
                            Total acumulado: <span class="highlight">75% invertido</span>. Reserva: 25% en efectivo.
                        </span>
                    </div>
                </div>
                
                <h3 style="color: white; margin-top: 30px; margin-bottom: 15px;">🎯 Regla de Salida</h3>
                
                <div class="rule-item" style="border-color: #f23645;">
                    <div class="rule-icon" style="background: #f2364522; color: #f23645;">$</div>
                    <div>
                        <strong style="color: white;">Take Profit (+20%)</strong><br>
                        <span style="color: #888; font-size: 0.9rem;">
                            Vender TODO cuando el precio alcance <span class="success">+20% sobre el precio medio</span> de compra.
                            Esto equivale a solo ~6% de recuperación en S&P 500, muy alcanzable tras caídas.
                            Una vez vendido, esperar nueva señal de compra.
                        </span>
                    </div>
                </div>
                
                <h3 style="color: white; margin-top: 30px; margin-bottom: 15px;">🛡️ Mecanismo de Seguridad (CDS)</h3>
                
                <div class="rule-item" style="background: #f2364511; border-color: #f23645;">
                    <div class="rule-icon" style="background: #f23645; color: white;">!</div>
                    <div>
                        <strong style="color: #f23645;">STOP DE CRISIS: Credit Default Swaps</strong><br>
                        <span style="color: #888; font-size: 0.9rem;">
                            Si el índice <strong>BAMLH0A0HYM2</strong> supera <span class="danger">10.7</span> 
                            o sube 250% desde mínimos, <strong>DETENER TODAS LAS COMPRAS</strong>.
                            Esto indica crisis de crédito sistémica (tipo 2008). Mantener posiciones pero no añadir capital.
                        </span>
                    </div>
                </div>
            </div>
        </div>
        
        # Botón de descarga PDF
        pdf_path = "assets/SPXL.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📄 Descargar Estrategia Completa (PDF)",
                data=pdf_bytes,
                file_name="SPXL.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.warning("Archivo PDF no encontrado en assets/SPXL.pdf")

    # === TAB 3: CALCULADORA ===
    with tab3:
        st.markdown("""
        <div class="section-container">
            <div class="section-header">💰 Calculadora de Posición</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        col_calc1, col_calc2 = st.columns(2)
        
        with col_calc1:
            capital_total = st.number_input(
                "Capital Total para Estrategia ($):",
                min_value=1000,
                value=10000,
                step=1000,
                help="Capital total que destinarás a esta estrategia"
            )
            
            tiene_posicion = st.checkbox("¿Tienes posición abierta actualmente?")
            
            if tiene_posicion:
                precio_medio = st.number_input(
                    "Precio medio de compra actual ($):",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                    help="Promedio ponderado de tus compras anteriores"
                )
                cantidad_acciones = st.number_input(
                    "Cantidad de acciones poseídas:",
                    min_value=0,
                    value=0,
                    step=1
                )
            else:
                precio_medio = 0
                cantidad_acciones = 0
        
        with col_calc2:
            st.markdown("### 📊 Distribución Recomendada")
            
            allocations = {
                "Fase 1 (-15%)": (0.20, "Esperando caída..."),
                "Fase 2 (-25%)": (0.15, "Esperando caída..."),
                "Fase 3 (-32%)": (0.20, "Esperando caída..."),
                "Fase 4 (-42%)": (0.20, "Esperando caída..."),
                "Reserva Efectivo": (0.25, "Protección")
            }
            
            total_allocated = 0
            for fase, (pct, desc) in allocations.items():
                monto = capital_total * pct
                total_allocated += monto if fase != "Reserva Efectivo" else 0
                
                if fase == "Reserva Efectivo":
                    st.markdown(f"""
                    <div style="background: #0c0e12; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #ff9800;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #888;">{fase}</span>
                            <span style="color: #ff9800; font-weight: bold;">${monto:,.2f}</span>
                        </div>
                        <div style="color: #666; font-size: 0.8rem;">{desc}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    price_level = data['buy_levels'][f'phase{list(allocations.keys()).index(fase)+1}']
                    st.markdown(f"""
                    <div style="background: #0c0e12; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #00ffad;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: white; font-weight: 500;">{fase}</span>
                            <span style="color: #00ffad; font-weight: bold;">${monto:,.2f}</span>
                        </div>
                        <div style="color: #666; font-size: 0.8rem;">Precio objetivo: ${price_level:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: #00ffad11; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #00ffad;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: white; font-weight: 600;">Capital a invertir:</span>
                    <span style="color: #00ffad; font-size: 1.3rem; font-weight: bold;">${total_allocated:,.2f}</span>
                </div>
                <div style="color: #888; font-size: 0.8rem; margin-top: 5px;">
                    75% del capital total | Objetivo: +20% = ${total_allocated * 1.20:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Cálculo de objetivo de venta si hay posición
        if tiene_posicion and precio_medio > 0:
            st.markdown("---")
            st.markdown("### 🎯 Tu Posición Actual")
            
            valor_actual = cantidad_acciones * data['spxl_price']
            costo_total = cantidad_acciones * precio_medio
            pnl = valor_actual - costo_total
            pnl_pct = (pnl / costo_total) * 100 if costo_total > 0 else 0
            target_price = precio_medio * 1.20
            
            col_pos1, col_pos2, col_pos3 = st.columns(3)
            
            with col_pos1:
                st.metric(
                    "Valor Actual",
                    f"${valor_actual:,.2f}",
                    f"{pnl_pct:+.2f}%"
                )
            
            with col_pos2:
                st.metric(
                    "Precio de Venta Objetivo",
                    f"${target_price:.2f}",
                    f"+20.00%"
                )
            
            with col_pos3:
                distancia_objetivo = ((target_price - data['spxl_price']) / data['spxl_price']) * 100
                st.metric(
                    "Distancia al Objetivo",
                    f"{distancia_objetivo:.2f}%",
                    None
                )
            
            if data['spxl_price'] >= target_price:
                st.balloons()
                st.markdown("""
                <div class="alert-box alert-sell pulse">
                    <strong>🎯 ¡OBJETIVO ALCANZADO!</strong><br>
                    Se ha activado la señal de venta. Considera cerrar posición.
                </div>
                """, unsafe_allow_html=True)
            else:
                progreso = ((data['spxl_price'] - precio_medio) / (target_price - precio_medio)) * 100
                progreso = max(0, min(100, progreso))
                
                st.markdown(f"""
                <div style="margin-top: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="color: #888;">Progreso hacia objetivo:</span>
                        <span style="color: #00ffad; font-weight: bold;">{progreso:.1f}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progreso}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

    # === TAB 4: RIESGO (CDS) ===
    with tab4:
        st.markdown("""
        <div class="section-container">
            <div class="section-header">⚠️ Monitor de Riesgo Sistémico (CDS)</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #0c0e12; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <strong style="color: white;">Índice: BAMLH0A0HYM2</strong> | 
            <span style="color: #888;">ICE BofA US High Yield Index Option-Adjusted Spread</span><br>
            <span style="color: #666; font-size: 0.9rem;">
                Mide el riesgo de crédito en bonos high-yield. Valores >10.7 indican crisis sistémica.
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Gauge visual del CDS
        st.markdown("""
        <div style="margin: 30px 0;">
            <div class="cds-gauge">
                <div class="cds-marker" style="left: 30%;" id="cds-marker"></div>
            </div>
            <div class="cds-labels">
                <span>Normal (<3)</span>
                <span>Atención (3-7)</span>
                <span>Peligro (7-10.7)</span>
                <span style="color: #f23645; font-weight: bold;">CRISIS (>10.7)</span>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 20px;">
            <div style="background: #00ffad22; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #00ffad;">
                <div style="color: #00ffad; font-size: 0.8rem;">ZONA SEGURA</div>
                <div style="color: white; font-size: 1.5rem; font-weight: bold;">&lt; 3.0</div>
                <div style="color: #888; font-size: 0.7rem;">Compras normales</div>
            </div>
            <div style="background: #ff980022; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ff9800;">
                <div style="color: #ff9800; font-size: 0.8rem;">PRECAUCIÓN</div>
                <div style="color: white; font-size: 1.5rem; font-weight: bold;">3.0 - 7.0</div>
                <div style="color: #888; font-size: 0.7rem;">Reducir posiciones</div>
            </div>
            <div style="background: #f2364522; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #f23645;">
                <div style="color: #f23645; font-size: 0.8rem;">ALERTA</div>
                <div style="color: white; font-size: 1.5rem; font-weight: bold;">7.0 - 10.7</div>
                <div style="color: #888; font-size: 0.7rem;">No nuevas compras</div>
            </div>
            <div style="background: #9c27b022; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #9c27b0;">
                <div style="color: #9c27b0; font-size: 0.8rem;">CRISIS</div>
                <div style="color: white; font-size: 1.5rem; font-weight: bold;">&gt; 10.7</div>
                <div style="color: #888; font-size: 0.7rem;">STOP TOTAL</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Gráfico de TradingView del CDS
        st.markdown("""
        <div class="chart-container" style="margin-top: 30px;">
            <div style="color: white; font-weight: 600; margin-bottom: 10px;">📈 Evolución del CDS</div>
        """, unsafe_allow_html=True)
        
        cds_chart = """
        <div class="tradingview-widget-container">
          <div id="tradingview_cds"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({
            "width": "100%",
            "height": 400,
            "symbol": "FRED:BAMLH0A0HYM2",
            "interval": "W",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "es",
            "enable_publishing": false,
            "hide_side_toolbar": true,
            "container_id": "tradingview_cds",
            "overrides": {
                "paneProperties.background": "#0c0e12",
                "paneProperties.vertGridProperties.color": "#1a1e26",
                "paneProperties.horzGridProperties.color": "#1a1e26"
            }
          });
          </script>
        </div>
        """
        components.html(cds_chart, height=420)
        
        st.markdown("""
        </div>
        <div class="alert-box alert-warning" style="margin-top: 20px;">
            <strong>⚠️ Instrucción de Emergencia:</strong><br>
            Si el CDS muestra un pico vertical brusco hacia 10.7 o superior, 
            <strong>DETÉN INMEDIATAMENTE</strong> todas las compras aunque el precio de SPXL esté cayendo.
            Esto indica crisis de crédito sistémica similar a 2008.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

    # === FOOTER ===
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #555; font-size: 0.8rem; padding: 20px;">
        <p>RSU - Redistribution Strategy Research Unit</p>
        <p style="color: #444;">Esta herramienta es educativa. No constituye asesoramiento financiero.</p>
    </div>
    """, unsafe_allow_html=True)

# Para ejecutar la función si el script se corre directamente
if __name__ == "__main__":
    render()

