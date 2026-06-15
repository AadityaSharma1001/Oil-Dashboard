import React from 'react';

const TradeHistory = ({ trades = [] }) => {
  if (!trades || trades.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-400 py-10">
        <svg className="w-12 h-12 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
        <p>No trades executed yet.</p>
      </div>
    );
  }

  return (
    <table className="w-full text-sm text-left relative">
      <thead className="text-xs text-slate-500 uppercase bg-slate-100/90 sticky top-0 backdrop-blur-sm z-10 border-b border-slate-200">
        <tr>
          <th className="px-4 py-3 rounded-tl-lg">Time</th>
          <th className="px-4 py-3">Asset</th>
          <th className="px-4 py-3">Dir</th>
          <th className="px-4 py-3">Entry</th>
          <th className="px-4 py-3">Exit</th>
          <th className="px-4 py-3 text-right">PnL</th>
          <th className="px-4 py-3 rounded-tr-lg">Reason</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {[...trades].reverse().map((trade, idx) => {
          const isWin = trade.pnl > 0;
          const isLoss = trade.pnl < 0;
          const pnlColor = isWin ? 'text-emerald-600' : isLoss ? 'text-red-600' : 'text-slate-500';
          const dirColor = trade.direction === 'LONG' ? 'text-emerald-700 bg-emerald-100' : 'text-red-700 bg-red-100';
          
          const time = new Date(trade.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

          return (
            <tr key={trade.id || idx} className="hover:bg-slate-50 transition-colors group">
              <td className="px-4 py-3 text-xs text-slate-500 font-mono">{time}</td>
              <td className="px-4 py-3 font-medium text-slate-800">{trade.asset_strat}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${dirColor}`}>
                  {trade.direction}
                </span>
              </td>
              <td className="px-4 py-3 text-slate-600 font-mono">{trade.entry_price?.toFixed(2)}</td>
              <td className="px-4 py-3 text-slate-600 font-mono">{trade.exit_price?.toFixed(2)}</td>
              <td className={`px-4 py-3 text-right font-mono font-bold ${pnlColor}`}>
                {isWin ? '+' : ''}{trade.pnl?.toFixed(2)}
              </td>
              <td className="px-4 py-3 text-xs text-slate-500">{trade.reason}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default TradeHistory;
