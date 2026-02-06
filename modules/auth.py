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
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
        st.session_state["login_attempts"] = 0
        st.session_state["lockout_time"] = None
        st.session_state["last_activity"] = None
        st.session_state["show_password"] = False
    
    if st.session_state["auth"] and st.session_state["last_activity"]:
        if datetime.now() - st.session_state["last_activity"] > timedelta(minutes=30):
            st.session_state["auth"] = False
            st.session_state["last_activity"] = None
            st.warning("⏱️ Sesión expirada")
            st.rerun()
    
    if st.session_state["auth"]:
        st.session_state["last_activity"] = datetime.now()
        return True

    if st.session_state["lockout_time"]:
        if datetime.now() < st.session_state["lockout_time"]:
            remaining = int((st.session_state["lockout_time"] - datetime.now()).total_seconds() / 60)
            st.error(f"⏱️ Cuenta bloqueada. Intente en {remaining} minutos")
            return False
        else:
            st.session_state["lockout_time"] = None
            st.session_state["login_attempts"] = 0

    # CSS - ELIMINAR TODA BARRA SUPERIOR
    st.markdown("""
    <style>
        /* ELIMINAR BARRA SUPERIOR DE STREAMLIT */
        .stApp {
            margin-top: -100px !important;
        }
        
        header[data-testid="stHeader"],
        .stApp header,
        [data-testid="stHeader"] {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            visibility: hidden !important;
        }
        
        /* Espaciado cero en contenedores */
        .main > div:first-child,
        .block-container,
        [data-testid="stVerticalBlock"] {
            padding-top: 0 !important;
            margin-top: 0 !important;
            gap: 0 !important;
        }
        
        /* Ocultar menú */
        #MainMenu, footer, .stDeployButton {
            display: none !important;
        }
        
        /* Fondo */
        body, .stApp {
            background: #0c0e12 !important;
        }
        
        /* CONTENEDOR PRINCIPAL */
        .login-container {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-top: none;
            border-radius: 0 0 20px 20px;
            width: 100%;
            max-width: 420px;
            margin: 0 auto;
            padding: 25px 30px 30px;
        }
        
        /* LOGO */
        .logo-box {
            width: 160px;
            height: 160px;
            margin: 0 auto 20px;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 15px 40px rgba(0, 255, 173, 0.25);
            background: linear-gradient(135deg, #00ffad 0%, #00a8e8 100%);
        }
        
        .logo-box img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }
        
        /* TÍTULOS */
        .main-title {
            color: white;
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: 3px;
            text-align: center;
            margin: 0 0 8px 0;
        }
        
        .sub-title {
            color: #00ffad;
            font-size: 0.9rem;
            text-align: center;
            letter-spacing: 1px;
            margin: 0 0 30px 0;
        }
        
        /* FORMULARIO */
        .form-label {
            color: #888;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 6px;
            display: block;
        }
        
        /* INPUT */
        .stTextInput > div > div > input {
            background: #0c0e12 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 8px !important;
            color: white !important;
            height: 46px !important;
            font-size: 15px !important;
        }
        
        /* BOTÓN OJO - CORREGIDO */
        div[data-testid="column"]:nth-of-type(2) button {
            background: #1a1e26 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 8px !important;
            color: #888 !important;
            height: 46px !important;
            width: 46px !important;
            margin: 0 !important;
            padding: 0 !important;
            position: relative;
            top: 24px;
        }
        
        /* BOTÓN PRINCIPAL */
        .stButton > button {
            width: 100% !important;
            background: linear-gradient(90deg, #00ffad, #00d4aa) !important;
            color: #0c0e12 !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            letter-spacing: 1.5px !important;
            height: 48px !important;
            margin-top: 15px !important;
        }
        
        /* ERROR */
        .error-box {
            background: rgba(242, 54, 69, 0.1);
            border: 1px solid rgba(242, 54, 69, 0.3);
            border-radius: 6px;
            padding: 10px 14px;
            margin-top: 15px;
            color: #f23645;
            font-size: 13px;
        }
        
        /* FOOTER */
        .footer {
            text-align: center;
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid #1a1e26;
        }
        
        .footer-secure {
            color: #00ffad;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
        }
        
        .footer-copy {
            color: #555;
            font-size: 10px;
            margin-top: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

    logo_b64 = get_logo_base64()

    # CONTENIDO
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # LOGO
    if logo_b64:
        st.markdown(f'<div class="logo-box"><img src="data:image/png;base64,{logo_b64}" alt="RSU"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="logo-box" style="display:flex;align-items:center;justify-content:center;font-size:4rem;">🔐</div>', unsafe_allow_html=True)
    
    # TÍTULOS
    st.markdown('<h1 class="main-title">RSU TERMINAL</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Sistema de Acceso Seguro</p>', unsafe_allow_html=True)
    
    # FORMULARIO
    st.markdown('<span class="form-label">Contraseña de Acceso</span>', unsafe_allow_html=True)
    
    # Input + Toggle (solo UN botón de ojo)
    col_input, col_toggle = st.columns([5, 1])
    
    with col_input:
        password = st.text_input(
            "",
            type="text" if st.session_state["show_password"] else "password",
            placeholder="Ingrese su contraseña...",
            label_visibility="collapsed"
        )
    
    with col_toggle:
        # Solo el botón de ojo, sin label
        if st.button("👁️" if not st.session_state["show_password"] else "🙈", key="eye_toggle"):
            st.session_state["show_password"] = not st.session_state["show_password"]
            st.rerun()
    
    # BOTÓN ACCESO
    if st.button("🔓 DESBLOQUEAR TERMINAL"):
        if not password:
            st.markdown('<div class="error-box">⚠️ Ingrese una contraseña</div>', unsafe_allow_html=True)
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
                    st.markdown('<div class="error-box">⚠️ Contraseña incorrecta</div>', unsafe_allow_html=True)
                    if 5 - st.session_state["login_attempts"] <= 2:
                        st.warning(f"⚠️ {5 - st.session_state['login_attempts']} intentos restantes")
    
    # FOOTER
    st.markdown("""
        <div class="footer">
            <div class="footer-secure">🔒 CONEXIÓN SEGURA SSL</div>
            <div class="footer-copy">© 2026 RSU Terminal v2.0</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

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
