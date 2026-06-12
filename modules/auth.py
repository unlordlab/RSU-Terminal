# modules/auth.py
import os
import hashlib
import logging
import base64
from datetime import datetime, timedelta

import streamlit as st
import streamlit.components.v1 as components

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FADE_GIF_B64 = "R0lGODlhCAAIAPcAAAAAAAAAMwAAZgAAmQAAzAAA/wAzAAAzMwAzZgAzmQAzzAAz/wBmAABmMwBmZgBmmQBmzABm/wCZAACZMwCZZgCZmQCZzACZ/wDMAADMMwDMZgDMmQDMzADM/wD/AAD/MwD/ZgD/mQD/zAD//zMAADMAMzMAZjMAmTMAzDMA/zMzADMzMzMzZjMzmTMzzDMz/zNmADNmMzNmZjNmmTNmzDNm/zOZADOZMzOZZjOZmTOZzDOZ/zPMADPMMzPMZjPMmTPMzDPM/zP/ADP/MzP/ZjP/mTP/zDP//2YAAGYAM2YAZmYAmWYAzGYA/2YzAGYzM2YzZmYzmWYzzGYz/2ZmAGZmM2ZmZmZmmWZmzGZm/2aZAGaZM2aZZmaZmWaZzGaZ/2bMAGbMM2bMZmbMmWbMzGbM/2b/AGb/M2b/Zmb/mWb/zGb//5kAAJkAM5kAZpkAmZkAzJkA/5kzAJkzM5kzZpkzmZkzzJkz/5lmAJlmM5lmZplmmZlmzJlm/5mZAJmZM5mZZpmZmZmZzJmZ/5nMAJnMM5nMZpnMmZnMzJnM/5n/AJn/M5n/Zpn/mZn/zJn//8wAAMwAM8wAZswAmcwAzMwA/8wzAMwzM8wzZswzmcwzzMwz/8xmAMxmM8xmZsxmmcxmzMxm/8yZAMyZM8yZZsyZmcyZzMyZ/8zMAMzMM8zMZszMmczMzMzM/8z/AMz/M8z/Zsz/mcz/zMz///8AAP8AM/8AZv8Amf8AzP8A//8zAP8zM/8zZv8zmf8zzP8z//9mAP9mM/9mZv9mmf9mzP9m//+ZAP+ZM/+ZZv+Zmf+ZzP+Z///MAP/MM//MZv/Mmf/MzP/M////AP//M///Zv//mf//zP///yEOCQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAANgALAAAAAAIAAgAAAgZAK9hE0gQ28CDBAsWRIhQ4UGGCSEadHgtIAA7"


def get_logo_base64():
    try:
        if os.path.exists("assets/logo.png"):
            with open("assets/logo.png", "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return None


def login() -> bool:
    # ── INIT ──────────────────────────────────────────────────────────────────
    defaults = {
        "auth": False,
        "login_attempts": 0,
        "lockout_time": None,
        "last_activity": None,
        "vt_theme": "VT220",
        "vt_error": "",
    }
    for k, v in defaults.items():
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
            remaining = int(
                (st.session_state["lockout_time"] - datetime.now()).total_seconds() / 60
            )
            st.session_state["vt_error"] = f"⛔ BLOQUEADO — {remaining} MIN"
        else:
            st.session_state["lockout_time"] = None
            st.session_state["login_attempts"] = 0
            st.session_state["vt_error"] = ""

    # ── THEME HANDLING ────────────────────────────────────────────────────────
    qp = st.query_params
    if "_vt_theme" in qp:
        tv = qp["_vt_theme"]
        if tv in ("VT220", "GREEN", "CYAN"):
            st.session_state["vt_theme"] = tv
        st.query_params.clear()
        st.rerun()

    theme = st.session_state.get("vt_theme", "VT220")
    THEMES = {
        "VT220": dict(pri="#ffb300", bg="#0a0800", bg2="#130f00", bg3="#1a1200",
                      border="#3d2900", mid="#5a3e00", dim="#7a5500", dark="#1e1400",
                      crt="#0d0500", tint="rgba(180,60,0,0.12)"),
        "GREEN": dict(pri="#00ffad", bg="#000d04", bg2="#001508", bg3="#001e0a",
                      border="#003820", mid="#006640", dim="#008855", dark="#001810",
                      crt="#000d04", tint="rgba(0,180,80,0.10)"),
        "CYAN":  dict(pri="#00d9ff", bg="#00080d", bg2="#001018", bg3="#001520",
                      border="#002c38", mid="#005566", dim="#006680", dark="#000c14",
                      crt="#00080d", tint="rgba(0,130,180,0.10)"),
    }
    t = THEMES[theme]

    logo_b64  = get_logo_base64() or ""
    error_msg = st.session_state.get("vt_error", "")
    attempts_l = 5 - st.session_state.get("login_attempts", 0)
    fade_b64  = FADE_GIF_B64

    pri    = t["pri"]
    bg     = t["bg"]
    bg2    = t["bg2"]
    bg3    = t["bg3"]
    border = t["border"]
    mid    = t["mid"]
    dim    = t["dim"]
    dark   = t["dark"]
    crt    = t["crt"]
    tint   = t["tint"]
    label  = {"VT220": "VT220", "GREEN": "P3 GREEN", "CYAN": "CYAN VDT"}[theme]

    logo_img = ""
    if logo_b64:
        logo_img = f'<img src="data:image/png;base64,{logo_b64}" style="display:block;width:92px;height:92px;border-radius:10px;margin:0 auto 16px;filter:drop-shadow(0 0 14px rgba(255,140,0,0.55));">'

    # ── THEME SELECTOR (visual only iframe, no auth logic) ────────────────────
    cur = theme
    def dot(k): return "▶" if k == cur else "○"
    def arr(k): return f'<span style="margin-left:auto;font-size:.6rem;color:{dim};">←</span>' if k == cur else ""
    def dc(k):  return dim if k == cur else border

    theme_html = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:'Share Tech Mono',monospace;}}
