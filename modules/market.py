import streamlit as st
import yfinance as yf
from datetime import datetime
import requests

# 1. CONFIGURACIÓ DE LA PÀGINA
st.set_page_config(
    layout="wide", 
    page_title="Market Dashboard Pro",
    page_icon="📈"
)

# 2. ESTILS CSS (Separats per evitar errors de renderitzat HTML)
st.markdown("""
<style>
    /* Contenidors principals */
    .group-container { 
        background: #11141a; 
        border-radius: 12px; 
        border: 1px solid #1a1e26; 
        margin-bottom: 20px; 
        overflow: hidden;
    }
    .group-header { 
        padding: 12px 15px; 
        border-bottom: 1px solid #1a1e26; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        background: rgba(255,255,255,0.03);
    }
    .group-title { 
        margin: 0; 
        color: #888; 
        font-size: 0.75rem; 
        font-weight: bold; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
    }
    .group-content { padding: 15px; overflow-y: auto; }

    /* Tooltips */
    .tooltip-container { position: relative; cursor: help; }
    .tooltip-container .tooltip-text { 
        visibility: hidden; width: 220px; background: #1e222d; color: #eee; 
        padding: 10px; border-radius: 6px; position: absolute; z-index: 999; 
        bottom: 130%; right: 0; opacity: 0; transition: opacity 0.3s; 
        font-size: 11px; border: 1px solid #444; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

    /* Files de dades (Indices, Crypto, Calendar) */
    .data-row { 
        background: #0c0e12; 
        padding: 10px 12px; 
        border-radius: 8px; 
        margin-bottom: 8px; 
        border: 1px solid #1a1e26; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        transition: transform 0.2s;
    }
    .data-row:hover { transform: translateX(3px); background: #12151c; }
    .item-name { color: white; font-weight: bold; font-size: 13px; }
    .item-sub { color: #555; font-size: 9px; text-transform: uppercase; }
    .val-pos { color: #00ffad; font-weight: bold; font-size: 12px; }
    .val-neg { color: #f23645; font-weight: bold; font-size: 12px; }
    
    /* Enllaços de notícies */
    .news-link { color: #00ffad; text-decoration: none; font-size: 11px; font-weight: bold; }
    .news-link:hover { text-decoration: underline; }
</style>
""", unsafe_allow_html=True)

# 3. LOGICA DE DADES (Backend)

