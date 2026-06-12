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
        ("vt_theme", "VT220"),
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

    t   = THEMES[st.session_state["vt_theme"]]
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

    # Build JS themes object
    themes_js_parts = []
    for k, v in THEMES.items():
        themes_js_parts.append(
            f'"{k}":{{"pri":"{v["pri"]}","bg":"{v["bg"]}","bg2":"{v["bg2"]}","bg3":"{v["bg3"]}",'
            f'"border":"{v["border"]}","mid":"{v["mid"]}","dim":"{v["dim"]}","label":"{v["label"]}"}}'
        )
    themes_js = "{" + ",".join(themes_js_parts) + "}"

    cur = st.session_state["vt_theme"]

    # ── ALL CSS + ALL HTML in a single st.markdown() call ─────────────────────
    logo_img = ""
    if logo_b64:
        logo_img = (
            f'<img src="data:image/png;base64,{logo_b64}" '
            f'style="display:block;width:56px;height:56px;border-radius:6px;'
            f'margin:0 auto 10px;opacity:0.9;">'
        )

    def mk_dot(k):
        return ("▶", dim) if k == cur else ("○", border)
    def mk_arrow(k):
        return f'<span style="margin-left:auto;color:{dim};font-size:0.6rem;">←</span>' if k == cur else ""

    vt_d, vt_c   = mk_dot("VT220")
    gr_d, gr_c   = mk_dot("GREEN")
    cy_d, cy_c   = mk_dot("CYAN")

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

/* ── GLOBAL ─────────────────────────── */
#MainMenu, footer, header {{ visibility: hidden !important; }}
html, body, .stApp {{ background: {bg} !important; }}

.stApp::before {{
    content:''; position:fixed; inset:0; z-index:9998; pointer-events:none;
    background: repeating-linear-gradient(
        to bottom, transparent 0, transparent 3px,
        rgba(0,0,0,0.25) 3px, rgba(0,0,0,0.25) 4px);
}}
.stApp::after {{
    content:''; position:fixed; inset:0; z-index:9997; pointer-events:none;
    background: radial-gradient(ellipse 90% 90% at 50% 50%, transparent 50%, rgba(0,0,0,0.7) 100%);
}}

/* ── STRIP STREAMLIT CHROME ─────────── */
.main .block-container {{
    max-width:100% !important; padding:0 !important; margin:0 !important;
}}
section[data-testid="stMain"] > div {{ padding:0 !important; }}
div[data-testid="stVerticalBlock"] {{
    background:transparent !important; border:none !important;
    box-shadow:none !important; padding:0 !important; gap:0 !important;
}}
div[data-testid="stHorizontalBlock"],
div[data-testid="column"] {{
    background:transparent !important; border:none !important;
    box-shadow:none !important; padding:0 !important;
    gap:0 !important; min-height:0 !important;
}}

/* ── HIDE THEME BUTTONS ─────────────── */
[data-testid="stButton"].vt-hidden-btn,
.vt-hidden-btn {{ display:none !important; }}

/* ── INPUT ───────────────────────────── */
.stTextInput > label {{ display:none !important; }}
.stTextInput > div {{
    border:none !important; box-shadow:none !important;
    background:transparent !important; padding:0 !important;
}}
.stTextInput > div > div {{
    border:none !important; box-shadow:none !important;
    background:transparent !important;
}}
.stTextInput > div > div > input {{
    background: {bg3} !important;
    border: none !important;
    border-bottom: 1px solid {border} !important;
    border-radius: 0 !important;
    color: {pri} !important;
    height: 32px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
    letter-spacing: 1px !important;
    padding: 0 8px !important;
    caret-color: {pri};
    box-shadow: none !important;
    width: 100% !important;
    margin: 0 !important;
}}
.stTextInput > div > div > input:focus {{
    border-bottom-color: {dim} !important;
    box-shadow: none !important;
    outline: none !important;
}}
.stTextInput > div > div > input::placeholder {{
    color: {border} !important; font-style:italic;
}}
.stTextInput [data-testid="stIcon"] {{ display:none !important; }}

/* ── MAIN SIGN IN BUTTON ─────────────── */
.vt-signin-btn > div[data-testid="stButton"] > button {{
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
    box-shadow: none !important;
    transition: opacity 0.1s !important;
    display: block !important;
}}
.vt-signin-btn > div[data-testid="stButton"] > button:hover {{ opacity:0.85 !important; }}

/* ── ALERTS ──────────────────────────── */
.stAlert {{
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important;
    border-radius: 0 !important;
    border-left: 2px solid {pri} !important;
    background: {bg2} !important;
    margin: 4px 0 0 !important;
}}

/* ── BLINK ───────────────────────────── */
@keyframes vt-blink {{ 0%,100%{{opacity:1;}} 50%{{opacity:0;}} }}
.vt-dot {{
    display:inline-block; width:5px; height:5px; border-radius:50%;
    background:{pri}; vertical-align:middle; margin-right:5px;
    animation: vt-blink 1.1s step-end infinite;
}}

