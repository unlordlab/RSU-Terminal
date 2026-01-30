# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    st.markdown("## Market Dashboard")
    
    col_idx, col_spread = st.columns([1, 2])
    
    # --- CAIXA ESQUERRA: ÍNDEXS ---
    with col_idx:
        st.markdown('<div class="group-container">', unsafe_allow_html=True)
        st.markdown('<div class="group-title">Market Indices</div>', unsafe_allow_html=True)
        
        indices = [
            {"label": "SPY", "t": "SPY"},
            {"label": "QQQ", "t": "QQQ"},
            {"label": "DIA", "t": "DIA"},
            {"label": "IWM", "t": "IWM"}
        ]
        
        for idx in indices:
            p, c = get_market_index(idx['t'])
            color_class = "pos" if c >= 0 else "neg"
            st.markdown(f"""
                <div class="index-card">
                    <p class="index-ticker">{idx['label']}</p>
                    <div style="text-align:right;">
                        <p class="index-price">${p:,.2f}</p>
                        <span class="index-delta {color_class}">{c:+.2f}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- CAIXA DRETA: CREDIT SPREADS (Ticker BAMLH0A0HYM2) ---
    with col_spread:
        st.markdown('<div class="group-container">', unsafe_allow_html=True)
        st.markdown('<div class="group-title">US High Yield Credit Spreads (OAS)</div>', unsafe_allow_html=True)
        
        # Widget de TradingView mini per al Spread
        spread_widget = """
        <div style="height:250px;">
          <div id="tv_spread"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.MediumWidget({
            "symbols": [["FRED:BAMLH0A0HYM2|1M"]],
            "chartOnly": true,
            "width": "100%",
            "height": "100%",
            "locale": "en",
            "colorTheme": "dark",
            "gridLineColor": "rgba(42, 46, 57, 0)",
            "fontColor": "#787b86",
            "trendLineColor": "#f23645",
            "underLineColor": "rgba(242, 54, 69, 0.15)",
            "container_id": "tv_spread"
          });
          </script>
        </div>
        """
        components.html(spread_widget, height=255)
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")
    
    # 3. BUSCADOR I GRÀFIC GRAN DE TICKER
    t_search = st.text_input("🔍 Analitzar Ticker Específic", "NVDA").upper()
    
    main_chart = f"""
    <div style="height:600px;">
      <div id="tv_main"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true, "symbol": "{t_search}", "interval": "D", "timezone": "Etc/UTC",
        "theme": "dark", "style": "1", "locale": "en", "container_id": "tv_main"
      }});
      </script>
    </div>
    """
    components.html(main_chart, height=600)
