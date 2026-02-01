# modules/rsu_algoritmo.py
import streamlit as st
import pandas as pd
import pandas_ta as ta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestBarRequest
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY

class RSUAlgoritmo:
    def __init__(self):
        self.df = pd.DataFrame(columns=['close', 'volume'])
        self.estado_actual = "CALIBRANDO"

    def procesar_dato(self, precio, volumen):
        nuevo_dato = pd.DataFrame([{'close': precio, 'volume': volumen}])
        self.df = pd.concat([self.df, nuevo_dato], ignore_index=True)
        if len(self.df) > 300:
            self.df = self.df.iloc[-300:].reset_index(drop=True)
        if len(self.df) < 20:
            return "CALIBRANDO"
        return self.calcular_logica()

    def calcular_logica(self):
        self.df['rsi'] = ta.rsi(self.df['close'], length=14)
        rsi_actual = self.df['rsi'].iloc[-1]
        sma_200 = self.df['close'].rolling(window=min(len(self.df), 200)).mean().iloc[-1]
        precio_actual = self.df['close'].iloc[-1]
        
        max_reciente = self.df['close'].iloc[-6:-1].max()
        choch_alcista = precio_actual > max_reciente

        if precio_actual > sma_200 and rsi_actual > 35 and choch_alcista:
            self.estado_actual = "VERDE"
        elif rsi_actual < 35:
            self.estado_actual = "AMBAR"
        elif precio_actual < sma_200 or rsi_actual > 70:
            self.estado_actual = "ROJO"
        
        return self.estado_actual

def render():
    st.title("🤖 RSU ALGORITMO - SEMÁFORO")
    
    try:
        # Nueva forma de conectar con alpaca-py
        client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        request_params = StockLatestBarRequest(symbol_or_symbols="SPY")
        latest_bar = client.get_stock_latest_bar(request_params)
        
        precio = latest_bar["SPY"].close
        volumen = latest_bar["SPY"].volume
        
        estado = st.session_state.algoritmo_engine.procesar_dato(precio, volumen)
        
        # Lógica de luces
        luz_r = "luz-on" if estado == "ROJO" else ""
        luz_a = "luz-on" if estado == "AMBAR" else ""
        luz_v = "luz-on" if estado == "VERDE" else ""

        st.markdown(f"""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 50px; background: #11141a; border-radius: 20px; border: 1px solid #2962ff; margin-top: 20px;">
                <div style="display: flex; gap: 30px;">
                    <div class="semaforo-luz luz-roja {luz_r}" style="width: 80px; height: 80px;"></div>
                    <div class="semaforo-luz luz-ambar {luz_a}" style="width: 80px; height: 80px;"></div>
                    <div class="semaforo-luz luz-verde {luz_v}" style="width: 80px; height: 80px;"></div>
                </div>
                <div style="margin-top: 30px; text-align: center;">
                    <h1 style="color: white; font-size: 48px; margin: 0;">{estado}</h1>
                    <p style="color: #888; font-size: 18px;">Precio SPY: ${precio:.2f} | Vol: {int(volumen)}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Actualizar"):
            st.rerun()

    except Exception as e:
        st.error(f"Error en la conexión de datos: {e}")
