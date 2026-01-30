
# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    st.markdown('<h1 style="margin-top:-60px; margin-bottom:20px;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    col_idx, col_spread = st.columns([1, 2])
    
    # --- CAJA IZQUIERDA: MARKET INDICES ---
    with col_idx:
        indices = [
            {"label": "S&P 500", "full": "US 500 Index", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "Nasdaq Composite", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "Industrial Average", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "Small Cap Index", "t": "^RUT"}
        ]
        
        # Generamos el HTML de todas las tarjetas primero
        cards_html = ""
        for idx in indices:
            p, c = get_market_index(idx['t'])
            color_class = "pos" if c >= 0 else "neg"
            price_display = f"{p:,.2f}" if p > 0 else "Cargando..."
            
            cards_html += f"""
                <div class="index-card">
                    <div>
                        <p class="index-ticker">{idx['label']}</p>
                        <p class="index-fullname">{idx['full']}</p>
                    </div>
                    <div style="text-align:right;">
                        <p class="index-price">{price_display}</p>
                        <span class="index-delta {color_class}">{c:+.2f}%</span>
                    </div>
                </div>
            """

        # Metemos TODO el bloque HTML junto para que no se "rompa" el div
        st.markdown(f"""
            <div class="group-container">
                <div class="group-header"><p class="group-title">Market Indices</p></div>
                <div class="group-content">
                    {cards_html}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- CAJA DERECHA: CREDIT SPREADS ---
    with col_spread:
        # Calculamos la altura para que coincida visualmente con los 4 índices de la izquierda
        # Cada tarjeta mide unos 85px + márgenes. 400px es el punto dulce.
        altura_grafico = 400
        
        # 1. Abrimos el contenedor oscuro
        st.markdown(f"""
            <div class="group-container">
                <div class="group-header"><p class="group-title">US High Yield Credit Spreads (OAS)</p></div>
                <div class="group-content" style="height: {altura_grafico + 20}px; padding: 10px;">
        """, unsafe_allow_html=True)
        
        # 2. Insertamos el componente de TradingView
        spread_widget = f"""
        <div style="height:{altura_grafico}px; width:100%;">
          <div id="tv_spread" style="height:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.MediumWidget({{
            "symbols": [["FRED:BAMLH0A0HYM2|1M"]],
            "chartOnly": true, "width": "100%", "height": "100%",
            "locale": "en", "colorTheme": "dark", "gridLineColor": "transparent",
            "trendLineColor": "#f23645", "underLineColor": "rgba(242, 54, 69, 0.15)",
            "container_id": "tv_spread"
          }});
          </script>
        </div>
        """
        components.html(spread_widget, height=altura_grafico)
        
        # 3. Cerramos el contenedor oscuro
        st.markdown('</div></div>', unsafe_allow_html=True)

    st.write("---")
