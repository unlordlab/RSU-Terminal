import streamlit as st

def render():
    # Inject custom CSS with VT323 font and hacker terminal aesthetic
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp { 
            background: #0c0e12; 
        }

        /* VT323 font for all headings */
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

        /* Body text styling */
        p, li {
            font-family: 'Courier New', monospace;
            color: #ccc !important;
            line-height: 1.8;
            font-size: 0.95rem;
        }

        /* Custom containers */
        .terminal-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #00ffad44;
            border-radius: 8px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 0 15px #00ffad11;
        }

        .strategy-box {
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

        .taco-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #ff980044;
            border-radius: 8px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 0 15px #ff980011;
        }

        /* Timeline styling */
        .timeline-container {
            position: relative;
            padding-left: 30px;
        }

        .timeline-item {
            position: relative;
            margin-bottom: 25px;
            padding-left: 40px;
        }

        .timeline-item::before {
            content: '';
            position: absolute;
            left: -30px;
            top: 0;
            bottom: -25px;
            width: 2px;
            background: linear-gradient(180deg, #00ffad 0%, #00ffad44 100%);
        }

        .timeline-item::after {
            content: '';
            position: absolute;
            left: -38px;
            top: 5px;
            width: 16px;
            height: 16px;
            background: #00ffad;
            border-radius: 50%;
            box-shadow: 0 0 10px #00ffad66;
        }

        .timeline-day {
            font-family: 'VT323', monospace;
            color: #00d9ff;
            font-size: 1.1rem;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }

        .timeline-title {
            font-family: 'VT323', monospace;
            color: #ff9800;
            font-size: 1.3rem;
            margin-bottom: 8px;
            text-transform: uppercase;
        }

        .timeline-desc {
            color: #ccc;
            font-family: 'Courier New', monospace;
            line-height: 1.6;
            background: #1a1e26;
            padding: 12px;
            border-radius: 6px;
            border-left: 2px solid #00ffad33;
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

        /* Horizontal rule */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad, transparent);
            margin: 40px 0;
        }

        /* Strong text */
        strong {
            color: #00ffad;
            font-weight: bold;
        }

        /* Caption styling */
        .terminal-caption {
            font-family: 'VT323', monospace;
            color: #666;
            font-size: 0.9rem;
            text-align: center;
            margin-top: 30px;
            padding: 15px;
            border-top: 1px solid #1a1e26;
        }

        /* Phase indicators */
        .phase-indicator {
            display: inline-block;
            background: #00ffad;
            color: #0c0e12;
            font-family: 'VT323', monospace;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.9rem;
            margin-right: 8px;
        }

        .panic-indicator {
            background: #f23645;
            color: white;
        }

        .opportunity-indicator {
            background: #00ffad;
            color: #0c0e12;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header Section
    st.markdown("""
    <div style="text-align:center; margin-bottom:40px;">
        <div style="font-family: 'VT323', monospace; font-size: 1rem; color: #666; margin-bottom: 10px;">
            [CLASSIFIED // TRUMP_TRADING_PROTOCOL v2.0]
        </div>
        <h1>🇺🇸 TRUMP PLAYBOOK</h1>
        <div style="font-family: 'VT323', monospace; color: #00d9ff; font-size: 1.2rem; letter-spacing: 3px;">
            MANUAL DE OPERACIONES // CICLO DE ARANCELES
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- INTRODUCCIÓN ESTRATEGIA TACO ---
    st.markdown("""
    <div class="taco-box">
        <h3 style="color: #ff9800 !important; margin-top: 0; border-bottom: 1px solid #ff980033; padding-bottom: 10px;">
            🌮 LA ESTRATEGIA T.A.C.O.
        </h3>
        <p style="font-family: 'VT323', monospace; font-size: 1.3rem; color: #ff9800 !important; margin: 15px 0;">
            <strong>"TRUMP ALWAYS CHICKENS OUT"</strong>
        </p>
        <p style="color: #ccc !important; line-height: 1.8;">
            Término acuñado en Wall Street para describir el patrón cíclico de las negociaciones de Donald Trump. 
            La estrategia consiste en lanzar una <strong>amenaza extrema</strong> (generalmente aranceles) para generar 
            pánico y obtener posición de fuerza, solo para suavizar o retrasar la medida una vez que los mercados 
            reaccionan o se inician conversaciones.
        </p>
        <div class="highlight-quote" style="margin: 20px 0; font-size: 1.1rem;">
            Para los inversores, este "ruido" crea oportunidades de compra durante el pánico inicial.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # --- LÍNEA DE TIEMPO ESTILIZADA ---
    st.markdown("""
    <h2>🗓️ CRONOLOGÍA DEL PLAYBOOK</h2>
    <p style="margin-bottom: 30px;">Análisis de fases desde el mensaje inicial hasta el retorno del optimismo:</p>
    """, unsafe_allow_html=True)

    playbook_steps = [
        {"dia": "VIERNES", "titulo": "El Mensaje Inicial", "desc": "El presidente publica un mensaje críptico sugiriendo aranceles a un país o sector específico.", "fase": "ALERTA"},
        {"dia": "VIE/SÁB", "titulo": "Anuncio Oficial", "desc": "Anuncia formalmente un nuevo gran arancel, sofít del 25% o más.", "fase": "AMENAZA"},
        {"dia": "FINDE", "titulo": "Presión Psicológica", "desc": "Refuerza sus amenazas repetidamente para aplicar presión con mercados cerrados.", "fase": "TENSIÓN"},
        {"dia": "FINDE", "titulo": "Reacción Internacional", "desc": "Los países afectados dan señales de estar dispuestos a negociar.", "fase": "NEGOCIACIÓN"},
        {"dia": "DOM NOCHE", "titulo": "Apertura de Futuros", "desc": "El mercado cae en una reacción emocional inicial a los titulares.", "fase": "PÁNICO"},
        {"dia": "LUN/MAR", "titulo": "Fase de Realismo", "desc": "Los inversores se dan cuenta de que los aranceles aún no se han aplicado (fecha futura).", "fase": "ANÁLISIS"},
        {"dia": "MIÉRCOLES", "titulo": "Rebote de Alivio", "desc": "Aparecen los compradores de oportunidades ('smart money').", "fase": "OPORTUNIDAD"},
        {"dia": "FINDE 2", "titulo": "Cambio de Narrativa", "desc": "El presidente publica que hay conversaciones en marcha y soluciones en camino.", "fase": "OPTIMISMO"},
        {"dia": "DOM NOCHE 2", "titulo": "Retorno del Optimismo", "desc": "Los futuros abren al alza a medida que vuelve la confianza.", "fase": "RECUPERACIÓN"},
        {"dia": "LUNES 2", "titulo": "Aparición de Moderadores", "desc": "Altos cargos (como Scott Bessent) tranquilizan a los inversores en TV.", "fase": "ESTABILIZACIÓN"},
        {"dia": "SEMANAS 2-4", "titulo": "Fase de Filtraciones", "desc": "Pistas sobre los avances hacia un acuerdo final.", "fase": "RESOLUCIÓN"}
    ]

    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
    
    for i, step in enumerate(playbook_steps, 1):
        phase_class = "opportunity-indicator" if "OPORTUNIDAD" in step['fase'] or "RECUPERACIÓN" in step['fase'] or "OPTIMISMO" in step['fase'] else "panic-indicator" if "PÁNICO" in step['fase'] else ""
        
        st.markdown(f"""
        <div class="timeline-item">
            <div class="timeline-day">{step['dia']} <span class="phase-indicator {phase_class}">FASE: {step['fase']}</span></div>
            <div class="timeline-title">{step['titulo']}</div>
            <div class="timeline-desc">{step['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- SECCIÓN DE ESTRATEGIA OPERATIVA ---
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown("""
    <h2>⚡ ESTRATEGIA OPERATIVA</h2>
    
    <div class="strategy-box">
        <h4 style="color: #00ffad !important; font-family: 'VT323', monospace; font-size: 1.3rem; margin-top: 0;">
            🎯 MOMENTO DE ENTRADA ÓPTIMO
        </h4>
        <p>La <strong>fase de realismo (Lun/Mar)</strong> suele ofrecer el mejor risk/reward. El pánico inicial ha pasado, 
        pero el mercado aún no ha procesado completamente que los aranceles tienen fecha futura o son negociables.</p>
    </div>
    
    <div class="strategy-box">
        <h4 style="color: #00ffad !important; font-family: 'VT323', monospace; font-size: 1.3rem; margin-top: 0;">
            📊 GESTIÓN DE RIESGO
        </h4>
        <ul>
            <li>No operar el gap inicial del domingo (demasiado volatilidad)</li>
            <li>Escalar posiciones progresivamente durante la fase de realismo</li>
            <li>Stop loss por debajo del mínimo de la apertura de futuros</li>
            <li>Objetivo: recuperación del 50-61.8% de la caída inicial</li>
        </ul>
    </div>
    
    <div class="strategy-box">
        <h4 style="color: #00ffad !important; font-family: 'VT323', monospace; font-size: 1.3rem; margin-top: 0;">
            🔄 PATRÓN DE REPETICIÓN
        </h4>
        <p>Este playbook se ha repetido en múltiples ocasiones (2018-2019 trade war, 2025 aranceles). 
        La clave es reconocer la <strong>secuencia</strong>, no solo el evento aislado.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # --- NOTAS FINALES ---
    st.markdown("""
    <div class="terminal-box" style="border-color: #ff9800;">
        <h3 style="color: #ff9800 !important; margin-top: 0;">⚠️ ADVERTENCIA DE SISTEMA</h3>
        <p style="color: #ccc !important;">
            Este playbook asume comportamiento histórico del sujeto. Eventos estructurales reales, 
            escalada geopolítica genuina o cambios en el entorno macro pueden invalidar el patrón. 
            Siempre operar con stops definidos.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="terminal-caption">
        [FUENTE: ESTRATEGIA DE MERCADO BASADA EN PATRONES HISTÓRICOS DE ADMINISTRACIÓN TRUMP]<br>
        [TIMESTAMP: 2026-03-01T00:00:00Z]<br>
        [STATUS: ACTIVE]
    </div>
    """, unsafe_allow_html=True)
