# modules/rsu_algoritmo.py
import streamlit as st
import pandas as pd
import pandas_ta as ta
import plotly.express as px
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestBarRequest
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY

class RSUAlgoritmo:
    def __init__(self):
        self.df = pd.DataFrame(columns=['close', 'volume'])
        self.estado_actual = "CALIBRANDO"
        self.puntos_necesarios = 20 # Mínimo para RSI estable

    def procesar_dato(self, precio, volumen):
        nuevo_dato = pd.DataFrame([{'close': precio, 'volume': volumen}])
        self.df = pd.concat([self.df, nuevo_dato], ignore_index=True)
        
        if len(self.df) > 300:
            self.df = self.df.iloc[-300:].reset_index(drop=True)
            
        if len(self.df) < self.puntos_necesarios:
            return "CALIBRANDO"
            
        return self.calcular_logica()

    def calcular_logica(self):
        # Cálculos Técnicos
        self.df['rsi'] = ta.rsi(self.df['close'], length=14)
        rsi_actual = self.df['rsi'].iloc[-1]
        sma_200 = self.df['close'].rolling(window=min(len(self.df), 200)).mean().iloc[-1]
        precio_actual = self.df['close'].iloc[-1]
        
        # Lógica CHoCH (Ruptura de máximo de 5 velas)
        max_reciente = self.df['close'].iloc[-6:-1].max()
        choch_alcista = precio_actual > max_reciente

        # Determinación de color
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
        # Cliente de Datos Alpaca
        client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        request_params = StockLatestBarRequest(symbol_or_symbols="SPY")
        latest_bar = client.get_stock_latest_bar(request_params)
        
        precio = latest_bar["SPY"].close
        volumen = latest_bar["SPY"].volume
        
        # Procesar dato en el motor de sesión
        engine = st.session_state.algoritmo_engine
        estado = engine.procesar_dato(precio, volumen)
        
        # --- UI: BARRA DE PROGRESO DE CALIBRACIÓN ---
        puntos_actuales = len(engine.df)
        if estado == "CALIBRANDO":
            progreso = puntos_actuales / engine.puntos_necesarios
            st.write(f"⚙️ Calibrando motor: {puntos_actuales}/{engine.puntos_necesarios} datos")
            st.progress(min(progreso, 1.0))
        
        # --- UI: SEMÁFORO ---
        luz_r = "luz-on" if estado == "ROJO" else ""
        luz_a = "luz-on" if estado == "AMBAR" else ""
        luz_v = "luz-on" if estado == "VERDE" else ""

        st.markdown(f"""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px; background: #11141a; border-radius: 20px; border: 1px solid #2962ff; margin-bottom: 25px;">
                <div style="display: flex; gap: 30px;">
                    <div class="semaforo-luz luz-roja {luz_r}" style="width: 70px; height: 70px;"></div>
                    <div class="semaforo-luz luz-ambar {luz_a}" style="width: 70px; height: 70px;"></div>
                    <div class="semaforo-luz luz-verde {luz_v}" style="width: 70px; height: 70px;"></div>
                </div>
                <div style="margin-top: 25px; text-align: center;">
                    <h1 style="color: white; font-size: 42px; margin: 0;">{estado}</h1>
                    <p style="color: #00ffad; font-size: 20px; font-weight: bold; margin-top: 5px;">${precio:.2f}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- UI: GRÁFICA DE MONITOREO ---
        if puntos_actuales > 1:
            fig = px.line(engine.df, y="close", title="Seguimiento de Precio (Tick-by-Tick)",
                         color_discrete_sequence=["#2962ff"])
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="white",
                height=300,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

        if st.button("🔄 Forzar Tick"):
            st.rerun()

    except Exception as e:
        st.error(f"Error en la señal: {e}")
