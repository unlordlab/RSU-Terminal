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

THEMES = {
    "VT220": {
        "pri": "#ffb300", "bg": "#0a0800", "bg2": "#130f00", "bg3": "#1a1200",
        "border": "#3d2900", "mid": "#5a3e00", "dim": "#7a5500", "dark": "#1e1400",
        "label": "VT220",
    },
    "GREEN": {
        "pri": "#00ffad", "bg": "#000d04", "bg2": "#001508", "bg3": "#001e0a",
        "border": "#003820", "mid": "#006640", "dim": "#008855", "dark": "#001810",
        "label": "P3 GREEN",
    },
    "CYAN": {
        "pri": "#00d9ff", "bg": "#00080d", "bg2": "#001018", "bg3": "#001520",
        "border": "#002c38", "mid": "#005566", "dim": "#006680", "dark": "#000c14",
        "label": "CYAN VDT",
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
    pri    = t["pri"]
    bg     = t["bg"]
    bg2    = t["bg2"]
    bg3    = t["bg3"]
    border = t["border"]
    mid    = t["mid"]
    dim    = t["dim"]
    dark   = t["dark"]
    label  = t["label"]

    logo_b64 = get_logo_base64()

    # Build theme JS object for the switcher
    themes_js = "{"
    for k, v in THEMES.items():
        themes_js += f'"{k}":{{"pri":"{v["pri"]}","bg":"{v["bg"]}","bg2":"{v["bg2"]}","bg3":"{v["bg3"]}","border":"{v["border"]}","mid":"{v["mid"]}","dim":"{v["dim"]}","dark":"{v["dark"]}","label":"{v["label"]}"}},'
    themes_js = themes_js.rstrip(",") + "}"

    # ── CSS + HTML ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

        #MainMenu, footer, header {{ visibility: hidden !important; }}

        html, body, .stApp {{
            background: {bg} !important;
        }}

        /* CRT scanlines */
        .stApp::before {{
            content: '';
            position: fixed; inset: 0;
            background: repeating-linear-gradient(
                to bottom,
                transparent 0, transparent 3px,
                rgba(0,0,0,0.25) 3px, rgba(0,0,0,0.25) 4px
            );
            pointer-events: none; z-index: 9998;
        }}

        /* phosphor vignette */
        .stApp::after {{
            content: '';
            position: fixed; inset: 0;
            background: radial-gradient(ellipse 90% 90% at 50% 50%, transparent 50%, rgba(0,0,0,0.7) 100%);
            pointer-events: none; z-index: 9997;
        }}

        /* Strip all Streamlit chrome */
        .main .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }}

        section[data-testid="stMain"] > div {{ padding: 0 !important; }}

        div[data-testid="stVerticalBlock"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            gap: 0 !important;
        }}

        div[data-testid="stHorizontalBlock"],
        div[data-testid="column"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            gap: 0 !important;
            min-height: 0 !important;
        }}

        /* ── INPUT ────────────────────────────────────────── */
        .stTextInput > label {{ display: none !important; }}

        .stTextInput > div {{
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
            padding: 0 !important;
        }}

        .stTextInput > div > div > input {{
            background: {bg3} !important;
            border: none !important;
            border-bottom: 1px solid {border} !important;
            border-radius: 0 !important;
            color: {pri} !important;
            height: 30px !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.82rem !important;
            letter-spacing: 1px !important;
            padding: 0 8px !important;
            caret-color: {pri};
            transition: border-color 0.1s;
            width: 100% !important;
        }}

        .stTextInput > div > div > input:focus {{
            border-bottom-color: {dim} !important;
            box-shadow: none !important;
            outline: none !important;
        }}

        .stTextInput > div > div > input::placeholder {{
            color: {border} !important;
            font-style: italic;
        }}

        .stTextInput [data-testid="stIcon"] {{ display: none !important; }}

        /* ── BUTTON ──────────────────────────────────────── */
        div[data-testid="stButton"] {{
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }}

        .stButton > button {{
            font-family: 'Share Tech Mono', monospace !important;
            background: {pri} !important;
            color: {bg} !important;
            border: none !important;
            border-radius: 0 !important;
            font-size: 0.85rem !important;
            letter-spacing: 4px !important;
            width: 100% !important;
            height: 44px !important;
            padding: 0 !important;
            text-transform: uppercase !important;
            margin: 0 !important;
            transition: opacity 0.1s !important;
            box-shadow: none !important;
        }}

        .stButton > button:hover {{ opacity: 0.85 !important; }}
        .stButton > button:focus {{ outline: 2px solid {pri} !important; outline-offset: 2px !important; }}

        /* ── ALERTS ──────────────────────────────────────── */
        .stAlert {{
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.75rem !important;
            border-radius: 0 !important;
            border-left: 2px solid {pri} !important;
            background: {bg2} !important;
        }}

        /* theme toggle btn — hidden visually, keep functionality */
        #theme-toggle-row {{
            position: absolute; top: 0; right: 0;
            opacity: 0; pointer-events: none;
            height: 0; overflow: hidden;
        }}
    </style>
    """, unsafe_allow_html=True)

    # ── FULL PAGE HTML ────────────────────────────────────────────────────────
    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="display:block;width:56px;height:56px;border-radius:6px;margin:0 auto 10px;box-shadow:0 0 16px rgba(255,179,0,0.3);">'

    cur_theme = st.session_state["vt_theme"]

    def dot(k):
        return "▶" if k == cur_theme else "○"
    def arrow(k):
        return '<span style="margin-left:auto;font-size:0.62rem;color:' + dim + ';">←</span>' if k == cur_theme else ""
    def dot_cls(k):
        return dim if k == cur_theme else border

    st.markdown(f"""
    <div id="vt-root" style="
        font-family:'Share Tech Mono',monospace;
        color:{pri};
        background:{bg};
        min-height:100vh;
        ">

      <!-- MENUBAR -->
      <div style="
          display:flex;justify-content:space-between;align-items:stretch;
          height:30px;border-bottom:1px solid {border};background:{bg2};
          font-size:0.7rem;letter-spacing:1px;position:relative;z-index:10;">

        <div style="display:flex;align-items:stretch;">
          <div style="display:flex;align-items:center;padding:0 10px;color:{pri};
                      border-right:1px solid {border};background:{bg};
                      border-top:1px solid {dim};border-bottom:1px solid {dim};">
            <span style="color:{dim};margin-right:3px;">^1</span>LOGIN
          </div>
          <div style="display:flex;align-items:center;padding:0 10px;color:{dim};border-right:1px solid {border};">
            <span style="color:{border};margin-right:3px;">^2</span>STATUS
          </div>
          <div style="display:flex;align-items:center;padding:0 10px;color:{dim};border-right:1px solid {border};">
            <span style="color:{border};margin-right:3px;">^3</span>INFO
          </div>
        </div>

        <div style="display:flex;align-items:stretch;border-left:1px solid {border};">
          <div id="theme-trigger" onclick="toggleAppear()"
               style="display:flex;align-items:center;padding:0 10px;cursor:pointer;
                      border-left:1px solid {border};background:{bg2};color:{pri};">
            <span style="color:{dim};margin-right:3px;">^T</span>
            <span id="theme-label">{label}</span>
          </div>
          <div style="display:flex;align-items:center;padding:0 12px;
                      border-left:1px solid {border};background:{bg};color:{pri};">
            RSU TERMINAL
          </div>
        </div>
      </div>

      <!-- CONTENT -->
      <div style="padding:20px 0 0 28px;">
        <div style="font-size:0.78rem;color:{pri};letter-spacing:1px;margin-bottom:2px;">RSU TERMINAL</div>
        <div style="font-size:0.72rem;color:{dim};margin-bottom:18px;">Redistribution Strategy Unit.</div>

        <div style="display:flex;">

          <!-- LOGIN BOX -->
          <div style="border:1px solid {mid};width:460px;position:relative;">
            <div style="display:flex;align-items:center;justify-content:center;
                        height:28px;font-size:0.7rem;letter-spacing:3px;
                        border-bottom:1px solid {border};background:{bg2};position:relative;">
              <span style="position:absolute;left:12px;color:{border};">── </span>
              LOGIN
              <span style="position:absolute;right:12px;color:{border};"> ──</span>
            </div>

            <div style="padding:18px 18px 0;">
              {logo_html}
              <div style="font-family:'VT323',monospace;font-size:2.1rem;letter-spacing:6px;
                          text-align:center;color:{pri};text-shadow:0 0 12px rgba(255,179,0,0.4);
                          margin-bottom:2px;text-transform:uppercase;">
                RSU TERMINAL
              </div>
              <div style="font-size:0.58rem;letter-spacing:3px;text-align:center;
                          color:{dim};text-transform:uppercase;margin-bottom:14px;">
                Redistribution Strategy Unit
              </div>

              <!-- PASSWORD LABEL -->
              <div style="font-size:0.7rem;color:{pri};letter-spacing:2px;
                          text-transform:uppercase;padding:4px 6px 2px;background:{bg2};
                          border-top:1px solid {border};border-left:1px solid {border};
                          border-right:1px solid {border};">
                PASSWORD
              </div>
            </div>
    """, unsafe_allow_html=True)

    # Native Streamlit password input
    password = st.text_input(
        "pwd",
        type="password",
        placeholder="Enter your password",
        label_visibility="collapsed",
        key="login_password"
    )

    st.markdown(f"""
            <div style="height:2px;"></div>
          </div>
    """, unsafe_allow_html=True)

    # Native Streamlit button
    button_clicked = st.button("SIGN IN", key="btn_login", use_container_width=True)

    st.markdown(f"""
          <div style="font-size:0.58rem;color:{border};text-align:center;
                      letter-spacing:2px;text-transform:uppercase;padding:8px 0 4px;">
            <span style="display:inline-block;width:5px;height:5px;background:{pri};
                         border-radius:50%;vertical-align:middle;margin-right:4px;
                         animation:blink 1.1s step-end infinite;"></span>
            SECURE CONNECTION · AES-256 · TLS 1.3
          </div>
          <div style="font-size:0.56rem;color:{border};text-align:center;letter-spacing:2px;
                      padding:6px 18px;border-top:1px solid {border};text-transform:uppercase;">
            🔒 SSL ENCRYPTED · © 2026 RSU TERMINAL v2.0 // STATUS: ACTIVE
          </div>

          <!-- APPEARANCE PANEL (positioned relative to loginbox) -->
          <div id="appear-panel" style="
              display:none;
              position:absolute;top:0;right:-212px;
              width:202px;
              border:1px solid {dim};
              background:{bg2};
              z-index:200;
              font-family:'Share Tech Mono',monospace;
              ">
            <div style="font-size:0.62rem;letter-spacing:3px;color:{dim};text-align:center;
                        padding:7px 0 6px;border-bottom:1px solid {border};text-transform:uppercase;">
              <span style="color:{border};">── </span>APPEARANCE<span style="color:{border};"> ──</span>
            </div>

            <!-- THEME -->
            <div style="padding:8px 10px 4px;">
              <div style="font-size:0.58rem;color:{dim};letter-spacing:2px;margin-bottom:4px;text-transform:uppercase;">THEME</div>
              <div style="background:{bg};border:1px solid {border};padding:2px 0;">
                <div class="ap-opt" onclick="setTheme('VT220')" style="display:flex;align-items:center;padding:4px 8px;font-size:0.75rem;cursor:pointer;gap:8px;color:{pri};">
                  <span id="d-vt220" style="font-size:0.62rem;width:10px;color:{dot_cls('VT220')};">{dot('VT220')}</span>VT220{arrow('VT220')}
                </div>
                <div class="ap-opt" onclick="setTheme('GREEN')" style="display:flex;align-items:center;padding:4px 8px;font-size:0.75rem;cursor:pointer;gap:8px;color:{pri};">
                  <span id="d-green" style="font-size:0.62rem;width:10px;color:{dot_cls('GREEN')};">{dot('GREEN')}</span>Green Phosphor{arrow('GREEN')}
                </div>
                <div class="ap-opt" onclick="setTheme('CYAN')" style="display:flex;align-items:center;padding:4px 8px;font-size:0.75rem;cursor:pointer;gap:8px;color:{pri};">
                  <span id="d-cyan" style="font-size:0.62rem;width:10px;color:{dot_cls('CYAN')};">{dot('CYAN')}</span>Cyan VDT{arrow('CYAN')}
                </div>
              </div>
            </div>

            <div style="font-size:0.58rem;color:{border};text-align:center;padding:6px 0;
                        border-top:1px solid {border};letter-spacing:1px;">
              ↑↓ NAV · ↵ SEL · ESC
            </div>
          </div>
        </div><!-- /loginbox -->
      </div><!-- /content-row -->
    </div><!-- /content -->
    </div><!-- /vt-root -->

    <style>
    @keyframes blink {{0%,100%{{opacity:1;}}50%{{opacity:0;}}}}
    .ap-opt:hover {{ background: rgba(255,179,0,0.07) !important; }}
    </style>

    <script>
    var THEMES = {themes_js};
    var panelOpen = false;

    function toggleAppear() {{
        panelOpen = !panelOpen;
        document.getElementById('appear-panel').style.display = panelOpen ? 'block' : 'none';
    }}

    function applyTheme(k) {{
        var t = THEMES[k];
        var r = document.documentElement.style;
        r.setProperty('--vt-pri', t.pri);
        // recolor all inline elements via a class swap would need full DOM walk
        // instead reload with Streamlit session_state
    }}

    function setTheme(k) {{
        // Store in sessionStorage so Streamlit can pick it up via JS
        window.sessionStorage.setItem('vt_pending_theme', k);
        // Trigger Streamlit rerun by clicking the hidden theme button
        var btn = document.querySelector('[data-testid="stButton"][key="btn_set_theme"] button, button[kind="secondary"]');
        // fallback: find any button whose text is the theme key
        var btns = document.querySelectorAll('button');
        for(var i=0;i<btns.length;i++){{
            if(btns[i].innerText.trim() === '__THEME_' + k + '__') {{
                btns[i].click(); return;
            }}
        }}
    }}

    document.addEventListener('keydown', function(e) {{
        if (e.key === 'Escape') {{
            panelOpen = false;
            var p = document.getElementById('appear-panel');
            if(p) p.style.display = 'none';
        }}
        if (e.key === 'Enter') {{
            var inp = document.querySelector('input[type="password"]');
            if (inp && document.activeElement === inp) {{
                var btns = document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){{
                    if(btns[i].innerText.trim()==='SIGN IN'){{btns[i].click();return;}}
                }}
            }}
        }}
        if (e.key === 't' && (e.ctrlKey || e.metaKey)) {{
            e.preventDefault(); toggleAppear();
        }}
    }});

    // Auto-focus password field
    setTimeout(function(){{
        var inp = document.querySelector('input[type="password"]');
        if(inp) inp.focus();
    }}, 500);
    </script>
    """, unsafe_allow_html=True)

    # Hidden theme-change buttons (one per theme)
    for tkey in THEMES:
        if st.button(f"__THEME_{tkey}__", key=f"btn_theme_{tkey}"):
            st.session_state["vt_theme"] = tkey
            st.rerun()

    # Hidden theme toggle button for menubar click
    if st.button("__TOGGLE_MENU__", key="btn_menu_toggle"):
        st.session_state["vt_menu_open"] = not st.session_state["vt_menu_open"]
        st.rerun()

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

    return False


def logout():
    st.session_state["auth"] = False
    st.session_state["last_activity"] = None
    st.rerun()


def require_auth():
    if "auth" not in st.session_state or not st.session_state["auth"]:
        st.error("🔒 ACCESO DENEGADO")
        login()
        st.stop()
    st.session_state["last_activity"] = datetime.now()
