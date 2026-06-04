import React, { memo } from 'react';
import Card from './Card';
import { TRADE_SIGNALS } from '../data/mockData';

const directionConfig = {
  BUY:  { bg: 'bg-green-50', border: 'border-green-200', badge: 'bg-green-600', text: 'text-green-700', barColor: '#16a34a' },
  SELL: { bg: 'bg-red-50',   border: 'border-red-200',   badge: 'bg-red-600',   text: 'text-red-700',   barColor: '#dc2626' },
  HOLD: { bg: 'bg-slate-50', border: 'border-slate-200', badge: 'bg-slate-500',  text: 'text-slate-600', barColor: '#64748b' },
};

const SignalCard = memo(({ signal }) => {
  const cfg = directionConfig[signal.direction] || directionConfig.HOLD;
  return (
    <div className={`${cfg.bg} ${cfg.border} border rounded-lg p-3 transition-all hover:shadow-md`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold text-slate-700 leading-tight">{signal.name}</span>
        <span className={`${cfg.badge} text-white text-[9px] font-bold px-2 py-0.5 rounded tracking-wide`}>
          {signal.direction}
        </span>
      </div>
      {/* Confidence bar */}
      <div className="flex items-center gap-2 mb-2">
        <div className="flex-1 h-1.5 bg-slate-200/60 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${signal.confidence}%`, background: cfg.barColor }}
          />
        </div>
        <span className={`text-[10px] font-bold tabular-nums ${cfg.text}`}>{signal.confidence}%</span>
      </div>
      <p className="text-[10px] text-slate-500 leading-relaxed">{signal.rationale}</p>
    </div>
  );
});

const TradeSignals = memo(function TradeSignals() {
  const buyCount = TRADE_SIGNALS.filter(s => s.direction === 'BUY').length;
  const sellCount = TRADE_SIGNALS.filter(s => s.direction === 'SELL').length;
  const holdCount = TRADE_SIGNALS.filter(s => s.direction === 'HOLD').length;

  return (
    <Card
      title="Trade Signals"
      badge={
        <span className="flex items-center gap-2">
          <span className="text-green-600 font-semibold">{buyCount} BUY</span>
          <span className="text-slate-300">·</span>
          <span className="text-red-600 font-semibold">{sellCount} SELL</span>
          <span className="text-slate-300">·</span>
          <span className="text-slate-500 font-semibold">{holdCount} HOLD</span>
        </span>
      }
    >
      <div className="grid grid-cols-1 gap-2.5 max-h-[420px] overflow-y-auto pr-1">
        {TRADE_SIGNALS.map(s => <SignalCard key={s.id} signal={s} />)}
      </div>
    </Card>
  );
});

export default TradeSignals;
