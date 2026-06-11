# modules/newsfeed.py  — RSU Terminal integration
"""
RSU News Feed — autocontenido, sin utils/, sin st.set_page_config(), sin st.sidebar.
"""
import re
import streamlit as st
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ══════════════════════════════════════════════════════════════════════
# SOURCES  (~50, matching HTML reference)
# ══════════════════════════════════════════════════════════════════════
SOURCES = [
    # ── Mainstream ──────────────────────────────────────────────────
    {"id":"reuters",     "label":"REUTERS",      "css":"src-reuters",     "url":"https://feeds.reuters.com/reuters/businessNews"},
    {"id":"wsj",         "label":"WSJ",          "css":"src-wsj",         "url":"https://feeds.a.dj.com/rss/RSSMarketsMain.xml"},
    {"id":"cnbc",        "label":"CNBC",         "css":"src-cnbc",        "url":"https://www.cnbc.com/id/20910258/device/rss/rss.html"},
    {"id":"ft",          "label":"FT",           "css":"src-ft",          "url":"https://www.ft.com/rss/home/uk"},
    {"id":"marketwatch", "label":"MKTWATCH",     "css":"src-marketwatch", "url":"https://feeds.content.dowjones.io/public/rss/mw_topstories"},
    # ── Policy / Regulatory ─────────────────────────────────────────
    {"id":"trump",       "label":"TRUMP",        "css":"src-trump",       "url":"https://truthsocial.com/@realDonaldTrump.rss","special":"trump"},
    {"id":"sec",         "label":"SEC 8-K",      "css":"src-sec",         "url":"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&dateb=&owner=include&count=20&output=atom","fmt":"atom"},
    {"id":"fed",         "label":"FED",          "css":"src-fed",         "url":"https://www.federalreserve.gov/feeds/press_all.xml","fmt":"atom"},
    {"id":"bce",         "label":"BCE",          "css":"src-bce",         "url":"https://www.ecb.europa.eu/rss/press.html"},
    {"id":"reddit",      "label":"REDDIT",       "css":"src-reddit",      "url":"https://www.reddit.com/r/investing+stocks+options/new.rss"},
    {"id":"zerohedge",   "label":"ZEROHEDGE",    "css":"src-zerohedge",   "url":"https://feeds.feedburner.com/zerohedge/feed"},
    {"id":"investing",   "label":"INVESTING",    "css":"src-investing",   "url":"https://www.investing.com/rss/news.rss"},
    # ── Finance analysts / newsletters ──────────────────────────────
    {"id":"kobeissi",    "label":"KOBEISSI",     "css":"src-kobeissi",    "url":"https://nitter.poast.org/KobeissiLetter/rss"},
    {"id":"tedzhang",    "label":"TED ZHANG",    "css":"src-tedzhang",    "url":"https://nitter.poast.org/tedzhangfin/rss"},
    {"id":"unusualwhales","label":"UNQ.WHALES",  "css":"src-unusualwhales","url":"https://unusualwhales.com/rss"},
    {"id":"calcrisk",    "label":"CALC.RISK",    "css":"src-calcrisk",    "url":"https://feeds.feedburner.com/CalculatedRisk"},
    {"id":"nakedcap",    "label":"NAKED CAP",    "css":"src-nakedcap",    "url":"https://www.nakedcapitalism.com/feed"},
    {"id":"ftalphaville","label":"FT ALPHAV",    "css":"src-ftalphaville","url":"https://ftalphaville.ft.com/feed/"},
    {"id":"bizinsider",  "label":"BUS.INSIDER",  "css":"src-bizinsider",  "url":"https://feeds.businessinsider.com/custom/all"},
    {"id":"yahoofinance","label":"YAHOO FIN",    "css":"src-yahoofinance","url":"https://finance.yahoo.com/rss/topstories"},
    {"id":"macroalf",    "label":"MACRO ALF",    "css":"src-macroalf",    "url":"https://themacrocompass.substack.com/feed","fmt":"atom"},
    {"id":"doomberg",    "label":"DOOMBERG",     "css":"src-doomberg",    "url":"https://doomberg.substack.com/feed","fmt":"atom"},
    {"id":"chartbook",   "label":"CHARTBOOK",    "css":"src-chartbook",   "url":"https://adamtooze.substack.com/feed","fmt":"atom"},
    {"id":"steno",       "label":"STENO",        "css":"src-steno",       "url":"https://stenoresearch.substack.com/feed","fmt":"atom"},
    {"id":"timiraos",    "label":"TIMIRAOS",     "css":"src-timiraos",    "url":"https://nitter.poast.org/NickTimiraos/rss"},
    {"id":"burry",       "label":"BURRY",        "css":"src-burry",       "url":"https://nitter.poast.org/michaeljburry/rss"},
    {"id":"blockworks",  "label":"BLOCKWORKS",   "css":"src-blockworks",  "url":"https://blockworks.co/feed"},
    {"id":"netinterest", "label":"NET INTEREST", "css":"src-netinterest", "url":"https://www.netinterest.co/feed","fmt":"atom"},
    {"id":"barchart",    "label":"BARCHART",     "css":"src-barchart",    "url":"https://www.barchart.com/news/rss"},
    {"id":"nasdaq",      "label":"NASDAQ",       "css":"src-nasdaq",      "url":"https://www.nasdaq.com/feed/rss/nasdaq-originals"},
    # ── Hedge funds ─────────────────────────────────────────────────
    {"id":"citadel",     "label":"CITADEL",      "css":"src-citadel",     "url":"https://www.citadel.com/research-insights/rss"},
    {"id":"bridgewater", "label":"BRIDGEWATER",  "css":"src-bridgewater", "url":"https://www.bridgewater.com/research-and-insights/rss"},
    {"id":"oaktree",     "label":"OAKTREE",      "css":"src-oaktree",     "url":"https://www.oaktreecapital.com/insights/rss"},
    {"id":"aqr",         "label":"AQR",          "css":"src-aqr",         "url":"https://www.aqr.com/insights/rss"},
    {"id":"point72",     "label":"POINT72",      "css":"src-point72",     "url":"https://www.point72.com/feed"},
    {"id":"elliott",     "label":"ELLIOTT",      "css":"src-elliott",     "url":"https://elliottinvestment.com/feed"},
    {"id":"ackman",      "label":"ACKMAN",       "css":"src-ackman",      "url":"https://nitter.poast.org/BillAckman/rss"},
    {"id":"drucken",     "label":"DRUCKEN",      "css":"src-drucken",     "url":"https://nitter.poast.org/StanleyDruckenmiller/rss"},
    {"id":"millennium",  "label":"MILLENNIUM",   "css":"src-millennium",  "url":"https://www.mlp.com/insights/rss"},
    # ── HF news ─────────────────────────────────────────────────────
    {"id":"hfnews",      "label":"HF NEWS",      "css":"src-hfnews",      "url":"https://www.hedgefundnews.com/feed"},
    {"id":"hedgeweek",   "label":"HEDGEWEEK",    "css":"src-hedgeweek",   "url":"https://www.hedgeweek.com/feed"},
    {"id":"valuewalk",   "label":"VALUEWALK",    "css":"src-valuewalk",   "url":"https://www.valuewalk.com/feed"},
    {"id":"insidermonkey","label":"INSDR MNKY",  "css":"src-insidermonkey","url":"https://www.insidermonkey.com/feed"},
    {"id":"marketfolly", "label":"MKT FOLLY",    "css":"src-marketfolly", "url":"https://www.marketfolly.com/feeds/posts/default?alt=rss"},
    {"id":"gurufocus",   "label":"GURUFOCUS",    "css":"src-gurufocus",   "url":"https://www.gurufocus.com/term/news/rss"},
    {"id":"dalio",       "label":"DALIO",        "css":"src-dalio",       "url":"https://nitter.poast.org/RayDalio/rss"},
    {"id":"seekingalpha","label":"SEKALPHA",     "css":"src-seekingalpha","url":"https://seekingalpha.com/market_currents.xml"},
    {"id":"benzinga",    "label":"BENZINGA",     "css":"src-benzinga",    "url":"https://www.benzinga.com/feed"},
    {"id":"hedgeco",     "label":"HEDGECO",      "css":"src-hedgeco",     "url":"https://www.hedgeco.net/feed"},
]

