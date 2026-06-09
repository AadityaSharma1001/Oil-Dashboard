import React, { memo } from 'react';
import { useApiTickers } from '../hooks/useApiData';
import { INITIAL_TICKERS } from '../data/mockData';

const GlobalHeader = memo(function GlobalHeader() {
  const [tickers, flashMap, source] = useApiTickers(INITIAL_TICKERS, 15000);

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
          const price = t.price ?? 0;
          const change = t.change ?? 0;
          const isUp = change >= 0;
          const flash = flashMap[t.id];
          return (
            <div key={t.id} className="flex items-center gap-1.5 shrink-0 text-xs whitespace-nowrap">
              <span className="text-slate-500 font-medium text-[10px] uppercase tracking-[0.5px]">{t.label}</span>
              <span
                className={`font-semibold tabular-nums transition-colors duration-500 ${flash === 'up' ? 'text-green-400' : flash === 'down' ? 'text-red-400' : 'text-white'
                  }`}
              >
                {price.toFixed(price > 100 ? 2 : price > 10 ? 2 : 3)}
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
                {isUp ? '▲' : '▼'} {isUp ? '+' : ''}{change.toFixed(price > 100 ? 2 : price > 10 ? 2 : 3)} ({t.pct ?? '0.00%'})
              </span>
            </div>
          );
        })}
      </div>

      {/* Data Source Indicator */}
      <div className={`flex items-center gap-1.5 shrink-0 px-2.5 py-1 rounded border ${
        source === 'live'
          ? 'border-emerald-500/20 bg-emerald-500/10'
          : source === 'loading'
            ? 'border-blue-500/20 bg-blue-500/10'
            : 'border-amber-500/20 bg-amber-500/10'
      }`}>
        <span className={`w-[7px] h-[7px] rounded-full animate-pulse ${
          source === 'live' ? 'bg-emerald-400' : source === 'loading' ? 'bg-blue-400' : 'bg-amber-400'
        }`} />
        <span className={`text-[11px] font-medium ${
          source === 'live' ? 'text-emerald-400' : source === 'loading' ? 'text-blue-400' : 'text-amber-400'
        }`}>
          {source === 'live' ? 'LIVE' : source === 'loading' ? 'CONNECTING' : 'MOCK DATA'}
        </span>
      </div>
    </header>
  );
});

export default GlobalHeader;
