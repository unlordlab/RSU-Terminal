#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nightly_scan.py — Job nocturno CAN SLIM Scanner Pro v4.0.1
FIXES:
  1. _to_float() — corrige "The truth value of a Series is ambiguous"
  2. get_spy() — normaliza MultiIndex de yf.download
  3. SP500_TICKERS — eliminados 11 tickers delistados
"""

import argparse, json, logging, os, random, re, sys, time
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf

os.makedirs("data", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/nightly_scan.log", mode="a", encoding="utf-8"),
    ],
)
log = logging.getLogger("nightly_scan")

OUTPUT_PATH    = os.path.join("data", "scan_cache.json")
BATCH_SIZE     = 50
MIN_PRICE      = 10.0
MIN_AVG_VOLUME = 500_000
MIN_MARKET_CAP = 0.5e9

SP500_TICKERS = [
    "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","ABNB",
    "AKAM","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL","GOOG","MO","AMZN",
    "AMCR","AEE","AAL","AEP","AXP","AIG","AMT","AWK","AMP","AME","AMGN",
    "APH","ADI","AON","APA","AAPL","AMAT","APTV","ACGL","ADM","ANET",
    "AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON","BKR","BALL",
    "BAC","BK","BBWI","BAX","BDX","BRK-B","BBY","TECH","BIIB","BLK","BX",
    "BA","BKNG","BWA","BSX","BMY","AVGO","BR","BRO","BF-B","BLDR","BG","CDNS",
    "CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR","CAT","CBOE","CBRE",
    "CDW","CE","COR","CNC","CF","CRL","SCHW","CHTR","CVX","CMG",
    "CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO",
    "CTSH","CL","CMCSA","CAG","COP","ED","STZ","CEG","COO","CPRT","GLW","CPAY",
    "CTVA","CSGP","COST","CTRA","CRWD","CCI","CSX","CMI","CVS","DHR","DRI",
    "DVA","DAY","DE","DAL","XRAY","DVN","DXCM","FANG","DLR","DG","DLTR",
    "D","DPZ","DOV","DOW","DHI","DTE","DUK","DD","EMN","ETN","EBAY","ECL",
    "EIX","EW","EA","ELV","LLY","EMR","ENPH","ETR","EOG","EPAM","EQT","EFX",
    "EQIX","EQR","ESS","EL","ETSY","EG","EXAS","EXPD","EXPE","EXR",
    "XOM","FFIV","FDS","FICO","FAST","FRT","FDX","FIS","FITB","FSLR","FE",
    "FMC","F","FOXA","FOX","BEN","FCX","GRMN","IT","GE","GEHC",
    "GEV","GEN","GNRC","GD","GIS","GM","GPC","GILD","GS","HAL","HIG","HAS",
    "HCA","DOC","HSIC","HSY","HPE","HLT","HOLX","HD","HON","HRL","HST",
    "HWM","HPQ","HUBB","HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY",
    "IR","PODD","INTC","ICE","IFF","IP","INTU","ISRG","IVZ","INVH",
    "IQV","IRM","JBHT","JBL","JKHY","J","JNJ","JCI","JPM","KVUE",
    "KDP","KEY","KEYS","KMB","KIM","KMI","KLAC","KHC","KR","LHX","LH","LRCX",
    "LW","LVS","LDOS","LEN","LIN","LYV","LKQ","LMT","L","LOW","LULU","LYB",
    "MTB","MPC","MKTX","MAR","MMC","MLM","MAS","MA","MTCH","MKC","MCD",
    "MCK","MDT","MRK","META","MET","MTD","MGM","MCHP","MU","MSFT","MAA","MRNA",
    "MHK","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS","MSI","MSCI",
    "NDAQ","NTAP","NFLX","NEM","NWSA","NWS","NEE","NKE","NI","NDSN","NSC",
    "NTRS","NOC","NCLH","NRG","NUE","NVDA","NVR","NXPI","ORLY","OXY","ODFL",
    "OMC","ON","OKE","ORCL","OTIS","PCAR","PKG","PANW","PH","PAYX","PAYC",
    "PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNW","PNC","POOL","PPG","PPL",
    "PFG","PG","PGR","PLD","PRU","PEG","PTC","PSA","PHM","QRVO","PWR","QCOM",
    "DGX","RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY","ROK",
    "ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB","STX","SRE","NOW",
    "SHW","SPG","SWKS","SJM","SNA","SOLV","SO","LUV","SWK","SBUX","STT","STLD",
    "STE","SYK","SMCI","SYF","SNPS","SYY","TMUS","TROW","TTWO","TPR","TRGP",
    "TGT","TEL","TDY","TFX","TER","TSLA","TXN","TXT","TMO","TJX","TSCO","TT",
    "TDG","TRV","TRMB","TFC","TYL","TSN","USB","UBER","UDR","ULTA","UNP","UAL",
    "UPS","URI","UNH","UHS","VLO","VTR","VLTO","VRSN","VRSK","VZ","VRTX","VTRS",
    "VICI","V","VST","VMC","WRB","GWW","WAB","WMT","DIS","WBD","WM",
    "WAT","WEC","WFC","WELL","WST","WDC","WY","WHR","WMB","WTW","WYNN","XEL",
    "XYL","YUM","ZBRA","ZBH","ZTS",
]


def _to_float(val) -> float:
    """FIX PRINCIPAL: extrae float escalar de cualquier tipo pandas/numpy."""
    if hasattr(val, 'item'):
        return float(val.item())
    if hasattr(val, 'iloc'):
        return float(val.iloc[0])
    return float(val)


def get_sp500() -> list:
    base = list(dict.fromkeys(SP500_TICKERS))
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", header=0)
        col = "Symbol" if "Symbol" in tables[0].columns else tables[0].columns[0]
        for t in tables[0][col].str.replace(".", "-", regex=False):
            t = str(t).strip().upper()
            if t and t not in base and re.match(r'^[A-Z][A-Z0-9\-]{0,5}$', t):
                base.append(t)
        log.info(f"SP500: {len(base)} tickers")
    except Exception as e:
        log.warning(f"Wikipedia no disponible: {e}")
    return base


def download_hist_batch(tickers: list, period: str = "1y") -> dict:
    if not tickers: return {}
    try:
        raw = yf.download(tickers, period=period, auto_adjust=True,
                          progress=False, group_by="ticker", threads=True)
        result = {}
        if len(tickers) == 1:
            if not raw.empty: result[tickers[0]] = raw.copy()
        else:
            for t in tickers:
                try:
                    df = raw[t].dropna(how="all")
                    if len(df) > 30: result[t] = df
                except Exception: pass
        return result
    except Exception as e:
        log.error(f"Error batch: {e}"); return {}


def download_info(tickers: list) -> dict:
    result = {}
    for i, t in enumerate(tickers):
        try:
            info = yf.Ticker(t).info
            if info and len(info) > 5: result[t] = info
            time.sleep(0.3 + random.uniform(0.05, 0.2))
        except Exception as e:
            log.debug(f"Info {t}: {e}"); time.sleep(0.5)
        if (i + 1) % 50 == 0:
            log.info(f"  Info: {i+1}/{len(tickers)}"); time.sleep(2)
    return result


def get_spy() -> pd.DataFrame:
    """FIX: normaliza MultiIndex de yf.download para SPY."""
    try:
        raw = yf.download("SPY", period="2y", auto_adjust=True, progress=False)
        if raw.empty: return pd.DataFrame()
        if isinstance(raw.columns, pd.MultiIndex):
            if "SPY" in raw.columns.get_level_values(1):
                raw = raw.xs("SPY", axis=1, level=1)
            else:
                raw = raw.droplevel(1, axis=1)
        return raw
    except Exception as e:
        log.error(f"SPY error: {e}"); return pd.DataFrame()


def get_market_score(spy_df: pd.DataFrame) -> dict:
    """FIX: usa _to_float() en todos los valores antes de comparar."""
    empty = {"score": 50, "phase": "UNKNOWN", "color": "#888888", "signals": []}
    if spy_df is None or spy_df.empty or len(spy_df) < 50: return empty
    try:
        close  = spy_df["Close"]
        price  = _to_float(close.iloc[-1])
        sma50  = _to_float(close.rolling(50).mean().iloc[-1])
        sma200 = _to_float(close.rolling(200).mean().iloc[-1]) if len(spy_df) >= 200 else sma50
        tr20d  = (_to_float(close.iloc[-1]) / _to_float(close.iloc[-20]) - 1) * 100 if len(spy_df) >= 20 else 0.0

        score, signals = 50, []
        if price > sma50 > sma200:
            score += 20; signals.append("SPY: Golden Cross (Alcista)")
        elif price > sma50:
            score += 10; signals.append("SPY: Sobre SMA50")
        elif price < sma50 < sma200:
            score -= 20; signals.append("SPY: Death Cross (Bajista)")
        else:
            score -= 10
        if tr20d > 5:  score += 10
        elif tr20d < -5: score -= 10
        score = max(0, min(100, score))

        if   score >= 80: phase, color = "CONFIRMED UPTREND",        "#00ffad"
        elif score >= 60: phase, color = "UPTREND UNDER PRESSURE",   "#ff9800"
        elif score >= 40: phase, color = "MARKET IN TRANSITION",     "#888888"
        elif score >= 20: phase, color = "DOWNTREND UNDER PRESSURE", "#ff9800"
        else:             phase, color = "CONFIRMED DOWNTREND",      "#f23645"
        return {"score": score, "phase": phase, "color": color, "signals": signals}
    except Exception as e:
        log.error(f"market_score error: {e}", exc_info=True); return empty


def pre_filter(tickers, hist_data, info_data):
    ok = []
    for t in tickers:
        h = hist_data.get(t)
        if h is None or h.empty or len(h) < 50: continue
        try:
            if _to_float(h["Close"].iloc[-1]) < MIN_PRICE: continue
            if _to_float(h["Volume"].rolling(20).mean().iloc[-1]) < MIN_AVG_VOLUME: continue
            mkt = info_data.get(t, {}).get("marketCap")
            if mkt is not None and float(mkt) < MIN_MARKET_CAP: continue
            ok.append(t)
        except Exception: pass
    return ok


def compute_rs_universe(tickers, hist_data, spy_df):
    if spy_df is None or spy_df.empty: return {t: 50 for t in tickers}
    spy_c = spy_df["Close"].copy()
    if hasattr(spy_c.index, "tz") and spy_c.index.tz:
        spy_c.index = spy_c.index.tz_localize(None)
    raw_scores, days = {}, 63
    for t in tickers:
        h = hist_data.get(t)
        if h is None or len(h) < 130: continue
        try:
            sc = h["Close"].copy()
            if hasattr(sc.index, "tz") and sc.index.tz:
                sc.index = sc.index.tz_localize(None)
            merged = pd.merge(sc.rename("s"), spy_c.rename("m"), left_index=True, right_index=True, how="inner")
            if len(merged) < 100: continue
            ws, scores = [.40,.20,.20,.20], []
            for i in range(4):
                e = len(merged)-1-(0 if i==0 else i*days); s = e-days
                if s < 0: scores.append(0.0); continue
                sr = _to_float(merged["s"].iloc[e])/_to_float(merged["s"].iloc[s])-1
                mr = _to_float(merged["m"].iloc[e])/_to_float(merged["m"].iloc[s])-1
                scores.append((1+sr)/(1+mr)-1 if abs(mr)>.001 else sr)
            raw_scores[t] = sum(w*v for w,v in zip(ws,scores))
        except Exception as e: log.debug(f"RS {t}: {e}")
    if not raw_scores: return {t: 50 for t in tickers}
    sv = sorted(raw_scores.values()); n = len(sv)
    result = {t: min(99,max(1,round(1+(sv.index(v)/max(n-1,1))*98))) for t,v in raw_scores.items()}
    for t in tickers:
        if t not in result: result[t] = 50
    return result


def ibd_eps_rating(g):
    if g is None: return 50
    if g>=100: return 99
    if g>=50:  return 90+min(9,int((g-50)/5))
    if g>=25:  return 80+min(9,int((g-25)/2.5))
    if g>=15:  return 60+min(19,int(g-15))
    if g>0:    return 40+min(19,int(g*2))
    return max(1,40+int(g))

def ibd_composite(rs,eps,sg,roe,p12):
    return min(99,max(1,round(eps*.30+rs*.30+min(99,max(1,50+(sg or 0)))*.15+min(99,max(1,(roe or 0)*2))*.15+min(99,max(1,50+(p12 or 0)))*.10)))

def ibd_smr(sg,roe,mg):
    sc=0
    if sg>=25:sc+=40
    elif sg>=15:sc+=30
    elif sg>=10:sc+=20
    elif sg>0:sc+=10
    if roe>=25:sc+=40
    elif roe>=17:sc+=30
    elif roe>=10:sc+=20
    elif roe>0:sc+=10
    if mg and mg>.20:sc+=20
    elif mg and mg>.10:sc+=15
    elif mg and mg>0:sc+=10
    return "A" if sc>=80 else "B" if sc>=60 else "C" if sc>=40 else "D"

def ibd_acc_dis(h,period=50):
    if h is None or len(h)<period: return "C"
    try:
        r=h.tail(period).copy(); r["chg"]=r["Close"].pct_change()
        vu=r[r["chg"]>0]["Volume"].sum(); vt=r["Volume"].sum()
        if vt==0: return "C"
        ar=_to_float(vu/vt)*100; pf=(_to_float(r["Close"].iloc[-1])/_to_float(r["Close"].iloc[0])-1)*100
        if ar>=65 and pf>5: return "A"
        if ar>=58: return "B"
        if ar>=42: return "C"
        if ar>=35: return "D"
        return "E"
    except: return "C"

def ibd_atr(h,period=14):
    if h is None or len(h)<period: return 0.0
    try:
        hi,lo,cl=h["High"],h["Low"],h["Close"]
        tr=pd.concat([hi-lo,(hi-cl.shift()).abs(),(lo-cl.shift()).abs()],axis=1).max(axis=1)
        return round(_to_float(tr.rolling(period).mean().iloc[-1])/_to_float(cl.iloc[-1])*100,2)
    except: return 0.0

def trend_template(h,price):
    empty={"all_pass":False,"score":0,"criteria":{},"stage":"Insufficient Data","values":{}}
    if h is None or len(h)<200: return empty
    try:
        c=h["Close"]
        s50=_to_float(c.rolling(50).mean().iloc[-1]); s150=_to_float(c.rolling(150).mean().iloc[-1])
        s200=_to_float(c.rolling(200).mean().iloc[-1]); s200_20=_to_float(c.rolling(200).mean().iloc[-20])
        h52=_to_float(h["High"].tail(252).max()); l52=_to_float(h["Low"].tail(252).min())
        crit={
            "Precio > SMA 50":price>s50,"Precio > SMA 150":price>s150,"Precio > SMA 200":price>s200,
            "SMA 50 > SMA 150":s50>s150,"SMA 150 > SMA 200":s150>s200,
            "SMA 200 Tendencia Alcista":s200>s200_20,
            "Precio > 30% del minimo 52s":price>=l52*1.30,
            "Precio dentro 25% del maximo 52s":price>=h52*.75,
        }
        sc=sum(crit.values())
        if sc==8: stage="Stage 2 (Advancing)"
        elif price>s200 and s200>s200_20: stage="Stage 1/2 Transition"
        elif price<s200 and s200<=s200_20: stage="Stage 4 (Declining)"
        else: stage="Stage 3 (Distribution)"
        return {"all_pass":sc==8,"score":sc,"criteria":crit,"stage":stage,
                "values":{"sma_50":s50,"sma_150":s150,"sma_200":s200,"high_52w":h52,"low_52w":l52,
                           "distance_from_high":round((price/h52-1)*100,2),"distance_from_low":round((price/l52-1)*100,2)}}
    except Exception as e: return {**empty,"stage":f"Error: {e}"}


def analyze_ticker(t,h,info,rs_universe,mkt_score):
    try:
        if h is None or h.empty or len(h)<50: return None
        price=_to_float(h["Close"].iloc[-1]); mc=float((info.get("marketCap",0) or 0))/1e9
        eg=float((info.get("earningsGrowth",0) or 0))*100; rg=float((info.get("revenueGrowth",0) or 0))*100
        epsg=float((info.get("earningsQuarterlyGrowth",0) or 0))*100; roe=float((info.get("returnOnEquity",0) or 0))*100
        mg=float(info.get("profitMargins",0) or 0); inst=float((info.get("heldPercentInstitutions",0) or 0))*100
        hi52=_to_float(h["High"].max()); pfh=(price-hi52)/hi52*100
        avgv=_to_float(h["Volume"].rolling(20).mean().iloc[-1]); vr=_to_float(h["Volume"].iloc[-1])/avgv if avgv>0 else 1.0
        rs=int(rs_universe.get(t,50)); eps_r=ibd_eps_rating(epsg)
        p12=(_to_float(h["Close"].iloc[-1])/_to_float(h["Close"].iloc[-252])-1)*100 if len(h)>=252 else (_to_float(h["Close"].iloc[-1])/_to_float(h["Close"].iloc[0])-1)*100
        comp=ibd_composite(rs,eps_r,rg,roe,p12); smr=ibd_smr(rg,roe,mg)
        ad=ibd_acc_dis(h); atr=ibd_atr(h); tt=trend_template(h,price)
        vol=float(h["Close"].pct_change().std()*np.sqrt(252)*100)
        mom20=(_to_float(h["Close"].iloc[-1])/_to_float(h["Close"].iloc[-20])-1)*100 if len(h)>=20 else 0.0
        ms=int(mkt_score.get("score",50))

        score=0
        cg,cs=("A",20) if eg>50 else ("A",15) if eg>25 else ("B",10) if eg>15 else ("C",5) if eg>0 else ("D",0); score+=cs
        ag,as_=("A",15) if epsg>50 else ("A",12) if epsg>25 else ("B",8) if epsg>15 else ("C",4) if epsg>0 else ("D",0); score+=as_
        ng,ns=("A",15) if pfh>-3 else ("A",12) if pfh>-10 else ("B",8) if pfh>-20 else ("C",4) if pfh>-30 else ("D",0); score+=ns
        sg2,ss=("A",10) if vr>2.0 else ("A",8) if vr>1.5 else ("B",5) if vr>1.0 else ("C",2); score+=ss
        lg,ls=("A",15) if rs>90 else ("A",12) if rs>80 else ("B",8) if rs>70 else ("C",4) if rs>60 else ("D",0); score+=ls
        ig,is_=("A",10) if inst>80 else ("A",8) if inst>60 else ("B",5) if inst>40 else ("C",3) if inst>20 else ("D",0); score+=is_
        mg2,ms2=("A",15) if ms>=80 else ("B",10) if ms>=60 else ("C",5) if ms>=40 else ("D",0); score+=ms2

        return {
            "ticker":t,"name":info.get("shortName",t),"sector":info.get("sector","N/A"),"industry":info.get("industry","N/A"),
            "market_cap":round(mc,2),"price":round(price,2),"score":score,"ml_probability":0.5,
            "grades":{"C":cg,"A":ag,"N":ng,"S":sg2,"L":lg,"I":ig,"M":mg2},
            "scores":{"C":cs,"A":as_,"N":ns,"S":ss,"L":ls,"I":is_,"M":ms2},
            "metrics":{"earnings_growth":round(eg,2),"revenue_growth":round(rg,2),"eps_growth":round(epsg,2),
                        "pct_from_high":round(pfh,2),"volume_ratio":round(vr,2),"rs_rating":rs,
                        "inst_ownership":round(inst,2),"market_score":ms,"market_phase":mkt_score.get("phase","N/A"),
                        "volatility":round(vol,2),"price_momentum":round(mom20,2)},
            "ibd_ratings":{"composite":comp,"rs":rs,"eps":eps_r,"smr":smr,"acc_dis":ad,"atr_percent":atr,
                            "pe_ratio":float(info.get("trailingPE",0) or 0),"roe":round(roe,2),"sales_growth":round(rg,2)},
            "trend_template":tt,
            "week_52_range":{"high":round(hi52,2),"low":round(_to_float(h["Low"].min()),2),
                              "current_position":round(price/hi52*100,1) if hi52 else 0},
        }
    except Exception as e:
        log.debug(f"Error {t}: {e}"); return None


def run_scan(min_score=55, min_composite=65, max_results=100):
    sp500=get_sp500(); log.info(f"Universo: {len(sp500)} tickers")
    log.info("PASO 1/4 — Historico batch...")
    hist_data={}
    for idx,batch in enumerate([sp500[i:i+BATCH_SIZE] for i in range(0,len(sp500),BATCH_SIZE)]):
        hist_data.update(download_hist_batch(batch))
        log.info(f"  Batch {idx+1} — {len(hist_data)} descargados")
    log.info("PASO 2/4 — Info fundamental...")
    info_data=download_info(sp500); log.info(f"  {len(info_data)} tickers")
    log.info("PASO 3/4 — Pre-filtro...")
    filtered=pre_filter(sp500,hist_data,info_data); log.info(f"  {len(filtered)} tickers")
    log.info("PASO 3b — SPY + RS + Market Score...")
    spy_df=get_spy(); rs_univ=compute_rs_universe(filtered,hist_data,spy_df)
    mkt_score=get_market_score(spy_df); log.info(f"  Market: {mkt_score['score']}/100 {mkt_score['phase']}")
    log.info("PASO 4/4 — Scores CAN SLIM...")
    candidates=[]
    for i,t in enumerate(filtered):
        r=analyze_ticker(t,hist_data.get(t),info_data.get(t,{}),rs_univ,mkt_score)
        if r and r["score"]>=min_score and r["ibd_ratings"]["composite"]>=min_composite:
            candidates.append(r)
        if (i+1)%50==0: log.info(f"  {i+1}/{len(filtered)} — candidatos: {len(candidates)}")
    candidates.sort(key=lambda x:x["score"],reverse=True)
    log.info(f"Completo: {len(candidates)} candidatos")
    return candidates[:max_results],mkt_score,len(sp500)


def save_results(candidates,mkt,sp500_count):
    os.makedirs("data",exist_ok=True)
    with open(OUTPUT_PATH,"w",encoding="utf-8") as f:
        json.dump({"generated_at":datetime.utcnow().isoformat(),"sp500_count":sp500_count,
                   "total_candidates":len(candidates),"market_status":mkt,"candidates":candidates},
                  f,ensure_ascii=False,indent=2,default=str)
    log.info(f"Guardado: {OUTPUT_PATH}")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--min-score",type=int,default=55)
    parser.add_argument("--min-composite",type=int,default=65)
    parser.add_argument("--max-results",type=int,default=100)
    args=parser.parse_args()
    log.info("="*60)
    log.info(f"CAN SLIM Nightly Scan v4.0.1 — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    t0=time.time()
    try:
        candidates,mkt,sp500_count=run_scan(args.min_score,args.min_composite,args.max_results)
        save_results(candidates,mkt,sp500_count)
        log.info(f"Tiempo: {(time.time()-t0)/60:.1f} min — OK")
        sys.exit(0)
    except Exception as e:
        log.error(f"Error fatal: {e}",exc_info=True); sys.exit(1)
