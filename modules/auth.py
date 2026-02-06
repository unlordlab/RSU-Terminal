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
    """Convierte el logo a base64 para mostrarlo correctamente"""
    try:
        if os.path.exists("assets/logo.png"):
            with open("assets/logo.png", "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.error(f"Error loading logo: {e}")
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

    # CSS - SIN ESPACIOS, TODO CENTRADO
    st.markdown("""
    <style>
        /* RESET TOTAL */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        .main, .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        
        #MainMenu, footer, header, .stDeployButton {display: none !important;}
        
        [data-testid="stAppViewContainer"] {
            background: #0c0e12;
        }
        
        /* CONTENEDOR PRINCIPAL - TODO CENTRADO VERTICAL Y HORIZONTAL */
        .login-container {
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
            max-width: 420px;
            padding: 40px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        
        /* LOGO - GRANDE Y CENTRADO */
        .logo-box {
            width: 200px;
            height: 200px;
            margin: 0 auto 30px;
            background: linear-gradient(135deg, #00ffad 0%, #00a8e8 100%);
            border-radius: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 20px 60px rgba(0, 255, 173, 0.3);
            overflow: hidden;
        }
        
        .logo-box img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .logo-emoji {
            font-size: 6rem;
        }
        
        /* TEXTOS CENTRADOS */
        .brand-title {
            color: white;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: 4px;
            text-align: center;
            margin-bottom: 10px;
        }
        
        .brand-subtitle {
            color: #00ffad;
            font-size: 1rem;
            text-align: center;
            letter-spacing: 2px;
            margin-bottom: 40px;
        }
        
        /* FORMULARIO */
        .form-group {
            margin-bottom: 20px;
        }
        
        .input-label {
            color: #888;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 8px;
            display: block;
        }
        
        /* INPUT STYLING */
        .stTextInput > div {
            width: 100%;
        }
        
        .stTextInput > div > div > input {
            background: #0c0e12 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 10px !important;
            color: white !important;
            padding: 16px 20px !important;
            font-size: 16px !important;
            width: 100% !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #00ffad !important;
            box-shadow: 0 0 0 3px rgba(0, 255, 173, 0.1) !important;
        }
        
        /* BOTÓN TOGGLE OJO - POSICIÓN CORREGIDA */
        div[data-testid="column"] {
            display: flex;
            align-items: flex-end;
        }
        
        div[data-testid="column"] button {
            background: #1a1e26 !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 10px !important;
            color: #888 !important;
            height: 54px !important;
            width: 54px !important;
            margin: 0 !important;
            padding: 0 !important;
            font-size: 1.2rem !important;
        }
        
        div[data-testid="column"] button:hover {
            border-color: #00ffad !important;
            color: #00ffad !important;
        }
        
        /* BOTÓN PRINCIPAL - GRANDE Y ANCHO COMPLETO */
        .stButton > button {
            width: 100% !important;
            background: linear-gradient(90deg, #00ffad 0%, #00d4aa 100%) !important;
            color: #0c0e12 !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 18px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-top: 10px !important;
            height: auto !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 255, 173, 0.4) !important;
        }
        
        /* ERROR */
        .error-box {
            background: rgba(242, 54, 69, 0.1);
            border: 1px solid rgba(242, 54, 69, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .error-text {
            color: #f23645;
            font-size: 13px;
        }
        
        /* FOOTER */
        .login-footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #1a1e26;
        }
        
        .secure-text {
            color: #00ffad;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .ip-text {
            color: #555;
            font-size: 10px;
            margin-top: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Obtener logo en base64
    logo_b64 = get_logo_base64()
    
    # Layout centrado con columnas de ancho fijo
    left_col, center_col, right_col = st.columns([1, 3, 1])
    
    with center_col:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # LOGO
        if logo_b64:
            st.markdown(f"""
                <div class="logo-box">
                    <img src="data:image/png;base64,{logo_b64}" alt="RSU Logo">
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="logo-box">
                    <span class="logo-emoji">🔐</span>
                </div>
            """, unsafe_allow_html=True)
        
        # TÍTULOS
        st.markdown("""
            <div class="brand-title">RSU TERMINAL</div>
            <div class="brand-subtitle">Sistema de Acceso Seguro</div>
        """, unsafe_allow_html=True)
        
        # FORMULARIO
        st.markdown('<div class="form-group">', unsafe_allow_html=True)
        st.markdown('<label class="input-label">Contraseña de Acceso</label>', unsafe_allow_html=True)
        
        # Input + Toggle en columnas
        input_col, toggle_col = st.columns([5, 1])
        
        with input_col:
            password = st.text_input(
                "",
                type="text" if st.session_state["show_password"] else "password",
                placeholder="Ingrese su contraseña...",
                label_visibility="collapsed"
            )
        
        with toggle_col:
            if st.button("👁️" if not st.session_state["show_password"] else "🙈", key="toggle"):
                st.session_state["show_password"] = not st.session_state["show_password"]
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # BOTÓN ACCESO
        if st.button("🔓 Desbloquear Terminal"):
            if not password:
                st.markdown("""
                    <div class="error-box">
                        <span style="color: #f23645; font-size: 16px;">⚠️</span>
                        <span class="error-text">Ingrese una contraseña</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Hash y verificación
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
                    
                    logger.warning(f"[LOGIN FAILED] Attempt: {st.session_state['login_attempts']}")
                    
                    if st.session_state["login_attempts"] >= 5:
                        st.session_state["lockout_time"] = datetime.now() + timedelta(minutes=15)
                        st.error("⏱️ Cuenta bloqueada 15 minutos")
                    else:
                        st.markdown("""
                            <div class="error-box">
                                <span style="color: #f23645; font-size: 16px;">⚠️</span>
                                <span class="error-text">Contraseña incorrecta</span>
                            </div>
                        """, unsafe_allow_html=True)
                        if remaining <= 2:
                            st.warning(f"⚠️ {remaining} intentos restantes")
        
        # FOOTER
        st.markdown("""
            <div class="login-footer">
                <div class="secure-text">🔒 Conexión Segura SSL</div>
                <div class="ip-text">© 2026 RSU Terminal v2.0</div>
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
