import streamlit as st

def render():
    st.title("📈 ESTRATEGIA COMERCIAL SPXL")
    st.caption("Basada en reglas v0.1 - Direxion Daily S&P 500 Bull 3X Shares")
    
    # --- INTRODUCCIÓN ---
    st.markdown("""
    Esta estrategia utiliza el **SPXL**, un ETF apalancado que multiplica por 3 los movimientos diarios del S&P 500[cite: 198]. 
    El objetivo es aprovechar las correcciones del mercado mediante compras escalonadas[cite: 215, 238].
    """)

    # --- OBJETIVO DE VENTA (TAKE PROFIT) ---
    st.subheader("🎯 Regla de Venta")
    st.success("**Take Profit: +20% sobre el precio medio de compra.** [cite: 263, 265]")
    st.info("Un 20% en SPXL equivale aproximadamente a una recuperación del 6% en el S&P 500[cite: 266].")

    st.write("---")

    # --- REGLAS DE COMPRA (DESENCADENANTES) ---
    st.subheader("🛒 Desencadenantes de Compra")
    st.markdown("Se debe comprar en etapas a medida que el precio cae desde máximos o desde la última compra:")

    col1, col2 = st.columns(2)

    with col1:
        st.info("### 1ª Compra\n**Caída del 15%** desde el último máximo histórico[cite: 240, 241].")
        st.info("### 2ª Compra\n**Caída del 10% adicional** desde el precio de la 1ª compra[cite: 244, 245].")

    with col2:
        st.info("### 3ª Compra\n**Caída del 7% adicional** desde el precio de la 2ª compra[cite: 248, 249].")
        st.info("### 4ª Compra\n**Caída del 10% adicional** desde el precio de la 3ª compra[cite: 251, 253].")

    # --- GESTIÓN DE CAPITAL ---
    st.subheader("💰 Gestión de Capital")
    st.write("Distribución recomendada del capital total destinado a esta estrategia[cite: 273]:")
    
    data = {
        "Etapa": ["1ª Compra", "2ª Compra", "3ª Compra", "4ª Compra", "Reserva (Efectivo)"],
        "Capital a Invertir": ["20%", "15%", "20%", "20%", "25%"],
        "Estado": ["Activo", "Activo", "Activo", "Activo", "Seguridad"]
    }
    st.table(data)
    st.caption("Al completar las 4 compras, habrás invertido el 75% del capital total[cite: 287].")

    # --- MECANISMO DE SEGURIDAD (CDS) ---
    with st.expander("🚨 MECANISMO DE SEGURIDAD (Freno de Emergencia)"):
        st.warning("""
        **No comprar** si el indicador de riesgo sistémico (Credit Default Swaps - CDS) se dispara[cite: 289, 292].
        
        * **Indicador:** BAMLHOA0HYM2 (disponible en TradingView)[cite: 295].
        * **Alerta:** Si sube por encima de **10.7** o aumenta un **250%** desde mínimos[cite: 295].
        * **Acción:** Dejar de comprar y no aumentar posiciones. Mantener lo que ya esté invertido[cite: 298, 299].
        """)

    st.write("---")
    st.markdown("> **Nota:** Esta estrategia se basa en la premisa de que el mercado de EE.UU. continuará creciendo a largo plazo[cite: 206].")
