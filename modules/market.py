import streamlit as st
from datetime import datetime, timedelta
from config import get_market_index, get_cnn_fear_greed
import requests
import streamlit.components.v1 as components

# Intentar importar investpy
try:
    import investpy
    INVESTPY_AVAILABLE = True
except ImportError:
    INVESTPY_AVAILABLE = False

# ────────────────────────────────────────────────
# FUNCIONS AUXILIARS
# ────────────────────────────────────────────────

def get_economic_calendar():
    """Obtiene el calendario económico de hoy y mañana."""
    if not INVESTPY_AVAILABLE:
        return get_fallback_economic_calendar()
    
    try:
        from_date = datetime.now().strftime('%d/%m/%Y')
        to_date = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')
        
        calendar = investpy.economic_calendar(
            time_zone='GMT',
            time_filter='time_only',
            from_date=from_date,
            to_date=to_date,
            countries=['united states', 'euro zone'],
            importances=['high', 'medium', 'low']
        )
        
        events = []
        for _, row in calendar.head(10).iterrows():
            time_str = row['time']
            if time_str and time_str != '':
                try:
                    hour, minute = map(int, time_str.split(':'))
                    hour_es = (hour + 1) % 24
                    time_es = f"{hour_es:02d}:{minute:02d}"
                except:
                    time_es = time_str
            else:
                time_es = "TBD"
            
            importance_map = {
                'high': 'High',
                'medium': 'Medium', 
                'low': 'Low'
            }
            impact = importance_map.get(row['importance'].lower(), 'Medium')
            
            events.append({
                "time": time_es,
                "event": row['event'],
                "imp": impact,
                "val": row.get('actual', '-'),
                "prev": row.get('previous', '-')
            })
        
        return events if events else get_fallback_economic_calendar()
        
    except Exception as e:
        return get_fallback_economic_calendar()

def get_fallback_economic_calendar():
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "High", "val": "-", "prev": "-"},
    ]

@st.cache_data(ttl=300)
def get_crypto_prices():
    """
    Obtiene los precios de las 5 principales criptomonedas por market cap.
    Usa CoinGecko API (gratuita, no requiere API key).
    """
    try:
        # CoinGecko API - top 5 criptos por market cap
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 5,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        cryptos = []
        for coin in data:
            symbol = coin['symbol'].upper()
            price = coin['current_price']
            change_24h = coin['price_change_percentage_24h']
            
            # Formatear precio según su magnitud
            if price >= 1000:
                price_str = f"{price:,.2f}"
            elif price >= 1:
                price_str = f"{price:,.2f}"
            else:
                price_str = f"{price:.4f}"
            
            # Formatear cambio porcentual
            if change_24h is not None:
                change_str = f"{change_24h:+.2f}%"
                change_color = "positive" if change_24h >= 0 else "negative"
            else:
                change_str = "N/A"
                change_color = "neutral"
            
            cryptos.append({
                'symbol': symbol,
                'name': coin['name'],
                'price': price_str,
                'change': change_str,
                'change_color': change_color,
                'market_cap': coin['market_cap'],
                'image': coin['image']
            })
        
        return cryptos
        
    except Exception as e:
        st.warning(f"Error obtenint preus de cripto: {str(e)[:50]}")
        return get_fallback_crypto_prices()

def get_fallback_crypto_prices():
    """Datos simulados como fallback"""
    return [
        {"symbol": "BTC", "name": "Bitcoin", "price": "104,231.50", "change": "+2.4%", "change_color": "positive"},
        {"symbol": "ETH", "name": "Ethereum", "price": "3,120.12", "change": "-1.1%", "change_color": "negative"},
        {"symbol": "BNB", "name": "BNB", "price": "685.45", "change": "+0.8%", "change_color": "positive"},
        {"symbol": "SOL", "name": "Solana", "price": "245.88", "change": "+5.7%", "change_color": "positive"},
        {"symbol": "XRP", "name": "XRP", "price": "3.15", "change": "-2.3%", "change_color": "negative"},
    ]

def get_earnings_calendar():
    return [
        ("AAPL", "Feb 05", "After Market", "High"),
        ("AMZN", "Feb 05", "After Market", "High"),
        ("GOOGL", "Feb 06", "Before Bell", "High"),
        ("TSLA", "Feb 07", "After Market", "High"),
    ]

