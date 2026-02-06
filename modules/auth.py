# modules/auth.py
import os
import streamlit as st
from datetime import datetime, timedelta
import hashlib
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def login():
    """Sistema de autenticación RSU Terminal"""
    
    # Inicialización
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
        st.session_state["login_attempts"] = 0
        st.session_state["lockout_time"] = None
        st.session_state["last_activity"] = None
        st.session_state["user_ip"] = None
        st.session_state["show_password"] = False
    
    # Verificar timeout (30 min)
    if st.session_state["auth"] and st.session_state["last_activity"]:
        if datetime.now() - st.session_state["last_activity"] > timedelta(minutes=30):
            st.session_state["auth"] = False
            st.session_state["last_activity"] = None
            st.warning("⏱️ Sesión expirada por inactividad")
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

    # CSS - ELIMINADO ESPACIO SUPERIOR, LOGO MÁS GRANDE
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* CRÍTICO: Eliminar TODO el padding/margin superior */
        .main, .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        
        /* Ocultar elementos de Streamlit */
        #MainMenu, footer, header, .stDeployButton {display: none !important;}
        
        /* Fondo completo */
        [data-testid="stAppViewContainer"] {
            background: #0c0e12;
        }
        
        /* Contenedor login - SIN ESPACIO SUPERIOR */
        .login-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            min-height: 100vh;
            width: 100%;
            padding: 0;
            margin: 0;
            box-sizing: border-box;
        }
        
        /* Tarjeta sin bordes superiores */
        .login-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-top: none;
            border-radius: 0 0 10px 10px;
            width: 100%;
            max-width: 500px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            margin-top: 0;
        }
        
        /* Sección logo - SIN PADDING SUPERIOR EXCESIVO */
        .logo-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px 30px 25px;
            background: #0c0e12;
            border-bottom: 1px solid #1a1e26;
        }
        
        /* LOGO GRANDE - 180px */
        .logo-container {
            width: 180px;
            height: 180px;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #00ffad 0%, #00a8e8 100%);
            border-radius: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 20px 50px rgba(0, 255, 173, 0.3);
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
        
        /* Títulos centrados */
        .brand-title {
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: 4px;
            margin: 0;
            text-align: center;
            text-transform: uppercase;
        }
        
        .brand-subtitle {
            color: #00ffad;
            font-size: 1.1rem;
            margin-top: 8px;
            font-weight: 400;
            text-align: center;
            letter-spacing: 2px;
        }
        
        /* Formulario */
        .form-section {
            padding: 30px 40px;
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
            padding: 16px !important;
            font-size: 16px !important;
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
            padding: 18px !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-top: 15px !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 255, 173, 0.35) !important;
        }
        
        /* Toggle button */
        div[data-testid="column"]:nth-of-type(2) button {
            background: transparent !important;
            border: none !important;
            color: #888 !important;
            font-size: 1.3rem !important;
            padding: 0 !important;
            margin-top: 28px !important;
        }
        
        /* Error box */
        .error-box {
            background: rgba(242, 54, 69, 0.1);
            border: 1px solid rgba(242, 54, 69, 0.3);
            border-radius: 8px;
            padding: 14px;
            margin-top: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .error-icon { color: #f23645; font-size: 18px; }
        .error-text { color: #f23645; font-size: 13px; font-weight: 500; }
        
        /* Footer */
        .login-footer {
            background: #0c0e12;
            padding: 20px 40px;
            border-top: 1px solid #1a1e26;
            text-align: center;
        }
        
        .secure-badge {
            color: #00ffad;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .ip-info {
            color: #555;
            font-size: 11px;
            margin-top: 6px;
            font-family: monospace;
        }
        
        .attempts-warning {
            color: #ff9800;
            font-size: 12px;
            text-align: center;
            margin-top: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Obtener IP
    try:
        user_ip = st.request.headers.get("X-Forwarded-For", "Unknown")
        if isinstance(user_ip, str) and "," in user_ip:
            user_ip = user_ip.split(",")[0].strip()
    except:
        user_ip = "Unknown"

    # Layout - SIN COLUMNAS QUE CREAN ESPACIO
    logo_exists = os.path.exists("assets/logo.png")
    
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    # LOGO SECCIÓN - CENTRADO Y GRANDE
    st.markdown('<div class="logo-section">', unsafe_allow_html=True)
    
    if logo_exists:
        # Usar HTML para control total del tamaño
        st.markdown(f"""
            <div style="display: flex; justify-content: center;">
                <div class="logo-container">
                    <img src="assets/logo.png" alt="RSU Logo">
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="display: flex; justify-content: center;">
                <div class="logo-container">
                    <span class="logo-fallback">🔐</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
        <h1 class="brand-title">RSU Terminal</h1>
        <p class="brand-subtitle">Sistema de Acceso Seguro</p>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # FORMULARIO
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    
    st.markdown('<label class="input-label">Contraseña de Acceso</label>', unsafe_allow_html=True)
    
    # Input y toggle en una fila
    pwd_col, toggle_col = st.columns([5, 1])
    with pwd_col:
        password = st.text_input(
            "",
            type="text" if st.session_state["show_password"] else "password",
            placeholder="Ingrese su contraseña...",
            label_visibility="collapsed"
        )
    
    with toggle_col:
        if st.button("👁️" if not st.session_state["show_password"] else "🙈"):
            st.session_state["show_password"] = not st.session_state["show_password"]
            st.rerun()
    
    # Botón acceso
    if st.button("🔓 Desbloquear Terminal"):
        if not password:
            st.markdown("""
                <div class="error-box">
                    <span class="error-icon">⚠️</span>
                    <span class="error-text">Ingrese una contraseña</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            # Hash SHA-256
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            real_pwd = st.secrets.get("APP_PASSWORD", "RSU2026")
            real_hash = hashlib.sha256(real_pwd.encode()).hexdigest()
            
            if pwd_hash == real_hash:
                st.session_state["auth"] = True
                st.session_state["login_attempts"] = 0
                st.session_state["last_activity"] = datetime.now()
                st.session_state["user_ip"] = user_ip
                
                logger.info(f"[LOGIN SUCCESS] IP: {user_ip}")
                
                # SIN GLOBOS - Solo mensaje limpio
                st.success("✅ Acceso concedido")
                time.sleep(0.3)
                st.rerun()
            else:
                st.session_state["login_attempts"] += 1
                remaining = 5 - st.session_state["login_attempts"]
                
                logger.warning(f"[LOGIN FAILED] IP: {user_ip} - Attempt: {st.session_state['login_attempts']}")
                
                if st.session_state["login_attempts"] >= 5:
                    st.session_state["lockout_time"] = datetime.now() + timedelta(minutes=15)
                    st.error("⏱️ Demasiados intentos. Cuenta bloqueada 15 min.")
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
            <div class="secure-badge">🔒 Conexión Segura SSL</div>
            <div class="ip-info">IP: {user_ip}</div>
            <div style="color: #444; font-size: 11px; margin-top: 8px;">
                © {current_year} RSU Terminal v2.0
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    return False


def logout():
    """Cierra sesión"""
    st.session_state["auth"] = False
    st.session_state["last_activity"] = None
    st.session_state["user_ip"] = None
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
