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
        # Definición de Tickers
        ticker_spxl = "SPXL"
        ticker_sp500 = "^GSPC" # Ticker estándar del S&P 500 en Yahoo Finance
        
        # Descarga de datos
        data_spxl = yf.Ticker(ticker_spxl).history(period="1y")
        data_sp500 = yf.Ticker(ticker_sp500).history(period="2d")
        
        if not data_spxl.empty:
            precio_actual = data_spxl['Close'].iloc[-1]
            cierre_anterior_spxl = data_spxl['Close'].iloc[-2]
            max_periodo = data_spxl['High'].max()
            caida_desde_max = ((precio_actual - max_periodo) / max_periodo) * 100
            var_spxl = ((precio_actual - cierre_anterior_spxl) / cierre_anterior_spxl) * 100
        else:
            precio_actual, max_periodo, caida_desde_max, var_spxl = 0, 0, 0, 0

        if not data_sp500.empty:
            precio_sp500 = data_sp500['Close'].iloc[-1]
            cierre_anterior_sp500 = data_sp500['Close'].iloc[-2]
            var_sp500 = ((precio_sp500 - cierre_anterior_sp500) / cierre_anterior_sp500) * 100
        else:
            precio_sp500, var_sp500 = 0, 0
    except:
        precio_actual, max_periodo, caida_desde_max, var_spxl = 0, 0, 0, 0
        precio_sp500, var_sp500 = 0, 0

    # --- DASHBOARD DE PRECIOS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("SPXL (Actual)", f"${precio_actual:.2f}", f"{var_spxl:.2f}%")
    m2.metric("S&P 500 (US500)", f"{precio_sp500:,.2f}", f"{var_sp500:.2f}%")
    m3.metric("Drawdown desde Máx", f"{caida_desde_max:.2f}%", delta_color="inverse")

    # --- DESCRIPCIÓN DE LA ESTRATEGIA ---
    with st.expander("📖 Filosofía y Premisas", expanded=False):
        st.markdown("""
        **Premisa Fundamental:** Esta estrategia se basa estrictamente en la premisa de que el mercado de EE.UU. (**S&P 500 / US500**) mantendrá su **macro tendencia alcista** a largo plazo.
        
        **Metodología:**
        * Se utiliza el ETF apalancado **SPXL** (3x Bull) para maximizar retornos.
        * **Entradas:** 4 fases escalonadas al caer un 15%, 10%, 7% y 10%.
        * **Salida:** Venta total al alcanzar un **+20%** sobre el precio medio.
        """)
        
        pdf_path = "assets/SPXL.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(label="📄 Descargar Estrategia (PDF)", data=pdf_bytes, file_name="SPXL.pdf", mime="application/pdf")

    # --- SECCIÓN DE POSICIÓN ABIERTA ---
    st.subheader("🛒 Tu Posición Actual")
    col_pos1, col_pos2 = st.columns(2)
    
    with col_pos1:
        tiene_posicion = st.checkbox("¿Tienes una posición abierta actualmente?")
        capital_total = st.number_input("Capital total para esta estrategia ($):", value=10000, step=500)
    
    with col_pos2:
        if tiene_posicion:
            precio_medio = st.number_input("Tu precio medio de compra ($):", value=0.0, step=0.1)
        else:
            precio_medio = 0.0

    # --- ALERTAS DE COMPRA Y VENTA ---
    st.write("---")
    if tiene_posicion and precio_medio > 0:
        target_venta = precio_medio * 1.20
        rendimiento = ((precio_actual - precio_medio) / precio_medio) * 100
        
        if precio_actual >= target_venta:
            st.balloons()
            st.success(f"🎯 **SEÑAL DE VENTA ACTIVA:** Objetivo del +20% alcanzado (${target_venta:.2f}).")
        else:
            st.info(f"Rendimiento actual: **{rendimiento:.2f}%**. Objetivo de venta en: **${target_venta:.2f}**")
    
    if caida_desde_max <= -15:
        st.error(f"🚨 **SEÑAL DE COMPRA ACTIVA:** El precio ha caído un {caida_desde_max:.2f}% desde máximos.")
    else:
        st.info(f"Distancia desde el máximo anual: **{caida_desde_max:.2f}%** (La 1ª compra se activa al -15%)")

    # --- TABLA DE REGLAS ---
    st.subheader("🪜 Niveles de Ejecución (Basados en Máximo Anual)")
    p1, p2 = max_periodo * 0.85, (max_periodo * 0.85) * 0.90
    p3, p4 = p2 * 0.93, p3 * 0.90
    
    fases = [
        {"Fase": "1ª Compra", "Trigger": "-15% desde Máx", "Precio Ref": p1, "Monto": capital_total * 0.20},
        {"Fase": "2ª Compra", "Trigger": "-10% desde 1ª", "Precio Ref": p2, "Monto": capital_total * 0.15},
        {"Fase": "3ª Compra", "Trigger": "-7% desde 2ª", "Precio Ref": p3, "Monto": capital_total * 0.20},
        {"Fase": "4ª Compra", "Trigger": "-10% desde 3ª", "Precio Ref": p4, "Monto": capital_total * 0.20},
    ]
    st.table(pd.DataFrame(fases).style.format({"Precio Ref": "{:.2f}$", "Monto": "{:,.2f}$"}))

    # --- RIESGO SISTÉMICO ---
    st.write("---")
    st.subheader("🚨 Monitor de Riesgo Sistémico")
    st.markdown(f"Ticker: **BAMLH0A0HYM2** | **Límite de Seguridad: 10.7**")
    
    tv_widget_html = """
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({
        "width": "100%", "height": 400, "symbol": "FRED:BAMLH0A0HYM2",
        "interval": "D", "theme": "dark", "style": "1", "locale": "es", "container_id": "tradingview_chart"
      });
      </script>
    </div>
    """
    components.html(tv_widget_html, height=420)

if __name__ == "__main__":
    render()


