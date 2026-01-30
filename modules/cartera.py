import streamlit as st
import pandas as pd

def render():
    st.title("💼 Cartera Estratégica RSU")
    
    try:
        url = st.secrets["URL_CARTERA"]
        # Forcem la lectura i eliminem files totalment buides que envia Google Sheets
        df = pd.read_csv(f"{url}&cache_bus={pd.Timestamp.now().timestamp()}").dropna(how='all')
        
        # Neteja extrema de noms de columnes
        df.columns = [c.strip() for c in df.columns]

        # VERIFICACIÓ: Si 'Fecha' no existeix, t'avisarà exactament de quines columnes veu
        if 'Fecha' not in df.columns:
            st.error(f"No trobo la columna 'Fecha'. Columnes detectades: {list(df.columns)}")
            return

        # Convertim Fecha gestionant errors (files buides es tornen NaT)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha']) # Eliminem si hi ha alguna data mal escrita

        # Separem estats
        abiertas = df[df['Estado'] == 'ABIERTA'].copy()
        cerradas = df[df['Estado'] == 'CERRADA'].copy()

        # --- MÉTRICAS SUPERIORES ---
        if not abiertas.empty:
            total_inv = abiertas['Inversión'].sum()
            total_val = abiertas['Valor Actual'].sum()
            total_comis = abiertas['Comisiones'].sum()
            pnl_real_abs = (total_val - total_inv) - total_comis
            
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("CAPITAL INVERTIDO", f"${total_inv:,.2f}")
            with c2: st.metric("VALOR MERCADO", f"${total_val:,.2f}")
            with c3: st.metric("P&L REAL (NETO)", f"${pnl_real_abs:,.2f}")

        st.write("---")

        # --- TABLA MAESTRA ---
        st.subheader("🚀 Posiciones Activas")
        if not abiertas.empty:
            cols_vista = ['Fecha', 'Ticker', 'Precio Compra', 'Precio Actual', 'P&L Terminal (%)', 'Comentarios']
            
            # Ordenem i formategem
            df_display = abiertas[cols_vista].sort_values(by='Fecha', ascending=False)
            
            st.dataframe(
                df_display.style.applymap(lambda x: f"color: {'#00ffad' if x >= 0 else '#f23645'}", subset=['P&L Terminal (%)'])
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
            if not abiertas.empty:
                ult_compras = abiertas.sort_values(by='Fecha', ascending=False).head(5).copy()
                ult_compras['Fecha'] = ult_compras['Fecha'].dt.strftime('%d/%m/%Y')
                st.table(ult_compras[['Fecha', 'Ticker', 'Precio Compra']])
            else:
                st.write("Sense dades.")

        with col2:
            st.markdown("##### 📤 Últimas Salidas")
            if not cerradas.empty:
                ult_ventas = cerradas.sort_values(by='Fecha', ascending=False).head(5).copy()
                ult_ventas['Fecha'] = ult_ventas['Fecha'].dt.strftime('%d/%m/%Y')
                st.table(ult_ventas[['Fecha', 'Ticker', 'P&L Terminal (%)', 'Comentarios']])
            else:
                st.write("Sense dades.")

    except Exception as e:
        st.error(f"Error detallat: {e}")
