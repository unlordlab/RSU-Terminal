import streamlit as st
import yfinance as yf
import pandas as pd
from config import get_ia_model

def get_earnings_data(ticker_symbol):
    """Extrae datos financieros clave con manejo de errores robusto."""
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    
    # Manejo robusto del calendario
    next_date = "No disponible"
    try:
        calendar = stock.calendar
        if calendar is not None:
            # En versiones nuevas es un dict, en viejas un DF
            if isinstance(calendar, dict):
                next_date = calendar.get('Earnings Date', ["N/A"])[0]
            elif isinstance(calendar, pd.DataFrame):
                if 'Value' in calendar.columns:
                    next_date = calendar.loc['Earnings Date', 'Value']
                else:
                    next_date = calendar.iloc[0, 0]
    except:
        pass

    # Construcción del diccionario con valores por defecto para evitar errores
    data = {
        "ticker": ticker_symbol,
        "name": info.get('longName', ticker_symbol),
        "price": info.get('currentPrice', "N/A"),
        "revenue_growth": info.get('revenueGrowth'),
        "ebitda_margins": info.get('ebitdaMargins'),
        "eps_actual": info.get('trailingEps'),
        "forward_pe": info.get('forwardPE'),
        "debt_to_equity": info.get('debtToEquity'),
        "free_cash_flow": info.get('freeCashflow'),
        "next_earnings": next_date
    }
    return data

def generate_capyfin_style_analysis(data):
    """Usa Gemini para generar el análisis cualitativo."""
    model, _, _ = get_ia_model()
    if not model:
        return "⚠️ Error: Configura tu GEMINI_API_KEY en secrets para ver el análisis."

    # Formateamos los números para que la IA los entienda mejor
    rev_growth = f"{data['revenue_growth']:.2%}" if data['revenue_growth'] else "Dato no disponible"
    
    prompt = f"""
    Actúa como un analista senior de Capyfin. Analiza estos datos de {data['name']} ({data['ticker']}):
    - Crecimiento Ingresos: {rev_growth}
    - Margen EBITDA: {data['ebitda_margins']}
    - EPS (Beneficio por acción): {data['eps_actual']}
    - PER Adelantado: {data['forward_pe']}
    - Ratio Deuda/Patrimonio: {data['debt_to_equity']}
    
    Genera un informe con este formato Markdown:
    
    ### 📊 Métricas Clave
    (3 puntos clave sobre su valoración y crecimiento)
    
    ### ✅ Puntos Fuertes
    - (Punto 1)
    - (Punto 2)
    
    ### ❌ Puntos Débiles
    - (Punto 1)
    - (Punto 2)
    
    ### 💡 Conclusión
    (Sentimiento final en una frase)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error en la IA: {e}"

def render():
    st.title("📅 Earnings Insight (Capyfin Style)")
    st.markdown("---")
    
    ticker = st.text_input("Introduce el Ticker", value="AAPL").upper()
    
    if st.button("Generar Reporte"):
        if not ticker:
            st.warning("Por favor, introduce un ticker.")
            return

        with st.spinner(f"Consultando datos de {ticker}..."):
            try:
                data = get_earnings_data(ticker)
                
                # Si info está casi vacío, yfinance falló
                if data['price'] == "N/A":
                    st.error(f"No se encontraron datos para {ticker}. Revisa si el ticker es correcto en Yahoo Finance.")
                    return

                # Visualización de métricas superiores
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Precio", f"${data['price']}")
                c2.metric("Próximo Reporte", str(data['next_earnings']))
                
                rev_val = f"{data['revenue_growth']:.2%}" if data['revenue_growth'] else "N/A"
                c3.metric("Rev. Growth", rev_val)
                
                pe_val = f"{data['forward_pe']:.2f}" if data['forward_pe'] else "N/A"
                c4.metric("Forward P/E", pe_val)
                
                st.markdown("---")
                
                # Análisis de IA
                analysis = generate_capyfin_style_analysis(data)
                st.markdown(analysis)
                
            except Exception as e:
                st.error(f"Error crítico: {e}")
