# modules/rsu_club.py
import streamlit as st
import base64
from pathlib import Path

def get_logo_path():
    """Encuentra la ruta del logo"""
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
    # CSS global
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 0rem;
        }
        .rsu-header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(180deg, #0c0e12 0%, #11141a 100%);
            border: 1px solid #1a1e26;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .rsu-title {
            font-size: 1.8rem;
            font-weight: bold;
            color: #00ffad;
            margin: 10px 0;
            text-shadow: 0 0 20px rgba(0, 255, 173, 0.3);
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #00ffad22;
            color: #00ffad;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            border: 1px solid #00ffad44;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            background: #00ffad;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .rsu-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            height: 100%;
        }
        .rsu-card-header {
            background: #0c0e12;
            padding: 12px 15px;
            border-bottom: 1px solid #1a1e26;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
        }
        .rsu-card-title {
            margin: 0;
            color: white;
            font-size: 14px;
            font-weight: bold;
        }
        .rsu-card-content {
            padding: 20px;
            background: #11141a;
        }
        .tooltip-icon {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: #1a1e26;
            border: 2px solid #555;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 14px;
            cursor: help;
            position: relative;
        }
        .tooltip-icon:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            top: 35px;
            right: -10px;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 12px;
            border: 1px solid #444;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            z-index: 1000;
            white-space: normal;
        }
        .highlight-text {
            color: #00ffad;
            font-size: 1.1rem;
            font-weight: bold;
            border-left: 3px solid #00ffad;
            padding-left: 12px;
            margin: 15px 0;
            display: block;
        }
        .feature-box {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }
        .feature-box:hover {
            border-color: #00ffad44;
            transform: translateY(-2px);
        }
        .feature-title {
            color: white;
            font-weight: bold;
            font-size: 0.95rem;
            margin: 8px 0 5px 0;
        }
        .feature-desc {
            color: #888;
            font-size: 0.85rem;
            line-height: 1.4;
        }
        .tip-box {
            background: linear-gradient(135deg, #00ffad11 0%, #00ffad05 100%);
            border-left: 3px solid #00ffad;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }
        .signature-box {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #1a1e26;
            text-align: center;
            color: #888;
            font-style: italic;
        }
    </style>
    """, unsafe_allow_html=True)

    # HEADER CON LOGO - Usando st.image nativo
    logo_path = get_logo_path()
    
    header_col1, header_col2, header_col3 = st.columns([1, 2, 1])
    with header_col2:
        if logo_path:
            st.image(logo_path, width=120, use_container_width=False)
        st.markdown('<div class="rsu-title">♣️ RSU Elite Club</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-top: 10px;">
            <div class="status-badge">
                <div class="status-dot"></div>
                <span>Estado de suscripción: ACTIVO (Elite Member)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # CONTENIDO EN DOS COLUMNAS
    col1, col2 = st.columns(2)

    with col1:
        # NUESTRA FILOSOFÍA
        st.markdown("""
        <div class="rsu-card" style="height: 580px;">
            <div class="rsu-card-header">
                <div class="rsu-card-title">🎯 Nuestra Filosofía</div>
                <div class="tooltip-icon" data-tooltip="El núcleo de valores que define a nuestra comunidad de trading.">?</div>
            </div>
            <div class="rsu-card-content" style="height: calc(580px - 50px); overflow-y: auto;">
                <span class="highlight-text">Más que un club, una comunidad.</span>
                <p style="color: #ccc; line-height: 1.6; font-size: 0.9rem; text-align: justify; margin-bottom: 15px;">
                    En el ecosistema del trading, encontrar un espacio transparente es un verdadero desafío. Entre "gurús" que prometen riqueza inmediata y cursos costosos de nula eficacia, es normal sentirse perdido.
                </p>
                <p style="color: #ccc; line-height: 1.6; font-size: 0.9rem; text-align: justify; margin-bottom: 15px;">
                    En <strong style="color: #00ffad;">RSU Club</strong> marcamos la distancia: aquí no hay promesas vacías, solo <strong>conocimiento real, colaboración y responsabilidad</strong>.
                </p>
                <p style="color: #ccc; line-height: 1.6; font-size: 0.9rem; text-align: justify;">
                    Somos una comunidad de trading diseñada para ser <strong>seria, responsable y rentable</strong>. Te dotamos de las herramientas y el respaldo necesarios para que tus decisiones de inversión estén fundamentadas y cuenten con garantías.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # QUÉ TE OFRECEMOS
        st.markdown("""
        <div class="rsu-card" style="height: 580px;">
            <div class="rsu-card-header">
                <div class="rsu-card-title">🛠️ ¿Qué te ofrecemos?</div>
                <div class="tooltip-icon" data-tooltip="Recursos exclusivos disponibles para miembros Elite.">?</div>
            </div>
            <div class="rsu-card-content" style="height: calc(580px - 50px); overflow-y: auto;">
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

        st.markdown('</div></div>', unsafe_allow_html=True)

    # SECCIÓN FINAL
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="rsu-card">
        <div class="rsu-card-header">
            <div class="rsu-card-title">🚀 Tu camino empieza aquí</div>
            <div class="tooltip-icon" data-tooltip="Próximos pasos para aprovechar al máximo tu membresía.">?</div>
        </div>
        <div class="rsu-card-content">
            <p style="color: #ccc; line-height: 1.6; font-size: 0.9rem; margin-bottom: 15px;">
                Te invito a explorar la comunidad, participar en los debates y consultar cualquier duda. Si necesitas algo específico, puedes contactarme por <strong style="color: #00ffad;">mensaje directo (MD)</strong>; te responderé lo antes posible.
            </p>
            
            <div class="tip-box">
                <p style="margin: 0; color: #fff; font-size: 0.9rem;">
                    💡 <strong>Consejo:</strong> No te abrumes por el volumen de información. Tómalo con calma, a tu ritmo; poco a poco integrarás los conocimientos necesarios para operar con confianza.
                </p>
            </div>
            
            <p style="color: #ccc; line-height: 1.6; font-size: 0.9rem; margin-bottom: 15px;">
                Gracias por formar parte de un espacio donde la <strong>formación, la responsabilidad y la transparencia</strong> son la prioridad. Deja atrás el ruido de los falsos gurús y comienza tu camino hacia un <strong style="color: #00ffad;">trading consciente</strong>.
            </p>
            
            <div class="signature-box">
                <strong style="color: #00ffad; font-style: normal;">unlord</strong> | RSU Club ♣️
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
