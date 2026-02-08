import streamlit as st
import streamlit.components.v1 as components
import re

# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    # CSS Global - Estética market.py
    st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        /* Tooltips */
        .tooltip-container {
            position: relative;
            cursor: help;
        }
        .tooltip-container .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 12px 14px;
            border-radius: 8px;
            position: absolute;
            z-index: 999;
            top: 140%;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s, visibility 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            line-height: 1.4;
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        
        /* Contenedores */
        .group-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
        }
        .group-header {
            background: #0c0e12;
            padding: 12px 15px;
            border-bottom: 1px solid #1a1e26;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .group-title {
            margin: 0;
            color: white;
            font-size: 14px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Botones estilo trading */
        .btn-discord {
            background: linear-gradient(135deg, #5865F2 0%, #4752C4 100%) !important;
            color: white !important;
            border: none !important;
            padding: 14px 28px !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            width: 100% !important;
            font-size: 15px !important;
            transition: all 0.3s !important;
            cursor: pointer !important;
        }
        .btn-discord:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(88, 101, 242, 0.4) !important;
        }
        
        .btn-telegram {
            background: linear-gradient(135deg, #0088cc 0%, #006699 100%) !important;
            color: white !important;
            border: none !important;
            padding: 14px 28px !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            width: 100% !important;
            font-size: 15px !important;
            transition: all 0.3s !important;
            cursor: pointer !important;
        }
        .btn-telegram:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 136, 204, 0.4) !important;
        }
        
        .btn-submit {
            background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%) !important;
            color: #0c0e12 !important;
            border: none !important;
            padding: 14px 28px !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            font-size: 15px !important;
            width: 100% !important;
            transition: all 0.3s !important;
            cursor: pointer !important;
        }
        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 255, 173, 0.4) !important;
        }
        
        /* Inputs */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {
            background-color: #0c0e12 !important;
            color: white !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 6px !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #00ffad !important;
            box-shadow: 0 0 0 1px #00ffad !important;
        }
        
        /* Descripción */
        .desc-text {
            color: #888;
            font-size: 0.9rem;
            line-height: 1.6;
            margin: 15px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # TÍTULO
    st.markdown('<h1 style="text-align:center; margin-bottom:40px; color:white;">👥 Comunidad RSU</h1>', unsafe_allow_html=True)

    # ─── TRES COLUMNAS ───
    col1, col2, col3 = st.columns(3)

    # DISCORD
    with col1:
        discord_card = """
        <div class="group-container" style="height: 100%;">
            <div class="group-header">
                <p class="group-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="#5865F2" style="margin-right:8px;">
                        <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/>
                    </svg>
                    Discord
                </p>
                <div class="tooltip-container">
                    <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                    <div class="tooltip-text">
                        <strong>Nuestra comunidad principal</strong><br>
                        Salas de voz 24/7, canales organizados por temas (análisis técnico, crypto, forex), alertas en tiempo real y sesiones de trading en equipo.
                    </div>
                </div>
            </div>
            <div style="padding: 20px; background: #11141a;">
                <p class="desc-text">
                    Únete al ecosistema de traders. Comparte operativas, recibe feedback en tiempo real y accede a salas de voz exclusivas durante sesiones de mercado.
                </p>
                <button class="btn-discord" onclick="window.open('https://discord.gg/TU_INVITACION', '_blank')">
                    Unirse al Discord →
                </button>
            </div>
        </div>
        """
        components.html(discord_card, height=280, scrolling=False)

    # TELEGRAM
    with col2:
        telegram_card = """
        <div class="group-container" style="height: 100%;">
            <div class="group-header">
                <p class="group-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="#0088cc" style="margin-right:8px;">
                        <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                    </svg>
                    Telegram
                </p>
                <div class="tooltip-container">
                    <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                    <div class="tooltip-text">
                        <strong>Canal de anuncios oficiales</strong><br>
                        Alertas instantáneas push a tu móvil. Sin spam, solo contenido relevante: breakouts, cambios de tendencia y oportunidades detectadas.
                    </div>
                </div>
            </div>
            <div style="padding: 20px; background: #11141a;">
                <p class="desc-text">
                    Recibe alertas instantáneas en tu móvil. Notificaciones push con análisis rápidos, niveles clave y oportunidades de mercado en tiempo real.
                </p>
                <button class="btn-telegram" onclick="window.open('https://t.me/TU_CANAL', '_blank')">
                    Unirse al Canal →
                </button>
            </div>
        </div>
        """
        components.html(telegram_card, height=280, scrolling=False)

    # FORMULARIO DE CONTACTO
    with col3:
        st.markdown("""
        <div class="group-container" style="height: 100%;">
            <div class="group-header">
                <p class="group-title">✉️ Contacto</p>
                <div class="tooltip-container">
                    <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                    <div class="tooltip-text">
                        <strong>Contacto directo</strong><br>
                        Para colaboraciones, soporte o consultas privadas. Respuesta garantizada en 24-48h a unl4b@proton.me
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("contact_form", clear_on_submit=True):
            nombre = st.text_input("Nombre", placeholder="Tu nombre", label_visibility="collapsed")
            email = st.text_input("Email", placeholder="tu@email.com", label_visibility="collapsed")
            mensaje = st.text_area("Mensaje", placeholder="Escribe tu mensaje...", height=80, label_visibility="collapsed")
            
            submitted = st.form_submit_button("📤 Enviar a unl4b@proton.me", use_container_width=True)
            
            if submitted:
                if nombre and email and mensaje:
                    if re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                        st.success("✅ Mensaje enviado correctamente")
                    else:
                        st.error("❌ Email inválido")
                else:
                    st.warning("⚠️ Completa todos los campos")

        st.markdown("""
        <style>
        [data-testid="stForm"] {
            background: #11141a;
            padding: 0 20px 20px 20px;
            border-radius: 0 0 10px 10px;
            margin-top: -5px;
        }
        </style>
        """, unsafe_allow_html=True)


# Para testing standalone
if __name__ == "__main__":
    render()
