import pandas as pd
import pandas_ta as ta

class RSUAlgoritmo:
    def __init__(self):
        # Memoria del algoritmo: guardamos los últimos precios para calcular indicadores
        self.df = pd.DataFrame(columns=['close', 'volume'])
        self.estado_actual = "ROJO" # Estado inicial
        self.soporte_previo = None
        self.resistencia_previa = None

    def procesar_dato(self, precio, volumen):
        """Añade un nuevo precio y recalcula el semáforo"""
        # 1. Actualizar datos
        nuevo_dato = pd.DataFrame([{'close': precio, 'volume': volumen}])
        self.df = pd.concat([self.df, nuevo_dato], ignore_index=True)
        
        # Mantener solo las últimas 300 velas para optimizar rendimiento
        if len(self.df) > 300:
            self.df = self.df.iloc[-300:].reset_index(drop=True)

        # 2. Si no hay suficientes datos para el RSI (necesita al menos 14), esperamos
        if len(self.df) < 20:
            return "CALIBRANDO..."

        return self.calcular_logica()

    def calcular_logica(self):
        # --- INDICADORES ---
        # RSI de 14 periodos
        self.df['rsi'] = ta.rsi(self.df['close'], length=14)
        rsi_actual = self.df['rsi'].iloc[-1]
        
        # Macro tendencia (Media Móvil de 200 periodos o proporcional a los datos)
        sma_200 = self.df['close'].rolling(window=min(len(self.df), 200)).mean().iloc[-1]
        precio_actual = self.df['close'].iloc[-1]
        
        # --- LÓGICA DE RILEY & CORRECCIONES ---
        en_correccion = rsi_actual < 35  # Basado en tu premisa de comprar en correcciones
        
        # --- CHANGE OF CHARACTER (CHoCH) ---
        # Detectamos si el precio rompe el máximo de las últimas 5 velas (giro al alza)
        max_reciente = self.df['close'].iloc[-6:-1].max()
        choch_alcista = precio_actual > max_reciente

        # --- LÓGICA DEL SEMÁFORO ---
        
        # 🟢 VERDE: Precio > SMA200 (Macro alcista) + Salida de sobreventa + CHoCH alcista
        if precio_actual > sma_200 and rsi_actual > 35 and choch_alcista:
            # Aquí se cumple la premisa de Riley tras una corrección
            self.estado_actual = "VERDE"
            
        # 🟡 ÁMBAR: Estamos en corrección (RSI bajo) pero aún no hay CHoCH
        elif en_correccion:
            self.estado_actual = "AMBAR"
            
        # 🔴 ROJO: Macro bajista o mercado sobreextendido (RSI > 70)
        elif precio_actual < sma_200 or rsi_actual > 70:
            self.estado_actual = "ROJO"
        
        # Si no cambia drásticamente, mantiene el último estado conocido
        return self.estado_actual