/* ── APPEARANCE PANEL ────────────────── */
.vt-appear {{
    display:none; position:fixed; z-index:9999;
    top:31px; right:0;
    width:206px;
    border:1px solid {dim};
    background:{bg2};
    font-family:'Share Tech Mono',monospace;
    border-top:none;
}}
.vt-appear.open {{ display:block; }}
.vt-ap-head {{
    font-size:0.62rem; letter-spacing:3px; color:{dim};
    text-align:center; padding:7px 0 6px;
    border-bottom:1px solid {border}; text-transform:uppercase;
}}
.vt-ap-sec {{ padding:8px 10px 4px; }}
.vt-ap-lbl {{
    font-size:0.58rem; color:{dim}; letter-spacing:2px;
    text-transform:uppercase; margin-bottom:4px;
}}
.vt-ap-grp {{
    background:{bg}; border:1px solid {border}; padding:2px 0; margin-bottom:6px;
}}
.vt-ap-opt {{
    display:flex; align-items:center;
    padding:5px 8px; font-size:0.75rem; cursor:pointer;
    gap:8px; color:{pri}; letter-spacing:0.5px;
}}
.vt-ap-opt:hover {{ background:rgba(255,255,255,0.04); }}
.vt-ap-foot {{
    font-size:0.58rem; color:{border}; text-align:center;
    padding:6px 0; border-top:1px solid {border}; letter-spacing:1px;
}}
</style>

<!-- ═══════════════════════════════════════ TOP MENUBAR -->
<div id="vt-menubar" style="
    display:flex; justify-content:space-between; align-items:stretch;
    height:30px; border-bottom:1px solid {border}; background:{bg2};
    font-family:'Share Tech Mono',monospace; font-size:0.7rem;
    letter-spacing:1px; position:relative; z-index:100;">
  <div style="display:flex;align-items:stretch;">
    <div style="display:flex;align-items:center;padding:0 10px;color:{pri};
                border-right:1px solid {border};background:{bg};
                border-top:1px solid {mid};border-bottom:1px solid {mid};">
      <span style="color:{dim};margin-right:3px;">^1</span>LOGIN
    </div>
    <div style="display:flex;align-items:center;padding:0 10px;color:{dim};border-right:1px solid {border};">
      <span style="color:{border};margin-right:3px;">^2</span>STATUS
    </div>
    <div style="display:flex;align-items:center;padding:0 10px;color:{dim};border-right:1px solid {border};">
      <span style="color:{border};margin-right:3px;">^3</span>INFO
    </div>
  </div>
  <div style="display:flex;align-items:stretch;">
    <div id="vt-theme-btn" onclick="vtToggleAppear()" style="
        display:flex;align-items:center;padding:0 10px;cursor:pointer;
        border-left:1px solid {border};background:{bg2};color:{pri};">
      <span style="color:{dim};margin-right:3px;">^T</span>
      <span id="vt-theme-label">{label}</span>
    </div>
    <div style="display:flex;align-items:center;padding:0 12px;
                border-left:1px solid {border};background:{bg};color:{pri};">
      RSU TERMINAL
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════ APPEARANCE PANEL -->
<div class="vt-appear" id="vt-appear">
  <div class="vt-ap-head"><span style="color:{border};">── </span>APPEARANCE<span style="color:{border};"> ──</span></div>
  <div class="vt-ap-sec">
    <div class="vt-ap-lbl">THEME</div>
    <div class="vt-ap-grp">
      <div class="vt-ap-opt" onclick="vtSetTheme('VT220')">
        <span id="vt-d-VT220" style="width:10px;font-size:0.62rem;color:{vt_c};">{vt_d}</span>
        VT220
        <span id="vt-a-VT220" style="margin-left:auto;color:{dim};font-size:0.6rem;">{"←" if cur=="VT220" else ""}</span>
      </div>
      <div class="vt-ap-opt" onclick="vtSetTheme('GREEN')">
        <span id="vt-d-GREEN" style="width:10px;font-size:0.62rem;color:{gr_c};">{gr_d}</span>
        Green Phosphor
        <span id="vt-a-GREEN" style="margin-left:auto;color:{dim};font-size:0.6rem;">{"←" if cur=="GREEN" else ""}</span>
      </div>
      <div class="vt-ap-opt" onclick="vtSetTheme('CYAN')">
        <span id="vt-d-CYAN" style="width:10px;font-size:0.62rem;color:{cy_c};">{cy_d}</span>
        Cyan VDT
        <span id="vt-a-CYAN" style="margin-left:auto;color:{dim};font-size:0.6rem;">{"←" if cur=="CYAN" else ""}</span>
      </div>
    </div>
  </div>
  <div class="vt-ap-foot">↑↓ NAV · ↵ SEL · ESC</div>
</div>