.wrap{{
  display:flex;justify-content:flex-end;
  background:{bg2};border-bottom:1px solid {border};
  height:30px;
}}
.chip{{display:flex;align-items:center;padding:0 10px;border-left:1px solid {border};
       background:{bg2};color:{pri};cursor:pointer;font-size:0.7rem;letter-spacing:1px;}}
.chip .key{{color:{dim};margin-right:3px;}}
.chip:hover{{background:{dark};}}
.chip.site{{background:{bg};cursor:default;}}
.chip.site:hover{{background:{bg};}}
.tab{{display:flex;align-items:center;padding:0 10px;color:{dim};
      border-right:1px solid {border};font-size:0.7rem;letter-spacing:1px;}}
.tab .key{{color:{border};margin-right:3px;}}
.tab.active{{color:{pri};background:{bg};border-top:1px solid {mid};border-bottom:1px solid {mid};}}
.tab.active .key{{color:{dim};}}
.tabs{{display:flex;align-items:stretch;}}
.bar{{display:flex;justify-content:space-between;align-items:stretch;
      height:30px;width:100%;border-bottom:1px solid {border};background:{bg2};}}
.right{{display:flex;align-items:stretch;}}

.panel{{display:none;position:absolute;top:30px;right:0;z-index:999;
        width:230px;background:{bg2};
        border:1px solid {mid};border-top:none;
        border-left:4px solid transparent;
        border-image:url("data:image/gif;base64,{fade_b64}") 8 repeat;
        font-family:'Share Tech Mono',monospace;}}
.panel.open{{display:block;}}
.ap-head{{font-size:.62rem;letter-spacing:3px;color:{dim};text-align:center;
          padding:8px 0 7px;text-transform:uppercase;
          border-bottom:3px solid transparent;
          border-image:url("data:image/gif;base64,{fade_b64}") 8 repeat;}}
.ap-sec{{padding:8px 12px 4px;}}
.ap-lbl{{font-size:.58rem;color:{dim};letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;}}
.ap-grp{{background:{bg};padding:2px 0;margin-bottom:6px;
         border:2px solid transparent;
         border-image:url("data:image/gif;base64,{fade_b64}") 8 repeat;}}
.ap-opt{{display:flex;align-items:center;padding:6px 10px;font-size:.78rem;
         cursor:pointer;gap:8px;color:{pri};letter-spacing:.5px;}}
.ap-opt:hover{{background:rgba(255,255,255,.05);}}
.ap-dot{{font-size:.65rem;width:12px;}}
.ap-foot{{font-size:.6rem;color:{border};text-align:center;padding:7px 0;letter-spacing:1px;
          border-top:3px solid transparent;
          border-image:url("data:image/gif;base64,{fade_b64}") 8 repeat;}}
