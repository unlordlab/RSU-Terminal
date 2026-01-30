
# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import yfinance as yf

# Configuración de página única (se llama una sola vez)
if 'page_config_set' not in st.session_state:
    st.set_page_config(page_title="RSU Terminal", layout="wide", page_icon="📊")
    st.session_state.page_config_set = True

def set_style():
    """
    Define los estilos CSS globales para la aplicación.
    Se han ajustado los contenedores para asegurar que el contenido 
    se mantenga dentro de las cajas oscuras.
    """
    st.markdown("""
        <style>
        /* Fondo general y barra lateral */
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* Contenedores del Dashboard */
        .group-container {
            background-color: #11141a; 
            border: 1px solid #2d3439;
            border-radius: 12px; 
            padding: 0px; 
            height: 100%;
            overflow: hidden;
            margin-bottom: 20px;
        }
        
        /* Cabecera con título DENTRO de la caja */
        .group-header {
            background-color: #1a1e26;
            padding: 12px 20px;
            border-bottom: 1px solid #2d3439;
        }
        
        .group-title { 
            color: #888; 
            font-size: 12px; 
            font-weight: bold; 
            text-transform: uppercase; 
            letter-spacing: 1px;
            margin: 0 !important;
        }

        /* Espaciado del contenido interno */
        .group-content { padding: 20px; }

        /* Tarjetas de Índices */
        .index-card {
            background-color: #1a1e26; 
            border: 1px solid #2d3439; 
            border-radius: 8px;
            padding: 12px 15px; 
            margin-bottom: 10px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
        }
        .index-ticker { color: white; font-weight: bold; font-size: 14px; margin: 0; }
        .index-fullname { color: #555; font-size: 10px; margin: 0; text-transform: uppercase; }
        .index-price { font-weight: bold; font-size: 16px; color: white; margin: 0; }
        .index-delta { font-size: 11px; border-radius: 4px; padding: 2px 6px; font-weight: bold; }
        .pos { background-color: rgba(0, 255, 173, 0.1); color: #00ffad; }
        .neg { background-color: rgba(242, 54, 69, 0.1); color: #f23645; }
        
        .prompt-container { 
            background-color: #1a1e26; 
            border-left: 5px solid #2962ff; 
            padding: 20px; 
            border-radius: 5px; 
            white-space: pre-wrap; 
        }
        </style>
        """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_market_index(ticker_symbol):
    """
    Obtiene el precio y cambio porcentual de un índice.
    Se ha ampliado el periodo a 7 días para evitar errores de datos en fines de semana
    y se ha validado el precio 'live' para evitar valores en 0.00.
    """
    try:
        t = yf.Ticker(ticker_symbol)
        # Ampliamos el histórico para asegurar datos previos válidos
        hist = t.history(period="7d")
        if not hist.empty:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            
            # Intentar capturar precio en vivo solo si es un valor positivo real
            try:
                live = t.fast_info.last_price
                if live and live > 0: 
                    current = live
            except: 
                pass
                
            change = ((current - prev) / prev) * 100
            return current, change
        return 0.0, 0.0
    except: 
        return 0.0, 0.0

@st.cache_data(ttl=3600)
def get_cnn_fear_greed():
    """Obtiene el índice Fear & Greed de CNN Business."""
    try:
        r = requests.get("https://edition.cnn.com/markets/fear-and-greed")
        soup = BeautifulSoup(r.text, 'html.parser')
        val = soup.find("span", class_="market-fng-gauge__dial-number-value")
        return int(val.text.strip()) if val else 50
    except: 
        return 50

# --- CONFIGURACIÓN DE INTELIGENCIA ARTIFICIAL ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

@st.cache_resource
def get_ia_model():
    """Configura y devuelve el modelo de IA Gemini."""
    if not API_KEY: return None, None, "API Key missing"
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model, "Gemini 1.5 Flash", None

@st.cache_data(ttl=600)
def obtener_prompt_github():
    """Descarga el prompt base desde GitHub para el reporte de IA."""
    try:
        r = requests.get("https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/prompt_report.txt")
        return r.text if r.status_code == 200 else ""
    except: 
        return ""