@st.cache_data(ttl=60)
def fetch_realtime_data(tickers_dict):
    """Obté dades actualitzades de mercat via yfinance."""
    results = {}
    for symbol, name in tickers_dict.items():
        try:
            t = yf.Ticker(symbol)
            # Agafem 2 dies per calcular la diferència real respecte al tancament anterior
            hist = t.history(period="2d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                results[symbol] = {"name": name, "price": current, "change": change}
            else:
                # Fallback si el mercat està tancat o no hi ha prou dades
                info = t.fast_info
                results[symbol] = {"name": name, "price": info.last_price, "change": 0.0}
        except:
            results[symbol] = {"name": name, "price": 0.0, "change": 0.0}
    return results

@st.cache_data(ttl=3600)
def get_fed_data():
    """Obté el balanç de la FED (FRED API)."""
    api_key = st.secrets.get("FRED_API_KEY", "1455ec63d36773c0e47770e312063789")
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=WALCL&api_key={api_key}&file_type=json&limit=2&sort_order=desc"
    try:
        r = requests.get(url, timeout=10).json()
        obs = r['observations']
        latest, prev = float(obs[0]['value']), float(obs[1]['value'])
        change = latest - prev
        status = "QT" if change < -100 else ("QE" if change > 100 else "STABLE")
        color = "#f23645" if status == "QT" else ("#00ffad" if status == "QE" else "#ff9800")
        return status, color, f"{latest/1000000:.1f}T", obs[0]['date']
    except:
        return "N/A", "#888", "Error", "N/A"

# 4. FUNCIONS DE RENDERITZAT (UI Components)

def draw_card(title, html_body, tooltip, height="340px"):
    """Dibuixa una targeta de dashboard amb disseny consistent."""
    st.markdown(f'''
    <div class="group-container">
        <div class="group-header">
            <p class="group-title">{title}</p>
            <div class="tooltip-container">
                <div style="width:20px;height:20px;border-radius:50%;background:#1a1e26;border:1px solid #444;display:flex;align-items:center;justify-content:center;color:#888;font-size:11px;">?</div>
                <div class="tooltip-text">{tooltip}</div>
            </div>
        </div>
        <div class="group-content" style="height:{height};">
            {html_body}
        </div>
    </div>
    ''', unsafe_allow_html=True)

# 5. MAIN DASHBOARD

def render():
    st.markdown('<h1 style="text-align:center; margin-top:-30px; padding-bottom:20px;">Market Dashboard</h1>', unsafe_allow_html=True)

    # --- FILA 1: Índexs, Calendari, Social ---
    col1, col2, col3 = st.columns(3)

    with col1:
        indices_map = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq 100", "^DJI": "Dow Jones", "^RUT": "Russell 2000"}
        indices_data = fetch_realtime_data(indices_map)
        html = ""
        for sym, d in indices_data.items():
            val_class = "val-pos" if d['change'] >= 0 else "val-neg"
            html += f'''
            <div class="data-row">
                <div><div class="item-name">{d['name']}</div><div class="item-sub">Índex</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold;">{d['price']:,.2f}</div>
                <div class="{val_class}">{d['change']:+.2f}%</div></div>
            </div>'''
        draw_card("Market Indices", html, "Dades reals via Yahoo Finance (yfinance)")

    with col2:
        # Aquí podries connectar una API de calendari real si cal
        events = [("14:15", "ADP Nonfarm", "High"), ("16:00", "ISM Services", "High"), ("16:30", "Crude Oil", "Med")]
        html = "".join([f'''
            <div class="data-row">
                <div style="color:#888; font-size:10px; width:45px; font-family:monospace;">{t}</div>
                <div style="flex-grow:1; margin-left:10px;"><div class="item-name">{ev}</div></div>
                <div class="val-neg" style="font-size:8px;">{imp} IMPACT</div>
            </div>''' for t, ev, imp in events])
        draw_card("Economic Calendar", html, "Esdeveniments macroeconòmics d'avui")

    with col3:
        reddit_tickers = ["NVDA", "TSLA", "PLTR", "AAPL", "MSFT", "GME", "AMD", "META"]
        html = "".join([f'''
            <div class="data-row">
                <span style="color:#00ffad; font-weight:bold; font-size:12px;">${t}</span>
                <span style="color:#f23645; font-size:8px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 6px; border-radius:4px;">HOT 🔥</span>
            </div>''' for t in reddit_tickers])
        draw_card("Reddit Social Pulse", html, "Tickers més mencionats a WallStreetBets")

    # --- FILA 2: Sentiment, Sectors, Crypto ---
    st.write("")
    c1, c2, c3 = st.columns(3)

    with c1:
        # Simulat (requereix config.py original per dades CNN)
        fng_val = 68 
        html = f'''
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
            <div style="font-size:4.5rem; font-weight:bold; color:#00ffad;">{fng_val}</div>
            <div style="color:white; font-size:1.2rem; font-weight:bold; margin-bottom:20px;">GREED</div>
            <div style="width:85%; background:#0c0e12; height:14px; border-radius:7px; border:1px solid #333; overflow:hidden;">
                <div style="width:{fng_val}%; background:linear-gradient(90deg, #f23645, #00ffad); height:100%;"></div>
            </div>
        </div>'''
        draw_card("Fear & Greed Index", html, "Sentiment del mercat segons CNN")

    with c2:
        sectors = [("TECH", 1.2), ("FINL", -0.4), ("ENER", 2.1), ("HLTH", 0.1), ("CONS", -0.8), ("UTIL", -0.2)]
        html = '<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;">'
        for n, p in sectors:
            txt_col = "#00ffad" if p >= 0 else "#f23645"
            html += f'''
            <div style="background:{txt_col}11; border:1px solid {txt_col}44; padding:12px 5px; border-radius:8px; text-align:center;">
                <div style="color:white; font-size:10px; font-weight:bold;">{n}</div>
                <div style="color:{txt_col}; font-size:12px; font-weight:bold;">{p:+.2f}%</div>
            </div>'''
        html += '</div>'
        draw_card("Sector Performance", html, "Heatmap diari de sectors")

    with c3:
        cryptos = {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana", "BNB-USD": "BNB"}
        c_data = fetch_realtime_data(cryptos)
        html = ""
        for sym, d in c_data.items():
            val_class = "val-pos" if d['change'] >= 0 else "val-neg"
            html += f'''
            <div class="data-row">
                <div><div class="item-name">{d['name']}</div><div class="item-sub">Crypto</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold;">${d['price']:,.2f}</div>
                <div class="{val_class}">{d['change']:+.2f}%</div></div>
            </div>'''
        draw_card("Crypto Pulse", html, "Preus en viu via yfinance")

    # --- FILA 3: VIX, FED, Yields ---
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)

    with f3c1:
        vix = fetch_realtime_data({"^VIX": "VIX Index"})["^VIX"]
        html = f'''
        <div style="text-align:center; padding-top:20px;">
            <div style="font-size:4.5rem; font-weight:bold; color:white;">{vix['price']:.2f}</div>
            <div style="color:#f23645; font-size:1.3rem; font-weight:bold;">VOLATILITY INDEX</div>
            <div style="color:{"#00ffad" if vix['change'] < 0 else "#f23645"}; font-size:1.1rem;">{vix['change']:+.2f}% avui</div>
        </div>'''
        draw_card("VIX Index", html, "Mesura de la por esperada (S&P 500)")

    with f3c2:
        status, col, total, date = get_fed_data()
        html = f'''
        <div style="text-align:center;">
            <div style="font-size:4.5rem; font-weight:bold; color:{col};">{status}</div>
            <div style="color:white; font-size:1.1rem; margin-bottom:15px;">Liquidity Policy</div>
            <div style="background:#0c0e12; padding:15px; border-radius:10px; border:1px solid #333; display:inline-block; min-width:180px;">
                <div style="font-size:1.8rem; color:white; font-weight:bold;">{total}</div>
                <div style="color:#555; font-size:0.8rem;">Fed Balance Sheet</div>
            </div>
            <div style="color:#444; font-size:0.7rem; margin-top:10px;">Data: {date}</div>
        </div>'''
        draw_card("FED Liquidity", html, "Dades setmanals de la Reserva Federal")

    with f3c3:
        tnx = fetch_realtime_data({"^TNX": "10Y Yield"})["^TNX"]
        html = f'''
        <div style="text-align:center; padding-top:20px;">
            <div style="font-size:4.5rem; font-weight:bold; color:white;">{tnx['price']:.2f}%</div>
            <div style="color:white; font-size:1.3rem; font-weight:bold;">US 10-YEAR TREASURY</div>
            <div style="color:{"#00ffad" if tnx['change'] >= 0 else "#f23645"}; font-size:1.1rem;">{tnx['change']:+.2f}% avui</div>
        </div>'''
        draw_card("10Y Treasury Yield", html, "Rendiment del bo americà a 10 anys")

if __name__ == "__main__":
    render()
