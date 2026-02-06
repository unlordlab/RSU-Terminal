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

    # SECCIÓN 1: Carácter Educativo
    html_section1 = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; padding: 12px 0 0 0; font-family: Inter, sans-serif; background: transparent; }
        .wrapper { padding: 0 20px; }
        .card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            padding: 30px;
            position: relative;
            box-sizing: border-box;
        }
        .number {
            position: absolute;
            top: -12px;
            left: 25px;
            background: linear-gradient(135deg, #00ffad 0%, #00d4ff 100%);
            color: #0c0e12;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0, 255, 173, 0.3);
            z-index: 10;
        }
        .title {
            color: white;
            font-size: 1.2rem;
            font-weight: 600;
            margin: 10px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #00ffad;
        }
        .content {
            color: #ccc;
            font-size: 0.95rem;
            line-height: 1.7;
            font-weight: 400;
            margin-bottom: 20px;
        }
        .highlight {
            background: rgba(242, 54, 69, 0.08);
            border: 1px solid rgba(242, 54, 69, 0.3);
            border-radius: 8px;
            padding: 20px;
        }
        .highlight-title {
            color: #f23645;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .highlight-text {
            color: #aaa;
            font-size: 0.9rem;
            line-height: 1.6;
            margin: 0;
        }
        .badges {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        .badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-green {
            background: rgba(0, 255, 173, 0.15);
            color: #00ffad;
            border: 1px solid rgba(0, 255, 173, 0.3);
        }
        .badge-orange {
            background: rgba(255, 152, 0, 0.15);
            color: #ff9800;
            border: 1px solid rgba(255, 152, 0, 0.3);
        }
        .badge-red {
            background: rgba(242, 54, 69, 0.15);
            color: #f23645;
            border: 1px solid rgba(242, 54, 69, 0.3);
        }
    </style>
    </head>
    <body>
    <div class="wrapper">
        <div class="card">
            <div class="number">1</div>
            <h2 class="title">Carácter Educativo e Informativo</h2>
            <p class="content">
                Todo el contenido compartido en la comunidad <strong style="color: #00ffad;">RSU</strong>, incluyendo análisis de mercado, señales de trading, gráficos, videos y comentarios, tiene una finalidad <strong>estrictamente educativa e informativa</strong>.
            </p>
            <div class="highlight">
                <div class="highlight-title">⚠️ Importante</div>
                <p class="highlight-text">
                    Bajo ninguna circunstancia debe considerarse como asesoría financiera, recomendación de inversión o invitación a comprar/vender activos financieros.
                </p>
            </div>
            <div class="badges">
                <span class="badge badge-green">Educativo</span>
                <span class="badge badge-orange">Informativo</span>
                <span class="badge badge-red">No es Asesoría</span>
            </div>
        </div>
    </div>
    </body>
    </html>
    """
    components.html(html_section1, height=300, scrolling=False)

    # SECCIÓN 2: Riesgo de Capital
    html_section2 = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; padding: 12px 0 0 0; font-family: Inter, sans-serif; background: transparent; }
        .wrapper { padding: 0 20px; }
        .card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            padding: 30px;
            position: relative;
            box-sizing: border-box;
        }
        .number {
            position: absolute;
            top: -12px;
            left: 25px;
            background: linear-gradient(135deg, #00ffad 0%, #00d4ff 100%);
            color: #0c0e12;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0, 255, 173, 0.3);
            z-index: 10;
        }
        .title {
            color: white;
            font-size: 1.2rem;
            font-weight: 600;
            margin: 10px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #00ffad;
        }
        .content {
            color: #ccc;
            font-size: 0.95rem;
            line-height: 1.7;
            font-weight: 400;
            margin-bottom: 20px;
        }
        .risk-meter {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            background: #0c0e12;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .risk-label {
            color: #666;
            font-size: 0.85rem;
            font-weight: 500;
            min-width: 80px;
        }
        .risk-bar-container {
            flex: 1;
            height: 8px;
            background: #1a1e26;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }
        .risk-bar {
            width: 85%;
            height: 100%;
            background: linear-gradient(90deg, #00ffad 0%, #ff9800 50%, #f23645 100%);
            border-radius: 4px;
            position: relative;
        }
        .risk-marker {
            position: absolute;
            top: -4px;
            left: 85%;
            width: 16px;
            height: 16px;
            background: white;
            border: 3px solid #f23645;
            border-radius: 50%;
            transform: translateX(-50%);
            box-shadow: 0 2px 8px rgba(242, 54, 69, 0.4);
        }
        .risk-value {
            color: #f23645;
            font-weight: 700;
            font-size: 0.9rem;
            min-width: 60px;
            text-align: right;
        }
        .highlight-warning {
            background: rgba(255, 152, 0, 0.08);
            border: 1px solid rgba(255, 152, 0, 0.3);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
        }
        .highlight-title-warning {
            color: #ff9800;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .highlight-text {
            color: #aaa;
            font-size: 0.9rem;
            line-height: 1.6;
            margin: 0;
        }
        .badges {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: rgba(242, 54, 69, 0.15);
            color: #f23645;
            border: 1px solid rgba(242, 54, 69, 0.3);
        }
    </style>
    </head>
    <body>
    <div class="wrapper">
        <div class="card">
            <div class="number">2</div>
            <h2 class="title">Riesgo de Capital</h2>
            <p class="content">
                El trading de activos financieros conlleva un <strong style="color: #f23645;">alto nivel de riesgo</strong> y puede no ser adecuado para todos los inversores. Existe la posibilidad de perder una parte o la totalidad del capital invertido.
            </p>
            
            <div class="risk-meter">
                <span class="risk-label">Riesgo:</span>
                <div class="risk-bar-container">
                    <div class="risk-bar">
                        <div class="risk-marker"></div>
                    </div>
                </div>
                <span class="risk-value">ALTO</span>
            </div>
            
            <div class="highlight-warning">
                <div class="highlight-title-warning">🛑 Advertencia Crítica</div>
                <p class="highlight-text">
                    <strong>Nunca operes con dinero que no puedas permitirte perder.</strong> El apalancamiento puede amplificar tanto ganancias como pérdidas.
                </p>
            </div>
            
            <div class="badges">
                <span class="badge">Forex</span>
                <span class="badge">Criptomonedas</span>
                <span class="badge">Acciones</span>
                <span class="badge">Futuros</span>
            </div>
        </div>
    </div>
    </body>
    </html>
    """
    components.html(html_section2, height=400, scrolling=False)

    # SECCIÓN 3: Responsabilidad Individual
    html_section3 = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; padding: 12px 0 0 0; font-family: Inter, sans-serif; background: transparent; }
        .wrapper { padding: 0 20px; }
        .card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            padding: 30px;
            position: relative;
            box-sizing: border-box;
        }
        .number {
            position: absolute;
            top: -12px;
            left: 25px;
            background: linear-gradient(135deg, #00ffad 0%, #00d4ff 100%);
            color: #0c0e12;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0, 255, 173, 0.3);
            z-index: 10;
        }
        .title {
            color: white;
            font-size: 1.2rem;
            font-weight: 600;
            margin: 10px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #00ffad;
        }
        .content {
            color: #ccc;
            font-size: 0.95rem;
            line-height: 1.7;
            font-weight: 400;
            margin-bottom: 20px;
        }
        .check-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin: 12px 0;
            color: #aaa;
            font-size: 0.9rem;
        }
        .check-icon {
            color: #00ffad;
            font-weight: bold;
            min-width: 20px;
        }
        .highlight {
            background: rgba(242, 54, 69, 0.08);
            border: 1px solid rgba(242, 54, 69, 0.3);
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        .highlight-title {
            color: #f23645;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .highlight-text {
            color: #aaa;
            font-size: 0.9rem;
            line-height: 1.6;
            margin: 0;
        }
    </style>
    </head>
    <body>
    <div class="wrapper">
        <div class="card">
            <div class="number">3</div>
            <h2 class="title">Responsabilidad Individual</h2>
            <p class="content">
                Cada miembro de <strong style="color: #00ffad;">RSU</strong> es el <strong>único responsable</strong> de sus propias decisiones financieras y ejecuciones en el mercado. Los resultados pasados no garantizan rendimientos futuros.
            </p>
            
            <div class="check-item">
                <span class="check-icon">✓</span>
                <span>Tú eres responsable de tus decisiones de trading</span>
            </div>
            <div class="check-item">
                <span class="check-icon">✓</span>
                <span>Realiza tu propio análisis antes de operar</span>
            </div>
            <div class="check-item">
                <span class="check-icon">✓</span>
                <span>Gestiona tu riesgo adecuadamente</span>
            </div>
            
            <div class="highlight">
                <div class="highlight-title">📋 Limitación de Responsabilidad</div>
                <p class="highlight-text">
                    La comunidad y sus administradores <strong>no se hacen responsables</strong> de las pérdidas o daños económicos que puedan derivarse del uso de la información compartida.
                </p>
            </div>
        </div>
    </div>
    </body>
    </html>
    """
    components.html(html_section3, height=380, scrolling=False)

    # SECCIÓN 4: No somos Asesores
    html_section4 = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; padding: 12px 0 0 0; font-family: Inter, sans-serif; background: transparent; }
        .wrapper { padding: 0 20px; }
        .card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            padding: 30px;
            position: relative;
            box-sizing: border-box;
        }
        .number {
            position: absolute;
            top: -12px;
            left: 25px;
            background: linear-gradient(135deg, #00ffad 0%, #00d4ff 100%);
            color: #0c0e12;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0, 255, 173, 0.3);
            z-index: 10;
        }
        .title {
            color: white;
            font-size: 1.2rem;
            font-weight: 600;
            margin: 10px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #00ffad;
        }
        .content {
            color: #ccc;
            font-size: 0.95rem;
            line-height: 1.7;
            font-weight: 400;
            margin-bottom: 20px;
        }
        .highlight-success {
            background: rgba(0, 255, 173, 0.08);
            border: 1px solid rgba(0, 255, 173, 0.3);
            border-radius: 8px;
            padding: 20px;
        }
        .highlight-title-success {
            color: #00ffad;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .highlight-text {
            color: #aaa;
            font-size: 0.9rem;
            line-height: 1.6;
            margin: 0;
        }
    </style>
    </head>
    <body>
    <div class="wrapper">
        <div class="card">
            <div class="number">4</div>
            <h2 class="title">No somos Asesores Financieros</h2>
            <p class="content">
                Los administradores y moderadores de <strong style="color: #00ffad;">RSU</strong> <strong>no son asesores financieros titulados</strong> ni gestores de patrimonio. Somos traders y entusiastas del mercado compartiendo conocimiento.
            </p>
            
            <div class="highlight-success">
                <div class="highlight-title-success">👨‍💼 Recomendación Profesional</div>
                <p class="highlight-text">
                    Te recomendamos encarecidamente que consultes con un <strong>profesional financiero certificado</strong> antes de tomar cualquier decisión de inversión significativa.
                </p>
            </div>
        </div>
    </div>
    </body>
    </html>
    """
    components.html(html_section4, height=280, scrolling=False)

    # Divider
    st.markdown("""
    <div style="height: 1px; background: linear-gradient(90deg, transparent, #2a3f5f, transparent); margin: 40px 0;"></div>
    """, unsafe_allow_html=True)

    # Footer
    html_footer = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; font-family: Inter, sans-serif; background: transparent; }
        .footer {
            padding: 40px 30px;
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border-radius: 12px;
            border: 1px solid #2a3f5f;
            text-align: center;
            box-sizing: border-box;
        }
        .footer-icon {
            font-size: 32px;
            margin-bottom: 15px;
            opacity: 0.9;
        }
        .footer-title {
            color: white;
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 20px;
        }
        .footer-text {
            color: #ccc;
            font-size: 0.95rem;
            line-height: 1.8;
            margin: 0 auto;
            max-width: 700px;
        }
        .footer-highlight {
            color: #f23645;
            font-weight: 600;
        }
        .footer-divider {
            margin-top: 25px;
            padding-top: 25px;
            border-top: 1px solid #2a3f5f;
        }
        .footer-copyright {
            color: #555;
            font-size: 0.8rem;
            margin: 0;
        }
    </style>
    </head>
    <body>
    <div class="footer">
        <div class="footer-icon">📜</div>
        <h3 class="footer-title">Nota Importante</h3>
        <p class="footer-text">
            Al permanecer en esta comunidad y utilizar nuestro contenido, declaras comprender y aceptar los riesgos inherentes al trading y <span class="footer-highlight">liberas a RSU de cualquier responsabilidad legal o financiera</span>.
        </p>
        <div class="footer-divider">
            <p class="footer-copyright">
                © 2025 RSU Trading Community • Última actualización: Febrero 2025
            </p>
        </div>
    </div>
    </body>
    </html>
    """
    components.html(html_footer, height=260, scrolling=False)

    st.markdown('</div>', unsafe_allow_html=True)
