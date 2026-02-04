# modules/rsu_algoritmo.py
import streamlit as st
import pandas as pd
import yfinance as yf
import sys
import os

# Agregar el directorio padre al path para importar config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import set_style

def calcular_rsi(prices, period=14):
    """Calcula RSI manualmente"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def obtener_datos_spy():
    """Obtiene RSI y precio de SPY"""
    try:
        ticker = yf.Ticker("SPY")
        df = ticker.history(interval="1wk", period="6mo")
        
        if df.empty or len(df) < 14:
            return None, None
        
        df['rsi'] = calcular_rsi(df['Close'])
        rsi_val = float(df['rsi'].iloc[-1])
        precio_val = float(df['Close'].iloc[-1])
        
        return rsi_val, precio_val
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None

def calcular_color(rsi):
    if rsi < 30:
        return "VERDE"
    elif rsi > 70:
        return "ROJO"
    else:
        return "AMBAR"

def render():
    set_style()
    
    st.title("🤖 RSU ALGORITMO - SEMÁFORO")
    st.info("Estrategia basada exclusivamente en el RSI Semanal del S&P 500 (SPY).")
    
    with st.spinner('Calculando...'):
        rsi_val, precio_val = obtener_datos_spy()
    
    if rsi_val is None:
        st.error("Error al obtener datos. Intenta recargar.")
        if st.button("🔄 Recargar"):
            st.rerun()
        return
    
    # Determinar color
    estado = calcular_color(rsi_val)
    luz_r = "luz-on" if estado == "ROJO" else ""
    luz_a = "luz-on" if estado == "AMBAR" else ""
    luz_v = "luz-on" if estado == "VERDE" else ""
    
    # Mostrar semáforo
    st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 50px; background: #11141a; border-radius: 20px; border: 1px solid #2962ff;">
            <div style="display: flex; gap: 30px;">
                <div class="semaforo-luz luz-roja {luz_r}" style="width: 80px; height: 80px;"></div>
                <div class="semaforo-luz luz-ambar {luz_a}" style="width: 80px; height: 80px;"></div>
                <div class="semaforo-luz luz-verde {luz_v}" style="width: 80px; height: 80px;"></div>
            </div>
            <div style="margin-top: 30px; text-align: center;">
                <h1 style="color: white; font-size: 48px; margin: 0;">{estado}</h1>
                <p style="color: #888; font-size: 18px; margin-top: 10px;">
                    RSI: <span style="color:#2962ff;">{rsi_val:.2f}</span> | Precio: ${precio_val:.2f}
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    col1, col2, col3 = st.columns(3)
    col1.error("🔴 RSI > 70: Riesgo")
    col2.warning("🟡 RSI 30-70: Neutral")
    col3.success("🟢 RSI < 30: Oportunidad")

    if st.button("🔄 Forzar Recálculo"):
        st.rerun()
