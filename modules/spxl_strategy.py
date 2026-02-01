import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_tradingview_widget import streamlit_tradingview_widget

def render():
    st.title("📈 ESTRATEGIA COMERCIAL SPXL")
    st.caption("Terminal RSU - Basada en Reglas de Corrección de Mercado")

    # --- DATOS DE MERCADO ---
    try:
        ticker = "SPXL"
        data = yf.Ticker(ticker)
        hist = data.history(period="1y")
        precio_actual = hist['Close'].iloc[-1]
        max_periodo = hist['High'].max()
        caida_desde_max = ((precio_actual - max_periodo) / max_periodo) * 100
    except Exception as e:
        st.error("Error al conectar con Yahoo Finance")
        precio_actual, max_periodo, caida_desde_max = 0, 0, 0

    # --- CALCULADORA Y GESTIÓN DE POSICIÓN ---
    col_input, col_metrics = st.columns([1, 1.5])

    with col_input:
        st.subheader("📝 Gestión de Capital")
        capital_total = st.number_input("Capital total para SPXL ($):", value=10000, step=500)
        precio_medio = st.number_input("Tu precio medio actual ($):", value=0.0, step=0.1, help="Si ya tienes acciones, pon tu precio promedio de compra.")
        
        # Cálculo de Take Profit
        if precio_medio > 0:
            target_venta = precio_medio * 1.20
            st.success(f"🎯 **Objetivo de Venta (+20%): ${target_venta:.2f}**")

    with col_metrics:
        st.subheader("📊 Estado del Mercado")
        m1, m2 = st.columns(2)
        m1.metric("Precio Actual", f"${precio_actual:.2f}")
        m2.metric("Máximo Anual", f"${max_periodo:.2f}")
        
        # Alerta de Compra dinámica
        if caida_desde_max <= -15:
            st.error(f"🚨 ALERTA: Caída del {caida_desde_max:.2f}%. ¡Zona de 1ª Compra!")
        else:
            st.info(f"Distancia al máximo: {caida_desde_max:.2f}%")

    st.write("---")

    # --- REGLAS DE COMPRA ESCALONADA ---
    st.subheader("🪜 Plan de Ejecución")
    
    fases = [
        {"Fase": "1ª Compra", "Disparador": "-15% desde Máx", "Precio Ref": max_periodo * 0.85, "Capital": "20%", "Monto": capital_total * 0.20},
        {"Fase": "2ª Compra", "Disparador": "-10% desde 1ª", "Precio Ref": (max_periodo * 0.85) * 0.90, "Capital": "15%", "Monto": capital_total * 0.15},
        {"Fase": "3ª Compra", "Disparador": "-7% desde 2ª", "Precio Ref": ((max_periodo * 0.85) * 0.90) * 0.93, "Capital": "20%", "Monto": capital_total * 0.20},
        {"Fase": "4ª Compra", "Disparador": "-10% desde 3ª", "Precio Ref": (((max_periodo * 0.85) * 0.90) * 0.93) * 0.90, "Capital": "20%", "Monto": capital_total * 0.20},
    ]
    
    df_fases = pd.DataFrame(fases)
    st.table(df_fases.style.format({"Precio Ref": "{:.2f}$", "Monto": "{:,.2f}$"}))
    st.caption(f"💰 Reserva de Efectivo (25%): ${(capital_total * 0.25):,.2f}")

    # --- RIESGO SISTÉMICO (CDS) ---
    st.write("---")
    st.subheader("🚨 Monitor de Riesgo Sistémico (CDS)")
    st.markdown("""
    **Regla de Oro:** Si el ticker **BAMLHOA0HYM2** (ICE BofA US High Yield Index Option-Adjusted Spread) sube de **10.7**, se detienen todas las compras.
    """)

    # Widget de TradingView para los CDS (usando el código de FRED)
    streamlit_tradingview_widget(
        symbol="FRED:BAMLHOA0HYM2",
        dataset="FRED",
        height=400,
        theme="dark",
        autosize=True
    )

    # --- FOOTER ---
    with st.expander("ℹ️ Ayuda sobre las reglas"):
        st.write("""
        1. **Comprar** solo cuando el precio toque los niveles de la tabla.
        2. **Vender** la posición completa cuando el beneficio sea del 20%.
        3. **No comprar** si el gráfico de arriba (CDS) muestra un pico de pánico financiero.
        """)
