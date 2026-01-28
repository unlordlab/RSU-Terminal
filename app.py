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
    
    /* Contenedores estilo Dashboard */
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
        background-color: #2962ff;
        color: white; border: none; border-radius: 4px;
        font-weight: 600; width: 100%; transition: 0.2s;
    }
    .stButton>button:hover { background-color: #1e4bd8; border: none; }
    
    /* Texto IA */
    .prompt-container {
        background-color: #151921;
        border-left: 4px solid #2962ff;
        padding: 20px;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONFIGURACIÓN IA (SECRETS) ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

def conectar_ia():
    if not API_KEY: return None, None
    try:
        genai.configure(api_key=API_KEY)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        return genai.GenerativeModel(sel), sel
    except: return None, None

model, modelo_nombre = conectar_ia()

# --- 4. SEGURIDAD ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<h2 style='text-align:center;'>RSU TERMINAL LOGIN</h2>", unsafe_allow_html=True)
        pw = st.text_input("Access Key", type="password")
        if st.button("CONNECT"):
            if pw == "RSU2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Access Denied")
    st.stop()

# --- 5. DASHBOARD LAYOUT ---
with st.sidebar:
    st.markdown("### 🛠️ CONTROL PANEL")
    ticker = st.text_input("SYMBOL", value="NVDA").upper()
    st.write("---")
    if os.path.exists("formacion"):
        imgs = [f for f in os.listdir("formacion") if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if imgs:
            st.image(os.path.join("formacion", random.choice(imgs)), caption="RSU Education", use_container_width=True)

# Fila Superior: Indices Rápidos (Simulados como en tu imagen)
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown('<div class="metric-card"><p class="metric-title">S&P 500</p><p class="metric-value">4,890.97</p><p class="metric-delta-pos">▲ +0.45%</p></div>', unsafe_allow_html=True)
with c2: st.markdown('<div class="metric-card"><p class="metric-title">NASDAQ 100</p><p class="metric-value">17,510.58</p><p class="metric-delta-pos">▲ +0.82%</p></div>', unsafe_allow_html=True)
with c3: st.markdown('<div class="metric-card"><p class="metric-title">VIX</p><p class="metric-value">13.45</p><p class="metric-delta-neg">▼ -2.10%</p></div>', unsafe_allow_html=True)
with c4: st.markdown('<div class="metric-card"><p class="metric-title">FEAR & GREED</p><p class="metric-value">64</p><p style="color: #ffa500;">GREED</p></div>', unsafe_allow_html=True)

# Sección Principal
st.write("##")
if st.button(f"RUN PROMPT RSU: {ticker}"):
    with st.spinner("Analyzing Market Catalysts..."):
        try:
            data = yf.Ticker(ticker)
            price = data.fast_info['last_price']
            
            # Layout de resultados IA
            st.markdown(f'<div class="metric-card" style="border-left: 5px solid #2962ff;">'
                        f'<p class="metric-title">{ticker} CURRENT PRICE</p>'
                        f'<p class="metric-value" style="font-size: 2.5rem;">{price:.2f} USD</p>'
                        f'</div>', unsafe_allow_html=True)
            
            # PROMPT RSU 
            prompt_final = f"""
            Analitza {ticker} basant-te en la metodologia RSU (Preu actual: {price}):
            1. Explicació per a 12 anys (3 punts i analogia)[cite: 1].
            2. Resum Professional (màxim 10 frases): sector, productes, competidors (tickers) i fossat (moat)[cite: 2].
            3. TAULA: Narrativa/Temes candents, Catalitzadors i Fonamentals[cite: 3, 4].
            4. TAULA NOTÍCIES (3 mesos): Data, Tipus, Resum i Enllaç[cite: 5, 6, 7].
            5. Insiders i Moviments Institucionals[cite: 8].
            6. Comparativa sectorial (últim mes)[cite: 9].
            7. Catalitzadors propers (30 dies)[cite: 10].
            8. Canvis en Target Price d'analistes[cite: 11].
            Enfoca't en per què l'acció pot fer un gran moviment[cite: 14, 15].
            """
            
            if model:
                response = model.generate_content(prompt_final)
                st.markdown('<div class="prompt-container">', unsafe_allow_html=True)
                st.markdown("### 🤖 PROMPT RSU REPORT")
                st.markdown(response.text)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("IA Engine Offline. Check Secrets.")
                
        except Exception as e:
            st.error(f"Error fetching {ticker}: {e}")

st.write("---")
st.caption(f"Terminal RSU v0.1 | Market Data via Yahoo Finance | Engine: {modelo_nombre}")
