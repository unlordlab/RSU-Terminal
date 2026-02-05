
# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components

def render():
    # CSS Global
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .main-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        
        .header-section {
            text-align: center;
            margin-bottom: 50px;
            padding: 40px 30px;
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border-radius: 16px;
            border: 1px solid #2a3f5f;
            position: relative;
            overflow: hidden;
        }
        
        .header-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00ffad, #00d4ff, #00ffad);
            background-size: 200% 100%;
            animation: gradient-shift 3s ease infinite;
        }
        
        @keyframes gradient-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .header-icon { font-size: 48px; margin-bottom: 15px; }
        .header-title { color: white; font-size: 2.2rem; font-weight: 700; margin: 0 0 10px 0; letter-spacing: -0.5px; }
        .header-subtitle { color: #888; font-size: 1rem; font-weight: 400; margin: 0; }
        
        .footer-section {
            margin-top: 40px;
            padding: 40px 30px;
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border-radius: 12px;
            border: 1px solid #2a3f5f;
            text-align: center;
        }
        
        .footer-icon { font-size: 32px; margin-bottom: 15px; opacity: 0.9; }
        .footer-title { color: white; font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; }
        .footer-text { color: #ccc; font-size: 0.95rem; line-height: 1.8; margin: 0; text-align: center; }
        .footer-highlight { color: #f23645; font-weight: 600; }
        .footer-divider { margin-top: 25px; padding-top: 25px; border-top: 1px solid #2a3f5f; }
        .footer-copyright { color: #555; font-size: 0.8rem; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="header-section">
        <div class="header-icon">⚖️</div>
        <h1 class="header-title">Descargo de Responsabilidad</h1>
        <p class="header-subtitle">RSU Trading Community • Términos y Condiciones Legales</p>
    </div>
    """, unsafe_allow_html=True)

    # SECCIÓN 1: Carácter Educativo (HTML simple funciona)
    st.markdown("""
    <div style="background: #11141a; border: 1px solid #1a1e26; border-radius: 12px; padding: 30px; margin-bottom: 25px; position: relative;">
        <div style="position: absolute; top: -12px; left: 25px; background: linear-gradient(135deg, #00ffad 0%, #00d4ff 100%); color: #0c0e12; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; box-shadow: 0 4px 12px rgba(0, 255, 173, 0.3);">1</div>
        <h2 style="color: white; font-size: 1.2rem; font-weight: 600; margin: 10px 0 15px 0; padding-left: 10px; border-left: 3px solid #00ffad;">Carácter Educativo e Informativo</h2>
        <p style="color: #ccc; font-size: 0.95rem; line-height: 1.7; font-weight: 400;">
            Todo el contenido compartido en la comunidad <strong style="color: #00ffad;">RSU</strong>, incluyendo análisis de mercado, señales de trading, gráficos, videos y comentarios, tiene una finalidad <strong>estrictamente educativa e informativa</strong>.
        </p>
        <div style="background: rgba(242, 54, 69, 0.08); border: 1px solid rgba(242, 54, 69, 0.3); border-radius: 8px; padding: 20px; margin-top: 20px;">
            <div style="color: #f23645; font-weight: 600; font-size: 0.9rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">⚠️ Importante</div>
            <p style="color: #aaa; font-size: 0.9rem; line-height: 1.6; margin: 0;">
                Bajo ninguna circunstancia debe considerarse como asesoría financiera, recomendación de inversión o invitación a comprar/vender activos financieros.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # SECCIÓN 2: Riesgo de Capital (usando components.html)
    html_section2 = """
    <div style="background: #11141a; border: 1px solid #1a1e26; border-radius: 12px; padding: 30px; margin-bottom: 25px; position: relative; font-family: Inter, sans-serif;">
        <div style="position: absolute; top: -12px; left: 25px; background: linear-gradient(135deg, #00ffad 0%, #00d4ff 100%); color: #0c0e12; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; box-shadow: 0 4px 12px rgba(0, 255, 173, 0.3);">2</div>
        <h2 style="color: white; font-size: 1.2rem; font-weight: 600; margin: 10px 0 15px 0; padding-left: 10px; border-left: 3px solid #00ffad;">Riesgo de Capital</h2>
        <p style="color: #ccc; font-size: 0.95rem; line-height: 1.7; font-weight: 400; margin-bottom: 20px;">
            El trading de activos financieros conlleva un <strong style="color: #f23645;">alto nivel de riesgo</strong> y puede no ser adecuado para todos los inversores. Existe la posibilidad de perder una parte o la totalidad del capital invertido.
        </p>
        
        <div style="display: flex; align-items: center; gap: 15px; margin-top: 20px; padding: 15px; background: #0c0e12; border-radius: 8px;">
            <span style="color: #666; font-size: 0.85rem; font-weight: 500; min-width: 80px;">Riesgo:</span>
            <div style="flex: 1; height: 8px; background: #1a1e26; border-radius: 4px; overflow: hidden; position: relative;">
                <div style="width: 85%; height: 100%; background: linear-gradient(90deg, #00ffad 0%, #ff9800 50%, #f23645 100%); border-radius: 4px; position: relative;">
                    <div style="position: absolute; top: -4px; left: 85%; width: 16px; height: 16px; background: white; border: 3px solid #f23645; border-radius: 50%; transform: translateX(-50%); box-shadow: 0 2px 8px rgba(242, 54, 69, 0.4);"></div>
                </div>
            </div>
            <span style="color: #f23645; font-weight: 700; font-size: 0.9rem; min-width: 60px; text-align: right;">ALTO</span>
        </div>
        
        <div style="background: rgba(255, 152, 0, 0.08); border: 1px solid rgba(255, 152, 0, 0.3); border-radius: 8px; padding: 20px; margin-top: 15px;">
            <div style="color: #ff9800; font-weight: 600; font-size: 0.9rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">🛑 Advertencia Crítica</div>
            <p style="color: #aaa; font-size: 0.9rem; line-height: 1.6; margin: 0;">
                <strong>Nunca operes con dinero que no puedas permitirte perder.</strong> El apalancamiento puede amplificar tanto ganancias como pérdidas.
            </p>
        </div>
        
        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px;">
            <span style="padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: rgba(242, 54, 69, 0.15); color: #f23645; border: 1px solid rgba(242, 54, 69, 0.3);">Forex</span>
            <span style="padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: rgba(242, 54, 69, 0.15); color: #f23645; border: 1px solid rgba(242, 54, 69, 0.3);">Criptomonedas</span>
            <span style="padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: rgba(242, 54, 69, 0.15); color: #f23645; border: 1px solid rgba(242, 54, 69, 0.3);">Acciones</span>
            <span style="padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: rgba(242, 54, 69, 0.15); color: #f23645; border: 1px solid rgba(242, 54, 69, 0.3);">Futuros</span>
        </div>
    </div>
    """
    components.html(html_section2, height=320, scrolling=False)

    # SECCIÓN 3: Responsabilidad Individual
    html_section3 = """
    <div style="background: #11141a; border: 1px solid #1a1e26; border-radius: 12px; padding: 30px; margin-bottom: 25px; position: relative; font-family: Inter, sans-serif;">
        <div style="position: absolute; top: -12px; left: 25px; background: linear-gradient(135deg, #00ffad 0%, #00d4ff 100%); color: #0c0e12; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; box-shadow: 0 4px 12px rgba(0, 255, 173, 0.3);">3</div>
        <h2 style="color: white; font-size: 1.2rem; font-weight: 600; margin: 10px 0 15px 0; padding-left: 10px; border-left: 3px solid #00ffad;">Responsabilidad Individual</h2>
        <p style="color: #ccc; font-size: 0.95rem; line-height: 1.7; font-weight: 400; margin-bottom: 20px;">
            Cada miembro de <strong style="color: #00ffad;">RSU</strong> es el <strong>único responsable</strong> de sus propias decisiones financieras y ejecuciones en el mercado. Los resultados pasados no garantizan rendimientos futuros.
        </p>
        
        <div style="display: flex; align-items: flex-start; gap: 12px; margin: 12px 0; color: #aaa; font-size: 0.9rem;">
            <span style="color: #00ffad; font-weight: bold; min-width: 20px;">✓</span>
            <span>Tú eres responsable de tus decisiones de trading</span>
        </div>
        <div style="display: flex; align-items: flex-start; gap: 12px; margin: 12px 0; color: #aaa; font-size: 0.9rem;">
            <span style="color: #00ffad; font-weight: bold; min-width: 20px;">✓</span>
            <span>Realiza tu propio análisis antes de operar</span>
        </div>
        <div style="display: flex; align-items: flex-start; gap: 12px; margin: 12px 0; color: #aaa; font-size: 0.9rem;">
            <span style="color: #00ffad; font-weight: bold; min-width: 20px;">✓</span>
            <span>Gestiona tu riesgo adecuadamente</span>
        </div>
        
        <div style="background: rgba(242, 54, 69, 0.08); border: 1px solid rgba(242, 54, 69, 0.3); border-radius: 8px; padding: 20px; margin-top: 15px;">
            <div style="color: #f23645; font-weight: 600; font-size: 0.9rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">📋 Limitación de Responsabilidad</div>
            <p style="color: #aaa; font-size: 0.9rem; line-height: 1.6; margin: 0;">
                La comunidad y sus administradores <strong>no se hacen responsables</strong> de las pérdidas o daños económicos que puedan derivarse del uso de la información compartida.
            </p>
        </div>
    </div>
    """
    components.html(html_section3, height=340, scrolling=False)

    # SECCIÓN 4: No somos Asesores
    html_section4 = """
    <div style="background: #11141a; border: 1px solid #1a1e26; border-radius: 12px; padding: 30px; margin-bottom: 25px; position: relative; font-family: Inter, sans-serif;">
        <div style="position: absolute; top: -12px; left: 25px; background: linear-gradient(135deg, #00ffad 0%, #00d4ff 100%); color: #0c0e12; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; box-shadow: 0 4px 12px rgba(0, 255, 173, 0.3);">4</div>
        <h2 style="color: white; font-size: 1.2rem; font-weight: 600; margin: 10px 0 15px 0; padding-left: 10px; border-left: 3px solid #00ffad;">No somos Asesores Financieros</h2>
        <p style="color: #ccc; font-size: 0.95rem; line-height: 1.7; font-weight: 400; margin-bottom: 20px;">
            Los administradores y moderadores de <strong style="color: #00ffad;">RSU</strong> <strong>no son asesores financieros titulados</strong> ni gestores de patrimonio. Somos traders y entusiastas del mercado compartiendo conocimiento.
        </p>
        
        <div style="background: rgba(0, 255, 173, 0.08); border: 1px solid rgba(0, 255, 173, 0.3); border-radius: 8px; padding: 20px; margin-top: 15px;">
            <div style="color: #00ffad; font-weight: 600; font-size: 0.9rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">👨‍💼 Recomendación Profesional</div>
            <p style="color: #aaa; font-size: 0.9rem; line-height: 1.6; margin: 0;">
                Te recomendamos encarecidamente que consultes con un <strong>profesional financiero certificado</strong> antes de tomar cualquier decisión de inversión significativa.
            </p>
        </div>
    </div>
    """
    components.html(html_section4, height=260, scrolling=False)

    # Divider
    st.markdown('<div style="height: 1px; background: linear-gradient(90deg, transparent, #2a3f5f, transparent); margin: 40px 0;"></div>', unsafe_allow_html=True)

    # Footer
    html_footer = """
    <div style="margin-top: 40px; padding: 40px 30px; background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border-radius: 12px; border: 1px solid #2a3f5f; text-align: center; font-family: Inter, sans-serif;">
        <div style="font-size: 32px; margin-bottom: 15px; opacity: 0.9;">📜</div>
        <h3 style="color: white; font-size: 1.1rem; font-weight: 600; margin-bottom: 20px;">Nota Importante</h3>
        <p style="color: #ccc; font-size: 0.95rem; line-height: 1.8; margin: 0 auto; max-width: 700px; text-align: center;">
            Al permanecer en esta comunidad y utilizar nuestro contenido, declaras comprender y aceptar los riesgos inherentes al trading y <span style="color: #f23645; font-weight: 600;">liberas a RSU de cualquier responsabilidad legal o financiera</span>.
        </p>
        <div style="margin-top: 25px; padding-top: 25px; border-top: 1px solid #2a3f5f;">
            <p style="color: #555; font-size: 0.8rem; margin: 0;">
                © 2025 RSU Trading Community • Última actualización: Febrero 2025
            </p>
        </div>
    </div>
    """
    components.html(html_footer, height=220, scrolling=False)

    st.markdown('</div>', unsafe_allow_html=True)
