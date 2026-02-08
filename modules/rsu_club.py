# modules/rsu_club.py
import streamlit as st
from pathlib import Path

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
    # CSS actualizado
    st.markdown("""
    <style>
        .header-container {
            background: linear-gradient(180deg, #0c0e12 0%, #11141a 100%);
            border: 1px solid #1a1e26;
            border-radius: 16px;
            padding: 40px 20px;
            margin-bottom: 30px;
            text-align: center;
        }
        .logo-wrapper {
            position: relative;
            display: inline-block;
            margin: 0 auto 20px auto;
        }
        .logo-glow {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 320px;
            height: 320px;
            background: radial-gradient(circle, rgba(0,255,173,0.28) 0%, rgba(0,255,173,0.06) 60%, transparent 80%);
            filter: blur(35px);
            z-index: 0;
            pointer-events: none;
            border-radius: 50%;
        }
        .logo-circle {
            width: 260px;
            height: 260px;
            border-radius: 50%;
            overflow: hidden;
            border: 2px solid #00ffad33;
            box-shadow: 0 0 30px rgba(0,255,173,0.35);
            position: relative;
            z-index: 1;
            background: #0c0e12;
        }
        .logo-circle img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .main-title {
            font-size: 2.8rem;
            font-weight: 800;
            color: #00ffad;
            text-shadow: 0 0 35px rgba(0, 255, 173, 0.45);
            margin: 10px 0 0 0;
            letter-spacing: 1px;
        }
        .rsu-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 24px;
        }
        .rsu-header {
            background: #0c0e12;
            padding: 16px 20px;
            border-bottom: 1px solid #1a1e26;
            font-weight: bold;
            color: white;
            font-size: 1.15rem;
        }
        .rsu-body {
            padding: 20px;
        }
        .highlight-box {
            background: linear-gradient(90deg, #00ffad22 0%, transparent 100%);
            border-left: 4px solid #00ffad;
            padding: 14px 16px;
            margin: 16px 0;
            border-radius: 0 10px 10px 0;
        }
        .highlight-text {
            color: #00ffad;
            font-weight: bold;
            font-size: 1.15rem;
        }
        .feature-box {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 14px;
            display: flex;
            gap: 14px;
            align-items: flex-start;
        }
        .feature-icon {
            font-size: 1.8rem;
            line-height: 1;
            min-width: 40px;
        }
        .feature-content {
            flex: 1;
        }
        .feature-title {
            color: white;
            font-weight: 600;
            margin: 0 0 6px 0;
        }
        .feature-desc {
            color: #aaa;
            font-size: 0.95rem;
            line-height: 1.5;
        }
        .tip-box {
            background: #00ffad0f;
            border-left: 4px solid #00ffad;
            padding: 16px;
            margin: 24px 0;
            border-radius: 0 10px 10px 0;
            font-size: 0.98rem;
        }
        .signature {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #1a1e26;
            color: #777;
            font-size: 0.95rem;
        }
        p {
            color: #ccc;
            line-height: 1.75;
            margin-bottom: 14px;
        }
    </style>
    """, unsafe_allow_html=True)

    # HEADER
    logo_path = get_logo_path()

    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    
    # Logo circular + glow
    st.markdown('<div class="logo-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="logo-glow"></div>', unsafe_allow_html=True)
    
    if logo_path:
        st.markdown(f"""
        <div class="logo-circle">
            <img src="{logo_path}" alt="RSU Logo">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="logo-circle" style="display:flex; align-items:center; justify-content:center; font-size:8rem; color:#00ffad44;">
            ♣
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="main-title">RSU Elite Club</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # COLUMNAS con las dos tarjetas principales
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
                <div class="feature-icon">{icon}</div>
                <div class="feature-content">
                    <div class="feature-title">{title}</div>
                    <div class="feature-desc">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

    # SECCIÓN FINAL
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



