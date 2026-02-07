# modules/rsu_club.py
import streamlit as st
from pathlib import Path

def get_logo_path():
    possible_paths = [
        "/mnt/kimi/upload/rsu_logo.png",
        "rsu_logo.png",
        "assets/rsu_logo.png", 
        "static/rsu_logo.png"
    ]
    for path in possible_paths:
        if Path(path).exists():
            return path
    return None

def render():
    # CSS mínimo
    st.markdown("""
    <style>
        .stApp {
            background: #0e1117;
        }
        .logo-text {
            font-size: 2.5rem;
            font-weight: bold;
            color: #00ffad;
            text-align: center;
            margin: 20px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # HEADER - Logo y título
    logo_path = get_logo_path()
    
    if logo_path:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_path, width=150, use_container_width=False)
    
    st.markdown('<div class="logo-text">♣️ RSU Elite Club</div>', unsafe_allow_html=True)
    st.markdown("---")

    # CONTENIDO EN TABS O EXPANDERS PARA EVITAR PROBLEMAS DE COLUMNAS
    tab1, tab2 = st.tabs(["🎯 Nuestra Filosofía", "🛠️ ¿Qué te ofrecemos?"])
    
    with tab1:
        st.info("**Más que un club, una comunidad.**")
        
        st.write("""
        En el ecosistema del trading, encontrar un espacio transparente es un verdadero desafío. 
        Entre "gurús" que prometen riqueza inmediata y cursos costosos de nula eficacia, es normal sentirse perdido.
        """)
        
        st.write("""
        En **RSU Club** marcamos la distancia: aquí no hay promesas vacías, solo 
        **conocimiento real, colaboración y responsabilidad**.
        """)
        
        st.write("""
        Somos una comunidad de trading diseñada para ser **seria, responsable y rentable**. 
        Te dotamos de las herramientas y el respaldo necesarios para que tus decisiones de 
        inversión estén fundamentadas y cuenten con garantías.
        """)

    with tab2:
        st.success("Beneficios exclusivos para miembros")
        
        with st.expander("📊 Análisis profundo y actualizado", expanded=True):
            st.write("Seguimiento diario del sentimiento del mercado, tesis de compra exhaustivas e ideas operativas de alto interés.")
        
        with st.expander("🎓 Estrategias y Formación", expanded=True):
            st.write("Metodologías únicas adaptadas a diversos perfiles de riesgo. Base de datos de 'operaciones inusuales' y biblioteca exclusiva.")
        
        with st.expander("💎 Recursos Exclusivos", expanded=True):
            st.write("Listado actualizado de activos para carteras de medio/largo plazo e información de 'segundo nivel'.")
        
        with st.expander("🤝 Soporte Personalizado", expanded=True):
            st.write("Asesoramiento individual en configuración de herramientas (TradingView, brókers) para un entorno operativo óptimo.")

    # SECCIÓN FINAL
    st.markdown("---")
    st.subheader("🚀 Tu camino empieza aquí")
    
    st.write("""
    Te invito a explorar la comunidad, participar en los debates y consultar cualquier duda. 
    Si necesitas algo específico, puedes contactarme por **mensaje directo (MD)**; te responderé lo antes posible.
    """)
    
    st.info("💡 **Consejo:** No te abrumes por el volumen de información. Tómalo con calma, a tu ritmo; poco a poco integrarás los conocimientos necesarios para operar con confianza.")
    
    st.write("""
    Gracias por formar parte de un espacio donde la **formación, la responsabilidad y la transparencia** 
    son la prioridad. Deja atrás el ruido de los falsos gurús y comienza tu camino hacia un **trading consciente**.
    """)
    
    st.markdown("""
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #333; color: #666;">
        <strong style="color: #00ffad;">unlord</strong> | RSU Club ♣️
    </div>
    """, unsafe_allow_html=True)
