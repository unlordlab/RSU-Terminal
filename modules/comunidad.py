import streamlit as st

DISCORD_URL = "https://discord.gg/8BZDAXAx"
TELEGRAM_URL = "https://t.me/TU_CANAL"
FORMSPREE_ID = "TU_ID_AQUI"  # Ej: xnqkvnzp

def render():
    st.markdown("""
    <style>
        .block-container { padding-top: 2rem; max-width: 1200px; }
        .main-title { text-align: center; color: white; font-size: 2.5rem; font-weight: bold; margin-bottom: 3rem; }
        .connect-card { background: linear-gradient(180deg, #11141a 0%, #0c0e12 100%); border: 1px solid #1a1e26; border-radius: 12px; padding: 2rem; height: 100%; }
        .connect-card:hover { border-color: #2a3f5f; }
        .platform-icon { font-size: 3rem; margin-bottom: 1rem; }
        .discord-color { color: #5865F2; } .telegram-color { color: #0088cc; } .email-color { color: #00ffad; }
        .card-title { color: white; font-size: 1.3rem; font-weight: bold; margin-bottom: 0.8rem; }
        .card-desc { color: #888; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem; min-height: 70px; }
        .stButton > button { width: 100%; border-radius: 8px !important; padding: 0.8rem !important; font-weight: bold !important; border: none !important; }
        .btn-discord > button { background: linear-gradient(135deg, #5865F2 0%, #4752C4 100%) !important; color: white !important; }
        .btn-telegram > button { background: linear-gradient(135deg, #0088cc 0%, #006699 100%) !important; color: white !important; }
        .stTextInput > div > div > input, .stTextArea > div > div > textarea { background-color: #11141a !important; color: white !important; border: 1px solid #1a1e26 !important; border-radius: 6px !important; }
        .stFormSubmitButton > button { background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%) !important; color: #0c0e12 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-title">👥 Comunidad RSU</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="large")

    # DISCORD
    with col1:
        st.markdown(f"""
        <div class="connect-card">
            <div class="platform-icon discord-color">💬</div>
            <div class="card-title">Discord</div>
            <div class="card-desc">Únete al ecosistema de traders. Comparte operativas, recibe feedback en tiempo real y accede a salas de voz durante sesiones de mercado.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="btn-discord">', unsafe_allow_html=True)
        st.link_button("Unirse al Discord →", DISCORD_URL, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # TELEGRAM
    with col2:
        st.markdown(f"""
        <div class="connect-card">
            <div class="platform-icon telegram-color">📢</div>
            <div class="card-title">Telegram</div>
            <div class="card-desc">Recibe alertas instantáneas en tu móvil. Notificaciones push con análisis rápidos, niveles clave y oportunidades de mercado en tiempo real.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="btn-telegram">', unsafe_allow_html=True)
        st.link_button("Unirse al Canal →", TELEGRAM_URL, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # FORMULARIO CON FORMSPREE
    with col3:
        st.markdown("""
        <div class="connect-card">
            <div class="platform-icon email-color">✉️</div>
            <div class="card-title">Contacto</div>
        """, unsafe_allow_html=True)
        
        # Formulario que envía realmente el email vía Formspree
        form_html = f"""
        <form action="https://formspree.io/f/{FORMSPREE_ID}" method="POST" style="display: flex; flex-direction: column; gap: 12px;">
            <input type="text" name="nombre" placeholder="Tu nombre" required 
                style="background: #11141a; border: 1px solid #1a1e26; color: white; padding: 10px; border-radius: 6px; font-size: 14px;">
            <input type="email" name="email" placeholder="tu@email.com" required 
                style="background: #11141a; border: 1px solid #1a1e26; color: white; padding: 10px; border-radius: 6px; font-size: 14px;">
            <textarea name="mensaje" placeholder="Escribe tu mensaje..." required rows="4"
                style="background: #11141a; border: 1px solid #1a1e26; color: white; padding: 10px; border-radius: 6px; font-size: 14px; resize: vertical; font-family: inherit;"></textarea>
            <input type="hidden" name="_subject" value="Nuevo mensaje desde RSU Web">
            <input type="hidden" name="_replyto" value="unl4b@proton.me">
            <button type="submit" 
                style="background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%); color: #0c0e12; border: none; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 15px; cursor: pointer; margin-top: 8px;">
                Enviar a unl4b@proton.me →
            </button>
        </form>
        """
        st.markdown(form_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