PRICE_TICKERS = {
    "S&P 500":"^GSPC","NASDAQ":"^IXIC","DOW":"^DJI","VIX":"^VIX",
    "EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"USDJPY=X",
    "BTC/USD":"BTC-USD","ETH/USD":"ETH-USD","SOL/USD":"SOL-USD",
    "GOLD":"GC=F","OIL WTI":"CL=F","10Y UST":"^TNX",
}
SECTORS_MAP = {
    "TECH":    ["nvidia","apple","microsoft","google","meta","tesla","amd","intel",
                "nvda","aapl","msft","googl","chip","semiconductor","ai","cloud","software"],
    "FINANCE": ["jpmorgan","goldman","bank","federal reserve","interest rate","yield",
                "treasury","fomc","jpm","gs","bac","bonds","lending","credit"],
    "ENERGY":  ["oil","gas","opec","crude","wti","brent","energy","xom","cvx"],
    "HEALTH":  ["pharma","fda","drug","biotech","clinical","vaccine","pfizer","jnj","merck"],
    "MACRO":   ["gdp","cpi","jobs","unemployment","recession","inflation","economy","fed ","fomc"],
    "CRYPTO":  ["bitcoin","btc","ethereum","eth","crypto","blockchain","sol","solana","xrp","defi"],
    "POLICY":  ["trump","white house","congress","tariff","sanction","executive order","regulation"],
    "DEFENSE": ["military","war","iran","ukraine","russia","china","taiwan","missile","pentagon"],
}
# Full keyword lists from HTML reference
HIGH_KW = [
    "fed","federal reserve","fomc","rate hike","rate cut","interest rate","basis points","bps",
    "recession","crash","collapse","default","bankrupt","bailout","systemic",
    "gdp miss","inflation surge","cpi","ppi","nonfarm","payrolls",
    "crisis","emergency","plunge","surge","halt","flash crash","circuit breaker",
    "acquisition","merger","sec","indictment","tariff","ban","war","sanction","breakout","breakdown",
]
MED_KW = [
    "earnings","revenue","profit","loss","guidance","forecast","outlook",
    "upgrade","downgrade","analyst","target price","rating",
    "oil","crude","wti","brent","opec","energy","gold","silver",
    "ipo","dividend","buyback","layoff","deal","quarterly","beat","miss",
]
LOW_KW = [
    "product launch","new feature","partnership","collaboration","award",
    "recognition","appointment","ceo","executive","conference","summit",
    "meeting","speech","interview","research","report","study","survey","index","upgrade rating",
]
BULL_KW = ["surge","rally","beats","upgrade","bullish","growth","record high","breakout",
           "strong","profit","gain","rise","boost","soar","jump","outperform","buy"]
BEAR_KW = ["plunge","crash","miss","downgrade","bearish","recession","default","crisis",
           "collapse","loss","decline","fall","weak","layoff","slump","underperform","sell"]
KNOWN_TICKERS = {
    "AAPL","MSFT","GOOGL","GOOG","AMZN","META","TSLA","NVDA","AMD","INTC",
    "JPM","GS","BAC","MS","C","WFC","XOM","CVX","JNJ","PFE","MRK",
    "SPY","QQQ","IWM","DIA","TLT","GLD","SLV","HYG","VXX","BTC","ETH","SOL",
    "UBER","LYFT","NFLX","DIS","PYPL","SQ","SHOP","CRM","SNOW","PLTR",
    "HOOD","COIN","MSTR","SMCI","ARM","AVGO","QCOM","MU","ASML","SOFI",
    "RIVN","NIO","BABA","JD","PDD","ROKU","ZM","DOCU","ORCL","IBM","DELL",
    "F","GM","BA","LMT","RTX","CAT","DE","GE","MMM","HON","UNH","V","MA",
}

