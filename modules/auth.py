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


def get_logo_base64():
    try:
        if os.path.exists("assets/logo.png"):
            with open("assets/logo.png", "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return None


def _build_html(logo_b64: str, theme: str, error_msg: str, attempts_left: int) -> str:
    """Return the full HTML for the login iframe."""

    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="logo-img" alt="RSU">'

    error_block = ""
    if error_msg:
        error_block = f'<div class="vt-error">{error_msg}</div>'

    attempts_block = ""
    if 0 < attempts_left <= 2:
        attempts_block = f'<div class="vt-warn">⚠ {attempts_left} INTENTOS RESTANTES</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

/* ── RESET ──────────────────────────────── */
*{{box-sizing:border-box;margin:0;padding:0}}

/* ── THEMES ─────────────────────────────── */
:root{{
  --bg:#0a0800;--bg2:#130f00;--bg3:#1a1200;
  --pri:#ffb300;--dim:#7a5500;--border:#3d2900;--mid:#5a3e00;--dark:#1e1400;
}}
.t-GREEN{{
  --bg:#000d04;--bg2:#001508;--bg3:#001e0a;
  --pri:#00ffad;--dim:#008855;--border:#003820;--mid:#006640;--dark:#001810;
}}
.t-CYAN{{
  --bg:#00080d;--bg2:#001018;--bg3:#001520;
  --pri:#00d9ff;--dim:#006680;--border:#002c38;--mid:#005566;--dark:#000c14;
}}

/* ── GLOBAL ─────────────────────────────── */
html,body{{
  width:100%;height:100%;
  background:var(--bg);
  font-family:'Share Tech Mono',monospace;
  color:var(--pri);
  overflow-x:hidden;
  position:relative;
}}

/* CRT scanlines */
body::before{{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:9998;
  background:repeating-linear-gradient(
    to bottom,transparent 0,transparent 3px,
    rgba(0,0,0,0.25) 3px,rgba(0,0,0,0.25) 4px);
}}
/* Phosphor vignette */
body::after{{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:9997;
  background:radial-gradient(ellipse 90% 90% at 50% 50%,transparent 50%,rgba(0,0,0,0.65) 100%);
}}

/* ── TOP MENUBAR ─────────────────────────── */
.menubar{{
  display:flex;justify-content:space-between;align-items:stretch;
  height:30px;border-bottom:1px solid var(--border);background:var(--bg2);
  font-size:0.7rem;letter-spacing:1px;
  position:sticky;top:0;z-index:200;
}}
.menubar-left,.menubar-right{{display:flex;align-items:stretch;}}
.tab{{
  display:flex;align-items:center;padding:0 10px;
  color:var(--dim);border-right:1px solid var(--border);
  cursor:default;white-space:nowrap;user-select:none;
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
  color:var(--pri);cursor:pointer;white-space:nowrap;user-select:none;
  font-size:0.7rem;letter-spacing:1px;
}}
.chip .key{{color:var(--dim);margin-right:3px;}}
.chip:hover{{background:var(--dark);}}
.chip.site{{background:var(--bg);cursor:default;}}
.chip.site:hover{{background:var(--bg);}}

/* ── PAGE ────────────────────────────────── */
.page{{
  padding:20px 0 0 28px;
  position:relative;z-index:1;
}}
.page-title{{font-size:0.78rem;letter-spacing:1px;margin-bottom:2px;}}
.page-sub{{font-size:0.7rem;color:var(--dim);margin-bottom:18px;}}

/* ── LOGIN BOX ───────────────────────────── */
.loginbox{{
  width:460px;
  border:1px solid var(--mid);
  background:var(--bg);
}}
.loginbox-head{{
  display:flex;align-items:center;justify-content:center;
  height:28px;font-size:0.7rem;letter-spacing:3px;
  border-bottom:1px solid var(--border);background:var(--bg2);
  position:relative;
}}
.loginbox-head::before{{content:'── ';color:var(--border);position:absolute;left:12px;}}
.loginbox-head::after{{content:' ──';color:var(--border);position:absolute;right:12px;}}
.loginbox-body{{padding:16px 18px 0;}}

/* Title */
.app-title{{
  font-family:'VT323',monospace;font-size:2.1rem;letter-spacing:6px;
  text-align:center;color:var(--pri);text-transform:uppercase;
  text-shadow:0 0 14px rgba(255,179,0,0.4);line-height:1;margin-bottom:2px;
}}
.app-sub{{
  font-size:0.58rem;letter-spacing:3px;text-align:center;
  color:var(--dim);text-transform:uppercase;margin-bottom:14px;
}}

/* Logo */
.logo-img{{
  display:block;width:56px;height:56px;border-radius:6px;
  margin:0 auto 10px;opacity:0.9;
}}

/* Field */
.field-label{{
  display:block;font-size:0.7rem;color:var(--pri);letter-spacing:2px;
  text-transform:uppercase;padding:4px 6px 3px;background:var(--bg2);
  border:1px solid var(--border);border-bottom:none;margin-top:4px;
}}
.field-input{{
  display:block;width:100%;height:32px;
  background:var(--bg3);border:none;border-bottom:1px solid var(--border);
  color:var(--pri);font-family:'Share Tech Mono',monospace;
  font-size:0.82rem;letter-spacing:1px;padding:0 8px;outline:none;
  caret-color:var(--pri);transition:border-color 0.1s;
}}
.field-input::placeholder{{color:var(--border);font-style:italic;}}
.field-input:focus{{border-bottom-color:var(--dim);}}

/* Button */
.btn-signin{{
  display:block;width:100%;height:44px;
  background:var(--pri);color:var(--bg);
  font-family:'Share Tech Mono',monospace;
  font-size:0.85rem;letter-spacing:4px;text-transform:uppercase;
  border:none;cursor:pointer;margin-top:12px;
  transition:opacity 0.15s;
}}
.btn-signin:hover{{opacity:0.85;}}
.btn-signin:active{{opacity:0.7;}}

/* Feedback */
.vt-error{{
  font-size:0.72rem;color:#ff4444;letter-spacing:1px;
  padding:6px 0 2px;text-transform:uppercase;
}}
.vt-warn{{
  font-size:0.68rem;color:var(--dim);letter-spacing:1px;
  padding:2px 0;
}}

/* Status / footer */
.loginbox-status{{
  font-size:0.58rem;color:var(--border);text-align:center;
  letter-spacing:2px;text-transform:uppercase;padding:8px 0 5px;
}}
.loginbox-footer{{
  font-size:0.55rem;color:var(--border);text-align:center;
  letter-spacing:1px;padding:5px 18px 10px;
  border-top:1px solid var(--border);text-transform:uppercase;
}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:0;}}}}
.dot{{
  display:inline-block;width:5px;height:5px;border-radius:50%;
  background:var(--pri);vertical-align:middle;margin-right:5px;
  animation:blink 1.1s step-end infinite;
}}