def get_insider_trading():
    return [
        ("NVDA", "CEO", "SELL", "$12.5M"),
        ("MSFT", "CFO", "BUY", "$1.2M"),
        ("PLTR", "DIR", "BUY", "$450K"),
        ("TSLA", "DIR", "SELL", "$2.1M"),
    ]

def get_fallback_news():
    return [
        {"time": "19:45", "title": "Tesla supera expectatives i puja un 8% després del tancament", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "18:30", "title": "El PIB dels EUA creix un 2,3% al darrer trimestre", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "16:15", "title": "Apple presenta resultats rècord gràcies a serveis", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "14:00", "title": "La inflació subjacent a la zona euro es modera al 2,7%", "impact": "Moderado", "color": "#ff9800", "link": "#"},
        {"time": "12:30", "title": "Microsoft Cloud supera els 30.000 milions en ingressos", "impact": "Alto", "color": "#f23645", "link": "#"},
    ]

@st.cache_data(ttl=300)
def fetch_finnhub_news():
    api_key = st.secrets.get("FINNHUB_API_KEY", None)
    
    if not api_key:
        return get_fallback_news()

    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        data = r.json()

        news_list = []
        for item in data[:8]:
            title = item.get("headline", "Sense títol")
            link = item.get("url", "#")
            timestamp = item.get("datetime", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "N/A"

            lower = title.lower()
            if any(k in lower for k in ["earnings", "profit", "revenue", "gdp", "fed", "fomc", "inflation", "employment"]):
                impact = "Alto"
                color = "#f23645"
            else:
                impact = "Moderado"
                color = "#ff9800"

            news_list.append({
                "time": time_str,
                "title": title,
                "impact": impact,
                "color": color,
                "link": link
            })
        return news_list if news_list else get_fallback_news()
    except Exception as e:
        return get_fallback_news()


def get_fed_liquidity():
    api_key = st.secrets.get("FRED_API_KEY", None)
    
    if not api_key:
        return "ERROR", "#888", "API Key no configurada", "N/A", "N/A"
    
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=WALCL&api_key={api_key}&file_type=json&limit=10&sort_order=desc"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            if len(observations) >= 2:
                latest_val = float(observations[0]['value'])
                prev_val = float(observations[1]['value'])
                date_latest = observations[0]['date']
                change = latest_val - prev_val
                if change < -100:
                    status = "QT"
                    color = "#f23645"
                    desc = "Quantitative Tightening"
                elif change > 100:
                    status = "QE"
                    color = "#00ffad"
                    desc = "Quantitative Easing"
                else:
                    status = "STABLE"
                    color = "#ff9800"
                    desc = "Balance sheet stable"
                return status, color, desc, f"{latest_val/1000:.1f}T", date_latest
        return "ERROR", "#888", "API temporalment no disponible", "N/A", "N/A"
    except:
        return "N/A", "#888", "Sense connexió a FRED", "N/A", "N/A"


# ────────────────────────────────────────────────
# RENDER DEL DASHBOARD
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .tooltip-container {
            position: absolute;
            top: 50%;
            right: 12px;
            transform: translateY(-50%);
            cursor: help;
        }
        .tooltip-container .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px 12px;
            border-radius: 6px;
            position: absolute;
            z-index: 999;
            top: 140%;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s, visibility 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }

        .fng-legend {
            display: flex;
            justify-content: space-between;
            width: 100%;
            margin-top: 12px;
            font-size: 0.65rem;
            color: #ccc;
            text-align: center;
            padding: 0 10px;
        }
        .fng-legend-item {
            flex: 1;
            padding: 0 4px;
        }
        .fng-color-box {
            width: 100%;
            height: 6px;
            margin-bottom: 4px;
            border-radius: 3px;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .news-item {
            padding: 12px 15px;
            border-bottom: 1px solid #1a1e26;
            transition: background 0.2s;
        }
        .news-item:hover {
            background: #0c0e12;
        }
        .news-item:last-child {
            border-bottom: none;
        }
        .impact-badge {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: bold;
        }
        .news-link {
            color: #00ffad;
            text-decoration: none;
            font-size: 0.85rem;
        }
        .news-link:hover {
            text-decoration: underline;
        }
        
        .group-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
        }
        .group-header {
            background: #0c0e12;
            padding: 12px 15px;
            border-bottom: 1px solid #1a1e26;
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .group-title {
            margin: 0;
            color: white;
            font-size: 14px;
            font-weight: bold;
        }
        .group-content {
            padding: 0;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    H = "340px"

    # FILA 1
    col1, col2, col3 = st.columns(3)

    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1] >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{get_market_index(t)[1]:+.2f}%</div></div>
            </div>''' for t, n in indices])
        tooltip = "Rendiment en temps real dels principals índexs borsaris dels EUA."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        events = get_economic_calendar()
        
        impact_colors = {
            'High': '#f23645',
            'Medium': '#ff9800',
            'Low': '#4caf50'
        }
        
        events_html = "".join([f'''
            <div style="padding:10px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;">
                <div style="color:#888; font-size:10px; width:45px; font-family:monospace;">{ev['time']}</div>
                <div style="flex-grow:1; margin-left:10px;">
                    <div style="color:white; font-size:11px; font-weight:500; line-height:1.3;">{ev['event']}</div>
                    <div style="color:{impact_colors.get(ev['imp'], '#888')}; font-size:8px; font-weight:bold; text-transform:uppercase; margin-top:3px;">
                        {'● ' + ev['imp'] + ' IMPACT'}
                    </div>
                </div>
                <div style="text-align:right; min-width:50px;">
                    <div style="color:white; font-size:11px; font-weight:bold;">{ev['val']}</div>
                    <div style="color:#444; font-size:9px;">P: {ev['prev']}</div>
                </div>
            </div>''' for ev in events])
            
        tooltip = "Calendari econòmic en temps real (hora espanyola CET/CEST). Dades d'investpy."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Calendari Econòmic</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "NVDA", "PLTR", "TSLA"]
        reddit_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#333; font-weight:bold; font-size:10px;">{i+1:02d}</span>
                <span style="color:#00ffad; font-weight:bold; font-size:12px;">{tkr}</span>
                <span style="color:#f23645; font-size:8px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 5px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        tooltip = "Tickers més mencionats i trending a Reddit (WallStreetBets, etc)."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Social Pulse</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # FILA 2
    st.write("")
    c1, c2, c3 = st.columns(3)

    with c1:
        val = get_cnn_fear_greed()
        if val is None:
            val_display = "N/D"
            label = "ERROR DE CONNEXIÓ"
            col = "#888"
            bar_width = 50
            extra = " (refresca)"
        else:
            val_display = val
            bar_width = val
            if val <= 24:
                label, col = "EXTREME FEAR", "#d32f2f"
            elif val <= 44:
                label, col = "FEAR", "#f57c00"
            elif val <= 55:
                label, col = "NEUTRAL", "#ff9800"
            elif val <= 75:
                label, col = "GREED", "#4caf50"
            else:
                label, col = "EXTREME GREED", "#00ffad"
            extra = ""

        tooltip = "Índex CNN Fear & Greed – mesura el sentiment del mercat."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'

        st.markdown(f'''<div class="group-container">
            <div class="group-header">
                <p class="group-title">Fear & Greed Index</p>
                {info_icon}
            </div>
            <div class="group-content" style="background:#11141a; height:{H}; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px 15px;">
                <div style="font-size:4.2rem; font-weight:bold; color:{col};">{val_display}</div>
                <div style="color:white; font-size:1.1rem; letter-spacing:1.5px; font-weight:bold; margin:12px 0;">{label}{extra}</div>
                <div style="width:88%; background:#0c0e12; height:14px; border-radius:7px; margin:18px 0 12px 0; border:1px solid #1a1e26; overflow:hidden;">
                    <div style="width:{bar_width}%; background:linear-gradient(to right, {col}, {col}aa); height:100%; transition:width 0.8s ease;"></div>
                </div>
                <div class="fng-legend">
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#d32f2f;"></div><div>Extreme Fear</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#f57c00;"></div><div>Fear</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#ff9800;"></div><div>Neutral</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#4caf50;"></div><div>Greed</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#00ffad;"></div><div>Extreme Greed</div></div>
                </div>
            </div>
        </div>''', unsafe_allow_html=True)

    with c2:
        sectors = [("TECH", +1.24), ("FINL", -0.45), ("HLTH", +0.12), ("ENER", +2.10), ("CONS", -0.80), ("UTIL", -0.25)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px; font-weight:bold;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        tooltip = "Rendiment diari dels principals sectors del mercat (heatmap)."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Sectors Heatmap</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c3:
        # NUEVO: Precios reales de criptomonedas
        cryptos = get_crypto_prices()
        
        # Construir HTML para cada cripto
        crypto_html_parts = []
        for crypto in cryptos:
            symbol = crypto['symbol']
            name = crypto['name']
            price = crypto['price']
            change = crypto['change']
            
            # Determinar color del cambio
            if 'change_color' in crypto:
                color = "#00ffad" if crypto['change_color'] == 'positive' else "#f23645"
            else:
                color = "#00ffad" if "+" in change else "#f23645"
            
            # HTML para esta cripto
            crypto_html_parts.append(f'''
                <div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <div style="color:white; font-weight:bold; font-size:13px;">{symbol}</div>
                        <div style="color:#555; font-size:9px;">{name}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:white; font-size:13px; font-weight:bold;">${price}</div>
                        <div style="color:{color}; font-size:11px; font-weight:bold;">{change}</div>
                    </div>
                </div>
            ''')
        
        crypto_html = "".join(crypto_html_parts)
        
        tooltip = "Preus en temps real de les 5 principals criptomonedes per market cap (CoinGecko)."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

    # FILA 3
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)

    with f3c1:
        earnings = get_earnings_calendar()
        earn_html = "".join([f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:#00ffad; font-weight:bold; font-size:12px;">{t}</div><div style="color:#444; font-size:9px; font-weight:bold;">{d}</div></div>
            <div style="text-align:right;"><div style="color:#888; font-size:9px;">{tm}</div><span style="color:{"#f23645" if i=="High" else "#888"}; font-size:8px; font-weight:bold;">● {i}</span></div>
            </div>''' for t, d, tm, i in earnings])
        tooltip = "Calendari de publicació de resultats d'empreses importants aquesta setmana."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; overflow-y:auto;">{earn_html}</div></div>', unsafe_allow_html=True)

    with f3c2:
        insiders = get_insider_trading()
        insider_html = "".join([f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
            <div><div style="color:white; font-weight:bold; font-size:11px;">{t}</div><div style="color:#555; font-size:9px;">{p}</div></div>
            <div style="text-align:right;"><div style="color:{"#00ffad" if ty=="BUY" else "#f23645"}; font-weight:bold; font-size:10px;">{ty}</div><div style="color:#888; font-size:9px;">{a}</div></div>
            </div>''' for t, p, ty, a in insiders])
        tooltip = "Compres i vendes recents d'accions per part de directius i insiders."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; overflow-y:auto;">{insider_html}</div></div>', unsafe_allow_html=True)

    with f3c3:
        news = fetch_finnhub_news()
        
        tooltip_text = "Notícies d'alt impacte obtingudes via Finnhub API."
        
        # Construir HTML de noticias
        news_items_html = []
        for item in news:
            safe_title = item['title'].replace('"', '&quot;').replace("'", '&#39;')
            time_val = item['time']
            impact_val = item['impact']
            color_val = item['color']
            link_val = item['link']
            
            news_item = (
                '<div style="padding: 12px 15px; border-bottom: 1px solid #1a1e26;">'
                '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">'
                '<span style="color:#888;font-size:0.78rem;font-family:monospace;">' + time_val + '</span>'
                '<span style="padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; background-color:' + color_val + '22;color:' + color_val + ';">' + impact_val + '</span>'
                '</div>'
                '<div style="color:white;font-size:0.92rem;line-height:1.35;margin-bottom:8px;">' + safe_title + '</div>'
                '<a href="' + link_val + '" target="_blank" style="color: #00ffad; text-decoration: none; font-size: 0.85rem;">→ Llig la notícia completa</a>'
                '</div>'
            )
            news_items_html.append(news_item)
        
        news_content = "".join(news_items_html)
        
        # HTML completo con CSS inline para el tooltip
        full_html = '''<!DOCTYPE html>
<html>
<head>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }

.container {
    border: 1px solid #1a1e26;
    border-radius: 10px;
    overflow: hidden;
    background: #11141a;
    width: 100%;
}

.header {
    background: #0c0e12;
    padding: 12px 15px;
    border-bottom: 1px solid #1a1e26;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.title {
    color: white;
    font-size: 14px;
    font-weight: bold;
}

.tooltip-container {
    position: relative;
    cursor: help;
}

.tooltip-icon {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: #1a1e26;
    border: 2px solid #555;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #aaa;
    font-size: 16px;
    font-weight: bold;
}

.tooltip-text {
    visibility: hidden;
    width: 260px;
    background-color: #1e222d;
    color: #eee;
    text-align: left;
    padding: 10px 12px;
    border-radius: 6px;
    position: absolute;
    z-index: 999;
    top: 35px;
    right: -10px;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 12px;
    border: 1px solid #444;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

.tooltip-container:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}

.content {
    background: #11141a;
    height: 340px;
    overflow-y: auto;
}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="title">Notícies d'Alt Impacte</div>
        <div class="tooltip-container">
            <div class="tooltip-icon">?</div>
            <div class="tooltip-text">''' + tooltip_text + '''</div>
        </div>
    </div>
    <div class="content">
        ''' + news_content + '''
    </div>
</div>
</body>
</html>'''
        
        components.html(full_html, height=400, scrolling=False)

    # FILA 4
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)

    with f4c1:
        vix = get_market_index("^VIX")
        vix_html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
                <div style="font-size:4.2rem; font-weight:bold; color:white;">{vix[0]:.2f}</div>
                <div style="color:#f23645; font-size:1.4rem; font-weight:bold;">VIX INDEX</div>
                <div style="color:{"#00ffad" if vix[1]>=0 else "#f23645"}; font-size:1.2rem; font-weight:bold;">{vix[1]:+.2f}%</div>
                <div style="color:#555; font-size:0.9rem; margin-top:15px;">Volatility Index</div>
            </div>
        '''
        tooltip = "Índex de volatilitat CBOE (VIX) – mesura la por esperada al mercat."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">VIX Index</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{vix_html}</div></div>', unsafe_allow_html=True)

    with f4c2:
        status, color, desc, assets, date = get_fed_liquidity()
        fed_html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
                <div style="font-size:5rem; font-weight:bold; color:{color};">{status}</div>
                <div style="color:white; font-size:1.3rem; font-weight:bold; margin:10px 0;">{desc}</div>
                <div style="background:#0c0e12; padding:12px 20px; border-radius:8px; border:1px solid #1a1e26;">
                    <div style="font-size:1.8rem; color:white;">{assets}</div>
                    <div style="color:#888; font-size:0.9rem;">Total Assets (FED)</div>
                </div>
                <div style="color:#555; font-size:0.8rem; margin-top:12px;">Actualitzat: {date}</div>
            </div>
        '''
        tooltip = "Política de liquiditat de la FED: expansió (QE) / contracció (QT) segons balanç."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">FED Liquidity Policy</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{fed_html}</div></div>', unsafe_allow_html=True)

    with f4c3:
        tnx = get_market_index("^TNX")
        tnx_html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
                <div style="font-size:4.2rem; font-weight:bold; color:white;">{tnx[0]:.2f}%</div>
                <div style="color:white; font-size:1.4rem; font-weight:bold;">10Y TREASURY</div>
                <div style="color:{"#00ffad" if tnx[1]>=0 else "#f23645"}; font-size:1.2rem; font-weight:bold;">{tnx[1]:+.2f}%</div>
                <div style="color:#555; font-size:0.9rem; margin-top:15px;">US 10-Year Yield</div>
            </div>
        '''
        tooltip = "Rendiment del bo del Tresor dels EUA a 10 anys."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">10Y Treasury Yield</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{tnx_html}</div></div>', unsafe_allow_html=True)


# Final del fitxer market.py
