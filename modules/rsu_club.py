# modules/rsu_club.py
import streamlit as st
import streamlit.components.v1 as components

def render():
    # CSS global consistente con market.py
    st.markdown("""
    <style>
        .tooltip-container {
            position: absolute;
            top: 50%;
            right: 12px;
            transform: translateY(-50%);
            cursor: help;
        }
        .tooltip-container .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px 12px;
            border-radius: 6px;
            position: absolute;
            z-index: 999;
            top: 140%;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s, visibility 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        .group-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
        }
        .group-header {
            background: #0c0e12;
            padding: 12px 15px;
            border-bottom: 1px solid #1a1e26;
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .group-title {
            margin: 0;
            color: white;
            font-size: 14px;
            font-weight: bold;
        }
        .group-content {
            padding: 0;
        }
        .rsu-logo-container {
            text-align: center;
            padding: 20px;
            background: linear-gradient(180deg, #0c0e12 0%, #11141a 100%);
            border-bottom: 1px solid #1a1e26;
        }
        .rsu-logo {
            max-width: 120px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 255, 173, 0.2);
        }
        .hero-text {
            font-size: 1.8rem;
            font-weight: bold;
            color: #00ffad;
            text-align: center;
            margin: 20px 0;
            text-shadow: 0 0 20px rgba(0, 255, 173, 0.3);
        }
        .section-title {
            color: #00ffad;
            font-size: 1.1rem;
            font-weight: bold;
            margin: 20px 0 10px 0;
            border-left: 3px solid #00ffad;
            padding-left: 10px;
        }
        .feature-card {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }
        .feature-card:hover {
            border-color: #00ffad44;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 255, 173, 0.1);
        }
        .feature-icon {
            font-size: 1.5rem;
            margin-bottom: 8px;
        }
        .feature-title {
            color: white;
            font-weight: bold;
            font-size: 0.95rem;
            margin-bottom: 5px;
        }
        .feature-desc {
            color: #888;
            font-size: 0.85rem;
            line-height: 1.4;
        }
        .manifesto-text {
            color: #ccc;
            line-height: 1.6;
            font-size: 0.9rem;
            text-align: justify;
        }
        .highlight-box {
            background: linear-gradient(135deg, #00ffad11 0%, #00ffad05 100%);
            border-left: 3px solid #00ffad;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
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
        .signature {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #1a1e26;
            text-align: center;
            color: #888;
            font-style: italic;
        }
        .signature strong {
            color: #00ffad;
            font-style: normal;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header con logo
    st.markdown("""
    <div class="group-container" style="margin-bottom: 20px;">
        <div class="rsu-logo-container">
            <img src="data:image/png;base64,{}" class="rsu-logo" alt="RSU Logo">
            <div class="hero-text">♣️ RSU Elite Club</div>
            <div class="status-badge">
                <div class="status-dot"></div>
                <span>Estado de suscripción: ACTIVO (Elite Member)</span>
            </div>
        </div>
    </div>
    """.format(get_image_base64()), unsafe_allow_html=True)

    # Layout de dos columnas
    col1, col2 = st.columns([1, 1])

    with col1:
        # Manifiesto / Introducción
        st.markdown("""
        <div class="group-container" style="height: 100%;">
            <div class="group-header">
                <p class="group-title">🎯 Nuestra Filosofía</p>
                <div class="tooltip-container">
                    <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                    <div class="tooltip-text">El núcleo de valores que define a nuestra comunidad de trading.</div>
                </div>
            </div>
            <div class="group-content" style="padding: 20px; background: #11141a;">
                <div class="highlight-box">
                    <strong style="color: #00ffad; font-size: 1.1rem;">Más que un club, una comunidad.</strong>
                </div>
                <div class="manifesto-text">
                    <p>En el ecosistema del trading, encontrar un espacio transparente es un verdadero desafío. Entre "gurús" que prometen riqueza inmediata y cursos costosos de nula eficacia, es normal sentirse perdido.</p>
                    <p>En <strong style="color: #00ffad;">RSU Club</strong> marcamos la distancia: aquí no hay promesas vacías, solo <strong>conocimiento real, colaboración y responsabilidad</strong>.</p>
                    <p>Somos una comunidad de trading diseñada para ser <strong>seria, responsable y rentable</strong>. Te dotamos de las herramientas y el respaldo necesarios para que tus decisiones de inversión estén fundamentadas y cuenten con garantías.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Qué te ofrecemos
        st.markdown("""
        <div class="group-container" style="height: 100%;">
            <div class="group-header">
                <p class="group-title">🛠️ ¿Qué te ofrecemos?</p>
                <div class="tooltip-container">
                    <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                    <div class="tooltip-text">Recursos exclusivos disponibles para miembros Elite.</div>
                </div>
            </div>
            <div class="group-content" style="padding: 15px; background: #11141a; height: calc(100% - 50px); overflow-y: auto;">
        """, unsafe_allow_html=True)

        features = [
            ("📊", "Análisis profundo y actualizado", "Seguimiento diario del sentimiento del mercado, tesis de compra exhaustivas e ideas operativas de alto interés."),
            ("🎓", "Estrategias y Formación", "Metodologías únicas adaptadas a diversos perfiles de riesgo. Base de datos de 'operaciones inusuales' y biblioteca exclusiva."),
            ("💎", "Recursos Exclusivos", "Listado actualizado de activos para carteras de medio/largo plazo e información de 'segundo nivel'."),
            ("🤝", "Soporte Personalizado", "Asesoramiento individual en configuración de herramientas (TradingView, brókers) para un entorno operativo óptimo.")
        ]

        for icon, title, desc in features:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    # Sección de bienvenida / cierre
    st.markdown("""
    <div class="group-container" style="margin-top: 20px;">
        <div class="group-header">
            <p class="group-title">🚀 Tu camino empieza aquí</p>
            <div class="tooltip-container">
                <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                <div class="tooltip-text">Próximos pasos para aprovechar al máximo tu membresía.</div>
            </div>
        </div>
        <div class="group-content" style="padding: 25px; background: #11141a;">
            <div class="manifesto-text">
                <p>Te invito a explorar la comunidad, participar en los debates y consultar cualquier duda. Si necesitas algo específico, puedes contactarme por <strong style="color: #00ffad;">mensaje directo (MD)</strong>; te responderé lo antes posible.</p>
                
                <div class="highlight-box" style="margin: 20px 0;">
                    <p style="margin: 0; color: #fff;">💡 <strong>Consejo:</strong> No te abrumes por el volumen de información. Tómalo con calma, a tu ritmo; poco a poco integrarás los conocimientos necesarios para operar con confianza.</p>
                </div>
                
                <p>Gracias por formar parte de un espacio donde la <strong>formación, la responsabilidad y la transparencia</strong> son la prioridad. Deja atrás el ruido de los falsos gurús y comienza tu camino hacia un <strong style="color: #00ffad;">trading consciente</strong>.</p>
            </div>
            
            <div class="signature">
                <strong>unlord</strong> | RSU Club ♣️
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def get_image_base64():
    """Convierte el logo a base64 para incrustarlo en HTML"""
    import base64
    try:
        with open("assets/rsu_logo.png", "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        # Fallback si no encuentra la imagen
        return ""
