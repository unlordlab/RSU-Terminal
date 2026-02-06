# modules/auth.py
import os
import streamlit as st
from datetime import datetime

def login():
    """Sistema de autenticación con estética RSU Terminal profesional"""
    
    # Inicialización del estado
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
    
    if st.session_state["auth"]:
        return True

    # CSS Global - Estética Market Dashboard
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Reset y base */
        .main {
            background: #0c0e12 !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Contenedor principal centrado */
        .login-wrapper {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        /* Tarjeta de login - Estilo group-container */
        .login-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        
        /* Header de la tarjeta */
        .login-header {
            background: #0c0e12;
            padding: 30px;
            border-bottom: 1px solid #1a1e26;
            text-align: center;
        }
        
        /* Logo/Icono */
        .login-logo {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #00ffad 0%, #00a8e8 100%);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            box-shadow: 0 10px 30px rgba(0, 255, 173, 0.2);
        }
        
        .login-logo img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            border-radius: 16px;
        }
        
        /* Títulos */
        .login-title {
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: 2px;
            margin: 0;
            text-transform: uppercase;
        }
        
        .login-subtitle {
            color: #8892b0;
            font-size: 0.85rem;
            margin-top: 8px;
            font-weight: 400;
        }
        
        /* Cuerpo del formulario */
        .login-body {
            padding: 30px;
        }
        
        /* Input de contraseña - Estilo Market */
        .stTextInput > div > div > input {
            background: #0c0e12 !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 8px !important;
            color: white !important;
            padding: 14px 16px !important;
            font-size: 14px !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #00ffad !important;
            box-shadow: 0 0 0 3px rgba(0, 255, 173, 0.1) !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #555 !important;
        }
        
        /* Label del input */
        .input-label {
            color: white;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
            display: block;
        }
        
        /* Botón de acceso - Estilo Market */
        .stButton > button {
            width: 100%;
            background: linear-gradient(90deg, #00ffad 0%, #00d4aa 100%) !important;
            color: #0c0e12 !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 14px !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            transition: all 0.3s ease !important;
            margin-top: 10px !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 255, 173, 0.3) !important;
        }
        
        .stButton > button:active {
            transform: translateY(0);
        }
        
        /* Mensaje de error - Estilo Market */
        .error-container {
            background: rgba(242, 54, 69, 0.1);
            border: 1px solid rgba(242, 54, 69, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .error-icon {
            color: #f23645;
            font-size: 16px;
        }
        
        .error-text {
            color: #f23645;
            font-size: 13px;
            font-weight: 500;
            margin: 0;
        }
        
        /* Footer de la tarjeta */
        .login-footer {
            background: #0c0e12;
            padding: 20px 30px;
            border-top: 1px solid #1a1e26;
            text-align: center;
        }
        
        .security-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #00ffad;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .footer-text {
            color: #555;
            font-size: 11px;
            margin-top: 8px;
        }
        
        /* Animación de carga */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .loading {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        /* Responsive */
        @media (max-width: 480px) {
            .login-card {
                max-width: 100%;
            }
            .login-header, .login-body {
                padding: 24px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Layout principal
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Verificar si existe logo
        logo_exists = os.path.exists("assets/logo.png")
        
        # Estructura HTML de la tarjeta
        st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # Header con logo
        st.markdown('<div class="login-header">', unsafe_allow_html=True)
        
        if logo_exists:
            st.image("assets/logo.png", use_container_width=False, width=80)
        else:
            st.markdown('<div class="login-logo">🔐</div>', unsafe_allow_html=True)
        
        st.markdown("""
            <h1 class="login-title">RSU Terminal</h1>
            <p class="login-subtitle">Sistema de Acceso Seguro</p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Cuerpo del formulario
        st.markdown('<div class="login-body">', unsafe_allow_html=True)
        
        # Label personalizado
        st.markdown('<label class="input-label">Contraseña de Acceso</label>', unsafe_allow_html=True)
        
        # Input de contraseña
        password = st.text_input(
            "",
            type="password",
            placeholder="Ingrese su contraseña...",
            label_visibility="collapsed"
        )
        
        # Botón de acceso
        if st.button("🔓 Desbloquear Terminal", use_container_width=True):
            real_pwd = st.secrets.get("APP_PASSWORD", "RSU2026")
            
            if password == real_pwd:
                st.session_state["auth"] = True
                st.success("✅ Acceso concedido")
                st.balloons()
                st.rerun()
            else:
                st.markdown("""
                    <div class="error-container">
                        <span class="error-icon">⚠️</span>
                        <span class="error-text">Contraseña incorrecta. Intente nuevamente.</span>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Cierre login-body
        
        # Footer con info de seguridad
        current_year = datetime.now().year
        st.markdown(f"""
            <div class="login-footer">
                <div class="security-badge">
                    <span>🔒</span>
                    <span>Conexión Segura SSL</span>
                </div>
                <div class="footer-text">
                    © {current_year} RSU Terminal v2.0 • Acceso Restringido
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Cierre login-card
        st.markdown('</div>', unsafe_allow_html=True)  # Cierre login-wrapper

    return False
