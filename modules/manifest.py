# modules/manifest.py
import streamlit as st

def render():
    # CSS Global para estética hacker/terminal
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
        
        .stApp { 
            background: #0c0e12; 
            font-family: 'JetBrains Mono', monospace;
        }
        
        /* Glitch effect para títulos */
        .glitch {
            position: relative;
            color: #00ffad;
            font-family: 'Fira Code', monospace;
            font-weight: 700;
            letter-spacing: -1px;
        }
        
        .glitch::before,
        .glitch::after {
            content: attr(data-text);
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
        
        .glitch::before {
            left: 2px;
            text-shadow: -1px 0 #f23645;
            clip: rect(24px, 550px, 90px, 0);
            animation: glitch-anim-1 2s infinite linear alternate-reverse;
        }
        
        .glitch::after {
            left: -2px;
            text-shadow: -1px 0 #00d9ff;
            clip: rect(85px, 550px, 140px, 0);
            animation: glitch-anim-2 2s infinite linear alternate-reverse;
        }
        
        @keyframes glitch-anim-1 {
            0% { clip: rect(20px, 9999px, 51px, 0); }
            20% { clip: rect(89px, 9999px, 15px, 0); }
            40% { clip: rect(10px, 9999px, 82px, 0); }
            60% { clip: rect(65px, 9999px, 99px, 0); }
            80% { clip: rect(34px, 9999px, 12px, 0); }
            100% { clip: rect(76px, 9999px, 43px, 0); }
        }
        
        @keyframes glitch-anim-2 {
            0% { clip: rect(65px, 9999px, 99px, 0); }
            20% { clip: rect(10px, 9999px, 82px, 0); }
            40% { clip: rect(89px, 9999px, 15px, 0); }
            60% { clip: rect(20px, 9999px, 51px, 0); }
            80% { clip: rect(76px, 9999px, 43px, 0); }
            100% { clip: rect(34px, 9999px, 12px, 0); }
        }
        
        /* Terminal window styling */
        .terminal-window {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            margin: 20px 0;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(0, 255, 173, 0.1);
        }
        
        .terminal-header {
            background: #1a1e26;
            padding: 8px 15px;
            border-bottom: 1px solid #2a3f5f;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .terminal-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        
        .terminal-dot.red { background: #f23645; }
        .terminal-dot.yellow { background: #ff9800; }
        .terminal-dot.green { background: #00ffad; }
        
        .terminal-title {
            color: #888;
            font-size: 11px;
            margin-left: 10px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .terminal-content {
            padding: 25px;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1.8;
        }
        
        /* Section headers */
        .section-header {
            background: linear-gradient(90deg, #00ffad22 0%, transparent 100%);
            border-left: 3px solid #00ffad;
            padding: 15px 20px;
            margin: 30px 0 20px 0;
            font-family: 'Fira Code', monospace;
            font-weight: 700;
            color: #00ffad;
            font-size: 1.2rem;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        /* Quote blocks */
        .quote-block {
            background: #1a1e26;
            border-left: 3px solid #f23645;
            padding: 20px;
            margin: 20px 0;
            font-style: italic;
            color: #ccc;
            position: relative;
        }
        
        .quote-block::before {
            content: '"';
            position: absolute;
            top: -10px;
            left: 15px;
            font-size: 40px;
            color: #f23645;
            font-family: serif;
        }
        
        .quote-author {
            color: #ff9800;
            font-size: 0.85rem;
            margin-top: 10px;
            text-align: right;
            font-family: 'JetBrains Mono', monospace;
        }
        
        /* Code blocks inline */
        code {
            background: #1a1e26;
            color: #00ffad;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Fira Code', monospace;
            font-size: 0.9em;
        }
        
        /* Warning boxes */
        .warning-box {
            background: linear-gradient(135deg, #1a0f0f 0%, #261a1a 100%);
            border: 1px solid #f23645;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .warning-box h4 {
            color: #f23645;
            margin: 0 0 10px 0;
            font-family: 'Fira Code', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Highlight text */
        .highlight-red { color: #f23645; font-weight: bold; }
        .highlight-green { color: #00ffad; font-weight: bold; }
        .highlight-orange { color: #ff9800; font-weight: bold; }
        .highlight-blue { color: #00d9ff; font-weight: bold; }
        
        /* Blinking cursor */
        .cursor {
            display: inline-block;
            width: 10px;
            height: 18px;
            background: #00ffad;
            animation: blink 1s infinite;
            vertical-align: middle;
            margin-left: 5px;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        /* Matrix rain effect container */
        .matrix-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
            opacity: 0.03;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0c0e12;
        }
        ::-webkit-scrollbar-thumb {
            background: #1a1e26;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #00ffad;
        }
        
        /* Typing effect */
        .typing {
            overflow: hidden;
            white-space: nowrap;
            border-right: 2px solid #00ffad;
            animation: typing 3s steps(40, end), blink-caret 0.75s step-end infinite;
        }
        
        @keyframes typing {
            from { width: 0 }
            to { width: 100% }
        }
        
        @keyframes blink-caret {
            from, to { border-color: transparent }
            50% { border-color: #00ffad }
        }
        
        /* Section divider */
        .section-divider {
            text-align: center;
            margin: 40px 0;
            color: #1a1e26;
            font-family: 'Fira Code', monospace;
            letter-spacing: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header con glitch effect
    st.markdown("""
    <div style="text-align: center; margin: -50px 0 40px 0;">
        <h1 class="glitch" data-text=">> MANIFESTO_RSU.exe" style="font-size: 3rem; margin-bottom: 10px;">
            >> MANIFESTO_RSU.exe
        </h1>
        <p style="color: #666; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;">
            <span class="highlight-green">root@rsu-terminal</span>:<span class="highlight-blue">~/manifest</span># cat MANIFESTO.txt<span class="cursor"></span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Warning inicial
    st.markdown("""
    <div class="warning-box">
        <h4>⚠️ ADVERTENCIA DE SEGURIDAD</h4>
        <p style="color: #aaa; margin: 0; font-size: 0.9rem;">
            Este documento contiene información clasificada. La lectura puede provocar 
            <span class="highlight-green">despertar de clase</span>, 
            <span class="highlight-orange">síndrome de impostor invertido</span> y 
            <span class="highlight-red">deseo irrefrenable de leer gráficos de velas</span>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # SECCIÓN 0
    st.markdown("""
    <div class="section-header">
        0. LA LENTA CANCELACIÓN DEL FUTURO
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="terminal-window">
        <div class="terminal-header">
            <div class="terminal-dot red"></div>
            <div class="terminal-dot yellow"></div>
            <div class="terminal-dot green"></div>
            <span class="terminal-title">realismo_capitalista.log</span>
        </div>
        <div class="terminal-content">
            <p style="color: #ccc; margin: 0;">
                Vivimos en el <span class="highlight-red">Realismo Capitalista</span>: la atmósfera mental que nos impide imaginar un final para este sistema que no sea el colapso total. El neoliberalismo no es solo un modelo económico; es una <span class="highlight-orange">tanatopolítica</span> que nos precariza, nos enferma con ansiedad y luego nos vende el ansiolítico para que sigamos siendo productivos.
            </p>
            <br>
            <p style="color: #ccc; margin: 0;">
                Nos dijeron que el futuro había muerto. Que el <code>"No Future"</code> punk era una profecía cumplida. Pero mientras nosotros nos hundimos en la nostalgia y la precariedad, las élites siguen operando en una temporalidad distinta.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quote de Buffett
    st.markdown("""
    <div class="quote-block">
        <p style="margin-left: 30px; margin-top: 10px;">
            Claro que hay una guerra de clases, y es mi clase, la de los ricos, la que la está haciendo, y la estamos ganando.
        </p>
        <div class="quote-author">— Warren Buffett [TARGET_ACQUIRED]</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #0c0e12; border: 1px solid #00ffad; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
        <span style="color: #00ffad; font-family: 'Fira Code', monospace; font-size: 1.3rem; font-weight: bold;">
            RSU nace para dejar de perder.
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # SECCIÓN 1
    st.markdown('<div class="section-divider">▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="section-header">
        1. EL MERCADO COMO CAMPO DE BATALLA (Y EXPLOIT)
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        <div class="terminal-window" style="height: 100%;">
            <div class="terminal-header">
                <div class="terminal-dot red"></div>
                <div class="terminal-dot yellow"></div>
                <div class="terminal-dot green"></div>
                <span class="terminal-title">sistema.picadora</span>
            </div>
            <div class="terminal-content">
                <p style="color: #ccc;">
                    El mercado financiero no es un templo de libertad; es una <span class="highlight-red">picadora de carne</span> diseñada para extraer valor de la base y concentrarlo en la cúspide.
                </p>
                <br>
                <p style="color: #888; font-size: 0.85rem;">
                    Como señala <span class="highlight-orange">Gary Stevenson</span>, la desigualdad no es un error del sistema, es su <span class="highlight-red">función principal</span>.
                </p>
                <br>
                <p style="color: #ccc;">
                    Mientras la inflación monetaria de <span class="highlight-blue">Jose Luis Cava</span> devora tus ahorros y tu tiempo de vida, las élites operan con información privilegiada y herramientas que tú no tienes.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #1a1e26; border: 1px solid #f23645; border-radius: 8px; padding: 20px; height: 100%;">
            <h4 style="color: #f23645; font-family: 'Fira Code', monospace; margin-top: 0;">
                ⚡ VULNERABILIDAD DETECTADA
            </h4>
            <p style="color: #ccc; font-size: 0.9rem;">
                Sin embargo, el mercado posee una vulnerabilidad: <span class="highlight-green">su propia infraestructura</span>.
            </p>
            <br>
            <div style="background: #0c0e12; padding: 15px; border-radius: 5px; border-left: 2px solid #00ffad;">
                <p style="color: #00ffad; font-family: 'Fira Code', monospace; font-size: 0.8rem; margin: 0;">
                    > El Rastro de la Liquidez<br>
                    > Los gigantes no pueden moverse sin dejar huellas<br>
                    > Sus órdenes alteran el tejido de la realidad gráfica
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Metodología RSU
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #00ffad; border-radius: 10px; padding: 25px; margin: 30px 0; position: relative; overflow: hidden;">
        <div style="position: absolute; top: -20px; right: -20px; width: 100px; height: 100px; background: #00ffad; opacity: 0.05; border-radius: 50%;"></div>
        
        <h3 style="color: #00ffad; font-family: 'Fira Code', monospace; margin-top: 0;">
            > LA METODOLOGÍA RSU
        </h3>
        
        <p style="color: #ccc; line-height: 1.8;">
            No somos inversores pasivos esperando migajas. Somos <span class="highlight-green">hackers del flujo de capital</span>. 
            Buscamos el rastro de las <code>"manos fuertes"</code>, identificamos sus zonas de manipulación y 
            ejecutamos un <span class="highlight-orange">exploit</span> sobre su propia avaricia.
        </p>
        
        <div style="margin-top: 20px; padding: 15px; background: #0c0e12; border-radius: 5px; border-left: 3px solid #ff9800;">
            <p style="color: #ff9800; font-family: 'Fira Code', monospace; font-size: 0.9rem; margin: 0;">
                💡 Marx en la Terminal: No olvidemos que el mismo Karl Marx operaba en bolsa para financiar su vida y su obra. 
                Entender el capital no es amarlo; es diseccionarlo para sobrevivir a él.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # SECCIÓN 2
    st.markdown('<div class="section-divider">▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="section-header">
        2. MERITOCRACIA RADICAL VS. PRECARIEDAD
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="display: grid; gap: 20px;">
        <div style="background: #1a1e26; border: 1px solid #f23645; border-radius: 8px; padding: 20px;">
            <h4 style="color: #f23645; font-family: 'Fira Code', monospace; margin-top: 0;">🌍 MUNDO EXTERIOR</h4>
            <p style="color: #aaa; margin: 0;">
                Tu género, tu raza y tu código postal predeterminan tu techo de cristal. 
                El neoliberalismo privatiza tu malestar y te culpa de tu pobreza.
            </p>
        </div>
        
        <div style="text-align: center; color: #00ffad; font-size: 2rem;">⇅</div>
        
        <div style="background: #0c0e12; border: 1px solid #00ffad; border-radius: 8px; padding: 20px; box-shadow: 0 0 20px rgba(0, 255, 173, 0.1);">
            <h4 style="color: #00ffad; font-family: 'Fira Code', monospace; margin-top: 0;">💻 TERMINAL RSU</h4>
            <p style="color: #ccc; margin: 0;">
                El gráfico no sabe quién eres. El mercado es un entorno hostil, sí, pero es uno de los pocos lugares donde 
                <span class="highlight-green">el conocimiento técnico y la disciplina pueden superar a la herencia</span>.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: #1a1e26; border-radius: 8px; padding: 20px; height: 100%; border-top: 3px solid #00d9ff;">
            <h4 style="color: #00d9ff; font-family: 'Fira Code', monospace; font-size: 0.9rem;">
                🧠 DESPRIVATIZAR LA SALUD MENTAL
            </h4>
            <p style="color: #aaa; font-size: 0.9rem; line-height: 1.6;">
                Operar no es una terapia, pero la <span class="highlight-green">libertad financiera</span> es la única cura real 
                para la ansiedad estructural de la precariedad.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #1a1e26; border-radius: 8px; padding: 20px; height: 100%; border-top: 3px solid #ff9800;">
            <h4 style="color: #ff9800; font-family: 'Fira Code', monospace; font-size: 0.9rem;">
                ⚔️ CONSCIENCIA DE CLASE
            </h4>
            <p style="color: #aaa; font-size: 0.9rem; line-height: 1.6;">
                Operamos con los ricos, pero no somos como ellos. No buscamos la explotación del prójimo, sino la 
                <span class="highlight-orange">extracción de liquidez</span> de un sistema amañado que lleva décadas robándonos el futuro.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # SECCIÓN 3
    st.markdown('<div class="section-divider">▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="section-header">
        3. EL CÓDIGO DE RSU
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="terminal-window">
        <div class="terminal-header">
            <div class="terminal-dot red"></div>
            <div class="terminal-dot yellow"></div>
            <div class="terminal-dot green"></div>
            <span class="terminal-title">protocolos.rsu</span>
        </div>
        <div class="terminal-content">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="margin-bottom: 20px;">
            <h4 style="color: #00ffad; font-family: 'Fira Code', monospace; font-size: 0.9rem; margin-bottom: 10px;">
                01. SEGUIR EL RASTRO
            </h4>
            <p style="color: #888; font-size: 0.85rem; margin: 0;">
                Donde hay manipulación, hay oportunidad. No operamos contra el mercado, operamos contra 
                <span style="color: #f23645;">la ilusión que el mercado crea para las masas</span>.
            </p>
        </div>
        
        <div style="margin-bottom: 20px;">
            <h4 style="color: #00d9ff; font-family: 'Fira Code', monospace; font-size: 0.9rem; margin-bottom: 10px;">
                02. SOLIDARIDAD TÉCNICA
            </h4>
            <p style="color: #888; font-size: 0.85rem; margin: 0;">
                El conocimiento bursátil ha sido propiedad exclusiva de las clases dominantes. 
                RSU democratiza el acceso a la <span style="color: #00ffad;">"caja negra"</span> del trading profesional.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="margin-bottom: 20px;">
            <h4 style="color: #ff9800; font-family: 'Fira Code', monospace; font-size: 0.9rem; margin-bottom: 10px;">
                03. REALISMO OPERATIVO
            </h4>
            <p style="color: #888; font-size: 0.85rem; margin: 0;">
                Aceptamos que el capitalismo es una estructura impersonal y abstracta. Para destruirla o escapar de ella, 
                primero debemos <span style="color: #ff9800;">dominar su lenguaje</span>: el precio y el tiempo.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # CONCLUSIÓN
    st.markdown('<div class="section-divider">▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 50%, #0c0e12 100%); 
                border: 2px solid #00ffad; border-radius: 15px; padding: 40px; margin: 40px 0; 
                text-align: center; position: relative; overflow: hidden;">
        
        <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; 
                    background: linear-gradient(90deg, #f23645, #ff9800, #00ffad, #00d9ff, #f23645);">
        </div>
        
        <h2 style="color: #00ffad; font-family: 'Fira Code', monospace; font-size: 1.5rem; 
                   margin-bottom: 30px; text-transform: uppercase; letter-spacing: 3px;">
            Conclusión: Hackea el Deseo, Reclama el Tiempo
        </h2>
        
        <p style="color: #ccc; font-size: 1.1rem; line-height: 1.8; max-width: 800px; margin: 0 auto 30px auto;">
            El neoliberalismo controla tus deseos para que desees rendir. <span class="highlight-green">RSU hackea ese deseo</span>. 
            No queremos Lamborghinis; queremos <span class="highlight-orange">nuestro tiempo de vuelta</span>. 
            Queremos la soberanía que nos fue arrebatada.
        </p>
        
        <div style="background: #0c0e12; border-left: 3px solid #f23645; border-right: 3px solid #f23645; 
                    padding: 20px; margin: 30px 0; display: inline-block;">
            <p style="color: #fff; font-family: 'Fira Code', monospace; font-size: 1rem; margin: 0; font-weight: bold;">
                Si la guerra de clases es real, el gráfico es nuestro mapa de guerra.<br>
                Si ellos ganan porque tienen la información, nosotros ganaremos porque sabemos leer su rastro.
            </p>
        </div>
        
        <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid #1a1e26;">
            <p style="color: #00ffad; font-family: 'Fira Code', monospace; font-size: 1.3rem; 
                      font-weight: bold; letter-spacing: 5px; margin: 0;">
                BIENVENIDOS A RSU
            </p>
            <p style="color: #f23645; font-family: 'Fira Code', monospace; font-size: 0.9rem; 
                      margin-top: 10px; text-transform: uppercase;">
                El exploit ha comenzado<span class="cursor"></span>
            </p>
        </div>
        
        <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 3px; 
                    background: linear-gradient(90deg, #f23645, #ff9800, #00ffad, #00d9ff, #f23645);">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer con versión
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; padding: 20px; border-top: 1px solid #1a1e26;">
        <p style="color: #444; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; margin: 0;">
            RSU TERMINAL v1.0.0 | BUILD: 2024-02-12 | LICENSE: COPYLEFT<br>
            <span style="color: #333;">"El mercado es el opio del pueblo, pero también su metadona"</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
