import streamlit as st
import yfinance as yf
import google.generativeai as genai
import os
import random

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="RSU Terminal Pro", page_icon="💎", layout="wide")

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
            prompt_rsu = f"""
                Analitza [TICKER]: {ticker} (Preu: {price})$ de manera concisa i organitzada:
                1. Explica a què es dedica l'empresa com si tingués 12 anys: tres punts breus sobre el que fa i qualsevol exemple o analogia útil amb la qual em pugui identificar.[cite: 1].
                2. Resum professional (màxim 10 frases): sector, productes/serveis principals, competidors primaris (llista els tickers), mètriques o fites destacables, avantatge competitiu/fossat (moat), per què són únics i, si es tracta d'una biotecnològica, indica si tenen un producte comercial o estan en fases clíniques.[cite: 2].
                3. En una taula, proporciona el següent:
                - Qualsevol tema candent, narrativa o història de l'acció.
                - Qualsevol catalitzador (resultats, notícies, macro).
                - Qualsevol dada fonamental significativa (gran creixement en beneficis o ingressos, fossat, producte o servei únic, gestió superior, patents, etc.).
                [cite: 3, 4].
                4. Mostra totes les principals notícies/esdeveniments dels últims 3 mesos: Utilitza una taula per a:
                - Data (AAAA-MM-DD).
                - Tipus d'esdeveniment (Resultats, Llançament de producte, Millora/Degradació d'analistes, etc.).
                - Resum breu (màxim 1-2 frases).
                - Enllaç directe a la font.
                - Marca qualsevol esdeveniment important que hagi mogut el preu (resultats sorpresa, canvi significatiu en les previsions/guidance, accions d'analistes de primer nivell).[cite: 5, 6, 7].
                5. Esmenta qualsevol compra/venda recent d'insiders o presentacions institucionals si estan visibles.[cite: 8].
                6. Resumeix com es mou l'acció en comparació amb els seus competidors principals i la tendència general del sector en l'últim mes (pujada/baixada).[cite: 9].
                7. Senyala els propers catalitzadors (resultats, llançaments de productes, esdeveniments regulatoris) en els propers 30 dies.[cite: 10].
                8. Anota qualsevol canvi en els preus objectiu dels analistes per a aquest ticker durant el període esmentat. Dona-li un format de fàcil revisió. Si és possible, utilitza taules per als esdeveniments i els moviments dels parells del sector. Respon amb un estil clar, concís i fàcil de llegir per utilitzar-lo en decisions d'inversió.[cite: 11].
                n general, centra't en les raons per les quals l'acció pot fer un gran moviment en el futur: beneficis, vendes, previsions (guidance), llançaments de productes, millores/degradacions d'analistes, compres d'insiders (especialment del CEO/Fundador i de l'equip executiu), associacions i catalitzadors del sector o de notícies. Vull centrar-me en accions amb catalitzadors i temàtiques, ja que els catalitzadors són la causa dels grans moviments al mercat de valors.
                """
          
            if model:
                response = model.generate_content(prompt_rsu)
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



