# modules/auth.py
import os
import hashlib
import time
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

    fade_url = f"data:image/gif;base64,{FADE_GIF_B64}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

*{{box-sizing:border-box;margin:0;padding:0}}

/* ─── THEME VARS ─────────────────────────── */
:root{{
  --bg:#0a0800;--bg2:#130f00;--bg3:#1a1200;
  --pri:#ffb300;--dim:#7a5500;--border:#3d2900;--mid:#5a3e00;--dark:#1e1400;
  --crt-r:180;--crt-g:80;--crt-b:0;
}}
.t-GREEN{{
  --bg:#000d04;--bg2:#001508;--bg3:#001e0a;
  --pri:#00ffad;--dim:#008855;--border:#003820;--mid:#006640;--dark:#001810;
  --crt-r:0;--crt-g:200;--crt-b:100;
}}
.t-CYAN{{
  --bg:#00080d;--bg2:#001018;--bg3:#001520;
  --pri:#00d9ff;--dim:#006680;--border:#002c38;--mid:#005566;--dark:#000c14;
  --crt-r:0;--crt-g:160;--crt-b:220;
}}

/* ─── GLOBAL ──────────────────────────────── */
html,body{{
  width:100%;height:100%;min-height:600px;
  background:var(--bg);
  font-family:'Share Tech Mono',monospace;
  color:var(--pri);
  overflow-x:hidden;
}}

/* CRT scanlines */
body::before{{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:9998;
  background:repeating-linear-gradient(
    to bottom,transparent 0,transparent 3px,
    rgba(0,0,0,0.22) 3px,rgba(0,0,0,0.22) 4px);
}}
/* phosphor vignette */
body::after{{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:9997;
  background:radial-gradient(ellipse 92% 92% at 50% 50%,transparent 48%,rgba(0,0,0,0.72) 100%);
}}

/* ─── MENUBAR ─────────────────────────────── */
.menubar{{
  display:flex;justify-content:space-between;align-items:stretch;
  height:30px;border-bottom:1px solid var(--border);background:var(--bg2);
  font-size:0.7rem;letter-spacing:1px;
  position:sticky;top:0;z-index:500;
  user-select:none;
}}
.menubar-left,.menubar-right{{display:flex;align-items:stretch;}}
.tab{{
  display:flex;align-items:center;padding:0 10px;
  color:var(--dim);border-right:1px solid var(--border);
  cursor:default;white-space:nowrap;
}}
.tab .key{{color:var(--border);margin-right:3px;}}
.tab.active{{
  color:var(--pri);background:var(--bg);
  border-top:1px solid var(--mid);border-bottom:1px solid var(--mid);
}}
.tab.active .key{{color:var(--dim);}}
.menubar-right{{border-left:1px solid var(--border);}}
.chip{{
  display:flex;align-items:center;padding:0 10px;
  border-left:1px solid var(--border);background:var(--bg2);
  color:var(--pri);cursor:pointer;white-space:nowrap;
  font-size:0.7rem;letter-spacing:1px;
}}
.chip .key{{color:var(--dim);margin-right:3px;}}
.chip:hover{{background:var(--dark);}}
.chip.site{{background:var(--bg);cursor:default;}}
.chip.site:hover{{background:var(--bg);}}

/* ─── LAYOUT: FULL CENTER ─────────────────── */
.page{{
  display:flex;
  justify-content:center;
  align-items:flex-start;
  padding:32px 20px 40px;
  position:relative;z-index:1;
}}

/* ─── LOGIN BOX ───────────────────────────── */
.loginbox{{
  width:520px;
  border:1px solid var(--mid);
  background:var(--bg);
  position:relative;
}}

.loginbox-head{{
  display:flex;align-items:center;justify-content:center;
  height:28px;font-size:0.7rem;letter-spacing:3px;
  border-bottom:1px solid var(--border);background:var(--bg2);
  position:relative;
}}
.loginbox-head::before{{content:'── ';color:var(--border);position:absolute;left:12px;}}
.loginbox-head::after{{content:' ──';color:var(--border);position:absolute;right:12px;}}

/* ─── CRT INNER AREA ──────────────────────── */
.crt-screen{{
  position:relative;
  background:#0d0500;
  padding:28px 32px 24px;
  overflow:hidden;
}}

