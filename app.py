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
                Analitza [TICKER]: {ticker} (Preu: {price})$ de manera concisa i organitzada:
                1. Explica a què es dedica l'empresa com si tingués 12 anys: tres punts breus sobre el que fa i qualsevol exemple o analogia útil amb la qual em pugui identificar.
                2. Resum professional (màxim 10 frases): sector, productes/serveis principals, competidors primaris (llista els tickers), mètriques o fites destacables, avantatge competitiu/fossat (moat), per què són únics i, si es tracta d'una biotecnològica, indica si tenen un producte comercial o estan en fases clíniques.
                3. En una taula, proporciona el següent:
                - Qualsevol tema candent, narrativa o història de l'acció.
                - Qualsevol catalitzador (resultats, notícies, macro).
                - Qualsevol dada fonamental significativa (gran creixement en beneficis o ingressos, fossat, producte o servei únic, gestió superior, patents, etc.).
                4. Mostra totes les principals notícies/esdeveniments dels últims 3 mesos: Utilitza una taula per a:
                - Data (AAAA-MM-DD).
                - Tipus d'esdeveniment (Resultats, Llançament de producte, Millora/Degradació d'analistes, etc.).
                - Resum breu (màxim 1-2 frases).
                - Enllaç directe a la font.
                - Marca qualsevol esdeveniment important que hagi mogut el preu (resultats sorpresa, canvi significatiu en les previsions/guidance, accions d'analistes de primer nivell).
                5. Esmenta qualsevol compra/venda recent d'insiders o presentacions institucionals si estan visibles.
                6. Resumeix com es mou l'acció en comparació amb els seus competidors principals i la tendència general del sector en l'últim mes (pujada/baixada).
                7. Senyala els propers catalitzadors (resultats, llançaments de productes, esdeveniments regulatoris) en els propers 30 dies.
                8. Anota qualsevol canvi en els preus objectiu dels analistes per a aquest ticker durant el període esmentat. Dona-li un format de fàcil revisió. Si és possible, utilitza taules per als esdeveniments i els moviments dels parells del sector. Respon amb un estil clar, concís i fàcil de llegir per utilitzar-lo en decisions d'inversió.
                
                En general, centra't en les raons per les quals l'acció pot fer un gran moviment en el futur: beneficis, vendes, previsions (guidance), llançaments de productes, millores/degradacions d'analistes, compres d'insiders (especialment del CEO/Fundador i de l'equip executiu), associacions i catalitzadors del sector o de notícies. Vull centrar-me en accions amb catalitzadors i temàtiques, ja que els catalitzadors són la causa dels grans moviments al mercat de valors.
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



