# modules/rsu_algoritmo.py
import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf

class RSUAlgoritmo:
    def __init__(self):
        self.estado_actual = "CALIBRANDO"

    def obtener_rsi_semanal(self):
        try:
            # Descargamos datos semanales del SPY (últimos 2 años para asegurar el RSI)
            ticker = yf.Ticker("SPY")
            df = ticker.history(interval="1wk", period="2y")
            
            if df.empty or len(df) < 14:
                return None, None
            
            # Calculamos RSI de 14 periodos sobre el cierre semanal
            df['rsi'] = ta.rsi(df['Close'], length=14)
            rsi_actual = df['rsi'].iloc[-1]
            precio_actual = df['Close'].iloc[-1]
            
            return rsi_actual, precio_actual
        except:
            return None, None

    def calcular_color(self, rsi):
        # Lógica solicitada:
        # < 30 (Sobreventa) -> VERDE
        # 30 - 70 -> AMBAR
        # > 70 (Sobrecompra) -> ROJO
        if rsi < 30:
            return "VERDE"
        elif rsi > 70:
            return "ROJO"
        else:
            return "AMBAR"

def render():
    st.title("🤖 RSU ALGORITMO - SEMÁFORO")
    st.info("Estrategia basada exclusivamente en el RSI Semanal del S&P 500 (SPY).")
    
    # Usamos el motor de la sesión
    engine = st.session_state.algoritmo_engine
    
    with st.spinner('Calculando RSI Semanal...'):
        rsi_semanal, precio = engine.obtener_rsi_semanal()
        
    if rsi_semanal is not None:
        estado = engine.calcular_color(rsi_semanal)
        
        # Lógica de luces para el HTML
        luz_r = "luz-on" if estado == "ROJO" else ""
        luz_a = "luz-on" if estado == "AMBAR" else ""
        luz_v = "luz-on" if estado == "VERDE" else ""

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
                        RSI Semanal: <span style="color:#2962ff;">{rsi_semanal:.2f}</span> | Precio: ${precio:.2f}
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Comparativa visual
        st.write("---")
        st.write("**Parámetros de la estrategia:**")
        col1, col2, col3 = st.columns(3)
        col1.error("🔴 RSI > 70: Riesgo Alto")
        col2.warning("🟡 RSI 30-70: Neutral")
        col3.success("🟢 RSI < 30: Oportunidad")
        
    else:
        st.error("No se pudieron recuperar los datos de Yahoo Finance. Reintenta en unos instantes.")

    if st.button("🔄 Forzar Recálculo"):
        st.rerun()

