import React, { useState, useEffect } from 'react';
import RegimeMonitor from './RegimeMonitor';
import SignalTracker from './SignalTracker';
import ZScoreGauge from './ZScoreGauge';
import PnLEquityCurve from './PnLEquityCurve';
import PerformanceMetrics from './PerformanceMetrics';
import TradeHistory from './TradeHistory';
import OpenPositions from './OpenPositions';

const TradingDashboard = () => {
  const [data, setData] = useState({
    hmm_regimes: {},
    active_signals: {},
    positions: {},
    z_score: 0.0,
    metrics: { win_rate: 0, total_trades: 0, avg_win: 0, avg_loss: 0, total_pnl: 0, unrealized_pnl: 0 },
    trade_ledger: [],
    prices: {},
    _tick: 0
  });

  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Connect to the trading websocket room
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws/trading';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    
    ws.onmessage = (event) => {
      try {
        if (event.data === 'pong') return;
        const payload = JSON.parse(event.data);
        if (payload.type === 'trading_update') {
          setData(prev => ({ ...prev, ...payload, _tick: prev._tick + 1 }));
        }
      } catch (err) {
        console.error("WS parse error", err);
      }
    };

    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 10000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, []);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 text-slate-900 p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <header className="flex justify-between items-center pb-4 border-b border-slate-200">
          <div>
            <h1 className="text-3xl font-bold text-slate-800">
              Quantitative Execution Engine
            </h1>
            <p className="text-slate-500 text-sm mt-1">Multi-Strategy RV ML Portfolio</p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-slate-500">Status Engine:</span>
            <div className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-2 ${connected ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
              {connected ? 'LIVE' : 'DISCONNECTED'}
            </div>
          </div>
        </header>

        {/* Top Row: Metrics & Z-Score */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            <PerformanceMetrics metrics={data.metrics} />
          </div>
          <div className="lg:col-span-1">
            <ZScoreGauge zScore={data.z_score} />
          </div>
        </div>

        {/* Middle Row: Regimes & Signals */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <RegimeMonitor regimes={data.hmm_regimes} prices={data.prices} />
          </div>
          <div className="lg:col-span-2">
            <SignalTracker signals={data.active_signals} positions={data.positions} />
          </div>
        </div>

        {/* Middle Row 2: Open Positions */}
        <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 overflow-hidden mb-6">
          <h2 className="text-lg font-semibold mb-4 text-slate-800">Active Open Positions</h2>
          <div className="overflow-auto max-h-[300px]">
            <OpenPositions positions={data.positions} prices={data.prices} />
          </div>
        </div>

        {/* Bottom Row: PnL Curve & Trade History */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200">
            <h2 className="text-lg font-semibold mb-4 text-slate-800">Paper Equity Curve</h2>
            <div className="h-[300px]">
              <PnLEquityCurve data={data.trade_ledger} currentUnrealized={data.metrics.unrealized_pnl} />
            </div>
          </div>
          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 overflow-hidden flex flex-col h-[380px]">
            <h2 className="text-lg font-semibold mb-4 text-slate-800 shrink-0">Recent Trades (Ledger)</h2>
            <div className="flex-1 overflow-y-auto min-h-0">
              <TradeHistory trades={data.trade_ledger} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingDashboard;
