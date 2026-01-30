# modules/ia_report.py
import streamlit as st
from streamlit.components.v1 import html
from config import get_ia_model, obtener_prompt_github

def render():
    model_ia, modelo_nombre, error_ia = get_ia_model()
    
    st.subheader("🤖 IA Report RSU")
    t_in = st.text_input("Ticker", "NVDA").upper()
    
    if st.button("🔥 GENERAR PROMPT RSU", type="primary"):
        if error_ia:
            st.error(error_ia)
            return
            
        # ========== GRÀFIC TRADINGVIEW (ABANS del prompt) ==========
        with st.spinner(f"📊 Carregant gràfic de {t_in}..."):
            tradingview_widget = f"""
            <!-- TradingView Widget BEGIN -->
            <div class="tradingview-widget-container">
              <div id="tradingview_{t_in}"></div>
              <div class="tradingview-widget-copyright">
                <a href="https://es.tradingview.com/" rel="noopener" target="_blank">
                  <span class="blue-text">Gràfic de {t_in} - TradingView</span>
                </a>
              </div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
                new TradingView.widget({{
                  "autosize": true,
                  "symbol": "{t_in}",
                  "interval": "1D",
                  "timezone": "Europe/Madrid",
                  "theme": "light",
                  "style": "1",
                  "locale": "es",
                  "toolbar_bg": "#f1f3f6",
                  "enable_publishing": false,
                  "hide_legend": true,
                  "save_image": false,
                  "container_id": "tradingview_{t_in}"
                }});
              </script>
            </div>
            <!-- TradingView Widget END -->
            """
            html(tradingview_widget, height=500)
        
        # ========== GENERAR PROMPT IA ==========
        st.divider()
        with st.spinner(f"🤖 Analitzant {t_in} amb IA..."):
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
    else:
        # Gràfic de preview (opcional, quan NO has clicat el botó)
        if t_in:
            st.info("💡 Clica 'GENERAR PROMPT RSU' per veure el gràfic TradingView + anàlisi IA")


