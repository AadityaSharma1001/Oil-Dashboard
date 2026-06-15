import pandas as pd
import numpy as np
import yfinance as yf
from collections import deque
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class StateManager:
    def __init__(self, window_size_mins=65):
        self.window_size_mins = window_size_mins
        # We proxy GO (Gasoil) with HO (Heating Oil) since ICE Gasoil isn't on yfinance
        self.tickers = {"WTI": "CL=F", "BRENT": "BZ=F", "HO": "HO=F", "GO": "HO=F"}
        
        self.history = {asset: deque(maxlen=window_size_mins) for asset in self.tickers}
        self.latest_features = {}
        self.latest_prices = {}
        self.on_tick_callbacks = []
        
        # Kalman Filter Parameters
        self.kalman_states = {asset: {"x": None, "P": 1.0} for asset in self.tickers}
        self.kalman_Q = 1e-5  # Process noise
        self.kalman_R = 1e-2  # Measurement noise
        
    def register_callback(self, callback):
        """Register a callback to be fired on every new tick."""
        self.on_tick_callbacks.append(callback)
        
    async def poll_data(self):
        """Polls yfinance every 15 seconds to simulate a live 1-min feed."""
        logger.info("Starting yfinance tick polling loop...")
        while True:
            try:
                prices = {}
                symbols = list(dict.fromkeys(self.tickers.values()))  # deduplicate
                # Download all at once to match header behavior and bypass single-ticker cache
                data = await asyncio.to_thread(
                    yf.download, tickers=symbols, period='5d', interval='1m', group_by="ticker", progress=False, threads=True
                )
                
                if not data.empty:
                    for asset, ticker in self.tickers.items():
                        # Handle multi-index columns from yfinance 0.2+
                        if isinstance(data.columns, pd.MultiIndex):
                            if ticker in data.columns.get_level_values(0):
                                close_series = data[ticker]['Close']
                            else:
                                continue
                        else:
                            close_series = data['Close']
                            
                        close_series = close_series.dropna()
                        if close_series.empty:
                            continue
                            
                        last_close = float(close_series.iloc[-1])
                        
                        if asset in ["HO", "GO"]:
                            last_close = last_close * 42.0
                            prices_history = (close_series * 42.0).tail(self.window_size_mins).tolist()
                        else:
                            prices_history = close_series.tail(self.window_size_mins).tolist()
                            
                        prices[asset] = last_close
                        
                        self.history[asset].clear()
                        self.history[asset].extend(prices_history)
                
                self.latest_prices = prices
                if prices:
                    logger.info(f"TICK prices: WTI={prices.get('WTI','?'):.2f}, BRENT={prices.get('BRENT','?'):.2f}")
                    self.calculate_features(prices)
                    # Notify all listeners (like the Broker/Model loader)
                    for cb in self.on_tick_callbacks:
                        await cb(prices, self.latest_features)
                else:
                    logger.warning("poll_data: yfinance returned no prices")
                        
            except Exception as e:
                logger.error(f"Error polling yfinance: {e}", exc_info=True)
                
            await asyncio.sleep(15)
            
    def calculate_features(self, current_prices):
        """Constructs df_raw with 61+ periods of curve structures and kalman estimates."""
        data = {}
        lengths = [len(h) for h in self.history.values()]
        min_len = min(lengths) if lengths else 0
        if min_len < 61:
            logger.warning(f"Not enough data. History lengths: {lengths}")
            return None # Not enough data
            
        for asset in self.tickers:
            c1_series = np.array(self.history[asset])[-min_len:]
            data[f'{asset}_c1'] = c1_series
            data[f'{asset}_c6'] = c1_series * 0.99
            data[f'{asset}_c12'] = c1_series * 0.98
            
            c1 = current_prices.get(asset, 0)
            k_state = self.kalman_states[asset]
            if k_state["x"] is None and c1 > 0:
                k_state["x"] = c1
            if k_state["x"] is not None and c1 > 0:
                x_pred = k_state["x"]
                P_pred = k_state["P"] + self.kalman_Q
                K = P_pred / (P_pred + self.kalman_R)
                k_state["x"] = x_pred + K * (c1 - x_pred)
                k_state["P"] = (1 - K) * P_pred
            
            # Fill the entire column with the latest kalman state so iloc[-1] accesses it easily
            data[f'{asset}_Kalman'] = [k_state["x"]] * min_len
            
        df_raw = pd.DataFrame(data)
        self.latest_features = df_raw
        return df_raw

state_manager = StateManager()
