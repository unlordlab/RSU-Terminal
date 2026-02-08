import streamlit as st
import re

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE ENLACES
# ────────────────────────────────────────────────

DISCORD_URL = "https://discord.gg/8BZDAXAx"
TELEGRAM_URL = "https://t.me/TU_CANAL"  # Modifica cuando tengas el link
EMAIL_DESTINO = "unl4b@proton.me"

# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    # CSS Global - Estética market.py limpia
    st.markdown("""
    <style>
        /* Reset base */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* Título principal */
        .main-title {
            text-align: center;
            color: white;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 3rem;
            letter-spacing: -0.5px;
        }
        
        /* Tarjetas de conexión */
        .connect-card {
            background: linear-gradient(180deg, #11141a 0%, #0c0e12 100%);
            border: 1px solid #1a1e26;
            border-radius: 12px;
            padding: 2rem;
            height: 100%;
            transition: all 0.3s ease;
        }
        .connect-card:hover {
            border-color: #2a3f5f;
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        /* Iconos grandes */
        .platform-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        .discord-color { color: #5865F2; }
        .telegram-color { color: #0088cc; }
        .email-color { color: #00ffad; }
        
        /* Títulos de tarjeta */
        .card-title {
            color: white;
            font-size: 1.3rem;
            font-weight: bold;
            margin-bottom: 0.8rem;
        }
        
        /* Descripción */
        .card-desc {
            color: #888;
            font-size: 0.95rem;
            line-height: 1.6;
            margin-bottom: 1.5rem;
            min-height: 70px;
        }
        
        /* Botones estilizados via CSS puro */
        .stButton > button {
            width: 100%;
            border-radius: 8px !important;
            padding: 0.8rem 1.5rem !important;
            font-weight: bold !important;
            font-size: 1rem !important;
            border: none !important;
            transition: all 0.3s ease !important;
        }
        
        /* Discord button */
        .btn-discord > button {
            background: linear-gradient(135deg, #5865F2 0%, #4752C4 100%) !important;
            color: white !important;
        }
        .btn-discord > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(88, 101, 242, 0.4) !important;
        }
        
        /* Telegram button */
        .btn-telegram > button {
            background: linear-gradient(135deg, #0088cc 0%, #006699 100%) !important;
            color: white !important;
        }
        .btn-telegram > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 136, 204, 0.4) !important;
        }
        
        /* Formulario */
        .contact-form {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 1.5rem;
        }
        
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background-color: #11141a !important;
            color: white !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 6px !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #00ffad !important;
            box-shadow: 0 0 0 2px rgba(0, 255, 173, 0.2) !important;
        }
        
        /* Submit button email */
        .btn-email > button {
            background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%) !important;
            color: #0c0e12 !important;
        }
        .btn-email > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 255, 173, 0.4) !important;
        }
        
        /* Tooltips personalizados */
        .tooltip-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            background: #1a1e26;
            border: 1px solid #444;
            border-radius: 50%;
            color: #888;
            font-size: 12px;
            cursor: help;
            margin-left: 8px;
            position: relative;
        }
        
        .tooltip-icon:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            width: 220px;
            background: #1e222d;
            color: #eee;
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 12px;
            border: 1px solid #444;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            z-index: 1000;
            line-height: 1.4;
            pointer-events: none;
        }
        
        /* Separador visual */
        .section-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, #2a3f5f 50%, transparent 100%);
            margin: 2rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # TÍTULO
    st.markdown('<h1 class="main-title">👥 Comunidad RSU</h1>', unsafe_allow_html=True)

    # ─── TRES COLUMNAS ───
    col1, col2, col3 = st.columns(3, gap="large")

    # DISCORD
    with col1:
        st.markdown("""
        <div class="connect-card">
            <div class="platform-icon discord-color">💬</div>
            <div class="card-title">
                Discord
                <span class="tooltip-icon" data-tooltip="Comunidad principal con salas de voz 24/7, canales organizados por temas y alertas en tiempo real">?</span>
            </div>
            <div class="card-desc">
                Únete al ecosistema de traders. Comparte operativas, recibe feedback en tiempo real y accede a salas de voz durante sesiones de mercado.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón nativo de Streamlit con clase CSS
        st.markdown('<div class="btn-discord">', unsafe_allow_html=True)
        if st.button("Unirse al Discord →", key="btn_discord", use_container_width=True):
            st.markdown(f'<meta http-equiv="refresh" content="0; url={DISCORD_URL}">', unsafe_allow_html=True)
            st.markdown(f'<a href="{DISCORD_URL}" target="_blank">Click aquí si no redirige automáticamente</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # TELEGRAM
    with col2:
        st.markdown("""
        <div class="connect-card">
            <div class="platform-icon telegram-color">📢</div>
            <div class="card-title">
                Telegram
                <span class="tooltip-icon" data-tooltip="Canal de anuncios oficiales. Alertas push instantáneas a tu móvil sin spam, solo contenido relevante de mercado">?</span>
            </div>
            <div class="card-desc">
                Recibe alertas instantáneas en tu móvil. Notificaciones push con análisis rápidos, niveles clave y oportunidades de mercado en tiempo real.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="btn-telegram">', unsafe_allow_html=True)
        if st.button("Unirse al Canal →", key="btn_telegram", use_container_width=True):
            st.markdown(f'<meta http-equiv="refresh" content="0; url={TELEGRAM_URL}">', unsafe_allow_html=True)
            st.markdown(f'<a href="{TELEGRAM_URL}" target="_blank">Click aquí si no redirige automáticamente</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # FORMULARIO DE CONTACTO
    with col3:
        st.markdown("""
        <div class="connect-card">
            <div class="platform-icon email-color">✉️</div>
            <div class="card-title">
                Contacto
                <span class="tooltip-icon" data-tooltip="Para colaboraciones, soporte o consultas privadas. Respuesta garantizada en 24-48h">?</span>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("contact_form", clear_on_submit=True):
            nombre = st.text_input("Nombre", placeholder="Tu nombre", label_visibility="collapsed")
            email = st.text_input("Email", placeholder="tu@email.com", label_visibility="collapsed")
            mensaje = st.text_area("Mensaje", placeholder="Escribe tu mensaje...", height=100, label_visibility="collapsed")
            
            submitted = st.form_submit_button(f"Enviar a {EMAIL_DESTINO} →", use_container_width=True)
            
            if submitted:
                if nombre and email and mensaje:
                    if re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                        st.success("✅ Mensaje enviado correctamente")
                    else:
                        st.error("❌ Email inválido")
                else:
                    st.warning("⚠️ Completa todos los campos")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Separador y footer
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: #555; font-size: 0.9rem; margin-top: 1rem;">
        💡 Los miembros activos reciben acceso prioritario a alertas y análisis exclusivos
    </div>
    """, unsafe_allow_html=True)


# Para testing standalone
if __name__ == "__main__":
    render()
