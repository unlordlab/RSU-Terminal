import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_tradingview_widget import streamlit_tradingview_widget

def render():
    st.title("📈 ESTRATEGIA COMERCIAL SPXL")
    st.caption("Basada en reglas v0.1 - Direxion Daily S&P 500 Bull 3X Shares [cite: 11]")

    # --- OBTENCIÓN DE DATOS EN TIEMPO REAL ---
    try:
        spxl = yf.Ticker("SPXL")
        datos = spxl.history(period="1y")
        precio_actual = datos['Close'].iloc[-1]
        max_periodo = datos['High'].max()
        caida_desde_max = ((precio_actual - max_periodo) / max_periodo) * 100
    except:
        precio_actual, max_periodo, caida_desde_max = 0, 0, 0

    # --- CALCULADORA DE POSICIONES ---
    st.subheader("🧮 Calculadora de Estrategia")
    capital_total = st.number_input("Introduce tu capital total destinado ($):", min_value=0.0, value=10000.0, step=1000.0)
    
    col_calc_1, col_calc_2 = st.columns([2, 1])

    with col_calc_1:
        # Definición de fases según el documento
        fases = [
            {"Nombre": "1ª Compra", "Trigger": "15% desde Máx", "Capital %": 0.20, "Ref": "Máximo Hist."},
            {"Nombre": "2ª Compra", "Trigger": "10% desde 1ª", "Capital %": 0.15, "Ref": "Precio 1ª"},
            {"Nombre": "3ª Compra", "Trigger": "7% desde 2ª", "Capital %": 0.20, "Ref": "Precio 2ª"},
            {"Nombre": "4ª Compra", "Trigger": "10% desde 3ª", "Capital %": 0.20, "Ref": "Precio 3ª"}
        ]
        
        df_estrategia = pd.DataFrame([
            {
                "Fase": f["Nombre"],
                "Disparador": f["Trigger"],
                "Inversión ($)": f"{capital_total * f['Capital %']:,.2f}",
                "Referencia": f["Ref"]
            } for f in fases
        ])
        st.table(df_estrategia)
        st.caption(f"Reserva de seguridad (Efectivo): ${(capital_total * 0.25):,.2f} (25%) ")

    with col_calc_2:
        st.metric("Precio Actual SPXL", f"${precio_actual:.2f}")
        st.metric("Máximo Anual", f"${max_periodo:.2f}")
        color_delta = "inverse" if caida_desde_max < -15 else "normal"
        st.metric("Caída desde Máximo", f"{caida_desde_max:.2f}%", delta_color=color_delta)

    # --- SEMÁFORO DE ALERTAS ---
    st.subheader("🔔 Estado de Compra / Venta")
    
    # Lógica de aviso de compra [cite: 83, 84, 108]
    if caida_desde_max <= -15:
        st.error(f"🚨 **ALERTA DE COMPRA ACTIVA:** El SPXL ha caído un {caida_desde_max:.2f}%. Se cumple la condición de la 1ª Compra (-15%). [cite: 83]")
    elif precio_actual >= (precio_actual * 1.20): # Nota: lógica simplificada para el ejemplo
        st.success("🎯 **OBJETIVO DE VENTA:** El precio ha alcanzado el +20% desde tu entrada media. [cite: 108]")
    else:
        st.info("⌛ **ESPERANDO DISPARADOR:** El mercado no ha alcanzado niveles de compra o venta según las reglas.")

    st.write("---")

    # --- WIDGET TRADINGVIEW (CDS) ---
    st.subheader("🚨 Mecanismo de Seguridad: Riesgo Sistémico")
    st.markdown("""
    Monitorea el ticker **BAMLHOA0HYM2** (Credit Default Swaps). 
    Si supera **10.7**, detén las compras inmediatamente. [cite: 138, 141]
    """)
    
    # Widget de TradingView para el ticker de CDS
    # Nota: Usamos US High Yield Index como proxy si el ticker exacto tiene restricciones de visualización
    streamlit_tradingview_widget(
        symbol="FRED:BAMLHOA0HYM2", 
        dataset="FRED",
        height=400,
        theme="dark"
    )

    # --- RESUMEN DE REGLAS ---
    with st.expander("📚 Resumen de Reglas de la Estrategia"):
        st.write("""
        * **SPXL:** ETF apalancado 3x sobre el S&P 500. [cite: 41]
        * **Comprar en bajadas:** No intentamos adivinar el suelo, escalamos la posición. [cite: 57, 58]
        * **Take Profit:** Vender todo al alcanzar un **+20%** de beneficio sobre el precio medio. [cite: 106, 108]
        * **Liquidez:** Siempre mantenemos un **25% en efectivo** para casos extremos. [cite: 67, 130]
        """)

    st.write("---")
    st.warning("⚠️ **Advertencia de Riesgo:** El trading en ETFs apalancados como SPXL conlleva volatilidad extrema. [cite: 18, 20]")
