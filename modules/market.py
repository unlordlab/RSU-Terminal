# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    # Título principal con margen corregido
    st.markdown('<h1 style="margin-top:-60px; margin-bottom:25px;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.2])

    with col1:
        # CONTENEDOR NATIVO: Más estable que HTML manual
        with st.container(border=True):
            st.markdown('<p class="card-header-text">Market Indices</p>', unsafe_allow_html=True)
            
            indices = [
                ("S&P 500", "^GSPC"),
                ("NASDAQ 100", "^IXIC"),
                ("DOW JONES", "^DJI"),
                ("RUSSELL 2000", "^RUT")
            ]
            
            for name, ticker in indices:
                price, change = get_market_index(ticker)
                color = "pos" if change >= 0 else "neg"
                
                # Renderizamos solo la fila interna
                st.markdown(f"""
                    <div class="index-item">
                        <div>
                            <div style="font-weight:bold; font-size:14px; color:white;">{name}</div>
                            <div style="color:#555; font-size:10px;">{ticker}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:16px; font-weight:bold; color:white;">{price:,.2f}</div>
                            <div class="{color}" style="font-size:11px;">{change:+.2f}%</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    with col2:
        # CONTENEDOR NATIVO PARA EL WIDGET
        with st.container(border=True):
            st.markdown('<p class="card-header-text">US High Yield Credit Spreads (OAS)</p>', unsafe_allow_html=True)
            
            # El widget ahora es una pieza limpia de HTML
            tradingview_html = """
            <div id="tv_chart_market" style="height: 350px; width: 100%;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.MediumWidget({
              "symbols": [["FRED:BAMLH0A0HYM2|1D"]],
              "chartOnly": false, 
              "width": "100%", 
              "height": "100%",
              "locale": "en", 
              "colorTheme": "dark", 
              "gridLineColor": "transparent",
              "trendLineColor": "#f23645", 
              "underLineColor": "rgba(242, 54, 69, 0.1)",
              "container_id": "tv_chart_market"
            });
            </script>
            """
            components.html(tradingview_html, height=360)

    st.write("---")
