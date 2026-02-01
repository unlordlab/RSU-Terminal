import streamlit as st
import pandas as pd
import yfinance as yf
import streamlit.components.v1 as components

def render():
    st.title("📈 ESTRATEGIA COMERCIAL SPXL")
    st.caption("Terminal RSU - Gestión de Compras Escaladas y Riesgo de Crédito")

    # --- DESCRIPCIÓN DE LA ESTRATEGIA ---
    with st.expander("📖 Descripción de la Estrategia", expanded=False):
        st.markdown("""
        **Filosofía:** Esta estrategia busca capitalizar las correcciones del mercado utilizando el ETF apalancado **SPXL** (3x S&P 500). 
        En lugar de adivinar el suelo, se realizan compras promediadas en niveles de caída específicos.
        
        **Puntos Clave:**
        * **Entradas:** Se activan al caer un 15%, 10%, 7% y 10% respectivamente.
        * **Salida:** Objetivo de beneficio del **+20%** sobre el precio medio.
        * **Freno de Seguridad:** Si los diferenciales de crédito (CDS) se disparan, se detiene la operativa para evitar "cisnes negros" o crisis sistémicas.
        """)

    # --- DATOS DE MERCADO EN TIEMPO REAL ---
    try:
        ticker_symbol = "SPXL"
        data = yf.Ticker(ticker_symbol)
        hist = data.history(period="1y")
        if not hist.empty:
            precio_actual = hist['Close'].iloc[-1]
            max_periodo = hist['High'].max()
            caida_desde_max = ((precio_actual - max_periodo) / max_periodo) * 100
        else:
            precio_actual, max_periodo, caida_desde_max = 0, 0, 0
    except:
        precio_actual, max_periodo, caida_desde_max = 0, 0, 0

    # --- SECCIÓN DE POSICIÓN ABIERTA ---
    st.subheader("🛒 Tu Posición Actual")
    col_pos1, col_pos2 = st.columns(2)
    
    with col_pos1:
        tiene_posicion = st.checkbox("¿Tienes una posición abierta actualmente?")
        capital_total = st.number_input("Capital total destinado a esta estrategia ($):", value=10000, step=500)
    
    with col_pos2:
        if tiene_posicion:
            precio_medio = st.number_input("Tu precio medio de compra ($):", value=0.0, step=0.1)
            fase_actual = st.selectbox("¿En qué fase de compra te encuentras?", ["1ª Compra", "2ª Compra", "3ª Compra", "4ª Compra"])
        else:
            precio_medio = 0.0

    # --- ALERTAS DE COMPRA Y VENTA ---
    st.write("---")
    if tiene_posicion and precio_medio > 0:
        target_venta = precio_medio * 1.20
        rendimiento = ((precio_actual - precio_medio) / precio_medio) * 100
        
        st.subheader("🔔 Señales de Venta")
        if precio_actual >= target_venta:
            st.balloons()
            st.success(f"🎯 **SEÑAL DE VENTA ACTIVA:** El precio (${precio_actual:.2f}) ha alcanzado el objetivo del +20% (${target_venta:.2f}).")
        else:
            st.info(f"Rendimiento actual: **{rendimiento:.2f}%**. Objetivo de venta en: **${target_venta:.2f}**")
    
    # Alerta de Compra
    if caida_desde_max <= -15:
        st.error(f"🚨 **SEÑAL DE COMPRA ACTIVA:** SPXL ha caído un {caida_desde_max:.2f}% desde máximos.")

    # --- TABLA DE REGLAS ---
    st.subheader("🪜 Plan de Ejecución Basado en Reglas")
    fases = [
        {"Fase": "1ª Compra", "Trigger": "-15% desde Máx", "Precio Objetivo": max_periodo * 0.85, "Capital": "20%", "Inversión": capital_total * 0.20},
        {"Fase": "2ª Compra", "Trigger": "-10% desde 1ª", "Precio Objetivo": (max_periodo * 0.85) * 0.90, "Capital": "15%", "Inversión": capital_total * 0.15},
        {"Fase": "3ª Compra", "Trigger": "-7% desde 2ª", "Precio Objetivo": ((max_periodo * 0.85) * 0.90) * 0.93, "Capital": "20%", "Inversión": capital_total * 0.20},
        {"Fase": "4ª Compra", "Trigger": "-10% desde 3ª", "Precio Objetivo": (((max_periodo * 0.85) * 0.90) * 0.93) * 0.90, "Capital": "20%", "Inversión": capital_total * 0.20},
    ]
    st.table(pd.DataFrame(fases).style.format({"Precio Objetivo": "{:.2f}$", "Inversión": "{:,.2f}$"}))

    # --- RIESGO SISTÉMICO (CDS corregido) ---
    st.write("---")
    st.subheader("🚨 Monitor de Riesgo (BAMLH0A0HYM2)")
    st.caption("Si este spread supera los 10.7, no se ejecutan más compras (Pánico detectado).")
    
    tv_widget_html = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "width": "100%",
        "height": 400,
        "symbol": "FRED:BAMLH0A0HYM2",
        "interval": "D",
        "theme": "dark",
        "style": "1",
        "locale": "es",
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(tv_widget_html, height=420)
