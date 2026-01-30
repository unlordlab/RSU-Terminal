import streamlit as st
import pandas as pd

def render():
    st.title("💼 Cartera Estratégica RSU")
    
    try:
        url = st.secrets["URL_CARTERA"]
        df = pd.read_csv(f"{url}&cache_bus={pd.Timestamp.now().timestamp()}")
        df.columns = [c.strip() for c in df.columns]
        
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        abiertas = df[df['Estado'] == 'ABIERTA'].copy()
        cerradas = df[df['Estado'] == 'CERRADA'].copy()

        # --- MÉTRICAS SUPERIORES ---
        if not abiertas.empty:
            total_inv = abiertas['Inversión'].sum()
            total_val = abiertas['Valor Actual'].sum()
            
            # Aquí seguimos usando el Neto para que tu dinero total sea real
            pnl_real_abs = (total_val - total_inv) - abiertas['Comisiones'].sum()
            
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("CAPITAL INVERTIDO", f"${total_inv:,.2f}")
            with c2: st.metric("VALOR MERCADO", f"${total_val:,.2f}")
            with c3: st.metric("P&L REAL (NETO)", f"${pnl_real_abs:,.2f}")

        st.write("---")

        # --- TABLA MAESTRA (Usando la columna Bruta de la Terminal) ---
        st.subheader("🚀 Posiciones Activas")
        if not abiertas.empty:
            # USAMOS 'P&L Terminal (%)' que no tiene comisiones
            cols_vista = ['Fecha', 'Ticker', 'Precio Compra', 'Precio Actual', 'P&L Terminal (%)', 'Comentarios']
            
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

        # --- ACTIVIDAD RECIENTE ---
        st.write("---")
        st.subheader("🕒 Actividad Reciente")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 📥 Últimas Entradas")
            st.table(abiertas.sort_values(by='Fecha', ascending=False).head(5)[['Fecha', 'Ticker', 'Precio Compra']].assign(Fecha=lambda x: x['Fecha'].dt.strftime('%d/%m/%Y')))
        with col2:
            st.markdown("##### 📤 Últimas Salidas")
            # En salidas también mostramos el P&L Terminal para coherencia
            st.table(cerradas.sort_values(by='Fecha', ascending=False).head(5)[['Fecha', 'Ticker', 'P&L Terminal (%)', 'Comentarios']].assign(Fecha=lambda x: x['Fecha'].dt.strftime('%d/%m/%Y')))

    except Exception as e:
        st.error(f"Error: {e}")

