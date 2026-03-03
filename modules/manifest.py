# modules/manifest.py
import streamlit as st

def render():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&family=JetBrains+Mono:wght@400;700&display=swap');

        .stApp {
            background: #0c0e12;
        }

        /* VT323 para headings — estética CRT/terminal */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            color: #00ffad !important;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        h1 {
            font-size: 3.5rem !important;
            text-shadow: 0 0 30px #00ffad66, 0 0 60px #00ffad22;
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
            font-size: 1.4rem !important;
            color: #00ffad !important;
        }

        /* Body text */
        p, li {
            font-family: 'JetBrains Mono', monospace;
            color: #ccc !important;
            line-height: 1.8;
            font-size: 0.92rem;
        }

        /* Terminal box — contenedor principal */
        .terminal-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #00ffad44;
            border-radius: 8px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 0 20px #00ffad0d;
        }

        /* Phase box — bloques con acento lateral */
        .phase-box {
            background: #0c0e12;
            border-left: 3px solid #00ffad;
            padding: 20px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }

        .phase-box-red {
            background: #0c0e12;
            border-left: 3px solid #f23645;
            padding: 20px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }

        .phase-box-orange {
            background: #0c0e12;
            border-left: 3px solid #ff9800;
            padding: 20px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }

        /* Highlight quote — citas destacadas VT323 */
        .highlight-quote {
            background: #00ffad11;
            border: 1px solid #00ffad33;
            border-radius: 8px;
            padding: 20px 25px;
            margin: 20px 0;
            font-family: 'VT323', monospace;
            font-size: 1.3rem;
            color: #00ffad;
            text-align: center;
            letter-spacing: 1px;
        }

        .highlight-quote-red {
            background: #f2364511;
            border: 1px solid #f2364533;
            border-radius: 8px;
            padding: 20px 25px;
            margin: 20px 0;
            font-family: 'VT323', monospace;
            font-size: 1.3rem;
            color: #f23645;
            text-align: center;
            letter-spacing: 1px;
        }

        /* Risk box */
        .risk-box {
            background: linear-gradient(135deg, #1a0f0f 0%, #261a1a 100%);
            border: 1px solid #f2364544;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }

        /* Strategy grid */
        .strategy-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .strategy-card {
            background: #0c0e12;
            border: 1px solid #2a3f5f;
            border-radius: 8px;
            padding: 15px 20px;
        }

        .strategy-card-green {
            background: #00ffad11;
            border: 1px solid #00ffad44;
            border-radius: 8px;
            padding: 15px 20px;
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

        /* HR */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad, transparent);
            margin: 40px 0;
        }

        /* Strong */
        strong {
            color: #00ffad;
            font-weight: bold;
        }

        /* Blockquote */
        blockquote {
            border-left: 3px solid #ff9800;
            margin: 20px 0;
            padding-left: 20px;
            color: #ff9800 !important;
            font-style: italic;
        }

        /* Inline code */
        code {
            background: #1a1e26;
            color: #00ffad;
            padding: 2px 7px;
            border-radius: 3px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.88em;
        }

        /* Blinking cursor */
        .cursor {
            display: inline-block;
            width: 9px;
            height: 16px;
            background: #00ffad;
            animation: blink 1s infinite;
            vertical-align: middle;
            margin-left: 4px;
        }

        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }

        /* Glitch effect — solo para el H1 */
        .glitch {
            position: relative;
            color: #00ffad;
            font-family: 'VT323', monospace !important;
            font-weight: 700;
        }

        .glitch::before,
        .glitch::after {
            content: attr(data-text);
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
        }

        .glitch::before {
            left: 2px;
            text-shadow: -1px 0 #f23645;
            clip: rect(24px, 550px, 90px, 0);
            animation: glitch-1 2.5s infinite linear alternate-reverse;
        }

        .glitch::after {
            left: -2px;
            text-shadow: -1px 0 #00d9ff;
            clip: rect(85px, 550px, 140px, 0);
            animation: glitch-2 2.5s infinite linear alternate-reverse;
        }

        @keyframes glitch-1 {
            0%   { clip: rect(20px, 9999px, 51px, 0); }
            25%  { clip: rect(89px, 9999px, 15px, 0); }
            50%  { clip: rect(10px, 9999px, 82px, 0); }
            75%  { clip: rect(65px, 9999px, 99px, 0); }
            100% { clip: rect(34px, 9999px, 12px, 0); }
        }

        @keyframes glitch-2 {
            0%   { clip: rect(65px, 9999px, 99px, 0); }
            25%  { clip: rect(10px, 9999px, 82px, 0); }
            50%  { clip: rect(89px, 9999px, 15px, 0); }
            75%  { clip: rect(20px, 9999px, 51px, 0); }
            100% { clip: rect(76px, 9999px, 43px, 0); }
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0c0e12; }
        ::-webkit-scrollbar-thumb { background: #1a1e26; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #00ffad; }
    </style>
    """, unsafe_allow_html=True)

    # ── HEADER ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; margin-bottom: 40px;">
        <div style="font-family: 'VT323', monospace; font-size: 1rem; color: #444; margin-bottom: 15px; letter-spacing: 3px;">
            [SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]
        </div>
        <h1 class="glitch" data-text=">> MANIFESTO_RSU.exe" style="font-size: 3.5rem; display:inline-block;">
            >> MANIFESTO_RSU.exe
        </h1>
        <div style="font-family: 'VT323', monospace; color: #00d9ff; font-size: 1.2rem; letter-spacing: 3px; margin-top: 10px;">
            PROTOCOLO DE DESPERTAR DE CLASE // CICLO PERMANENTE<span class="cursor"></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── WARNING ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="risk-box" style="text-align:center;">
        <p style="font-family: 'VT323', monospace; font-size: 1.1rem; color: #f23645; margin: 0; letter-spacing: 2px;">
            ⚠️ ADVERTENCIA DE SEGURIDAD
        </p>
        <p style="margin: 10px 0 0 0; color: #aaa !important;">
            Este documento contiene información clasificada. La lectura puede provocar 
            <strong>despertar de clase</strong>, 
            <span style="color: #ff9800;">síndrome de impostor invertido</span> y 
            <span style="color: #f23645;">deseo irrefrenable de leer gráficos de velas</span>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── SECCIÓN 0 ────────────────────────────────────────────────────────────────
    st.markdown("""
    <h2>00 // LA LENTA CANCELACIÓN DEL FUTURO</h2>

    <div class="terminal-box">
        <p style="color: #fff !important;">
            Vivimos en el <strong>Realismo Capitalista</strong>: la atmósfera mental que nos impide imaginar un final 
            para este sistema que no sea el colapso total. El neoliberalismo no es solo un modelo económico; es una 
            <span style="color: #f23645;">tanatopolítica</span> que nos precariza, nos enferma con ansiedad 
            y luego nos vende el ansiolítico para que sigamos siendo productivos.
        </p>
        <p>
            Nos dijeron que el futuro había muerto. Que el <code>"No Future"</code> punk era una profecía cumplida. 
            Pero mientras nosotros nos hundimos en la nostalgia y la precariedad, las élites siguen operando 
            en una temporalidad distinta.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="highlight-quote-red">
        "Claro que hay una guerra de clases, y es mi clase, la de los ricos,<br>
        la que la está haciendo, y la estamos ganando."<br>
        <span style="font-size: 1rem; color: #ff9800;">— Warren Buffett [TARGET_ACQUIRED]</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="highlight-quote">
        RSU nace para dejar de perder.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── SECCIÓN 1 ────────────────────────────────────────────────────────────────
    st.markdown("""
    <h2>01 // EL MERCADO COMO CAMPO DE BATALLA (Y EXPLOIT)</h2>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("""
        <div class="terminal-box" style="height: 100%;">
            <p style="color: #fff !important;">
                El mercado financiero no es un templo de libertad; es una <strong style="color: #f23645;">picadora de carne</strong> 
                diseñada para extraer valor de la base y concentrarlo en la cúspide.
            </p>
            <p>
                Como señala <span style="color: #ff9800;">Gary Stevenson</span>, la desigualdad no es un error del sistema, 
                es su <strong style="color: #f23645;">función principal</strong>.
            </p>
            <p>
                Mientras la inflación monetaria de <span style="color: #00d9ff;">Jose Luis Cava</span> devora tus ahorros 
                y tu tiempo de vida, las élites operan con información privilegiada y herramientas que tú no tienes.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="risk-box" style="height: 100%;">
            <h4 style="color: #f23645 !important; margin-top: 0;">⚡ VULNERABILIDAD DETECTADA</h4>
            <p>Sin embargo, el mercado posee una vulnerabilidad: <strong>su propia infraestructura</strong>.</p>
            <div class="phase-box" style="margin-top: 15px;">
                <p style="font-family: 'VT323', monospace; color: #00ffad; font-size: 1.1rem; margin: 0; line-height: 1.6;">
                    ▸ El Rastro de la Liquidez<br>
                    ▸ Los gigantes no pueden moverse sin dejar huellas<br>
                    ▸ Sus órdenes alteran el tejido de la realidad gráfica
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="terminal-box" style="border-color: #00ffad; margin-top: 20px;">
        <h3 style="margin-top: 0; color: #00ffad !important;">▸ LA METODOLOGÍA RSU</h3>
        <p>
            No somos inversores pasivos esperando migajas. Somos <strong>hackers del flujo de capital</strong>. 
            Buscamos el rastro de las <code>"manos fuertes"</code>, identificamos sus zonas de manipulación y 
            ejecutamos un <span style="color: #ff9800;">exploit</span> sobre su propia avaricia.
        </p>
        <div class="phase-box-orange" style="margin-top: 15px;">
            <p style="color: #ff9800 !important; font-family: 'VT323', monospace; font-size: 1.1rem; margin: 0;">
                💡 Marx en la Terminal: No olvidemos que el mismo Karl Marx operaba en bolsa para financiar su vida y su obra. 
                Entender el capital no es amarlo; es diseccionarlo para sobrevivir a él.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── SECCIÓN 2 ────────────────────────────────────────────────────────────────
    st.markdown("""
    <h2>02 // MERITOCRACIA RADICAL VS. PRECARIEDAD</h2>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="risk-box" style="height: 100%;">
            <h4 style="color: #f23645 !important; margin-top: 0;">🌍 MUNDO EXTERIOR</h4>
            <p>
                Tu género, tu raza y tu código postal predeterminan tu techo de cristal. 
                El neoliberalismo privatiza tu malestar y te culpa de tu pobreza.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="terminal-box" style="height: 100%; border-color: #00ffad55;">
            <h4 style="margin-top: 0;">💻 TERMINAL RSU</h4>
            <p>
                El gráfico no sabe quién eres. El mercado es un entorno hostil, sí, pero es uno de los pocos 
                lugares donde <strong>el conocimiento técnico y la disciplina pueden superar a la herencia</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; padding: 10px 0; font-family: 'VT323', monospace; font-size: 2rem; color: #00ffad;">⇅</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="phase-box">
            <h4 style="margin-top: 0; color: #00d9ff !important;">🧠 DESPRIVATIZAR LA SALUD MENTAL</h4>
            <p>
                Operar no es una terapia, pero la <strong>libertad financiera</strong> es la única cura real 
                para la ansiedad estructural de la precariedad.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="phase-box-orange">
            <h4 style="margin-top: 0; color: #ff9800 !important;">⚔️ CONSCIENCIA DE CLASE</h4>
            <p>
                Operamos con los ricos, pero no somos como ellos. No buscamos la explotación del prójimo, 
                sino la <span style="color: #ff9800;">extracción de liquidez</span> de un sistema amañado 
                que lleva décadas robándonos el futuro.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── SECCIÓN 3 ────────────────────────────────────────────────────────────────
    st.markdown("""
    <h2>03 // EL CÓDIGO DE RSU</h2>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="strategy-grid">
        <div class="strategy-card">
            <h4>01. SEGUIR EL RASTRO</h4>
            <p>
                Donde hay manipulación, hay oportunidad. No operamos contra el mercado, operamos contra 
                <span style="color: #f23645;">la ilusión que el mercado crea para las masas</span>.
            </p>
        </div>
        <div class="strategy-card">
            <h4>02. SOLIDARIDAD TÉCNICA</h4>
            <p>
                El conocimiento bursátil ha sido propiedad exclusiva de las clases dominantes. 
                RSU democratiza el acceso a la <code>"caja negra"</code> del trading profesional.
            </p>
        </div>
        <div class="strategy-card">
            <h4>03. REALISMO OPERATIVO</h4>
            <p>
                Aceptamos que el capitalismo es una estructura impersonal y abstracta. Para destruirla o escapar de ella, 
                primero debemos <span style="color: #ff9800;">dominar su lenguaje</span>: el precio y el tiempo.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── CONCLUSIÓN ───────────────────────────────────────────────────────────────
    st.markdown("""
    <h2>🔚 CONCLUSIÓN: HACKEA EL DESEO, RECLAMA EL TIEMPO</h2>

    <div class="terminal-box" style="border-color: #00ffad;">
        <p style="color: #fff !important; font-size: 1.05rem;">
            El neoliberalismo controla tus deseos para que desees rendir. <strong>RSU hackea ese deseo</strong>. 
            No queremos Lamborghinis; queremos <span style="color: #ff9800;">nuestro tiempo de vuelta</span>. 
            Queremos la soberanía que nos fue arrebatada.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="highlight-quote-red" style="font-size: 1.15rem; line-height: 1.8;">
        Si la guerra de clases es real, el gráfico es nuestro mapa de guerra.<br>
        Si ellos ganan porque tienen la información, nosotros ganaremos porque sabemos leer su rastro.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="strategy-grid" style="margin-top: 30px;">
        <div class="strategy-card-green">
            <h4 style="text-align: center; margin: 0;">HACKEA EL DESEO</h4>
        </div>
        <div class="strategy-card-green">
            <h4 style="text-align: center; margin: 0;">RECLAMA EL TIEMPO</h4>
        </div>
        <div class="strategy-card-green">
            <h4 style="text-align: center; margin: 0;">LEE EL RASTRO</h4>
        </div>
        <div class="strategy-card-green">
            <h4 style="text-align: center; margin: 0;">EJECUTA</h4>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="highlight-quote" style="margin-top: 30px; font-size: 1.5rem; letter-spacing: 3px;">
        BIENVENIDOS A RSU<br>
        <span style="font-size: 1.1rem; color: #f23645;">El exploit ha comenzado<span class="cursor"></span></span>
    </div>
    """, unsafe_allow_html=True)

    # ── FOOTER ───────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; margin-top: 50px; padding: 20px; border-top: 1px solid #1a1e26;">
        <p style="font-family: 'VT323', monospace; color: #444; font-size: 0.9rem; margin: 0;">
            [END OF TRANSMISSION // MANIFEST_RSU_v1.0]<br>
            [TIMESTAMP: PERMANENTE]<br>
            [LICENSE: COPYLEFT // STATUS: ACTIVE]
        </p>
    </div>
    """, unsafe_allow_html=True)
