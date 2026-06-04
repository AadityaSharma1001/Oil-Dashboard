import React, { memo } from 'react';
import { useLiveTickers } from '../hooks/useLiveData';
import { INITIAL_TICKERS } from '../data/mockData';

const GlobalHeader = memo(function GlobalHeader() {
  const [tickers, flashMap] = useLiveTickers(INITIAL_TICKERS, 2000);

  return (
    <header className="sticky top-0 z-50 flex items-center h-[52px] px-5 bg-slate-900 text-white gap-4 border-b border-white/5">
      {/* Brand */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-blue-300 text-lg">◈</span>
        <span className="font-bold text-[13px] tracking-[1.5px] uppercase">QUANT OIL DESK</span>
        <span className="w-px h-5 bg-slate-700 mx-1" />
        <span className="text-[11px] text-slate-500 font-normal">Live Trading Analytics</span>
      </div>

      {/* Ticker Strip */}
      <div className="flex items-center gap-5 flex-1 overflow-x-auto scrollbar-hide px-3">
        {tickers.map(t => {
          const isUp = t.change >= 0;
          const flash = flashMap[t.id];
          return (
            <div key={t.id} className="flex items-center gap-1.5 shrink-0 text-xs whitespace-nowrap">
              <span className="text-slate-500 font-medium text-[10px] uppercase tracking-[0.5px]">{t.label}</span>
              <span
                className={`font-semibold tabular-nums transition-colors duration-500 ${flash === 'up' ? 'text-green-400' : flash === 'down' ? 'text-red-400' : 'text-white'
                  }`}
              >
                {t.price.toFixed(t.price > 100 ? 2 : t.price > 10 ? 2 : 3)}
              </span>
              <span
                className={`text-[10px] font-semibold px-1.5 py-px rounded tabular-nums transition-all duration-500 ${flash === 'up'
                    ? 'bg-green-500/30 text-green-300'
                    : flash === 'down'
                      ? 'bg-red-500/30 text-red-300'
                      : isUp
                        ? 'bg-green-500/15 text-green-400/80'
                        : 'bg-red-500/15 text-red-400/80'
                  }`}
              >
                {isUp ? '▲' : '▼'} {isUp ? '+' : ''}{t.change.toFixed(t.price > 100 ? 2 : t.price > 10 ? 2 : 3)} ({t.pct})
              </span>
            </div>
          );
        })}
      </div>

      {/* Alert */}
      <div className="flex items-center gap-1.5 shrink-0 px-2.5 py-1 rounded border border-amber-500/20 bg-amber-500/10">
        <span className="w-[7px] h-[7px] rounded-full bg-amber-400 animate-pulse" />
        <span className="text-[11px] text-amber-400 font-medium">1 threshold active</span>
      </div>
    </header>
  );
});

export default GlobalHeader;