/* ── APPEARANCE PANEL ────────────────────── */
.appear{{
  display:none;position:fixed;top:30px;right:0;z-index:9999;
  width:210px;border:1px solid var(--mid);border-top:none;
  background:var(--bg2);font-family:'Share Tech Mono',monospace;
}}
.appear.open{{display:block;}}
.ap-head{{
  font-size:0.62rem;letter-spacing:3px;color:var(--dim);
  text-align:center;padding:7px 0 6px;
  border-bottom:1px solid var(--border);text-transform:uppercase;
}}
.ap-sec{{padding:8px 10px 4px;}}
.ap-lbl{{font-size:0.58rem;color:var(--dim);letter-spacing:2px;
  text-transform:uppercase;margin-bottom:4px;}}
.ap-grp{{background:var(--bg);border:1px solid var(--border);padding:2px 0;margin-bottom:4px;}}
.ap-opt{{
  display:flex;align-items:center;
  padding:5px 8px;font-size:0.75rem;cursor:pointer;
  gap:8px;color:var(--pri);letter-spacing:0.5px;
}}
.ap-opt:hover{{background:rgba(255,255,255,0.04);}}
.ap-dot{{font-size:0.62rem;width:10px;}}
.ap-arrow{{margin-left:auto;font-size:0.6rem;color:var(--dim);}}
.ap-foot{{
  font-size:0.58rem;color:var(--border);text-align:center;
  padding:6px 0;border-top:1px solid var(--border);letter-spacing:1px;
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
  <div class="ap-head"><span style="opacity:0.4;">── </span>APPEARANCE<span style="opacity:0.4;"> ──</span></div>
  <div class="ap-sec">
    <div class="ap-lbl">THEME</div>
    <div class="ap-grp">
      <div class="ap-opt" onclick="setTheme('VT220')">
        <span class="ap-dot" id="d-VT220">▶</span>VT220
        <span class="ap-arrow" id="a-VT220">←</span>
      </div>
      <div class="ap-opt" onclick="setTheme('GREEN')">
        <span class="ap-dot" id="d-GREEN">○</span>Green Phosphor
        <span class="ap-arrow" id="a-GREEN" style="display:none;">←</span>
      </div>
      <div class="ap-opt" onclick="setTheme('CYAN')">
        <span class="ap-dot" id="d-CYAN">○</span>Cyan VDT
        <span class="ap-arrow" id="a-CYAN" style="display:none;">←</span>
      </div>
    </div>
  </div>
  <div class="ap-foot">↑↓ NAV · ↵ SEL · ESC</div>
</div>

<!-- PAGE -->
<div class="page">
  <div class="page-title">RSU TERMINAL</div>
  <div class="page-sub">Redistribution Strategy Unit.</div>

  <div class="loginbox">
    <div class="loginbox-head">LOGIN</div>
    <div class="loginbox-body">
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

var THEMES = {{
  VT220: {{bg:'#0a0800',bg2:'#130f00',bg3:'#1a1200',pri:'#ffb300',dim:'#7a5500',border:'#3d2900',mid:'#5a3e00',dark:'#1e1400'}},
  GREEN: {{bg:'#000d04',bg2:'#001508',bg3:'#001e0a',pri:'#00ffad',dim:'#008855',border:'#003820',mid:'#006640',dark:'#001810'}},
  CYAN:  {{bg:'#00080d',bg2:'#001018',bg3:'#001520',pri:'#00d9ff',dim:'#006680',border:'#002c38',mid:'#005566',dark:'#000c14'}}
}};

function applyThemeClass(k) {{
  document.getElementById('body').className = (k === 'VT220') ? '' : 't-' + k;
  document.getElementById('theme-label').textContent = k === 'GREEN' ? 'P3 GREEN' : k === 'CYAN' ? 'CYAN VDT' : 'VT220';
}}

function setTheme(k) {{
  currentTheme = k;
  applyThemeClass(k);
  ['VT220','GREEN','CYAN'].forEach(function(name) {{
    document.getElementById('d-' + name).textContent = (name === k) ? '▶' : '○';
    document.getElementById('a-' + name).style.display = (name === k) ? '' : 'none';
  }});
  toggleAppear();
  // Notify Streamlit to persist theme
  window.parent.postMessage({{type:'vt_theme', value:k}}, '*');
}}

function toggleAppear() {{
  panelOpen = !panelOpen;
  document.getElementById('appear').className = 'appear' + (panelOpen ? ' open' : '');
}}

function submitPassword() {{
  var pwd = document.getElementById('pwd').value;
  if (!pwd) return;
  window.parent.postMessage({{type:'vt_login', value:pwd}}, '*');
}}

document.addEventListener('keydown', function(e) {{
  if (e.key === 'Escape') {{
    panelOpen = false;
    document.getElementById('appear').className = 'appear';
  }}
  if (e.key === 'Enter') {{
    var inp = document.getElementById('pwd');
    if (document.activeElement === inp) submitPassword();
  }}
  if ((e.ctrlKey || e.metaKey) && e.key === 't') {{
    e.preventDefault(); toggleAppear();
  }}
}});

// Init
applyThemeClass(currentTheme);
document.getElementById('pwd').focus();
</script>
</body>
</html>"""


def login() -> bool:
    # ── INIT ──────────────────────────────────────────────────────────────────
    defaults = {
        "auth": False, "login_attempts": 0,
        "lockout_time": None, "last_activity": None,
        "vt_theme": "VT220",
        "vt_pwd_submitted": None,
        "vt_error": "",
        "vt_theme_pending": None,
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

    # ── HANDLE THEME CHANGE ───────────────────────────────────────────────────
    if st.session_state.get("vt_theme_pending"):
        st.session_state["vt_theme"] = st.session_state["vt_theme_pending"]
        st.session_state["vt_theme_pending"] = None

    # ── HANDLE PASSWORD SUBMIT ────────────────────────────────────────────────
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

    # ── RENDER HTML COMPONENT ─────────────────────────────────────────────────
    logo_b64 = get_logo_base64()
    error_msg = st.session_state.get("vt_error", "")
    attempts_left = 5 - st.session_state.get("login_attempts", 0)
    theme = st.session_state.get("vt_theme", "VT220")

    html_content = _build_html(logo_b64 or "", theme, error_msg, attempts_left)

    # Hide ALL Streamlit chrome first
    st.markdown("""
    <style>
    #MainMenu, footer, header { visibility: hidden !important; }
    .stApp { background: #0a0800 !important; }
    .main .block-container { padding: 0 !important; max-width: 100% !important; }
    section[data-testid="stMain"] > div { padding: 0 !important; }
    div[data-testid="stVerticalBlock"] {
        background: transparent !important; border: none !important;
        box-shadow: none !important; padding: 0 !important; gap: 0 !important;
    }
    iframe { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # Render the full HTML in an isolated iframe
    result = components.html(
        html_content,
        height=600,
        scrolling=False,
    )

    # ── RECEIVE MESSAGES FROM IFRAME VIA QUERY PARAMS ─────────────────────────
    # Streamlit components communicate via a bi-directional channel.
    # We use st.query_params as a fallback bridge for the password.
    # The HTML posts to parent; we handle it with a JS listener in the host page.
    st.markdown("""
    <script>
    window.addEventListener('message', function(e) {
        var d = e.data;
        if (!d || !d.type) return;
        if (d.type === 'vt_login') {
            // Store in sessionStorage, then trigger rerun via a hidden button
            window.sessionStorage.setItem('vt_pwd', d.value);
            var btn = document.getElementById('vt-submit-trigger');
            if (btn) btn.click();
        }
        if (d.type === 'vt_theme') {
            window.sessionStorage.setItem('vt_theme', d.value);
            var btn = document.getElementById('vt-theme-trigger');
            if (btn) btn.click();
        }
    }, false);
    </script>
    """, unsafe_allow_html=True)

    # Hidden submit button picked up by JS
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("__VT_SUBMIT__", key="vt_submit_btn"):
            pass  # handled above via session state
    with col2:
        if st.button("__VT_THEME__", key="vt_theme_btn"):
            pass

    st.markdown("""
    <script>
    (function() {
        // Wire up the hidden buttons with IDs
        var btns = document.querySelectorAll('button');
        btns.forEach(function(b) {
            if (b.innerText.trim() === '__VT_SUBMIT__') b.id = 'vt-submit-trigger';
            if (b.innerText.trim() === '__VT_THEME__')  b.id = 'vt-theme-trigger';
        });
        document.getElementById('vt-submit-trigger') &&
            document.getElementById('vt-submit-trigger').addEventListener('click', function() {
                var pwd = window.sessionStorage.getItem('vt_pwd');
                if (pwd) {
                    window.sessionStorage.removeItem('vt_pwd');
                    // Pass to Streamlit via URL param then reload
                    var url = new URL(window.location.href);
                    url.searchParams.set('_vt_pwd', btoa(pwd));
                    window.location.href = url.toString();
                }
            });
        document.getElementById('vt-theme-trigger') &&
            document.getElementById('vt-theme-trigger').addEventListener('click', function() {
                var t = window.sessionStorage.getItem('vt_theme');
                if (t) {
                    window.sessionStorage.removeItem('vt_theme');
                    var url = new URL(window.location.href);
                    url.searchParams.set('_vt_theme', t);
                    window.location.href = url.toString();
                }
            });
    })();
    </script>
    """, unsafe_allow_html=True)

    # ── READ QUERY PARAMS (password / theme submitted) ────────────────────────
    qp = st.query_params
    if "_vt_pwd" in qp:
        try:
            pwd_plain = base64.b64decode(qp["_vt_pwd"]).decode()
            st.session_state["vt_pwd_submitted"] = pwd_plain
        except Exception:
            pass
        # Clean URL
        st.query_params.clear()
        st.rerun()

    if "_vt_theme" in qp:
        theme_val = qp["_vt_theme"]
        if theme_val in ("VT220", "GREEN", "CYAN"):
            st.session_state["vt_theme"] = theme_val
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
