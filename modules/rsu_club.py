# modules/rsu_club.py
import streamlit as st
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import io

def get_logo_base64_enlarged():
    """Carga el logo, lo amplía y lo convierte a base64"""
    possible_paths = [
        "/mnt/kimi/upload/logo.png",
        "rsu_logo.png",
        "assets/logo.png", 
        "static/logo.png"
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            try:
                # Abrir imagen
                img = Image.open(path)
                
                # Convertir a RGBA si es necesario
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Ampliar el logo (6x para mayor nitidez)
                width, height = img.size
                new_size = (width * 6, height * 6)
                img_enlarged = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Guardar en buffer
                buffer = io.BytesIO()
                img_enlarged.save(buffer, format='PNG')
                return base64.b64encode(buffer.getvalue()).decode()
            except Exception as e:
                print(f"Error procesando logo: {e}")
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
    return None

def render():
    # CSS
    st.markdown("""
    <style>
        .rsu-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .logo-container {
            text-align: center;
            padding: 60px 20px 50px 20px;
            background: linear-gradient(180deg, #0c0e12 0%, #11141a 100%);
            border: 1px solid #1a1e26;
            border-radius: 20px;
            margin-bottom: 35px;
            position: relative;
            overflow: hidden;
        }
        /* Efecto de brillo verde intenso alrededor del logo */
        .logo-container::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(0,255,173,0.25) 0%, rgba(0,255,173,0.1) 40%, transparent 70%);
            pointer-events: none;
            filter: blur(20px);
        }
        .logo-img {
            width: 320px;
            height: auto;
            position: relative;
            z-index: 1;
            /* Esquinas redondeadas */
            border-radius: 30px;
            /* Sombra verde intensa */
            box-shadow: 
                0 0 60px rgba(0, 255, 173, 0.6),
                0 0 120px rgba(0, 255, 173, 0.4),
                0 0 180px rgba(0, 255, 173, 0.2);
            /* Mejora de nitidez */
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
        }
        .logo-title {
            font-size: 3rem;
            font-weight: bold;
            color: #00ffad;
            margin-top: 35px;
            position: relative;
            z-index: 1;
            text-shadow: 0 0 40px rgba(0, 255, 173, 0.5), 0 0 80px rgba(0, 255, 173, 0.3);
            letter-spacing: 2px;
        }
        .rsu-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            overflow: hidden;
            height: 100%;
        }
        .rsu-card-header {
            background: #0c0e12;
            padding: 18px 20px;
            border-bottom: 1px solid #1a1e26;
            font-weight: bold;
            color: white;
            font-size: 1.2rem;
        }
        .rsu-card-body {
            padding: 20px;
        }
        .highlight-box {
            background: linear-gradient(90deg, #00ffad22 0%, transparent 100%);
            border-left: 3px solid #00ffad;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }
        .highlight-text {
            color: #00ffad;
            font-weight: bold;
            font-size: 1.15rem;
        }
        .feature-item {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }
        .feature-item:hover {
            border-color: #00ffad44;
            transform: translateX(5px);
        }
        .feature-icon {
            font-size: 1.8rem;
            margin-bottom: 8px;
        }
        .feature-title {
            color: white;
            font-weight: bold;
            margin-bottom: 6px;
            font-size: 1.05rem;
        }
        .feature-desc {
            color: #888;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        .tip-box {
            background: #00ffad11;
            border-left: 3px solid #00ffad;
            padding: 18px;
            margin: 20px 0;
            border-radius: 0 10px 10px 0;
            color: white;
        }
        .signature {
            text-align: center;
            margin-top: 30px;
            padding-top: 25px;
            border-top: 1px solid #1a1e26;
            color: #666;
            font-style: italic;
        }
        p {
            color: #bbb;
            line-height: 1.8;
            margin-bottom: 15px;
            font-size: 0.95rem;
        }
        strong {
            color: #ddd;
        }
    </style>
    """, unsafe_allow_html=True)

    # HEADER CON LOGO AMPLIADO
    logo_b64 = get_logo_base64_enlarged()
    
    if logo_b64:
        st.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_b64}" class="logo-img" alt="RSU Logo">
            <div class="logo-title">♣️ RSU Elite Club</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Fallback con icono grande
        st.markdown("""
        <div class="logo-container">
            <div style="font-size: 10rem; line-height: 1; margin-bottom: 20px; text-shadow: 0 0 60px rgba(0,255,173,0.6), 0 0 120px rgba(0,255,173,0.4);">♣️</div>
            <div class="logo-title">RSU Elite Club</div>
        </div>
        """, unsafe_allow_html=True)

    # COLUMNAS PRINCIPALES
    col1, col2 = st.columns(2, gap="large")

    # COLUMNA IZQUIERDA - FILOSOFÍA
    with col1:
        st.markdown("""
        <div class="rsu-card">
            <div class="rsu-card-header">🎯 Nuestra Filosofía</div>
            <div class="rsu-card-body">
                <div class="highlight-box">
                    <span class="highlight-text">Más que un club, una comunidad.</span>
                </div>
                <p>
                    En el ecosistema del trading, encontrar un espacio transparente es un verdadero desafío. Entre "gurús" que prometen riqueza inmediata y cursos costosos de nula eficacia, es normal sentirse perdido.
                </p>
                <p>
                    En <strong style="color: #00ffad;">RSU Club</strong> marcamos la distancia: aquí no hay promesas vacías, solo <strong>conocimiento real, colaboración y responsabilidad</strong>.
                </p>
                <p>
                    Somos una comunidad de trading diseñada para ser <strong>seria, responsable y rentable</strong>. Te dotamos de las herramientas y el respaldo necesarios para que tus decisiones de inversión estén fundamentadas y cuenten con garantías.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # COLUMNA DERECHA - QUÉ OFRECEMOS
    with col2:
        features_html = """
        <div class="rsu-card">
            <div class="rsu-card-header">🛠️ ¿Qué te ofrecemos?</div>
            <div class="rsu-card-body">
                <div class="feature-item">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Análisis profundo y actualizado</div>
                    <div class="feature-desc">Seguimiento diario del sentimiento del mercado, tesis de compra exhaustivas e ideas operativas de alto interés.</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🎓</div>
                    <div class="feature-title">Estrategias y Formación</div>
                    <div class="feature-desc">Metodologías únicas adaptadas a diversos perfiles de riesgo. Base de datos de 'operaciones inusuales' y biblioteca exclusiva.</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">💎</div>
                    <div class="feature-title">Recursos Exclusivos</div>
                    <div class="feature-desc">Listado actualizado de activos para carteras de medio/largo plazo e información de 'segundo nivel'.</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🤝</div>
                    <div class="feature-title">Soporte Personalizado</div>
                    <div class="feature-desc">Asesoramiento individual en configuración de herramientas (TradingView, brókers) para un entorno operativo óptimo.</div>
                </div>
            </div>
        </div>
        """
        st.markdown(features_html, unsafe_allow_html=True)

    # SECCIÓN FINAL
    st.write("")
    st.markdown("""
    <div class="rsu-card">
        <div class="rsu-card-header">🚀 Tu camino empieza aquí</div>
        <div class="rsu-card-body">
            <p>
                Te invito a explorar la comunidad, participar en los debates y consultar cualquier duda. Si necesitas algo específico, puedes contactarme por <strong style="color: #00ffad;">mensaje directo (MD)</strong>; te responderé lo antes posible.
            </p>
            <div class="tip-box">
                💡 <strong>Consejo:</strong> No te abrumes por el volumen de información. Tómalo con calma, a tu ritmo; poco a poco integrarás los conocimientos necesarios para operar con confianza.
            </div>
            <p>
                Gracias por formar parte de un espacio donde la <strong>formación, la responsabilidad y la transparencia</strong> son la prioridad. Deja atrás el ruido de los falsos gurús y comienza tu camino hacia un <strong style="color: #00ffad;">trading consciente</strong>.
            </p>
            <div class="signature">
                <strong style="color: #00ffad; font-style: normal;">unlord</strong> | RSU Club ♣️
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)



