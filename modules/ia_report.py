# modules/ia_report.py
import streamlit as st
from streamlit.components.v1 import html
from config import get_ia_model, obtener_prompt_github

def render():
    model_ia, modelo_nombre, error_ia = get_ia_model()
    
    st.subheader("🤖 IA Report RSU")
    t_in = st.text_input("Ticker", "NVDA").upper()
    
    # ========== BOTO PERSONALITZAT amb colors del logo ==========
    if st.button(
        "🔥 GENERAR PROMPT RSU", 
        type="primary",
        use_container_width=True,
        help="Analitza l'actiu amb IA + Gràfic TradingView",
        **{
            "style": """
                background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                padding: 12px 24px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                transition: all 0.3s ease;
            """,
            "hover_style": """
                background: linear-gradient(45deg, #5a67d8 0%, #6b46c1 100%);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
                transform: translateY(-2px);
            """
        }
    ):
        if error_ia:
            st.error(error_ia)
            return
            
        # ========== WIDGET TRADINGVIEW - QUADRAT ==========
        st.markdown("### 📈 Gràfic TradingView")
        tradingview_widget = f"""
        <div style="max-width: 600px; margin: 0 auto; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
          <div class="tradingview-widget-container" style="height: 500px;">
            <div id="tradingview_{t_in}" style="height: 500px;"></div>
            <div class="tradingview-widget-copyright">
              <a href="https://es.tradingview.com/" rel="noopener" target="_blank">
                <span style="color: #667eea; font-size: 12px;">{t_in} - TradingView</span>
              </a>
            </div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
              new TradingView.widget({{
                "width": 600,
                "height": 500,
                "symbol": "{t_in}",
                "interval": "1D",
                "timezone": "Europe/Madrid",
                "theme": "light",
                "style": "1",
                "locale": "es",
                "toolbar_bg": "#f8fafc",
                "enable_publishing": false,
                "hide_legend": true,
                "save_image": false,
                "container_id": "tradingview_{t_in}"
              }});
            </script>
          </div>
        </div>
        """
        html(tradingview_widget, height=520)
        
        # ========== PROMPT IA ==========
        st.divider()
        with st.spinner(f"🤖 Generant anàlisi IA de {t_in}..."):
            template = obtener_prompt_github()
            prompt_final = f"Analitza {t_in} seguint això: {template.replace('[TICKER]', t_in)}"
            
            try:
                res = model_ia.generate_content(prompt_final)
                text = getattr(res, "text", None)
                if text:
                    st.markdown(f"### 📋 Informe complet: {t_in}")
                    st.markdown(text)
                else:
                    st.warning("No s'ha rebut resposta de l'IA.")
            except Exception as e:
                st.error(f"Error generant el prompt: {str(e)}")
