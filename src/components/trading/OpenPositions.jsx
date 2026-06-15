import React from 'react';

const OpenPositions = ({ positions = {}, prices = {} }) => {
  const positionKeys = Object.keys(positions);

  if (positionKeys.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-400 py-10">
        <svg className="w-12 h-12 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
        <p>No active positions.</p>
      </div>
    );
  }

  const multipliers = {
    "WTI": 1000,
    "BRENT": 1000,
    "HO": 1000,
    "GO": 1000
  };

  return (
    <table className="w-full text-sm text-left relative">
      <thead className="text-xs text-slate-500 uppercase bg-slate-100/90 sticky top-0 backdrop-blur-sm z-10 border-b border-slate-200">
        <tr>
          <th className="px-4 py-3 rounded-tl-lg">Strategy</th>
          <th className="px-4 py-3">Dir</th>
          <th className="px-4 py-3">Entry</th>
          <th className="px-4 py-3">Current</th>
          <th className="px-4 py-3">Stop Loss</th>
          <th className="px-4 py-3">Take Profit</th>
          <th className="px-4 py-3 text-right rounded-tr-lg">Unrl PnL</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {positionKeys.map((key) => {
          const pos = positions[key];
          const asset = key.split('_')[0];
          const currentPrice = prices[asset] || pos.entry_price;
          
          const isLong = pos.direction === 1;
          const dirColor = isLong ? 'text-emerald-700 bg-emerald-100' : 'text-red-700 bg-red-100';
          const dirText = isLong ? 'LONG' : 'SHORT';

          const pointsGained = (currentPrice - pos.entry_price) * pos.direction;
          const mult = multipliers[asset] || 1000;
          const unrealizedPnl = pointsGained * mult * pos.qty;

          const pnlColor = unrealizedPnl > 0 ? 'text-emerald-600' : unrealizedPnl < 0 ? 'text-red-600' : 'text-slate-500';

          return (
            <tr key={key} className="hover:bg-slate-50 transition-colors group">
              <td className="px-4 py-3 font-medium text-slate-800">{key}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${dirColor}`}>
                  {dirText}
                </span>
              </td>
              <td className="px-4 py-3 text-slate-600 font-mono">{pos.entry_price?.toFixed(2)}</td>
              <td className="px-4 py-3 text-slate-600 font-mono font-bold">{currentPrice?.toFixed(2)}</td>
              <td className="px-4 py-3 font-mono text-slate-500">{pos.sl?.toFixed(2)}</td>
              <td className="px-4 py-3 text-slate-500 font-mono">{pos.tp?.toFixed(2)}</td>
              <td className={`px-4 py-3 text-right font-mono font-bold ${pnlColor}`}>
                {unrealizedPnl > 0 ? '+' : ''}{unrealizedPnl?.toFixed(2)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default OpenPositions;