# ══════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════
_CSS = """
<style>
/* ── TICKER ──────────────────────────────────────────────── */
.nf-ticker-wrap{overflow:hidden;height:30px;display:flex;align-items:center;
  background:#00e676;border-radius:4px;margin-bottom:14px;}
.nf-ticker-label{background:#000;color:#00e676;font-family:"VT323",monospace;
  font-size:17px;padding:0 14px;height:100%;display:flex;align-items:center;
  white-space:nowrap;flex-shrink:0;letter-spacing:.1em;z-index:2;}
.nf-ticker-track{display:flex;animation:nf-ticker 80s linear infinite;white-space:nowrap;}
.nf-ticker-item{font-family:"VT323",monospace;font-size:16px;color:#000;
  font-weight:bold;padding:0 26px;letter-spacing:.05em;}
.nf-t-up{color:#003320}.nf-t-down{color:#5a0010}
@keyframes nf-ticker{from{transform:translateX(0)}to{transform:translateX(-50%)}}

/* ── HEADER ──────────────────────────────────────────────── */
.nf-logo{font-family:"VT323",monospace;font-size:2.4rem;color:#00e676;
  text-shadow:0 0 18px rgba(0,230,118,.5);letter-spacing:.1em;line-height:1;}
.nf-sub{font-family:"Courier New",monospace;font-size:.55rem;color:#4a4a68;
  letter-spacing:.2em;text-transform:uppercase;margin-bottom:4px;}
.nf-live-pill{display:inline-flex;align-items:center;gap:6px;
  background:rgba(255,23,68,.12);border:1px solid rgba(255,23,68,.3);
  padding:3px 10px;border-radius:2px;font-size:9px;color:#ff1744;
  letter-spacing:.15em;font-family:"Courier New",monospace;margin-bottom:6px;}
.nf-live-dot{width:6px;height:6px;border-radius:50%;background:#ff1744;
  display:inline-block;animation:nf-blink 1.2s ease-in-out infinite;}
@keyframes nf-blink{0%,100%{opacity:1}50%{opacity:.2}}
.nf-countdown{font-size:9px;color:#4a4a68;font-family:"Courier New",monospace;letter-spacing:.1em;}
#nf-cd-secs{color:#ffab00;}

/* ── STATUS STRIP ────────────────────────────────────────── */
.nf-status{display:flex;gap:16px;align-items:center;font-size:10px;color:#4a4a68;
  letter-spacing:.08em;padding:8px 0;border-bottom:1px solid #1c1c2a;margin-bottom:10px;
  font-family:"Courier New",monospace;flex-wrap:wrap;}
.nf-stat-item{display:flex;align-items:center;gap:5px;}
.nf-stat-dot{width:5px;height:5px;border-radius:50%;}
.nf-s-red{background:#ff1744}.nf-s-amber{background:#ffab00}
.nf-s-green{background:#00e676}.nf-s-blue{background:#448aff}
.nf-stat-n{color:#dde1f0;font-weight:600;}
.nf-stat-sep{color:#1c1c2a;}
.nf-stat-time{margin-left:auto;color:#4a4a68;}

/* ── STATS ROW (Impact/Sentiment/Timeline above feed) ─────── */
.nf-stats-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px;}
.nf-sbox{background:#0b0b10;border:1px solid #1c1c2a;border-radius:2px;overflow:hidden;margin-bottom:8px;}
.nf-sbox-hdr{padding:8px 14px;border-bottom:1px solid #1c1c2a;font-size:9px;
  letter-spacing:.2em;color:#6a6a88;background:#101018;
  font-family:"Courier New",monospace;text-transform:uppercase;}
.nf-sbox-hdr .acc{color:#00e676;}

/* Impact bars */
.nf-imp-bars{padding:10px 14px;display:flex;flex-direction:column;gap:7px;}
.nf-imp-row{display:flex;align-items:center;gap:8px;font-size:9px;font-family:"Courier New",monospace;}
.nf-imp-lbl{width:36px;letter-spacing:.1em;text-transform:uppercase;}
.nf-imp-lbl.high{color:#ff1744}.nf-imp-lbl.med{color:#ffab00}.nf-imp-lbl.low{color:#00e676}
.nf-imp-bw{flex:1;height:4px;background:#1c1c2a;border-radius:1px;overflow:hidden;}
.nf-imp-b{height:100%;border-radius:1px;}
.nf-imp-b.high{background:#ff1744}.nf-imp-b.med{background:#ffab00}.nf-imp-b.low{background:#00e676}
.nf-imp-n{color:#dde1f0;width:24px;text-align:right;}

/* Sentiment gauge */
.nf-sent-wrap{padding:10px 14px;display:flex;flex-direction:column;gap:8px;}
.nf-sent-lbl{display:flex;justify-content:space-between;font-size:9px;color:#6a6a88;
  letter-spacing:.1em;font-family:"Courier New",monospace;text-transform:uppercase;}
.nf-sent-bar-wrap{position:relative;height:8px;border-radius:4px;
  background:linear-gradient(90deg,#ff1744 0%,#ffab00 50%,#00e676 100%);opacity:.85;}
.nf-sent-needle{position:absolute;top:-2px;width:3px;height:12px;background:#fff;
  border-radius:1px;box-shadow:0 0 4px rgba(255,255,255,.8);transition:left .5s ease;}
.nf-sent-score{text-align:center;font-family:"VT323",monospace;font-size:1.2rem;letter-spacing:.1em;}

/* Timeline */
.nf-tl{display:flex;flex-direction:column;gap:4px;padding:10px 14px;}
.nf-tl-bars{display:flex;align-items:flex-end;gap:2px;height:50px;}
.nf-tl-bar{flex:1;background:#161620;border-radius:2px 2px 0 0;min-height:2px;}
.nf-tl-bar.imp-high{background:rgba(255,23,68,.6)}
.nf-tl-bar.imp-med{background:rgba(255,171,0,.6)}
.nf-tl-bar.imp-low{background:rgba(0,230,118,.5)}
.nf-tl-labels{display:flex;gap:2px;}
.nf-tl-lbl{flex:1;text-align:center;font-size:7px;color:#4a4a68;font-family:"Courier New",monospace;}

/* ── CARDS ───────────────────────────────────────────────── */
.nf-card{background:#0b0b10;border:1px solid #1c1c2a;border-left:3px solid #242434;
  padding:12px 14px 12px 16px;display:grid;grid-template-columns:56px 1fr;
  gap:12px;margin-bottom:2px;animation:nf-fadeUp .25s ease both;transition:background .12s;}
.nf-card:hover{background:#101018;}
.nf-card.high{border-left-color:#ff1744}
.nf-card.med{border-left-color:#ffab00}
.nf-card.low{border-left-color:#00e676}
.nf-card.trump{border-left-color:#ff6b35!important;background:rgba(255,107,53,.04);}
@keyframes nf-fadeUp{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
.nf-time-col{display:flex;flex-direction:column;align-items:center;gap:4px;padding-top:2px;}
.nf-mins{font-family:"VT323",monospace;font-size:22px;line-height:1;color:#dde1f0;}
.nf-mins-lbl{font-size:8px;color:#4a4a68;letter-spacing:.12em;font-family:"Courier New",monospace;text-align:center;}
.nf-impact-dot{width:7px;height:7px;border-radius:50%;margin-top:4px;}
.nf-dot-high{background:#ff1744;box-shadow:0 0 4px #ff1744}
.nf-dot-med{background:#ffab00;box-shadow:0 0 4px #ffab00}
.nf-dot-low{background:#00e676;box-shadow:0 0 4px #00e676}
.nf-score{font-size:8px;color:#4a4a68;letter-spacing:.05em;font-family:"Courier New",monospace;}
.nf-body{min-width:0;}
.nf-nc-header{display:flex;align-items:center;gap:7px;margin-bottom:5px;flex-wrap:wrap;}
.nf-src-badge{font-size:8px;letter-spacing:.12em;padding:2px 7px;border-radius:2px;
  border:1px solid;font-family:"Courier New",monospace;text-transform:uppercase;}
.nf-sector{font-size:8px;color:#4a4a68;letter-spacing:.12em;font-family:"Courier New",monospace;text-transform:uppercase;}
.nf-title{font-family:"VT323",monospace;font-size:1.2rem;font-weight:600;
  line-height:1.35;color:#dde1f0;margin-bottom:4px;}
.nf-title a{color:inherit;text-decoration:none;}.nf-title a:hover{color:#00e676;}
.nf-desc{font-size:9px;color:#6a6a88;line-height:1.5;margin-bottom:6px;
  font-family:"Courier New",monospace;display:-webkit-box;
  -webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.nf-keywords{display:flex;gap:4px;flex-wrap:wrap;align-items:center;}
.nf-kw{font-size:8px;padding:1px 6px;border-radius:1px;background:#161620;color:#6a6a88;
  border:1px solid #1c1c2a;letter-spacing:.06em;font-family:"Courier New",monospace;}
.nf-kw.hit{background:rgba(0,230,118,.07);color:#00e676;border-color:rgba(0,230,118,.2);}
.nf-kw.hit.red{background:rgba(255,23,68,.07);color:#ff1744;border-color:rgba(255,23,68,.2);}
.nf-tk{font-family:"Courier New",monospace;font-size:9px;font-weight:700;
  padding:1px 6px;border-radius:2px;background:rgba(68,138,255,.12);
  color:#6aa3ff;border:1px solid rgba(68,138,255,.3);letter-spacing:.03em;}
.nf-tk::before{content:"$";opacity:.6;}
.nf-sent-dot{display:inline-block;width:6px;height:6px;border-radius:50%;}
.nf-sent-bull{background:#00e676;box-shadow:0 0 4px #00e676}
.nf-sent-bear{background:#ff1744;box-shadow:0 0 4px #ff1744}

/* ── SOURCE BADGES ────────────────────────────────────────── */
.src-reuters{color:#f87171;border-color:rgba(248,113,113,.25);background:rgba(248,113,113,.07);}
.src-wsj{color:#94a3b8;border-color:rgba(148,163,184,.2);background:rgba(148,163,184,.06);}
.src-cnbc{color:#4ade80;border-color:rgba(74,222,128,.2);background:rgba(74,222,128,.06);}
.src-ft{color:#fb923c;border-color:rgba(251,146,60,.2);background:rgba(251,146,60,.06);}
.src-marketwatch{color:#a78bfa;border-color:rgba(167,139,250,.2);background:rgba(167,139,250,.07);}
.src-trump{color:#ff6b35;border-color:rgba(255,107,53,.35);background:rgba(255,107,53,.10);}
.src-sec{color:#448aff;border-color:rgba(68,138,255,.25);background:rgba(68,138,255,.10);}
.src-fed{color:#e040fb;border-color:rgba(224,64,251,.25);background:rgba(224,64,251,.07);}
.src-bce{color:#c084fc;border-color:rgba(192,132,252,.25);background:rgba(192,132,252,.07);}
.src-reddit{color:#ff4500;border-color:rgba(255,69,0,.25);background:rgba(255,69,0,.07);}
.src-zerohedge{color:#facc15;border-color:rgba(250,204,21,.25);background:rgba(250,204,21,.07);}
.src-investing{color:#38bdf8;border-color:rgba(56,189,248,.25);background:rgba(56,189,248,.07);}
.src-kobeissi{color:#f0abfc;border-color:rgba(240,171,252,.25);background:rgba(240,171,252,.07);}
.src-tedzhang{color:#86efac;border-color:rgba(134,239,172,.25);background:rgba(134,239,172,.07);}
.src-unusualwhales{color:#67e8f9;border-color:rgba(103,232,249,.25);background:rgba(103,232,249,.07);}
.src-calcrisk{color:#fda4af;border-color:rgba(253,164,175,.25);background:rgba(253,164,175,.07);}
.src-nakedcap{color:#d4d4d8;border-color:rgba(212,212,216,.2);background:rgba(212,212,216,.05);}
.src-ftalphaville{color:#fb923c;border-color:rgba(251,146,60,.2);background:rgba(251,146,60,.05);}
.src-bizinsider{color:#fb923c;border-color:rgba(251,146,60,.25);background:rgba(251,146,60,.07);}
.src-yahoofinance{color:#818cf8;border-color:rgba(129,140,248,.25);background:rgba(129,140,248,.07);}
.src-macroalf{color:#34d399;border-color:rgba(52,211,153,.25);background:rgba(52,211,153,.07);}
.src-doomberg{color:#f97316;border-color:rgba(249,115,22,.3);background:rgba(249,115,22,.08);}
.src-chartbook{color:#a78bfa;border-color:rgba(167,139,250,.25);background:rgba(167,139,250,.07);}
.src-steno{color:#22d3ee;border-color:rgba(34,211,238,.25);background:rgba(34,211,238,.07);}
.src-timiraos{color:#e2e8f0;border-color:rgba(226,232,240,.2);background:rgba(226,232,240,.05);}
.src-burry{color:#ef4444;border-color:rgba(239,68,68,.3);background:rgba(239,68,68,.08);}
.src-blockworks{color:#f59e0b;border-color:rgba(245,158,11,.3);background:rgba(245,158,11,.08);}
.src-netinterest{color:#6ee7b7;border-color:rgba(110,231,183,.25);background:rgba(110,231,183,.07);}
.src-barchart{color:#fb7185;border-color:rgba(251,113,133,.25);background:rgba(251,113,133,.07);}
.src-nasdaq{color:#60a5fa;border-color:rgba(96,165,250,.25);background:rgba(96,165,250,.07);}
.src-citadel{color:#fbbf24;border-color:rgba(251,191,36,.3);background:rgba(251,191,36,.08);}
.src-bridgewater{color:#34d399;border-color:rgba(52,211,153,.25);background:rgba(52,211,153,.06);}
.src-oaktree{color:#f97316;border-color:rgba(249,115,22,.3);background:rgba(249,115,22,.08);}
.src-aqr{color:#c084fc;border-color:rgba(192,132,252,.25);background:rgba(192,132,252,.07);}
.src-point72{color:#38bdf8;border-color:rgba(56,189,248,.25);background:rgba(56,189,248,.07);}
.src-elliott{color:#fb7185;border-color:rgba(251,113,133,.25);background:rgba(251,113,133,.07);}
.src-ackman{color:#38bdf8;border-color:rgba(56,189,248,.3);background:rgba(56,189,248,.08);}
.src-drucken{color:#e2e8f0;border-color:rgba(226,232,240,.2);background:rgba(226,232,240,.05);}
.src-millennium{color:#a78bfa;border-color:rgba(167,139,250,.25);background:rgba(167,139,250,.07);}
.src-hfnews{color:#94a3b8;border-color:rgba(148,163,184,.2);background:rgba(148,163,184,.05);}
.src-hedgeweek{color:#fbbf24;border-color:rgba(251,191,36,.3);background:rgba(251,191,36,.08);}
.src-valuewalk{color:#4ade80;border-color:rgba(74,222,128,.25);background:rgba(74,222,128,.07);}
.src-insidermonkey{color:#c084fc;border-color:rgba(192,132,252,.25);background:rgba(192,132,252,.07);}
.src-marketfolly{color:#94a3b8;border-color:rgba(148,163,184,.2);background:rgba(148,163,184,.06);}
.src-gurufocus{color:#f472b6;border-color:rgba(244,114,182,.25);background:rgba(244,114,182,.07);}
.src-dalio{color:#a3e635;border-color:rgba(163,230,53,.25);background:rgba(163,230,53,.07);}
.src-seekingalpha{color:#a3e635;border-color:rgba(163,230,53,.25);background:rgba(163,230,53,.07);}
.src-benzinga{color:#f59e0b;border-color:rgba(245,158,11,.3);background:rgba(245,158,11,.07);}
.src-hedgeco{color:#67e8f9;border-color:rgba(103,232,249,.25);background:rgba(103,232,249,.07);}
.src-generic{color:#6a6a88;border-color:#242434;background:transparent;}

/* ── TRUMP PANEL ─────────────────────────────────────────── */
.nf-trump-panel{background:rgba(255,107,53,.06);border:1px solid rgba(255,107,53,.25);
  border-radius:2px;overflow:hidden;margin-bottom:8px;}
.nf-trump-hdr{padding:8px 14px;border-bottom:1px solid rgba(255,107,53,.2);
  font-size:9px;letter-spacing:.2em;color:#ff6b35;background:rgba(255,107,53,.08);
  font-family:"Courier New",monospace;text-transform:uppercase;
  display:flex;align-items:center;gap:8px;}
.nf-trump-hdr .acc{color:#ff1744;}
.nf-trump-hdr-dot{width:6px;height:6px;border-radius:50%;background:#00e676;
  box-shadow:0 0 4px #00e676;animation:nf-blink 2s infinite;}
.nf-trump-post{padding:10px 14px;border-bottom:1px solid rgba(255,107,53,.12);}
.nf-trump-post:last-child{border-bottom:none;}
.nf-trump-text{font-size:10px;line-height:1.5;color:#dde1f0;margin-bottom:5px;
  font-family:"Courier New",monospace;}
.nf-trump-text a{color:#dde1f0;text-decoration:none;}.nf-trump-text a:hover{color:#ff6b35;}
.nf-trump-time{font-size:8px;color:#4a4a68;letter-spacing:.06em;font-family:"Courier New",monospace;}
.nf-trump-empty{padding:14px;font-size:9px;color:#4a4a68;
  font-family:"Courier New",monospace;letter-spacing:.1em;text-align:center;}

/* ── HEATMAP ─────────────────────────────────────────────── */
.nf-heatmap{display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:10px;}
.nf-hm-cell{padding:8px 10px;border-radius:2px;border:1px solid #1c1c2a;background:#161620;}
.nf-hm-cell.h0{background:#101018}.nf-hm-cell.h1{border-color:rgba(0,230,118,.3)}
.nf-hm-cell.h2{border-color:rgba(0,230,118,.5);background:rgba(0,230,118,.04)}
.nf-hm-cell.h3{border-color:rgba(255,171,0,.5);background:rgba(255,171,0,.04)}
.nf-hm-cell.h4{border-color:rgba(255,23,68,.5);background:rgba(255,23,68,.05)}
.nf-hm-cell.h5{border-color:#ff1744;background:rgba(255,23,68,.08);box-shadow:0 0 6px rgba(255,23,68,.2)}
.nf-hm-name{font-size:8px;letter-spacing:.1em;color:#6a6a88;margin-bottom:4px;font-family:"Courier New",monospace;}
.nf-hm-count{font-family:"VT323",monospace;font-size:22px;line-height:1;color:#dde1f0;}
.nf-hm-bar{height:2px;margin-top:5px;background:#1c1c2a;border-radius:1px;overflow:hidden;}
.nf-hm-fill{height:100%;border-radius:1px;background:#00e676;}

/* ── SOURCE HEALTH ───────────────────────────────────────── */
.nf-src-health{padding:10px 14px;display:flex;flex-direction:column;gap:6px;}
.nf-src-row{display:flex;align-items:center;gap:8px;font-size:9px;font-family:"Courier New",monospace;}
.nf-src-name{flex:1;color:#6a6a88;letter-spacing:.08em;}
.nf-src-count{color:#dde1f0;min-width:22px;text-align:right;}
.nf-src-bw{flex:2;height:3px;background:#1c1c2a;border-radius:1px;overflow:hidden;}
.nf-src-b{height:100%;background:#00e676;border-radius:1px;}
.nf-src-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0;}
.nf-src-ok{background:#00e676}.nf-src-err{background:#ff1744}
.nf-src-loading{background:#ffab00;animation:nf-blink 1s infinite;}

/* ── KEYWORDS LEGEND ─────────────────────────────────────── */
.nf-kw-legend{padding:10px 14px;}
.nf-kw-section{margin-bottom:8px;}
.nf-kw-title{font-size:8px;letter-spacing:.15em;margin-bottom:5px;
  font-family:"Courier New",monospace;text-transform:uppercase;}
.nf-kw-title.high{color:#ff1744}.nf-kw-title.med{color:#ffab00}.nf-kw-title.low{color:#00e676}
.nf-kw-list{display:flex;flex-wrap:wrap;gap:3px;}
.nf-kw-pill{font-size:8px;padding:1px 6px;border-radius:1px;font-family:"Courier New",monospace;}
.nf-kw-pill.high{background:rgba(255,23,68,.12);color:#ff1744;border:1px solid rgba(255,23,68,.2);}
.nf-kw-pill.med{background:rgba(255,171,0,.12);color:#ffab00;border:1px solid rgba(255,171,0,.2);}
.nf-kw-pill.low{background:rgba(0,230,118,.12);color:#00e676;border:1px solid rgba(0,230,118,.2);}

/* ── ALERTS ──────────────────────────────────────────────── */
.nf-alert-wrap{padding:10px 14px;display:flex;flex-direction:column;gap:10px;}
.nf-alert-row{display:flex;align-items:center;gap:8px;font-size:9px;
  font-family:"Courier New",monospace;color:#6a6a88;}
.nf-alert-row label{flex:1;cursor:pointer;letter-spacing:.06em;}
.nf-alert-status{padding:6px 10px;border-radius:2px;font-size:9px;text-align:center;
  letter-spacing:.1em;font-family:"Courier New",monospace;}
.nf-alert-on{background:rgba(255,23,68,.1);border:1px solid rgba(255,23,68,.3);color:#ff1744;}
.nf-alert-off{background:rgba(26,30,38,.5);border:1px solid #1c1c2a;color:#4a4a68;}

/* ── FILTER CHECKBOXES ───────────────────────────────────── */
.nf-filter-row{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;}

/* Streamlit checkbox label fix */
[data-testid="stCheckbox"] label p{
  font-family:"Courier New",monospace!important;
  font-size:.75rem!important;
  font-weight:600!important;
  letter-spacing:1px!important;
}

/* ── EMPTY ───────────────────────────────────────────────── */
.nf-empty{display:flex;flex-direction:column;align-items:center;padding:60px 20px;
  color:#4a4a68;font-size:11px;gap:10px;letter-spacing:.1em;font-family:"Courier New",monospace;}

/* expander style override */
[data-testid="stExpander"]{
  background:#0b0b10!important;border:1px solid #1c1c2a!important;border-radius:2px!important;
  margin-bottom:4px!important;
}
[data-testid="stExpander"] summary{
  font-family:"Courier New",monospace!important;font-size:.72rem!important;
  letter-spacing:.12em!important;text-transform:uppercase!important;
  color:#6a6a88!important;
}
</style>
"""

