# modules/cartera.py
import streamlit as st
import pandas as pd
import yfinance as yf

@st.cache_data(ttl=120)
def load_cartera():
    sheet_id = "1XjUEjniArxZ-6RkKIf6YKo96SA0IdAf9_wT68HSzAEo"
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Cartera%20RSU'
    
    try:
        df = pd.read_csv(url)
        st.success(f"✅ Cartera cargada: {len(df)} posiciones")
        return df
    except:
        st.warning("🔄 Sheet no accesible. Datos demo:")
        return pd.DataFrame({
            'Timestamp': ['2026-01-29'],
            'Ticker': ['NVDA', 'TSLA'],
            'Shares': [15, -8],
            'Precio_Compra': [145.50, 420.00]
        })

def render():
    st.subheader("💼 CARTERA RSU")
    
    df = load_cartera()
    
    # Precios reales
    for i, ticker in enumerate(df['Ticker']):
        try:
            precio = yf.Ticker(ticker).fast_info['last_price']
            df.at[i, 'Precio_Actual'] = precio
        except:
            df.at[i, 'Precio_Actual'] = df.at[i, 'Precio_Compra']
    
    # Cálculos
    df['PnL_$'] = (df['Precio_Actual'] - df['Precio_Compra']) * df['Shares']
    df['PnL_%'] = ((df['Precio_Actual'] - df['Precio_Compra']) / df['Precio_Compra']) * 100
    df['Peso_%'] = abs(df['PnL_$']) / abs(df['PnL_$']).sum() * 100
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total PnL", f"${df['PnL_$'].sum():,.0f}")
    with col2: st.metric("Posiciones", len(df))
    with col3: st.metric("Win Rate", f"{len(df[df['PnL_$']>0])/len(df)*100:.0f}%")
    
    st.dataframe(df[['Ticker','Shares','PnL_$','PnL_%','Peso_%']], use_container_width=True)