</style></head>
<body style="background:{bg};">
<div class="bar">
  <div class="tabs">
    <div class="tab active"><span class="key">^1</span>LOGIN</div>
    <div class="tab"><span class="key">^2</span>STATUS</div>
    <div class="tab"><span class="key">^3</span>INFO</div>
  </div>
  <div class="right">
    <div class="chip" onclick="toggle()"><span class="key">^T</span><span id="lbl">{label}</span></div>
    <div class="chip site">RSU TERMINAL</div>
  </div>
</div>
<div class="panel" id="panel">
  <div class="ap-head">── APPEARANCE ──</div>
  <div class="ap-sec">
    <div class="ap-lbl">THEME</div>
    <div class="ap-grp">
      <div class="ap-opt" onclick="pick('VT220')"><span class="ap-dot" style="color:{dc('VT220')};">{dot('VT220')}</span>VT220{arr('VT220')}</div>
      <div class="ap-opt" onclick="pick('GREEN')"><span class="ap-dot" style="color:{dc('GREEN')};">{dot('GREEN')}</span>Green Phosphor{arr('GREEN')}</div>
      <div class="ap-opt" onclick="pick('CYAN')"><span class="ap-dot" style="color:{dc('CYAN')};">{dot('CYAN')}</span>Cyan VDT{arr('CYAN')}</div>
    </div>
  </div>
  <div class="ap-foot">↑↓ NAV · ↵ SEL · ESC</div>
