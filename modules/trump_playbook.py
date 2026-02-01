import streamlit as st

def render():
    st.title("🇺🇸 Trump Playbook")
    
    # --- INTRODUCCIÓN ESTRATEGIA TACO ---
    st.markdown("""
    <div style="background-color: #1a1e26; border-left: 5px solid #2962ff; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
        <h3 style="color: #2962ff; margin-top: 0;">🌮 La Estrategia TACO</h3>
        <p style="font-style: italic; color: #e0e0e0;">
            <b>"Trump Always Chickens Out"</b> (Trump siempre se echa para atrás) es un término acuñado en Wall Street para describir el patrón 
            cíclico de las negociaciones de Donald Trump. 
        </p>
        <p style="font-size: 0.95rem; line-height: 1.6;">
            Esta estrategia consiste en lanzar una amenaza extrema (generalmente aranceles) para generar pánico y obtener una posición de fuerza, 
            solo para suavizar o retrasar la medida una vez que los mercados reaccionan o se inician conversaciones. Para los inversores, este "ruido" 
            crea oportunidades de compra durante el pánico inicial.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🗓️ Cronología de un 'Playbook' Típico")
    st.write("Análisis de las fases desde el mensaje inicial hasta el retorno del optimismo:")

    # --- LÍNEA DE TIEMPO ESTILIZADA ---
    # Usamos una lista de diccionarios para los pasos basados en tu .txt
    playbook_steps = [
        {"dia": "Viernes", "titulo": "El mensaje inicial", "desc": "El presidente publica un mensaje críptic sugerint aranzels a un país o sector específic."},
        {"dia": "Vie/Sáb", "titulo": "Anuncio oficial", "desc": "Anuncia formalmente un nou gran aranzel, sovint del 25% o més."},
        {"dia": "Finde", "titulo": "Presión psicológica", "desc": "Referma les seves amenaces repetidament per aplicar pressió amb mercats tancats."},
        {"dia": "Finde", "titulo": "Reacción internacional", "desc": "Els països afectats donen senyals d'estar disposats a negociar."},
        {"dia": "Dom Nit", "titulo": "Apertura de futuros", "desc": "El mercat cau en una reacció emocional inicial als titulars."},
        {"dia": "Lun/Mar", "titulo": "Fase de realismo", "desc": "Els inversors s'adonen que els aranzels encara no s'han aplicat (data futura)."},
        {"dia": "Miércoles", "titulo": "Rebote de alivio", "desc": "Apareixen els compradors d'oportunitats ('smart money')."},
        {"dia": "Finde 2", "titulo": "Cambio de narrativa", "desc": "El president publica que hi ha converses en marxa i solucions en camí."},
        {"dia": "Dom Nit 2", "titulo": "Retorno del optimismo", "desc": "Els futurs obren a l'alça a mesura que torna l'optimisme."},
        {"dia": "Lunes 2", "titulo": "Aparición de moderadores", "desc": "Alts càrrecs (com Scott Bessent) tranquil·litzen els inversors a la TV."},
        {"dia": "Semanas 2-4", "titulo": "Fase de filtraciones", "desc": "Pistes sobre els avenços cap a un acord final."}
    ]

    for i, step in enumerate(playbook_steps, 1):
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"""
                    <div style="text-align: center; background-color: #2962ff; color: white; border-radius: 50%; width: 40px; height: 40px; line-height: 40px; font-weight: bold; margin: auto;">
                        {i}
                    </div>
                    <p style="text-align: center; font-size: 0.8rem; color: #888; margin-top: 5px;">{step['dia']}</p>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{step['titulo']}**")
                st.info(step['desc'])
            st.markdown("<hr style='margin: 10px 0; border-color: #2d3439;'>", unsafe_allow_html=True)

    st.caption("Fuente: Estrategia de mercado basada en patrones históricos de administración Trump.")
