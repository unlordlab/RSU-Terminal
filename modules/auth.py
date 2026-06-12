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


def _build_html(logo_b64: str, theme: str, error_msg: str, attempts_left: int) -> str:

    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="logo-img" alt="RSU">'

    error_block = ""
    if error_msg:
        error_block = f'<div class="vt-error">{error_msg}</div>'

    attempts_block = ""
    if 0 < attempts_left <= 2:
        attempts_block = f'<div class="vt-warn">⚠ {attempts_left} INTENTOS RESTANTES</div>'

    fade_b64 = FADE_GIF_B64

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}

:root{{
  --bg:#0a0800;--bg2:#130f00;--bg3:#1a1200;
  --pri:#ffb300;--dim:#7a5500;--border:#3d2900;--mid:#5a3e00;--dark:#1e1400;
}}
.t-GREEN{{--bg:#000d04;--bg2:#001508;--bg3:#001e0a;--pri:#00ffad;--dim:#008855;--border:#003820;--mid:#006640;--dark:#001810;}}
.t-CYAN{{--bg:#00080d;--bg2:#001018;--bg3:#001520;--pri:#00d9ff;--dim:#006680;--border:#002c38;--mid:#005566;--dark:#000c14;}}

html,body{{
  width:100%;background:var(--bg);
  font-family:'Share Tech Mono',monospace;color:var(--pri);
  overflow-x:hidden;
}}
body::before{{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:9998;
  background:repeating-linear-gradient(to bottom,transparent 0,transparent 3px,rgba(0,0,0,0.22) 3px,rgba(0,0,0,0.22) 4px);
}}
body::after{{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:9997;
  background:radial-gradient(ellipse 92% 92% at 50% 50%,transparent 48%,rgba(0,0,0,0.72) 100%);
}}

/* MENUBAR */
.menubar{{
  display:flex;justify-content:space-between;align-items:stretch;
  height:30px;border-bottom:1px solid var(--border);background:var(--bg2);
  font-size:0.7rem;letter-spacing:1px;position:sticky;top:0;z-index:500;user-select:none;
}}
.menubar-left,.menubar-right{{display:flex;align-items:stretch;}}
.tab{{display:flex;align-items:center;padding:0 10px;color:var(--dim);border-right:1px solid var(--border);cursor:default;white-space:nowrap;}}
.tab .key{{color:var(--border);margin-right:3px;}}
.tab.active{{color:var(--pri);background:var(--bg);border-top:1px solid var(--mid);border-bottom:1px solid var(--mid);}}
.tab.active .key{{color:var(--dim);}}
.menubar-right{{border-left:1px solid var(--border);}}
.chip{{display:flex;align-items:center;padding:0 10px;border-left:1px solid var(--border);background:var(--bg2);color:var(--pri);cursor:pointer;white-space:nowrap;font-size:0.7rem;letter-spacing:1px;}}
.chip .key{{color:var(--dim);margin-right:3px;}}
.chip:hover{{background:var(--dark);}}
.chip.site{{background:var(--bg);cursor:default;}}
.chip.site:hover{{background:var(--bg);}}

/* PAGE */
.page{{display:flex;justify-content:center;align-items:flex-start;padding:28px 20px 40px;position:relative;z-index:1;}}

/* LOGIN BOX */
.loginbox{{width:min(700px,96vw);border:1px solid var(--mid);background:var(--bg);position:relative;}}
.loginbox-head{{
  display:flex;align-items:center;justify-content:center;
  height:28px;font-size:0.7rem;letter-spacing:3px;
  border-bottom:1px solid var(--border);background:var(--bg2);position:relative;
}}
.loginbox-head::before{{content:'── ';color:var(--border);position:absolute;left:12px;}}
.loginbox-head::after{{content:' ──';color:var(--border);position:absolute;right:12px;}}

/* CRT SCREEN */
.crt-screen{{position:relative;background:#0d0500;padding:32px 48px 32px;overflow:hidden;}}
.crt-screen::before{{
  content:'';position:absolute;inset:0;pointer-events:none;z-index:2;mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E");
  background-size:200px 200px;
}}
.crt-screen::after{{
  content:'';position:absolute;inset:0;pointer-events:none;z-index:3;
  background:repeating-linear-gradient(to bottom,transparent 0,transparent 2px,rgba(0,0,0,0.28) 2px,rgba(0,0,0,0.28) 4px);
}}
.crt-tint{{position:absolute;inset:0;pointer-events:none;z-index:4;background:radial-gradient(ellipse 80% 70% at 50% 40%,rgba(180,60,0,0.12) 0%,transparent 70%);}}
@keyframes flicker{{0%,100%{{opacity:1}}92%{{opacity:1}}93%{{opacity:.94}}94%{{opacity:1}}96%{{opacity:.97}}97%{{opacity:1}}}}
.crt-screen{{animation:flicker 8s infinite;}}
.crt-content{{position:relative;z-index:10;}}

.logo-img{{display:block;width:92px;height:92px;border-radius:10px;margin:0 auto 16px;filter:drop-shadow(0 0 14px rgba(255,140,0,0.55));}}

.app-title{{
  font-family:'VT323',monospace;font-size:3.4rem;letter-spacing:10px;
  text-align:center;color:var(--pri);text-transform:uppercase;
  text-shadow:0 0 18px rgba(255,140,0,0.6),0 0 4px rgba(255,200,0,0.4);
  line-height:1;margin-bottom:4px;
}}
.app-sub{{font-size:0.65rem;letter-spacing:5px;text-align:center;color:var(--dim);text-transform:uppercase;margin-bottom:28px;}}

/* PASSWORD FIELD — full rectangular */
.field-wrap{{border:1px solid var(--mid);margin-bottom:16px;}}
.field-label{{
  display:block;font-size:0.75rem;color:var(--pri);letter-spacing:3px;
  text-transform:uppercase;padding:7px 12px 6px;
  background:rgba(20,12,0,0.9);border-bottom:1px solid var(--border);
}}
.field-input{{
  display:block;width:100%;height:44px;
  background:rgba(8,5,0,0.95);border:none;
  color:var(--pri);font-family:'Share Tech Mono',monospace;
  font-size:1.05rem;letter-spacing:3px;padding:0 12px;outline:none;
  caret-color:var(--pri);
}}
.field-input::placeholder{{color:var(--dim);font-style:italic;letter-spacing:2px;font-size:0.9rem;}}
.field-wrap:focus-within{{border-color:var(--pri);}}
.field-wrap:focus-within .field-label{{color:var(--pri);background:rgba(30,18,0,0.95);}}

/* SIGN IN BUTTON */
.btn-signin{{
  display:block;width:100%;height:50px;
  background:var(--pri);color:var(--bg);
  font-family:'Share Tech Mono',monospace;font-size:0.95rem;
  letter-spacing:6px;text-transform:uppercase;
  border:none;cursor:pointer;transition:opacity 0.15s;
  background-image:repeating-linear-gradient(to bottom,transparent 0,transparent 2px,rgba(0,0,0,0.08) 2px,rgba(0,0,0,0.08) 4px);
}}
.btn-signin:hover{{opacity:.88;}}
.btn-signin:active{{opacity:.72;}}

.vt-error{{font-size:0.75rem;color:#ff5533;letter-spacing:1px;padding:8px 0 4px;text-transform:uppercase;}}
.vt-warn{{font-size:0.7rem;color:var(--dim);letter-spacing:1px;padding:2px 0 8px;}}

/* STATUS / FOOTER */
.loginbox-status{{font-size:0.58rem;color:var(--border);text-align:center;letter-spacing:2px;text-transform:uppercase;padding:10px 0 6px;background:var(--bg);}}
.loginbox-footer{{font-size:0.55rem;color:var(--border);text-align:center;letter-spacing:1px;padding:6px 18px 10px;border-top:1px solid var(--border);background:var(--bg);text-transform:uppercase;}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
.dot{{display:inline-block;width:5px;height:5px;border-radius:50%;background:var(--pri);vertical-align:middle;margin-right:5px;animation:blink 1.1s step-end infinite;}}

/* APPEARANCE PANEL */
.appear{{
  display:none;position:fixed;top:30px;right:0;z-index:9999;
  width:230px;background:var(--bg2);
  border:1px solid var(--mid);border-top:none;
  border-left:4px solid transparent;
  border-image:url("data:image/gif;base64,{fade_b64}") 8 repeat;
  font-family:'Share Tech Mono',monospace;
}}
.appear.open{{display:block;}}
.ap-head{{
  font-size:0.62rem;letter-spacing:3px;color:var(--dim);text-align:center;
  padding:8px 0 7px;text-transform:uppercase;
  border-bottom:3px solid transparent;
  border-image:url("data:image/gif;base64,{fade_b64}") 8 repeat;
}}
.ap-sec{{padding:8px 12px 4px;}}
.ap-lbl{{font-size:0.58rem;color:var(--dim);letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;}}
.ap-grp{{
  background:var(--bg);padding:2px 0;margin-bottom:6px;
  border:2px solid transparent;
  border-image:url("data:image/gif;base64,{fade_b64}") 8 repeat;
}}
.ap-opt{{display:flex;align-items:center;padding:6px 10px;font-size:0.78rem;cursor:pointer;gap:8px;color:var(--pri);letter-spacing:.5px;}}
.ap-opt:hover{{background:rgba(255,255,255,.05);}}
.ap-dot{{font-size:.65rem;width:12px;}}
.ap-arrow{{margin-left:auto;font-size:.62rem;color:var(--dim);}}
.ap-foot{{
  font-size:.6rem;color:var(--border);text-align:center;padding:7px 0;
  letter-spacing:1px;border-top:3px solid transparent;
  border-image:url("data:image/gif;base64,{fade_b64}") 8 repeat;
}}
</style>
</head>
<body id="body" class="">

<!-- MENUBAR -->
<div class="menubar">
  <div class="menubar-left">
    <div class="tab active"><span class="key">^1</span>LOGIN</div>
    <div class="tab"><span class="key">^2</span>STATUS</div>
    <div class="tab"><span class="key">^3</span>INFO</div>
  </div>
  <div class="menubar-right">
    <div class="chip" id="theme-btn" onclick="toggleAppear()">
      <span class="key">^T</span><span id="theme-label">VT220</span>
    </div>
    <div class="chip site">RSU TERMINAL</div>
  </div>
</div>

<!-- APPEARANCE PANEL -->
<div class="appear" id="appear">
  <div class="ap-head">── APPEARANCE ──</div>
  <div class="ap-sec">
    <div class="ap-lbl">THEME</div>
    <div class="ap-grp">
      <div class="ap-opt" onclick="setTheme('VT220')"><span class="ap-dot" id="d-VT220">▶</span>VT220<span class="ap-arrow" id="a-VT220">←</span></div>
      <div class="ap-opt" onclick="setTheme('GREEN')"><span class="ap-dot" id="d-GREEN">○</span>Green Phosphor<span class="ap-arrow" id="a-GREEN" style="display:none">←</span></div>
      <div class="ap-opt" onclick="setTheme('CYAN')"><span class="ap-dot" id="d-CYAN">○</span>Cyan VDT<span class="ap-arrow" id="a-CYAN" style="display:none">←</span></div>
    </div>
  </div>
  <div class="ap-foot">↑↓ NAV · ↵ SEL · ESC</div>
</div>

<!-- PAGE -->
<div class="page">
  <div class="loginbox">
    <div class="loginbox-head">LOGIN</div>
    <div class="crt-screen">
      <div class="crt-tint"></div>
      <div class="crt-content">
        {logo_html}
        <div class="app-title">RSU TERMINAL</div>
        <div class="app-sub">Redistribution Strategy Unit</div>
        <div class="field-wrap">
          <label class="field-label" for="pwd">PASSWORD</label>
          <input class="field-input" type="password" id="pwd"
                 placeholder="Enter your password" autocomplete="current-password">
        </div>
        {error_block}
        {attempts_block}
        <button class="btn-signin" id="btn-signin" onclick="submitPassword()">SIGN IN</button>
      </div>
    </div>
    <div class="loginbox-status"><span class="dot"></span>SECURE CONNECTION · AES-256 · TLS 1.3</div>
    <div class="loginbox-footer">🔒 SSL ENCRYPTED · © 2026 RSU TERMINAL v2.0 // STATUS: ACTIVE</div>
  </div>
</div>

<script>
// ── Streamlit component bridge ──────────────────────────────────────────────
// streamlit:setComponentValue sends data back to Python as the component return value
function sendToStreamlit(data) {{
  window.parent.postMessage({{
    type: 'streamlit:setComponentValue',
    value: data
  }}, '*');
}}

var currentTheme = '{theme}';
var panelOpen = false;

function applyThemeClass(k) {{
  document.getElementById('body').className = (k === 'VT220') ? '' : 't-' + k;
  var labels = {{VT220:'VT220', GREEN:'P3 GREEN', CYAN:'CYAN VDT'}};
  document.getElementById('theme-label').textContent = labels[k] || k;
}}

function setTheme(k) {{
  currentTheme = k;
  applyThemeClass(k);
  ['VT220','GREEN','CYAN'].forEach(function(n) {{
    document.getElementById('d-'+n).textContent = (n===k)?'▶':'○';
    document.getElementById('a-'+n).style.display = (n===k)?'':'none';
  }});
  panelOpen = false;
  document.getElementById('appear').className = 'appear';
  sendToStreamlit({{action:'theme', value:k}});
}}

function toggleAppear() {{
  panelOpen = !panelOpen;
  document.getElementById('appear').className = 'appear'+(panelOpen?' open':'');
}}

function submitPassword() {{
  var pwd = document.getElementById('pwd').value;
  if (!pwd) return;
  document.getElementById('btn-signin').textContent = 'VERIFICANDO...';
  document.getElementById('btn-signin').disabled = true;
  sendToStreamlit({{action:'login', value:pwd}});
}}

document.addEventListener('keydown', function(e) {{
  if (e.key==='Escape') {{
    panelOpen=false;
    document.getElementById('appear').className='appear';
  }}
  if (e.key==='Enter') {{
    if (document.activeElement===document.getElementById('pwd')) submitPassword();
  }}
  if ((e.ctrlKey||e.metaKey) && e.key==='t') {{
    e.preventDefault(); toggleAppear();
  }}
}});

applyThemeClass(currentTheme);
// Focus after a short delay to ensure iframe is ready
setTimeout(function(){{ document.getElementById('pwd').focus(); }}, 100);
</script>
</body>
</html>"""


def login() -> bool:
    # ── INIT ──────────────────────────────────────────────────────────────────
    defaults = {
        "auth": False, "login_attempts": 0,
        "lockout_time": None, "last_activity": None,
        "vt_theme": "VT220", "vt_error": "",
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

    # ── STREAMLIT CHROME: hide everything ─────────────────────────────────────
    st.markdown("""
    <style>
    #MainMenu,footer,header{visibility:hidden!important}
    .stApp{background:#0a0800!important}
    .main .block-container{padding:0!important;max-width:100%!important;margin:0!important}
    section[data-testid="stMain"]>div{padding:0!important}
    div[data-testid="stVerticalBlock"]{background:transparent!important;border:none!important;box-shadow:none!important;padding:0!important;gap:0!important}
    iframe{border:none!important;display:block!important}
    </style>
    """, unsafe_allow_html=True)

    # ── RENDER HTML COMPONENT ─────────────────────────────────────────────────
    logo_b64  = get_logo_base64() or ""
    error_msg = st.session_state.get("vt_error", "")
    attempts_l = 5 - st.session_state.get("login_attempts", 0)
    theme     = st.session_state.get("vt_theme", "VT220")

    html_content = _build_html(logo_b64, theme, error_msg, attempts_l)

    # components.html returns the value sent via Streamlit.setComponentValue
    result = components.html(html_content, height=740, scrolling=False)

    # ── PROCESS COMPONENT RETURN VALUE ────────────────────────────────────────
    # result is whatever was passed to sendToStreamlit({action, value})
    if result is not None and isinstance(result, dict):
        action = result.get("action")
        value  = result.get("value", "")

        if action == "theme" and value in ("VT220", "GREEN", "CYAN"):
            st.session_state["vt_theme"] = value
            st.rerun()

        elif action == "login" and value:
            pwd_hash  = hashlib.sha256(value.encode()).hexdigest()
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
