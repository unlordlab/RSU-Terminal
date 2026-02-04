
# modules/academy.py
import streamlit as st

def render():
    # CSS Global - Misma estética que market.py
    st.markdown("""
    <style>
        .group-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
            margin-bottom: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .group-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.4);
        }
        .group-header {
            background: #0c0e12;
            padding: 15px 20px;
            border-bottom: 1px solid #1a1e26;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .group-title {
            margin: 0;
            color: white;
            font-size: 16px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .module-number {
            background: #00ffad;
            color: #0c0e12;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }
        .group-content {
            padding: 20px;
            background: #11141a;
        }
        .module-thumbnail {
            width: 100%;
            height: 160px;
            background: linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%);
            border-radius: 8px;
            border: 2px solid #2a3f5f;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 15px;
            font-size: 48px;
        }
        .module-meta {
            display: flex;
            gap: 15px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }
        .meta-badge {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            color: #888;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .meta-badge.important {
            border-color: #00ffad44;
            color: #00ffad;
        }
        .progress-container {
            margin-top: 15px;
        }
        .progress-bar-bg {
            background: #0c0e12;
            height: 6px;
            border-radius: 3px;
            overflow: hidden;
            border: 1px solid #1a1e26;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ffad, #00ffad88);
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        .progress-text {
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 11px;
            color: #666;
        }
        .tooltip-container {
            position: relative;
            cursor: help;
        }
        .tooltip-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: #1a1e26;
            border: 2px solid #555;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 14px;
            font-weight: bold;
        }
        .tooltip-text {
            visibility: hidden;
            width: 280px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 12px;
            border-radius: 8px;
            position: absolute;
            z-index: 999;
            top: 35px;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            box-shadow: 0 8px 20px rgba(0,0,0,0.5);
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        .section-divider {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #2a3f5f, transparent);
            margin: 30px 0;
        }
        .locked {
            opacity: 0.7;
        }
        .locked .module-number {
            background: #555;
            color: #888;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px; padding: 20px 0;">
        <h1 style="color: white; font-size: 2.5rem; margin-bottom: 10px;">
            <span style="color: #00ffad;">🔥</span> RSU Academy
        </h1>
        <p style="color: #888; font-size: 1.1rem; max-width: 600px; margin: 0 auto;">
            Domina el trading con nuestro programa estructurado en 14 módulos. 
            Desde los fundamentos hasta estrategias avanzadas.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Datos de módulos
    modules = [
        {
            "id": 1,
            "title": "Bienvenida",
            "icon": "👋",
            "description": "Introducción al programa y configuración inicial de tu espacio de trabajo.",
            "chapters": 3,
            "duration": "45 min",
            "progress": 0,
            "videos": [
                {"title": "Bienvenida al Programa", "duration": "15:30", "url": "https://www.youtube.com/watch?v=6kjnyouSnHs"},
                {"title": "Configuración del Entorno", "duration": "18:45", "url": "https://www.youtube.com/watch?v=WSvGAHejvgU"},
                {"title": "Roadmap del Curso", "duration": "11:20", "url": "#"}
            ],
            "status": "available"
        },
        {
            "id": 2,
            "title": "Inicio Trading Lab",
            "icon": "🚀",
            "description": "Primeros pasos en el Trading Lab. Entendiendo la plataforma y herramientas básicas.",
            "chapters": 4,
            "duration": "1h 20min",
            "progress": 0,
            "videos": [
                {"title": "Introducción al Trading Lab", "duration": "20:00", "url": "#"},
                {"title": "Herramientas Esenciales", "duration": "25:30", "url": "#"},
                {"title": "Tu Primera Operación", "duration": "22:15", "url": "#"},
                {"title": "Checklist Pre-Trading", "duration": "12:45", "url": "#"}
            ],
            "status": "locked"
        },
        {
            "id": 3,
            "title": "Introducción",
            "icon": "📚",
            "description": "Conceptos fundamentales del trading: mercados, instrumentos y terminología.",
            "chapters": 5,
            "duration": "2h 10min",
            "progress": 0,
            "videos": [
                {"title": "¿Qué es el Trading?", "duration": "25:00", "url": "#"},
                {"title": "Tipos de Mercados", "duration": "30:00", "url": "#"},
                {"title": "Instrumentos Financieros", "duration": "28:00", "url": "#"},
                {"title": "Terminología Básica", "duration": "22:00", "url": "#"},
                {"title": "Psicología del Trader", "duration": "25:00", "url": "#"}
            ],
            "status": "locked"
        },
        {
            "id": 4,
            "title": "Lab Station",
            "icon": "🧪",
            "description": "Configuración avanzada de estaciones de trabajo para análisis técnico.",
            "chapters": 4,
            "duration": "1h 45min",
            "progress": 0,
            "videos": [
                {"title": "Setup Profesional", "duration": "28:00", "url": "#"},
                {"title": "Pantallas y Layouts", "duration": "22:00", "url": "#"},
                {"title": "Atajos y Productividad", "duration": "25:00", "url": "#"},
                {"title": "Gestión de Múltiples Monitores", "duration": "30:00", "url": "#"}
            ],
            "status": "locked"
        },
        {
            "id": 5,
            "title": "Lab Foundation",
            "icon": "🏗️",
            "description": "Fundamentos del análisis técnico: soportes, resistencias y tendencias.",
            "chapters": 6,
            "duration": "3h 30min",
            "progress": 0,
            "videos": [
                {"title": "Teoría de Dow", "duration": "35:00", "url": "#"},
                {"title": "Soportes y Resistencias", "duration": "40:00", "url": "#"},
                {"title": "Líneas de Tendencia", "duration": "35:00", "url": "#"},
                {"title": "Canales y Patrones", "duration": "45:00", "url": "#"},
                {"title": "Velas Japonesas I", "duration": "35:00", "url": "#"},
                {"title": "Velas Japonesas II", "duration": "30:00", "url": "#"}
            ],
            "status": "locked"
        },
        {
            "id": 6,
            "title": "Advanced Foundation",
            "icon": "🔬",
            "description": "Conceptos avanzados: indicadores, osciladores y sistemas de trading.",
            "chapters": 5,
            "duration": "4h 15min",
            "progress": 0,
            "videos": [
                {"title": "Medias Móviles Avanzadas", "duration": "50:00", "url": "#"},
                {"title": "RSI y Estocástico", "duration": "45:00", "url": "#"},
                {"title": "MACD y Divergencias", "duration": "55:00", "url": "#"},
                {"title": "Volumen y Perfíl", "duration": "45:00", "url": "#"},
                {"title": "Construcción de Sistemas", "duration": "60:00", "url": "#"}
            ],
            "status": "locked"
        },
        {
            "id": 7,
            "title": "Multi-TimeFrame Análisis",
            "icon": "📊",
            "description": "Análisis multi-temporal: sincronización de timeframes y confluencias.",
            "chapters": 4,
            "duration": "2h 45min",
            "progress": 0,
            "videos": [
                {"title": "Teoría de Timeframes", "duration": "40:00", "url": "#"},
                {"title": "Top-Down Analysis", "duration": "45:00", "url": "#"},
                {"title": "Confluencias y Zonas", "duration": "40:00", "url": "#"},
                {"title": "Casos Prácticos MTF", "duration": "50:00", "url": "#"}
            ],
            "status": "locked"
        },
        {
            "id": 10,
            "title": "Manejo de la Posición",
            "icon": "🎯",
            "description": "Gestión activa de trades: stops, targets y ajustes en vivo.",
            "chapters": 5,
            "duration": "3h 20min",
            "progress": 0,
            "videos": [
                {"title": "Stop Loss Inteligente", "duration": "40:00", "url": "#"},
                {"title": "Take Profit y RRR", "duration": "35:00", "url": "#"},
                {"title": "Breakeven y Trailing", "duration": "45:00", "url": "#"},
                {"title": "Escalado de Posiciones", "duration": "40:00", "url": "#"},
                {"title": "Gestión en Vivo", "duration": "50:00", "url": "#"}
            ],
            "status": "locked"
        },
        {
            "id": 11,
            "title": "Gestión Monetaria",
            "icon": "💰",
            "description": "Gestión de capital: sizing, riesgo por trade y curva de equity.",
            "chapters": 4,
            "duration": "2h 30min",
            "progress": 0,
            "videos": [
                {"title": "Regla del 1-2%", "duration": "35:00", "url": "#"},
                {"title": "Position Sizing", "duration": "40:00", "url": "#"},
                {"title": "Drawdown y Recuperación", "duration": "35:00", "url": "#"},
                {"title": "Optimización de Curva", "duration": "40:00", "url": "#"}
            ],
            "status": "locked"
        },
        {
            "id": 12,
            "title": "Creación de Watchlist",
            "icon": "📋",
            "description": "Construcción y mantenimiento de listas de seguimiento efectivas.",
            "chapters": 3,
            "duration": "1h 45min",
            "progress": 0,
            "videos": [
                {"title": "Criterios de Selección", "duration": "35:00", "url": "#"},
                {"title": "Scanning y Filtrado", "duration": "35:00", "url": "#"},
                {"title": "Mantenimiento Diario", "duration": "35:00", "url": "#"}
            ],
            "status": "locked"
        },
        {
            "id": 13,
            "title": "Trader Goals",
            "icon": "🎖️",
            "description": "Planificación de objetivos y desarrollo de disciplina de trading.",
            "chapters": 3,
            "duration": "1h 30min",
            "progress": 0,
            "videos": [
                {"title": "SMART Goals", "duration": "30:00", "url": "#"},
                {"title": "Trading Plan Personal", "duration": "35:00", "url": "#"},
                {"title": "Review y Mejora Continua", "duration": "25:00", "url": "#"}
            ],
            "status": "locked"
        },
        {
            "id": 14,
            "title": "Despedida",
            "icon": "🎓",
            "description": "Cierre del programa y próximos pasos en tu carrera de trading.",
            "chapters": 2,
            "duration": "45 min",
            "progress": 0,
            "videos": [
                {"title": "Resumen y Checklist Final", "duration": "25:00", "url": "#"},
                {"title": "Comunidad y Recursos", "duration": "20:00", "url": "#"}
            ],
            "status": "locked"
        }
    ]

    # FASE 1
    st.markdown('<div style="margin-bottom: 10px; color: #00ffad; font-size: 14px; font-weight: bold;">📍 FASE 1: FUNDAMENTOS</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for idx, module in enumerate(modules[:3]):
        with cols[idx]:
            render_module_card(module)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # FASE 2
    st.markdown('<div style="margin-bottom: 10px; color: #00ffad; font-size: 14px; font-weight: bold;">🔬 FASE 2: LABORATORIO Y TÉCNICO</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for idx, module in enumerate(modules[3:6]):
        with cols[idx]:
            render_module_card(module)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # FASE 3
    st.markdown('<div style="margin-bottom: 10px; color: #00ffad; font-size: 14px; font-weight: bold;">🎯 FASE 3: ESTRATEGIA AVANZADA</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for idx, module in enumerate([modules[6], modules[7], modules[8]]):
        with cols[idx]:
            render_module_card(module)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # FASE 4
    st.markdown('<div style="margin-bottom: 10px; color: #00ffad; font-size: 14px; font-weight: bold;">🚀 FASE 4: ESPECIALIZACIÓN</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for idx, module in enumerate(modules[9:]):
        with cols[idx]:
            render_module_card(module)


def render_module_card(module):
    """Renderiza una tarjeta de módulo individual"""
    
    status_class = ""
    lock_icon = ""
    
    if module['status'] == 'locked':
        status_class = "locked"
        tooltip_text = "Completa el módulo anterior para desbloquear"
        lock_icon = "🔒"
    else:
        tooltip_text = f"Haz click para ver {module['chapters']} capítulos"
    
    card_html = f"""
    <div class="group-container {status_class}">
        <div class="group-header">
            <div class="group-title">
                <div class="module-number">{module['id']}</div>
                <span>{module['title']} {lock_icon}</span>
            </div>
            <div class="tooltip-container">
                <div class="tooltip-icon">?</div>
                <div class="tooltip-text">{tooltip_text}</div>
            </div>
        </div>
        <div class="group-content">
            <div class="module-thumbnail">
                {module['icon']}
            </div>
            <div style="color: #aaa; font-size: 12px; line-height: 1.5; margin-bottom: 12px; min-height: 36px;">
                {module['description']}
            </div>
            <div class="module-meta">
                <div class="meta-badge">
                    <span>🎬</span> {module['chapters']} capítulos
                </div>
                <div class="meta-badge important">
                    <span>⏱️</span> {module['duration']}
                </div>
            </div>
            <div class="progress-container">
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {module['progress']}%;"></div>
                </div>
                <div class="progress-text">
                    <span>Progreso</span>
                    <span>{module['progress']}%</span>
                </div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Expander para capítulos
    if module['status'] != 'locked':
        with st.expander(f"📂 Ver {module['chapters']} capítulos"):
            for i, video in enumerate(module['videos'], 1):
                # Crear columnas para el layout
                c1, c2, c3 = st.columns([1, 6, 2])
                with c1:
                    st.markdown(f"<div style='background:#1a1e26;color:#00ffad;width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:bold;'>{i}</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div style='color:white;font-size:13px;font-weight:500;'>{video['title']}</div><div style='color:#666;font-size:11px;'>⏱️ {video['duration']}</div>", unsafe_allow_html=True)
                with c3:
                    if video['url'] != "#":
                        st.link_button("▶ Ver", video['url'], use_container_width=True)
                    else:
                        st.button("🔒", disabled=True, use_container_width=True, key=f"video_{module['id']}_{i}")
                st.markdown("<div style='border-bottom:1px solid #1a1e26;margin:8px 0;'></div>", unsafe_allow_html=True)
            
            if module['progress'] < 100:
                st.button(f"▶ Continuar módulo", key=f"btn_{module['id']}", use_container_width=True)
            else:
                st.button(f"✓ Completado", key=f"btn_{module['id']}", disabled=True, use_container_width=True)
    else:
        st.button("🔒 Bloqueado", key=f"btn_{module['id']}", disabled=True, use_container_width=True)
