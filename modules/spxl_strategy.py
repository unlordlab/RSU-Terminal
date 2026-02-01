import streamlit as st
import pandas as pd
import yfinance as yf
import streamlit.components.v1 as components

def render():
    st.title("📈 ESTRATEGIA COMERCIAL SPXL")
    st.caption("Terminal RSU - Gestión de Compras Escaladas")

    # --- DATOS DE MERCADO ---
    try:
        ticker = "SPXL"
        data = yf.Ticker(ticker)
        hist = data.history(period="1y")
        if not hist.empty:
            precio_actual = hist['Close'].iloc[-1]
            max_periodo = hist['High'].max()
            caida_desde_max = ((precio_actual - max_periodo) / max_periodo) * 100
        else:
            precio_actual, max_periodo, caida_desde_max = 0, 0, 0
    except:
        precio_actual, max_periodo, caida_desde_max = 0, 0, 0

    # --- CALCULADORA Y GESTIÓN DE POSICIÓN ---
    col_input, col_metrics = st.columns([1, 1.5])

    with col_input:
        st.subheader("📝 Gestión de Capital")
        capital_total = st.number_input("Capital total para SPXL ($):", value=10000, step=500)
        precio_medio = st.number_input("Tu precio medio actual ($):", value=0.0, step=0.1)
        
        if precio_medio > 0:
            target_venta = precio_medio * 1.20
            st.success(f"🎯 **Venta (+20%): ${target_venta:.2f}**")

    with col_metrics:
        st.subheader("📊 Estado del Mercado")
        m1, m2 = st.columns(2)
        m1.metric("Precio Actual", f"${precio_actual:.2f}")
        m2.metric("Máximo Anual", f"${max_periodo:.2f}")
        
        if caida_desde_max <= -15:
            st.error(f"🚨 ALERTA: Caída del {caida_desde_max:.2f}%")
        else:
            st.info(f"Distancia al máximo: {caida_desde_max:.2f}%")

    st.write("---")

    # --- REGLAS DE COMPRA ---
    st.subheader("🪜 Plan de Ejecución")
    
    fases = [
        {"Fase": "1ª Compra", "Trigger": "-15% desde Máx", "Precio Ref": max_periodo * 0.85, "Capital": "20%", "Monto": capital_total * 0.20},
        {"Fase": "2ª Compra", "Trigger": "-10% desde 1ª", "Precio Ref": (max_periodo * 0.85) * 0.90, "Capital": "15%", "Monto": capital_total * 0.15},
        {"Fase": "3ª Compra", "Trigger": "-7% desde 2ª", "Precio Ref": ((max_periodo * 0.85) * 0.90) * 0.93, "Capital": "20%", "Monto": capital_total * 0.20},
        {"Fase": "4ª Compra", "Trigger": "-10% desde 3ª", "Precio Ref": (((max_periodo * 0.85) * 0.90) * 0.93) * 0.90, "Capital": "20%", "Monto": capital_total * 0.20},
    ]
    
    df_fases = pd.DataFrame(fases)
    st.table(df_fases.style.format({"Precio Ref": "{:.2f}$", "Monto": "{:,.2f}$"}))
    st.caption(f"💰 Reserva de Efectivo (25%): ${(capital_total * 0.25):,.2f}")

    # --- WIDGET TRADINGVIEW (CDS) ---
    st.write("---")
    st.subheader("🚨 Monitor de Riesgo (CDS - BAMLHOA0HYM2)")
    
    # Widget insertado mediante Iframe directo de TradingView
    tv_widget_html = """
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({
        "width": "100%",
        "height": 400,
        "symbol": "FRED:BAMLHOA0HYM2",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "es",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
      });
      </script>
    </div>
    """
    components.html(tv_widget_html, height=420)

    st.warning("⚠️ **Regla de Seguridad:** Si el gráfico anterior supera **10.7**, detén las compras.")
