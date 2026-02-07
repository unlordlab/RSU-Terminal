# modules/rsu_club.py
import streamlit as st
from pathlib import Path

def get_logo_path():
    possible_paths = [
        "rsu_logo.png",
        "assets/rsu_logo.png", 
        "static/rsu_logo.png",
        "/mnt/kimi/upload/rsu_logo.png"
    ]
    for path in possible_paths:
        if Path(path).exists():
            return path
    return None

def render():
    # CSS mínimo necesario
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            padding: 30px;
            background: linear-gradient(180deg, #0c0e12 0%, #11141a 100%);
            border: 1px solid #1a1e26;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .main-title {
            font-size: 2rem;
            font-weight: bold;
            color: #00ffad;
            margin-top: 15px;
            text-shadow: 0 0 20px rgba(0, 255, 173, 0.3);
        }
        .section-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            padding: 20px;
            height: 100%;
        }
        .section-header {
            background: #0c0e12;
            margin: -20px -20px 20px -20px;
            padding: 15px 20px;
            border-bottom: 1px solid #1a1e26;
            border-radius: 10px 10px 0 0;
            font-weight: bold;
            color: white;
            font-size: 1.1rem;
        }
        .highlight {
            color: #00ffad;
            font-weight: bold;
            border-left: 3px solid #00ffad;
            padding-left: 12px;
            display: block;
            margin: 15px 0;
            font-size: 1.1rem;
        }
        .feature-item {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
        }
        .feature-title {
            color: white;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .feature-desc {
            color: #888;
            font-size: 0.9rem;
        }
        .tip-box {
            background: #00ffad11;
            border-left: 3px solid #00ffad;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }
        .signature {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #1a1e26;
            color: #888;
            font-style: italic;
        }
    </style>
    """, unsafe_allow_html=True)

    # HEADER
    logo_path = get_logo_path()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if logo_path:
            st.image(logo_path, width=150)
        st.markdown('<div class="main-title">♣️ RSU Elite Club</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # DOS COLUMNAS PRINCIPALES
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("""
        <div class="section-card">
            <div class="section-header">🎯 Nuestra Filosofía</div>
            <span class="highlight">Más que un club, una comunidad.</span>
            <p style="color: #ccc; line-height: 1.6; margin-bottom: 15px;">
                En el ecosistema del trading, encontrar un espacio transparente es un verdadero desafío. Entre "gurús" que prometen riqueza inmediata y cursos costosos de nula eficacia, es normal sentirse perdido.
            </p>
            <p style="color: #ccc; line-height: 1.6; margin-bottom: 15px;">
                En <strong style="color: #00ffad;">RSU Club</strong> marcamos la distancia: aquí no hay promesas vacías, solo <strong>conocimiento real, colaboración y responsabilidad</strong>.
            </p>
            <p style="color: #ccc; line-height: 1.6;">
                Somos una comunidad de trading diseñada para ser <strong>seria, responsable y rentable</strong>. Te dotamos de las herramientas y el respaldo necesarios para que tus decisiones de inversión estén fundamentadas y cuenten con garantías.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🛠️ ¿Qué te ofrecemos?</div>', unsafe_allow_html=True)
        
        features = [
            ("📊", "Análisis profundo y actualizado", "Seguimiento diario del sentimiento del mercado, tesis de compra exhaustivas e ideas operativas de alto interés."),
            ("🎓", "Estrategias y Formación", "Metodologías únicas adaptadas a diversos perfiles de riesgo. Base de datos de 'operaciones inusuales' y biblioteca exclusiva."),
            ("💎", "Recursos Exclusivos", "Listado actualizado de activos para carteras de medio/largo plazo e información de 'segundo nivel'."),
            ("🤝", "Soporte Personalizado", "Asesoramiento individual en configuración de herramientas (TradingView, brókers) para un entorno operativo óptimo.")
        ]
        
        for icon, title, desc in features:
            st.markdown(f"""
            <div class="feature-item">
                <div style="font-size: 1.5rem; margin-bottom: 5px;">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # SECCIÓN FINAL
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="section-card">
        <div class="section-header">🚀 Tu camino empieza aquí</div>
        <p style="color: #ccc; line-height: 1.6; margin-bottom: 15px;">
            Te invito a explorar la comunidad, participar en los debates y consultar cualquier duda. Si necesitas algo específico, puedes contactarme por <strong style="color: #00ffad;">mensaje directo (MD)</strong>; te responderé lo antes posible.
        </p>
        <div class="tip-box">
            💡 <strong>Consejo:</strong> No te abrumes por el volumen de información. Tómalo con calma, a tu ritmo; poco a poco integrarás los conocimientos necesarios para operar con confianza.
        </div>
        <p style="color: #ccc; line-height: 1.6; margin-bottom: 15px;">
            Gracias por formar parte de un espacio donde la <strong>formación, la responsabilidad y la transparencia</strong> son la prioridad. Deja atrás el ruido de los falsos gurús y comienza tu camino hacia un <strong style="color: #00ffad;">trading consciente</strong>.
        </p>
        <div class="signature">
            <strong style="color: #00ffad; font-style: normal;">unlord</strong> | RSU Club ♣️
        </div>
    </div>
    """, unsafe_allow_html=True)