/* Red-tinted phosphor noise via canvas */
.crt-screen::before{{
  content:'';
  position:absolute;inset:0;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E");
  background-repeat:repeat;
  background-size:200px 200px;
  pointer-events:none;
  z-index:2;
  mix-blend-mode:overlay;
}}
/* scanlines inside CRT too */
.crt-screen::after{{
  content:'';
  position:absolute;inset:0;
  background:repeating-linear-gradient(
    to bottom,transparent 0,transparent 2px,
    rgba(0,0,0,0.30) 2px,rgba(0,0,0,0.30) 4px);
  pointer-events:none;
  z-index:3;
}}

/* warm tint overlay */
.crt-tint{{
  position:absolute;inset:0;
  background:radial-gradient(ellipse 80% 70% at 50% 40%,
    rgba(180,60,0,0.12) 0%,transparent 70%);
  pointer-events:none;z-index:4;
}}

/* CRT screen flicker */
@keyframes flicker{{
  0%,100%{{opacity:1;}}
  92%{{opacity:1;}}
  93%{{opacity:0.94;}}
  94%{{opacity:1;}}
  96%{{opacity:0.97;}}
  97%{{opacity:1;}}
}}
.crt-screen{{animation:flicker 8s infinite;}}

/* content inside CRT must be above overlays */
.crt-content{{position:relative;z-index:10;}}

/* logo */
.logo-img{{
  display:block;width:72px;height:72px;border-radius:8px;
  margin:0 auto 14px;
  filter:drop-shadow(0 0 10px rgba(255,140,0,0.5));
}}

/* App title */
.app-title{{
  font-family:'VT323',monospace;font-size:2.6rem;letter-spacing:8px;
  text-align:center;color:var(--pri);text-transform:uppercase;
  text-shadow:0 0 18px rgba(255,140,0,0.6),0 0 4px rgba(255,200,0,0.4);
  line-height:1;margin-bottom:3px;
}}
.app-sub{{
  font-size:0.6rem;letter-spacing:4px;text-align:center;
  color:var(--dim);text-transform:uppercase;margin-bottom:20px;
}}

/* Field */
.field-label{{
  display:block;font-size:0.72rem;color:var(--pri);letter-spacing:2px;
  text-transform:uppercase;padding:4px 6px 3px;
  background:rgba(0,0,0,0.5);
  border:1px solid var(--border);border-bottom:none;
}}
.field-input{{
  display:block;width:100%;height:34px;
  background:rgba(0,0,0,0.6);
  border:none;border-bottom:1px solid var(--border);
  color:var(--pri);font-family:'Share Tech Mono',monospace;
  font-size:0.88rem;letter-spacing:2px;padding:0 8px;outline:none;
  caret-color:var(--pri);transition:border-color 0.1s;
}}
.field-input::placeholder{{color:var(--border);font-style:italic;}}
.field-input:focus{{border-bottom-color:var(--dim);}}

/* Button */
.btn-signin{{
  display:block;width:100%;height:46px;
  background:var(--pri);color:var(--bg);
  font-family:'Share Tech Mono',monospace;
  font-size:0.9rem;letter-spacing:5px;text-transform:uppercase;
  border:none;cursor:pointer;margin-top:14px;
  transition:opacity 0.15s;
  /* CRT scanlines on button too */
  background-image:repeating-linear-gradient(
    to bottom,transparent 0,transparent 2px,
    rgba(0,0,0,0.08) 2px,rgba(0,0,0,0.08) 4px);
}}
.btn-signin:hover{{opacity:0.88;}}
.btn-signin:active{{opacity:0.72;}}

/* Feedback */
.vt-error{{
  font-size:0.72rem;color:#ff5533;letter-spacing:1px;
  padding:6px 0 2px;text-transform:uppercase;
}}
.vt-warn{{
  font-size:0.68rem;color:var(--dim);letter-spacing:1px;padding:2px 0;
}}

/* Status / footer */
.loginbox-status{{
  font-size:0.58rem;color:var(--border);text-align:center;
  letter-spacing:2px;text-transform:uppercase;padding:8px 0 5px;
  background:var(--bg);
}}
.loginbox-footer{{
  font-size:0.55rem;color:var(--border);text-align:center;
  letter-spacing:1px;padding:5px 18px 9px;
  border-top:1px solid var(--border);background:var(--bg);
  text-transform:uppercase;
}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:0;}}}}
.dot{{
  display:inline-block;width:5px;height:5px;border-radius:50%;
  background:var(--pri);vertical-align:middle;margin-right:5px;
  animation:blink 1.1s step-end infinite;
}}

