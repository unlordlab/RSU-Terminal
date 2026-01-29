# modules/cartera.py (versión SIMPLE con SHEET_ID público)
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

@st.cache_data(ttl=120)
def load_cartera():
    sheet_id = st.secrets["SHEET_ID"]
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Cartera%20RSU"
    return pd.read_csv(url)

def render():
    st.subheader("💼 CARTERA RSU")
    
    df = load_cartera()
    
    # Precios reales
    for ticker in df['Ticker']:
        try:
            precio = yf.Ticker(ticker).fast_info['last_price']
            df.loc[df['Ticker']==ticker, 'Precio_Actual'] = precio
        except:
            pass
    
    # Cálculos
    df['PnL_$'] = (df['Precio_Actual'] - df['Precio_Compra']) * df['Shares']
    df['PnL_%'] = ((df['Precio_Actual'] - df['Precio_Compra']) / df['Precio_Compra']) * 100
    df['Valor'] = abs(df['Shares']) * df['Precio_Actual']
    df['Peso_%'] = (df['Valor'] / df['Valor'].sum() * 100).round(2)
    
    # Métricas totales
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total PnL", f"${df['PnL_$'].sum():,.0f}")
    with col2: st.metric("Posiciones", len(df[df['Status']=='OPEN']))
    with col3: st.metric("Valor Total", f"${df['Valor'].sum():,.0f}")
    
    # Tabla principal
    st.dataframe(df[['Ticker','Shares','PnL_$','PnL_%','Peso_%','Status']], 
                use_container_width=True)
