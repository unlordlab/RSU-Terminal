
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
    # Inicialización
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
        st.session_state["login_attempts"] = 0
        st.session_state["lockout_time"] = None
        st.session_state["last_activity"] = None

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

    # ── CSS TERMINAL AESTHETIC ──────────────────────────────────────────────────
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        /* Ocultar elementos de Streamlit */
        #MainMenu, footer, header { visibility: hidden; }

        /* Fondo global */
        .stApp { background: #0c0e12; }

        /* Wrapper centrado en pantalla */
        .main .block-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 90vh;
            padding-top: 0 !important;
            max-width: 480px !important;
            margin: 0 auto;
        }

        /* Caja terminal principal */
        div[data-testid="stVerticalBlock"] {
            background: linear-gradient(135deg, #0c0e12 0%, #11141a 100%);
            border: 1px solid #00ffad44;
            border-radius: 8px;
            padding: 48px 52px;
            max-width: 460px;
            width: 100%;
            margin: 0 auto;
            box-shadow: 0 0 40px #00ffad11, 0 0 80px #00ffad08;
        }

        /* Status bar superior */
        .terminal-status {
            font-family: 'VT323', monospace;
            font-size: 0.85rem;
            color: #444;
            text-align: center;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 28px;
        }

        /* Logo */
        .logo-img {
            width: 120px;
            height: 120px;
            border-radius: 12px;
            margin: 0 auto 24px;
            display: block;
            box-shadow: 0 0 30px #00ffad33, 0 0 60px #00ffad11;
        }

        .logo-placeholder {
            width: 120px;
            height: 120px;
            margin: 0 auto 24px;
            background: linear-gradient(135deg, #00ffad22, #00d9ff11);
            border: 1px solid #00ffad44;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            box-shadow: 0 0 30px #00ffad22;
        }

        /* Títulos VT323 */
        h1 {
            font-family: 'VT323', monospace !important;
            color: #00ffad !important;
            font-size: 2.8rem !important;
            text-align: center !important;
            letter-spacing: 5px !important;
            text-shadow: 0 0 20px #00ffad66 !important;
            margin-bottom: 4px !important;
            margin-top: 0 !important;
            text-transform: uppercase;
        }

        .subtitle {
            font-family: 'VT323', monospace;
            color: #00d9ff;
            font-size: 1.1rem;
            text-align: center;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 36px;
        }

        /* Separador tipo terminal */
        .term-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad44, transparent);
            margin: 0 0 32px 0;
        }

        /* Label del input */
        .input-label {
            font-family: 'VT323', monospace;
            color: #00ffad99;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-align: center;
            display: block;
            margin-bottom: 8px;
        }

        /* Input password */
        .stTextInput > div > div > input {
            background: #0c0e12 !important;
            border: 1px solid #00ffad33 !important;
            border-radius: 6px !important;
            color: #00ffad !important;
            height: 52px !important;
            font-family: 'VT323', monospace !important;
            font-size: 1.3rem !important;
            letter-spacing: 3px !important;
            text-align: center !important;
            caret-color: #00ffad;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .stTextInput > div > div > input:focus {
            border-color: #00ffad88 !important;
            box-shadow: 0 0 12px #00ffad22 !important;
        }

        .stTextInput > div > div > input::placeholder {
            color: #333 !important;
            letter-spacing: 2px;
        }

        /* Ocultar ojo de Streamlit */
        .stTextInput [data-testid="stIcon"] { display: none !important; }

        /* Botón */
        div[data-testid="stButton"] {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            margin-top: 28px !important;
        }

        .stButton > button {
            font-family: 'VT323', monospace !important;
            background: transparent !important;
            color: #00ffad !important;
            border: 1px solid #00ffad !important;
            border-radius: 6px !important;
            font-size: 1.3rem !important;
            letter-spacing: 3px !important;
            width: auto !important;
            min-width: 240px !important;
            height: 52px !important;
            padding: 0 28px !important;
            margin: 0 auto !important;
            text-transform: uppercase !important;
            transition: all 0.2s !important;
            box-shadow: 0 0 12px #00ffad22 !important;
        }

        .stButton > button:hover {
            background: #00ffad !important;
            color: #0c0e12 !important;
            box-shadow: 0 0 24px #00ffad55 !important;
        }

        /* Alertas con fuente terminal */
        .stAlert {
            font-family: 'Courier New', monospace !important;
            font-size: 0.85rem !important;
            border-radius: 6px !important;
        }

        /* Ocultar bordes de columnas */
        div[data-testid="stHorizontalBlock"],
        div[data-testid="column"] {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }

        /* Footer */
        .term-footer {
            font-family: 'VT323', monospace;
            text-align: center;
            color: #444;
            font-size: 0.9rem;
            margin-top: 32px;
            padding-top: 20px;
            border-top: 1px solid #1a1e26;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .term-footer span {
            color: #00ffad66;
        }
    </style>
    """, unsafe_allow_html=True)

    logo_b64 = get_logo_base64()

    # ── STATUS BAR ──────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="terminal-status">[SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]</div>',
        unsafe_allow_html=True
    )

    # ── LOGO ────────────────────────────────────────────────────────────────────
    if logo_b64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="logo-placeholder">🔐</div>',
            unsafe_allow_html=True
        )

    # ── TÍTULOS ─────────────────────────────────────────────────────────────────
    st.markdown("<h1>RSU TERMINAL</h1>", unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Sistema de Acceso Seguro</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="term-divider"></div>', unsafe_allow_html=True)

    # ── INPUT ───────────────────────────────────────────────────────────────────
    st.markdown(
        '<span class="input-label">▸ Contraseña de Acceso</span>',
        unsafe_allow_html=True
    )

    password = st.text_input(
        "",
        type="password",
        placeholder="_ _ _ _ _ _ _ _",
        label_visibility="collapsed"
    )

    # ── BOTÓN ───────────────────────────────────────────────────────────────────
    button_clicked = st.button("🔓 DESBLOQUEAR TERMINAL")

    if button_clicked:
        if not password:
            st.error("⚠️ Ingrese una contraseña")
        else:
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            real_pwd = st.secrets.get("APP_PASSWORD")
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
                    st.error("⚠️ Contraseña incorrecta")
                    if 5 - st.session_state["login_attempts"] <= 2:
                        st.warning(f"⚠️ {5 - st.session_state['login_attempts']} intentos restantes")

    # ── FOOTER ──────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="term-footer">'
        '🔒 Conexión segura SSL<br>'
        '<span>© 2026 RSU Terminal v2.0 // STATUS: ACTIVE</span>'
        '</div>',
        unsafe_allow_html=True
    )

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
