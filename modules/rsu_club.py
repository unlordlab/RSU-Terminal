
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
    # CSS — Terminal hacker aesthetic (aligned with roadmap_2026)
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
            content: "▸ ";
            color: #00ffad;
            font-weight: bold;
            margin-right: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    # ──────────────────────────────────────────────
    # HEADER
    # ──────────────────────────────────────────────
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
                <div style="position: relative; z-index: 1; font-size: 6rem;">♣️</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="main-title">RSU Club</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family: 'VT323', monospace; color: #00d9ff; font-size: 1.1rem; letter-spacing: 3px; text-align: center; margin-top: 8px;">
            COMUNIDAD DE TRADING // SERIA · RESPONSABLE · RENTABLE
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ──────────────────────────────────────────────
    # COLUMNAS PRINCIPALES
    # ──────────────────────────────────────────────
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="rsu-card">
            <div class="rsu-header">🎯 Nuestra Filosofía</div>
            <div class="rsu-body">
                <div class="highlight-box">
                    <span class="highlight-text">Más que un club, una comunidad.</span>
                </div>
                <p>En el ecosistema del trading, encontrar un espacio transparente es un verdadero desafío. Entre "gurús" que prometen riqueza inmediata y cursos costosos de nula eficacia, es normal sentirse perdido.</p>
                <p>En <strong>RSU Club</strong> marcamos la distancia: aquí no hay promesas vacías, solo <strong>conocimiento real, colaboración y responsabilidad</strong>.</p>
                <p>Somos una comunidad de trading diseñada para ser <strong>seria, responsable y rentable</strong>. Te dotamos de las herramientas y el respaldo necesarios para que tus decisiones de inversión estén fundamentadas y cuenten con garantías.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        features = [
            ("📊", "Análisis profundo y actualizado", "Seguimiento diario del sentimiento del mercado, tesis de compra exhaustivas e ideas operativas de alto interés."),
            ("🎓", "Estrategias y Formación", "Metodologías únicas adaptadas a diversos perfiles de riesgo. Base de datos de 'operaciones inusuales' y biblioteca exclusiva."),
            ("💎", "Recursos Exclusivos", "Listado actualizado de activos para carteras de medio/largo plazo e información de 'segundo nivel'."),
            ("🤝", "Soporte Personalizado", "Asesoramiento individual en configuración de herramientas (TradingView, brókers) para un entorno operativo óptimo.")
        ]

        features_html = ""
        for icon, title, desc in features:
            features_html += '<div class="feature-box">'
            features_html += f'<div style="font-size: 1.5rem;">{icon}</div>'
            features_html += f'<div class="feature-title">{title}</div>'
            features_html += f'<div class="feature-desc">{desc}</div>'
            features_html += '</div>'

        card_html = '<div class="rsu-card">'
        card_html += '<div class="rsu-header">🛠️ ¿Qué te ofrecemos?</div>'
        card_html += '<div class="rsu-body">'
        card_html += features_html
        card_html += '</div></div>'

        st.markdown(card_html, unsafe_allow_html=True)

    # ──────────────────────────────────────────────
    # SECCIÓN FINAL
    # ──────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("""
    <div class="rsu-card">
        <div class="rsu-header">🚀 Tu camino empieza aquí</div>
        <div class="rsu-body">
            <p>Te invito a explorar la comunidad, participar en los debates y consultar cualquier duda. Si necesitas algo específico, puedes contactarme por <strong>mensaje directo (MD)</strong>; te responderé lo antes posible.</p>
            <div class="tip-box">
                💡 <strong>Consejo:</strong> No te abrumes por el volumen de información. Tómalo con calma, a tu ritmo; poco a poco integrarás los conocimientos necesarios para operar con confianza.
            </div>
            <p>Gracias por formar parte de un espacio donde la <strong>formación, la responsabilidad y la transparencia</strong> son la prioridad. Deja atrás el ruido de los falsos gurús y comienza tu camino hacia un <strong>trading consciente</strong>.</p>
            <div class="signature">
                <strong style="color: #00ffad; font-size: 1.3rem;">unlord</strong> | RSU Club ♣️<br>
                <span style="color: #444; font-size: 0.85rem;">[END OF TRANSMISSION // RSU_CLUB_v2.0]</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
