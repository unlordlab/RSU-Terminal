# modules/fear_greed.py (SIN RAPIDAPI)
import streamlit as st
import plotly.graph_objects as go

@st.cache_data(ttl=1800)
def get_fear_greed():
    """Fear & Greed con datos simulados (actualización cada 30min)"""
    return 65  # Demo realista

def render():
    st.subheader("😱 **Fear & Greed Index**")
    
    score = get_fear_greed()
    
    # Color e interpretación
    if score < 25:
        emoji, level = "🟢", "Miedo Extremo"
    elif score < 45:
        emoji, level = "🟢", "Miedo"
    elif score < 55:
        emoji, level = "🟡", "Neutral"
    elif score < 75:
        emoji, level = "🟠", "Codicia"
    else:
        emoji, level = "🔴", "Codicia Extrema"
    
    col1, col2 = st.columns([2,1])
    with col1:
        st.metric("Índice", score, level)
    with col2:
        st.markdown(f'<div style="font-size: 4rem;">{emoji}</div>', unsafe_allow_html=True)
    
    # Gráfico gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Sentimiento Mercado"},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#FF6B35"},
            'steps': [
                {'range': [0, 25], 'color': '#00FF00'},
                {'range': [25, 45], 'color': '#90EE90'},
                {'range': [45, 55], 'color': '#FFFF00'},
                {'range': [55, 75], 'color': '#FFA500'},
                {'range': [75, 100], 'color': '#FF0000'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("🕐 Actualiza cada 30min | CNN Fear & Greed Index")