<!-- ═══════════════════════════════════════ PAGE CONTENT -->
<div id="vt-page" style="
    padding:18px 0 0 28px;
    font-family:'Share Tech Mono',monospace;
    color:{pri};">
  <div style="font-size:0.78rem;letter-spacing:1px;margin-bottom:2px;">{logo_img}RSU TERMINAL</div>
  <div style="font-size:0.7rem;color:{dim};margin-bottom:18px;">Redistribution Strategy Unit.</div>

  <!-- LOGIN BOX WRAPPER: only top border + sides, no bottom yet -->
  <div style="width:460px;border:1px solid {mid};border-bottom:none;">
    <!-- Box title -->
    <div style="display:flex;align-items:center;justify-content:center;
                height:28px;font-size:0.7rem;letter-spacing:3px;
                border-bottom:1px solid {border};background:{bg2};position:relative;">
      <span style="position:absolute;left:12px;color:{border};">── </span>
      LOGIN
      <span style="position:absolute;right:12px;color:{border};"> ──</span>
    </div>
    <!-- Box body top -->
    <div style="padding:16px 18px 0 18px;background:{bg};">
      <div style="font-family:'VT323',monospace;font-size:2.1rem;letter-spacing:6px;
                  text-align:center;color:{pri};text-transform:uppercase;
                  text-shadow:0 0 12px rgba(255,179,0,0.35);line-height:1;margin-bottom:2px;">
        RSU TERMINAL
      </div>
      <div style="font-size:0.58rem;letter-spacing:3px;text-align:center;
                  color:{dim};text-transform:uppercase;margin-bottom:14px;">
        Redistribution Strategy Unit
      </div>
      <!-- PASSWORD label -->
      <div style="font-size:0.7rem;color:{pri};letter-spacing:2px;text-transform:uppercase;
                  padding:4px 6px 3px;background:{bg2};
                  border:1px solid {border};border-bottom:none;">
        PASSWORD
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── NATIVE: password input (sits flush inside the box via CSS) ────────────
    password = st.text_input(
        "pwd", type="password",
        placeholder="Enter your password",
        label_visibility="collapsed",
        key="login_password"
    )

    # ── SIGN IN BUTTON wrapper div ─────────────────────────────────────────────
    st.markdown(f"""
<div class="vt-signin-btn" style="width:460px;margin-left:28px;
     border-left:1px solid {mid};border-right:1px solid {mid};">
""", unsafe_allow_html=True)

    button_clicked = st.button("SIGN IN", key="btn_login", use_container_width=True)

    # ── CLOSE the box + footer ────────────────────────────────────────────────
    st.markdown(f"""
</div>
<div style="width:460px;margin-left:28px;border:1px solid {mid};border-top:none;background:{bg};">
  <div style="font-size:0.58rem;color:{border};text-align:center;letter-spacing:2px;
              text-transform:uppercase;padding:7px 0 5px;">
    <span class="vt-dot"></span>SECURE CONNECTION · AES-256 · TLS 1.3
  </div>
  <div style="font-size:0.55rem;color:{border};text-align:center;letter-spacing:1px;
              padding:5px 18px 10px;border-top:1px solid {border};text-transform:uppercase;">
    🔒 SSL ENCRYPTED · © 2026 RSU TERMINAL v2.0 // STATUS: ACTIVE
  </div>
</div>

<script>
var VT_THEMES = {themes_js};
var vtPanelOpen = false;
var vtCurrent = "{cur}";

function vtToggleAppear() {{
    vtPanelOpen = !vtPanelOpen;
    document.getElementById('vt-appear').className = 'vt-appear' + (vtPanelOpen ? ' open' : '');
}}

function vtSetTheme(k) {{
    // Click the hidden Streamlit button for that theme
    var btns = document.querySelectorAll('button');
    var target = '__VT_THEME_' + k + '__';
    for (var i = 0; i < btns.length; i++) {{
        if (btns[i].innerText.trim() === target) {{
            btns[i].click();
            vtPanelOpen = false;
            document.getElementById('vt-appear').className = 'vt-appear';
            return;
        }}
    }}
}}

document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{
        vtPanelOpen = false;
        var p = document.getElementById('vt-appear');
        if (p) p.className = 'vt-appear';
    }}
    if (e.key === 'Enter') {{
        var inp = document.querySelector('input[type="password"]');
        if (inp && document.activeElement === inp) {{
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {{
                if (btns[i].innerText.trim() === 'SIGN IN') {{ btns[i].click(); return; }}
            }}
        }}
    }}
}});

// Auto-focus
setTimeout(function() {{
    var inp = document.querySelector('input[type="password"]');
    if (inp) inp.focus();
}}, 500);
</script>
""", unsafe_allow_html=True)

    # ── HIDDEN THEME BUTTONS (invisible, triggered via JS) ────────────────────
    hide_css = """
    <style>
    .vt-theme-triggers { position:absolute; width:0; height:0; overflow:hidden; opacity:0; pointer-events:none; }
    .vt-theme-triggers button { position:absolute; width:1px; height:1px; }
    </style>
    <div class="vt-theme-triggers">
    """
    st.markdown(hide_css, unsafe_allow_html=True)

    for tkey in THEMES:
        if st.button(f"__VT_THEME_{tkey}__", key=f"vt_btn_theme_{tkey}"):
            st.session_state["vt_theme"] = tkey
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ── AUTH LOGIC ─────────────────────────────────────────────────────────────
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
