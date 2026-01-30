
# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    st.markdown('<h1 style="margin-top:-60px; margin-bottom:20px;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    col_idx, col_spread = st.columns([1, 2])
    
    # --- COLUMNA IZQUIERDA: ÍNDICES ---
    with col_idx:
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
            price_val = f"{p:,.2f}" if p > 0 else "Cargando..."
            
            cards_html += f"""
            <div class="index-card">
                <div>
                    <p class="index-ticker">{idx['label']}</p>
                    <p class="index-fullname">{idx['full']}</p>
                </div>
                <div style="text-align:right;">
                    <p class="index-price">{price_val}</p>
                    <span class="index-delta {color_class}">{c:+.2f}%</span>
                </div>
            </div>"""

        st.markdown(f"""
            <div class="group-container">
                <div class="group-header"><p class="group-title">Market Indices</p></div>
                <div class="group-content">{cards_html}</div>
            </div>
        """, unsafe_allow_html=True)

    # --- COLUMNA DERECHA: CREDIT SPREADS ---
    with col_spread:
        # Altura calculada para igualar visualmente los 4 índices (aprox 415px)
        altura_optima = 415 

        # Iniciamos el contenedor oscuro
        st.markdown(f"""
            <div class="group-container" style="height: {altura_optima + 55}px;">
                <div class="group-header"><p class="group-title">US High Yield Credit Spreads (OAS)</p></div>
                <div class="group-content" style="padding: 10px; height: {altura_optima}px;">
        """, unsafe_allow_html=True)
        
        # Widget de TradingView ajustado a temporalidad diaria ("1D")
        widget_code = f"""
        <div style="height:{altura_optima - 20}px; width:100%;">
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
        # Renderizamos el widget dentro de la zona de contenido
        components.html(widget_code, height=altura_optima - 10)
        
        # Cerramos los divs del contenedor oscuro
        st.markdown("</div></div>", unsafe_allow_html=True)

    st.write("---")
