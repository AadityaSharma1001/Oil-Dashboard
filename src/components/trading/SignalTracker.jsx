import React from 'react';

const SignalTracker = ({ signals = {}, positions = {} }) => {
  const assets = ["WTI", "BRENT", "HO", "GO"];
  const strategies = ["Outright", "Spread", "Fly"];

  const getSignalColor = (val) => {
    if (val === 1.0) return 'text-emerald-700 bg-emerald-100 border-emerald-200';
    if (val === -1.0) return 'text-red-700 bg-red-100 border-red-200';
    return 'text-slate-500 bg-slate-100 border-slate-200';
  };

  const getSignalText = (val) => {
    if (val === 1.0) return 'LONG';
    if (val === -1.0) return 'SHORT';
    return 'FLAT';
  };

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm h-full flex flex-col">
      <h2 className="text-lg font-semibold mb-4 text-slate-800 flex items-center gap-2">
        <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
        Model Signals & Open Positions
      </h2>
      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 rounded-tl-lg">Asset</th>
              {strategies.map(s => <th key={s} className="px-4 py-3">{s}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {assets.map(asset => (
              <tr key={asset} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-medium text-slate-800">{asset}</td>
                {strategies.map(strat => {
                  const key = `${asset}_${strat}`;
                  const sig = signals[key] !== undefined ? signals[key] : 0;
                  const pos = positions[key];
                  const hasPos = !!pos;
                  
                  return (
                    <td key={strat} className="px-4 py-3">
                      <div className="flex flex-col gap-1">
                        <div className={`inline-flex items-center justify-center px-2 py-1 rounded border text-xs font-bold ${getSignalColor(sig)}`}>
                          {getSignalText(sig)}
                        </div>
                        {hasPos && (
                          <div className="text-[10px] text-slate-500 font-mono">
                            Entry: {pos.entry_price.toFixed(2)}<br/>
                            SL/TP: {pos.sl.toFixed(2)} / {pos.tp.toFixed(2)}
                          </div>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SignalTracker;
