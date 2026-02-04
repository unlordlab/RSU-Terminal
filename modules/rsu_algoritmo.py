# modules/rsu_algoritmo.py
import streamlit as st
import pandas as pd
import yfinance as yf
import sys
import os

# Agregar el directorio padre al path para importar config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import set_style

class RSUAlgoritmo:
    def __init__(self):
        self.estado_actual = "CALIBRANDO"

    def calcular_rsi_manual(self, prices, period=14):
        """
        Calcula RSI manualmente sin pandas_ta
        RSI = 100 - (100 / (1 + RS))
        RS = Media Ganancias / Media Pérdidas
        """
        try:
            # Calcular diferencias
            delta = prices.diff()
            
            # Separar ganancias y pérdidas
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # Calcular media móvil exponencial
            avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
            avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
            
            # Calcular RS y RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            st.error(f"Error en cálculo RSI manual: {e}")
            return None

    def obtener_rsi_semanal(self):
        try:
            st.info("Descargando datos de SPY...")
            ticker = yf.Ticker("SPY")
            df = ticker.history(interval="1wk", period="1y")
            
            if df.empty:
                st.error("DataFrame vacío")
                return None, None
            
            if len(df) < 14:
                st.error(f"Datos insuficientes: {len(df)} semanas (necesita 14+)")
                return None, None
            
            # Calcular RSI manualmente
            df['rsi'] = self.calcular_rsi_manual(df['Close'], 14)
            
            if df['rsi'] is None:
                st.error("RSI es None")
                return None, None
            
            if df['rsi'].isna().all():
                st.error("RSI calculado es todo NaN")
                return None, None
            
            rsi_actual = df['rsi'].iloc[-1]
            precio_actual = df['Close'].iloc[-1]
            
            # Verificar que no sean NaN
            if pd.isna(rsi_actual) or pd.isna(precio_actual):
                st.error("RSI o Precio es NaN")
                return None, None
            
            return float(rsi_actual), float(precio_actual)
            
        except Exception as e:
            st.error(f"Error en obtener_rsi_semanal: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None, None

    def calcular_color(self, rsi):
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
    
    # Verificación de seguridad por si no se inicializó en app.py
    if 'algoritmo_engine' not in st.session_state:
        st.session_state.algoritmo_engine = RSUAlgoritmo()
        
    engine = st.session_state.algoritmo_engine
    
    rsi_semanal = None
    precio = None
    
    with st.spinner('Calculando RSI Semanal...'):
        try:
            rsi_semanal, precio = engine.obtener_rsi_semanal()
        except Exception as e:
            st.error(f"Error al obtener RSI: {e}")
            import traceback
            st.code(traceback.format_exc())
        
    if rsi_semanal is not None and precio is not None:
        estado = engine.calcular_color(rsi_semanal)
        
        # Estas clases coinciden con tu config.py
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
        
        st.write("---")
        st.write("**Parámetros de la estrategia:**")
        col1, col2, col3 = st.columns(3)
        col1.error("🔴 RSI > 70: Riesgo Alto")
        col2.warning("🟡 RSI 30-70: Neutral")
        col3.success("🟢 RSI < 30: Oportunidad")
        
    else:
        st.error("No se pudieron recuperar los datos. Posibles causas:")
        st.markdown("""
        - Problema de conexión con Yahoo Finance
        - Datos insuficientes (menos de 14 semanas)
        - Error en el cálculo del RSI
        
        **Intenta recargar la página o verifica tu conexión a internet.**
        """)

    if st.button("🔄 Forzar Recálculo"):
        st.rerun()
