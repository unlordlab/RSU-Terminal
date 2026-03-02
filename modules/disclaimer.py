# -*- coding: utf-8 -*-
import streamlit as st

def render():
    # CSS Global — terminal/hacker aesthetic (aligned with roadmap_2026)
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp {
            background: #0c0e12;
        }

        /* VT323 for headings */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            color: #00ffad !important;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        h1 {
            font-size: 3.5rem !important;
            text-shadow: 0 0 20px #00ffad66;
            border-bottom: 2px solid #00ffad;
            padding-bottom: 15px;
            margin-bottom: 30px !important;
        }

        h2 {
            font-size: 2.2rem !important;
            color: #00d9ff !important;
            border-left: 4px solid #00ffad;
            padding-left: 15px;
            margin-top: 40px !important;
        }

        h3 {
            font-size: 1.8rem !important;
            color: #ff9800 !important;
            margin-top: 30px !important;
        }

        h4 {
            font-size: 1.5rem !important;
            color: #9c27b0 !important;
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

        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad, transparent);
            margin: 40px 0;
        }

        blockquote {
            border-left: 3px solid #ff9800;
            margin: 20px 0;
            padding-left: 20px;
            color: #ff9800;
            font-style: italic;
        }

        /* Shared layout classes */
        .terminal-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #00ffad44;
            border-radius: 8px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 0 15px #00ffad11;
        }

        .phase-box {
            background: #0c0e12;
            border-left: 3px solid #00ffad;
            padding: 20px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }

        .highlight-quote {
            background: #00ffad11;
            border: 1px solid #00ffad33;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            font-family: 'VT323', monospace;
            font-size: 1.2rem;
            color: #00ffad;
            text-align: center;
        }

        .risk-box {
            background: linear-gradient(135deg, #1a0f0f 0%, #261a1a 100%);
            border: 1px solid #f2364544;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }

        .warning-box {
            background: linear-gradient(135deg, #1a110a 0%, #261b0f 100%);
            border: 1px solid #ff980044;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }

        .success-box {
            background: #00ffad0d;
            border: 1px solid #00ffad33;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }

        .badge-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }

        .badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-family: 'VT323', monospace;
            font-size: 1rem;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .badge-green  { background: rgba(0,255,173,0.12); color: #00ffad; border: 1px solid rgba(0,255,173,0.3); }
        .badge-orange { background: rgba(255,152,0,0.12);  color: #ff9800; border: 1px solid rgba(255,152,0,0.3); }
        .badge-red    { background: rgba(242,54,69,0.12);  color: #f23645; border: 1px solid rgba(242,54,69,0.3); }

        .check-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            color: #aaa;
            font-size: 0.9rem;
        }

        .check-icon { color: #00ffad; font-weight: bold; min-width: 18px; }

        .risk-meter {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            background: #0c0e12;
            border-radius: 8px;
            margin: 15px 0;
        }

        .risk-label {
            font-family: 'Courier New', monospace;
            color: #666;
            font-size: 0.85rem;
            min-width: 80px;
        }

        .risk-bar-container {
            flex: 1;
            height: 8px;
            background: #1a1e26;
            border-radius: 4px;
            overflow: visible;
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
            box-shadow: 0 2px 8px rgba(242,54,69,0.4);
        }

        .risk-value {
            font-family: 'VT323', monospace;
            color: #f23645;
            font-size: 1.1rem;
            min-width: 60px;
            text-align: right;
        }

        .strategy-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin: 20px 0;
        }

        .strategy-card {
            background: #0c0e12;
            border: 1px solid #2a3f5f;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }

        .strategy-card p {
            font-family: 'VT323', monospace !important;
            font-size: 1.05rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── HEADER ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; margin-bottom:40px;">
        <div style="font-family:'VT323',monospace; font-size:1rem; color:#666; margin-bottom:10px;">
            [SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]
        </div>
        <h1>⚖️ DESCARGO DE RESPONSABILIDAD</h1>
        <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.2rem; letter-spacing:3px;">
            RSU TRADING COMMUNITY // TÉRMINOS Y CONDICIONES LEGALES
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── SECCIÓN 1: Carácter Educativo ────────────────────────────────────────
    st.markdown("""
    <h2>01 // CARÁCTER EDUCATIVO E INFORMATIVO</h2>

    <p>
        Todo el contenido compartido en la comunidad <strong>RSU</strong>, incluyendo análisis de mercado,
        señales de trading, gráficos, videos y comentarios, tiene una finalidad
        <strong>estrictamente educativa e informativa</strong>.
    </p>

    <div class="risk-box">
        <h4 style="color:#f23645 !important; margin-top:0;">⚠️ IMPORTANTE</h4>
        <p>
            Bajo ninguna circunstancia debe considerarse como asesoría financiera,
            recomendación de inversión o invitación a comprar/vender activos financieros.
        </p>
    </div>

    <div class="badge-row">
        <span class="badge badge-green">Educativo</span>
        <span class="badge badge-orange">Informativo</span>
        <span class="badge badge-red">No es Asesoría</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── SECCIÓN 2: Riesgo de Capital ─────────────────────────────────────────
    st.markdown("""
    <h2>02 // RIESGO DE CAPITAL</h2>

    <p>
        El trading de activos financieros conlleva un <strong style="color:#f23645;">alto nivel de riesgo</strong>
        y puede no ser adecuado para todos los inversores. Existe la posibilidad de perder una parte o
        la totalidad del capital invertido.
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

    <div class="warning-box">
        <h4 style="color:#ff9800 !important; margin-top:0;">🛑 ADVERTENCIA CRÍTICA</h4>
        <p>
            <strong>Nunca operes con dinero que no puedas permitirte perder.</strong>
            El apalancamiento puede amplificar tanto ganancias como pérdidas.
        </p>
    </div>

    <div class="badge-row">
        <span class="badge badge-red">Forex</span>
        <span class="badge badge-red">Criptomonedas</span>
        <span class="badge badge-red">Acciones</span>
        <span class="badge badge-red">Futuros</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── SECCIÓN 3: Responsabilidad Individual ────────────────────────────────
    st.markdown("""
    <h2>03 // RESPONSABILIDAD INDIVIDUAL</h2>

    <p>
        Cada miembro de <strong>RSU</strong> es el <strong>único responsable</strong> de sus propias
        decisiones financieras y ejecuciones en el mercado. Los resultados pasados no garantizan
        rendimientos futuros.
    </p>

    <div class="phase-box">
        <div class="check-item"><span class="check-icon">✓</span><span>Tú eres responsable de tus decisiones de trading</span></div>
        <div class="check-item"><span class="check-icon">✓</span><span>Realiza tu propio análisis antes de operar</span></div>
        <div class="check-item"><span class="check-icon">✓</span><span>Gestiona tu riesgo adecuadamente</span></div>
    </div>

    <div class="risk-box">
        <h4 style="color:#f23645 !important; margin-top:0;">📋 LIMITACIÓN DE RESPONSABILIDAD</h4>
        <p>
            La comunidad y sus administradores <strong>no se hacen responsables</strong> de las pérdidas
            o daños económicos que puedan derivarse del uso de la información compartida.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── SECCIÓN 4: No somos Asesores ─────────────────────────────────────────
    st.markdown("""
    <h2>04 // NO SOMOS ASESORES FINANCIEROS</h2>

    <p>
        Los administradores y moderadores de <strong>RSU</strong> <strong>no son asesores financieros
        titulados</strong> ni gestores de patrimonio. Somos traders y entusiastas del mercado
        compartiendo conocimiento.
    </p>

    <div class="strategy-grid">
        <div class="strategy-card" style="border-color:#f23645;">
            <h4 style="color:#f23645 !important;">❌ NO ES</h4>
            <p style="color:#f23645;">Asesoría financiera certificada</p>
        </div>
        <div class="strategy-card" style="border-color:#00ffad;">
            <h4 style="color:#00ffad !important;">✅ SÍ ES</h4>
            <p style="color:#00ffad;">Conocimiento compartido entre traders</p>
        </div>
    </div>

    <div class="success-box">
        <h4 style="color:#00ffad !important; margin-top:0;">👨‍💼 RECOMENDACIÓN PROFESIONAL</h4>
        <p>
            Te recomendamos encarecidamente que consultes con un <strong>profesional financiero
            certificado</strong> antes de tomar cualquier decisión de inversión significativa.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── FOOTER ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="terminal-box" style="text-align:center; border-color:#00ffad;">
        <div style="font-size:2rem; margin-bottom:15px;">📜</div>
        <h3 style="color:#00ffad !important; margin-top:0;">NOTA IMPORTANTE</h3>
        <p style="max-width:700px; margin:0 auto 20px auto; color:#ccc !important;">
            Al permanecer en esta comunidad y utilizar nuestro contenido, declaras comprender y aceptar
            los riesgos inherentes al trading y
            <strong style="color:#f23645;">liberas a RSU de cualquier responsabilidad legal o financiera</strong>.
        </p>
        <div style="border-top: 1px solid #1a1e26; padding-top: 20px; margin-top: 10px;">
            <p style="font-family:'VT323',monospace; color:#555; font-size:0.95rem;">
                [END OF DISCLAIMER // RSU_LEGAL_v2025]<br>
                [ÚLTIMA ACTUALIZACIÓN: FEBRERO 2025]<br>
                [STATUS: ACTIVE]
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
