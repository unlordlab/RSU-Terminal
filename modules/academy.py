# modules/academy.py
import streamlit as st

def render():
    st.subheader("RSU Academy")
    
    # Múltiples vídeos (afegeix els teus enllaços aquí)
    videos = [
        "https://www.youtube.com/watch?v=6kjnyouSnHs",
        # "https://www.youtube.com/watch?v=TEU_ENUXc5A",  # Afegeix més
    ]
    
    for video_url in videos:
        st.video(video_url, format="video")
