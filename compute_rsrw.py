"""
compute_rsrw.py — GitHub Actions Worker
========================================
Ejecuta en GitHub Actions (cron cada 30 min en horario de mercado).
Descarga ~550 tickers, calcula RS scores y guarda resultado en GitHub Gist.

Secrets necesarios en GitHub Actions:
  - GH_GIST_TOKEN        → token con scope 'gist'
  - RSRW_GIST_ID         → ID del Gist donde guardar el JSON

Uso local para test:
  python compute_rsrw.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
import requests
import os
import time
from datetime import datetime, timezone

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

BENCHMARK = "SPY"

SECTOR_ETFS = {
    "Tecnología":             "XLK",
    "Salud":                  "XLV",
    "Financieros":            "XLF",
    "Consumo Discrecional":   "XLY",
    "Consumo Básico":         "XLP",
    "Industriales":           "XLI",
    "Energía":                "XLE",
    "Materiales":             "XLB",
    "Servicios Públicos":     "XLU",
    "Bienes Raíces":          "XLRE",
    "Comunicaciones":         "XLC",
}

# Períodos y pesos del score compuesto
PERIODS  = [5, 20, 60]
WEIGHTS  = {5: 0.50, 20: 0.30, 60: 0.20}

GIST_FILENAME = "rsrw_scan.json"
BATCH_SIZE    = 80
LOOKBACK_DAYS = "70d"

# =============================================================================
# OBTENER UNIVERSO S&P 500
# =============================================================================

def get_sp500_tickers() -> list[str]:
    """Obtiene lista limpia del S&P 500 desde Wikipedia con fallback."""
    print("[1/5] Obteniendo universo S&P 500...")
    try:
        df = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            match="Symbol"
        )[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        if len(tickers) >= 490:
            # Guardar sector de Wikipedia para enriquecer resultados
            sector_map = dict(zip(
                df["Symbol"].str.replace(".", "-", regex=False),
                df["GICS Sector"]
            ))
            print(f"  ✓ {len(tickers)} tickers obtenidos de Wikipedia")
            return tickers, sector_map
    except Exception as e:
        print(f"  ✗ Wikipedia falló: {e}")

    # Fallback: lista hardcoded conocida (~250 tickers top del S&P)
    fallback = [
        "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","AVGO","JPM",
        "LLY","V","UNH","XOM","MA","JNJ","PG","HD","MRK","COST","ABBV","CVX",
        "BAC","KO","CRM","PEP","TMO","WFC","NFLX","ORCL","AMD","ACN","ADBE","LIN",
        "MCD","PM","WMT","CSCO","IBM","GS","GE","HON","DIS","CAT","RTX","AMGN",
        "VZ","T","CMCSA","PFE","ABT","TXN","MS","NEE","BMY","SPGI","DHR","UNP",
        "LOW","BLK","ISRG","GILD","SYK","MDT","C","REGN","AXP","PNC","CB","MMC",
        "VRTX","ETN","SHW","CI","BSX","ELV","ITW","DE","NOC","LMT","EMR","GD",
        "USB","TFC","SCHW","COF","MCO","ICE","CME","PGR","AIG","MET","WELL",
        "COP","EOG","SLB","OXY","PSX","MPC","VLO","WMB","KMI","OKE","EPD",
        "FCX","NEM","DOW","ECL","NUE","VMC","PPG","ALB","LYB","PLD","AMT",
        "CCI","EQIX","PSA","O","DLR","SPG","VICI","AVB","EQR","EXR","BXP",
        "CRWD","PANW","SNOW","PLTR","NET","UBER","ABNB","SQ","SHOP","DXCM",
        "ENPH","FSLR","CEG","VST","NRG","AEP","SRE","EXC","XEL","ED","WEC",
        "AWK","D","FE","AEE","CMS","ETR","ZTS","IQV","EW","IDXX","ILMN",
        "BIIB","MRNA","BNTX","HUM","ANTM","CVS","CAH","MCK","ABC","WBA",
        "YUM","SBUX","BKNG","MAR","HLT","CCL","RCL","NCLH","LVS","MGM",
        "TTWO","EA","MTCH","LYV","FOXA","NWSA","WBD","PARA","IPG","OMC",
        "K","HSY","MKC","GIS","MDLZ","KHC","CAG","SJM","HRL","TSN","BG",
        "INTC","QCOM","MU","KLAC","LRCX","AMAT","SNPS","CDNS","ADI","MCHP",
        "TGT","DG","DLTR","TJX","ROST","GPS","ANF","PVH","RL","HBI","VFC",
        "NKE","LULU","UAA","UPS","FDX","NSC","CSX","DAL","UAL","LUV","AAL",
    ]
    sector_map = {}
    print(f"  ✓ Usando fallback hardcoded: {len(fallback)} tickers")
    return list(dict.fromkeys(fallback)), sector_map


# =============================================================================
# DESCARGA DE DATOS EN BATCHES
# =============================================================================

def download_all(symbols: list[str]) -> pd.DataFrame | None:
    """
    Descarga datos históricos para todos los símbolos + benchmark + ETFs sector.
    Usa yf.Ticker().history() para evitar problemas de MultiIndex.
    Devuelve DataFrame con índice=fecha, columnas=ticker (solo Close y Volume).
    """
    all_symbols = list(dict.fromkeys(
        [BENCHMARK] + list(SECTOR_ETFS.values()) + symbols
    ))
    batches = [all_symbols[i:i+BATCH_SIZE] for i in range(0, len(all_symbols), BATCH_SIZE)]

    close_frames  = {}
    volume_frames = {}

    print(f"[2/5] Descargando {len(all_symbols)} símbolos en {len(batches)} lotes...")

    for idx, batch in enumerate(batches):
        print(f"  Lote {idx+1}/{len(batches)} ({len(batch)} símbolos)...")
        for attempt in range(3):
            try:
                if idx > 0:
                    time.sleep(0.8)
                raw = yf.download(
                    batch,
                    period=LOOKBACK_DAYS,
                    interval="1d",
                    progress=False,
                    threads=True,
                    timeout=30,
                    auto_adjust=True,
                )
                if raw.empty:
                    raise ValueError("Empty response")

                # Normalizar siempre a MultiIndex
                if isinstance(raw.columns, pd.MultiIndex):
                    if "Close" in raw.columns.get_level_values(0):
                        for t in raw["Close"].columns:
                            s = raw["Close"][t].dropna()
                            if len(s) > 5:
                                close_frames[t] = s
                    if "Volume" in raw.columns.get_level_values(0):
                        for t in raw["Volume"].columns:
                            s = raw["Volume"][t].dropna()
                            if len(s) > 5:
                                volume_frames[t] = s
                else:
                    # Caso de un solo ticker (raro en batch)
                    if "Close" in raw.columns:
                        close_frames[batch[0]] = raw["Close"].dropna()
                    if "Volume" in raw.columns:
                        volume_frames[batch[0]] = raw["Volume"].dropna()
                break

            except Exception as e:
                print(f"    Intento {attempt+1} falló: {e}")
                if attempt == 2:
                    print(f"    ✗ Lote {idx+1} descartado")
                time.sleep(2)

    if not close_frames:
        print("✗ No se descargaron datos.")
        return None, None

    close  = pd.DataFrame(close_frames)
    volume = pd.DataFrame(volume_frames)

    # Alinear índices
    close  = close.sort_index().dropna(how="all")
    volume = volume.reindex(close.index).fillna(0)

    print(f"  ✓ {len(close.columns)} tickers con datos válidos ({len(close)} días)")
    return close, volume


# =============================================================================
# CÁLCULO DE MÉTRICAS RS
# =============================================================================

def compute_metrics(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    sector_map: dict,
) -> tuple[dict, dict, float]:
    """
    Calcula RS Score ponderado multi-período, RVOL real, RS vs sector.
    Devuelve (stocks_dict, sectors_dict, spy_perf_20d).
    """
    print("[3/5] Calculando métricas RS...")

    if BENCHMARK not in close.columns:
        print("✗ SPY no encontrado en datos.")
        return {}, {}, 0.0

    spy = close[BENCHMARK].dropna()

    # --- Rendimiento del SPY ---
    spy_perf_20d = float((spy.iloc[-1] / spy.iloc[-20]) - 1) if len(spy) >= 20 else 0.0

    # --- RS de sectores (20d) ---
    sector_rs: dict[str, dict] = {}
    for sector_name, etf in SECTOR_ETFS.items():
        if etf not in close.columns:
            continue
        s = close[etf].dropna()
        if len(s) < 20:
            continue
        etf_ret  = float((s.iloc[-1] / s.iloc[-20]) - 1)
        spy_ret  = float((spy.iloc[-1] / spy.iloc[-20]) - 1)
        sector_rs[sector_name] = {
            "RS":     round(etf_ret - spy_ret, 6),
            "Return": round(etf_ret, 6),
            "ETF":    etf,
        }

    # --- Columnas a procesar (excluir benchmark y ETFs) ---
    exclude = {BENCHMARK} | set(SECTOR_ETFS.values())
    tickers = [t for t in close.columns if t not in exclude]

    results: dict[str, dict] = {}

    for ticker in tickers:
        prices = close[ticker].dropna()
        if len(prices) < max(PERIODS):
            continue

        try:
            # Retornos por período
            rs_by_period: dict[str, float] = {}
            for p in PERIODS:
                if len(prices) < p:
                    continue
                stock_ret = float((prices.iloc[-1] / prices.iloc[-p]) - 1)
                spy_ret_p = float((spy.iloc[-1] / spy.iloc[-p]) - 1) if len(spy) >= p else 0.0
                rs_by_period[f"rs_{p}d"] = round(stock_ret - spy_ret_p, 6)

            if not rs_by_period:
                continue

            # Score ponderado (solo con períodos disponibles)
            available = [p for p in PERIODS if f"rs_{p}d" in rs_by_period]
            w_total   = sum(WEIGHTS[p] for p in available)
            rs_score  = sum(rs_by_period[f"rs_{p}d"] * (WEIGHTS[p] / w_total) for p in available)

            # Sector desde Wikipedia o fallback
            wiki_sector = sector_map.get(ticker, "")
            # Mapeo GICS → nuestros nombres
            GICS_MAP = {
                "Information Technology":   "Tecnología",
                "Health Care":              "Salud",
                "Financials":               "Financieros",
                "Consumer Discretionary":   "Consumo Discrecional",
                "Consumer Staples":         "Consumo Básico",
                "Industrials":              "Industriales",
                "Energy":                   "Energía",
                "Materials":                "Materiales",
                "Utilities":                "Servicios Públicos",
                "Real Estate":              "Bienes Raíces",
                "Communication Services":   "Comunicaciones",
            }
            sector = GICS_MAP.get(wiki_sector, "Otros")

            # RS vs Sector (usando 20d para consistencia con sector_rs)
            rs_vs_sector = 0.0
            if sector in sector_rs and "rs_20d" in rs_by_period:
                rs_vs_sector = round(rs_by_period["rs_20d"] - sector_rs[sector]["RS"], 6)

            # RVOL: volumen hoy vs media 20 días
            rvol = 1.0
            if ticker in volume.columns:
                vol_series = volume[ticker].replace(0, np.nan).dropna()
                if len(vol_series) >= 5:
                    avg_vol     = float(vol_series.iloc[-20:].mean()) if len(vol_series) >= 20 else float(vol_series.mean())
                    current_vol = float(vol_series.iloc[-1])
                    rvol = round(current_vol / avg_vol, 4) if avg_vol > 0 else 1.0
                    rvol = max(0.1, min(rvol, 20.0))  # cap razonable

            results[ticker] = {
                **rs_by_period,
                "rs_score":     round(rs_score, 6),
                "rs_vs_sector": rs_vs_sector,
                "rvol":         rvol,
                "sector":       sector,
                "price":        round(float(prices.iloc[-1]), 4),
            }

        except Exception as e:
            continue

    print(f"  ✓ {len(results)} stocks calculados | {len(sector_rs)} sectores")
    return results, sector_rs, spy_perf_20d


# =============================================================================
# GUARDAR EN GITHUB GIST
# =============================================================================

def save_to_gist(payload: dict) -> bool:
    """Actualiza el Gist con los datos calculados."""
    token   = os.environ.get("GH_GIST_TOKEN")
    gist_id = os.environ.get("RSRW_GIST_ID")

    if not token or not gist_id:
        # Guardar localmente para test
        with open("rsrw_scan_output.json", "w") as f:
            json.dump(payload, f, indent=2)
        print("[5/5] ⚠ Sin credenciales Gist — guardado en rsrw_scan_output.json")
        return True

    print("[5/5] Guardando en GitHub Gist...")
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {
        "Authorization": f"token {token}",
        "Accept":        "application/vnd.github.v3+json",
    }
    body = {
        "files": {
            GIST_FILENAME: {
                "content": json.dumps(payload, separators=(",", ":"))
            }
        }
    }
    try:
        r = requests.patch(url, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        print(f"  ✓ Gist actualizado: https://gist.github.com/{gist_id}")
        return True
    except Exception as e:
        print(f"  ✗ Error actualizando Gist: {e}")
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    start = time.time()
    print("=" * 60)
    print("RSRW COMPUTE WORKER")
    print(f"Hora UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 1. Universo
    tickers, sector_map = get_sp500_tickers()

    # 2. Descarga
    close, volume = download_all(tickers)
    if close is None:
        print("✗ Abortando — sin datos")
        exit(1)

    # 3. Métricas
    stocks, sectors, spy_perf = compute_metrics(close, volume, sector_map)
    if not stocks:
        print("✗ Abortando — sin resultados")
        exit(1)

    # 4. Construir payload
    print("[4/5] Construyendo payload JSON...")
    payload = {
        "meta": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "tickers_total": len(tickers),
            "tickers_scored": len(stocks),
            "spy_perf_20d": round(spy_perf, 6),
            "benchmark": BENCHMARK,
            "periods": PERIODS,
            "weights": WEIGHTS,
            "version": "3.0",
        },
        "sectors": sectors,
        "stocks":  stocks,
    }
    print(f"  ✓ Payload: {len(json.dumps(payload)) / 1024:.1f} KB")

    # 5. Guardar
    ok = save_to_gist(payload)

    elapsed = time.time() - start
    print("=" * 60)
    print(f"{'✓ COMPLETADO' if ok else '✗ FALLIDO'} en {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