# ══════════════════════════════════════════════════════════════════════
# NLP
# ══════════════════════════════════════════════════════════════════════
def _classify_impact(text):
    t = text.lower()
    if any(k in t for k in HIGH_KW): return "high"
    if any(k in t for k in MED_KW):  return "med"
    if any(k in t for k in LOW_KW):  return "low"
    return "low"

def _sentiment(text):
    t = text.lower()
    b = sum(1 for k in BULL_KW if k in t)
    e = sum(1 for k in BEAR_KW if k in t)
    if b > e: return {"label":"bullish","score":b}
    if e > b: return {"label":"bearish","score":e}
    return {"label":"neutral","score":0}

def _sector(text):
    t = text.lower()
    for sec, kws in SECTORS_MAP.items():
        if any(k in t for k in kws): return sec
    return "GENERAL"

def _score(text):
    t = text.lower()
    s = 3
    s += sum(2 for k in HIGH_KW if k in t)
    s += sum(1 for k in MED_KW  if k in t)
    return min(10, s)

def _tickers(text):
    words = re.findall(r'\b[A-Z]{2,5}\b', text)
    return sorted({w for w in words if w in KNOWN_TICKERS})

def _mins_feedparser(entry):
    import calendar
    for field in ("published_parsed","updated_parsed"):
        val = getattr(entry, field, None)
        if val:
            try:
                dt = datetime.fromtimestamp(calendar.timegm(val), tz=timezone.utc)
                return max(0, int((datetime.now(timezone.utc)-dt).total_seconds()/60))
            except: pass
    return 30

