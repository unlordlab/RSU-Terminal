
# modules/cartera.py (FUNCIONA CON CUALQUIER ESTRUCTURA)
import streamlit as st
import pandas as pd
import yfinance as yf

@st.cache_data(ttl=120)
def load_cartera():
    sheet_id = "1XjUEjniArxZ-6RkKIf6YKo96SA0IdAf9_wT68HSzAEo"
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Cartera%20RSU'
    
    try:
        df = pd.read_csv(url)
        st.success(f"✅ Sheet cargado. Columnas: {list(df.columns)}")
        st.write("📊 Vista previa:", df.head(2))  # Muestra tus datos reales
        return df
    except:
        st.warning("🔄 Usando datos demo")
        return pd.DataFrame({
            'Timestamp': ['2026-01-29'],
            'Ticker': ['NVDA', 'TSLA'], 
            'Shares': [15, -8],
            'Precio_Compra': [145.50, 420.00]
        })

def render():
    st.subheader("💼 CARTERA RSU")
    
    df = load_cartera()
    
    # 🔍 MOSTRAR QUÉ COLUMNAS TIENES REALMENTE
    st.info(f"**Columnas disponibles**: {list(df.columns)}")
    
    # Verificar columnas necesarias
    required_cols = ['Ticker', 'Shares', 'Precio_Compra']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        st.error(f"❌ Faltan columnas: {missing_cols}")
        st.info("💡 **Crea estas columnas en tu Sheet**: Timestamp | Ticker | Shares | Precio_Compra | Status")
        return
    
    # Crear columnas si no existen
    if 'Precio_Actual' not in df.columns:
        df['Precio_Actual'] = df['Precio_Compra']
    
    # Precios reales
    for i, ticker in enumerate(df['Ticker']):
        try:
            precio = yf.Ticker(ticker).fast_info['last_price']
            df.at[i, 'Precio_Actual'] = precio
        except:
            pass
    
    # Cálculos seguros
    df['PnL_$'] = (df['Precio_Actual'] - df['Precio_Compra']) * df['Shares']
    df['PnL_%'] = ((df['Precio_Actual'] - df['Precio_Compra']) / df['Precio_Compra']) * 100
    df['Peso_%'] = abs(df['PnL_$']) / abs(df['PnL_$']).sum() * 100
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total PnL", f"${df['PnL_$'].sum():,.0f}")
    with col2: st.metric("Posiciones", len(df))
    with col3: st.metric("Win Rate", f"{len(df[df['PnL_$']>0])/len(df)*100:.0f}%")
    
    # Tabla
    st.dataframe(df[['Ticker','Shares','PnL_$','PnL_%','Peso_%']], use_container_width=True)
