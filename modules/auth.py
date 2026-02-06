# modules/auth.py
import os
import streamlit as st
from datetime import datetime, timedelta
import hashlib
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def login():
    """Sistema de autenticación RSU Terminal con seguridad mejorada"""
    
    # Inicialización del estado
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
        st.session_state["login_attempts"] = 0
        st.session_state["lockout_time"] = None
        st.session_state["last_activity"] = None
        st.session_state["user_ip"] = None
        st.session_state["show_password"] = False
    
    # Verificar timeout de sesión (30 minutos)
    if st.session_state["auth"] and st.session_state["last_activity"]:
        if datetime.now() - st.session_state["last_activity"] > timedelta(minutes=30):
            st.session_state["auth"] = False
            st.session_state["last_activity"] = None
            st.warning("⏱️ Sesión expirada por inactividad (30 min)")
            st.rerun()
    
    if st.session_state["auth"]:
        st.session_state["last_activity"] = datetime.now()
        return True

    # Verificar bloqueo por intentos fallidos
    if st.session_state["lockout_time"]:
        if datetime.now() < st.session_state["lockout_time"]:
            remaining = int((st.session_state["lockout_time"] - datetime.now()).total_seconds() / 60)
            st.error(f"⏱️ Cuenta bloqueada. Intente en {remaining} minutos")
            return False
        else:
            st.session_state["lockout_time"] = None
            st.session_state["login_attempts"] = 0

    # CSS Global - Estética Market Dashboard
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .main {
            background: #0c0e12 !important;
            font-family: 'Inter', sans-serif;
        }
        
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        
        #MainMenu, footer, header {visibility: hidden;}
        
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            width: 100%;
            padding: 20px;
            box-sizing: border-box;
        }
        
        .login-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            width: 100%;
            max-width: 480px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            overflow: hidden;
        }
        
        .logo-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 50px 40px 30px;
            background: #0c0e12;
            border-bottom: 1px solid #1a1e26;
        }
        
        .logo-wrapper {
            width: 140px;
            height: 140px;
            margin-bottom: 25px;
            background: linear-gradient(135deg, #00ffad 0%, #00a8e8 100%);
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 15px 40px rgba(0, 255, 173, 0.25);
            overflow: hidden;
        }
        
        .logo-wrapper img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        
        .logo-fallback {
            font-size: 4rem;
        }
        
        .brand-title {
            color: white;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: 3px;
            margin: 0;
            text-align: center;
            text-transform: uppercase;
        }
        
        .brand-subtitle {
            color: #00ffad;
            font-size: 1rem;
            margin-top: 10px;
            font-weight: 400;
            text-align: center;
            letter-spacing: 1px;
        }
        
        .form-section {
            padding: 35px 40px;
        }
        
        .input-label {
            color: white;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 10px;
            display: block;
        }
        
        .stTextInput > div > div > input {
            background: #0c0e12 !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 8px !important;
            color: white !important;
            padding: 16px 16px !important;
            font-size: 15px !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #00ffad !important;
            box-shadow: 0 0 0 3px rgba(0, 255, 173, 0.1) !important;
        }
        
        .stButton > button {
            width: 100%;
            background: linear-gradient(90deg, #00ffad 0%, #00d4aa 100%) !important;
            color: #0c0e12 !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 16px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            letter-spacing: 2px;
            text-transform: uppercase;
            transition: all 0.3s ease !important;
            margin-top: 10px !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 255, 173, 0.35) !important;
        }
        
        .error-box {
            background: rgba(242, 54, 69, 0.1);
            border: 1px solid rgba(242, 54, 69, 0.3);
            border-radius: 8px;
            padding: 14px 16px;
            margin-top: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: shake 0.5s ease-in-out;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        .error-icon { color: #f23645; font-size: 18px; }
        .error-text { color: #f23645; font-size: 13px; font-weight: 500; }
        
        .login-footer {
            background: #0c0e12;
            padding: 25px 40px;
            border-top: 1px solid #1a1e26;
            text-align: center;
        }
        
        .security-info {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        
        .secure-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #00ffad;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }
        
        .ip-info {
            color: #555;
            font-size: 11px;
            font-family: monospace;
        }
        
        .copyright {
            color: #444;
            font-size: 11px;
            margin-top: 12px;
        }
        
        .attempts-warning {
            color: #ff9800;
            font-size: 12px;
            text-align: center;
            margin-top: 15px;
            font-weight: 500;
        }
        
        /* Toggle password button */
        .toggle-pwd-btn {
            background: transparent !important;
            border: none !important;
            color: #888 !important;
            font-size: 1.2rem !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        
        @media (max-width: 520px) {
            .login-card { max-width: 100%; }
            .logo-wrapper { width: 120px; height: 120px; }
            .brand-title { font-size: 1.8rem; }
            .logo-section, .form-section, .login-footer {
                padding-left: 25px;
                padding-right: 25px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Obtener IP del usuario
    try:
        user_ip = st.request.headers.get("X-Forwarded-For", "Unknown")
        if isinstance(user_ip, str) and "," in user_ip:
            user_ip = user_ip.split(",")[0].strip()
    except:
        user_ip = "Unknown"

    # Layout principal
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        logo_exists = os.path.exists("assets/logo.png")
        
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # SECCIÓN DEL LOGO - CENTRADA Y GRANDE
        st.markdown('<div class="logo-section">', unsafe_allow_html=True)
        
        if logo_exists:
            st.image("assets/logo.png", width=140)
        else:
            st.markdown('<div class="logo-wrapper"><span class="logo-fallback">🔐</span></div>', unsafe_allow_html=True)
        
        st.markdown("""
            <h1 class="brand-title">RSU Terminal</h1>
            <p class="brand-subtitle">Sistema de Acceso Seguro</p>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECCIÓN DEL FORMULARIO
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        
        st.markdown('<label class="input-label">Contraseña de Acceso</label>', unsafe_allow_html=True)
        
        # Input con toggle de visibilidad
        pwd_col, toggle_col = st.columns([6, 1])
        with pwd_col:
            password = st.text_input(
                "",
                type="text" if st.session_state["show_password"] else "password",
                placeholder="Ingrese su contraseña...",
                label_visibility="collapsed",
                key="pwd_input",
                on_change=lambda: None
            )
        
        with toggle_col:
            if st.button("👁️" if not st.session_state["show_password"] else "🙈", 
                        key="toggle_pwd", 
                        help="Mostrar/Ocultar contraseña"):
                st.session_state["show_password"] = not st.session_state["show_password"]
                st.rerun()
        
        # Botón de acceso
        if st.button("🔓 Desbloquear Terminal", use_container_width=True):
            if not password:
                st.markdown("""
                    <div class="error-box">
                        <span class="error-icon">⚠️</span>
                        <span class="error-text">Ingrese una contraseña</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Hash de la contraseña ingresada (SHA-256)
                pwd_hash = hashlib.sha256(password.encode()).hexdigest()
                real_pwd = st.secrets.get("APP_PASSWORD", "RSU2026")
                real_hash = hashlib.sha256(real_pwd.encode()).hexdigest()
                
                if pwd_hash == real_hash:
                    # Éxito
                    st.session_state["auth"] = True
                    st.session_state["login_attempts"] = 0
                    st.session_state["last_activity"] = datetime.now()
                    st.session_state["user_ip"] = user_ip
                    
                    logger.info(f"[LOGIN SUCCESS] IP: {user_ip} - Time: {datetime.now()}")
                    
                    st.success("✅ Acceso concedido")
                    st.balloons()
                    time.sleep(0.5)
                    st.rerun()
                else:
                    # Fallo
                    st.session_state["login_attempts"] += 1
                    remaining = 5 - st.session_state["login_attempts"]
                    
                    logger.warning(f"[LOGIN FAILED] IP: {user_ip} - Attempt: {st.session_state['login_attempts']}")
                    
                    if st.session_state["login_attempts"] >= 5:
                        st.session_state["lockout_time"] = datetime.now() + timedelta(minutes=15)
                        st.error("⏱️ Demasiados intentos. Cuenta bloqueada por 15 minutos.")
                    else:
                        st.markdown("""
                            <div class="error-box">
                                <span class="error-icon">⚠️</span>
                                <span class="error-text">Contraseña incorrecta</span>
                            </div>
                        """, unsafe_allow_html=True)
                        if remaining <= 2:
                            st.markdown(f'<p class="attempts-warning">⚠️ {remaining} intentos restantes</p>', 
                                      unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # FOOTER
        current_year = datetime.now().year
        st.markdown(f"""
            <div class="login-footer">
                <div class="security-info">
                    <div class="secure-badge">
                        <span>🔒</span>
                        <span>Conexión Segura SSL</span>
                    </div>
                    <div class="ip-info">IP: {user_ip}</div>
                    <div class="copyright">© {current_year} RSU Terminal v2.0 • Acceso Restringido</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    return False


def logout():
    """Cierra la sesión del usuario"""
    st.session_state["auth"] = False
    st.session_state["last_activity"] = None
    st.session_state["user_ip"] = None
    logger.info(f"[LOGOUT] IP: {st.session_state.get('user_ip', 'Unknown')} - Time: {datetime.now()}")
    st.success("👋 Sesión cerrada correctamente")
    time.sleep(0.5)
    st.rerun()


def require_auth():
    """Verifica que el usuario esté autenticado"""
    if "auth" not in st.session_state or not st.session_state["auth"]:
        st.error("🔒 Acceso denegado. Inicie sesión primero.")
        login()
        st.stop()
    
    # Actualizar actividad
    st.session_state["last_activity"] = datetime.now()
    
    # Verificar timeout
    if "last_activity" in st.session_state:
        last = st.session_state["last_activity"]
        if datetime.now() - last > timedelta(minutes=30):
            st.session_state["auth"] = False
            st.warning("⏱️ Sesión expirada")
            st.rerun()
