# modules/auth.py
import os
import streamlit as st
from datetime import datetime, timedelta
import hashlib
import time

def login():
    """Sistema de autenticación RSU Terminal con estética profesional"""
    
    # Inicialización del estado
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
        st.session_state["login_attempts"] = 0
        st.session_state["lockout_time"] = None
        st.session_state["last_activity"] = None
    
    # Verificar timeout de sesión (30 minutos)
    if st.session_state["auth"] and st.session_state["last_activity"]:
        if datetime.now() - st.session_state["last_activity"] > timedelta(minutes=30):
            st.session_state["auth"] = False
            st.warning("Sesión expirada por inactividad")
    
    if st.session_state["auth"]:
        st.session_state["last_activity"] = datetime.now()
        return True

    # Verificar bloqueo por intentos fallidos
    if st.session_state["lockout_time"]:
        if datetime.now() < st.session_state["lockout_time"]:
            remaining = (st.session_state["lockout_time"] - datetime.now()).seconds // 60
            st.error(f"⏱️ Cuenta bloqueada. Intente en {remaining} minutos")
            return False
        else:
            st.session_state["lockout_time"] = None
            st.session_state["login_attempts"] = 0

    # CSS Global - Estética Market Dashboard optimizada
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Reset completo */
        .main {
            background: #0c0e12 !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Eliminar espacios por defecto de Streamlit */
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Contenedor principal - Centrado perfecto */
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
        
        /* Tarjeta de login */
        .login-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            width: 100%;
            max-width: 480px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            overflow: hidden;
        }
        
        /* Sección del logo - CENTRADA Y GRANDE */
        .logo-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 50px 40px 30px;
            background: #0c0e12;
            border-bottom: 1px solid #1a1e26;
        }
        
        /* Logo grande centrado */
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
        
        /* Títulos centrados */
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
        
        /* Cuerpo del formulario */
        .form-section {
            padding: 35px 40px;
        }
        
        /* Input container con botón de ojo */
        .input-wrapper {
            position: relative;
            margin-bottom: 20px;
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
        
        /* Estilo del input */
        .stTextInput > div > div > input {
            background: #0c0e12 !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 8px !important;
            color: white !important;
            padding: 16px 50px 16px 16px !important;
            font-size: 15px !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #00ffad !important;
            box-shadow: 0 0 0 3px rgba(0, 255, 173, 0.1) !important;
            outline: none !important;
        }
        
        /* Botón de ojo para mostrar/ocultar */
        .eye-button {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #888;
            cursor: pointer;
            padding: 8px;
            font-size: 18px;
            z-index: 10;
            transition: color 0.2s;
        }
        
        .eye-button:hover {
            color: #00ffad;
        }
        
        /* Botón principal */
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
            font-family: 'Inter', sans-serif !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 255, 173, 0.35) !important;
        }
        
        /* Mensaje de error */
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
        
        .error-icon {
            color: #f23645;
            font-size: 18px;
        }
        
        .error-text {
            color: #f23645;
            font-size: 13px;
            font-weight: 500;
        }
        
        /* Footer */
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
        
        /* Intentos restantes */
        .attempts-warning {
            color: #ff9800;
            font-size: 12px;
            text-align: center;
            margin-top: 15px;
            font-weight: 500;
        }
        
        /* Responsive */
        @media (max-width: 520px) {
            .login-card {
                max-width: 100%;
            }
            .logo-wrapper {
                width: 120px;
                height: 120px;
            }
            .brand-title {
                font-size: 1.8rem;
            }
            .logo-section, .form-section, .login-footer {
                padding-left: 25px;
                padding-right: 25px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Obtener IP del usuario (para logging)
    user_ip = st.request.headers.get("X-Forwarded-For", "Unknown")
    if isinstance(user_ip, str) and "," in user_ip:
        user_ip = user_ip.split(",")[0].strip()

    # Layout principal
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    # SECCIÓN DEL LOGO - CENTRADA Y GRANDE
    st.markdown('<div class="logo-section">', unsafe_allow_html=True)
    
    logo_exists = os.path.exists("assets/logo.png")
    
    if logo_exists:
        # Logo desde archivo
        st.image("assets/logo.png", width=140)
    else:
        # Fallback emoji centrado
        st.markdown('<div class="logo-wrapper"><span class="logo-fallback">🔐</span></div>', unsafe_allow_html=True)
    
    # Títulos centrados
    st.markdown("""
        <h1 class="brand-title">RSU Terminal</h1>
        <p class="brand-subtitle">Sistema de Acceso Seguro</p>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Cierre logo-section
    
    # SECCIÓN DEL FORMULARIO
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    
    # Label
    st.markdown('<label class="input-label">Contraseña de Acceso</label>', unsafe_allow_html=True)
    
    # Toggle para mostrar/ocultar contraseña
    if "show_password" not in st.session_state:
        st.session_state["show_password"] = False
    
    col1, col2 = st.columns([6, 1])
    with col1:
        password = st.text_input(
            "",
            type="text" if st.session_state["show_password"] else "password",
            placeholder="Ingrese su contraseña...",
            label_visibility="collapsed",
            key="pwd_input"
        )
    
    with col2:
        if st.button("👁️" if not st.session_state["show_password"] else "🙈", 
                     key="toggle_pwd", help="Mostrar/Ocultar contraseña"):
            st.session_state["show_password"] = not st.session_state["show_password"]
            st.rerun()
    
    # Botón de acceso con Enter habilitado implícitamente
    login_clicked = st.button("🔓 Desbloquear Terminal", use_container_width=True)
    
    # Procesar login
    if login_clicked or (password and st.session_state.get("pwd_input") == password):
        if not password:
            st.markdown("""
                <div class="error-box">
                    <span class="error-icon">⚠️</span>
                    <span class="error-text">Ingrese una contraseña</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            # Hash de la contraseña ingresada
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            real_pwd = st.secrets.get("APP_PASSWORD", "RSU2026")
            real_hash = hashlib.sha256(real_pwd.encode()).hexdigest()
            
            if pwd_hash == real_hash:
                # Éxito - Resetear intentos y establecer sesión
                st.session_state["auth"] = True
                st.session_state["login_attempts"] = 0
                st.session_state["last_activity"] = datetime.now()
                st.session_state["user_ip"] = user_ip
                
                # Log de éxito (en producción, guardar en archivo/DB)
                print(f"[LOGIN SUCCESS] IP: {user_ip} - Time: {datetime.now()}")
                
                st.success("✅ Acceso concedido")
                st.balloons()
                time.sleep(0.5)
                st.rerun()
            else:
                # Fallo - Incrementar contador
                st.session_state["login_attempts"] += 1
                remaining = 5 - st.session_state["login_attempts"]
                
                # Log de fallo
                print(f"[LOGIN FAILED] IP: {user_ip} - Attempt: {st.session_state['login_attempts']} - Time: {datetime.now()}")
                
                if st.session_state["login_attempts"] >= 5:
                    # Bloquear por 15 minutos
                    st.session_state["lockout_time"] = datetime.now() + timedelta(minutes=15)
                    st.error("⏱️ Demasiados intentos. Cuenta bloqueada por 15 minutos.")
                else:
                    st.markdown(f"""
                        <div class="error-box">
                            <span class="error-icon">⚠️</span>
                            <span class="error-text">Contraseña incorrecta</span>
                        </div>
                    """, unsafe_allow_html=True)
                    if remaining <= 2:
                        st.markdown(f'<p class="attempts-warning">⚠️ {remaining} intentos restantes antes del bloqueo</p>', 
                                  unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Cierre form-section
    
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
    
    st.markdown('</div>', unsafe_allow_html=True)  # Cierre login-card
    st.markdown('</div>', unsafe_allow_html=True)  # Cierre login-container

    return False


def logout_button():
    """Botón de logout para usar en el dashboard (market.py)"""
    if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state["auth"] = False
        st.session_state["last_activity"] = None
        st.rerun()


def require_auth():
    """Decorador/función helper para proteger páginas"""
    if "auth" not in st.session_state or not st.session_state["auth"]:
        st.warning("🔒 Acceso denegado. Por favor inicie sesión.")
        login()
        st.stop()
    else:
        # Actualizar última actividad
        st.session_state["last_activity"] = datetime.now()
