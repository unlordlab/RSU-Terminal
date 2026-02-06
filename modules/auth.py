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
    """Convierte el logo a base64"""
    try:
        if os.path.exists("assets/logo.png"):
            with open("assets/logo.png", "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return None

def login():
    """Sistema de autenticación RSU Terminal"""
    
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

    # CSS - ELIMINAR TODO ESPACIO SUPERIOR
    st.markdown("""
    <style>
        /* RESET ABSOLUTO - ELIMINAR TODO ESPACIO */
        html, body, [data-testid="stAppViewContainer"], .main, .block-container {
            margin: 0 !important;
            padding: 0 !important;
            max-width: 100% !important;
        }
        
        /* Ocultar elementos de Streamlit */
        #MainMenu, footer, header, .stDeployButton, .stToolbar {
            display: none !important;
        }
        
        /* Fondo */
        body {
            background: #0c0e12;
        }
        
        [data-testid="stAppViewContainer"] {
            background: #0c0e12;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            overflow-y: auto;
        }
        
        /* CONTENEDOR - SIN ESPACIO SUPERIOR */
        .login-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            min-height: 100vh;
            width: 100%;
            padding-top: 20px !important;
            padding-bottom: 20px;
        }
        
        /* TARJETA */
        .login-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 16px;
            width: 90%;
            max-width: 400px;
            padding: 30px;
            margin-top: 0;
        }
        
        /* LOGO - PRIMERO EN APARECER */
        .logo-container {
            width: 180px;
            height: 180px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #00ffad 0%, #00a8e8 100%);
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 15px 40px rgba(0, 255, 173, 0.3);
            overflow: hidden;
        }
        
        .logo-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .logo-fallback {
            font-size: 5rem;
        }
        
        /* TÍTULOS */
        .brand-title {
            color: white;
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: 3px;
            text-align: center;
            margin: 0 0 8px 0;
        }
        
        .brand-subtitle {
            color: #00ffad;
            font-size: 0.9rem;
            text-align: center;
            letter-spacing: 1px;
            margin-bottom: 30px;
        }
        
        /* FORMULARIO */
        .input-label {
            color: #888;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 6px;
            display: block;
        }
        
        /* INPUT */
        div[data-testid="stTextInput"] {
            width: 100%;
        }
        
        .stTextInput > div > div > input {
            background: #0c0e12 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 8px !important;
            color: white !important;
            padding: 14px 16px !important;
            font-size: 15px !important;
            height: 50px !important;
        }
        
        /* COLUMNA DEL BOTÓN OJO */
        div[data-testid="column"]:nth-child(2) {
            display: flex !important;
            align-items: flex-end !important;
            padding-bottom: 0 !important;
        }
        
        div[data-testid="column"]:nth-child(2) button {
            background: #1a1e26 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 8px !important;
            color: #888 !important;
            height: 50px !important;
            width: 50px !important;
            margin: 0 !important;
            padding: 0 !important;
            font-size: 1.1rem !important;
        }
        
        /* BOTÓN PRINCIPAL */
        .stButton > button {
            width: 100% !important;
            background: linear-gradient(90deg, #00ffad 0%, #00d4aa 100%) !important;
            color: #0c0e12 !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 16px !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            letter-spacing: 1.5px;
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
            padding-top: 15px;
            border-top: 1px solid #1a1e26;
        }
        
        .footer-text {
            color: #00ffad;
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1px;
        }
        
        .footer-sub {
            color: #555;
            font-size: 10px;
            margin-top: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Obtener logo
    logo_b64 = get_logo_base64()

    # Layout - CENTRADO, SIN MÁRGENES SUPERIORES
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    # LOGO (PRIMERO, SIN ESPACIO ARRIBA)
    if logo_b64:
        st.markdown(f"""
            <div class="logo-container">
                <img src="data:image/png;base64,{logo_b64}" alt="RSU">
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="logo-container">
                <span class="logo-fallback">🔐</span>
            </div>
        """, unsafe_allow_html=True)
    
    # TÍTULOS
    st.markdown("""
        <div class="brand-title">RSU TERMINAL</div>
        <div class="brand-subtitle">Sistema de Acceso Seguro</div>
    """, unsafe_allow_html=True)
    
    # FORMULARIO
    st.markdown('<div class="input-label">Contraseña de Acceso</div>', unsafe_allow_html=True)
    
    # Input + Toggle
    col1, col2 = st.columns([5, 1])
    
    with col1:
        password = st.text_input(
            "",
            type="text" if st.session_state["show_password"] else "password",
            placeholder="Ingrese su contraseña...",
            label_visibility="collapsed"
        )
    
    with col2:
        if st.button("👁️" if not st.session_state["show_password"] else "🙈"):
            st.session_state["show_password"] = not st.session_state["show_password"]
            st.rerun()
    
    # Botón acceso
    if st.button("🔓 Desbloquear Terminal"):
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
                logger.info("[LOGIN SUCCESS]")
                st.success("✅ Acceso concedido")
                time.sleep(0.3)
                st.rerun()
            else:
                st.session_state["login_attempts"] += 1
                remaining = 5 - st.session_state["login_attempts"]
                logger.warning(f"[LOGIN FAILED] {st.session_state['login_attempts']}")
                
                if st.session_state["login_attempts"] >= 5:
                    st.session_state["lockout_time"] = datetime.now() + timedelta(minutes=15)
                    st.error("⏱️ Cuenta bloqueada 15 minutos")
                else:
                    st.markdown('<div class="error-box">⚠️ Contraseña incorrecta</div>', unsafe_allow_html=True)
                    if remaining <= 2:
                        st.warning(f"⚠️ {remaining} intentos restantes")
    
    # Footer
    st.markdown("""
        <div class="footer">
            <div class="footer-text">🔒 CONEXIÓN SEGURA SSL</div>
            <div class="footer-sub">© 2026 RSU Terminal v2.0</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    return False


def logout():
    """Cierra sesión"""
    st.session_state["auth"] = False
    st.session_state["last_activity"] = None
    logger.info("[LOGOUT]")
    st.success("👋 Sesión cerrada")
    time.sleep(0.3)
    st.rerun()


def require_auth():
    """Verifica autenticación"""
    if "auth" not in st.session_state or not st.session_state["auth"]:
        st.error("🔒 Acceso denegado")
        login()
        st.stop()
    st.session_state["last_activity"] = datetime.now()