/* ─── APPEARANCE PANEL ────────────────────── */
.appear{{
  display:none;position:fixed;top:30px;right:0;z-index:9999;
  width:230px;
  background:var(--bg2);
  border:1px solid var(--mid);border-top:none;
  font-family:'Share Tech Mono',monospace;
  /* fade.gif as border texture on left+bottom */
  border-left: 4px solid transparent;
  border-image: url("data:image/gif;base64,{FADE_GIF_B64}") 8 repeat;
}}
.appear.open{{display:block;}}
.ap-head{{
  font-size:0.62rem;letter-spacing:3px;color:var(--dim);
  text-align:center;padding:8px 0 7px;
  border-bottom:3px solid transparent;
  border-image:url("data:image/gif;base64,{FADE_GIF_B64}") 8 repeat;
  text-transform:uppercase;
}}
.ap-sec{{padding:8px 12px 4px;}}
.ap-lbl{{
  font-size:0.58rem;color:var(--dim);letter-spacing:2px;
  text-transform:uppercase;margin-bottom:4px;
}}
.ap-grp{{
  background:var(--bg);
  border:2px solid transparent;
  border-image:url("data:image/gif;base64,{FADE_GIF_B64}") 8 repeat;
  padding:2px 0;margin-bottom:6px;
}}
.ap-opt{{
  display:flex;align-items:center;
  padding:6px 10px;font-size:0.78rem;cursor:pointer;
  gap:8px;color:var(--pri);letter-spacing:0.5px;
}}
.ap-opt:hover{{background:rgba(255,255,255,0.05);}}
.ap-dot{{font-size:0.65rem;width:12px;}}
.ap-arrow{{margin-left:auto;font-size:0.62rem;color:var(--dim);}}
.ap-foot{{
  font-size:0.6rem;color:var(--border);text-align:center;
  padding:7px 0;
  border-top:3px solid transparent;
  border-image:url("data:image/gif;base64,{FADE_GIF_B64}") 8 repeat;
  letter-spacing:1px;
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
      <div class="ap-opt" onclick="setTheme('VT220')">
        <span class="ap-dot" id="d-VT220">▶</span>VT220
        <span class="ap-arrow" id="a-VT220">←</span>
      </div>
      <div class="ap-opt" onclick="setTheme('GREEN')">
        <span class="ap-dot" id="d-GREEN">○</span>Green Phosphor
        <span class="ap-arrow" id="a-GREEN" style="display:none">←</span>
      </div>
      <div class="ap-opt" onclick="setTheme('CYAN')">
        <span class="ap-dot" id="d-CYAN">○</span>Cyan VDT
        <span class="ap-arrow" id="a-CYAN" style="display:none">←</span>
      </div>
    </div>
  </div>
  <div class="ap-foot">↑↓ NAV · ↵ SEL · ESC</div>
</div>

<!-- PAGE: centered -->
<div class="page">
  <div class="loginbox">
    <div class="loginbox-head">LOGIN</div>

    <!-- CRT phosphor screen area -->
    <div class="crt-screen">
      <div class="crt-tint"></div>
      <div class="crt-content">
        {logo_html}
        <div class="app-title">RSU TERMINAL</div>
        <div class="app-sub">Redistribution Strategy Unit</div>

        <label class="field-label" for="pwd">PASSWORD</label>
        <input class="field-input" type="password" id="pwd"
               placeholder="Enter your password" autocomplete="current-password">

        {error_block}
        {attempts_block}

        <button class="btn-signin" onclick="submitPassword()">SIGN IN</button>
      </div>
    </div>
    <!-- end CRT screen -->

    <div class="loginbox-status">
      <span class="dot"></span>SECURE CONNECTION · AES-256 · TLS 1.3
    </div>
    <div class="loginbox-footer">
      🔒 SSL ENCRYPTED · © 2026 RSU TERMINAL v2.0 // STATUS: ACTIVE
    </div>
  </div>
</div>

<script>
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
  window.parent.postMessage({{type:'vt_theme', value:k}}, '*');
}}

