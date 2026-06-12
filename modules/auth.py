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

THEMES = {
    "VT220": dict(pri="#ffb300", bg="#0a0800", bg2="#130f00", bg3="#1a1200",
                  border="#3d2900", mid="#5a3e00", dim="#7a5500", dark="#1e1400",
                  crt="#0d0500", tint="rgba(180,60,0,0.12)"),
    "GREEN": dict(pri="#00ffad", bg="#000d04", bg2="#001508", bg3="#001e0a",
                  border="#003820", mid="#006640", dim="#008855", dark="#001810",
                  crt="#010d04", tint="rgba(0,180,80,0.10)"),
    "CYAN":  dict(pri="#00d9ff", bg="#00080d", bg2="#001018", bg3="#001520",
                  border="#002c38", mid="#005566", dim="#006680", dark="#000c14",
                  crt="#000d12", tint="rgba(0,130,180,0.10)"),
}


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
    for k, v in [("auth", False), ("login_attempts", 0), ("lockout_time", None),
                 ("last_activity", None), ("vt_theme", "VT220"), ("vt_error", "")]:
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
            st.session_state["vt_error"] = f"⛔ BLOQUEADO — {remaining} MIN"
        else:
            st.session_state["lockout_time"] = None
            st.session_state["login_attempts"] = 0
            st.session_state["vt_error"] = ""

    # ── THEME QUERY PARAM ──────────────────────────────────────────────────────
    qp = st.query_params
    if "_vt_theme" in qp:
        if qp["_vt_theme"] in THEMES:
            st.session_state["vt_theme"] = qp["_vt_theme"]
        st.query_params.clear()
        st.rerun()

    # ── THEME VARS ─────────────────────────────────────────────────────────────
    theme = st.session_state.get("vt_theme", "VT220")
    t     = THEMES[theme]
    pri   = t["pri"]; bg = t["bg"]; bg2 = t["bg2"]; bg3 = t["bg3"]
    border= t["border"]; mid = t["mid"]; dim = t["dim"]; dark = t["dark"]
    crt   = t["crt"]; tint = t["tint"]
    label = {"VT220": "VT220", "GREEN": "P3 GREEN", "CYAN": "CYAN VDT"}[theme]

    logo_b64  = get_logo_base64() or ""
    error_msg = st.session_state.get("vt_error", "")
    attempts_l = 5 - st.session_state.get("login_attempts", 0)
    fade_b64  = FADE_GIF_B64

    logo_img = ""
    if logo_b64:
        logo_img = (f'<img src="data:image/png;base64,{logo_b64}" '
                    f'style="display:block;width:96px;height:96px;border-radius:10px;'
                    f'margin:0 auto 18px;filter:drop-shadow(0 0 16px rgba(255,140,0,0.55));">')

    # theme dot helpers
    def dot(k): return "▶" if k == theme else "○"
    def dc(k):  return dim if k == theme else border
    def arr(k): return f'<span style="margin-left:auto;font-size:.6rem;color:{dim};">←</span>' if k == theme else ""

    # ── MENUBAR HTML (iframe, 31px) ────────────────────────────────────────────
    menubar_html = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:{bg};font-family:'Share Tech Mono',monospace;overflow:hidden;}}
.bar{{display:flex;justify-content:space-between;align-items:stretch;
      height:30px;width:100%;border-bottom:1px solid {border};background:{bg2};}}
.tabs{{display:flex;align-items:stretch;}}
.tab{{display:flex;align-items:center;padding:0 10px;color:{dim};
      border-right:1px solid {border};font-size:0.7rem;letter-spacing:1px;white-space:nowrap;}}
.tab .k{{color:{border};margin-right:3px;}}
.tab.active{{color:{pri};background:{bg};border-top:1px solid {mid};border-bottom:1px solid {mid};}}
.tab.active .k{{color:{dim};}}
.right{{display:flex;align-items:stretch;}}
.chip{{display:flex;align-items:center;padding:0 10px;border-left:1px solid {border};
       background:{bg2};color:{pri};cursor:pointer;font-size:0.7rem;letter-spacing:1px;white-space:nowrap;}}
.chip .k{{color:{dim};margin-right:3px;}}
.chip:hover{{background:{dark};}}
.chip.site{{background:{bg};cursor:default;}}
.chip.site:hover{{background:{bg};}}
.panel{{display:none;position:fixed;top:30px;right:0;z-index:9999;width:230px;
        background:{bg2};border:1px solid {mid};border-top:none;
        border-left:4px solid transparent;
        border-image:url("data:image/gif;base64,{fade_b64}") 8 repeat;}}
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
.ap-foot{{font-size:.6rem;color:{border};text-align:center;padding:7px 0;letter-spacing:1px;
          border-top:3px solid transparent;
          border-image:url("data:image/gif;base64,{fade_b64}") 8 repeat;}}
