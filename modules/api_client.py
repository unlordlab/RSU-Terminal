import requests
import streamlit as st

BACKEND_URL = st.secrets.get("RSU_BACKEND_URL", "http://localhost:8000")

class RSUApiClient:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
    
    def get_price(self, symbol: str):
        try:
            response = self.session.get(
                f"{self.base_url}/api/price/{symbol}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("from_cache"):
                    st.caption("🟢 Cache")
                return data
        except Exception as e:
            st.error(f"Backend error: {e}")
        return None
    
    def get_history(self, symbol: str, period: str = "1mo"):
        try:
            response = self.session.get(
                f"{self.base_url}/api/history/{symbol}",
                params={"period": period},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            st.error(f"Backend error: {e}")
        return None

@st.cache_resource
def get_api_client():
    return RSUApiClient()
