import React from 'react';

const RegimeMonitor = ({ regimes = {}, prices = {} }) => {
  const assets = ["WTI", "BRENT", "HO", "GO"];
  
  const getRegimeColor = (state) => {
    switch(state) {
      case 0: return 'bg-slate-50 text-slate-700 border-slate-200'; // Flat
      case 1: return 'bg-red-50 text-red-700 border-red-200'; // Contango
      case 2: return 'bg-emerald-50 text-emerald-700 border-emerald-200'; // Backwardation
      default: return 'bg-slate-100 text-slate-500 border-slate-200'; // Unknown
    }
  };

  const getRegimeLabel = (state) => {
    switch(state) {
      case 0: return 'State 0 (Flat)';
      case 1: return 'State 1 (Contango)';
      case 2: return 'State 2 (Backwardation)';
      default: return 'Awaiting Data';
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm h-full">
      <h2 className="text-lg font-semibold mb-4 text-slate-800 flex items-center gap-2">
        <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path></svg>
        HMM Gatekeeper
      </h2>
      <div className="space-y-3">
        {assets.map(asset => {
          const state = regimes[asset] !== undefined ? regimes[asset] : -1;
          const price = prices[asset] ? prices[asset].toFixed(2) : '---';
          
          return (
            <div key={asset} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div>
                <div className="font-bold text-slate-800">{asset}</div>
                <div className="text-xs text-slate-500 font-mono">${price}</div>
              </div>
              <div className={`px-3 py-1.5 rounded-lg border text-sm font-medium ${getRegimeColor(state)}`}>
                {getRegimeLabel(state)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RegimeMonitor;
