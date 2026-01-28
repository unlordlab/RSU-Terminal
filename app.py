import streamlit as st
import yfinance as yf
import google.generativeai as genai
import os
import random

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="RSU Terminal Pro", page_icon="📊", layout="wide")

# --- 2. ESTILO DARK TERMINAL (CSS AVANZADO) ---
st.markdown("""
    <style>
    .stApp { background-color: #0c0e12; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2d3439; }
    
    /* Tarjetas de Métricas */
    .metric-card {
        background-color: #151921;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2d3439;
        margin-bottom: 10px;
    }
    .metric-title { color: #848e9c; font-size: 0.8rem; font-weight: bold; text-transform: uppercase; }
    .metric-value { color: #ffffff; font-size: 1.4rem; font-weight: bold; }
    .metric-delta-pos { color: #00c087; font-size: 0.9rem; }
    .metric-delta-neg { color: #f23645; font-size: 0.9rem; }
    
    /* Botones y UI */
    .stButton>button {
        background: linear-gradient(45deg, #2962ff, #7000ff);
        color: white; border: none; border-radius: 4px;
        font-weight: 600; width: 100%; transition: 0.2s;
    }
    .stButton>button:hover { box-shadow: 0px 0px 10px #2962ff; }
    
    /* Contenedor del Reporte IA */
    .prompt-container {
        background-color: #151921;
        border-left: 4px solid #2962ff;
        padding: 20px;
        border-radius: 4px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONFIGURACIÓN IA (MODO SEGURO - SECRETS) ---
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

# --- 4. SEGURIDAD ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<h2 style='text-align:center;'>RSU TERMINAL ACCESS</h2>", unsafe_allow_html=True)
        pw = st.text_input("Clave Maestra:", type="password")
        if st.button("DESBLOQUEAR"):
            if pw == "RSU2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Acceso Denegado")
    st.stop()

# --- 5. DASHBOARD LAYOUT ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=150)
    st.markdown("### ⚙️ CONFIGURACIÓN")
    ticker = st.text_input("SYMBOL", value="NVDA").upper()
    
    if os.path.exists("formacion"):
        archivos = [f for f in os.listdir("formacion") if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if archivos:
            st.write("---")
            st.subheader("🎓 Píldora RSU")
            st.image(os.path.join("formacion", random.choice(archivos)), use_container_width=True)

# Fila Superior de Índices (Visual)
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown('<div class="metric-card"><p class="metric-title">S&P 500</p><p class="metric-value">4,890.97</p><p class="metric-delta-pos">▲ +0.45%</p></div>', unsafe_allow_html=True)
with c2: st.markdown('<div class="metric-card"><p class="metric-title">NASDAQ 100</p><p class="metric-value">17,510.58</p><p class="metric-delta-pos">▲ +0.82%</p></div>', unsafe_allow_html=True)
with c3: st.markdown('<div class="metric-card"><p class="metric-title">VIX Index</p><p class="metric-value">13.45</p><p class="metric-delta-neg">▼ -2.10%</p></div>', unsafe_allow_html=True)
with c4: st.markdown('<div class="metric-card"><p class="metric-title">FEAR & GREED</p><p class="metric-value">64</p><p style="color:#ffa500;">GREED</p></div>', unsafe_allow_html=True)

# --- 6. EJECUCIÓN PRINCIPAL ---
st.title(f"📊 Terminal RSU: {ticker}")

if st.button(f"EJECUTAR PROMPT RSU"):
    if error_msg:
        st.error(f"Error de conexión: {error_msg}")
    else:
        with st.spinner(f"Analizando catalizadores para {ticker}..."):
            try:
                # Datos de Mercado
                stock = yf.Ticker(ticker)
                price = stock.fast_info['last_price']
                
                st.markdown(f'<div class="metric-card" style="border-left: 5px solid #2962ff;">'
                            f'<p class="metric-title">{ticker} LAST PRICE</p>'
                            f'<p class="metric-value" style="font-size: 2.2rem;">{price:.2f} USD</p>'
                            f'</div>', unsafe_allow_html=True)
                
                # Prompt RSU Estructurado 
                prompt_rsu = f"""
                Analitza [TICKER]: {ticker} (Preu: {price}) de manera concisa i organitzada:
                1. Empresa per a 12 anys: 3 punts breus i analogia.[cite: 1]
                2. Resum professional: sector, productes, competidors (tickers), mètriques, moat i unicitat.[cite: 2]
                3. Taula: Temes candents, narrativa, catalitzadors i dades fonamentals.[cite: 3, 4]
                4. Taula de notícies (3 mesos): Data, Tipus, Resum i Enllaç directo. Marca esdeveniments que hagin mogut el preu.[cite: 5, 6, 7]
                5. Insiders: compres/vendes recents i institucional.
                6. Comparativa: Moviment respecte a competidors i tendència del sector (últim mes).[cite: 9]
                7. Propers catalitzadors: esdeveniments en els propers 30 dies.[cite: 10]
                8. Analistes: Canvis en preus objectiu recents. Dona format de taules on sigui possible.[cite: 11, 12]
                
                Centra't en catalitzadors (beneficis, guidance, insiders) que causin grans moviments.[cite: 14, 15]
                """
                
                response = model.generate_content(prompt_rsu)
                st.markdown('<div class="prompt-container">', unsafe_allow_html=True)
                st.markdown("## 🤖 Prompt RSU Report")
                st.markdown(response.text)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error en el análisis de {ticker}: {e}")

st.write("---")
st.caption(f"RSU Project 2026 | Engine: {modelo_nombre} | Market Data: Yahoo Finance")
