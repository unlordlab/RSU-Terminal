import streamlit as st
import pandas as pd
import yfinance as yf
import streamlit.components.v1 as components
import os

def render():
    st.title("📈 ESTRATEGIA COMERCIAL SPXL")
    st.caption("Terminal RSU - Gestión de Compras Escaladas y Riesgo de Crédito")

    # --- DATOS DE MERCADO EN TIEMPO REAL ---
    try:
        # Tickers: SPXL y S&P 500 (^GSPC)
        ticker_spxl = "SPXL"
        ticker_sp500 = "^GSPC"
        
        # Descarga de datos (último año para SPXL, 2 días para el cierre del S&P)
        df_spxl = yf.Ticker(ticker_spxl).history(period="1y")
        df_sp500 = yf.Ticker(ticker_sp500).history(period="2d")
        
        if not df_spxl.empty:
            precio_actual = df_spxl['Close'].iloc[-1]
            cierre_prev_spxl = df_spxl['Close'].iloc[-2]
            max_periodo = df_spxl['High'].max()
            caida_desde_max = ((precio_actual - max_periodo) / max_periodo) * 100
            var_spxl = ((precio_actual - cierre_prev_spxl) / cierre_prev_spxl) * 100
        else:
            precio_actual, max_periodo, caida_desde_max, var_spxl = 0, 0, 0, 0

        if not df_sp500.empty:
            precio_sp500 = df_sp500['Close'].iloc[-1]
            cierre_prev_sp500 = df_sp500['Close'].iloc[-2]
            var_sp500 = ((precio_sp500 - cierre_prev_sp500) / cierre_prev_sp500) * 100
        else:
            precio_sp500, var_sp500 = 0, 0
            
    except Exception as e:
        st.error(f"Error al obtener datos: {e}")
        precio_actual, max_periodo, caida_desde_max, var_spxl = 0, 0, 0, 0
        precio_sp500, var_sp500 = 0, 0

    # --- MÉTRICAS DE ÚLTIMA SESIÓN ---
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("SPXL (Último)", f"${precio_actual:.2f}", f"{var_spxl:.2f}%")
    col_m2.metric("S&P 500 (US500)", f"{precio_sp500:,.2f}", f"{var_sp500:.2f}%")
    col_m3.metric("Caída desde Máx", f"{caida_desde_max:.2f}%", delta_color="inverse")

    # --- DESCRIPCIÓN DE LA ESTRATEGIA ---
    with st.expander("📖 Filosofía y Premisas", expanded=False):
        st.markdown("""
        **Premisa Fundamental:** El mercado de EE.UU. (**S&P 500**) mantiene su macro tendencia alcista histórica.
        * **Entradas:** 4 fases (Caída 15%, 10%, 7%, 10%).
        * **Salida:** Objetivo +20% sobre el precio medio.
        """)
        
        pdf_path = "assets/SPXL.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button("📄 Descargar Estrategia (PDF)", f.read(), "SPXL.pdf", "application/pdf")

    # --- SECCIÓN DE POSICIÓN ---
    st.subheader("🛒 Tu Posición Actual")
    cp1, cp2 = st.columns(2)
    with cp1:
        tiene_posicion = st.checkbox("¿Tienes una posición abierta?")
        capital_total = st.number_input("Capital total ($):", value=10000, step=500)
    with cp2:
        precio_medio = st.number_input("Precio medio ($):", value=0.0, step=0.1) if tiene_posicion else 0.0

    # --- ALERTAS ---
    st.write("---")
    if tiene_posicion and precio_medio > 0:
        target_venta = precio_medio * 1.20
        rendimiento = ((precio_actual - precio_medio) / precio_medio) * 100
        if precio_actual >= target_venta:
            st.balloons()
            st.success(f"🎯 **VENTA ACTIVA:** Objetivo alcanzado en ${target_venta:.2f}")
        else:
            st.info(f"Rendimiento: **{rendimiento:.2f}%**. Venta en: **${target_venta:.2f}**")
    
    if caida_desde_max <= -15:
        st.error(f"🚨 **COMPRA ACTIVA:** Caída del {caida_desde_max:.2f}% detectada.")

    # --- TABLA DE NIVELES (Corregida) ---
    st.subheader("🪜 Niveles de Ejecución")
    p1 = max_periodo * 0.85
    p2 = p1 * 0.90
    p3 = p2 * 0.93
    p4 = p3 * 0.90
    
    fases = [
        {"Fase": "1ª Compra", "Trigger": "-15% desde Máx", "Precio": p1, "Monto": capital_total * 0.20},
        {"Fase": "2ª Compra", "Trigger": "-10% desde 1ª", "Precio": p2, "Monto": capital_total * 0.15},
        {"Fase": "3ª Compra", "Trigger": "-7% desde 2ª", "Precio": p3, "Monto": capital_total * 0.20},
        {"Fase": "4ª Compra", "Trigger": "-10% desde 3ª", "Precio": p4, "Monto": capital_total * 0.20},
    ]
    st.table(pd.DataFrame(fases).style.format({"Precio": "{:.2f}$", "Monto": "{:,.2f}$"}))

    # --- RIESGO SISTÉMICO ---
    st.write("---")
    st.subheader("🚨 Monitor de Riesgo Sistémico (FRED)")
    tv_widget = """
    <div class="tradingview-widget-container"><div id="tv_chart"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
      new TradingView.widget({"width": "100%","height": 400,"symbol": "FRED:BAMLH0A0HYM2","interval": "D","theme": "dark","container_id": "tv_chart"});
    </script></div>
    """
    components.html(tv_widget, height=420)

if __name__ == "__main__":
    render()
