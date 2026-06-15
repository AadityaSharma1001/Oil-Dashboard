import os
import json
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PaperBroker:
    def __init__(self):
        self.multipliers = {
            "WTI": 1000.0,
            "BRENT": 1000.0,
            "HO": 1000.0, # 1000 barrels per contract (42,000 gallons)
            "GO": 1000.0   # generic multiplier
        }
        
        # Risk Management (Point values)
        self.default_risk = {
            "WTI": {"SL": 0.50, "TP": 1.50},
            "BRENT": {"SL": 0.50, "TP": 1.50},
            "HO": {"SL": 0.02, "TP": 0.05},
            "GO": {"SL": 0.02, "TP": 0.05}
        }
        
        self.initial_capital = 100000.0
        self.open_positions = {}
        self.trade_ledger = []
        self.total_pnl = 0.0
        self.equity_curve = [{"timestamp": datetime.utcnow().isoformat(), "equity": self.initial_capital}]
        
        self.state_file = "/app/data/paper_broker_state.json"
        self.load_state()
        
    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                self.open_positions = state.get("open_positions", {})
                self.trade_ledger = state.get("trade_ledger", [])
                self.total_pnl = state.get("total_pnl", 0.0)
                self.equity_curve = state.get("equity_curve", [{"timestamp": datetime.utcnow().isoformat(), "equity": self.initial_capital}])
                logger.info("Successfully loaded PaperBroker state from disk.")
            except Exception as e:
                logger.error(f"Failed to load PaperBroker state: {e}")
                
    def save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        try:
            state = {
                "open_positions": self.open_positions,
                "trade_ledger": self.trade_ledger,
                "total_pnl": self.total_pnl,
                "equity_curve": self.equity_curve
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"Failed to save PaperBroker state: {e}")
        
    def _close_position(self, key, exit_price, reason="Signal Change", timestamp=None):
        if key not in self.open_positions:
            return
            
        pos = self.open_positions.pop(key)
        asset = key.split("_")[0]
        mult = self.multipliers.get(asset, 1000.0)
        
        direction = pos["direction"]
        entry = pos["entry_price"]
        qty = pos["qty"]
        
        points_gained = (exit_price - entry) * direction
        realized_pnl = points_gained * mult * qty
        
        self.total_pnl += realized_pnl
        
        trade_record = {
            "id": str(uuid.uuid4())[:8],
            "asset_strat": key,
            "direction": "LONG" if direction == 1 else "SHORT",
            "entry_price": entry,
            "exit_price": exit_price,
            "sl": pos["sl"],
            "tp": pos["tp"],
            "pnl": realized_pnl,
            "reason": reason,
            "timestamp": timestamp or datetime.utcnow().isoformat()
        }
        
        self.trade_ledger.append(trade_record)
        self.equity_curve.append({"timestamp": trade_record["timestamp"], "equity": self.initial_capital + self.total_pnl})
        
        logger.info(f"CLOSED {key}: {trade_record['direction']} at {exit_price} | PnL: ${realized_pnl:.2f} | Reason: {reason}")
        
    def _open_position(self, key, direction, entry_price):
        asset = key.split("_")[0]
        risk = self.default_risk.get(asset, {"SL": 0.5, "TP": 1.5})
        
        sl = entry_price - (risk["SL"] * direction)
        tp = entry_price + (risk["TP"] * direction)
        
        mult = self.multipliers.get(asset, 1000.0)
        
        # Calculate quantity to allocate exactly 100k notional
        qty = self.initial_capital / (entry_price * mult)
        
        self.open_positions[key] = {
            "direction": direction,
            "entry_price": entry_price,
            "sl": sl,
            "tp": tp,
            "qty": qty
        }
        logger.info(f"OPENED {key}: {'LONG' if direction == 1 else 'SHORT'} at {entry_price} (SL: {sl}, TP: {tp})")
        
    def process_tick(self, asset, current_price, signals):
        """
        Processes a tick for an asset. 
        1. Checks active positions for SL/TP hits.
        2. Applies new signals.
        """
        ts = datetime.utcnow().isoformat()
        
        for strat, signal_val in signals.items():
            key = f"{asset}_{strat}"
            
            # Check Risk Limits first
            if key in self.open_positions:
                pos = self.open_positions[key]
                direction = pos["direction"]
                
                # SL/TP hit logic
                hit_sl = (direction == 1 and current_price <= pos["sl"]) or (direction == -1 and current_price >= pos["sl"])
                hit_tp = (direction == 1 and current_price >= pos["tp"]) or (direction == -1 and current_price <= pos["tp"])
                
                if hit_sl:
                    self._close_position(key, pos["sl"], reason="Stop Loss", timestamp=ts)
                elif hit_tp:
                    self._close_position(key, pos["tp"], reason="Take Profit", timestamp=ts)

            # Signal Logic
            if signal_val != 0.0:
                target_dir = int(signal_val)
                
                if key in self.open_positions:
                    current_dir = self.open_positions[key]["direction"]
                    if current_dir != target_dir:
                        # Reversal
                        self._close_position(key, current_price, reason="Signal Reversal", timestamp=ts)
                        self._open_position(key, target_dir, current_price)
                else:
                    # New Entry
                    self._open_position(key, target_dir, current_price)
            else:
                # Flat signal
                if key in self.open_positions:
                    self._close_position(key, current_price, reason="Signal Flat", timestamp=ts)
                    
        self.save_state()
                    
    def get_metrics(self):
        total_trades = len(self.trade_ledger)
        if total_trades == 0:
            return {"win_rate": 0.0, "total_trades": 0, "avg_win": 0.0, "avg_loss": 0.0, "total_pnl": 0.0}
            
        winning_trades = [t for t in self.trade_ledger if t["pnl"] > 0]
        losing_trades = [t for t in self.trade_ledger if t["pnl"] <= 0]
        
        win_rate = len(winning_trades) / total_trades
        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0.0
        
        return {
            "win_rate": round(win_rate * 100, 2),
            "total_trades": total_trades,
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "total_pnl": round(self.total_pnl, 2),
            "equity": round(self.initial_capital + self.total_pnl, 2)
        }
        
    def get_unrealized_pnl(self, current_prices):
        unrealized = 0.0
        for key, pos in self.open_positions.items():
            asset = key.split("_")[0]
            if asset in current_prices:
                mult = self.multipliers.get(asset, 1000.0)
                points_gained = (current_prices[asset] - pos["entry_price"]) * pos["direction"]
                unrealized += points_gained * mult * pos["qty"]
        return round(unrealized, 2)

paper_broker = PaperBroker()