</div>
<script>
var open=false;
function toggle(){{open=!open;document.getElementById('panel').className='panel'+(open?' open':'');}}
function pick(k){{
  var url=new URL(window.parent.location.href);
  url.searchParams.set('_vt_theme',k);
  window.parent.location.href=url.toString();
}}
document.addEventListener('keydown',function(e){{
  if(e.key==='Escape'){{open=false;document.getElementById('panel').className='panel';}}
}});
</script>
</body></html>"""

    # ── FULL PAGE CSS ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

    #MainMenu, footer, header {{ visibility: hidden !important; }}

    html, body, .stApp {{
        background: {bg} !important;
    }}

    /* CRT scanlines on full page */
    .stApp::before {{
        content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 9998;
        background: repeating-linear-gradient(to bottom, transparent 0, transparent 3px, rgba(0,0,0,0.20) 3px, rgba(0,0,0,0.20) 4px);
    }}
    /* Phosphor vignette */
    .stApp::after {{
        content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 9997;
        background: radial-gradient(ellipse 95% 95% at 50% 50%, transparent 50%, rgba(0,0,0,0.65) 100%);
    }}

    /* Strip all Streamlit padding/chrome */
    .main .block-container {{
        padding: 0 !important; max-width: 100% !important; margin: 0 !important;
    }}
    section[data-testid="stMain"] > div {{ padding: 0 !important; }}
    div[data-testid="stVerticalBlock"] {{
        background: transparent !important; border: none !important;
        box-shadow: none !important; padding: 0 !important; gap: 0 !important;
    }}
    div[data-testid="stHorizontalBlock"], div[data-testid="column"] {{
        background: transparent !important; border: none !important;
        box-shadow: none !important; padding: 0 !important;
        gap: 0 !important; min-height: 0 !important;
    }}
    iframe {{ border: none !important; display: block !important; }}

    /* ── CENTER THE LOGIN BOX ─────────────────────────────── */
    .vt-page {{
        display: flex;
        justify-content: center;
        align-items: flex-start;
        padding: 28px 20px 40px;
        position: relative;
        z-index: 1;
    }}

    /* ── LOGIN BOX ───────────────────────────────────────── */
    .vt-box {{
        width: min(700px, 96vw);
        border: 1px solid {mid};
        background: {bg};
        position: relative;
    }}

    /* Header */
    .vt-box-head {{
        display: flex; align-items: center; justify-content: center;
        height: 28px; font-family: 'Share Tech Mono', monospace;
        font-size: 0.7rem; letter-spacing: 3px;
        border-bottom: 1px solid {border}; background: {bg2};
        position: relative; color: {pri};
    }}
    .vt-box-head::before {{ content: '── '; color: {border}; position: absolute; left: 12px; }}
    .vt-box-head::after  {{ content: ' ──'; color: {border}; position: absolute; right: 12px; }}

    /* ── CRT SCREEN AREA ─────────────────────────────────── */
    .vt-crt {{
        position: relative;
        background: {crt};
        padding: 32px 48px 32px;
        overflow: hidden;
    }}
    /* noise grain */
    .vt-crt::before {{
        content: ''; position: absolute; inset: 0; pointer-events: none; z-index: 2;
        mix-blend-mode: overlay;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E");
        background-size: 200px 200px;
    }}
    /* scanlines inside CRT */
    .vt-crt::after {{
        content: ''; position: absolute; inset: 0; pointer-events: none; z-index: 3;
        background: repeating-linear-gradient(to bottom, transparent 0, transparent 2px, rgba(0,0,0,0.28) 2px, rgba(0,0,0,0.28) 4px);
    }}
    .vt-crt-tint {{
        position: absolute; inset: 0; pointer-events: none; z-index: 4;
        background: radial-gradient(ellipse 80% 70% at 50% 40%, {tint} 0%, transparent 70%);
    }}
    @keyframes vt-flicker {{
        0%,100%{{opacity:1}} 92%{{opacity:1}} 93%{{opacity:.94}} 94%{{opacity:1}} 96%{{opacity:.97}} 97%{{opacity:1}}
    }}
    .vt-crt {{ animation: vt-flicker 8s infinite; }}
    .vt-crt-inner {{ position: relative; z-index: 10; }}

    /* Title */
    .vt-title {{
        font-family: 'VT323', monospace !important;
        font-size: 3.4rem !important;
        letter-spacing: 10px !important;
        text-align: center !important;
        color: {pri} !important;
        text-transform: uppercase;
        text-shadow: 0 0 18px rgba(255,140,0,0.6), 0 0 4px rgba(255,200,0,0.4);
        line-height: 1; margin-bottom: 4px;
    }}
    .vt-sub {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.65rem; letter-spacing: 5px; text-align: center;
        color: {dim}; text-transform: uppercase; margin-bottom: 28px;
    }}

    /* ── PASSWORD FIELD — full rectangular block ─────────── */
    .vt-field {{
        border: 1px solid {mid};
        margin-bottom: 16px;
    }}
    .vt-field-label {{
        display: block;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 0.75rem !important;
        color: {pri} !important;
        letter-spacing: 3px;
        text-transform: uppercase;
        padding: 7px 12px 6px;
        background: rgba(20,12,0,0.9);
        border-bottom: 1px solid {border};
    }}
    /* Native Streamlit input override */
    .stTextInput > label {{ display: none !important; }}
    .stTextInput > div {{ border: none !important; box-shadow: none !important; background: transparent !important; padding: 0 !important; }}
    .stTextInput > div > div {{ border: none !important; box-shadow: none !important; background: transparent !important; }}
    .stTextInput > div > div > input {{
        background: rgba(8,5,0,0.95) !important;
        border: none !important;
        border-radius: 0 !important;
        color: {pri} !important;
        height: 44px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 1rem !important;
        letter-spacing: 3px !important;
        padding: 0 12px !important;
        caret-color: {pri} !important;
        box-shadow: none !important;
        width: 100% !important;
        margin: 0 !important;
    }}
    .stTextInput > div > div > input::placeholder {{
        color: {dim} !important; font-style: italic; letter-spacing: 2px; font-size: 0.9rem !important;
    }}
    .stTextInput > div > div > input:focus {{
        box-shadow: none !important; outline: none !important;
    }}
    .stTextInput [data-testid="stIcon"] {{ display: none !important; }}
    /* Highlight border on focus */
    .vt-field:focus-within {{ border-color: {pri} !important; }}

    /* ── SIGN IN BUTTON ──────────────────────────────────── */
    div[data-testid="stButton"] > button {{
        font-family: 'Share Tech Mono', monospace !important;
        background: {pri} !important;
        color: {bg} !important;
        border: none !important;
        border-radius: 0 !important;
        font-size: 0.95rem !important;
        letter-spacing: 6px !important;
        width: 100% !important;
        height: 50px !important;
        padding: 0 !important;
        text-transform: uppercase !important;
        margin: 0 !important;
        box-shadow: none !important;
        background-image: repeating-linear-gradient(to bottom, transparent 0, transparent 2px, rgba(0,0,0,0.08) 2px, rgba(0,0,0,0.08) 4px) !important;
        transition: opacity 0.15s !important;
    }}
    div[data-testid="stButton"] > button:hover {{ opacity: 0.88 !important; }}

    /* ── STATUS / FOOTER ─────────────────────────────────── */
    .vt-status {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.58rem; color: {border}; text-align: center;
        letter-spacing: 2px; text-transform: uppercase; padding: 10px 0 6px;
    }}
    .vt-footer {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.55rem; color: {border}; text-align: center;
        letter-spacing: 1px; padding: 6px 18px 10px;
        border-top: 1px solid {border}; text-transform: uppercase;
    }}
    @keyframes vt-blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0}} }}
    .vt-dot {{
        display: inline-block; width: 5px; height: 5px; border-radius: 50%;
        background: {pri}; vertical-align: middle; margin-right: 5px;
        animation: vt-blink 1.1s step-end infinite;
    }}

    /* Alerts */
    .stAlert {{
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 0.75rem !important; border-radius: 0 !important;
        margin: 0 0 12px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── MENUBAR (iframe, purely visual + theme switcher) ──────────────────────
    components.html(theme_html, height=31, scrolling=False)

    # ── LOGIN BOX ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="vt-page">
      <div class="vt-box">
        <div class="vt-box-head">LOGIN</div>
        <div class="vt-crt">
          <div class="vt-crt-tint"></div>
          <div class="vt-crt-inner">
            {logo_img}
            <div class="vt-title">RSU TERMINAL</div>
            <div class="vt-sub">Redistribution Strategy Unit</div>
            <div class="vt-field">
              <span class="vt-field-label">PASSWORD</span>
    """, unsafe_allow_html=True)

    # ── NATIVE STREAMLIT INPUT — this is what actually reads the password ──────
    password = st.text_input(
        "pwd", type="password",
        placeholder="Enter your password",
        label_visibility="collapsed",
        key="vt_password_input",
    )

    st.markdown("</div>", unsafe_allow_html=True)  # close vt-field

    # Show errors if any
    if error_msg:
        st.error(error_msg)
    elif 0 < attempts_l <= 2:
        st.warning(f"⚠ {attempts_l} INTENTOS RESTANTES")

    # ── NATIVE STREAMLIT BUTTON — this is what actually triggers login ─────────
    sign_in = st.button("SIGN IN", key="vt_signin_btn", use_container_width=True)

    # Close box
    st.markdown(f"""
          </div>
        </div>
        <div class="vt-status"><span class="vt-dot"></span>SECURE CONNECTION · AES-256 · TLS 1.3</div>
        <div class="vt-footer">🔒 SSL ENCRYPTED · © 2026 RSU TERMINAL v2.0 // STATUS: ACTIVE</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── AUTH LOGIC ─────────────────────────────────────────────────────────────
    if sign_in:
        if not password:
            st.session_state["vt_error"] = "⚠ INGRESE CONTRASEÑA"
            st.rerun()
        elif not st.session_state["lockout_time"]:
            pwd_hash  = hashlib.sha256(password.encode()).hexdigest()
            real_pwd  = st.secrets.get("APP_PASSWORD", "")
            real_hash = hashlib.sha256(real_pwd.encode()).hexdigest()

            if pwd_hash == real_hash:
                st.session_state["auth"] = True
                st.session_state["login_attempts"] = 0
                st.session_state["last_activity"] = datetime.now()
                st.session_state["vt_error"] = ""
                st.rerun()
            else:
                st.session_state["login_attempts"] += 1
                remaining = 5 - st.session_state["login_attempts"]
                if st.session_state["login_attempts"] >= 5:
                    st.session_state["lockout_time"] = datetime.now() + timedelta(minutes=15)
                    st.session_state["vt_error"] = "⛔ ACCESO BLOQUEADO — 15 MIN"
                else:
                    st.session_state["vt_error"] = f"⚠ CONTRASEÑA INCORRECTA — {remaining} INTENTOS"
                st.rerun()

    # Enter key via JS
    st.markdown("""
    <script>
    setTimeout(function() {
        var inp = document.querySelector('input[type="password"]');
        if (!inp) return;
        inp.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                var btns = document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].innerText.trim() === 'SIGN IN') { btns[i].click(); return; }
                }
            }
        });
    }, 400);
    </script>
    """, unsafe_allow_html=True)

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
