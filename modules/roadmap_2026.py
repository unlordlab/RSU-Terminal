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

        h4 {
            font-size: 1.5rem !important;
            color: #9c27b0 !important;
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

        .strategy-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .strategy-card {
            background: #0c0e12;
            border: 1px solid #2a3f5f;
            border-radius: 8px;
            padding: 15px;
        }

        .strategy-card h4 {
            color: #00ffad !important;
            font-size: 1.1rem !important;
            margin-bottom: 10px;
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

        /* Blockquote styling */
        blockquote {
            border-left: 3px solid #ff9800;
            margin: 20px 0;
            padding-left: 20px;
            color: #ff9800;
            font-style: italic;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header Section
    st.markdown("""
    <div style="text-align:center; margin-bottom:40px;">
        <div style="font-family: 'VT323', monospace; font-size: 1rem; color: #666; margin-bottom: 10px;">
            [SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]
        </div>
        <h1>🗺️ 2026 ROADMAP</h1>
        <div style="font-family: 'VT323', monospace; color: #00d9ff; font-size: 1.2rem; letter-spacing: 3px;">
            PROTOCOLO DE NAVEGACIÓN ESTRATÉGICA // CICLO 2026
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Introduction
    st.markdown("""
    <div class="terminal-box">
        <p style="font-size: 1.05rem; color: #fff !important;">
            Cuando pienso en 2026 no veo un año lineal. No veo una tendencia limpia ni un mercado que simplemente continúe lo iniciado en 2025. Lo que visualizo es un año con <strong>fases muy definidas</strong>, con tensión política creciente, con volatilidad cíclica marcada y, sobre todo, con una <strong>ventana táctica extremadamente importante en primavera</strong>.
        </p>
        <p>
            Mi escenario base no es euforia constante ni colapso estructural. Es algo mucho más interesante: <strong>un año de correcciones estratégicas dentro de una estructura macro todavía funcional</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 1: Midterms Context
    st.markdown("""
    <h2>01 // EL CONTEXTO QUE LO CONDICIONA TODO: AÑO DE MIDTERMS</h2>

    <p>2026 es un año de elecciones intermedias en EE.UU., y eso importa mucho más de lo que el inversor promedio cree.</p>

    <p>Históricamente, los años de midterms tienden a tener:</p>
    <ul>
        <li>Volatilidad superior a la media</li>
        <li>Correcciones significativas en la primera mitad del año</li>
        <li>Recuperaciones importantes hacia la segunda mitad</li>
        <li>Un cierre de año generalmente constructivo</li>
    </ul>

    <p>No es casualidad. Es política. Y la política impacta liquidez, narrativa y percepción económica.</p>

    <div class="highlight-quote">
        "El mercado no es solo descuento de flujos futuros. Es también un termómetro psicológico. 
        Y ningún gobierno quiere llegar a noviembre con mercados deprimidos."
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 2: Base Scenario
    st.markdown("""
    <h2>02 // MI ESCENARIO BASE PARA 2026 (ESTRUCTURA TEMPORAL)</h2>

    <p>Si tuviera que dibujar la película del año, sería algo así:</p>

    <h3>Fase 1: Inicio relativamente constructivo (enero–febrero)</h3>
    <div class="phase-box">
        <ul>
            <li>Comienzo de año con inercia positiva</li>
            <li>Liquidez todavía presente</li>
            <li>Sentimiento moderadamente optimista</li>
        </ul>
        <p>Nada extremo, pero tampoco debilidad clara.</p>
        <p style="color: #ff9800 !important;">Sin embargo, debajo de la superficie empieza a acumularse desgaste:</p>
        <ul>
            <li>Valoraciones exigentes en algunos sectores</li>
            <li>Posicionamiento cargado</li>
            <li>Narrativas muy consensuadas</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 3: Spring Drop
    st.markdown("""
    <h2>03 // LA CAÍDA DE PRIMAVERA: EL NÚCLEO TÁCTICO DEL AÑO</h2>

    <p>Mi escenario base incluye una <strong>corrección clara entre marzo y mayo</strong>.</p>

    <div class="highlight-quote" style="border-color: #f23645; color: #f23645;">
        No como posibilidad remota. Como elemento central del año.
    </div>

    <h3>¿Por qué primavera?</h3>
    <p>Porque ahí confluyen varios factores:</p>
    <ul>
        <li>Ajustes de expectativas macro</li>
        <li>Repricing de política monetaria</li>
        <li>Ruido político creciente</li>
        <li>Fatiga tras el impulso inicial del año</li>
        <li>Liquidez más irregular</li>
    </ul>

    <p>En años de midterms, esta fase suele concentrar la debilidad más incómoda.</p>

    <h3>¿Qué magnitud espero?</h3>
    <div class="terminal-box" style="border-color: #ff9800;">
        <p style="color: #fff !important;">No hablo de crisis financiera. No estoy proyectando un colapso sistémico.</p>
        <p>Estoy pensando en:</p>
        <ul>
            <li>Correcciones del <strong>8% al 15%</strong> en índices principales</li>
            <li>Más daño en sectores especulativos</li>
            <li>Limpieza fuerte en activos sobreextendidos</li>
            <li>Volatilidad disparándose temporalmente</li>
            <li>Titulares alarmistas</li>
            <li>Narrativa de "el ciclo se acabó"</li>
        </ul>
        <p style="color: #00ffad !important; font-size: 1.1rem; margin-top: 15px;">
            Lo suficiente para generar miedo real. Pero no lo suficiente para romper la estructura macro.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 4: Why Buyable
    st.markdown("""
    <h2>04 // ¿POR QUÉ CREO QUE SERÍA COMPRABLE?</h2>

    <p>Aquí entra el componente político y fiscal.</p>

    <p>En año electoral, el incentivo para sostener el sentimiento económico es altísimo. Si los mercados corrigen de forma significativa en primavera, aumenta la probabilidad de:</p>
    <ul>
        <li>Tono más acomodaticio desde autoridades</li>
        <li>Señales de apoyo fiscal</li>
        <li>Narrativa de estabilidad</li>
        <li>Expectativas de política monetaria menos restrictiva</li>
    </ul>

    <p>No necesito estímulos masivos. Solo necesito que el mercado perciba que el riesgo de endurecimiento extremo desaparece.</p>

    <div class="strategy-grid">
        <div class="strategy-card">
            <h4>❌ NO ES</h4>
            <p style="color: #f23645;">"Si cae, salgo corriendo"</p>
        </div>
        <div class="strategy-card">
            <h4>✅ ES</h4>
            <p style="color: #00ffad;">"Si cae según el patrón esperado, empiezo a escalar riesgo"</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 5: Preparation
    st.markdown("""
    <h2>05 // CÓMO ME PREPARO PARA ESA VENTANA</h2>

    <p>La caída de primavera no se improvisa. Se planifica antes.</p>

    <h3>Liquidez estratégica</h3>
    <div class="phase-box">
        <p>No quiero llegar a marzo completamente invertido si veo extensión excesiva en febrero.</p>
        <p style="color: #00ffad;">Mantener munición seca es parte del plan.</p>
    </div>

    <h3>Lista definida antes de la corrección</h3>
    <p>No decido qué comprar cuando todo está rojo. Ya lo tengo decidido:</p>
    <div class="strategy-grid">
        <div class="strategy-card">
            <h4>⚡ INFRAESTRUCTURA ENERGÉTICA</h4>
        </div>
        <div class="strategy-card">
            <h4>🔌 REDES ELÉCTRICAS Y TRANSICIÓN</h4>
        </div>
        <div class="strategy-card">
            <h4>💻 SEMICONDUCTORES REALES</h4>
        </div>
        <div class="strategy-card">
            <h4>⛏️ METALES INDUSTRIALES ESTRATÉGICOS</h4>
        </div>
        <div class="strategy-card">
            <h4>📈 ACTIVOS DE BETA ELEVADA</h4>
        </div>
    </div>

    <h3>Escalonamiento progresivo</h3>
    <p>No intento adivinar el mínimo exacto. Escalo posiciones cuando:</p>
    <ul>
        <li>Se rompen estructuras técnicas clave</li>
        <li>El sentimiento alcanza extremos negativos</li>
        <li>La volatilidad se expande de forma emocional</li>
        <li>El posicionamiento se limpia</li>
    </ul>

    <div class="highlight-quote" style="background: #00ffad22;">
        La primavera es mi momento de acumulación estratégica.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 6: Second Half
    st.markdown("""
    <h2>06 // EL SEGUNDO SEMESTRE: RECUPERACIÓN Y TRAMO FUERTE</h2>

    <p>Si el patrón se cumple, la segunda mitad del año cambia completamente el tono.</p>

    <p>A medida que se acercan las elecciones:</p>
    <ul>
        <li>Disminuye la incertidumbre</li>
        <li>Aumenta el apoyo narrativo</li>
        <li>Se estabilizan expectativas</li>
        <li>El mercado anticipa menor riesgo político</li>
    </ul>

    <p>Históricamente, tras la fase de debilidad pre-midterm, el mercado suele entrar en tramo constructivo.</p>

    <div class="terminal-box">
        <h4 style="color: #00ffad !important; margin-top: 0;">MI ESCENARIO BASE CONTEMPLA:</h4>
        <ul>
            <li>Rebote fuerte tras la caída primaveral</li>
            <li>Posible recuperación en V si la corrección fue intensa</li>
            <li>Rotación hacia sectores con fundamentos sólidos</li>
            <li>Mejor comportamiento relativo de activos de riesgo</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 7: Fiscal Policy
    st.markdown("""
    <h2>07 // POLÍTICA FISCAL: "RUN IT HOT"</h2>

    <p>No espero austeridad agresiva.</p>

    <p>Mi lectura es que veremos voluntad de mantener la economía caliente:</p>
    <ul>
        <li>Gasto público elevado</li>
        <li>Proyectos de infraestructura</li>
        <li>Incentivos industriales</li>
        <li>Apoyo indirecto a mercados a través de narrativa y liquidez</li>
    </ul>

    <p>No necesariamente expansión descontrolada, pero sí <strong>ausencia de contracción fuerte</strong>.</p>

    <div class="highlight-quote">
        Eso limita el riesgo de recesión profunda en mi escenario base.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 8: Monetary Policy
    st.markdown("""
    <h2>08 // POLÍTICA MONETARIA</h2>

    <p>No espero un endurecimiento extremo.</p>

    <p>Si la inflación se mantiene contenida o moderándose, el margen para mantener tasas estables o incluso suavizar existe.</p>

    <p>Y en contexto electoral, ese margen se vuelve políticamente conveniente.</p>

    <div class="phase-box">
        <p style="color: #fff !important;">Para activos de riesgo, eso es relevante.</p>
        <p>No necesito recortes agresivos. <strong>Necesito que el miedo a subidas adicionales desaparezca.</strong></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 9: Dollar and Inflation
    st.markdown("""
    <h2>09 // EL DÓLAR Y LA INFLACIÓN</h2>

    <p>No veo un colapso del dólar. Tampoco una fortaleza explosiva sostenida.</p>

    <p>Probablemente comportamiento mixto:</p>
    <ul>
        <li>Fortaleza temporal en momentos de estrés</li>
        <li>Debilidad relativa cuando mejora el apetito por riesgo</li>
    </ul>

    <p>En cuanto a inflación, espero un canal moderado. Lo suficiente para no forzar políticas restrictivas extremas, pero sin volver al pánico inflacionario.</p>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 10: Commodities
    st.markdown("""
    <h2>10 // COMMODITIES Y ACTIVOS REALES</h2>

    <p>2026 puede favorecer activos reales en determinados momentos:</p>

    <div class="strategy-grid">
        <div class="strategy-card">
            <h4>🥇 ORO</h4>
            <p>Cobertura ante incertidumbre</p>
        </div>
        <div class="strategy-card">
            <h4>🔩 METALES INDUSTRIALES</h4>
            <p>Ligados a infraestructura</p>
        </div>
        <div class="strategy-card">
            <h4>⛽ ENERGÍA TRADICIONAL</h4>
            <p>Sensible a tensiones geopolíticas</p>
        </div>
        <div class="strategy-card">
            <h4>🔗 CADENAS DE SUMINISTRO</h4>
            <p>Activos estratégicos</p>
        </div>
    </div>

    <p>No veo un superciclo explosivo automático, pero sí <strong>oportunidades tácticas claras</strong>.</p>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 11: Technology
    st.markdown("""
    <h2>11 // TECNOLOGÍA E INTELIGENCIA ARTIFICIAL</h2>

    <p>No etiqueto automáticamente el sector como burbuja.</p>

    <p>Sí veo sobreextensiones en ciertos nombres. Pero también veo transformación estructural real.</p>

    <div class="risk-box">
        <h4 style="color: #ff9800 !important; margin-top: 0;">⚠️ EL RIESGO ESTÁ EN PAGAR CUALQUIER PRECIO</h4>
        <p style="color: #00ffad !important;">La oportunidad está en seleccionar modelos de negocio con adopción tangible.</p>
    </div>

    <p>En la caída de primavera, probablemente muchos nombres tecnológicos sufran más que el índice. Y ahí puede haber oportunidades si la estructura fundamental es sólida.</p>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Section 12: Risks
    st.markdown("""
    <h2>12 // RIESGOS QUE PODRÍAN INVALIDAR MI ESCENARIO</h2>

    <p>Siempre tengo presente qué podría romper esta tesis:</p>

    <div class="risk-box">
        <ul>
            <li>Repunte inflacionario inesperado</li>
            <li>Política monetaria volviéndose agresiva otra vez</li>
            <li>Evento geopolítico estructural</li>
            <li>Recesión profunda no anticipada</li>
        </ul>
    </div>

    <div class="highlight-quote" style="border-color: #f23645; color: #f23645;">
        Si la caída de primavera viniera acompañada de deterioro macro estructural, entonces no sería corrección táctica, sería cambio de régimen.
    </div>

    <p>Pero ese no es mi escenario base.</p>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Conclusion
    st.markdown("""
    <h2>🔚 CONCLUSIÓN: 2026 COMO AÑO DE PREPARACIÓN Y EJECUCIÓN</h2>

    <p>Mi mapa mental para 2026 es claro:</p>

    <div class="terminal-box" style="border-color: #00ffad;">
        <ul>
            <li>Inicio razonablemente estable</li>
            <li>Corrección relevante en primavera</li>
            <li>Ventana estratégica de acumulación</li>
            <li>Recuperación progresiva hacia segunda mitad</li>
            <li>Cierre de año constructivo si el patrón electoral se mantiene</li>
        </ul>
    </div>

    <p>No espero un año cómodo. <strong>Espero un año exigente.</strong></p>

    <p>Pero precisamente por eso, potencialmente muy rentable para quien entienda el timing de la volatilidad.</p>

    <div class="strategy-grid" style="margin-top: 30px;">
        <div class="strategy-card" style="border-color: #00ffad; background: #00ffad11;">
            <h4 style="color: #00ffad !important;">NO TEMO LA CAÍDA DE PRIMAVERA</h4>
        </div>
        <div class="strategy-card" style="border-color: #00ffad; background: #00ffad11;">
            <h4 style="color: #00ffad !important;">LA ESPERO</h4>
        </div>
        <div class="strategy-card" style="border-color: #00ffad; background: #00ffad11;">
            <h4 style="color: #00ffad !important;">LA PLANIFICO</h4>
        </div>
        <div class="strategy-card" style="border-color: #00ffad; background: #00ffad11;">
            <h4 style="color: #00ffad !important;">LA QUIERO</h4>
        </div>
    </div>

    <div class="highlight-quote" style="margin-top: 30px; font-size: 1.3rem;">
        Porque en mi escenario base, no es el inicio del problema.<br><br>
        <span style="color: #00ffad; font-size: 1.5rem;">Es la oportunidad del año.</span>
    </div>

    <div style="text-align:center; margin-top: 50px; padding: 20px; border-top: 1px solid #1a1e26;">
        <p style="font-family: 'VT323', monospace; color: #666; font-size: 0.9rem;">
            [END OF TRANSMISSION // ROADMAP_2026_v1.0]<br>
            [TIMESTAMP: 2026-01-01T00:00:00Z]<br>
            [STATUS: ACTIVE]
        </p>
    </div>
    """, unsafe_allow_html=True)

