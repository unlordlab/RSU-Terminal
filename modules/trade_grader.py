# modules/backend_tester.py
"""
Herramienta de diagnóstico para probar conexión con backend Railway
NO MODIFICA NINGÚN MÓDULO EXISTENTE - Solo prueba la conexión
"""
import streamlit as st
import pandas as pd
from modules.api_client import get_api_client

def render():
    st.title("🔧 Backend Tester - Diagnóstico")
    st.markdown("Herramienta para verificar conexión con backend Railway")
    
    # Inicializar cliente
    client = get_api_client()
    
    # ==========================================
    # SECCIÓN 1: TEST DE CONEXIÓN BÁSICA
    # ==========================================
    st.header("1️⃣ Test de Conexión Básica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Probar Conexión", use_container_width=True):
            with st.spinner("Conectando..."):
                if client.test_connection():
                    st.success("✅ Backend respondiendo")
                else:
                    st.error("❌ Backend no responde")
                    st.info(f"URL configurada: `{client.base_url}`")
    
    with col2:
        st.markdown("**URL del backend:**")
        st.code(client.base_url)
        st.caption("Esta URL viene de los secrets de Streamlit")
    
    # ==========================================
    # SECCIÓN 2: TEST DE PRECIOS
    # ==========================================
    st.header("2️⃣ Test de Precios en Tiempo Real")
    
    symbol = st.text_input("Símbolo a consultar", "AAPL", key="test_symbol")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💰 Precio Simple", use_container_width=True):
            with st.spinner("Consultando..."):
                data = client.get_price(symbol)
                if data:
                    st.json(data)
                else:
                    st.error("Error obteniendo precio")
    
    with col2:
        if st.button("📊 Datos Históricos", use_container_width=True):
            with st.spinner("Descargando..."):
                df = client.get_history(symbol, "1mo")
                if df is not None:
                    st.success(f"✅ {len(df)} filas obtenidas")
                    st.dataframe(df.tail(5))
                    
                    # Gráfico rápido
                    st.line_chart(df["Close"])
                else:
                    st.error("Error obteniendo históricos")
    
    with col3:
        if st.button("⚡ Comparar con yfinance", use_container_width=True):
            with st.spinner("Comparando..."):
                # Backend
                start_time = pd.Timestamp.now()
                data_backend = client.get_price(symbol)
                time_backend = (pd.Timestamp.now() - start_time).total_seconds()
                
                # yfinance directo
                start_time = pd.Timestamp.now()
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    time_yf = (pd.Timestamp.now() - start_time).total_seconds()
                    
                    # Comparar
                    st.markdown("**⏱️ Tiempos de respuesta:**")
                    st.markdown(f"- Backend: `{time_backend:.3f}s`")
                    st.markdown(f"- yfinance directo: `{time_yf:.3f}s`")
                    
                    if data_backend:
                        st.markdown("**💰 Precios:**")
                        st.markdown(f"- Backend: `${data_backend.get('price', 'N/A')}`")
                        st.markdown(f"- yfinance: `${info.get('regularMarketPrice', 'N/A')}`")
                        
                        if data_backend.get("from_cache"):
                            st.success("🟢 Datos desde cache (rápido)")
                        else:
                            st.info("📡 Datos frescos desde Yahoo")
                    
                except Exception as e:
                    st.error(f"Error yfinance: {e}")
    
    # ==========================================
    # SECCIÓN 3: TEST DE MÚLTIPLES SÍMBOLOS
    # ==========================================
    st.header("3️⃣ Test de Múltiples Símbolos (Batch)")
    
    symbols_input = st.text_input(
        "Símbolos separados por coma", 
        "AAPL,MSFT,GOOGL,AMZN,TSLA",
        key="batch_symbols"
    )
    
    if st.button("🚀 Consultar Batch", use_container_width=True):
        symbols = [s.strip().upper() for s in symbols_input.split(",")]
        
        progress_bar = st.progress(0)
        results = []
        
        for i, sym in enumerate(symbols):
            progress_bar.progress((i + 1) / len(symbols))
            data = client.get_price(sym)
            if data:
                results.append({
                    "Símbolo": sym,
                    "Precio": data.get("price", "N/A"),
                    "Cambio %": data.get("change", "N/A"),
                    "Cache": data.get("from_cache", "unknown")
                })
        
        progress_bar.empty()
        
        if results:
            df_results = pd.DataFrame(results)
            st.dataframe(df_results, use_container_width=True)
            
            # Estadísticas
            cache_hits = sum(1 for r in results if r["Cache"] != False)
            st.success(f"✅ {len(results)} símbolos | {cache_hits} desde cache")
    
    # ==========================================
    # SECCIÓN 4: DIAGNÓSTICO DE RED
    # ==========================================
    st.header("4️⃣ Diagnóstico de Red")
    
    with st.expander("Ver detalles técnicos"):
        st.markdown("**Configuración actual:**")
        st.json({
            "backend_url": client.base_url,
            "timeout_requests": "5s (precios), 10s (históricos)",
            "session_persistente": True,
            "cache_streamlit": "Activado (@st.cache_resource)"
        })
        
        st.markdown("**Endpoints disponibles:**")
        st.code(f"""
GET {client.base_url}/           -> Status general
GET {client.base_url}/health     -> Healthcheck
GET {client.base_url}/api/price/{{symbol}}   -> Precio
GET {client.base_url}/api/history/{{symbol}} -> Históricos
        """)
        
        if st.button("🌐 Abrir backend en navegador"):
            st.markdown(f"[Click para abrir]({client.base_url})")
    
    # ==========================================
    # SECCIÓN 5: ESTADO DEL SISTEMA
    # ==========================================
    st.header("5️⃣ Estado del Sistema")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.metric(
            label="Backend",
            value="🟢 Online" if client.test_connection() else "🔴 Offline"
        )
    
    with status_col2:
        try:
            import yfinance as yf
            yf.Ticker("AAPL").info
            st.metric(label="yfinance", value="🟢 OK")
        except:
            st.metric(label="yfinance", value="🔴 Error")
    
    with status_col3:
        st.metric(label="Redis", value="⚪ Unknown")
        st.caption("Se verificará al consultar datos")

    # Footer
    st.markdown("---")
    st.caption("""
    💡 **Tip:** Si el backend está offline, los módulos automáticamente usarán yfinance como fallback.
    Esta herramienta no modifica ningún archivo existente.
    """)

# Si se ejecuta directamente
if __name__ == "__main__":
    render()