def _mins_pubdate(s):
    import email.utils
    try:
        dt = email.utils.parsedate_to_datetime(s)
        return max(0, int((datetime.now(timezone.utc)-dt.astimezone(timezone.utc)).total_seconds()/60))
    except: return 30

def _build(title, desc, link, src, mins):
    combined = f"{title} {desc}"
    return {"title":title,"desc":desc[:300],"link":link,
            "src_id":src["id"],"src_label":src["label"],"src_css":src.get("css","src-generic"),
            "special":src.get("special"),
            "impact":_classify_impact(combined),"sentiment":_sentiment(combined),
            "sector":_sector(combined),"score":_score(combined),
            "tickers":_tickers(combined),"minutes_ago":mins}

# ══════════════════════════════════════════════════════════════════════
# FETCHING
# ══════════════════════════════════════════════════════════════════════
def _fetch_feedparser(src):
    import feedparser
    feed = feedparser.parse(src["url"])
    items = []
    for e in feed.entries[:30]:
        title = getattr(e,"title","") or ""
        raw   = getattr(e,"summary",None) or getattr(e,"description","") or ""
        desc  = re.sub(r"<[^>]+>","",raw)
        link  = getattr(e,"link","") or ""
        items.append(_build(title.strip(),desc.strip(),link.strip(),src,_mins_feedparser(e)))
    return items, len(items)>0

def _fetch_requests_rss(src):
    import requests, xml.etree.ElementTree as ET
    r = requests.get(src["url"],timeout=8,headers={"User-Agent":"RSU-Terminal/2.0"})
    root = ET.fromstring(r.text)
    items = []
    for item in root.findall(".//item")[:30]:
        title = (item.findtext("title") or "").strip()
        desc  = re.sub(r"<[^>]+>", (item.findtext("description") or "")).strip()
        link  = (item.findtext("link") or "").strip()
        pub   = item.findtext("pubDate") or ""
        items.append(_build(title,desc,link,src,_mins_pubdate(pub)))
    return items, len(items)>0

