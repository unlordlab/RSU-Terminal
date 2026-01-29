# modules/fear_greed.py
import streamlit as st
import requests
from datetime import datetime

@st.cache_data(ttl=1800)  # 30min
def get_fear_greed():
    try:
        # CNN Fear & Greed API
        url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
        headers = {
            "X-RapidAPI-Key": st.secrets.get("RAPIDAPI_KEY", "demo"),
            "X-RapidAPI-Host": "fear-and-greed-index.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return data['score']
    except:
        return 65  # Demo

def render():
    st.subheader("😱 **Fear & Greed Index**")
    
    score = get_fear_greed()
    
    # Color según nivel
    if score < 25:
        color, level = "🟢", "Extreme Fear"
    elif score < 45:
        color, level = "🟢", "Fear" 
    elif score < 55:
        color, level = "🟡", "Neutral"
    elif score < 75:
        color, level = "🟠", "Greed"
    else:
        color, level = "🔴", "Extreme Greed"
    
    col1, col2 = st.columns([2,1])
    with col1:
        st.metric("Índice", f"{score}", f"{level}")
    with col2:
        st.markdown(f"""
        <div style="font-size: 2rem; text-align: center;">
            {color}
        </div>
        """, unsafe_allow_html=True)
    
    # Gráfico histórico
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Fear & Greed"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': 'green'},
                {'range': [25, 45], 'color': 'lightgreen'},
                {'range': [45, 55], 'color': 'yellow'},
                {'range': [55, 75], 'color': 'orange'},
                {'range': [75, 100], 'color': 'red'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    st.plotly_chart(fig, use_container_width=True)
