"""
compute_rsrw.py — GitHub Actions Worker v4.0
=============================================
Cambios vs v3.x:
- Períodos ampliados: 21d, 63d, 126d (en lugar de 5d, 20d, 60d)
- RS convertido a PERCENTIL dentro del universo (0–99), como IBD
- Score EMA-suavizado: media exponencial de los últimos 10 días de RS para
  eliminar spikes de earnings/noticias
- Filtro de tendencia: RS_trend = pendiente de la recta de regresión del RS
  sobre los últimos 21 días (>0 = RS acelerándose, <0 = deteriorándose)
- RS_Momentum: RS_21d − RS_63d (¿está ganando o perdiendo fuerza relativa?)
- Period de descarga ampliado a 160d para cubrir los 126d + suavizado

Secrets necesarios:
  GH_GIST_TOKEN, RSRW_GIST_ID
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json, requests, os, time
from datetime import datetime, timezone
from scipy import stats as scipy_stats

BENCHMARK    = "SPY"
# Períodos en días de trading — equivalen a ~1m, ~3m, ~6m
PERIODS      = [21, 63, 126]
# Pesos: el período más largo domina — captura liderazgo sostenido, no spikes
WEIGHTS      = {21: 0.20, 63: 0.35, 126: 0.45}
EMA_SMOOTH   = 10      # días para suavizar el RS diario antes de calcular el score
TREND_WIN    = 21      # días para calcular la pendiente de tendencia RS
LOOKBACK     = "200d"  # suficiente para 126d + suavizado + trend
BATCH_SIZE   = 80
GIST_FILE    = "rsrw_scan.json"

SECTOR_ETFS = {
    "Tecnología":"XLK","Salud":"XLV","Financieros":"XLF",
    "Consumo Discrecional":"XLY","Consumo Básico":"XLP","Industriales":"XLI",
    "Energía":"XLE","Materiales":"XLB","Servicios Públicos":"XLU",
    "Bienes Raíces":"XLRE","Comunicaciones":"XLC",
}
GICS_MAP = {
    "Information Technology":"Tecnología","Health Care":"Salud",
    "Financials":"Financieros","Consumer Discretionary":"Consumo Discrecional",
    "Consumer Staples":"Consumo Básico","Industrials":"Industriales",
    "Energy":"Energía","Materials":"Materiales","Utilities":"Servicios Públicos",
    "Real Estate":"Bienes Raíces","Communication Services":"Comunicaciones",
}

# ─────────────────────────────────────────────────────────────
def get_sp500_tickers():
    print("[1/5] Obteniendo universo S&P 500...")
    try:
        df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", match="Symbol")[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        smap = dict(zip(df["Symbol"].str.replace(".", "-", regex=False), df["GICS Sector"]))
        if len(tickers) >= 490:
            print(f"  ✓ {len(tickers)} tickers de Wikipedia")
            return tickers, smap
    except Exception as e:
        print(f"  ✗ Wikipedia falló: {e}")
    fallback = [
        "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","AVGO","JPM",
        "LLY","V","UNH","XOM","MA","JNJ","PG","HD","MRK","COST","ABBV","CVX",
        "BAC","KO","CRM","PEP","TMO","WFC","NFLX","ORCL","AMD","ACN","ADBE","LIN",
        "MCD","PM","WMT","CSCO","IBM","GS","GE","HON","DIS","CAT","RTX","AMGN",
        "VZ","T","CMCSA","PFE","ABT","TXN","MS","NEE","BMY","SPGI","DHR","UNP",
        "LOW","BLK","ISRG","GILD","SYK","CI","BSX","ELV","ITW","DE","NOC","LMT",
        "EMR","ETN","PH","GD","USB","TFC","SCHW","COF","MCO","ICE","CME","PGR",
        "COP","EOG","SLB","OXY","PSX","MPC","VLO","WMB","FCX","NEM","DOW","ECL",
        "PLD","AMT","CCI","EQIX","PSA","O","DLR","SPG","VICI","CRWD","PANW",
        "SNOW","PLTR","NET","UBER","ABNB","DXCM","ZTS","IQV","EW","IDXX","BIIB",
        "MRNA","HUM","YUM","SBUX","BKNG","MAR","TTWO","EA","NKE","LULU",
        "TGT","DG","DLTR","TJX","UPS","FDX","NSC","CSX","DAL","UAL","LUV",
        "INTC","QCOM","MU","KLAC","LRCX","AMAT","SNPS","CDNS","ADI","MCHP",
        "K","HSY","GIS","MDLZ","KHC","TSN","BG","NUE","VMC","PPG","ALB",
        "SO","DUK","AEP","SRE","EXC","XEL","ED","WEC","AWK",
    ]
    print(f"  ✓ Fallback: {len(fallback)} tickers")
    return list(dict.fromkeys(fallback)), {}

# ─────────────────────────────────────────────────────────────
def download_all(symbols):
    all_syms = list(dict.fromkeys([BENCHMARK] + list(SECTOR_ETFS.values()) + symbols))
    batches  = [all_syms[i:i+BATCH_SIZE] for i in range(0, len(all_syms), BATCH_SIZE)]
    close_d, vol_d = {}, {}

    print(f"[2/5] Descargando {len(all_syms)} símbolos en {len(batches)} lotes...")
    for idx, batch in enumerate(batches):
        print(f"  Lote {idx+1}/{len(batches)}...")
        for attempt in range(3):
            try:
                if idx > 0: time.sleep(0.8)
                raw = yf.download(batch, period=LOOKBACK, interval="1d",
                    progress=False, threads=True, timeout=30, auto_adjust=True)
                if raw.empty: raise ValueError("Empty")
                if isinstance(raw.columns, pd.MultiIndex):
                    for t in raw.get("Close", pd.DataFrame()).columns:
                        s = raw["Close"][t].dropna()
                        if len(s) > 10: close_d[t] = s
                    for t in raw.get("Volume", pd.DataFrame()).columns:
                        s = raw["Volume"][t].dropna()
                        if len(s) > 10: vol_d[t] = s
                else:
                    if "Close" in raw.columns:
                        close_d[batch[0]] = raw["Close"].dropna()
                        vol_d[batch[0]]   = raw.get("Volume", pd.Series()).dropna()
                break
            except Exception as e:
                if attempt == 2: print(f"    ✗ Lote {idx+1} falló: {e}")
                time.sleep(2)

    if not close_d:
        return None, None
    close  = pd.DataFrame(close_d).sort_index().dropna(how="all")
    volume = pd.DataFrame(vol_d).reindex(close.index).fillna(0)
    print(f"  ✓ {len(close.columns)} tickers · {len(close)} días")
    return close, volume

# ─────────────────────────────────────────────────────────────
def _rs_series_smoothed(prices: pd.Series, spy: pd.Series, period: int) -> pd.Series:
    """
    Calcula la serie diaria de RS (retorno relativo al SPY) para un período dado
    y aplica suavizado EMA para eliminar spikes de eventos puntuales.
    """
    # RS diario rolling: retorno período-días del stock vs SPY
    stock_ret = prices.pct_change(period)
    spy_ret   = spy.pct_change(period)
    rs_raw    = stock_ret - spy_ret
    # Suavizar con EMA — elimina el impacto de un día de earnings en el score
    rs_smooth = rs_raw.ewm(span=EMA_SMOOTH, min_periods=3).mean()
    return rs_smooth

def _rs_trend(rs_series: pd.Series, window: int = TREND_WIN) -> float:
    """
    Pendiente normalizada de la regresión lineal del RS suavizado en los últimos
    `window` días. Positiva = RS acelerándose, negativa = deteriorándose.
    """
    recent = rs_series.dropna().iloc[-window:]
    if len(recent) < 5:
        return 0.0
    x = np.arange(len(recent))
    slope, _, _, _, _ = scipy_stats.linregress(x, recent.values)
    # Normalizar por la desviación estándar para comparar entre tickers
    std = recent.std()
    return round(float(slope / std) if std > 0 else 0.0, 4)

# ─────────────────────────────────────────────────────────────
def compute_metrics(close, volume, smap):
    print("[3/5] Calculando métricas RS v4.0...")

    if BENCHMARK not in close.columns:
        print("✗ SPY no encontrado.")
        return {}, {}, 0.0

    spy = close[BENCHMARK].dropna()
    spy_perf = float((spy.iloc[-1]/spy.iloc[-20])-1) if len(spy) >= 20 else 0.0

    # Sector RS (63d — equivale a ~3 meses, más estable que 20d)
    sector_rs = {}
    for sname, etf in SECTOR_ETFS.items():
        if etf not in close.columns: continue
        s = close[etf].dropna()
        if len(s) < 63: continue
        rs_s = _rs_series_smoothed(s, spy.reindex(s.index).ffill(), 63)
        sector_rs[sname] = {
            "RS":          round(float(rs_s.iloc[-1]), 6),
            "RS_trend":    _rs_trend(rs_s),
            "Return_63d":  round(float((s.iloc[-1]/s.iloc[-63])-1), 6),
            "ETF":         etf,
        }

    exclude  = {BENCHMARK} | set(SECTOR_ETFS.values())
    raw_scores: dict[str, dict] = {}

    # Paso 1: calcular RS raw para todos los tickers
    for ticker in [t for t in close.columns if t not in exclude]:
        prices = close[ticker].dropna()
        spy_a  = spy.reindex(prices.index).ffill()
        if len(prices) < max(PERIODS): continue
        try:
            rs_by_p = {}
            rs_series_main = None  # usaremos 63d como serie principal para trend/momentum

            for p in PERIODS:
                if len(prices) < p: continue
                rs_s = _rs_series_smoothed(prices, spy_a, p)
                if len(rs_s.dropna()) < 5: continue
                rs_by_p[f"rs_{p}d_smooth"] = round(float(rs_s.iloc[-1]), 6)
                if p == 63:
                    rs_series_main = rs_s

            if not rs_by_p: continue

            # Score ponderado con los períodos disponibles
            avail   = [p for p in PERIODS if f"rs_{p}d_smooth" in rs_by_p]
            w_total = sum(WEIGHTS[p] for p in avail)
            rs_score_raw = sum(rs_by_p[f"rs_{p}d_smooth"] * (WEIGHTS[p]/w_total) for p in avail)

            # RS Momentum = diferencia entre corto y largo plazo suavizados
            # Positivo = ganando fuerza relativa, negativo = perdiendo
            rs_momentum = 0.0
            if "rs_21d_smooth" in rs_by_p and "rs_63d_smooth" in rs_by_p:
                rs_momentum = round(rs_by_p["rs_21d_smooth"] - rs_by_p["rs_63d_smooth"], 6)

            # Tendencia del RS
            trend = _rs_trend(rs_series_main) if rs_series_main is not None else 0.0

            # RVOL
            rvol = 1.0
            if ticker in volume.columns:
                vs = volume[ticker].replace(0, np.nan).dropna()
                if len(vs) >= 5:
                    avg = float(vs.iloc[-20:].mean() if len(vs) >= 20 else vs.mean())
                    cur = float(vs.iloc[-1])
                    rvol = round(min(max(cur/avg if avg > 0 else 1.0, 0.1), 20.0), 4)

            sector  = GICS_MAP.get(smap.get(ticker,""), "Otros")
            raw_scores[ticker] = {
                **rs_by_p,
                "rs_score_raw":  round(rs_score_raw, 6),
                "rs_momentum":   rs_momentum,
                "rs_trend":      trend,
                "rvol":          rvol,
                "sector":        sector,
                "price":         round(float(prices.iloc[-1]), 4),
            }
        except Exception:
            continue

    if not raw_scores:
        return {}, sector_rs, spy_perf

    # Paso 2: convertir RS score a PERCENTIL dentro del universo (0–99)
    # Esto es el cambio clave: elimina la dependencia del valor absoluto del mercado
    scores_array = np.array([v["rs_score_raw"] for v in raw_scores.values()])
    tickers_list = list(raw_scores.keys())

    results = {}
    for i, ticker in enumerate(tickers_list):
        d    = raw_scores[ticker]
        pct  = float(scipy_stats.percentileofscore(scores_array, d["rs_score_raw"], kind="rank"))
        pct  = round(min(pct, 99.0), 1)  # cap en 99 como IBD

        # RS vs Sector (usando rs_63d_smooth para consistencia con sector_rs)
        sector     = d["sector"]
        rs_vs_s    = 0.0
        if sector in sector_rs and "rs_63d_smooth" in d:
            rs_vs_s = round(d["rs_63d_smooth"] - sector_rs[sector]["RS"], 6)

        results[ticker] = {
            "rs_percentile": pct,                          # 0–99, principal métrica
            "rs_score_raw":  d["rs_score_raw"],            # valor absoluto (referencia)
            "rs_21d":        d.get("rs_21d_smooth", 0),   # corto plazo suavizado
            "rs_63d":        d.get("rs_63d_smooth", 0),   # medio plazo suavizado
            "rs_126d":       d.get("rs_126d_smooth", 0),  # largo plazo suavizado
            "rs_momentum":   d["rs_momentum"],             # ¿ganando/perdiendo fuerza?
            "rs_trend":      d["rs_trend"],                # pendiente tendencia RS
            "rs_vs_sector":  rs_vs_s,
            "rvol":          d["rvol"],
            "sector":        sector,
            "price":         d["price"],
        }

    print(f"  ✓ {len(results)} stocks · {len(sector_rs)} sectores")
    return results, sector_rs, spy_perf

# ─────────────────────────────────────────────────────────────
def save_to_gist(payload):
    token   = os.environ.get("GH_GIST_TOKEN")
    gist_id = os.environ.get("RSRW_GIST_ID")
    if not token or not gist_id:
        with open("rsrw_scan_output.json", "w") as f:
            json.dump(payload, f, indent=2)
        print("[5/5] ⚠ Sin credenciales — guardado en rsrw_scan_output.json")
        return True
    print("[5/5] Guardando en GitHub Gist...")
    try:
        r = requests.patch(f"https://api.github.com/gists/{gist_id}",
            headers={"Authorization":f"token {token}","Accept":"application/vnd.github.v3+json"},
            json={"files":{GIST_FILE:{"content":json.dumps(payload, separators=(",",":"))}}},
            timeout=20)
        r.raise_for_status()
        print(f"  ✓ Gist actualizado")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

# ─────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    print("="*60)
    print("RSRW COMPUTE WORKER v4.0")
    print(f"UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}")
    print(f"Períodos: {PERIODS}d · Pesos: {WEIGHTS}")
    print(f"EMA smooth: {EMA_SMOOTH}d · Trend window: {TREND_WIN}d")
    print("="*60)

    tickers, smap = get_sp500_tickers()
    close, volume = download_all(tickers)
    if close is None:
        print("✗ Sin datos"); exit(1)

    stocks, sectors, spy_perf = compute_metrics(close, volume, smap)
    if not stocks:
        print("✗ Sin resultados"); exit(1)

    print("[4/5] Construyendo payload...")
    payload = {
        "meta": {
            "timestamp_utc":  datetime.now(timezone.utc).isoformat(),
            "tickers_total":  len(tickers),
            "tickers_scored": len(stocks),
            "spy_perf_20d":   round(spy_perf, 6),
            "benchmark":      BENCHMARK,
            "periods":        PERIODS,
            "weights":        WEIGHTS,
            "ema_smooth":     EMA_SMOOTH,
            "methodology":    "percentile_ema_smoothed",
            "version":        "4.0",
        },
        "sectors": sectors,
        "stocks":  stocks,
    }
    kb = len(json.dumps(payload)) / 1024
    print(f"  ✓ Payload: {kb:.1f} KB · {len(stocks)} stocks")

    ok = save_to_gist(payload)
    print("="*60)
    print(f"{'✓ OK' if ok else '✗ FAIL'} en {time.time()-t0:.1f}s")
    print("="*60)

if __name__ == "__main__":
    main()
