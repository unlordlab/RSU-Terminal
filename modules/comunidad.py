import streamlit as st

DISCORD_URL = "https://discord.gg/8BZDAXAx"
TELEGRAM_URL = "https://t.me/TU_CANAL"
FORMSPREE_ID = "meelqyyb"

def render():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp {
            background: #0c0e12;
        }

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

        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad, transparent);
            margin: 40px 0;
        }

        /* Cards de plataforma */
        .connect-card {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #00ffad44;
            border-radius: 8px;
            padding: 25px;
            margin: 10px 0;
            box-shadow: 0 0 15px #00ffad11;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
            height: 100%;
        }

        .connect-card:hover {
            border-color: #00ffad99;
            box-shadow: 0 0 25px #00ffad22;
        }

        .platform-icon {
            font-size: 2.8rem;
            margin-bottom: 1rem;
            display: block;
        }

        .discord-color { color: #5865F2; }
        .telegram-color { color: #0088cc; }
        .email-color { color: #00ffad; }

        .card-title {
            font-family: 'VT323', monospace !important;
            color: #00ffad !important;
            font-size: 1.8rem !important;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 0.8rem;
        }

        .card-badge {
            display: inline-block;
            background: #00ffad11;
            border: 1px solid #00ffad33;
            border-radius: 4px;
            padding: 2px 10px;
            font-family: 'VT323', monospace;
            font-size: 0.85rem;
            color: #00ffad;
            letter-spacing: 1px;
            margin-bottom: 1rem;
        }

        .card-desc {
            color: #888 !important;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            line-height: 1.7;
            margin-bottom: 1.5rem;
            min-height: 70px;
        }

        .card-feature {
            color: #aaa !important;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            padding: 4px 0;
        }

        .card-feature::before {
            content: "▸ ";
            color: #00ffad;
        }

        /* Botones nativos de Streamlit */
        .stButton > button, .stLinkButton > a {
            width: 100% !important;
            border-radius: 6px !important;
            padding: 0.75rem !important;
            font-weight: bold !important;
            border: none !important;
            font-family: 'VT323', monospace !important;
            font-size: 1.1rem !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
        }

        .btn-discord .stLinkButton > a {
            background: linear-gradient(135deg, #5865F2 0%, #4752C4 100%) !important;
            color: white !important;
        }

        .btn-telegram .stLinkButton > a {
            background: linear-gradient(135deg, #0088cc 0%, #006699 100%) !important;
            color: white !important;
        }

        /* Formulario Formspree */
        .form-input {
            background: #11141a;
            border: 1px solid #1a1e26;
            color: white;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 14px;
            font-family: 'Courier New', monospace;
            width: 100%;
            box-sizing: border-box;
            transition: border-color 0.2s ease;
        }

        .form-input:focus {
            outline: none;
            border-color: #00ffad55;
        }

        .form-input::placeholder {
            color: #444;
        }

        .form-submit {
            background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%);
            color: #0c0e12;
            border: none;
            padding: 12px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 1rem;
            font-family: 'VT323', monospace;
            letter-spacing: 1px;
            cursor: pointer;
            width: 100%;
            text-transform: uppercase;
            margin-top: 6px;
        }

        .form-submit:hover {
            opacity: 0.9;
        }

        /* Header terminal */
        .terminal-header {
            text-align: center;
            margin-bottom: 40px;
        }

        .terminal-tag {
            font-family: 'VT323', monospace;
            font-size: 1rem;
            color: #666;
            margin-bottom: 10px;
        }

        .terminal-subtitle {
            font-family: 'VT323', monospace;
            color: #00d9ff;
            font-size: 1.2rem;
            letter-spacing: 3px;
            margin-top: 10px;
        }

        /* Highlight quote */
        .highlight-quote {
            background: #00ffad11;
            border: 1px solid #00ffad33;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
            font-family: 'VT323', monospace;
            font-size: 1.2rem;
            color: #00ffad;
            text-align: center;
        }

        /* Footer */
        .footer-terminal {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            border-top: 1px solid #1a1e26;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── HEADER ──
    st.markdown("""
    <div class="terminal-header">
        <div class="terminal-tag">[SECURE CONNECTION ESTABLISHED // RED RSU ACTIVA]</div>
        <h1>👥 COMUNIDAD RSU</h1>
        <div class="terminal-subtitle">PROTOCOLO DE CONEXIÓN // ÚNETE AL ECOSISTEMA</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="highlight-quote">
        "La ventaja no es solo el análisis. Es la red de traders que lo aplica en tiempo real."
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── CARDS ──
    col1, col2, col3 = st.columns(3, gap="large")

    # DISCORD
    with col1:
        st.markdown(f"""
        <div class="connect-card">
            <span class="platform-icon discord-color">💬</span>
            <div class="card-badge">// COMUNIDAD PRINCIPAL</div>
            <div class="card-title">Discord</div>
            <div class="card-desc">Únete al ecosistema de traders. Comparte operativas, recibe feedback en tiempo real y accede a salas de voz durante sesiones de mercado.</div>
            <div class="card-feature">Salas de voz en directo</div>
            <div class="card-feature">Feedback de operativas</div>
            <div class="card-feature">Canales por activo</div>
            <div class="card-feature">Comunidad 24/7</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="btn-discord">', unsafe_allow_html=True)
        st.link_button("▸ UNIRSE AL DISCORD", DISCORD_URL, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # TELEGRAM
    with col2:
        st.markdown(f"""
        <div class="connect-card">
            <span class="platform-icon telegram-color">📢</span>
            <div class="card-badge">// ALERTAS EN TIEMPO REAL</div>
            <div class="card-title">Telegram</div>
            <div class="card-desc">Recibe alertas instantáneas en tu móvil. Notificaciones push con análisis rápidos, niveles clave y oportunidades de mercado al instante.</div>
            <div class="card-feature">Notificaciones push</div>
            <div class="card-feature">Niveles y zonas clave</div>
            <div class="card-feature">Análisis rápidos</div>
            <div class="card-feature">Sin ruido, solo señal</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="btn-telegram">', unsafe_allow_html=True)
        st.link_button("▸ UNIRSE AL CANAL", TELEGRAM_URL, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # CONTACTO
    with col3:
        st.markdown("""
        <div class="connect-card">
            <span class="platform-icon email-color">✉️</span>
            <div class="card-badge">// CONTACTO DIRECTO</div>
            <div class="card-title">Contacto</div>
        """, unsafe_allow_html=True)

        form_html = f"""
        <form action="https://formspree.io/f/{FORMSPREE_ID}" method="POST"
              style="display: flex; flex-direction: column; gap: 10px; margin-top: 12px;">
            <input  class="form-input" type="text"  name="nombre"  placeholder="// Tu nombre"  required>
            <input  class="form-input" type="email" name="email"   placeholder="// tu@email.com" required>
            <textarea class="form-input" name="mensaje" placeholder="// Escribe tu mensaje..." required
                      rows="4" style="resize: vertical;"></textarea>
            <input type="hidden" name="_subject" value="Nuevo mensaje desde RSU Web">
            <input type="hidden" name="_replyto" value="unl4b@proton.me">
            <button type="submit" class="form-submit">▸ ENVIAR MENSAJE</button>
        </form>
        """
        st.markdown(form_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── FOOTER ──
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div class="footer-terminal">
        <p style="font-family: 'VT323', monospace; color: #666; font-size: 0.9rem;">
            [END OF TRANSMISSION // COMUNIDAD_RSU_v2.0]<br>
            [STATUS: ACTIVE // RED EN LÍNEA]
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render()
