
# modules/auth.py
import os
import streamlit as st
from datetime import datetime, timedelta
import hashlib
import time
import logging
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_logo_base64():
    try:
        if os.path.exists("assets/logo.png"):
            with open("assets/logo.png", "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return None

def login():
    # Inicialización
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
        st.session_state["login_attempts"] = 0
        st.session_state["lockout_time"] = None
        st.session_state["last_activity"] = None
        st.session_state["show_password"] = False
    
    # Verificar timeout
    if st.session_state["auth"] and st.session_state["last_activity"]:
        if datetime.now() - st.session_state["last_activity"] > timedelta(minutes=30):
            st.session_state["auth"] = False
            st.session_state["last_activity"] = None
            st.warning("⏱️ Sesión expirada")
            st.rerun()
    
    if st.session_state["auth"]:
        st.session_state["last_activity"] = datetime.now()
        return True

    # Verificar bloqueo
    if st.session_state["lockout_time"]:
        if datetime.now() < st.session_state["lockout_time"]:
            remaining = int((st.session_state["lockout_time"] - datetime.now()).total_seconds() / 60)
            st.error(f"⏱️ Cuenta bloqueada. Intente en {remaining} minutos")
            return False
        else:
            st.session_state["lockout_time"] = None
            st.session_state["login_attempts"] = 0

    # CSS CON !IMPORTANT EN TODO
    st.markdown("""
    <style>
        /* RESET TOTAL */
        #MainMenu, footer, header, .stDeployButton {display: none !important;}
        
        .stApp {
            background: #0c0e12 !important;
        }
        
        /* CONTENEDOR PRINCIPAL - CENTRADO */
        section.main > div {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 100vh !important;
            padding: 20px !important;
        }
        
        /* TARJETA LOGIN */
        section.main > div > div {
            background: #11141a !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 16px !important;
            padding: 40px 50px !important;
            max-width: 420px !important;
            width: 100% !important;
        }
        
        /* LOGO */
        .logo-img {
            width: 130px !important;
            height: 130px !important;
            border-radius: 20px !important;
            margin: 0 auto 20px !important;
            display: block !important;
            box-shadow: 0 10px 30px rgba(0, 255, 173, 0.2) !important;
        }
        
        /* TÍTULOS */
        h1 {
            color: white !important;
            font-size: 1.8rem !important;
            text-align: center !important;
            letter-spacing: 3px !important;
            margin: 0 0 10px 0 !important;
        }
        
        h3 {
            color: #00ffad !important;
            font-size: 0.95rem !important;
            text-align: center !important;
            margin: 0 0 30px 0 !important;
            font-weight: normal !important;
        }
        
        /* LABEL */
        p > strong {
            color: #888 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
        
        /* INPUT CONTAINER */
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            gap: 10px !important;
            align-items: flex-start !important;
        }
        
        /* INPUT - SIN OJO INTERNO */
        div[data-testid="stTextInput"] {
            flex: 1 !important;
        }
        
        div[data-testid="stTextInput"] > div {
            width: 100% !important;
        }
        
        div[data-testid="stTextInput"] input {
            background: #0c0e12 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 8px !important;
            color: white !important;
            height: 48px !important;
            font-size: 15px !important;
            width: 100% !important;
        }
        
        /* OCULTAR CUALQUIER OJO EN EL INPUT */
        div[data-testid="stTextInput"] button,
        div[data-testid="stTextInput"] [data-testid="stIcon"],
        div[data-testid="stTextInput"] svg,
        .stTextInput button,
        input[type="password"] + div,
        input[type="text"] + div {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            width: 0 !important;
            height: 0 !important;
        }
        
        /* BOTÓN OJO EXTERNO */
        div[data-testid="column"]:nth-of-type(2) {
            width: auto !important;
            flex: 0 0 50px !important;
        }
        
        div[data-testid="column"]:nth-of-type(2) > div {
            width: 100% !important;
        }
        
        div[data-testid="column"]:nth-of-type(2) button {
            background: #1a1e26 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 8px !important;
            color: #888 !important;
            width: 48px !important;
            height: 48px !important;
            margin: 24px 0 0 0 !important;
            padding: 0 !important;
            font-size: 1.1rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        div[data-testid="column"]:nth-of-type(2) button:hover {
            border-color: #00ffad !important;
            color: #00ffad !important;
        }
        
        /* BOTÓN PRINCIPAL */
        div[data-testid="stButton"] > button {
            background: linear-gradient(90deg, #00ffad, #00d4aa) !important;
            color: #0c0e12 !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            letter-spacing: 1.5px !important;
            width: 100% !important;
            height: 50px !important;
            margin-top: 15px !important;
        }
        
        /* FOOTER */
        .footer-box {
            text-align: center !important;
            margin-top: 30px !important;
            padding-top: 20px !important;
            border-top: 1px solid #1a1e26 !important;
            color: #00ffad !important;
            font-size: 11px !important;
        }
        
        .footer-box span {
            color: #555 !important;
            font-size: 10px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    logo_b64 = get_logo_base64()

    # LOGO
    if logo_b64:
        st.markdown(f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">', unsafe_allow_html=True)
    else:
        st.markdown('<div style="width:130px;height:130px;margin:0 auto 20px;background:linear-gradient(135deg,#00ffad,#00a8e8);border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:4rem;">🔐</div>', unsafe_allow_html=True)
    
    # TÍTULOS
    st.markdown("<h1>RSU TERMINAL</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Sistema de Acceso Seguro</h3>", unsafe_allow_html=True)
    
    # CONTRASEÑA
    st.markdown("<p><strong>Contraseña de Acceso</strong></p>", unsafe_allow_html=True)
    
    # Input + Botón ojo
    c1, c2 = st.columns([5, 1])
    
    with c1:
        password = st.text_input(
            "",
            type="text" if st.session_state["show_password"] else "password",
            placeholder="Ingrese su contraseña...",
            label_visibility="collapsed"
        )
    
    with c2:
        if st.button("👁️", key="eye_btn"):
            st.session_state["show_password"] = not st.session_state["show_password"]
            st.rerun()
    
    # BOTÓN ACCESO
    if st.button("🔓 DESBLOQUEAR TERMINAL"):
        if not password:
            st.error("⚠️ Ingrese una contraseña")
        else:
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            real_pwd = st.secrets.get("APP_PASSWORD", "RSU2026")
            real_hash = hashlib.sha256(real_pwd.encode()).hexdigest()
            
            if pwd_hash == real_hash:
                st.session_state["auth"] = True
                st.session_state["login_attempts"] = 0
                st.session_state["last_activity"] = datetime.now()
                st.success("✅ Acceso concedido")
                time.sleep(0.3)
                st.rerun()
            else:
                st.session_state["login_attempts"] += 1
                if st.session_state["login_attempts"] >= 5:
                    st.session_state["lockout_time"] = datetime.now() + timedelta(minutes=15)
                    st.error("⏱️ Bloqueado 15 minutos")
                else:
                    st.error("⚠️ Contraseña incorrecta")
                    if 5 - st.session_state["login_attempts"] <= 2:
                        st.warning(f"⚠️ {5 - st.session_state['login_attempts']} intentos restantes")
    
    # FOOTER
    st.markdown('<div class="footer-box">🔒 CONEXIÓN SEGURA SSL<br><span>© 2026 RSU Terminal v2.0</span></div>', unsafe_allow_html=True)

    return False


def logout():
    st.session_state["auth"] = False
    st.session_state["last_activity"] = None
    st.success("👋 Sesión cerrada")
    time.sleep(0.3)
    st.rerun()


def require_auth():
    if "auth" not in st.session_state or not st.session_state["auth"]:
        st.error("🔒 Acceso denegado")
        login()
        st.stop()
    st.session_state["last_activity"] = datetime.now()

