import streamlit as st

def render():
    st.title("👥 Comunidad RSU")
    st.markdown('<div class="group-container"><div class="group-content">', unsafe_allow_html=True)
    st.info("Únete a nuestro ecosistema de traders para compartir tesis y operativas.")
    st.button("Acceder al Discord Oficial")
    st.button("Canal de Anuncios Telegram")
    st.markdown('</div></div>', unsafe_allow_html=True)