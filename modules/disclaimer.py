import streamlit as st

def render():
    st.title("⚠️ Disclaimer")
    st.markdown('<div class="group-container"><div class="group-content">', unsafe_allow_html=True)
    st.error("AVISO LEGAL IMPORTANTE")
    st.write("""
    Todo el contenido de esta terminal tiene fines puramente educativos e informativos. 
    No constituye asesoramiento financiero ni recomendaciones de inversión. 
    Operar en los mercados financieros conlleva riesgos significativos.
    """)
    st.markdown('</div></div>', unsafe_allow_html=True)