def _fetch_atom(src):
    import requests, xml.etree.ElementTree as ET
    ns = {"a":"http://www.w3.org/2005/Atom"}
    r = requests.get(src["url"],timeout=10,headers={"User-Agent":"RSU-Terminal/2.0"})
    root = ET.fromstring(r.text)
    items = []
    for entry in root.findall("a:entry",ns)[:20]:
        title   = (entry.findtext("a:title","",ns) or "").strip()
        summary = re.sub(r"<[^>]+>", (entry.findtext("a:summary","",ns) or "")).strip()
        le = entry.find("a:link",ns)
        link = le.get("href","") if le is not None else ""
        updated = (entry.findtext("a:updated","",ns) or "").strip()
        mins = 30
        try:
            dt = datetime.fromisoformat(updated.replace("Z","+00:00"))
            mins = max(0,int((datetime.now(timezone.utc)-dt).total_seconds()/60))
        except: pass
        items.append(_build(title,summary[:300],link,src,mins))
    return items, len(items)>0

def _fetch_source(src):
    fmt = src.get("fmt","rss")
    try:
        if fmt == "atom":
            return _fetch_atom(src)
        return _fetch_feedparser(src)
    except ImportError:
        pass
    except Exception:
        if fmt == "atom":
            return [], False
    try:
        return _fetch_requests_rss(src)
    except: pass
    return [], False

@st.cache_data(ttl=120, show_spinner=False)
def _load_news():
    all_items, status = [], {}
    with ThreadPoolExecutor(max_workers=min(len(SOURCES),16)) as ex:
        futures = {ex.submit(_fetch_source,s):s for s in SOURCES}
        for fut in as_completed(futures):
            src = futures[fut]
            try:
                items, ok = fut.result()
                all_items.extend(items)
                status[src["id"]] = {"count":len(items),"ok":ok}
            except:
                status[src["id"]] = {"count":0,"ok":False}
    all_items.sort(key=lambda x: x["minutes_ago"])
    return all_items, status

@st.cache_data(ttl=60, show_spinner=False)
def _load_prices():
    try:
        import yfinance as yf
        prices = {}
        for label,sym in PRICE_TICKERS.items():
            try:
                h = yf.Ticker(sym).history(period="2d",interval="1d")
                if len(h)>=2:
                    price=float(h["Close"].iloc[-1]); prev=float(h["Close"].iloc[-2])
                    prices[label]={"price":price,"chg":(price-prev)/prev*100 if prev else None}
                elif len(h)==1:
                    prices[label]={"price":float(h["Close"].iloc[-1]),"chg":None}
            except: pass
        return prices
    except: return {}

# ══════════════════════════════════════════════════════════════════════
# HTML BUILDERS
# ══════════════════════════════════════════════════════════════════════
def _ticker_html(prices):
    ORDER=["S&P 500","NASDAQ","DOW","VIX","EUR/USD","GBP/USD","USD/JPY",
           "BTC/USD","ETH/USD","SOL/USD","GOLD","OIL WTI","10Y UST"]
    items=[]
    for lbl in ORDER:
        d=prices.get(lbl)
        if not d:
            items.append(f'<span class="nf-ticker-item">{lbl} <span style="color:#444">—</span></span>')
            continue
        p=d["price"]
        pf=(f"{p:,.0f}" if p>10000 else f"{p:.2f}" if p>100 else f"{p:.4f}" if p>1 else f"{p:.6f}")
        chg=d.get("chg")
        ch=""
        if chg is not None:
            cls="nf-t-up" if chg>=0 else "nf-t-down"
            arr="▲" if chg>=0 else "▼"
            ch=f' <span class="{cls}">{arr}{chg:+.2f}%</span>'
        items.append(f'<span class="nf-ticker-item">{lbl} <strong>{pf}</strong>{ch}</span>')
    doubled="".join(items)*2
    return (f'<div class="nf-ticker-wrap">'
            f'<div class="nf-ticker-label">◈ MARKET</div>'
            f'<div class="nf-ticker-track">{doubled}</div>'
            f'</div>')

def _status_html(nh,nm,nl,active,total):
    now=datetime.now().strftime("%H:%M")
    return (f'<div class="nf-status">'
            f'<span class="nf-stat-item"><span class="nf-stat-dot nf-s-red"></span>ALTO <span class="nf-stat-n">{nh}</span></span>'
            f'<span class="nf-stat-item"><span class="nf-stat-dot nf-s-amber"></span>MEDIO <span class="nf-stat-n">{nm}</span></span>'
            f'<span class="nf-stat-item"><span class="nf-stat-dot nf-s-green"></span>BAJO <span class="nf-stat-n">{nl}</span></span>'
            f'<span class="nf-stat-sep">·</span>'
            f'<span class="nf-stat-item"><span class="nf-stat-dot nf-s-blue"></span>'
            f'FUENTES ACTIVAS <span class="nf-stat-n">{active}/{len(SOURCES)}</span></span>'
            f'<span class="nf-stat-sep">·</span>'
            f'<span class="nf-stat-item">TOTAL <span class="nf-stat-n">{total}</span></span>'
            f'<span class="nf-stat-time">⏱ {now}</span>'
            f'</div>')

def _card_html(it):
    mins=it["minutes_ago"]
    tstr=f"{mins}" if mins<60 else f"{mins//60}h{mins%60:02d}"
    lbl="MIN AGO" if mins<60 else "AGO"
    dot_cls={"high":"nf-dot-high","med":"nf-dot-med","low":"nf-dot-low"}[it["impact"]]
    sent=it["sentiment"]["label"]
    sdot=""
    if sent=="bullish": sdot='<span class="nf-sent-dot nf-sent-bull"></span>'
    elif sent=="bearish": sdot='<span class="nf-sent-dot nf-sent-bear"></span>'
    tks="".join(f'<span class="nf-tk">{t}</span>' for t in it["tickers"])
    th=(f'<a href="{it["link"]}" target="_blank" rel="noopener">{it["title"]}</a>'
        if it["link"] else it["title"])
    return (f'<div class="nf-card {it["impact"]}">'
            f'<div class="nf-time-col"><div class="nf-mins">{tstr}</div>'
            f'<div class="nf-mins-lbl">{lbl}</div>'
            f'<div class="nf-impact-dot {dot_cls}"></div>'
            f'<div class="nf-score">{it["score"]}/10</div></div>'
            f'<div class="nf-body">'
            f'<div class="nf-nc-header">'
            f'<span class="nf-src-badge {it["src_css"]}">{it["src_label"]}</span>'
            f'<span class="nf-sector">{it["sector"]}</span>{sdot}</div>'
            f'<div class="nf-title">{th}</div>'
            f'<div class="nf-desc">{it["desc"][:180]}</div>'
            f'<div class="nf-keywords">{tks}</div></div></div>')

def _trump_panel_html(trump_items):
    if not trump_items:
        return (f'<div class="nf-trump-panel">'
                f'<div class="nf-trump-hdr">▲ TRUMP / TRUTH SOCIAL'
                f'<span class="nf-trump-hdr-dot" style="margin-left:auto"></span></div>'
                f'<div class="nf-trump-empty">◌ No posts disponibles</div>'
                f'</div>')
    posts=""
    for it in trump_items[:5]:
        mins=it["minutes_ago"]
        tstr=f"{mins}m ago" if mins<60 else f"{mins//60}h{mins%60:02d}m ago"
        text=(f'<a href="{it["link"]}" target="_blank" rel="noopener">{it["title"]}</a>'
              if it["link"] else it["title"])
        posts+=(f'<div class="nf-trump-post">'
                f'<div class="nf-trump-text">{text}</div>'
                f'<div class="nf-trump-time">{tstr} · Truth Social</div>'
                f'</div>')
    return (f'<div class="nf-trump-panel">'
            f'<div class="nf-trump-hdr">▲ TRUMP / TRUTH SOCIAL'
            f'<span class="nf-trump-hdr-dot" style="margin-left:auto"></span></div>'
            f'{posts}</div>')

