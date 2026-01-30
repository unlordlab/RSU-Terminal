# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    st.markdown('<h1 style="margin-top:-60px; margin-bottom:20px;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Proporción equilibrada
    col_idx, col_spread = st.columns([1, 1.5])
    
    with col_idx:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content">', unsafe_allow_html=True)
        indices = [
            {"label": "S&P 500", "full": "US 500 Index", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "Nasdaq Composite", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "Industrial Average", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "Small Cap Index", "t": "^RUT"}
        ]
        for idx in indices:
            p, c = get_market_index(idx['t'])
            color_class = "pos" if c >= 0 else "neg"
            st.markdown(f"""
                <div class="index-card">
                    <div><p class="index-ticker">{idx['label']}</p><p class="index-fullname">{idx['full']}</p></div>
                    <div style="text-align:right;"><p class="index-price">{p:,.2f}</p><span class="index-delta {color_class}">{c:+.2f}%</span></div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    with col_spread:
        # Altura del widget restando el header de la caja
        WIDGET_HEIGHT = 390 
        
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">US High Yield Credit Spreads (OAS)</p></div><div class="widget-content">', unsafe_allow_html=True)
        
        spread_widget = f"""
        <div style="height:{WIDGET_HEIGHT}px; width:100%;">
          <div id="tv_spread" style="height:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.MediumWidget({{
            "symbols": [["FRED:BAMLH0A0HYM2|1D"]],
            "chartOnly": false, 
            "width": "100%", 
            "height": "100%",
            "locale": "en", 
            "colorTheme": "dark", 
            "gridLineColor": "transparent",
            "trendLineColor": "#f23645", 
            "underLineColor": "rgba(242, 54, 69, 0.15)",
            "container_id": "tv_spread"
          }});
          </script>
        </div>
        """
        components.html(spread_widget, height=WIDGET_HEIGHT)
        st.markdown('</div></div>', unsafe_allow_html=True)

    st.write("---")
