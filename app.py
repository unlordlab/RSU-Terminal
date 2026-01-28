import streamlit as st
import yfinance as yf
import google.generativeai as genai
import os
import random

# --- 1. CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="RSU Terminal Pro", page_icon="📊", layout="wide")

# --- 2. ESTILO DARK TERMINAL (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0c0e12; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2d3439; }
    
    .metric-card {
        background-color: #151921;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2d3439;
        margin-bottom: 10px;
    }
    .metric-title { color: #848e9c; font-size: 0.8rem; font-weight: bold; text-transform: uppercase; }
    .metric-value { color: #ffffff; font-size: 1.4rem; font-weight: bold; }
    
    .stButton>button {
        background: linear-gradient(45deg, #2962ff, #7000ff);
        color: white; border: none; border-radius: 4px;
        font-weight: 600; width: 100%; transition: 0.2s;
    }
    .prompt-container {
        background-color: #151921;
        border-left: 4px solid #2962ff;
        padding: 20px;
        border-radius: 4px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONFIGURACIÓ IA (SECRETS) ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

def conectar_ia():
    if not API_KEY: return None, None, "Falta API KEY en Secrets"
    try:
        genai.configure(api_key=API_KEY)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        return genai.GenerativeModel(sel), sel, None
    except Exception as e: return None, None, str(e)

model, modelo_nombre, error_msg = conectar_ia()

# --- 4. LOGIN AMB LOGO ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.write("#")
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        
        st.markdown("<h3 style='text-align:center;'>RSU TERMINAL</h3>", unsafe_allow_html=True)
        pw = st.text_input("Access Key", type="password", placeholder="Introdueix la clau...")
        if st.button("CONNECT SYSTEM"):
            if pw == "RSU2026":
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Accés Denegat")
    st.stop()

# --- 5. FUNCIÓ MILLORA: ÍNDEXS EN TEMPS REAL ---
def get_market_index(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol)
        info = data.fast_info
        price = info['last_price']
        prev_close = info['previous_close']
        change = ((price - prev_close) / prev_close) * 100
        return price, change
    except:
        return 0.0, 0.0

# --- 6. DASHBOARD LAYOUT ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    st.markdown("### ⚙️ CONTROL")
    ticker = st.text_input("SYMBOL", value="NVDA").upper()
    st.write("---")
    
    if os.path.exists("formacion"):
        archivos = [f for f in os.listdir("formacion") if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if archivos:
            st.image(os.path.join("formacion", random.choice(archivos)), caption="RSU Píldora", use_container_width=True)

# Capçalera amb Logo i Títol
head_col1, head_col2 = st.columns([0.1, 0.9])
with head_col1:
    if os.path.exists("logo.png"): st.image("logo.png", width=60)
with head_col2:
    st.title(f"Terminal RSU: {ticker}")

# Índexs Ràpids (MILLORATS AMB DADES REALS)
sp_p, sp_c = get_market_index("^GSPC")
ndx_p, ndx_c = get_market_index("^IXIC")
vix_p, vix_c = get_market_index("^VIX")

c1, c2, c3, c4 = st.columns(4)
with c1:
    color = "#00c087" if sp_c >= 0 else "#f23645"
    st.markdown(f'<div class="metric-card"><p class="metric-title">S&P 500</p><p class="metric-value">{sp_p:,.2f}</p><p style="color:{color}">{"▲" if sp_c >= 0 else "▼"} {sp_c:.2f}%</p></div>', unsafe_allow_html=True)
with c2:
    color = "#00c087" if ndx_c >= 0 else "#f23645"
    st.markdown(f'<div class="metric-card"><p class="metric-title">NASDAQ 100</p><p class="metric-value">{ndx_p:,.2f}</p><p style="color:{color}">{"▲" if ndx_c >= 0 else "▼"} {ndx_c:.2f}%</p></div>', unsafe_allow_html=True)
with c3:
    # En el VIX el rojo suele ser cuando sube (miedo)
    color = "#f23645" if vix_c >= 0 else "#00c087"
    st.markdown(f'<div class="metric-card"><p class="metric-title">VIX Index</p><p class="metric-value">{vix_p:.2f}</p><p style="color:{color}">{"▲" if vix_c >= 0 else "▼"} {vix_c:.2f}%</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="metric-card"><p class="metric-title">FEAR & GREED</p><p class="metric-value">64</p><p style="color:#ffa500;">GREED</p></div>', unsafe_allow_html=True)

# --- 7. ACCIÓ PRINCIPAL ---
if st.button(f"EJECUTAR PROMPT RSU"):
    if error_msg:
        st.error(f"Error: {error_msg}")
    else:
        with st.spinner(f"Analitzant catalitzadors per a {ticker}..."):
            try:
                # Obtenció de dades reals
                stock = yf.Ticker(ticker)
                price = stock.fast_info['last_price']
                
                st.markdown(f'<div class="metric-card" style="border-left: 5px solid #2962ff;">'
                            f'<p class="metric-title">{ticker} LAST PRICE</p>'
                            f'<p class="metric-value" style="font-size: 2rem;">{price:.2f} USD</p>'
                            f'</div>', unsafe_allow_html=True)
                
                prompt_rsu = f"""
                Analitza [TICKER]: {ticker} (Preu: {price}) de manera concisa i organitzada:
                1. Explica a què es dedica l'empresa com si tingués 12 anys: tres punts breus i analogia.
                2. Resum professional (màx 10 frases): sector, productes, competidors (tickers), moat i per què són únics.
                3. Taula: Temes candents/narrativa, catalitzadors i dades fonamentals significatives.
                4. Taula de notícies (3 mesos): Data, Tipus, Resum i Enllaç. Marca els esdeveniments que hagin mogut el preu.
                5. Insiders i compres/vendes recents.
                6. Comparativa sectorial de l'últim mes.
                7. Propers catalitzadors (30 dies).
                8. Canvis en Target Price d'analistes.
                
                Centra't en catalitzadors (beneficis, guidance, insiders) que causin grans moviments al mercat.
                """
                
                response = model.generate_content(prompt_rsu)
                st.markdown('<div class="prompt-container">', unsafe_allow_html=True)
                st.markdown("### 🤖 PROMPT RSU REPORT")
                st.markdown(response.text)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error en el sistema: {e}")

st.write("---")
st.caption(f"RSU Project 2026 | Market Data via Yahoo Finance | Engine: {modelo_nombre}")


