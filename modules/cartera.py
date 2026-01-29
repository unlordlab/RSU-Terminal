# modules/cartera.py (VERSIÓN QUE SÍ FUNCIONA)
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

@st.cache_data(ttl=120)
def load_cartera():
    """Carga datos desde Google Sheet público"""
    try:
        sheet_id = st.secrets.get("SHEET_ID", "1XjUEjniArxZ-6RkKIf6YKo96SA0IdAf9_wT68HSzAEo")
        url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Cartera%20RSU'
        
        # Headers para evitar bloqueos
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        df = pd.read_csv(url, headers=headers)
        return df
    except Exception as e:
        st.warning("🔄 No se pudo cargar el Sheet. Usando datos demo...")
        # DATOS DE PRUEBA
        return pd.DataFrame({
            'Timestamp': ['2026-01-29 16:00', '2026-01-28 14:30', '2026-01-27 10:15'],
            'Ticker': ['NVDA', 'TSLA', 'AAPL'],
            'Shares': [15, -8, 25],
            'Precio_Compra': [145.50, 420.00, 185.00],
            'Status': ['OPEN', 'CLOSED', 'OPEN']
        })

def render():
    st.subheader("💼 CARTERA RSU")
    
    # Cargar datos
    df = load_cartera()
    
    # Precios reales con yfinance
    for ticker in df['Ticker']:
        try:
            precio = yf.Ticker(ticker).fast_info['last_price']
            df.loc[df['Ticker'] == ticker, 'Precio_Actual'] = precio
        except:
            df.loc[df['Ticker'] == ticker, 'Precio_Actual'] = df.loc[df['Ticker'] == ticker, 'Precio_Compra'].iloc[0]
    
    # Cálculos automáticos
    df['PnL_$'] = (df['Precio_Actual'] - df['Precio_Compra']) * df['Shares']
    df['PnL_%'] = ((df['Precio_Actual'] - df['Precio_Compra']) / df['Precio_Compra']) * 100
    df['Valor'] = abs(df['Shares']) * df['Precio_Actual']
    df['Peso_%'] = (df['Valor'] / df['Valor'].sum() * 100).round(2)
    
    # Métricas resumen
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total PnL", f"${df['PnL_$'].sum():,.0f}")
    with col2:
        st.metric("Posiciones", len(df[df['Status']=='OPEN']))
    with col3:
        st.metric("Valor Total", f"${df['Valor'].sum():,.0f}")
    with col4:
        win_rate = len(df[df['PnL_$']>0])/len(df)*100
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    # Tabla principal
    df_display = df[['Ticker', 'Shares', 'Precio_Actual', 'PnL_$', 'PnL_%', 'Peso_%', 'Status']].copy()
    st.dataframe(df_display, use_container_width=True)

