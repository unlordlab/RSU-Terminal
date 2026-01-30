import streamlit as st
import pandas as pd

def render():
    st.title("💼 Cartera Estratégica RSU")
    
    try:
        url = st.secrets["URL_CARTERA"]
        df = pd.read_csv(f"{url}&cache_bus={pd.Timestamp.now().timestamp()}").dropna(how='all')
        df.columns = [c.strip() for c in df.columns]

        # 1. Normalización de Texto
        for col in ['Estado', 'Ticker']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()

        # 2. LIMPIEZA NUMÉRICA (Evita el error 'f' for 'str')
        # Forzamos a que estas columnas sean números, si hay texto lo convierte en 0 o NaN
        cols_numericas = ['Precio Compra', 'Precio Actual', 'P&L Terminal (%)', 'Inversión', 'Valor Actual', 'Comisiones']
        for col in cols_numericas:
            if col in df.columns:
                # Convertimos a string, quitamos símbolos de moneda y pasamos a numérico
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('[$,%]', '', regex=True), errors='coerce').fillna(0)

        # 3. Conversión de Fecha
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha', 'Ticker'])

        # 4. Separación de carteras
        abiertas = df[df['Estado'] == 'ABIERTA'].copy()
        cerradas = df[df['Estado'] == 'CERRADA'].copy()

        # --- MÉTRICAS ---
        if not abiertas.empty:
            total_inv = abiertas['Inversión'].sum()
            total_val = abiertas['Valor Actual'].sum()
            total_comis = abiertas['Comisiones'].sum()
            pnl_neto_real = (total_val - total_inv) - total_comis
            
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("CAPITAL INVERTIDO", f"${total_inv:,.2f}")
            with c2: st.metric("VALOR MERCADO", f"${total_val:,.2f}")
            with c3: st.metric("P&L REAL (NETO)", f"${pnl_neto_real:,.2f}")

        st.write("---")

        # --- TABLA PRINCIPAL ---
        st.subheader("🚀 Posiciones Activas")
        if not abiertas.empty:
            cols_vista = ['Fecha', 'Ticker', 'Precio Compra', 'Precio Actual', 'P&L Terminal (%)', 'Comentarios']
            
            # Aplicamos formato asegurando que los datos son numéricos
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
        col_izq, col_der = st.columns(2)

        with col_izq:
            st.markdown("##### 📥 Últimas 5 Entradas")
            if not abiertas.empty:
                ult_compras = abiertas.sort_values(by='Fecha', ascending=False).head(5).copy()
                ult_compras['Fecha'] = ult_compras['Fecha'].dt.strftime('%d/%m/%Y')
                st.table(ult_compras[['Fecha', 'Ticker', 'Precio Compra']])

        with col_der:
            st.markdown("##### 📤 Últimas 5 Salidas")
            if not cerradas.empty:
                ult_ventas = cerradas.sort_values(by='Fecha', ascending=False).head(5).copy()
                ult_ventas['Fecha'] = ult_ventas['Fecha'].dt.strftime('%d/%m/%Y')
                st.table(ult_ventas[['Fecha', 'Ticker', 'P&L Terminal (%)', 'Comentarios']])

    except Exception as e:
        st.error(f"⚠️ Error al sincronizar la cartera: {e}")
