# modules/api_client.py
import requests
import streamlit as st
import pandas as pd

# URL del backend (Railway) o fallback a local
BACKEND_URL = st.secrets.get("RSU_BACKEND_URL", "http://localhost:8000")

class RSUApiClient:
    """
    Cliente para conectar con backend Railway
    """
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
    
    def get_price(self, symbol: str):
        """Obtiene precio actual con cache"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/price/{symbol.upper()}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                # Mostrar indicador de cache
                cache_type = data.get("from_cache")
                if cache_type == "memory":
                    st.caption("⚡ Cache memoria")
                elif cache_type == "redis":
                    st.caption("🟢 Cache Redis")
                elif cache_type:
                    st.caption("📡 Directo")
                return data
        except Exception as e:
            st.warning(f"Backend no disponible: {e}")
        return None
    
    def get_history(self, symbol: str, period: str = "1mo"):
        """Obtiene datos históricos"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/history/{symbol.upper()}",
                params={"period": period},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                # Convertir a DataFrame
                if "data" in data:
                    df = pd.DataFrame(data["data"])
                    # Convertir fecha a índice si existe
                    date_col = "Date" if "Date" in df.columns else "Datetime" if "Datetime" in df.columns else None
                    if date_col:
                        df[date_col] = pd.to_datetime(df[date_col])
                        df.set_index(date_col, inplace=True)
                    return df
                return data
        except Exception as e:
            st.warning(f"Usando datos locales: {e}")
        return None
    
    def test_connection(self):
        """Prueba conexión con backend"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=3)
            return response.status_code == 200
        except:
            return False

# Singleton para reutilizar
@st.cache_resource
def get_api_client():
    return RSUApiClient()
