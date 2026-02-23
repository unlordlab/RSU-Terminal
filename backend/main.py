# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import yfinance as yf
from datetime import datetime
import os

app = FastAPI(title="RSU Backend")

# CORS para permitir que Streamlit llame al backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: tu URL de Streamlit
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectar a Redis (Railway creará esta variable automáticamente)
redis_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True
)

# Cache local en memoria (más rápido que Redis)
_local_cache = {}

@app.get("/")
def home():
    """Página de inicio - verifica que todo funciona"""
    try:
        redis_ok = redis_client.ping()
    except:
        redis_ok = False
    
    return {
        "status": "RSU Backend activo",
        "redis_connected": redis_ok,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/price/{symbol}")
def get_price(symbol: str):
    """
    Obtiene precio actual con cache de 30 segundos.
    100 usuarios = 1 llamada a Yahoo cada 30s, no 100.
    """
    symbol = symbol.upper()
    cache_key = f"price:{symbol}"
    now = datetime.now().timestamp()
    
    # 1. Cache local (más rápido)
    if cache_key in _local_cache:
        data, timestamp = _local_cache[cache_key]
        if now - timestamp < 30:  # 30 segundos
            return {**data, "from_cache": "memory"}
    
    # 2. Cache Redis (segunda capa)
    try:
        cached = redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            _local_cache[cache_key] = (data, now)  # Guardar en memoria también
            return {**data, "from_cache": "redis"}
    except Exception as e:
        print(f"Redis error: {e}")
    
    # 3. Fetch de Yahoo Finance (solo si no hay cache)
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        result = {
            "symbol": symbol,
            "price": info.get("regularMarketPrice", 0),
            "change": info.get("regularMarketChangePercent", 0),
            "volume": info.get("regularMarketVolume", 0),
            "time": datetime.now().isoformat()
        }
        
        # Guardar en ambos caches
        _local_cache[cache_key] = (result, now)
        try:
            redis_client.setex(cache_key, 60, json.dumps(result))  # 60s en Redis
        except:
            pass  # Si Redis falla, al menos tenemos memoria
        
        return {**result, "from_cache": False}
        
    except Exception as e:
        raise HTTPException(500, f"Error obteniendo datos: {str(e)}")

@app.get("/api/history/{symbol}")
def get_history(symbol: str, period: str = "1mo"):
    """
    Datos históricos con cache de 5 minutos.
    """
    symbol = symbol.upper()
    cache_key = f"history:{symbol}:{period}"
    
    # Intentar leer de Redis
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return {**json.loads(cached), "from_cache": True}
    except:
        pass
    
    # Fetch de Yahoo
    try:
        data = yf.download(symbol, period=period, progress=False)
        if data.empty:
            raise HTTPException(404, f"Símbolo {symbol} no encontrado")
        
        result = {
            "symbol": symbol,
            "period": period,
            "data": data.reset_index().to_dict("records"),
            "columns": list(data.columns),
            "last_price": float(data['Close'].iloc[-1])
        }
        
        # Guardar en Redis por 5 minutos (300 segundos)
        try:
            redis_client.setex(cache_key, 300, json.dumps(result))
        except:
            pass
        
        return result
        
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@app.get("/api/batch")
def get_batch_prices(symbols: str):
    """
    Obtiene múltiples precios en UNA sola llamada.
    Ejemplo: /api/batch?symbols=AAPL,MSFT,NVDA
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    results = {}
    
    for symbol in symbol_list:
        try:
            # Reutilizar la función get_price (con su cache)
            data = get_price(symbol)
            results[symbol] = {
                "price": data.get("price"),
                "change": data.get("change"),
                "cached": data.get("from_cache", False) != False
            }
        except Exception as e:
            results[symbol] = {"error": str(e)}
    
    return {
        "count": len(results),
        "data": results,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    """Para que Railway sepa que estamos vivos"""
    return {"status": "ok"}
