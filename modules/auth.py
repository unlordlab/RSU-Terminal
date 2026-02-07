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

    # CSS - CENTRADO Y SIMÉTRICO SIN CAJAS EXTRA
    st.markdown("""
    <style>
        /* Ocultar elementos de Streamlit */
        #MainMenu, footer, header {visibility: hidden;}
        
        /* Fondo */
        .stApp {background: #0c0e12;}
        
        /* Centrar todo */
        .main {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 90vh;
        }
        
        /* Contenedor del login */
        div[data-testid="stVerticalBlock"] {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 16px;
            padding: 40px 50px;
            max-width: 450px;
            width: 100%;
            margin: 0 auto;
        }
        
        /* Logo */
        .logo-img {
            width: 140px;
            height: 140px;
            border-radius: 20px;
            margin: 0 auto 20px;
            display: block;
            box-shadow: 0 15px 40px rgba(0, 255, 173, 0.25);
        }
        
        /* Títulos */
        h1 {
            color: white !important;
            font-size: 1.9rem !important;
            text-align: center !important;
            letter-spacing: 4px !important;
            margin-bottom: 10px !important;
        }
        
        h3 {
            color: #00ffad !important;
            font-size: 1rem !important;
            text-align: center !important;
            margin-bottom: 30px !important;
            font-weight: normal !important;
        }
        
        /* Label centrado */
        label {
            color: #888 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
            text-align: center !important;
            display: block !important;
            width: 100% !important;
        }
        
        /* Centrar el contenedor del label */
        .stMarkdown p {
            text-align: center !important;
            color: #888 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
            margin-bottom: 10px !important;
        }
        
        /* Input */
        .stTextInput > div > div > input {
            background: #0c0e12 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 10px !important;
            color: white !important;
            height: 50px !important;
            font-size: 15px !important;
        }
        
        /* OCULTAR OJO DE STREAMLIT */
        .stTextInput [data-testid="stIcon"] {
            display: none !important;
        }
        
        /* Contenedor del botón - CENTRADO CON MARGEN */
        div[data-testid="stButton"] {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            margin-top: 25px !important;
        }
        
        /* Botón principal - CENTRADO Y MÁS PEQUEÑO */
        .stButton > button {
            background: linear-gradient(90deg, #00ffad, #00d4aa) !important;
            color: #0c0e12 !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            letter-spacing: 2px !important;
            width: auto !important;
            min-width: 220px !important;
            height: 48px !important;
            padding: 0 25px !important;
            margin: 0 auto !important;
        }
        
        /* OCULTAR BORDES DE COLUMNAS */
        div[data-testid="stHorizontalBlock"] {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        
        div[data-testid="column"] {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        
        /* Footer */
        .footer-text {
            text-align: center;
            color: #00ffad;
            font-size: 11px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #1a1e26;
        }
        
        .footer-text span {
            color: #555;
            font-size: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

    logo_b64 = get_logo_base64()

    # LOGO
    if logo_b64:
        st.markdown(f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">', unsafe_allow_html=True)
    else:
        st.markdown('<div style="width:140px;height:140px;margin:0 auto 20px;background:linear-gradient(135deg,#00ffad,#00a8e8);border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:4rem;">🔐</div>', unsafe_allow_html=True)
    
    # TÍTULOS
    st.markdown("<h1>RSU TERMINAL</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Sistema de Acceso Seguro</h3>", unsafe_allow_html=True)
    
    # CONTRASEÑA - LABEL CENTRADO
    st.markdown('<p style="text-align:center;color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Contraseña de Acceso</p>', unsafe_allow_html=True)
    
    # Input de contraseña
    password = st.text_input(
        "",
        type="password",
        placeholder="Ingrese contraseña",
        label_visibility="collapsed"
    )
    
    # BOTÓN ACCESO CENTRADO CON HTML
    button_clicked = st.button("🔓 DESBLOQUEAR TERMINAL")
    
    if button_clicked:
        if not password:
            st.error("⚠️ Ingrese una contraseña")
        else:
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            real_pwd = st.secrets.get("APP_PASSWORD")
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
    st.markdown('<div class="footer-text">🔒 CONEXIÓN SEGURA SSL<br><span>© 2026 RSU Terminal v2.0</span></div>', unsafe_allow_html=True)

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