def _impact_bars_html(nh,nm,nl):
    t=nh+nm+nl or 1
    pw=lambda n:int(n/t*100)
    return (f'<div class="nf-sbox"><div class="nf-sbox-hdr">◈ DISTRIBUCIÓN <span class="acc">IMPACTO</span></div>'
            f'<div class="nf-imp-bars">'
            f'<div class="nf-imp-row"><span class="nf-imp-lbl high">HIGH</span>'
            f'<div class="nf-imp-bw"><div class="nf-imp-b high" style="width:{pw(nh)}%"></div></div>'
            f'<span class="nf-imp-n">{nh}</span></div>'
            f'<div class="nf-imp-row"><span class="nf-imp-lbl med">MED</span>'
            f'<div class="nf-imp-bw"><div class="nf-imp-b med" style="width:{pw(nm)}%"></div></div>'
            f'<span class="nf-imp-n">{nm}</span></div>'
            f'<div class="nf-imp-row"><span class="nf-imp-lbl low">LOW</span>'
            f'<div class="nf-imp-bw"><div class="nf-imp-b low" style="width:{pw(nl)}%"></div></div>'
            f'<span class="nf-imp-n">{nl}</span></div>'
            f'</div></div>')

def _sentiment_html(items):
    recent=[it for it in items if it["minutes_ago"]<=60]
    bull=sum(1 for it in recent if it["sentiment"]["label"]=="bullish")
    bear=sum(1 for it in recent if it["sentiment"]["label"]=="bearish")
    total=bull+bear or 1
    net=(bull-bear)/total
    pct=int((net+1)/2*100)
    if net>0.25:   ls=f'<span style="color:#00e676">RISK-ON</span>'
    elif net<-0.25: ls=f'<span style="color:#ff1744">RISK-OFF</span>'
    else:           ls='<span style="color:#ffab00">MIXTO</span>'
    return (f'<div class="nf-sbox"><div class="nf-sbox-hdr">◈ SENTIMENT <span class="acc">1H</span></div>'
            f'<div class="nf-sent-wrap">'
            f'<div class="nf-sent-lbl"><span>BEARISH</span><span>BULLISH</span></div>'
            f'<div class="nf-sent-bar-wrap"><div class="nf-sent-needle" style="left:{pct}%"></div></div>'
            f'<div class="nf-sent-score">{ls} · {bull}↑ {bear}↓</div>'
            f'</div></div>')

def _timeline_html(items):
    buckets=[0]*24
    imp_cnt=[{"high":0,"med":0,"low":0} for _ in range(24)]
    for it in items:
        h=it["minutes_ago"]//60
        if 0<=h<24:
            idx=23-h; buckets[idx]+=1; imp_cnt[idx][it["impact"]]+=1
    mx=max(buckets) or 1
    bars=labels=""
    for i in range(24):
        cnt=buckets[i]; d=imp_cnt[i]
        dom=("high" if d["high"]>=d["med"] and d["high"]>=d["low"] else
             "med"  if d["med"]>=d["low"] else "low")
        cls=f"imp-{dom}" if cnt else ""
        ht=max(4,int(cnt/mx*46))
        lbl=f"-{23-i}h" if (23-i)%6==0 else ""
        bars+=f'<div class="nf-tl-bar {cls}" style="height:{ht}px" title="{cnt}"></div>'
        labels+=f'<div class="nf-tl-lbl">{lbl}</div>'
    return (f'<div class="nf-sbox"><div class="nf-sbox-hdr">◈ TIMELINE <span class="acc">24H</span></div>'
            f'<div class="nf-tl"><div class="nf-tl-bars">{bars}</div>'
            f'<div class="nf-tl-labels">{labels}</div></div></div>')

def _heatmap_html(items):
    counts={}
    for it in items: counts[it["sector"]]=counts.get(it["sector"],0)+1
    top=sorted(counts.items(),key=lambda x:-x[1])[:8]
    mx=top[0][1] if top else 1
    def heat(n):
        r=n/mx if mx else 0
        return "h5" if r>.8 else "h4" if r>.6 else "h3" if r>.4 else "h2" if r>.2 else "h1" if r>0 else "h0"
    cells="".join(f'<div class="nf-hm-cell {heat(cnt)}"><div class="nf-hm-name">{sec}</div>'
                  f'<div class="nf-hm-count">{cnt}</div>'
                  f'<div class="nf-hm-bar"><div class="nf-hm-fill" style="width:{int(cnt/mx*100)}%"></div></div></div>'
                  for sec,cnt in top)
    return (f'<div class="nf-sbox"><div class="nf-sbox-hdr">◈ HEATMAP <span class="acc">SECTORES</span></div>'
            f'<div class="nf-heatmap">{cells}</div></div>')

def _source_health_html(status):
    mc=max((s["count"] for s in status.values()),default=1) or 1
    rows=""
    for src in SOURCES:
        st_=status.get(src["id"],{"count":0,"ok":False})
        dot="nf-src-ok" if st_["ok"] else "nf-src-err"
        pct=int(st_["count"]/mc*100)
        rows+=(f'<div class="nf-src-row"><span class="nf-src-dot {dot}"></span>'
               f'<span class="nf-src-name">{src["label"]}</span>'
               f'<div class="nf-src-bw"><div class="nf-src-b" style="width:{pct}%"></div></div>'
               f'<span class="nf-src-count">{st_["count"]}</span></div>')
    return (f'<div class="nf-sbox"><div class="nf-sbox-hdr">◈ ESTADO <span class="acc">FUENTES</span></div>'
            f'<div class="nf-src-health">{rows}</div></div>')

def _keywords_html():
    h_kws=["fed","federal reserve","rate hike","rate cut","interest rate","basis points","bps",
           "recession","crash","collapse","default","bankrupt","bailout","systemic",
           "gdp miss","inflation surge","cpi","ppi","nonfarm","payrolls"]
    m_kws=["earnings","revenue","profit","loss","guidance","forecast","outlook",
           "upgrade","downgrade","analyst","target price","rating",
           "oil","crude","wti","brent","opec","energy","gold","silver"]
    l_kws=["product launch","new feature","partnership","collaboration","award",
           "recognition","appointment","ceo","executive","conference","summit",
           "meeting","speech","interview","research","report","study","survey","index","upgrade rating"]
    def pills(kws,cls):
        return "".join(f'<span class="nf-kw-pill {cls}">{k}</span>' for k in kws)
    return (f'<div class="nf-sbox"><div class="nf-sbox-hdr">◈ KEYWORDS <span class="acc">CLASIFICACIÓN</span></div>'
            f'<div class="nf-kw-legend">'
            f'<div class="nf-kw-section"><div class="nf-kw-title high">● ALTO IMPACTO</div>'
            f'<div class="nf-kw-list">{pills(h_kws,"high")}</div></div>'
            f'<div class="nf-kw-section"><div class="nf-kw-title med">● MEDIO IMPACTO</div>'
            f'<div class="nf-kw-list">{pills(m_kws,"med")}</div></div>'
            f'<div class="nf-kw-section"><div class="nf-kw-title low">● BAJO IMPACTO</div>'
            f'<div class="nf-kw-list">{pills(l_kws,"low")}</div></div>'
            f'</div></div>')

def _js_html(refresh_secs, new_high_cnt, alerts_on):
    beep=""
    if alerts_on and new_high_cnt>0:
        n=min(new_high_cnt,3)
        beep=f"""try{{for(var _i=0;_i<{n};_i++){{(function(d){{setTimeout(function(){{
var c=new(window.AudioContext||window.webkitAudioContext)();
var o=c.createOscillator();var g=c.createGain();
o.connect(g);g.connect(c.destination);o.frequency.value=880;o.type="sine";
g.gain.setValueAtTime(.4,c.currentTime);
g.gain.exponentialRampToValueAtTime(.001,c.currentTime+.25);
o.start(c.currentTime);o.stop(c.currentTime+.25);}},d*350);}})(_i);}}}}catch(e){{}}"""
    cd=f"""(function(){{var s={refresh_secs};function t(){{
var e=document.getElementById("nf-cd-secs");if(e)e.textContent=s+"s";
if(s<=0){{try{{window.parent.location.reload();}}catch(e){{window.location.reload();}}return;}}
s--;setTimeout(t,1000);}}t();}})();"""
    return f"<script>{beep}{cd}</script>"

