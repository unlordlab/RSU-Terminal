import streamlit as st
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import re

# ────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ────────────────────────────────────────────────

def get_community_stats():
    """Simula estadísticas de la comunidad - En producción, conectar con APIs reales"""
    return {
        "total_members": 1247,
        "online_now": 89,
        "messages_today": 342,
        "analysis_shared": 28,
        "weekly_growth": "+12%"
    }

def get_discord_events():
    """Eventos próximos de la comunidad"""
    return [
        {"date": "Feb 10", "time": "18:00", "title": "Análisis Semanal Mercado", "type": "Webinar", "importance": "High"},
        {"date": "Feb 12", "time": "20:00", "title": "AMA con Trader Pro", "type": "AMA", "importance": "High"},
        {"date": "Feb 15", "time": "17:30", "title": "Sesión Live Trading", "type": "Live", "importance": "Medium"},
    ]

def get_telegram_updates():
    """Simula últimos anuncios de Telegram"""
    return [
        {"time": "2h", "title": "🚨 Alerta: Breakout detectado en NVDA", "is_new": True},
        {"time": "5h", "title": "📊 Resumen del cierre de mercado", "is_new": True},
        {"time": "1d", "title": "🎯 Nuevos niveles de entrada para esta semana", "is_new": False},
        {"time": "2d", "title": "📈 Análisis técnico: S&P 500", "is_new": False},
    ]

def get_top_contributors():
    """Top contribuyentes de la comunidad"""
    return [
        {"name": "TraderPro", "role": "Analista Senior", "messages": 156, "badge": "Expert", "color": "#ffd700"},
        {"name": "MariaRS", "role": "Swing Trader", "messages": 89, "badge": "Pro", "color": "#00ffad"},
        {"name": "CryptoDave", "role": "Crypto Analyst", "messages": 134, "badge": "Pro", "color": "#00ffad"},
        {"name": "Newbie2024", "role": "Aprendiz", "messages": 45, "badge": "Rising", "color": "#ff9800"},
    ]

def send_contact_email(name, email, subject, message):
    """Placeholder para envío de email - Integrar con backend real"""
    # Aquí implementarías el envío real vía smtplib o servicio externo
    return True

# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    # CSS Global consistente con market.py
    st.markdown("""
    <style>
        /* Reset y base */
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
            width: 280px;
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
        
        /* Contenedores de grupo */
        .group-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
            height: 100%;
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
        .group-content {
            padding: 0;
            background: #11141a;
        }
        
        /* Badges */
        .badge {
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .badge-new {
            background: rgba(0, 255, 173, 0.15);
            color: #00ffad;
            border: 1px solid #00ffad44;
        }
        .badge-hot {
            background: rgba(242, 54, 69, 0.15);
            color: #f23645;
            border: 1px solid #f2364544;
        }
        .badge-pro {
            background: rgba(0, 255, 173, 0.15);
            color: #00ffad;
        }
        .badge-expert {
            background: rgba(255, 215, 0, 0.15);
            color: #ffd700;
            border: 1px solid #ffd70044;
        }
        
        /* Inputs estilo trading */
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
        
        /* Botones personalizados */
        .btn-discord {
            background: linear-gradient(135deg, #5865F2 0%, #4752C4 100%) !important;
            color: white !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            width: 100% !important;
            transition: all 0.3s !important;
        }
        .btn-discord:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(88, 101, 242, 0.4) !important;
        }
        .btn-telegram {
            background: linear-gradient(135deg, #0088cc 0%, #006699 100%) !important;
            color: white !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            width: 100% !important;
            transition: all 0.3s !important;
        }
        .btn-telegram:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 136, 204, 0.4) !important;
        }
        .btn-submit {
            background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%) !important;
            color: #0c0e12 !important;
            border: none !important;
            padding: 14px 28px !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            font-size: 16px !important;
            width: 100% !important;
            transition: all 0.3s !important;
        }
        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 255, 173, 0.4) !important;
        }
        
        /* Animaciones */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .live-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #00ffad;
            border-radius: 50%;
            margin-right: 6px;
            animation: pulse 2s infinite;
            box-shadow: 0 0 8px #00ffad;
        }
        
        /* Scrollbar personalizada */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0c0e12;
        }
        ::-webkit-scrollbar-thumb {
            background: #2a3f5f;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #00ffad;
        }
    </style>
    """, unsafe_allow_html=True)

    # TÍTULO PRINCIPAL
    st.markdown('<h1 style="text-align:center; margin-bottom:30px; color:white;">👥 Comunidad RSU</h1>', unsafe_allow_html=True)
    
    H = "360px"

    # ─── FILA 1: STATS GENERALES ───
    stats = get_community_stats()
    
    stats_html = f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px;">
        <div style="background: linear-gradient(135deg, #11141a 0%, #0c0e12 100%); border: 1px solid #1a1e26; border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 2.2rem; font-weight: bold; color: #00ffad;">{stats['total_members']}</div>
            <div style="color: #888; font-size: 0.85rem; margin-top: 5px;">Miembros Totales</div>
            <div style="color: #00ffad; font-size: 0.75rem; margin-top: 4px;">{stats['weekly_growth']} esta semana</div>
        </div>
        <div style="background: linear-gradient(135deg, #11141a 0%, #0c0e12 100%); border: 1px solid #1a1e26; border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 2.2rem; font-weight: bold; color: #00ffad;">{stats['online_now']}</div>
            <div style="color: #888; font-size: 0.85rem; margin-top: 5px;">Online Ahora</div>
            <div style="margin-top: 8px;"><span class="live-indicator"></span><span style="color: #00ffad; font-size: 0.75rem;">En vivo</span></div>
        </div>
        <div style="background: linear-gradient(135deg, #11141a 0%, #0c0e12 100%); border: 1px solid #1a1e26; border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 2.2rem; font-weight: bold; color: #ffd700;">{stats['messages_today']}</div>
            <div style="color: #888; font-size: 0.85rem; margin-top: 5px;">Mensajes Hoy</div>
            <div style="color: #ffd700; font-size: 0.75rem; margin-top: 4px;">+23% vs ayer</div>
        </div>
        <div style="background: linear-gradient(135deg, #11141a 0%, #0c0e12 100%); border: 1px solid #1a1e26; border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 2.2rem; font-weight: bold; color: #f23645;">{stats['analysis_shared']}</div>
            <div style="color: #888; font-size: 0.85rem; margin-top: 5px;">Análisis Compartidos</div>
            <div style="color: #f23645; font-size: 0.75rem; margin-top: 4px;">Esta semana</div>
        </div>
    </div>
    """
    st.markdown(stats_html, unsafe_allow_html=True)

    # ─── FILA 2: DISCORD + TELEGRAM + EVENTOS ───
    col1, col2, col3 = st.columns(3)

    # COLUMNA 1: DISCORD
    with col1:
        discord_html = f"""
        <div class="group-container" style="height: {H};">
            <div class="group-header">
                <p class="group-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="#5865F2" style="margin-right:8px;">
                        <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/>
                    </svg>
                    Servidor Discord
                </p>
                <div class="tooltip-container">
                    <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                    <div class="tooltip-text">
                        <strong>Comunidad Principal</strong><br>
                        Accede a salas de voz en tiempo real, comparte pantalla durante sesiones de trading y recibe alertas instantáneas. Canales organizados por temas: análisis técnico, fundamental, cripto y forex.
                    </div>
                </div>
            </div>
            <div class="group-content" style="height: calc({H} - 50px); padding: 20px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <div style="width: 10px; height: 10px; background: #00ffad; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite;"></div>
                            <span style="color: #00ffad; font-weight: bold; font-size: 0.9rem;">{stats['online_now']} usuarios online</span>
                        </div>
                        <div style="color: #888; font-size: 0.85rem; line-height: 1.5;">
                            Únete a la conversación activa. Canales de voz disponibles 24/7 para análisis en equipo.
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <span class="badge badge-pro">#análisis-técnico</span>
                        <span class="badge badge-hot">#alertas</span>
                        <span class="badge badge-new">#crypto</span>
                        <span class="badge" style="background: rgba(88, 101, 242, 0.15); color: #5865F2;">#general</span>
                    </div>
                </div>
                <button class="btn-discord" onclick="window.open('https://discord.gg/tu-invite', '_blank')">
                    Unirse al Servidor →
                </button>
            </div>
        </div>
        """
        components.html(discord_html, height=420, scrolling=False)

    # COLUMNA 2: TELEGRAM
    with col2:
        telegram_updates = get_telegram_updates()
        updates_html = ""
        
        for update in telegram_updates:
            new_badge = '<span class="badge badge-new" style="margin-left:8px; font-size:9px;">NUEVO</span>' if update['is_new'] else ''
            time_color = "#00ffad" if update['is_new'] else "#888"
            
            updates_html += f"""
            <div style="padding: 12px 15px; border-bottom: 1px solid #1a1e26; transition: background 0.2s; cursor: pointer;" onmouseover="this.style.background='#0c0e12'" onmouseout="this.style.background='transparent'">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="color: {time_color}; font-size: 0.75rem; font-family: monospace;">hace {update['time']}</span>
                    {new_badge}
                </div>
                <div style="color: white; font-size: 0.9rem; line-height: 1.4;">{update['title']}</div>
            </div>
            """
        
        telegram_html = f"""
        <div class="group-container" style="height: {H};">
            <div class="group-header">
                <p class="group-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="#0088cc" style="margin-right:8px;">
                        <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                    </svg>
                    Canal de Anuncios
                </p>
                <div class="tooltip-container">
                    <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                    <div class="tooltip-text">
                        <strong>Alertas Instantáneas</strong><br>
                        Recibe notificaciones push en tu móvil con alertas de mercado, análisis rápidos y oportunidades detectadas por la comunidad. Sin spam, solo valor.
                    </div>
                </div>
            </div>
            <div class="group-content" style="height: calc({H} - 50px); overflow-y: auto;">
                {updates_html}
            </div>
        </div>
        """
        components.html(telegram_html, height=420, scrolling=False)

    # COLUMNA 3: EVENTOS
    with col3:
        events = get_discord_events()
        events_html = ""
        
        importance_colors = {
            "High": "#f23645",
            "Medium": "#ff9800",
            "Low": "#4caf50"
        }
        
        for event in events:
            imp_color = importance_colors.get(event['importance'], '#888')
            days_left = (datetime.strptime(event['date'], "%b %d") - datetime.now()).days
            if days_left < 0:
                days_left += 365  # Ajuste simple para fechas cercanas
            
            events_html += f"""
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="background: {imp_color}22; color: {imp_color}; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">{event['type']}</span>
                    <span style="color: #888; font-size: 0.8rem;">{event['date']} • {event['time']}</span>
                </div>
                <div style="color: white; font-weight: bold; font-size: 0.95rem; margin-bottom: 6px;">{event['title']}</div>
                <div style="color: #00ffad; font-size: 0.8rem;">⏱️ En {days_left} días</div>
            </div>
            """
        
        events_container = f"""
        <div class="group-container" style="height: {H};">
            <div class="group-header">
                <p class="group-title">📅 Próximos Eventos</p>
                <div class="tooltip-container">
                    <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                    <div class="tooltip-text">
                        <strong>Calendario Comunitario</strong><br>
                        Webinars exclusivos, sesiones de trading en vivo y AMAs con traders profesionales. Todos los eventos son grabados y compartidos en el Discord.
                    </div>
                </div>
            </div>
            <div class="group-content" style="height: calc({H} - 50px); padding: 15px; overflow-y: auto;">
                {events_html}
            </div>
        </div>
        """
        components.html(events_container, height=420, scrolling=False)

    # ─── FILA 3: TOP CONTRIBUYENTES + FORMULARIO ───
    st.write("")
    c1, c2 = st.columns([1, 1])

    # TOP CONTRIBUYENTES
    with c1:
        contributors = get_top_contributors()
        contrib_html = ""
        
        for i, user in enumerate(contributors, 1):
            badge_class = "badge-expert" if user['badge'] == "Expert" else "badge-pro" if user['badge'] == "Pro" else ""
            badge_style = f"background: {user['color']}22; color: {user['color']}; border: 1px solid {user['color']}44;" if not badge_class else ""
            
            contrib_html += f"""
            <div style="display: flex; align-items: center; padding: 12px 15px; border-bottom: 1px solid #1a1e26; background: {'#0c0e12' if i <= 2 else 'transparent'};">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, {user['color']}44 0%, {user['color']}22 100%); border: 2px solid {user['color']}; display: flex; align-items: center; justify-content: center; color: {user['color']}; font-weight: bold; font-size: 0.8rem; margin-right: 12px;">
                    {user['name'][:2].upper()}
                </div>
                <div style="flex: 1;">
                    <div style="color: white; font-weight: bold; font-size: 0.95rem;">{user['name']}</div>
                    <div style="color: #888; font-size: 0.8rem;">{user['role']}</div>
                </div>
                <div style="text-align: right;">
                    <span class="badge {badge_class}" style="{badge_style} padding: 3px 8px; font-size: 0.7rem;">{user['badge']}</span>
                    <div style="color: #555; font-size: 0.75rem; margin-top: 4px;">{user['messages']} msgs</div>
                </div>
            </div>
            """
        
        contributors_container = f"""
        <div class="group-container" style="height: {H};">
            <div class="group-header">
                <p class="group-title">🏆 Top Contribuyentes</p>
                <div class="tooltip-container">
                    <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                    <div class="tooltip-text">
                        <strong>Reconocimiento a la Comunidad</strong><br>
                        Miembros más activos compartiendo análisis, respondiendo dudas y aportando valor. Los badges se otorgan manualmente por calidad de contribución, no solo cantidad.
                    </div>
                </div>
            </div>
            <div class="group-content" style="height: calc({H} - 50px); overflow-y: auto;">
                {contrib_html}
            </div>
        </div>
        """
        components.html(contributors_container, height=420, scrolling=False)

    # FORMULARIO DE CONTACTO
    with c2:
        st.markdown(f"""
        <div class="group-container" style="height: {H};">
            <div class="group-header">
                <p class="group-title">✉️ Contacto Directo</p>
                <div class="tooltip-container">
                    <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
                    <div class="tooltip-text">
                        <strong>Escríbenos</strong><br>
                        Para propuestas de colaboración, soporte técnico o consultas privadas. Respuesta garantizada en 24-48h. Tu email nunca será compartido.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("contact_form", clear_on_submit=True):
            col_nombre, col_email = st.columns(2)
            with col_nombre:
                nombre = st.text_input("Nombre", placeholder="Tu nombre", label_visibility="collapsed")
            with col_email:
                email = st.text_input("Email", placeholder="tu@email.com", label_visibility="collapsed")
            
            asunto = st.selectbox(
                "Asunto",
                ["Colaboración", "Soporte Técnico", "Propuesta de Contenido", "Reportar Problema", "Otro"],
                label_visibility="collapsed"
            )
            
            mensaje = st.text_area(
                "Mensaje",
                placeholder="Escribe tu mensaje aquí...",
                height=100,
                label_visibility="collapsed"
            )
            
            submitted = st.form_submit_button("📤 Enviar Mensaje", use_container_width=True)
            
            if submitted:
                if nombre and email and mensaje:
                    # Validación básica de email
                    if re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                        # Aquí implementarías el envío real
                        # send_contact_email(nombre, email, asunto, mensaje)
                        st.success("✅ Mensaje enviado correctamente. Te responderemos a la brevedad.")
                    else:
                        st.error("❌ Por favor introduce un email válido")
                else:
                    st.warning("⚠️ Por favor completa todos los campos")

        # Estilo adicional para el formulario
        st.markdown("""
        <style>
        [data-testid="stForm"] {
            background: #11141a;
            padding: 0 20px 20px 20px;
            border-radius: 0 0 10px 10px;
        }
        </style>
        """, unsafe_allow_html=True)

    # ─── FOOTER INFORMATIVO ───
    st.write("")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #0c0e12 0%, #1a1e26 50%, #0c0e12 100%); 
                border: 1px solid #2a3f5f; border-radius: 8px; padding: 15px; text-align: center; margin-top: 20px;">
        <span style="color: #888; font-size: 0.9rem;">
            💡 <strong style="color: #00ffad;">Tip:</strong> Los miembros activos en Discord reciben acceso prioritario a alertas y análisis exclusivos.
        </span>
    </div>
    """, unsafe_allow_html=True)


# Para ejecutar standalone (testing)
if __name__ == "__main__":
    render()
