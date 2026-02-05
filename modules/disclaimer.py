# -*- coding: utf-8 -*-
import streamlit as st

def render():
    # CSS Global con la estética de market.py
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        
        .main-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
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
        
        .header-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        
        .header-title {
            color: white;
            font-size: 2.2rem;
            font-weight: 700;
            margin: 0 0 10px 0;
            letter-spacing: -0.5px;
        }
        
        .header-subtitle {
            color: #888;
            font-size: 1rem;
            font-weight: 400;
            margin: 0;
        }
        
        .disclaimer-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 25px;
            position: relative;
            transition: all 0.3s ease;
        }
        
        .disclaimer-card:hover {
            border-color: #2a3f5f;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }
        
        .card-number {
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
        }
        
        .card-title {
            color: white;
            font-size: 1.2rem;
            font-weight: 600;
            margin: 10px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #00ffad;
        }
        
        .card-content {
            color: #ccc;
            font-size: 0.95rem;
            line-height: 1.7;
            font-weight: 400;
        }
        
        .highlight-box {
            background: rgba(242, 54, 69, 0.08);
            border: 1px solid rgba(242, 54, 69, 0.3);
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .highlight-box.warning {
            background: rgba(255, 152, 0, 0.08);
            border-color: rgba(255, 152, 0, 0.3);
        }
        
        .highlight-box.success {
            background: rgba(0, 255, 173, 0.08);
            border-color: rgba(0, 255, 173, 0.3);
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
        
        .highlight-box.warning .highlight-title {
            color: #ff9800;
        }
        
        .highlight-box.success .highlight-title {
            color: #00ffad;
        }
        
        .highlight-text {
            color: #aaa;
            font-size: 0.9rem;
            line-height: 1.6;
            margin: 0;
        }
        
        .footer-section {
            margin-top: 40px;
            padding: 40px 30px;
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border-radius: 12px;
            border: 1px solid #2a3f5f;
            text-align: center;
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
        
        .footer-text-container {
            max-width: 700px;
            margin: 0 auto;
            text-align: center;
        }
        
        .footer-text {
            color: #ccc;
            font-size: 0.95rem;
            line-height: 1.8;
            margin: 0;
            text-align: center;
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
        
        .risk-meter {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 20px;
            padding: 15px;
            background: #0c0e12;
            border-radius: 8px;
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
            height: 100%;
            background: linear-gradient(90deg, #00ffad 0%, #ff9800 50%, #f23645 100%);
            border-radius: 4px;
            position: relative;
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        .risk-marker {
            position: absolute;
            top: -4px;
            width: 16px;
            height: 16px;
            background: white;
            border: 3px solid #f23645;
            border-radius: 50%;
            transform: translateX(-50%);
            box-shadow: 0 2px 8px rgba(242, 54, 69, 0.4);
            animation: bounce 2s ease-in-out infinite;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateX(-50%) translateY(0); }
            50% { transform: translateX(-50%) translateY(-3px); }
        }
        
        .risk-value {
            color: #f23645;
            font-weight: 700;
            font-size: 0.9rem;
            min-width: 60px;
            text-align: right;
        }
        
        .badge-container {
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
        
        .badge-red {
            background: rgba(242, 54, 69, 0.15);
            color: #f23645;
            border: 1px solid rgba(242, 54, 69, 0.3);
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
        
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #2a3f5f, transparent);
            margin: 40px 0;
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
        
        @media (max-width: 768px) {
            .header-title {
                font-size: 1.6rem;
            }
            .disclaimer-card {
                padding: 20px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Contenedor principal
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="header-section">
        <div class="header-icon">⚖️</div>
        <h1 class="header-title">Descargo de Responsabilidad</h1>
        <p class="header-subtitle">RSU Trading Community • Términos y Condiciones Legales</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sección 1: Carácter Educativo
    st.markdown("""
    <div class="disclaimer-card">
        <div class="card-number">1</div>
        <h2 class="card-title">Carácter Educativo e Informativo</h2>
        <p class="card-content">
            Todo el contenido compartido en la comunidad <strong style="color: #00ffad;">RSU</strong>, incluyendo análisis de mercado, señales de trading, gráficos, videos y comentarios, tiene una finalidad <strong>estrictamente educativa e informativa</strong>.
        </p>
        <div class="highlight-box">
            <div class="highlight-title">⚠️ Importante</div>
            <p class="highlight-text">
                Bajo ninguna circunstancia debe considerarse como asesoría financiera, recomendación de inversión o invitación a comprar/vender activos financieros.
            </p>
        </div>
        <div class="badge-container">
            <span class="badge badge-green">Educativo</span>
            <span class="badge badge-orange">Informativo</span>
            <span class="badge badge-red">No es Asesoría</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sección 2: Riesgo de Capital
    st.markdown("""
    <div class="disclaimer-card">
        <div class="card-number">2</div>
        <h2 class="card-title">Riesgo de Capital</h2>
        <p class="card-content">
            El trading de activos financieros conlleva un <strong style="color: #f23645;">alto nivel de riesgo</strong> y puede no ser adecuado para todos los inversores. Existe la posibilidad de perder una parte o la totalidad del capital invertido.
        </p>
        
        <div class="risk-meter">
            <span class="risk-label">Riesgo:</span>
            <div class="risk-bar-container">
                <div class="risk-bar" style="width: 85%;">
                    <div class="risk-marker" style="left: 85%;"></div>
                </div>
            </div>
            <span class="risk-value">ALTO</span>
        </div>
        
        <div class="highlight-box warning" style="margin-top: 15px;">
            <div class="highlight-title">🛑 Advertencia Crítica</div>
            <p class="highlight-text">
                <strong>Nunca operes con dinero que no puedas permitirte perder.</strong> El apalancamiento puede amplificar tanto ganancias como pérdidas.
            </p>
        </div>
        
        <div class="badge-container">
            <span class="badge badge-red">Forex</span>
            <span class="badge badge-red">Criptomonedas</span>
            <span class="badge badge-red">Acciones</span>
            <span class="badge badge-red">Futuros</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sección 3: Responsabilidad Individual
    st.markdown("""
    <div class="disclaimer-card">
        <div class="card-number">3</div>
        <h2 class="card-title">Responsabilidad Individual</h2>
        <p class="card-content">
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
        
        <div class="highlight-box" style="margin-top: 15px;">
            <div class="highlight-title">📋 Limitación de Responsabilidad</div>
            <p class="highlight-text">
                La comunidad y sus administradores <strong>no se hacen responsables</strong> de las pérdidas o daños económicos que puedan derivarse del uso de la información compartida.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sección 4: No somos Asesores
    st.markdown("""
    <div class="disclaimer-card">
        <div class="card-number">4</div>
        <h2 class="card-title">No somos Asesores Financieros</h2>
        <p class="card-content">
            Los administradores y moderadores de <strong style="color: #00ffad;">RSU</strong> <strong>no son asesores financieros titulados</strong> ni gestores de patrimonio. Somos traders y entusiastas del mercado compartiendo conocimiento.
        </p>
        
        <div class="highlight-box success">
            <div class="highlight-title">👨‍💼 Recomendación Profesional</div>
            <p class="highlight-text">
                Te recomendamos encarecidamente que consultes con un <strong>profesional financiero certificado</strong> antes de tomar cualquier decisión de inversión significativa.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Divider
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Footer con nota importante - CORREGIDO Y CENTRADO
    st.markdown("""
    <div class="footer-section">
        <div class="footer-icon">📜</div>
        <h3 class="footer-title">Nota Importante</h3>
        <div class="footer-text-container">
            <p class="footer-text">
                Al permanecer en esta comunidad y utilizar nuestro contenido, declaras comprender y aceptar los riesgos inherentes al trading y <span class="footer-highlight">liberas a RSU de cualquier responsabilidad legal o financiera</span>.
            </p>
        </div>
        <div class="footer-divider">
            <p class="footer-copyright">
                © 2025 RSU Trading Community • Última actualización: Febrero 2025
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Final del archivo
