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

# ── THEMES ──────────────────────────────────────────────────────────────────────
THEMES = {
    "VT220": {
        "bg":       "#0a0800",
        "bg2":      "#110e00",
        "primary":  "#ffb300",
        "primary2": "#ff8c00",
        "dim":      "#7a5500",
        "dimmer":   "#3a2800",
        "glow":     "rgba(255,179,0,0.15)",
        "glow2":    "rgba(255,179,0,0.05)",
        "border":   "rgba(255,179,0,0.35)",
        "border2":  "rgba(255,179,0,0.15)",
        "label":    "VT220",
    },
    "GREEN": {
        "bg":       "#000d04",
        "bg2":      "#001508",
        "primary":  "#00ffad",
        "primary2": "#00d97a",
        "dim":      "#007a4a",
        "dimmer":   "#003020",
        "glow":     "rgba(0,255,173,0.15)",
        "glow2":    "rgba(0,255,173,0.05)",
        "border":   "rgba(0,255,173,0.35)",
        "border2":  "rgba(0,255,173,0.15)",
        "label":    "P3 GREEN",
    },
    "CYAN": {
        "bg":       "#00080d",
        "bg2":      "#001018",
        "primary":  "#00d9ff",
        "primary2": "#00aacc",
        "dim":      "#006688",
        "dimmer":   "#002030",
        "glow":     "rgba(0,217,255,0.15)",
        "glow2":    "rgba(0,217,255,0.05)",
        "border":   "rgba(0,217,255,0.35)",
        "border2":  "rgba(0,217,255,0.15)",
        "label":    "CYAN VDT",
    },
}

