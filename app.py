import streamlit as st
import yfinance as yf
import google.generativeai as genai
import os
import random

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="RSU Terminal Pro", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stSidebar"] { background-color: #1a1c24; border-right: 1px solid #00f2ff; }
    .stButton>button { background: linear-gradient(45deg, #00f2ff, #7000ff); color: white; border: none; font-weight: bold; width: 100%; }
    .price-card { background: #1a1c24; padding: 20px; border-radius: 10px; border-left: 5px solid #00f2ff; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN IA ---
# Clave extraída de tus capturas
API_KEY = "TU_CLAVE_AQUI_SOLO_EN_LOCAL"

def conectar_ia():
    try:
        genai.configure(api_key=API_KEY)
        modelos_disponibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        seleccionado = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos_disponibles else modelos_disponibles[0]
        return genai.GenerativeModel(seleccionado), seleccionado
    except:
        return None, None

model, modelo_nombre = conectar_ia()

# --- 3. LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if os.path.exists("logo.png"): st.image("logo.png")
        st.title("🛡️ Acceso RSU")
        pw = st.text_input("Clave:", type="password")
        if st.button("ENTRAR"):
            if pw == "RSU2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Clave Incorrecta")
    st.stop()

# --- 4. DASHBOARD ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=150)
    ticker = st.text_input("ACTIVO A ANALIZAR:", value="NVDA").upper()
    
    if os.path.exists("formacion"):
        archivos = [f for f in os.listdir("formacion") if f.endswith(('.png', '.jpg', '.jpeg'))]
        if archivos:
            st.write("---")
            st.subheader("🎓 Formación RSU")
            st.image(os.path.join("formacion", random.choice(archivos)), use_container_width=True)

st.title(f"📊 Terminal RSU: {ticker}")
st.caption(f"Motor activo: {modelo_nombre}")

if st.button(f"EJECUTAR IA"):
    with st.spinner(f"Ejecutando Prompt RSU para {ticker}..."):
        try:
            # Obtener datos básicos de precio
            stock = yf.Ticker(ticker)
            val = stock.fast_info['last_price']
            st.markdown(f"<div class='price-card'><h3>Precio Actual: {val:.2f} USD</h3></div>", unsafe_allow_html=True)
            
            # --- DEFINICIÓN DEL PROMPT RSU ---
            # Este prompt utiliza las instrucciones exactas de tu archivo [cite: 1-15]
            prompt_rsu = f"""
            Analiza el ticker {ticker} siguiendo estrictamente esta estructura:
            
            1. Explica a qué se dedica la empresa como si tuviera 12 años (3 puntos breves y analogía)[cite: 1].
            2. Resumen profesional (máximo 10 frases): sector, productos, competidores (tickers), métricas y ventaja competitiva (moat)[cite: 2].
            3. Tabla con: Temas candentes/narrativa, Catalizadores y Datos fundamentales significativos[cite: 3, 4].
            4. Tabla de principales noticias/eventos de los últimos 3 meses (Fecha, Tipo, Resumen, Enlace)[cite: 5, 6, 7].
            5. Menciona compras/ventas de insiders recientes[cite: 8].
            6. Resumen comparativo con competidores y tendencia del sector en el último mes[cite: 9].
            7. Catalizadores próximos en los siguientes 30 días[cite: 10].
            8. Cambios en precios objetivo de analistas recientemente[cite: 11].
            
            Utiliza un estilo claro, conciso y profesional, enfocado en catalizadores que muevan el precio[cite: 13, 14, 15].
            """
            
            if model:
                response = model.generate_content(prompt_rsu)
                st.markdown("## 🤖 Prompt RSU")
                st.markdown(response.text)
            else:
                st.error("Error: No se pudo conectar con el cerebro de la IA.")
                
        except Exception as e:
            st.error(f"Error al analizar {ticker}: {e}")

st.write("---")
st.caption("RSU Finanz-AI Pro | Basado en metodología de catalizadores y fundamentales.")