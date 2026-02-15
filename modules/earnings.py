# ────────────────────────────────────────────────
# CARGA DE PROMPT RSU
# ────────────────────────────────────────────────

def load_rsu_prompt():
    """Carga el prompt de análisis hedge fund desde earnings.txt en raíz."""
    try:
        # earnings.py está en /modules/, subir un nivel para llegar a raíz
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'earnings.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error cargando prompt RSU: {e}")
        # Fallback al prompt original si no se encuentra el archivo
        return None

def get_earnings_data_for_prompt(ticker):
    """Obtiene datos específicos de earnings para enriquecer el prompt."""
    try:
        rate_limit_delay()
        ticker_obj = yf.Ticker(ticker)
        
        # Calendario de earnings (próximos y pasados)
        calendar = ticker_obj.calendar
        
        # Earnings históricos trimestrales
        quarterly_earnings = None
        try:
            quarterly = ticker_obj.quarterly_earnings
            if quarterly is not None and not quarterly.empty:
                quarterly_earnings = quarterly
        except:
            pass
            
        # Recomendaciones de analistas
        recommendations = None
        try:
            recs = ticker_obj.recommendations
            if recs is not None and not recs.empty:
                recommendations = recs.tail(10)
        except:
            pass
            
        # Upgrade/Downgrade recientes
        upgrades = None
        try:
            up = ticker_obj.upgrades_downgrades
            if up is not None and not up.empty:
                upgrades = up.head(10)
        except:
            pass
            
        return {
            'calendar': calendar,
            'quarterly_earnings': quarterly_earnings,
            'recommendations': recommendations,
            'upgrades': upgrades
        }
        
    except Exception as e:
        print(f"Error obteniendo datos de earnings: {e}")
        return {}

# ────────────────────────────────────────────────
# ANÁLISIS RSU HEDGE FUND (REEMPLAZA AI ANTERIOR)
# ────────────────────────────────────────────────

def render_rsu_earnings_analysis(data):
    """Renderiza Análisis Prompt RSU Earnings - Estilo Hedge Fund."""
    st.markdown("### 📊 Análisis Prompt RSU Earnings")
    
    # Cargar el prompt base
    base_prompt = load_rsu_prompt()
    
    if not base_prompt:
        st.warning("⚠️ Prompt RSU no encontrado. Verifica que earnings.txt esté en el directorio raíz.")
        return
    
    # Obtener datos adicionales de earnings
    earnings_extra = get_earnings_data_for_prompt(data['ticker'])
    
    # Construir contexto de datos para el prompt
    contexto_datos = f"""
DATOS EN TIEMPO REAL PARA {data['name']} ({data['ticker']}):

📈 DATOS DE MERCADO:
- Precio Actual: ${data['price']:.2f}
- Cambio: {data.get('change_pct', 0):+.2f}%
- Market Cap: {format_value(data['market_cap'], '$')}
- Beta: {data.get('beta', 'N/A')}
- Rango 52 semanas: ${data.get('fifty_two_low', 0):.2f} - ${data.get('fifty_two_high', 0):.2f}
- Volumen: {format_value(data['volume'], '', '', 0)}

💰 FUNDAMENTALES CLAVE:
- P/E Trailing: {format_value(data.get('pe_trailing'), '', 'x', 2)}
- P/E Forward: {format_value(data.get('pe_forward'), '', 'x', 2)}
- EPS Actual: ${data.get('eps', 'N/A')}
- EPS Forward: ${data.get('eps_forward', 'N/A')}
- Crecimiento Ingresos: {format_value(data.get('rev_growth'), '', '%', 2)}
- Margen Neto: {format_value(data.get('profit_margin'), '', '%', 2)}
- Margen EBITDA: {format_value(data.get('ebitda_margin'), '', '%', 2)}
- ROE: {format_value(data.get('roe'), '', '%', 2)}
- Deuda/Patrimonio: {format_value(data.get('debt_to_equity'), '', '%', 2)}

🏦 SALUD FINANCIERA:
- Cash Total: {format_value(data.get('cash'), '$')}
- Deuda Total: {format_value(data.get('debt'), '$')}
- Free Cash Flow: {format_value(data.get('free_cashflow'), '$')}
- Current Ratio: {data.get('current_ratio', 'N/A')}

🎯 CONSENSO DE ANALISTAS:
- Número de Analistas: {data.get('num_analysts', 'N/A')}
- Precio Objetivo Medio: ${data.get('target_mean', 0):.2f}
- Precio Objetivo Alto: ${data.get('target_high', 0):.2f}
- Precio Objetivo Bajo: ${data.get('target_low', 0):.2f}
- Recomendación: {data.get('recommendation', 'N/A').upper()}

📅 CALENDARIO DE EARNINGS:
{earnings_extra.get('calendar', 'No disponible')}

📊 EARNINGS TRIMESTRALES HISTÓRICOS:
{earnings_extra.get('quarterly_earnings', 'No disponible')}

⚡ RECOMENDACIONES RECIENTES:
{earnings_extra.get('recommendations', 'No disponible')}

🔄 UPGRADES/DOWNGRADES:
{earnings_extra.get('upgrades', 'No disponible')}
"""
    
    # Combinar prompt base + contexto
    prompt_completo = base_prompt + "\n\n" + contexto_datos + "\n\nGenera el reporte completo en español y formato markdown según las instrucciones anteriores."
    
    model, name, err = get_ia_model()
    
    if not model:
        st.info("🤖 IA no configurada. Configura tu API key en secrets.toml")
        return
    
    try:
        with st.spinner("🧠 Generando análisis hedge fund..."):
            # Configurar generación para respuestas más largas y detalladas
            generation_config = {
                "temperature": 0.3,  # Más preciso para análisis financiero
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,  # Más tokens para reporte completo
            }
            
            response = model.generate_content(
                prompt_completo,
                generation_config=generation_config
            )
            
            # Renderizar resultado con estilo RSU/hacker
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); 
                        border: 1px solid #00ffad; 
                        border-radius: 8px; 
                        padding: 0;
                        margin: 20px 0;
                        box-shadow: 0 0 20px rgba(0, 255, 173, 0.1);">
                <div style="background: #00ffad11; 
                            border-bottom: 1px solid #00ffad; 
                            padding: 15px 20px; 
                            display: flex; 
                            align-items: center; 
                            justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="color: #00ffad; font-size: 20px;">📈</span>
                        <span style="color: #00ffad; font-weight: bold; font-size: 14px; text-transform: uppercase; letter-spacing: 2px;">
                            RSU Hedge Fund Analysis
                        </span>
                    </div>
                    <span style="color: #00ffad; font-size: 11px; font-family: monospace;">
                        {data['ticker']} // {datetime.now().strftime('%Y-%m-%d %H:%M')}
                    </span>
                </div>
                <div style="padding: 25px; color: #e0e0e0; line-height: 1.8; font-size: 14px;">
                    {response.text}
                </div>
                <div style="background: #0c0e12; 
                            border-top: 1px solid #2a3f5f; 
                            padding: 10px 20px; 
                            font-size: 10px; 
                            color: #666; 
                            font-family: monospace;
                            display: flex;
                            justify-content: space-between;">
                    <span>Fuente: Gemini Pro + Yahoo Finance</span>
                    <span style="color: #00ffad;">RSU TERMINAL v1.0</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botón para copiar análisis
            st.code(response.text, language='markdown')
            
    except Exception as e:
        st.error(f"❌ Error generando análisis: {e}")
        st.info("Intenta recargar la página o verifica tu configuración de API.")
