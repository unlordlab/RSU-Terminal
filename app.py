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

# --- 2. CONFIGURACIÓN IA (MODO SEGURO) ---
# Intentamos leer la clave desde los Secrets de Streamlit (Nube) 
# o desde una variable local (PC)
API_KEY = st.secrets.get("GEMINI_API_KEY")

def conectar_ia():
    if not API_KEY:
        return None, None, "No se encontró la API KEY en los Secrets."
    try:
        genai.configure(api_key=API_KEY)
        modelos_disponibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        seleccionado = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos_disponibles else modelos_disponibles[0]
        return genai.GenerativeModel(seleccionado), seleccionado, None
    except Exception as e:
        return None, None, str(e)

model, modelo_nombre, error_msg = conectar_ia()

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

if st.button(f"EJECUTAR IA"):
    if error_msg:
        st.error(f"Error de conexión: {error_msg}")
    else:
        with st.spinner(f"Ejecutando Prompt RSU para {ticker}..."):
            try:
                stock = yf.Ticker(ticker)
                val = stock.fast_info['last_price']
                st.markdown(f"<div class='price-card'><h3>Precio Actual: {val:.2f} USD</h3></div>", unsafe_allow_html=True)
                
                # Basado en la metodología de catalizadores RSU [cite: 1, 14, 15]
                prompt_rsu = f"""
                Analitza [TICKER]: {ticker} (Preu: {val}) de manera concisa i organitzada:
                1. Empresa per a 12 anys: 3 punts i analogia[cite: 1].
                2. Resum professional: sector, productes, competidors (tickers), avantatge (moat)[cite: 2].
                3. Taula: Temes candents, narrativa, catalitzadors i dades fonamentals[cite: 3, 4].
                4. Taula de notícies (3 mesos): Data, Tipus, Resum i Enllaç[cite: 5, 6, 7].
                5. Insiders i institucional[cite: 8].
                6. Comparativa sectorial (últim mes)[cite: 9].
                7. Catalitzadors propers (30 dies)[cite: 10].
                8. Canvis en preus objectiu d'analistes[cite: 11].
                """
                
                response = model.generate_content(prompt_rsu)
                st.markdown("## 🤖 Prompt RSU")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Error en el análisis: {e}")

st.caption(f"RSU Project 2026 | Motor: {modelo_nombre}")
