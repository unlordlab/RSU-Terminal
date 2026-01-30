import streamlit as st
import pandas as pd
import numpy as np

def render():
    st.title("💼 Cartera Estratégica RSU")
    
    try:
        url = st.secrets["URL_CARTERA"]
        # Cargamos los datos
        df = pd.read_csv(f"{url}&cache_bus={pd.Timestamp.now().timestamp()}").dropna(how='all')
        df.columns = [c.strip() for c in df.columns]

        # 1. FUNCIÓN DE LIMPIEZA NUMÉRICA (Maneja comas de Google Sheets)
        def clean_numeric(value):
            if pd.isna(value): return 0.0
            val_str = str(value).strip().replace('$', '').replace('%', '').replace(' ', '')
            # Si el formato es europeo (1.234,56), quitamos el punto de miles y cambiamos coma por punto
            if ',' in val_str:
                val_str = val_str.replace('.', '').replace(',', '.')
            try:
                return float(val_str)
            except:
                return 0.0

        # Aplicamos la limpieza a todas las columnas de dinero y %
        cols_to_fix = ['Precio Compra', 'Precio Actual', 'P&L Terminal (%)', 'Inversión', 'Valor Actual', 'Comisiones']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        # 2. RE-CÁLCULO DE SEGURIDAD (Si el sheet manda 0, lo calculamos aquí)
        # Calculamos el P&L Terminal (%) si llega vacío o en 0
        df['P&L Terminal (%)'] = df.apply(
            lambda x: ((x['Precio Actual'] - x['Precio Compra']) / x['Precio Compra'] * 100) 
            if x['Precio Compra'] != 0 else 0, axis=1
        )

        # 3. Normalización de Texto
        df['Estado'] = df['Estado'].astype(str).str.strip().str.upper()
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
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
            
            st.dataframe(
                abiertas[cols_vista].sort_values(by='Fecha', ascending=False)
                .style.map(lambda x: f"color: {'#00ffad' if x >= 0 else '#f23645'}", subset=['P&L Terminal (%)'])
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
                ult_compras['Fecha_F'] = ult_compras['Fecha'].dt.strftime('%d/%m/%Y')
                st.table(ult_compras[['Fecha_F', 'Ticker', 'Precio Compra']].rename(columns={'Fecha_F': 'Fecha'}))

        with col_der:
            st.markdown("##### 📤 Últimas 5 Salidas")
            if not cerradas.empty:
                ult_ventas = cerradas.sort_values(by='Fecha', ascending=False).head(5).copy()
                ult_ventas['Fecha_F'] = ult_ventas['Fecha'].dt.strftime('%d/%m/%Y')
                st.table(ult_ventas[['Fecha_F', 'Ticker', 'P&L Terminal (%)', 'Comentarios']].rename(columns={'Fecha_F': 'Fecha'}))

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
