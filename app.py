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
                
                response = model.generate_content(prompt_rsu)
                st.markdown("## 🤖 Prompt RSU")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Error en el análisis: {e}")

st.caption(f"RSU Project 2026 | Motor: {modelo_nombre}")