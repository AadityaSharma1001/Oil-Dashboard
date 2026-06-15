import React from 'react';

const ZScoreGauge = ({ zScore = 0 }) => {
  // Clamp zScore between -3 and 3 for visual mapping
  const clamped = Math.max(-3, Math.min(3, zScore));
  
  // Map -3..3 to 0..100%
  const percentage = ((clamped + 3) / 6) * 100;
  
  const getColor = (z) => {
    if (z > 1.5) return 'text-red-500 shadow-red-500/50 border-red-500';
    if (z < -1.5) return 'text-emerald-500 shadow-emerald-500/50 border-emerald-500';
    return 'text-blue-500 shadow-blue-500/50 border-blue-500';
  };

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm h-full flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background glow based on Z-score */}
      <div className={`absolute w-32 h-32 rounded-full blur-3xl opacity-10 transition-all duration-1000 bg-current ${getColor(zScore).split(' ')[0]}`}></div>
      
      <h2 className="text-sm font-semibold text-slate-500 mb-6 w-full text-center uppercase tracking-wider">
        WTI-Brent Arb Z-Score
      </h2>
      
      <div className="relative w-48 h-24 mb-4">
        {/* Semi-circle track */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="w-full h-[200%] border-[16px] border-slate-100 rounded-full"></div>
        </div>
        
        {/* Semi-circle fill */}
        <div className="absolute inset-0 overflow-hidden">
          <div 
            className={`w-full h-[200%] border-[16px] rounded-full border-t-transparent border-l-transparent transition-all duration-1000 ease-out`}
            style={{ 
              transform: `rotate(${percentage * 1.8 - 45}deg)`,
              borderColor: zScore > 1.5 ? '#ef4444' : zScore < -1.5 ? '#10b981' : '#3b82f6',
              borderBottomColor: 'transparent',
              borderLeftColor: 'transparent'
            }}
          ></div>
        </div>

        {/* Value Display */}
        <div className="absolute bottom-0 w-full text-center pb-2">
          <span className={`text-3xl font-bold font-mono tracking-tighter ${getColor(zScore).split(' ')[0]}`}>
            {zScore > 0 ? '+' : ''}{zScore.toFixed(2)}
          </span>
        </div>
      </div>
      
      <div className="flex justify-between w-full px-4 text-xs font-mono text-slate-400 mt-2">
        <span>-3.0</span>
        <span>0</span>
        <span>+3.0</span>
      </div>
    </div>
  );
};

export default ZScoreGauge;