</style></head>
<body>
<div class="bar">
  <div class="tabs">
    <div class="tab active"><span class="k">^1</span>LOGIN</div>
    <div class="tab"><span class="k">^2</span>STATUS</div>
    <div class="tab"><span class="k">^3</span>INFO</div>
  </div>
  <div class="right">
    <div class="chip" onclick="tog()"><span class="k">^T</span>{label}</div>
    <div class="chip site">RSU TERMINAL</div>
  </div>
</div>
<div class="panel" id="p">
  <div class="ap-head">── APPEARANCE ──</div>
  <div class="ap-sec">
    <div class="ap-lbl">THEME</div>
    <div class="ap-grp">
      <div class="ap-opt" onclick="pick('VT220')"><span style="font-size:.65rem;width:12px;color:{dc('VT220')};">{dot('VT220')}</span>VT220{arr('VT220')}</div>
      <div class="ap-opt" onclick="pick('GREEN')"><span style="font-size:.65rem;width:12px;color:{dc('GREEN')};">{dot('GREEN')}</span>Green Phosphor{arr('GREEN')}</div>
      <div class="ap-opt" onclick="pick('CYAN')"><span style="font-size:.65rem;width:12px;color:{dc('CYAN')};">{dot('CYAN')}</span>Cyan VDT{arr('CYAN')}</div>
    </div>
  </div>
  <div class="ap-foot">↑↓ NAV · ↵ SEL · ESC</div>
