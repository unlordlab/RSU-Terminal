# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    st.markdown('<h1 style="margin-top:-60px; margin-bottom:20px;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Proporción ajustada para mejor visibilidad del gráfico
    col_left, col_right = st.columns([1, 1.2])
    
    # Altura exacta para que coincida con el CSS
    BOX_HEIGHT = 440 

    with col_left:
        indices = [
            {"label": "S&P 500", "full": "US 500 Index", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "Nasdaq Composite", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "Industrial Average", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "Small Cap Index", "t": "^RUT"}
        ]
        
        cards_html = ""
        for idx in indices:
            p, c = get_market_index(idx['t'])
            color_class = "pos" if c >= 0 else "neg"
            price = f"{p:,.2f}" if p > 0 else "Cargando..."
            
            cards_html += f"""
            <div class="index-card">
                <div>
                    <p style="color:white; font-weight:bold; margin:0; font-size:13px;">{idx['label']}</p>
                    <p style="color:#555; font-size:9px; margin:0;">{idx['full']}</p>
                </div>
                <div style="text-align:right;">
                    <p style="font-weight:bold; color:white; margin:0; font-size:15px;">{price}</p>
                    <span class="index-delta {color_class}" style="font-size:10px; padding:1px 5px; border-radius:4px;">{c:+.2f}%</span>
                </div>
            </div>"""

        st.markdown(f"""
            <div class="group-container">
                <div class="group-header"><p class="group-title">Market Indices</p></div>
                <div class="group-content">{cards_html}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        # Widget inyectado con su propio contenedor para control absoluto de bordes
        widget_html = f"""
        <div style="background-color: #11141a; border: 1px solid #2d3439; border-radius: 12px; height: {BOX_HEIGHT}px; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            <div style="background-color: #1a1e26; padding: 12px 20px; border-bottom: 1px solid #2d3439;">
                <p style="color: #888; font-size: 11px; font-weight: bold; text-transform: uppercase; margin: 0; letter-spacing: 0.5px;">US High Yield Credit Spreads (OAS)</p>
            </div>
            <div style="height: calc(100% - 45px); width: 100%;">
                <div id="tv_spread" style="height: 100%; width: 100%;"></div>
            </div>
        </div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.MediumWidget({{
          "symbols": [["FRED:BAMLH0A0HYM2|1D"]],
          "chartOnly": false, 
          "width": "100%", 
          "height": "100%",
          "locale": "en", 
          "colorTheme": "dark", 
          "gridLineColor": "rgba(42, 46, 57, 0)",
          "trendLineColor": "#f23645", 
          "underLineColor": "rgba(242, 54, 69, 0.1)",
          "container_id": "tv_spread"
        }});
        </script>
        """
        components.html(widget_html, height=BOX_HEIGHT + 5)

    st.write("---")
