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

    # CSS CRÍTICO - Ejecutar PRIMERO y con !important en todo
    st.markdown("""
    <style>
        /* ELIMINAR ESPACIO SUPERIOR DE STREAMLIT */
        .stApp {
            margin-top: -80px !important;
        }
        
        header[data-testid="stHeader"] {
            display: none !important;
        }
        
        .main > div {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
            max-width: 100% !important;
        }
        
        #root > div > div {
            margin-top: 0 !important;
        }
        
        /* Ocultar todo lo demás */
        #MainMenu, footer, .stDeployButton, .stToolbar {
            display: none !important;
        }
        
        /* Fondo */
        .stApp, body {
            background: #0c0e12 !important;
        }
        
        /* CONTENEDOR PRINCIPAL - PEGADO ARRIBA */
        .login-box {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 0 0 16px 16px;
            width: 100%;
            max-width: 450px;
            margin: 0 auto;
            padding: 30px 35px;
        }
        
        /* LOGO GRANDE CENTRADO */
        .logo-img {
            width: 170px;
            height: 170px;
            margin: 0 auto 20px;
            display: block;
            border-radius: 24px;
            box-shadow: 0 15px 40px rgba(0, 255, 173, 0.3);
        }
        
        /* TÍTULOS */
        h1.title {
            color: white;
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: 3px;
            text-align: center;
            margin: 0 0 8px 0;
        }
        
        p.subtitle {
            color: #00ffad;
            font-size: 0.95rem;
            text-align: center;
            letter-spacing: 1px;
            margin: 0 0 35px 0;
        }
        
        /* LABEL */
        .pwd-label {
            color: #888;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
            display: block;
        }
        
        /* STREAMLIT INPUT OVERRIDE */
        div[data-testid="stTextInput"] > div > div > input {
            background-color: #0c0e12 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 8px !important;
            color: white !important;
            height: 48px !important;
        }
        
        /* BOTÓN OJO */
        button[kind="secondary"] {
            background: #1a1e26 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 8px !important;
            color: #888 !important;
            height: 48px !important;
            width: 48px !important;
            margin-top: 24px !important;
        }
        
        /* BOTÓN PRINCIPAL */
        button[kind="primary"] {
            background: linear-gradient(90deg, #00ffad, #00d4aa) !important;
            color: #0c0e12 !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            height: 50px !important;
            margin-top: 15px !important;
        }
        
        /* ERROR */
        .error-msg {
            background: rgba(242, 54, 69, 0.1);
            border: 1px solid rgba(242, 54, 69, 0.3);
            border-radius: 6px;
            padding: 10px 14px;
            margin-top: 15px;
            color: #f23645;
            font-size: 13px;
        }
        
        /* FOOTER */
        .footer-box {
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
            margin-top: 6px;
        }
    </style>
    """, unsafe_allow_html=True)

    logo_b64 = get_logo_base64()

    # CONTENIDO - SIN WRAPPER ADICIONAL
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    
    # LOGO (PRIMERO)
    if logo_b64:
        st.markdown(f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">', unsafe_allow_html=True)
    else:
        st.markdown('<div style="width:170px;height:170px;margin:0 auto 20px;background:linear-gradient(135deg,#00ffad,#00a8e8);border-radius:24px;display:flex;align-items:center;justify-content:center;font-size:5rem;">🔐</div>', unsafe_allow_html=True)
    
    # TÍTULOS
    st.markdown('<h1 class="title">RSU TERMINAL</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Sistema de Acceso Seguro</p>', unsafe_allow_html=True)
    
    # FORMULARIO
    st.markdown('<span class="pwd-label">Contraseña de Acceso</span>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([4, 1])
    with c1:
        pwd = st.text_input("", type="text" if st.session_state["show_password"] else "password", 
                          placeholder="Ingrese su contraseña...", label_visibility="collapsed")
    with c2:
        if st.button("👁️" if not st.session_state["show_password"] else "🙈"):
            st.session_state["show_password"] = not st.session_state["show_password"]
            st.rerun()
    
    # BOTÓN
    if st.button("🔓 DESBLOQUEAR TERMINAL", type="primary"):
        if not pwd:
            st.markdown('<div class="error-msg">⚠️ Ingrese una contraseña</div>', unsafe_allow_html=True)
        else:
            if hashlib.sha256(pwd.encode()).hexdigest() == hashlib.sha256(st.secrets.get("APP_PASSWORD", "RSU2026").encode()).hexdigest():
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
    
    # FOOTER
    st.markdown("""
        <div class="footer-box">
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
