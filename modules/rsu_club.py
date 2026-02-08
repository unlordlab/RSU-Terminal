
# modules/rsu_club.py
import streamlit as st
from pathlib import Path

def get_logo_path():
    """Encuentra la ruta del logo"""
    possible_paths = [
        "/mnt/kimi/upload/rsu_logo.png",
        "rsu_logo.png",
        "assets/rsu_logo.png", 
        "static/rsu_logo.png"
    ]
    for path in possible_paths:
        if Path(path).exists():
            return path
    return None

def render():
    # CSS
    st.markdown("""
    <style>
        .header-section {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(180deg, #0c0e12 0%, #11141a 100%);
            border: 1px solid #1a1e26;
            border-radius: 16px;
            margin-bottom: 30px;
        }
        .main-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #00ffad;
            margin-top: 20px;
            text-shadow: 0 0 30px rgba(0, 255, 173, 0.4);
        }
        .rsu-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            overflow: hidden;
        }
        .rsu-header {
            background: #0c0e12;
            padding: 16px 20px;
            border-bottom: 1px solid #1a1e26;
            font-weight: bold;
            color: white;
            font-size: 1.1rem;
        }
        .rsu-body {
            padding: 20px;
        }
        .highlight-box {
            background: linear-gradient(90deg, #00ffad22 0%, transparent 100%);
            border-left: 3px solid #00ffad;
            padding: 12px 15px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }
        .highlight-text {
            color: #00ffad;
            font-weight: bold;
            font-size: 1.1rem;
        }
        .feature-box {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }
        .feature-title {
            color: white;
            font-weight: bold;
            margin: 8px 0 5px 0;
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
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid #1a1e26;
            color: #666;
        }
        p {
            color: #bbb;
            line-height: 1.7;
            margin-bottom: 12px;
        }
    </style>
    """, unsafe_allow_html=True)

    # HEADER CON LOGO NATIVO (MÁS RÁPIDO)
    logo_path = get_logo_path()
    
    st.markdown('<div class="header-section">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if logo_path:
            # st.image es más rápido que base64 embebido
            st.image(logo_path, width=280, use_container_width=False)
        else:
            st.markdown('<div style="font-size: 6rem; text-align: center;">♣️</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="main-title">RSU Elite Club</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # COLUMNAS
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
                <p>En <strong style="color: #00ffad;">RSU Club</strong> marcamos la distancia: aquí no hay promesas vacías, solo <strong>conocimiento real, colaboración y responsabilidad</strong>.</p>
                <p>Somos una comunidad de trading diseñada para ser <strong>seria, responsable y rentable</strong>. Te dotamos de las herramientas y el respaldo necesarios para que tus decisiones de inversión estén fundamentadas y cuenten con garantías.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="rsu-card">
            <div class="rsu-header">🛠️ ¿Qué te ofrecemos?</div>
            <div class="rsu-body">
        """, unsafe_allow_html=True)
        
        features = [
            ("📊", "Análisis profundo y actualizado", "Seguimiento diario del sentimiento del mercado, tesis de compra exhaustivas e ideas operativas de alto interés."),
            ("🎓", "Estrategias y Formación", "Metodologías únicas adaptadas a diversos perfiles de riesgo. Base de datos de 'operaciones inusuales' y biblioteca exclusiva."),
            ("💎", "Recursos Exclusivos", "Listado actualizado de activos para carteras de medio/largo plazo e información de 'segundo nivel'."),
            ("🤝", "Soporte Personalizado", "Asesoramiento individual en configuración de herramientas (TradingView, brókers) para un entorno operativo óptimo.")
        ]
        
        for icon, title, desc in features:
            st.markdown(f"""
            <div class="feature-box">
                <div style="font-size: 1.5rem;">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

    # SECCIÓN FINAL
    st.write("")
    st.markdown("""
    <div class="rsu-card">
        <div class="rsu-header">🚀 Tu camino empieza aquí</div>
        <div class="rsu-body">
            <p>Te invito a explorar la comunidad, participar en los debates y consultar cualquier duda. Si necesitas algo específico, puedes contactarme por <strong style="color: #00ffad;">mensaje directo (MD)</strong>; te responderé lo antes posible.</p>
            <div class="tip-box">
                💡 <strong>Consejo:</strong> No te abrumes por el volumen de información. Tómalo con calma, a tu ritmo; poco a poco integrarás los conocimientos necesarios para operar con confianza.
            </div>
            <p>Gracias por formar parte de un espacio donde la <strong>formación, la responsabilidad y la transparencia</strong> son la prioridad. Deja atrás el ruido de los falsos gurús y comienza tu camino hacia un <strong style="color: #00ffad;">trading consciente</strong>.</p>
            <div class="signature">
                <strong style="color: #00ffad;">unlord</strong> | RSU Club ♣️
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


