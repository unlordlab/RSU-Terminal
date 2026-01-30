import streamlit as st
import pandas as pd

def render():
    st.title("💼 Cartera Estratégica RSU")
    
    try:
        # 1. Carga de datos desde Google Sheets (formato CSV)
        url = st.secrets["URL_CARTERA"]
        # El parámetro cache_bus evita que Google nos devuelva datos antiguos
        df = pd.read_csv(f"{url}&cache_bus={pd.Timestamp.now().timestamp()}").dropna(how='all')
        
        # 2. Limpieza de nombres de columnas (eliminar espacios invisibles)
        df.columns = [c.strip() for c in df.columns]

        # 3. Normalización de dades para evitar errores de escritura en el Sheet
        if 'Estado' in df.columns:
            df['Estado'] = df['Estado'].astype(str).str.strip().str.upper()
        
        if 'Ticker' in df.columns:
            df['Ticker'] = df['Ticker'].astype(str).str.strip()

        # Conversión de Fecha (si falla, pone NaT y luego lo eliminamos)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha', 'Ticker'])

        # 4. Separación de carteras
        abiertas = df[df['Estado'] == 'ABIERTA'].copy()
        cerradas = df[df['Estado'] == 'CERRADA'].copy()

        # --- MÉTRICAS SUPERIORES (USAN EL NETO REAL) ---
        if not abiertas.empty:
            total_inv = abiertas['Inversión'].sum()
            total_val = abiertas['Valor Actual'].sum()
            total_comis = abiertas['Comisiones'].sum()
            
            # P&L Neto real (incluye comisiones)
            pnl_neto_real = (total_val - total_inv) - total_comis
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("CAPITAL INVERTIDO", f"${total_inv:,.2f}")
            with c2:
                st.metric("VALOR MERCADO", f"${total_val:,.2f}")
            with c3:
                # Delta muestra el beneficio real monetario
                st.metric("P&L REAL (NETO)", f"${pnl_neto_real:,.2f}")

        st.write("---")

        # --- TABLA PRINCIPAL (POSICIONES ACTIVAS) ---
        st.subheader("🚀 Posiciones Activas")
        if not abiertas.empty:
            # Mostramos el rendimiento 'Puro' (P&L Terminal %) que pediste
            cols_vista = ['Fecha', 'Ticker', 'Precio Compra', 'Precio Actual', 'P&L Terminal (%)', 'Comentarios']
            
            # Formateo visual
            st.dataframe(
                abiertas[cols_vista].sort_values(by='Fecha', ascending=False)
                .style.applymap(lambda x: f"color: {'#00ffad' if x >= 0 else '#f23645'}", subset=['P&L Terminal (%)'])
                .format({
                    'Precio Compra': '${:.2f}', 
                    'Precio Actual': '${:.2f}', 
                    'P&L Terminal (%)': '{:.2f}%',
                    'Fecha': lambda x: x.strftime('%d/%m/%Y')
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay posiciones abiertas detectadas. Revisa que el Estado sea 'ABIERTA' en el Sheet.")

        # --- SECCIÓN DE ACTIVIDAD RECIENTE (ÚLTIMOS 5) ---
        st.write("---")
        st.subheader("🕒 Actividad Reciente")
        col_izq, col_der = st.columns(2)

        with col_izq:
            st.markdown("##### 📥 Últimas 5 Entradas")
            if not abiertas.empty:
                ult_compras = abiertas.sort_values(by='Fecha', ascending=False).head(5).copy()
                ult_compras['Fecha_str'] = ult_compras['Fecha'].dt.strftime('%d/%m/%Y')
                st.table(ult_compras[['Fecha_str', 'Ticker', 'Precio Compra']].rename(columns={'Fecha_str': 'Fecha'}))
            else:
                st.caption("Sin datos.")

        with col_der:
            st.markdown("##### 📤 Últimas 5 Salidas")
            if not cerradas.empty:
                ult_ventas = cerradas.sort_values(by='Fecha', ascending=False).head(5).copy()
                ult_ventas['Fecha_str'] = ult_ventas['Fecha'].dt.strftime('%d/%m/%Y')
                # Mostramos P&L Terminal % y comentarios en las salidas
                st.table(ult_ventas[['Fecha_str', 'Ticker', 'P&L Terminal (%)', 'Comentarios']].rename(columns={'Fecha_str': 'Fecha'}))
            else:
                st.caption("Sin datos registrados en 'CERRADA'.")

    except Exception as e:
        st.error(f"⚠️ Error al sincronizar la cartera: {e}")
        st.info("Consejo: Verifica que el enlace en Secrets termine en 'output=csv' y que el Sheet tenga las columnas correctas.")