</div>
<script>
var o=false;
function tog(){{o=!o;document.getElementById('p').className='panel'+(o?' open':'');}}
function pick(k){{
  var u=new URL(window.parent.location.href);
  u.searchParams.set('_vt_theme',k);
  window.parent.location.href=u.toString();
}}
document.addEventListener('keydown',function(e){{
  if(e.key==='Escape'){{o=false;document.getElementById('p').className='panel';}}
}});
</script>
</body></html>"""

    # ──────────────────────────────────────────────────────────────────────────
    # KEY INSIGHT: use a fixed-width column trick so Streamlit widgets
    # are constrained to the same width as the login box, then CSS
    # overlays the box visually on top with matching dimensions.
    # ──────────────────────────────────────────────────────────────────────────

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

    /* ── GLOBAL RESET ───────────────────────────────── */
    #MainMenu, footer, header {{ visibility: hidden !important; }}
    html, body, .stApp {{ background: {bg} !important; }}

    /* Full-page CRT effects */
    .stApp::before {{
        content:'';position:fixed;inset:0;pointer-events:none;z-index:9998;
        background:repeating-linear-gradient(to bottom,transparent 0,transparent 3px,rgba(0,0,0,0.20) 3px,rgba(0,0,0,0.20) 4px);
    }}
    .stApp::after {{
        content:'';position:fixed;inset:0;pointer-events:none;z-index:9997;
        background:radial-gradient(ellipse 95% 95% at 50% 50%,transparent 50%,rgba(0,0,0,0.65) 100%);
    }}

    /* ── STRIP ALL STREAMLIT CHROME ─────────────────── */
    .main .block-container {{
        padding: 0 !important;
        max-width: 100% !important;
        margin: 0 !important;
    }}
    section[data-testid="stMain"] > div {{ padding: 0 !important; }}
    div[data-testid="stVerticalBlock"] {{
        background: transparent !important; border: none !important;
        box-shadow: none !important; padding: 0 !important; gap: 0 !important;
    }}
    div[data-testid="stHorizontalBlock"] {{
        background: transparent !important; border: none !important;
        box-shadow: none !important; padding: 0 !important; gap: 0 !important;
    }}
    div[data-testid="column"] {{
        background: transparent !important; border: none !important;
        box-shadow: none !important; padding: 0 !important; gap: 0 !important;
    }}
    iframe {{ border: none !important; display: block !important; }}

    /* ── THE BOX SHELL ─────────────────────────────── */
    /* Top part of the box (logo, title, label) — pure HTML */
    .vt-box-top {{
        width: 80vw;
        max-width: 860px;
        margin: 24px auto 0;
        border: 1px solid {mid};
        border-bottom: none;
        background: {crt};
        position: relative;
        overflow: hidden;
    }}
    /* CRT noise inside box */
    .vt-box-top::before {{
        content:'';position:absolute;inset:0;pointer-events:none;z-index:2;mix-blend-mode:overlay;
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E");
        background-size:200px 200px;
    }}
    /* CRT scanlines inside box */
    .vt-box-top::after {{
        content:'';position:absolute;inset:0;pointer-events:none;z-index:3;
        background:repeating-linear-gradient(to bottom,transparent 0,transparent 2px,rgba(0,0,0,0.28) 2px,rgba(0,0,0,0.28) 4px);
    }}
    .vt-box-top-tint {{
        position:absolute;inset:0;pointer-events:none;z-index:4;
        background:radial-gradient(ellipse 80% 70% at 50% 40%,{tint} 0%,transparent 70%);
    }}
    @keyframes vt-flicker {{0%,100%{{opacity:1}}92%{{opacity:1}}93%{{opacity:.94}}94%{{opacity:1}}96%{{opacity:.97}}97%{{opacity:1}}}}
    .vt-box-top {{ animation: vt-flicker 8s infinite; }}
    .vt-box-top-inner {{ position:relative;z-index:10;padding:32px 56px 28px; }}

    .vt-login-head {{
        font-family:'Share Tech Mono',monospace;
        display:flex;align-items:center;justify-content:center;
        height:28px;font-size:0.7rem;letter-spacing:3px;
        border-bottom:1px solid {border};background:{bg2};
        position:relative;color:{pri};
    }}
    .vt-login-head::before{{content:'── ';color:{border};position:absolute;left:12px;}}
    .vt-login-head::after{{content:' ──';color:{border};position:absolute;right:12px;}}

    .vt-title {{
        font-family:'VT323',monospace !important;
        font-size:3.6rem !important; letter-spacing:12px !important;
        text-align:center !important; color:{pri} !important;
        text-transform:uppercase;
        text-shadow:0 0 20px rgba(255,140,0,0.65),0 0 6px rgba(255,200,0,0.4);
        line-height:1; margin-bottom:4px;
    }}
    .vt-sub {{
        font-family:'Share Tech Mono',monospace;
        font-size:0.65rem;letter-spacing:5px;text-align:center;
        color:{dim};text-transform:uppercase;margin-bottom:32px;
    }}

    /* ── FIELD LABEL BAND ──────────────────────────── */
    /* Sits between box-top and the native input */
    .vt-field-shell {{
        width: 80vw;
        max-width: 860px;
        margin: 0 auto;
        border-left: 1px solid {mid};
        border-right: 1px solid {mid};
        background: {crt};
    }}
    .vt-field-label {{
        font-family:'Share Tech Mono',monospace;
        font-size:0.75rem; color:{pri}; letter-spacing:3px;
        text-transform:uppercase; padding:7px 56px 6px;
        background:rgba(20,12,0,0.9);
        border-top:1px solid {border};
        border-bottom:1px solid {border};
        display:block;
    }}

    /* ── NATIVE INPUT — constrained to box width ───── */
    /* Target the column that wraps the input */
    .vt-input-col {{
        width: 80vw !important;
        max-width: 860px !important;
        margin: 0 auto !important;
    }}
    .vt-input-col .stTextInput > label {{ display: none !important; }}
    .vt-input-col .stTextInput > div {{
        border: none !important; box-shadow: none !important;
        background: transparent !important; padding: 0 !important;
    }}
    .vt-input-col .stTextInput > div > div {{
        border: none !important; box-shadow: none !important; background: transparent !important;
    }}
    .vt-input-col .stTextInput > div > div > input {{
        background: rgba(6,4,0,0.97) !important;
        border: none !important;
        border-left: 1px solid {mid} !important;
        border-right: 1px solid {mid} !important;
        border-bottom: 1px solid {mid} !important;
        border-radius: 0 !important;
        color: {pri} !important;
        height: 46px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 1rem !important;
        letter-spacing: 3px !important;
        padding: 0 56px !important;
        caret-color: {pri} !important;
        box-shadow: none !important;
        width: 100% !important;
    }}
    .vt-input-col .stTextInput > div > div > input::placeholder {{
        color: {dim} !important; font-style:italic; letter-spacing:2px; font-size:0.9rem !important;
    }}
    .vt-input-col .stTextInput > div > div > input:focus {{
        border-color: {pri} !important;
        box-shadow: none !important; outline: none !important;
    }}
    .vt-input-col .stTextInput [data-testid="stIcon"] {{ display: none !important; }}

    /* ── NATIVE BUTTON — constrained to box width ──── */
    .vt-btn-col {{
        width: 80vw !important;
        max-width: 860px !important;
        margin: 0 auto !important;
    }}
    .vt-btn-col div[data-testid="stButton"] {{ width: 100% !important; margin: 0 !important; }}
    .vt-btn-col div[data-testid="stButton"] > button {{
        font-family: 'Share Tech Mono', monospace !important;
        background: {pri} !important;
        color: {bg} !important;
        border: none !important;
        border-radius: 0 !important;
        font-size: 0.9rem !important;
        letter-spacing: 6px !important;
        width: 100% !important;
        height: 48px !important;
        padding: 0 !important;
        text-transform: uppercase !important;
        margin: 0 !important;
        box-shadow: none !important;
        background-image: repeating-linear-gradient(to bottom,transparent 0,transparent 2px,rgba(0,0,0,0.08) 2px,rgba(0,0,0,0.08) 4px) !important;
        transition: opacity 0.15s !important;
    }}
    .vt-btn-col div[data-testid="stButton"] > button:hover {{ opacity: 0.88 !important; }}

    /* ── BOX BOTTOM ────────────────────────────────── */
    .vt-box-bottom {{
        width: 80vw;
        max-width: 860px;
        margin: 0 auto 40px;
        border: 1px solid {mid};
        border-top: none;
        background: {bg};
    }}
    .vt-status {{
        font-family:'Share Tech Mono',monospace;
        font-size:0.58rem;color:{border};text-align:center;
        letter-spacing:2px;text-transform:uppercase;padding:10px 0 6px;
    }}
    .vt-footer {{
        font-family:'Share Tech Mono',monospace;
        font-size:0.55rem;color:{border};text-align:center;
        letter-spacing:1px;padding:6px 18px 10px;
        border-top:1px solid {border};text-transform:uppercase;
    }}
    @keyframes vt-blink {{0%,100%{{opacity:1}}50%{{opacity:0}}}}
    .vt-dot {{
        display:inline-block;width:5px;height:5px;border-radius:50%;
        background:{pri};vertical-align:middle;margin-right:5px;
        animation:vt-blink 1.1s step-end infinite;
    }}

    /* Alerts inside box */
    .vt-alert-col {{
        width: 80vw !important;
        max-width: 860px !important;
        margin: 0 auto !important;
    }}
    .vt-alert-col .stAlert {{
        font-family:'Share Tech Mono',monospace !important;
        font-size:0.75rem !important; border-radius:0 !important;
        margin:0 !important;
        border-left:2px solid {pri} !important;
        background:{bg2} !important;
        border-right: 1px solid {mid} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── MENUBAR ────────────────────────────────────────────────────────────────
    components.html(menubar_html, height=31, scrolling=False)

    # ── BOX TOP: header + logo + title (pure HTML) ─────────────────────────────
    st.markdown(f"""
    <div class="vt-box-top">
      <div class="vt-box-top-tint"></div>
      <div class="vt-login-head">LOGIN</div>
      <div class="vt-box-top-inner">
        {logo_img}
        <div class="vt-title">RSU TERMINAL</div>
        <div class="vt-sub">Redistribution Strategy Unit</div>
      </div>
    </div>
    <div class="vt-field-shell">
      <span class="vt-field-label">PASSWORD</span>
    </div>
    """, unsafe_allow_html=True)

    # ── NATIVE INPUT (inside vt-input-col) ────────────────────────────────────
    _, col_input, _ = st.columns([1, 8, 1])  # rough centering fallback
    with col_input:
        st.markdown('<div class="vt-input-col">', unsafe_allow_html=True)
        password = st.text_input(
            "pwd", type="password",
            placeholder="Enter your password",
            label_visibility="collapsed",
            key="vt_password_input",
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── ALERTS ────────────────────────────────────────────────────────────────
    if error_msg or (0 < attempts_l <= 2):
        _, col_alert, _ = st.columns([1, 8, 1])
        with col_alert:
            st.markdown('<div class="vt-alert-col">', unsafe_allow_html=True)
            if error_msg:
                st.error(error_msg)
            elif 0 < attempts_l <= 2:
                st.warning(f"⚠ {attempts_l} INTENTOS RESTANTES")
            st.markdown('</div>', unsafe_allow_html=True)

    # ── SIGN IN BUTTON ────────────────────────────────────────────────────────
    _, col_btn, _ = st.columns([1, 8, 1])
    with col_btn:
        st.markdown('<div class="vt-btn-col">', unsafe_allow_html=True)
        sign_in = st.button("SIGN IN", key="vt_signin_btn", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── BOX BOTTOM: status + footer ───────────────────────────────────────────
    st.markdown(f"""
    <div class="vt-box-bottom">
      <div class="vt-status"><span class="vt-dot"></span>SECURE CONNECTION · AES-256 · TLS 1.3</div>
      <div class="vt-footer">🔒 SSL ENCRYPTED · © 2026 RSU TERMINAL v2.0 // STATUS: ACTIVE</div>
    </div>
    """, unsafe_allow_html=True)

    # ── ENTER KEY ─────────────────────────────────────────────────────────────
    st.markdown("""
    <script>
    setTimeout(function(){
      var inp = document.querySelector('input[type="password"]');
      if(!inp) return;
      inp.addEventListener('keydown', function(e){
        if(e.key==='Enter'){
          var btns = document.querySelectorAll('button');
          for(var i=0;i<btns.length;i++){
            if(btns[i].innerText.trim()==='SIGN IN'){btns[i].click();return;}
          }
        }
      });
    }, 400);
    </script>
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