function toggleAppear() {{
  panelOpen = !panelOpen;
  document.getElementById('appear').className = 'appear'+(panelOpen?' open':'');
}}

function submitPassword() {{
  var pwd = document.getElementById('pwd').value;
  if (!pwd) return;
  window.parent.postMessage({{type:'vt_login', value:pwd}}, '*');
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
document.getElementById('pwd').focus();
</script>
</body>
</html>"""


def login() -> bool:
    defaults = {
        "auth": False, "login_attempts": 0,
        "lockout_time": None, "last_activity": None,
        "vt_theme": "VT220",
        "vt_pwd_submitted": None,
        "vt_error": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Timeout
    if st.session_state["auth"] and st.session_state["last_activity"]:
        if datetime.now() - st.session_state["last_activity"] > timedelta(minutes=30):
            st.session_state["auth"] = False
            st.session_state["last_activity"] = None
            st.rerun()

    if st.session_state["auth"]:
        st.session_state["last_activity"] = datetime.now()
        return True

    # Lockout
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

    # Handle password submit
    submitted_pwd = st.session_state.get("vt_pwd_submitted")
    if submitted_pwd:
        st.session_state["vt_pwd_submitted"] = None
        if not st.session_state["lockout_time"]:
            pwd_hash  = hashlib.sha256(submitted_pwd.encode()).hexdigest()
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
                    st.session_state["vt_error"] = "⛔ BLOQUEADO — 15 MIN"
                else:
                    st.session_state["vt_error"] = "⚠ CONTRASEÑA INCORRECTA"
                st.rerun()

    # Strip all Streamlit chrome
    st.markdown("""
    <style>
    #MainMenu,footer,header{visibility:hidden!important}
    .stApp{background:#0a0800!important}
    .main .block-container{padding:0!important;max-width:100%!important;margin:0!important}
    section[data-testid="stMain"]>div{padding:0!important}
    div[data-testid="stVerticalBlock"]{
        background:transparent!important;border:none!important;
        box-shadow:none!important;padding:0!important;gap:0!important}
    div[data-testid="stHorizontalBlock"],
    div[data-testid="column"]{
        background:transparent!important;border:none!important;
        box-shadow:none!important;padding:0!important;
        gap:0!important;min-height:0!important}
    iframe{border:none!important;display:block!important}
    /* Hide ALL stray buttons */
    button[kind="secondary"]{display:none!important}
    div[data-testid="stButton"]{display:none!important}
    </style>
    """, unsafe_allow_html=True)

    logo_b64   = get_logo_base64() or ""
    error_msg  = st.session_state.get("vt_error", "")
    attempts_l = 5 - st.session_state.get("login_attempts", 0)
    theme      = st.session_state.get("vt_theme", "VT220")

    html_content = _build_html(logo_b64, theme, error_msg, attempts_l)

    # Render in isolated iframe — height covers login box fully
    components.html(html_content, height=620, scrolling=False)

    # Message bridge: listen for postMessage from iframe
    st.markdown("""
    <script>
    (function(){
      if(window._vtListenerAttached) return;
      window._vtListenerAttached = true;
      window.addEventListener('message', function(e){
        var d = e.data;
        if(!d||!d.type) return;
        if(d.type==='vt_login'){
          var url=new URL(window.location.href);
          url.searchParams.set('_vt_pwd', btoa(unescape(encodeURIComponent(d.value))));
          window.location.href=url.toString();
        }
        if(d.type==='vt_theme'){
          var url=new URL(window.location.href);
          url.searchParams.set('_vt_theme', d.value);
          window.location.href=url.toString();
        }
      });
    })();
    </script>
    """, unsafe_allow_html=True)

    # Read query params
    qp = st.query_params
    if "_vt_pwd" in qp:
        try:
            pwd_plain = base64.b64decode(qp["_vt_pwd"]).decode("utf-8")
            st.session_state["vt_pwd_submitted"] = pwd_plain
        except Exception:
            pass
        st.query_params.clear()
        st.rerun()

    if "_vt_theme" in qp:
        tv = qp["_vt_theme"]
        if tv in ("VT220", "GREEN", "CYAN"):
            st.session_state["vt_theme"] = tv
        st.query_params.clear()
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