def get_logo_base64():
    try:
        if os.path.exists("assets/logo.png"):
            with open("assets/logo.png", "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return None

def _get_theme():
    return st.session_state.get("vt_theme", "VT220")

def login():
    # ── INIT ──────────────────────────────────────────────────────────────────
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
        st.session_state["login_attempts"] = 0
        st.session_state["lockout_time"] = None
        st.session_state["last_activity"] = None

    if "vt_theme" not in st.session_state:
        st.session_state["vt_theme"] = "VT220"

    if "vt_menu_open" not in st.session_state:
        st.session_state["vt_menu_open"] = False

    # ── SESSION TIMEOUT ───────────────────────────────────────────────────────
    if st.session_state["auth"] and st.session_state["last_activity"]:
        if datetime.now() - st.session_state["last_activity"] > timedelta(minutes=30):
            st.session_state["auth"] = False
            st.session_state["last_activity"] = None
            st.rerun()

    if st.session_state["auth"]:
        st.session_state["last_activity"] = datetime.now()
        return True

    # ── LOCKOUT ───────────────────────────────────────────────────────────────
    if st.session_state["lockout_time"]:
        if datetime.now() < st.session_state["lockout_time"]:
            remaining = int((st.session_state["lockout_time"] - datetime.now()).total_seconds() / 60)
            st.error(f"⏱ ACCESO BLOQUEADO — {remaining} MIN RESTANTES")
            return False
        else:
            st.session_state["lockout_time"] = None
            st.session_state["login_attempts"] = 0

    t = THEMES[_get_theme()]

    # ── THEME BUTTON CALLBACKS ─────────────────────────────────────────────────
    def toggle_menu():
        st.session_state["vt_menu_open"] = not st.session_state.get("vt_menu_open", False)

    def set_theme(name):
        st.session_state["vt_theme"] = name
        st.session_state["vt_menu_open"] = False

    # ── CSS ───────────────────────────────────────────────────────────────────
    bg        = t["bg"]
    bg2       = t["bg2"]
    primary   = t["primary"]
    primary2  = t["primary2"]
    dim       = t["dim"]
    dimmer    = t["dimmer"]
    glow      = t["glow"]
    glow2     = t["glow2"]
    border    = t["border"]
    border2   = t["border2"]
    label     = t["label"]

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

        /* ── GLOBAL ─────────────────────────────────────────── */
        #MainMenu, footer, header {{ visibility: hidden; }}

        .stApp {{
            background: {bg} !important;
        }}

        /* CRT scanlines overlay */
        .stApp::before {{
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0,0,0,0.18) 2px,
                rgba(0,0,0,0.18) 4px
            );
            pointer-events: none;
            z-index: 9998;
        }}

        /* CRT phosphor vignette */
        .stApp::after {{
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(ellipse at center,
                transparent 60%,
                rgba(0,0,0,0.55) 100%
            );
            pointer-events: none;
            z-index: 9997;
        }}

        /* ── LAYOUT ─────────────────────────────────────────── */
        .main .block-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 90vh;
            padding-top: 0 !important;
            max-width: 520px !important;
            margin: 0 auto;
        }}

        /* ── TOP BAR ─────────────────────────────────────────── */
        .vt-topbar {{
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid {border2};
            padding-bottom: 10px;
            margin-bottom: 32px;
            position: relative;
        }}

        .vt-topbar-left {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.75rem;
            color: {dim};
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        .vt-topbar-left span {{
            color: {primary};
            margin-right: 18px;
        }}

        .vt-topbar-right {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}

        .vt-badge {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.7rem;
            color: {dimmer};
            border: 1px solid {dimmer};
            padding: 2px 8px;
            border-radius: 2px;
            letter-spacing: 1px;
        }}

        /* ── THEME BUTTON ──────────────────────────────────────── */
        .vt-theme-btn {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.72rem;
            background: {bg2};
            color: {primary};
            border: 1px solid {primary};
            padding: 3px 10px;
            border-radius: 2px;
            letter-spacing: 1px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            box-shadow: 0 0 8px {glow};
            text-transform: uppercase;
        }}

        .vt-theme-btn::before {{
            content: '^T';
            color: {dim};
            font-size: 0.65rem;
        }}

        /* ── THEME DROPDOWN ─────────────────────────────────────── */
        .vt-menu {{
            background: {bg2};
            border: 1px solid {primary};
            border-radius: 3px;
            padding: 16px;
            margin-bottom: 20px;
            box-shadow: 0 0 30px {glow};
            width: 100%;
            box-sizing: border-box;
        }}

        .vt-menu-title {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.7rem;
            color: {dim};
            letter-spacing: 3px;
            text-transform: uppercase;
            text-align: center;
            margin-bottom: 12px;
            border-bottom: 1px solid {border2};
            padding-bottom: 8px;
        }}

        .vt-menu-title::before {{ content: '── '; }}
        .vt-menu-title::after  {{ content: ' ──'; }}

        .vt-option {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.85rem;
            padding: 8px 12px;
            border-radius: 2px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.1s;
            color: {primary};
            letter-spacing: 1px;
        }}

        .vt-option:hover {{
            background: {glow};
        }}

        .vt-option-dot {{
            font-size: 0.7rem;
            width: 14px;
            text-align: center;
            color: {dim};
        }}

        .vt-option-dot.active {{
            color: {primary};
        }}

        .vt-option-active {{
            background: {glow2};
        }}

        .vt-menu-hint {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.65rem;
            color: {dimmer};
            text-align: center;
            margin-top: 12px;
            letter-spacing: 1px;
            border-top: 1px solid {border2};
            padding-top: 8px;
        }}

        /* ── CARD ───────────────────────────────────────────── */
        .vt-card {{
            background: linear-gradient(160deg, {bg2} 0%, {bg} 100%);
            border: 1px solid {border};
            border-radius: 4px;
            padding: 40px 48px 36px;
            width: 100%;
            box-sizing: border-box;
            box-shadow: 0 0 50px {glow2}, inset 0 0 30px rgba(0,0,0,0.4);
        }}

        /* ── STATUS LINE ─────────────────────────────────────── */
        .vt-status {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.68rem;
            color: {dimmer};
            text-align: center;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 28px;
        }}

        .vt-status-dot {{
            display: inline-block;
            width: 6px;
            height: 6px;
            background: {primary};
            border-radius: 50%;
            margin-right: 8px;
            box-shadow: 0 0 6px {primary};
            vertical-align: middle;
            animation: blink 1.2s step-end infinite;
        }}

        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50%       {{ opacity: 0; }}
        }}

        /* ── LOGO / TITLE ────────────────────────────────────── */
        .vt-logo {{
            width: 88px;
            height: 88px;
            border-radius: 10px;
            display: block;
            margin: 0 auto 20px;
            box-shadow: 0 0 30px {glow}, 0 0 60px {glow2};
        }}

        .vt-logo-placeholder {{
            width: 88px;
            height: 88px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, {border2}, transparent);
            border: 1px solid {border};
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.2rem;
            box-shadow: 0 0 24px {glow2};
        }}

        .vt-title {{
            font-family: 'VT323', monospace;
            color: {primary};
            font-size: 3rem;
            text-align: center;
            letter-spacing: 8px;
            text-shadow: 0 0 20px {primary}, 0 0 40px {glow};
            margin-bottom: 2px;
            text-transform: uppercase;
            line-height: 1;
        }}

        .vt-subtitle {{
            font-family: 'Share Tech Mono', monospace;
            color: {dim};
            font-size: 0.72rem;
            text-align: center;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin-bottom: 30px;
        }}

        /* ── DIVIDER ─────────────────────────────────────────── */
        .vt-divider {{
            height: 1px;
            background: linear-gradient(90deg, transparent, {primary}55, transparent);
            margin: 0 0 28px;
        }}

        /* ── INPUT LABEL ─────────────────────────────────────── */
        .vt-label {{
            font-family: 'Share Tech Mono', monospace;
            color: {dim};
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 3px;
            text-align: left;
            display: block;
            margin-bottom: 6px;
        }}

        .vt-label::before {{ content: '▸ '; color: {primary}; }}

        /* ── INPUT ───────────────────────────────────────────── */
        .stTextInput > div > div > input {{
            background: {bg} !important;
            border: 1px solid {border} !important;
            border-radius: 3px !important;
            color: {primary} !important;
            height: 48px !important;
            font-family: 'VT323', monospace !important;
            font-size: 1.5rem !important;
            letter-spacing: 4px !important;
            text-align: left !important;
            padding: 0 14px !important;
            caret-color: {primary};
            transition: border-color 0.15s, box-shadow 0.15s;
        }}

        .stTextInput > div > div > input:focus {{
            border-color: {primary} !important;
            box-shadow: 0 0 14px {glow} !important;
            outline: none !important;
        }}

        .stTextInput > div > div > input::placeholder {{
            color: {dimmer} !important;
            letter-spacing: 6px;
        }}

        .stTextInput [data-testid="stIcon"] {{ display: none !important; }}

        /* ── BUTTON ─────────────────────────────────────────── */
        div[data-testid="stButton"] {{
            display: flex !important;
            justify-content: flex-start !important;
            width: 100% !important;
            margin-top: 6px !important;
        }}

        /* Small theme toggle buttons */
        div[data-testid="stButton"].theme-toggle-btn > button,
        .vt-small-btn > button {{
            min-width: 0 !important;
            width: auto !important;
            height: 28px !important;
            padding: 0 12px !important;
            font-size: 0.72rem !important;
            letter-spacing: 1px !important;
            margin-top: 0 !important;
        }}

        .stButton > button {{
            font-family: 'Share Tech Mono', monospace !important;
            background: transparent !important;
            color: {primary} !important;
            border: 1px solid {primary} !important;
            border-radius: 3px !important;
            font-size: 0.85rem !important;
            letter-spacing: 3px !important;
            width: 100% !important;
            height: 48px !important;
            padding: 0 !important;
            text-transform: uppercase !important;
            transition: all 0.15s !important;
            box-shadow: 0 0 10px {glow2} !important;
            margin-top: 20px !important;
        }}

        .stButton > button:hover {{
            background: {primary} !important;
            color: {bg} !important;
            box-shadow: 0 0 24px {glow} !important;
        }}

        .stButton > button:focus {{
            outline: 2px solid {primary} !important;
            outline-offset: 2px !important;
        }}

        /* ── ALERTS ─────────────────────────────────────────── */
        .stAlert {{
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.8rem !important;
            border-radius: 3px !important;
            margin-top: 12px !important;
        }}

        /* ── FOOTER ─────────────────────────────────────────── */
        .vt-footer {{
            font-family: 'Share Tech Mono', monospace;
            text-align: center;
            color: {dimmer};
            font-size: 0.65rem;
            margin-top: 28px;
            padding-top: 16px;
            border-top: 1px solid {border2};
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        .vt-footer span {{ color: {dim}; }}

        /* ── KEYBOARD HINT ───────────────────────────────────── */
        .vt-kbd-hint {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.62rem;
            color: {dimmer};
            text-align: right;
            letter-spacing: 1px;
            margin-top: 6px;
        }}

        .vt-kbd-hint kbd {{
            background: {bg2};
            border: 1px solid {dimmer};
            border-radius: 2px;
            padding: 1px 5px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.6rem;
            color: {dim};
        }}

        /* Hide stray streamlit borders */
        div[data-testid="stHorizontalBlock"],
        div[data-testid="column"] {{
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    logo_b64 = get_logo_base64()
    cur_theme = _get_theme()

    # ── KEYBOARD HANDLER (JS) ────────────────────────────────────────────────
    # Inject JS for Enter-to-submit and Esc-to-close menu
    st.markdown("""
    <script>
    (function() {
        function waitAndBind() {
            const input = document.querySelector('input[type="password"]');
            const btns  = document.querySelectorAll('button');
            let loginBtn = null;
            btns.forEach(b => {
                if (b.innerText.includes('ENTER') || b.innerText.includes('ACCESS') || b.innerText.includes('UNLOCK')) loginBtn = b;
            });
            if (input) {
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && loginBtn) loginBtn.click();
                    if (e.key === 'Escape') {
                        // Close menu if open — click the VT220 toggle
                        const toggles = document.querySelectorAll('button');
                        toggles.forEach(b => { if (b.innerText.includes('VT220') || b.innerText.includes('GREEN') || b.innerText.includes('CYAN')) b.blur(); });
                    }
                });
                input.focus();
            }
        }
        setTimeout(waitAndBind, 600);
    })();
    </script>
    """, unsafe_allow_html=True)

    # ── TOP BAR ──────────────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.markdown(f"""
        <div class="vt-topbar-left">
            <span>^1</span>LOGIN
            &nbsp;&nbsp;
            <span>^2</span>STATUS
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        if st.button(f"^T  {label}", key="btn_theme_toggle", help="Cambiar tema (^T)"):
            toggle_menu()

    # ── THEME MENU ────────────────────────────────────────────────────────────
    if st.session_state.get("vt_menu_open", False):
        st.markdown(f"""
        <div class="vt-menu">
            <div class="vt-menu-title">APPEARANCE</div>
        </div>
        """, unsafe_allow_html=True)

        theme_cols = st.columns(3)
        theme_list = list(THEMES.keys())

        for i, (tkey, tdata) in enumerate(THEMES.items()):
            is_active = (tkey == cur_theme)
            marker = "▶" if is_active else "○"
            with theme_cols[i]:
                if st.button(
                    f"{marker} {tdata['label']}",
                    key=f"theme_{tkey}",
                    help=f"Activar tema {tdata['label']}"
                ):
                    set_theme(tkey)
                    st.rerun()

        st.markdown(f"""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:{t['dimmer']}; text-align:center; letter-spacing:1px;
                    margin-top:4px; padding-top:8px; border-top:1px solid {t['border2']};">
            ↑↓ NAV &nbsp;·&nbsp; ↵ SEL &nbsp;·&nbsp; ESC
        </div>
        """, unsafe_allow_html=True)

    # ── MAIN CARD ─────────────────────────────────────────────────────────────
    st.markdown(f'<div class="vt-card">', unsafe_allow_html=True)

    # Status
    st.markdown(f"""
    <div class="vt-status">
        <span class="vt-status-dot"></span>
        SECURE CONNECTION &nbsp;·&nbsp; AES-256 &nbsp;·&nbsp; TLS 1.3
    </div>
    """, unsafe_allow_html=True)

    # Logo
    if logo_b64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_b64}" class="vt-logo">',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="vt-logo-placeholder">⬡</div>', unsafe_allow_html=True)

    # Title
    st.markdown('<div class="vt-title">RSU TERMINAL</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="vt-subtitle">SISTEMA DE ACCESO // v2.0</div>', unsafe_allow_html=True)
    st.markdown('<div class="vt-divider"></div>', unsafe_allow_html=True)

    # Input label
    st.markdown('<span class="vt-label">PASSWORD</span>', unsafe_allow_html=True)

    password = st.text_input(
        "",
        type="password",
        placeholder="················",
        label_visibility="collapsed",
        key="login_password"
    )

    # Keyboard hint
    st.markdown(f"""
    <div class="vt-kbd-hint">
        <kbd>ENTER</kbd> confirmar &nbsp;·&nbsp; <kbd>TAB</kbd> navegar
    </div>
    """, unsafe_allow_html=True)

    # ── LOGIN BUTTON ──────────────────────────────────────────────────────────
    button_clicked = st.button(
        "[ ENTER // UNLOCK TERMINAL ]",
        key="btn_login",
        use_container_width=True
    )

    if button_clicked:
        if not password:
            st.error("⚠  INGRESE CONTRASEÑA")
        else:
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            real_pwd = st.secrets.get("APP_PASSWORD", "")
            real_hash = hashlib.sha256(real_pwd.encode()).hexdigest()

            if pwd_hash == real_hash:
                st.session_state["auth"] = True
                st.session_state["login_attempts"] = 0
                st.session_state["last_activity"] = datetime.now()
                st.success("✓  ACCESO CONCEDIDO — INICIALIZANDO...")
                time.sleep(0.4)
                st.rerun()
            else:
                st.session_state["login_attempts"] += 1
                remaining = 5 - st.session_state["login_attempts"]
                if st.session_state["login_attempts"] >= 5:
                    st.session_state["lockout_time"] = datetime.now() + timedelta(minutes=15)
                    st.error("⛔  ACCESO BLOQUEADO — 15 MIN")
                else:
                    st.error(f"⚠  CONTRASEÑA INCORRECTA — {remaining} INTENTOS RESTANTES")

    # Footer
    st.markdown(f"""
    <div class="vt-footer">
        🔒 SSL ENCRYPTED &nbsp;·&nbsp;
        <span>© 2026 RSU TERMINAL // STATUS: ACTIVE</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close vt-card

    return False


def logout():
    st.session_state["auth"] = False
    st.session_state["last_activity"] = None
    st.success("SESSION TERMINATED")
    time.sleep(0.3)
    st.rerun()


def require_auth():
    if "auth" not in st.session_state or not st.session_state["auth"]:
        st.error("🔒 ACCESO DENEGADO")
        login()
        st.stop()
    st.session_state["last_activity"] = datetime.now()
