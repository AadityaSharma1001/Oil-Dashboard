import React from 'react';

const PerformanceMetrics = ({ metrics = {} }) => {
  const { win_rate = 0, total_trades = 0, avg_win = 0, avg_loss = 0, total_pnl = 0, unrealized_pnl = 0, equity = 100000 } = metrics;

  const StatBox = ({ label, value, prefix = '', suffix = '', colorClass = 'text-slate-900' }) => (
    <div className="flex flex-col p-4 rounded-xl bg-slate-50 border border-slate-200 hover:bg-slate-100 transition-colors">
      <span className="text-sm text-slate-500 font-medium mb-1">{label}</span>
      <span className={`text-2xl font-bold tracking-tight font-mono ${colorClass}`}>
        {prefix}{value}{suffix}
      </span>
    </div>
  );

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm h-full flex flex-col justify-center">
      <h2 className="text-lg font-semibold mb-4 text-slate-800 flex items-center gap-2">
        <svg className="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
        Performance Metrics
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <StatBox 
          label="Total Equity" 
          value={equity.toLocaleString()} 
          prefix="$" 
          colorClass="text-indigo-600" 
        />
        <StatBox 
          label="Total PnL" 
          value={total_pnl.toLocaleString()} 
          prefix="$" 
          colorClass={total_pnl >= 0 ? 'text-emerald-600' : 'text-red-600'} 
        />
        <StatBox 
          label="Unrealized" 
          value={unrealized_pnl.toLocaleString()} 
          prefix="$" 
          colorClass={unrealized_pnl >= 0 ? 'text-blue-600' : 'text-red-600'} 
        />
        <StatBox 
          label="Win Rate" 
          value={win_rate.toFixed(1)} 
          suffix="%" 
          colorClass={win_rate >= 50 ? 'text-emerald-600' : 'text-amber-600'} 
        />
        <StatBox 
          label="Total Trades" 
          value={total_trades} 
          colorClass="text-slate-800" 
        />
        <StatBox 
          label="Avg Win" 
          value={avg_win.toLocaleString()} 
          prefix="$" 
          colorClass="text-emerald-600" 
        />
        <StatBox 
          label="Avg Loss" 
          value={Math.abs(avg_loss).toLocaleString()} 
          prefix="-$" 
          colorClass="text-red-600" 
        />
      </div>
    </div>
  );
};

export default PerformanceMetrics;
