import asyncio
import logging
from app.services.trading.state_manager import state_manager
from app.services.trading.model_service import model_service
from app.services.trading.paper_broker import paper_broker
from app.api.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

async def on_tick(current_prices, df_raw):
    """
    Called every time a new tick of data arrives and features are calculated.
    """
    try:
        if df_raw is None or isinstance(df_raw, dict) or (hasattr(df_raw, "empty") and df_raw.empty):
            logger.info("Not enough data to calculate features yet.")
            return
            
        payload = {
            "type": "trading_update",
            "hmm_regimes": {},
            "active_signals": {},
            "positions": paper_broker.open_positions,
            "z_score": 0.0,
            "metrics": {},
            "prices": current_prices
        }
        
        for asset in ["WTI", "BRENT", "HO", "GO"]:
            # 1. Get HMM Regime & ML Signals
            state, display_features, signals = model_service.process_data_and_get_signals(df_raw, asset)
            
            payload["hmm_regimes"][asset] = state
            for strat, sig in signals.items():
                payload["active_signals"][f"{asset}_{strat}"] = sig
            
            # 2. Execute Paper Trades
            price = current_prices.get(asset, 0)
            if price > 0:
                paper_broker.process_tick(asset, price, signals)
                
            # Extract Z-Score for the dashboard
            if asset == "WTI":
                payload["z_score"] = display_features.get("Global_Crude_Z_Score", 0.0)
                logger.info(f"Broadcast tick for WTI: Z-Score={payload['z_score']}, df_raw shape={df_raw.shape}")

        # 3. Update PnL & Metrics
        payload["positions"] = {k: dict(v) for k, v in paper_broker.open_positions.items()}
        payload["metrics"] = paper_broker.get_metrics()
        payload["metrics"]["unrealized_pnl"] = paper_broker.get_unrealized_pnl(current_prices)
        payload["trade_ledger"] = list(paper_broker.trade_ledger)
        
        # 4. Broadcast to frontend
        await ws_manager.broadcast("trading", payload)
        
    except Exception as e:
        logger.error(f"Error in on_tick orchestrator: {e}", exc_info=True)

def start_trading_engine():
    """Initializes models and registers the orchestrator loop."""
    logger.info("Initializing Paper Trading Engine...")
    model_service.load_models()
    state_manager.register_callback(on_tick)
    logger.info("Trading Engine Orchestrator Ready.")
