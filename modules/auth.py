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
        "bg":      "#0a0800",
        "bg2":     "#130f00",
        "primary": "#ffb300",
        "dim":     "#6b4800",
        "dimmer":  "#2e1f00",
        "border":  "#3d2900",
        "glow":    "rgba(255,179,0,0.18)",
        "label":   "VT220",
    },
    "GREEN": {
        "bg":      "#000d04",
        "bg2":     "#001508",
        "primary": "#00ffad",
        "dim":     "#006640",
        "dimmer":  "#002418",
        "border":  "#003820",
        "glow":    "rgba(0,255,173,0.18)",
        "label":   "P3 GREEN",
    },
    "CYAN": {
        "bg":      "#00080d",
        "bg2":     "#001018",
        "primary": "#00d9ff",
        "dim":     "#005566",
        "dimmer":  "#001e28",
        "border":  "#002c38",
        "glow":    "rgba(0,217,255,0.18)",
        "label":   "CYAN VDT",
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


def login():
    # ── INIT ──────────────────────────────────────────────────────────────────
    for k, v in [
        ("auth", False), ("login_attempts", 0),
        ("lockout_time", None), ("last_activity", None),
        ("vt_theme", "VT220"), ("vt_menu_open", False),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ── TIMEOUT ───────────────────────────────────────────────────────────────
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

    t = THEMES[st.session_state["vt_theme"]]
    bg      = t["bg"]
    bg2     = t["bg2"]
    primary = t["primary"]
    dim     = t["dim"]
    dimmer  = t["dimmer"]
    border  = t["border"]
    glow    = t["glow"]
    label   = t["label"]

    logo_b64 = get_logo_base64()

    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

        /* ── RESET / GLOBAL ─────────────────────────────────── */
        #MainMenu, footer, header {{ visibility: hidden; }}

        html, body, .stApp {{
            background: {bg} !important;
            margin: 0;
            padding: 0;
        }}

        /* CRT scanlines */
        .stApp::before {{
            content: '';
            position: fixed;
            inset: 0;
            background: repeating-linear-gradient(
                to bottom,
                transparent 0px,
                transparent 3px,
                rgba(0,0,0,0.22) 3px,
                rgba(0,0,0,0.22) 4px
            );
            pointer-events: none;
            z-index: 9998;
        }}

        /* Phosphor vignette */
        .stApp::after {{
            content: '';
            position: fixed;
            inset: 0;
            background: radial-gradient(ellipse at 50% 50%,
                transparent 55%, rgba(0,0,0,0.65) 100%);
            pointer-events: none;
            z-index: 9997;
        }}

        /* ── STREAMLIT LAYOUT OVERRIDES ──────────────────────── */
        .main .block-container {{
            max-width: 640px !important;
            padding: 0 !important;
            margin: 0 auto !important;
        }}

        section[data-testid="stMain"] > div {{
            padding: 0 !important;
        }}

        /* Remove any card look from stVerticalBlock */
        div[data-testid="stVerticalBlock"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }}

        div[data-testid="stHorizontalBlock"],
        div[data-testid="column"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            gap: 0 !important;
        }}

        /* ── TOP MENUBAR ─────────────────────────────────────── */
        .vt-menubar {{
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: stretch;
            background: {bg2};
            border-bottom: 1px solid {border};
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 1px;
            height: 32px;
            box-sizing: border-box;
            margin-bottom: 0;
        }}

        .vt-menubar-left {{
            display: flex;
            align-items: stretch;
        }}

        .vt-tab {{
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: {primary};
            border-right: 1px solid {border};
            white-space: nowrap;
            cursor: default;
            opacity: 0.9;
        }}

        .vt-tab .key {{
            color: {dim};
            margin-right: 2px;
        }}

        .vt-tab.active {{
            background: {primary};
            color: {bg};
            font-weight: bold;
            opacity: 1;
        }}

        .vt-tab.active .key {{
            color: {bg};
        }}

        .vt-menubar-right {{
            display: flex;
            align-items: stretch;
            border-left: 1px solid {border};
        }}

        .vt-theme-chip {{
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: {primary};
            background: {bg2};
            border-left: 1px solid {border};
            white-space: nowrap;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 1px;
            cursor: pointer;
            text-decoration: none;
        }}

        .vt-theme-chip .key {{
            color: {dim};
            margin-right: 4px;
        }}

        .vt-site-chip {{
            display: flex;
            align-items: center;
            padding: 0 12px;
            color: {primary};
            background: {bg};
            border-left: 1px solid {border};
            white-space: nowrap;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 1px;
        }}

        /* ── THEME DROPDOWN ─────────────────────────────────── */
        .vt-dropdown {{
            background: {bg2};
            border: 1px solid {primary};
            width: 260px;
            margin: 0 auto 0;
            box-shadow: 0 4px 24px {glow};
        }}

        .vt-dropdown-title {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.68rem;
            color: {dim};
            letter-spacing: 3px;
            text-align: center;
            padding: 8px 0 6px;
            border-bottom: 1px solid {border};
            text-transform: uppercase;
        }}

        .vt-dropdown-footer {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.6rem;
            color: {dimmer};
            text-align: center;
            padding: 6px 0;
            border-top: 1px solid {border};
            letter-spacing: 1px;
        }}

        /* ── CONTENT AREA ────────────────────────────────────── */
        .vt-content {{
            padding: 28px 0 0;
            width: 100%;
        }}

        /* ── LOGIN BOX ───────────────────────────────────────── */
        .vt-loginbox {{
            border: 1px solid {border};
            width: 380px;
            margin: 0 auto;
            box-sizing: border-box;
        }}

        .vt-loginbox-title {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.7rem;
            color: {primary};
            letter-spacing: 3px;
            text-align: center;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 28px;
            border-bottom: 1px solid {border};
            background: {bg2};
        }}

        .vt-loginbox-title::before {{
            content: '── ';
            color: {border};
            margin-right: 6px;
        }}
        .vt-loginbox-title::after {{
            content: ' ──';
            color: {border};
            margin-left: 6px;
        }}

        .vt-loginbox-body {{
            padding: 20px 24px 20px;
        }}

        /* ── MAIN TITLE ──────────────────────────────────────── */
        .vt-apptitle {{
            font-family: 'VT323', monospace;
            color: {primary};
            font-size: 2.4rem;
            letter-spacing: 6px;
            text-align: center;
            text-shadow: 0 0 18px {glow}, 0 0 6px {primary};
            margin: 0 0 2px;
            text-transform: uppercase;
            line-height: 1;
        }}

        .vt-appsubtitle {{
            font-family: 'Share Tech Mono', monospace;
            color: {dim};
            font-size: 0.62rem;
            letter-spacing: 3px;
            text-align: center;
            text-transform: uppercase;
            margin-bottom: 18px;
        }}

        /* ── FIELD LABELS ────────────────────────────────────── */
        .vt-field-label {{
            font-family: 'Share Tech Mono', monospace;
            color: {primary};
            font-size: 0.72rem;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 2px;
            display: block;
        }}

        /* ── INPUT ───────────────────────────────────────────── */
        .stTextInput > label {{ display: none !important; }}

        .stTextInput > div > div > input {{
            background: {bg2} !important;
            border: none !important;
            border-bottom: 1px solid {dim} !important;
            border-radius: 0 !important;
            color: {primary} !important;
            height: 36px !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.9rem !important;
            letter-spacing: 2px !important;
            padding: 0 8px !important;
            caret-color: {primary};
            transition: border-color 0.1s;
            width: 100% !important;
        }}

        .stTextInput > div > div > input:focus {{
            border-bottom-color: {primary} !important;
            box-shadow: 0 2px 8px {glow} !important;
            outline: none !important;
        }}

        .stTextInput > div > div > input::placeholder {{
            color: {dimmer} !important;
            font-style: italic;
        }}

        .stTextInput [data-testid="stIcon"] {{ display: none !important; }}
        .stTextInput > div {{ border: none !important; box-shadow: none !important; }}

        /* ── BUTTON ─────────────────────────────────────────── */
        div[data-testid="stButton"] {{
            width: 100% !important;
            margin-top: 0 !important;
        }}

        .stButton > button {{
            font-family: 'Share Tech Mono', monospace !important;
            background: {primary} !important;
            color: {bg} !important;
            border: none !important;
            border-radius: 0 !important;
            font-size: 0.85rem !important;
            letter-spacing: 3px !important;
            width: 100% !important;
            height: 44px !important;
            padding: 0 !important;
            text-transform: uppercase !important;
            margin-top: 16px !important;
            transition: opacity 0.1s !important;
            box-shadow: 0 0 20px {glow} !important;
        }}

        .stButton > button:hover {{
            opacity: 0.85 !important;
        }}

        .stButton > button:focus {{
            outline: 2px solid {primary} !important;
            outline-offset: 2px !important;
        }}

        /* Theme option buttons — override the full-width default */
        [data-testid="stButton"][key*="theme_"] > button,
        .theme-opt .stButton > button {{
            background: transparent !important;
            color: {primary} !important;
            border: none !important;
            height: 32px !important;
            font-size: 0.78rem !important;
            margin-top: 0 !important;
            box-shadow: none !important;
            letter-spacing: 2px !important;
            text-align: left !important;
            justify-content: flex-start !important;
        }}

        .theme-opt .stButton > button:hover {{
            background: rgba(255,255,255,0.04) !important;
            opacity: 1 !important;
        }}

        /* ── ALERTS ─────────────────────────────────────────── */
        .stAlert {{
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.75rem !important;
            border-radius: 0 !important;
            margin-top: 8px !important;
            border-left: 2px solid {primary} !important;
        }}

        /* ── STATUS DOT ──────────────────────────────────────── */
        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50%       {{ opacity: 0.1; }}
        }}

        .vt-dot {{
            display: inline-block;
            width: 5px; height: 5px;
            background: {primary};
            border-radius: 50%;
            margin-right: 5px;
            vertical-align: middle;
            animation: blink 1.1s step-end infinite;
            box-shadow: 0 0 5px {primary};
        }}

        .vt-status-bar {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.62rem;
            color: {dimmer};
            text-align: center;
            letter-spacing: 2px;
            text-transform: uppercase;
            padding: 10px 0 4px;
        }}

        /* ── FOOTER ─────────────────────────────────────────── */
        .vt-footer {{
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.6rem;
            color: {dimmer};
            text-align: center;
            letter-spacing: 2px;
            text-transform: uppercase;
            padding: 12px 0 0;
            margin-top: 10px;
            border-top: 1px solid {border};
        }}

        .vt-footer span {{ color: {dim}; }}
    </style>
    """, unsafe_allow_html=True)

    # ── TOP MENUBAR ───────────────────────────────────────────────────────────
    site_name = "RSU TERMINAL"
    st.markdown(f"""
    <div class="vt-menubar">
        <div class="vt-menubar-left">
            <div class="vt-tab active"><span class="key">^1</span>&nbsp;LOGIN</div>
            <div class="vt-tab"><span class="key">^2</span>&nbsp;STATUS</div>
            <div class="vt-tab"><span class="key">^3</span>&nbsp;INFO</div>
        </div>
        <div class="vt-menubar-right">
            <div class="vt-theme-chip" id="vt-theme-trigger">
                <span class="key">^T</span>&nbsp;{label}
            </div>
            <div class="vt-site-chip">{site_name}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── THEME TOGGLE BUTTON (invisible, triggers menu) ────────────────────────
    col_dummy, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button(f"^T {label}", key="btn_theme_toggle",
                     help="Cambiar tema (^T)"):
            st.session_state["vt_menu_open"] = not st.session_state.get("vt_menu_open", False)
            st.rerun()

    # ── THEME DROPDOWN ────────────────────────────────────────────────────────
    if st.session_state.get("vt_menu_open", False):
        st.markdown(f"""
        <div class="vt-dropdown">
            <div class="vt-dropdown-title">── APPEARANCE ──</div>
        </div>
        """, unsafe_allow_html=True)

        for tkey, tdata in THEMES.items():
            is_active = (tkey == st.session_state["vt_theme"])
            marker = "▶" if is_active else "○"
            arrow = " ←" if is_active else ""
            st.markdown('<div class="theme-opt">', unsafe_allow_html=True)
            if st.button(f"  {marker}  {tdata['label']}{arrow}", key=f"theme_{tkey}"):
                st.session_state["vt_theme"] = tkey
                st.session_state["vt_menu_open"] = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="vt-dropdown">
            <div class="vt-dropdown-footer">↑↓ NAV · ↵ SEL · ESC</div>
        </div>
        """, unsafe_allow_html=True)

    # ── LOGIN BOX ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="vt-content">
        <div class="vt-loginbox">
            <div class="vt-loginbox-title">LOGIN</div>
            <div class="vt-loginbox-body">
    """, unsafe_allow_html=True)

    # App title inside box
    if logo_b64:
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:12px;">
            <img src="data:image/png;base64,{logo_b64}"
                 style="width:64px;height:64px;border-radius:6px;
                        box-shadow:0 0 20px {glow};">
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="vt-apptitle">RSU TERMINAL</div>
    <div class="vt-appsubtitle">Redistribution Strategy Unit</div>
    """, unsafe_allow_html=True)

    # Password field
    st.markdown('<span class="vt-field-label">PASSWORD</span>', unsafe_allow_html=True)
    password = st.text_input(
        "password",
        type="password",
        placeholder="Enter your password",
        label_visibility="collapsed",
        key="login_password"
    )

    # Login button
    button_clicked = st.button("SIGN IN", key="btn_login", use_container_width=True)

    st.markdown('</div></div></div>', unsafe_allow_html=True)  # close loginbox-body, loginbox, vt-content

    # Status bar below box
    st.markdown(f"""
    <div class="vt-status-bar">
        <span class="vt-dot"></span>
        SECURE CONNECTION · AES-256 · TLS 1.3
    </div>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div class="vt-footer">
        🔒 SSL ENCRYPTED ·
        <span>© 2026 RSU TERMINAL v2.0 // STATUS: ACTIVE</span>
    </div>
    """, unsafe_allow_html=True)

    # ── AUTH LOGIC ────────────────────────────────────────────────────────────
    if button_clicked:
        if not password:
            st.error("⚠  INGRESE CONTRASEÑA")
        else:
            pwd_hash  = hashlib.sha256(password.encode()).hexdigest()
            real_pwd  = st.secrets.get("APP_PASSWORD", "")
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

    # ── KEYBOARD ENTER HANDLER ────────────────────────────────────────────────
    st.markdown("""
    <script>
    (function() {
        function bindKeys() {
            const inp = document.querySelector('input[type="password"]');
            if (!inp) { setTimeout(bindKeys, 500); return; }
            inp.focus();
            inp.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const signIn = btns.find(b => b.innerText.trim() === 'SIGN IN');
                    if (signIn) signIn.click();
                }
            });
        }
        setTimeout(bindKeys, 600);
    })();
    </script>
    """, unsafe_allow_html=True)

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
