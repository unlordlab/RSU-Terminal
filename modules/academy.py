# modules/academy.py
import streamlit as st

def render():
    st.subheader("🔥 RSU Academy")
    
    # ========== EXEMPLE 1: VÍDEOS SIMPLES ==========
    st.markdown("## 📺 Vídeos Ràpids")
    col1, col2 = st.columns(2)
    
    with col1:
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    with col2:
        st.video("https://www.youtube.com/watch?v=TEU_ENUXc5A")
    
    st.divider()
    
    
    st.markdown("---")
    st.info("""
   
    """)
