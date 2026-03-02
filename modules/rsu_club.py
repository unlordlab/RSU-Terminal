
# modules/rsu_club.py
import streamlit as st
from pathlib import Path
import base64

def get_logo_path():
    possible_paths = [
        "/mnt/kimi/upload/logo.png",
        "logo.png",
        "assets/logo.png", 
        "static/logo.png"
    ]
    for path in possible_paths:
        if Path(path).exists():
            return path
    return None

def render():
    # CSS \u2014 Terminal hacker aesthetic (aligned with roadmap_2026)
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp {
            background: #0c0e12;
        }

        /* VT323 headings */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            color: #00ffad !important;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        /* Body text */
        p, li {
            font-family: 'Courier New', monospace;
            color: #ccc !important;
            line-height: 1.8;
            font-size: 0.95rem;
        }

        strong {
            color: #00ffad;
            font-weight: bold;
        }

        /* Main title */
        .main-title {
            font-family: 'VT323', monospace;
            font-size: 3.5rem;
            font-weight: normal;
            color: #00ffad;
            text-shadow: 0 0 30px rgba(0, 255, 173, 0.5);
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 4px;
            margin-top: 10px;
        }

        /* Cards */
        .rsu-card {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #00ffad44;
            border-radius: 8px;
            overflow: hidden;
            height: 100%;
            box-shadow: 0 0 15px #00ffad11;
        }

        .rsu-header {
            background: #0c0e12;
            padding: 16px 20px;
            border-bottom: 1px solid #00ffad33;
            font-family: 'VT323', monospace;
            font-weight: normal;
            color: #00ffad;
            font-size: 1.4rem;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .rsu-body {
            padding: 20px;
        }

        /* Highlight box */
        .highlight-box {
            background: #00ffad11;
            border: 1px solid #00ffad33;
            border-radius: 8px;
            padding: 15px 18px;
            margin: 15px 0;
            font-family: 'VT323', monospace;
            font-size: 1.2rem;
            color: #00ffad;
            text-align: center;
        }

        .highlight-text {
            color: #00ffad;
            font-family: 'VT323', monospace;
            font-size: 1.2rem;
            letter-spacing: 1px;
        }

        /* Feature boxes */
        .feature-box {
            background: #0c0e12;
            border: 1px solid #2a3f5f;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
        }

        .feature-title {
            font-family: 'VT323', monospace;
            color: #00ffad;
            font-size: 1.2rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 8px 0 5px 0;
        }

        .feature-desc {
            color: #888 !important;
            font-size: 0.9rem;
        }

        /* Tip box */
        .tip-box {
            background: #0c0e12;
            border-left: 3px solid #00ffad;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }

        /* Signature */
        .signature {
            text-align: center;
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid #1a1e26;
            font-family: 'VT323', monospace;
            color: #666;
            font-size: 1.1rem;
            letter-spacing: 2px;
        }

        /* Terminal status bar */
        .status-bar {
            font-family: 'VT323', monospace;
            font-size: 1rem;
            color: #666;
            text-align: center;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }

        /* Horizontal rule */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad, transparent);
            margin: 30px 0;
        }

        /* List styling */
        ul {
            list-style: none;
            padding-left: 0;
        }

        ul li::before {
            content: "\u25b8 ";
            color: #00ffad;
            font-weight: bold;
            margin-right: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    # \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    # HEADER
    # \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    logo_path = get_logo_path()

    left_spacer, center_col, right_spacer = st.columns([1, 2, 1])

    with center_col:
        st.markdown("""
        <div class="status-bar">[SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]</div>
        """, unsafe_allow_html=True)

        if logo_path:
            with open(logo_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode()

            st.markdown(f"""
            <div style="position: relative; display: flex; justify-content: center; align-items: center; height: 320px;">
                <div style="position: absolute; width: 350px; height: 350px; background: radial-gradient(circle, rgba(0,255,173,0.3) 0%, transparent 70%); filter: blur(30px); top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 0;"></div>
                <img src="data:image/png;base64,{img_base64}" width="260" style="position: relative; z-index: 1;">
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="position: relative; display: flex; justify-content: center; align-items: center; height: 320px;">
                <div style="position: absolute; width: 350px; height: 350px; background: radial-gradient(circle, rgba(0,255,173,0.3) 0%, transparent 70%); filter: blur(30px); top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 0;"></div>
                <div style="position: relative; z-index: 1; font-size: 6rem;">\u2663\ufe0f</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="main-title">RSU Club</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family: 'VT323', monospace; color: #00d9ff; font-size: 1.1rem; letter-spacing: 3px; text-align: center; margin-top: 8px;">
            COMUNIDAD DE TRADING // SERIA \u00b7 RESPONSABLE \u00b7 RENTABLE
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    # COLUMNAS PRINCIPALES
    # \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="rsu-card">
            <div class="rsu-header">\ud83c\udfaf Nuestra Filosof\u00eda</div>
            <div class="rsu-body">
                <div class="highlight-box">
                    <span class="highlight-text">M\u00e1s que un club, una comunidad.</span>
                </div>
                <p>En el ecosistema del trading, encontrar un espacio transparente es un verdadero desaf\u00edo. Entre "gur\u00fas" que prometen riqueza inmediata y cursos costosos de nula eficacia, es normal sentirse perdido.</p>
                <p>En <strong>RSU Club</strong> marcamos la distancia: aqu\u00ed no hay promesas vac\u00edas, solo <strong>conocimiento real, colaboraci\u00f3n y responsabilidad</strong>.</p>
                <p>Somos una comunidad de trading dise\u00f1ada para ser <strong>seria, responsable y rentable</strong>. Te dotamos de las herramientas y el respaldo necesarios para que tus decisiones de inversi\u00f3n est\u00e9n fundamentadas y cuenten con garant\u00edas.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        features = [
            ("\ud83d\udcca", "An\u00e1lisis profundo y actualizado", "Seguimiento diario del sentimiento del mercado, tesis de compra exhaustivas e ideas operativas de alto inter\u00e9s."),
            ("\ud83c\udf93", "Estrategias y Formaci\u00f3n", "Metodolog\u00edas \u00fanicas adaptadas a diversos perfiles de riesgo. Base de datos
