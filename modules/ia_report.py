# modules/ia_report.py
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from config import get_ia_model, obtener_prompt_github

def render():
    st.title("🤖 IA Market Analysis")
    
    # 1. INPUT BOX
    t_in = st.text_input("Introdueix el Ticker (Ex: NVDA, TSLA, BTC-USD)", "NVDA").upper()
    
    try:
        # Obtenir dades financeres amb yfinance
        ticker_data = yf.Ticker(t_in)
        info = ticker_data.info
        
        # Extracció de dades
        full_name = info.get('longName', t_in)
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        market_cap = info.get('marketCap', 0)
        description = info.get('longBusinessSummary', 'No hi ha descripció disponible.')
        
        # Preu i variació
        price = info.get('currentPrice') or info.get('regularMarketPrice', 0.0)
        prev_close = info.get('previousClose', 1.0)
        change = price - prev_close
        change_pct = (change / prev_close) * 100
        delta_color = "#00ffad" if change >= 0 else "#f23645"

        # 2. RENDERITZACIÓ CAPÇALERA
        st.markdown(f"""
            <div style="background-color: #151921; padding: 20px; border-radius: 10px; border: 1px solid #2d3439; margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h1 style="margin: 0; color: white; font-size: 2.5rem;">{t_in}</h1>
                        <p style="margin: 0; color: #888; font-size: 1.1rem;">{full_name}</p>
                        <p style="margin: 0; color: #555; font-size: 0.9rem;">{sector.upper()} · {industry.upper()}</p>
                        <p style="margin: 5px 0 0 0; color: #555; font-size: 0.8rem;">Market Cap: ${market_cap:,.0f}</p>
                    </div>
                    <div style="text-align: right;">
                        <h1 style="margin: 0; color: white; font-size: 2.5rem;">${price:,.2f}</h1>
                        <p style="margin: 0; color: {delta_color}; font-size: 1.2rem; font-weight: bold;">
                            {'+' if change >= 0 else ''}{change:,.2f} ({'+' if change >= 0 else ''}{change_pct:,.2f}%)
                        </p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 3. GRÀFIC DE TRADINGVIEW (Alçada ampliada a 650px)
        st.write("")
        tradingview_widget = f"""
            <div class="tradingview-widget-container" style="height:650px; width:100%;">
                <div id="tradingview_chart" style="height:100%; width:100%;"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                new TradingView.widget({{
                  "autosize": true,
                  "symbol": "{t_in}",
                  "interval": "D",
                  "timezone": "Etc/UTC",
                  "theme": "dark",
                  "style": "1",
                  "locale": "en",
                  "toolbar_bg": "#f1f3f6",
                  "enable_publishing": false,
                  "hide_side_toolbar": false,
                  "allow_symbol_change": true,
                  "container_id": "tradingview_chart"
                }});
                </script>
            </div>
        """
        # El paràmetre height de components.html ha de ser lleugerament superior al del div (650 vs 670)
        components.html(tradingview_widget, height=670)

        # 4. DESCRIPCIÓ BREU
        st.write("---")
        with st.expander(f"📖 Sobre {full_name}", expanded=True):
            st.write(description)

        # 5. BOTÓ GENERAR PROMPT RSU
        st.write("")
        if st.button("🚀 GENERAR PROMPT RSU"):
            model_ia, modelo_nombre, error_ia = get_ia_model()
            
            if error_ia:
                st.error(error_ia)
            else:
                with st.spinner(f"L'IA està analitzant els fonamentals de {t_in}..."):
                    template = obtener_prompt_github()
                    prompt_final = f"Analitza {t_in} seguint això: {template.replace('[TICKER]', t_in)}"
                    try:
                        res = model_ia.generate_content(prompt_final)
                        text = getattr(res, "text", None)
                        if text:
                            st.markdown("---")
                            st.markdown(f"### 🤖 IA Strategic Analysis")
                            st.markdown(f'<div class="prompt-container">{text}</div>', unsafe_allow_html=True)
                        else:
                            st.warning("No s'ha pogut obtenir text del model.")
                    except Exception as e:
                        st.error(f"Error de l'IA: {e}")

    except Exception as e:
        st.error(f"No s'han pogut carregar les dades per a {t_in}. Revisa el Ticker.")

    st.caption(f"Market Data: Yahoo Finance | Chart: TradingView")