# ══════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════
def render():
    _REFRESH_SECS = 120

    st.markdown(_CSS, unsafe_allow_html=True)

    # ── SESSION STATE ────────────────────────────────────────────
    if "nf_alerts_on"  not in st.session_state: st.session_state.nf_alerts_on  = False
    if "nf_seen_high"  not in st.session_state: st.session_state.nf_seen_high  = set()

    # ── HEADER ──────────────────────────────────────────────────
    hc1, hc2, hc3, hc4 = st.columns([5, 1, 1, 1])
    with hc1:
        st.markdown(
            "<div style='display:flex;align-items:flex-end;gap:14px;margin-bottom:6px'>"
            "  <div><div class='nf-logo'>RSU NEWS FEED</div>"
            "  <div class='nf-sub'>Financial Intelligence Feed</div></div>"
            "  <div class='nf-live-pill'><span class='nf-live-dot'></span>EN VIVO</div>"
            "</div>", unsafe_allow_html=True)
    with hc2:
        st.markdown("<br>", unsafe_allow_html=True)
        al_lbl = "🔔 ALERTAS ON" if st.session_state.nf_alerts_on else "🔕 ALERTAS"
        if st.button(al_lbl, use_container_width=True, key="nf_al_btn"):
            st.session_state.nf_alerts_on = not st.session_state.nf_alerts_on
            st.rerun()
    with hc3:
        st.markdown(
            "<br><div class='nf-countdown'>AUTO ⟳<br><span id='nf-cd-secs'>—</span></div>",
            unsafe_allow_html=True)
    with hc4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⟳ ACTUALIZAR", use_container_width=True, key="nf_ref_btn"):
            st.cache_data.clear()
            st.session_state.nf_seen_high = set()
            st.rerun()

    # ── TICKER ──────────────────────────────────────────────────
    prices = _load_prices()
    st.markdown(_ticker_html(prices), unsafe_allow_html=True)

    # ── LOAD DATA ───────────────────────────────────────────────
    with st.spinner("◌ Cargando feed..."):
        items, status = _load_news()
    active = sum(1 for s in status.values() if s["ok"])

    # ── SPLIT: trump vs main ─────────────────────────────────────
    trump_items = [it for it in items if it.get("special") == "trump"]
    main_items  = [it for it in items if it.get("special") != "trump"]

    # ── IMPACT / SENTIMENT / TIMELINE strip ─────────────────────
    nh_all = sum(1 for i in main_items if i["impact"]=="high")
    nm_all = sum(1 for i in main_items if i["impact"]=="med")
    nl_all = sum(1 for i in main_items if i["impact"]=="low")
    sc1, sc2, sc3 = st.columns(3)
    with sc1: st.markdown(_impact_bars_html(nh_all,nm_all,nl_all), unsafe_allow_html=True)
    with sc2: st.markdown(_sentiment_html(main_items), unsafe_allow_html=True)
    with sc3: st.markdown(_timeline_html(main_items), unsafe_allow_html=True)

    # ── FILTER ROW ──────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([3, 3, 3, 2])
    with fc1:
        fi1, fi2, fi3 = st.columns(3)
        with fi1: sh = st.checkbox("🔴 HIGH", value=True, key="nf_sh")
        with fi2: sm = st.checkbox("🟡 MED",  value=True, key="nf_sm")
        with fi3: sl = st.checkbox("🟢 LOW",  value=True, key="nf_sl")
    with fc2:
        src_opts = ["(todas)"] + [s["label"] for s in SOURCES if s.get("special") != "trump"]
        src_sel  = st.selectbox("src", src_opts, key="nf_src", label_visibility="collapsed")
    with fc3:
        search = st.text_input("search", placeholder="🔍 keyword...",
                               key="nf_search", label_visibility="collapsed")
    with fc4:
        tk_flt = st.text_input("ticker", placeholder="$ ej: NVDA",
                               key="nf_ticker", label_visibility="collapsed").upper().strip()

    # ── APPLY FILTERS ───────────────────────────────────────────
    impact_sel = []
    if sh: impact_sel.append("high")
    if sm: impact_sel.append("med")
    if sl: impact_sel.append("low")
    if not impact_sel: impact_sel = ["high","med","low"]

    filtered = [it for it in main_items if it["impact"] in impact_sel]
    if src_sel != "(todas)":
        filtered = [it for it in filtered if it["src_label"] == src_sel]
    if search:
        q = search.lower()
        filtered = [it for it in filtered if q in (it["title"]+it["desc"]).lower()]
    if tk_flt:
        filtered = [it for it in filtered if tk_flt in it["tickers"]]

    nh = sum(1 for i in filtered if i["impact"]=="high")
    nm = sum(1 for i in filtered if i["impact"]=="med")
    nl = sum(1 for i in filtered if i["impact"]=="low")

    # ── SOUND ALERT DETECTION ────────────────────────────────────
    high_hashes = {hash(it["title"][:60]) for it in filtered if it["impact"]=="high"}
    new_high    = len(high_hashes - st.session_state.nf_seen_high)
    st.session_state.nf_seen_high = high_hashes

    # ── STATUS STRIP ────────────────────────────────────────────
    st.markdown(_status_html(nh,nm,nl,active,len(filtered)), unsafe_allow_html=True)

    # ── TWO-COLUMN LAYOUT ───────────────────────────────────────
    col_feed, col_panel = st.columns([7, 3])

    # ── RIGHT PANEL ─────────────────────────────────────────────
    with col_panel:
        # Trump at top
        st.markdown(_trump_panel_html(trump_items), unsafe_allow_html=True)

        # Collapsible sections
        with st.expander("◈ FUENTES & FILTROS", expanded=False):
            st.markdown(_source_health_html(status), unsafe_allow_html=True)

        with st.expander("◈ HEATMAP SECTORES", expanded=False):
            st.markdown(_heatmap_html(filtered), unsafe_allow_html=True)

        with st.expander("◈ ALERTAS SONORAS", expanded=False):
            al_status = "ON — Alertas activas para noticias HIGH" if st.session_state.nf_alerts_on else "OFF — Pulsa el botón del header para activar"
            al_cls    = "nf-alert-on" if st.session_state.nf_alerts_on else "nf-alert-off"
            st.markdown(
                f'<div class="nf-alert-wrap">'
                f'  <div class="nf-alert-status {al_cls}">{al_status}</div>'
                f'  <div class="nf-alert-row"><label>Sonido al detectar noticias de ALTO impacto nuevas. '
                f'Usa el botón ALERTAS en el header para activar/desactivar.</label></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with st.expander("◈ KEYWORDS CLASIFICACIÓN", expanded=False):
            st.markdown(_keywords_html(), unsafe_allow_html=True)

    # ── FEED ────────────────────────────────────────────────────
    with col_feed:
        if not filtered:
            st.markdown("<div class='nf-empty'>◌ SIN NOTICIAS EN ESTE FILTRO</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown("".join(_card_html(it) for it in filtered[:120]),
                        unsafe_allow_html=True)

    # ── JS ───────────────────────────────────────────────────────
    st.markdown(_js_html(_REFRESH_SECS, new_high, st.session_state.nf_alerts_on),
                unsafe_allow_html=True)

    st.caption(
        f"↺ {datetime.now().strftime('%H:%M:%S')} · "
        f"auto-refresh {_REFRESH_SECS}s · "
        f"{len(filtered)} noticias · {active}/{len(SOURCES)} fuentes"
    )
