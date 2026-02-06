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

    # CSS - TODO CENTRADO, SIN DOBLES BOTONES
    st.markdown("""
    <style>
        /* RESET TOTAL */
        .stApp { margin-top: -80px !important; }
        header, #MainMenu, footer, .stDeployButton { display: none !important; }
        
        .main, .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        
        body, .stApp { background: #0c0e12 !important; }
        
        /* CONTENEDOR CENTRADO VERTICAL Y HORIZONTAL */
        .login-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            width: 100%;
            padding: 20px;
        }
        
        /* TARJETA CENTRADA */
        .login-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 16px;
            width: 100%;
            max-width: 380px;
            padding: 35px 40px;
            text-align: center;
        }
        
        /* LOGO - NO CORTADO, CENTRADO */
        .logo-wrap {
            width: 150px;
            height: 150px;
            margin: 0 auto 25px;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 15px 40px rgba(0, 255, 173, 0.25);
            background: linear-gradient(135deg, #00ffad 0%, #00a8e8 100%);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .logo-wrap img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        /* TÍTULOS */
        .brand-title {
            color: white;
            font-size: 1.9rem;
            font-weight: 700;
            letter-spacing: 4px;
            margin: 0 0 10px 0;
        }
        
        .brand-subtitle {
            color: #00ffad;
            font-size: 0.95rem;
            letter-spacing: 1.5px;
            margin: 0 0 35px 0;
        }
        
        /* FORMULARIO ALINEADO */
        .form-row {
            display: flex;
            gap: 10px;
            align-items: flex-end;
            margin-bottom: 5px;
        }
        
        .input-wrap {
            flex: 1;
            text-align: left;
        }
        
        .input-label {
            color: #888;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
            display: block;
        }
        
        /* INPUT STYLING */
        .stTextInput > div > div > input {
            background: #0c0e12 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 10px !important;
            color: white !important;
            height: 50px !important;
            font-size: 15px !important;
        }
        
        /* BOTÓN OJO - SOLO UNO */
        .eye-btn {
            background: #1a1e26 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 10px !important;
            color: #888 !important;
            width: 50px !important;
            height: 50px !important;
            margin: 0 !important;
            padding: 0 !important;
            font-size: 1.2rem !important;
        }
        
        .eye-btn:hover {
            border-color: #00ffad !important;
            color: #00ffad !important;
        }
        
        /* BOTÓN PRINCIPAL - ANCHO COMPLETO */
        .stButton > button {
            width: 100% !important;
            background: linear-gradient(90deg, #00ffad, #00d4aa) !important;
            color: #0c0e12 !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            letter-spacing: 2px !important;
            height: 52px !important;
            margin-top: 20px !important;
        }
        
        /* ERROR */
        .error-msg {
            background: rgba(242, 54, 69, 0.1);
            border: 1px solid rgba(242, 54, 69, 0.3);
            border-radius: 8px;
            padding: 12px;
            margin-top: 15px;
            color: #f23645;
            font-size: 13px;
            text-align: left;
        }
        
        /* FOOTER */
        .footer-box {
            margin-top: 30px;
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
            margin-top: 6px;
        }
    </style>
    """, unsafe_allow_html=True)

    logo_b64 = get_logo_base64()

    # WRAPPER CENTRADO
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    # LOGO CENTRADO
    if logo_b64:
        st.markdown(f'<div class="logo-wrap"><img src="data:image/png;base64,{logo_b64}"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="logo-wrap"><span style="font-size:4rem;">🔐</span></div>', unsafe_allow_html=True)
    
    # TÍTULOS CENTRADOS
    st.markdown('<div class="brand-title">RSU TERMINAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Sistema de Acceso Seguro</div>', unsafe_allow_html=True)
    
    # FORMULARIO CON LABEL
    st.markdown('<div class="input-label">Contraseña de Acceso</div>', unsafe_allow_html=True)
    
    # INPUT + BOTÓN OJO EN FILA FLEX
    input_col, btn_col = st.columns([4, 1])
    
    with input_col:
        password = st.text_input(
            "",
            type="text" if st.session_state["show_password"] else "password",
            placeholder="Ingrese su contraseña...",
            label_visibility="collapsed"
        )
    
    with btn_col:
        # USAR st.markdown PARA EL BOTÓN CON CLASE CUSTOM
        if st.button("👁️", key="toggle_pwd", help="Mostrar/Ocultar"):
            st.session_state["show_password"] = not st.session_state["show_password"]
            st.rerun()
    
    # BOTÓN ACCESO ANCHO COMPLETO
    if st.button("🔓 DESBLOQUEAR TERMINAL"):
        if not password:
            st.markdown('<div class="error-msg">⚠️ Ingrese una contraseña</div>', unsafe_allow_html=True)
        else:
            if hashlib.sha256(password.encode()).hexdigest() == hashlib.sha256(st.secrets.get("APP_PASSWORD", "RSU2026").encode()).hexdigest():
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
                    st.markdown('<div class="error-msg">⚠️ Contraseña incorrecta</div>', unsafe_allow_html=True)
                    if 5 - st.session_state["login_attempts"] <= 2:
                        st.warning(f"⚠️ {5 - st.session_state['login_attempts']} intentos restantes")
    
    # FOOTER
    st.markdown("""
        <div class="footer-box">
            <div class="footer-secure">🔒 CONEXIÓN SEGURA SSL</div>
            <div class="footer-copy">© 2026 RSU Terminal v2.0</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
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
