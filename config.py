# config.py
def set_style():
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        
        /* Contenedores principales con altura fija para alineación */
        .group-container {
            background-color: #11141a; 
            border: 1px solid #2d3439;
            border-radius: 12px; 
            height: 480px; /* Altura fija para ambas cajas */
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .group-header {
            background-color: #1a1e26;
            padding: 15px 20px;
            border-bottom: 1px solid #2d3439;
            flex-shrink: 0;
        }
        
        .group-title { 
            color: #888; font-size: 12px; font-weight: bold; 
            text-transform: uppercase; margin: 0 !important;
        }

        .group-content { 
            padding: 20px; 
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        
        /* Tarjetas de Índices */
        .index-card {
            background-color: #1a1e26; border: 1px solid #2d3439; border-radius: 8px;
            padding: 12px 15px; margin-bottom: 10px; display: flex; 
            justify-content: space-between; align-items: center;
        }
        .pos { background-color: rgba(0, 255, 173, 0.1); color: #00ffad; }
        .neg { background-color: rgba(242, 54, 69, 0.1); color: #f23645; }
        </style>
        """, unsafe_allow_html=True)
