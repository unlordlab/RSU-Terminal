import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Tesis de Inversión</h2>', unsafe_allow_html=True)

    # URL de tu Sheet CSV
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=300) # Se actualiza cada 5 minutos
        def load_index(url):
            data = pd.read_csv(url)
            # Limpieza básica de espacios en los nombres de columnas
            data.columns = data.columns.str.strip()
            return data
            
        df = load_index(CSV_URL)
        
        # Selector de Tesis
        opciones = df['Ticker'].tolist()
        sel = st.selectbox("Selecciona un activo para ver el análisis detallado:", opciones)
        
        # Obtener datos de la fila seleccionada
        data = df[df['Ticker'] == sel].iloc[0]

        # --- CABECERA DE LA TESIS ---
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### {data['Nombre']}")
            st.caption(f"Sector: {data.get('Sector', 'N/A')}")
            
        with col2:
            # Mostramos el Rating con color dinámico
            rating = str(data['Rating']).upper()
            color = "#00ffad" if "BUY" in rating else "#ff9800" if "HOLD" in rating else "#f23645"
            st.markdown(f"""
                <div style="text-align:center;">
                    <p style="margin:0; color:#888; font-size:12px;">RATING</p>
                    <h4 style="margin:0; color:{color};">{rating}</h4>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div style="text-align:center;">
                    <p style="margin:0; color:#888; font-size:12px;">TARGET</p>
                    <h4 style="margin:0; color:white;">${data['Precio_Objetivo']}</h4>
                </div>
            """, unsafe_allow_html=True)

        st.divider()

        # --- EXPOSICIÓN DEL DOCUMENTO ---
        # Verificamos que exista la URL del Doc
        url_doc = data['URL_Doc']
        
        if pd.notna(url_doc) and url_doc.startswith("http"):
            # Insertamos el Google Doc publicado
            components.iframe(url_doc, height=1000, scrolling=True)
        else:
            st.warning("No se ha encontrado un enlace válido de Google Docs para este activo.")

    except Exception as e:
        st.error("Error al conectar con el índice de tesis.")
        st.info("Verifica que las columnas del CSV coincidan exactamente con: Ticker, Nombre, Rating, Precio_Objetivo, URL_Doc")
        # st.write(e) # Descomentar para debug en caso de error
