# modules/auth.py
import os
import streamlit as st
from datetime import datetime

def login():
    # Inicialización del estado de autenticación
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
    
    if st.session_state["auth"]:
        return True

    # CSS personalizado para estética profesional
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .main {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    }
    
    .login-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 3rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        max-width: 450px;
        margin: 0 auto;
    }
    
    .login-header {
        font-family: 'Inter', sans-serif;
        color: #ffffff;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-title {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: 2px;
        margin-top: 1rem;
        background: linear-gradient(90deg, #00d4aa, #00a8e8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .login-subtitle {
        font-size: 0.9rem;
        color: #8892b0;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00d4aa !important;
        box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.1) !important;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #00d4aa, #00a8e8) !important;
        color: #1e1e2e !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.8rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 1px;
        transition: all 0.3s ease !important;
        margin-top: 1.5rem !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0, 212, 170, 0.3) !important;
    }
    
    .error-message {
        background: rgba(255, 71, 87, 0.1);
        border: 1px solid rgba(255, 71, 87, 0.3);
        border-radius: 8px;
        padding: 0.8rem;
        color: #ff4757;
        text-align: center;
        margin-top: 1rem;
        font-size: 0.9rem;
    }
    
    .footer-text {
        text-align: center;
        color: #8892b0;
        font-size: 0.75rem;
        margin-top: 2rem;
        opacity: 0.7;
    }
    
    /* Ocultar elementos de Streamlit por defecto */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    # Layout centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Contenedor principal de login
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Logo y título
        logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
        with logo_col2:
            if os.path.exists("assets/logo.png"):
                st.image("assets/logo.png", use_container_width=True)
            else:
                # Icono por defecto si no hay logo
                st.markdown("""
                <div style="text-align: center; font-size: 4rem; margin-bottom: 1rem;">
                    🔐
                </div>
                """, unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="login-header">
            <div class="login-title">RSU TERMINAL</div>
            <div class="login-subtitle">Sistema de Acceso Seguro</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Formulario
        password = st.text_input(
            "Contraseña de Acceso",
            type="password",
            placeholder="Ingrese su contraseña...",
            label_visibility="collapsed"
        )
        
        # Botón de acceso
        if st.button("🔓 ACCEDER AL SISTEMA", use_container_width=True):
            real_pwd = st.secrets.get("APP_PASSWORD", "RSU2026")
            
            if password == real_pwd:
                st.session_state["auth"] = True
                st.success("✅ Acceso concedido. Redirigiendo...")
                st.balloons()
                st.rerun()
            else:
                st.markdown("""
                <div class="error-message">
                    ⚠️ Contraseña incorrecta. Intente nuevamente.
                </div>
                """, unsafe_allow_html=True)
        
        # Footer
        current_year = datetime.now().year
        st.markdown(f"""
        <div class="footer-text">
            © {current_year} RSU Terminal • v2.0<br>
            Acceso restringido a personal autorizado
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    return False
