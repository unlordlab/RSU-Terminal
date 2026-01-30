import streamlit as st
import pandas as pd

def render():
    st.title("💼 Cartera Estratégica RSU")
    
    try:
        url = st.secrets["URL_CARTERA"]
        # Carreguem dades i eliminem files buides
        df = pd.read_csv(f"{url}&cache_bus={pd.Timestamp.now().timestamp()}").dropna(how='all')
        
        # Neteja de columnes
        df.columns = [c.strip() for c in df.columns]

        # Validació de seguretat
        if 'Fecha' not in df.columns:
            st.error("L'enllaç encara no retorna la columna 'Fecha'. Assegura't de publicar com a CSV.")
            return

        # Conversió de dades
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha'])

        abiertas = df[df['Estado'] == 'ABIERTA'].copy()
        cerradas = df[df['Estado'] == 'CERRADA'].copy()

        # --- MÉTRIQUES ---
        if not abiertas.empty:
            total_inv = abiertas['Inversión'].sum()
            total_val = abiertas['Valor Actual'].sum()
            pnl_neto_real = (total_val - total_inv) - abiertas['Comisiones'].sum()
            
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("CAPITAL INVERTIT", f"${total_inv:,.2f}")
            with c2: st.metric("VALOR MERCAT", f"${total_val:,.2f}")
            with c3: st.metric("P&L REAL (NET)", f"${pnl_neto_real:,.2f}")

        st.write("---")

        # --- TAULA PRINCIPAL (Rendiment Pur) ---
        st.subheader("🚀 Posicions Actives")
        if not abiertas.empty:
            cols_vista = ['Fecha', 'Ticker', 'Precio Compra', 'Precio Actual', 'P&L Terminal (%)', 'Comentarios']
            st.dataframe(
                abiertas[cols_vista].sort_values(by='Fecha', ascending=False)
                .style.applymap(lambda x: f"color: {'#00ffad' if x >= 0 else '#f23645'}", subset=['P&L Terminal (%)'])
                .format({
                    'Precio Compra': '${:.2f}', 'Precio Actual': '${:.2f}', 
                    'P&L Terminal (%)': '{:.2f}%', 'Fecha': lambda x: x.strftime('%d/%m/%Y')
                }),
                use_container_width=True, hide_index=True
            )

        # --- ACTIVITAT RECENT ---
        st.write("---")
        st.subheader("🕒 Activitat Recient")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 📥 Últimes Entrades")
            if not abiertas.empty:
                st.table(abiertas.sort_values(by='Fecha', ascending=False).head(5)[['Fecha', 'Ticker', 'Precio Compra']].assign(Fecha=lambda x: x['Fecha'].dt.strftime('%d/%m/%Y')))
        with col2:
            st.markdown("##### 📤 Últimes Salides")
            if not cerradas.empty:
                st.table(cerradas.sort_values(by='Fecha', ascending=False).head(5)[['Fecha', 'Ticker', 'P&L Terminal (%)', 'Comentarios']].assign(Fecha=lambda x: x['Fecha'].dt.strftime('%d/%m/%Y')))

    except Exception as e:
        st.error(f"Error: {e}")
