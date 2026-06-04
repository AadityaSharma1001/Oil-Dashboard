import React, { memo, useState, useEffect, useCallback, useMemo } from 'react';
import {
  ComposedChart, Line, Area,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import Card from './Card';

/* ── Generate realistic intraday session data ────────────────── */
function generateSession(basePrice, volatility, seed) {
  const minutes = 390; // 6.5hr session
  const data = [];
  let price = basePrice;
  let cumPV = 0;   // cumulative price * volume
  let cumVol = 0;  // cumulative volume
  let r = seed;

  // Simple seeded pseudo-random
  const rand = () => { r = (r * 16807 + 0) % 2147483647; return r / 2147483647; };

  for (let i = 0; i < minutes; i++) {
    // Simulate volume (higher at open/close)
    const distFromEdge = Math.min(i, minutes - 1 - i);
    const volumeBase = 800 + (distFromEdge < 30 ? (30 - distFromEdge) * 40 : 0);
    const volume = Math.round(volumeBase * (0.6 + rand() * 0.8));

    // Random walk with mean reversion
    const drift = (basePrice - price) * 0.002;
    const shock = (rand() - 0.5) * volatility;
    // Add occasional trending moves
    const trend = i > 120 && i < 200 ? 0.003 : i > 280 && i < 340 ? -0.002 : 0;
    price = price + drift + shock + trend;

    cumPV += price * volume;
    cumVol += volume;
    const vwap = cumPV / cumVol;

    // Calculate running std dev from VWAP
    // Approximate using exponential moving variance
    data.push({ min: i, price: +price.toFixed(3), vwap: +vwap.toFixed(3), volume });

    // We'll calculate bands after
  }

  // Now calculate bands with proper running std dev
  let sumSqDev = 0;
  for (let i = 0; i < data.length; i++) {
    const dev = data[i].price - data[i].vwap;
    sumSqDev += dev * dev;
    const stdDev = Math.sqrt(sumSqDev / (i + 1));
    data[i].upperBand = +(data[i].vwap + 2 * stdDev).toFixed(3);
    data[i].lowerBand = +(data[i].vwap - 2 * stdDev).toFixed(3);
    data[i].bandWidth = +(4 * stdDev).toFixed(3);
    data[i].deviation = stdDev > 0 ? +((data[i].price - data[i].vwap) / stdDev).toFixed(2) : 0;
    // Format time label
    const hours = Math.floor(i / 60) + 9; // 9:00 AM start
    const mins = i % 60;
    data[i].time = `${hours}:${mins.toString().padStart(2, '0')}`;
  }

  return data;
}

const AXIS_STYLE = { fontSize: 9, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.04)' };

/* ── Custom Tooltip ──────────────────────────────────────────── */
const VWAPTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div className="bg-slate-900 text-white text-[10px] px-2.5 py-2 rounded-md shadow-lg min-w-[140px]">
      <div className="font-semibold text-slate-300 mb-1 border-b border-slate-700 pb-1">{d.time}</div>
      <div className="space-y-0.5">
        <div className="flex justify-between gap-3"><span className="text-slate-400">Price</span><span className="font-semibold tabular-nums">${d.price.toFixed(2)}</span></div>
        <div className="flex justify-between gap-3"><span className="text-slate-400">VWAP</span><span className="font-semibold tabular-nums">${d.vwap.toFixed(2)}</span></div>
        <div className="flex justify-between gap-3"><span className="text-slate-400">Upper BB</span><span className="font-semibold tabular-nums text-blue-300">${d.upperBand.toFixed(2)}</span></div>
        <div className="flex justify-between gap-3"><span className="text-slate-400">Lower BB</span><span className="font-semibold tabular-nums text-blue-300">${d.lowerBand.toFixed(2)}</span></div>
        <div className="flex justify-between gap-3"><span className="text-slate-400">σ Dev</span><span className={`font-semibold tabular-nums ${d.deviation > 0 ? 'text-green-400' : 'text-red-400'}`}>{d.deviation > 0 ? '+' : ''}{d.deviation}σ</span></div>
      </div>
    </div>
  );
};

/* ── Metric Pill ─────────────────────────────────────────────── */
const Metric = ({ label, value, unit, color }) => (
  <div className="flex flex-col items-center px-4 py-1.5">
    <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-[0.5px]">{label}</span>
    <span className={`text-sm font-bold tabular-nums ${color || 'text-slate-800'}`}>{value}<span className="text-[10px] font-medium text-slate-400 ml-0.5">{unit}</span></span>
  </div>
);

/* ── Single VWAP Chart ───────────────────────────────────────── */
const VWAPChart = memo(({ title, basePrice, volatility, seed, accentColor }) => {
  const initialData = useMemo(() => generateSession(basePrice, volatility, seed), [basePrice, volatility, seed]);
  const [data, setData] = useState(initialData);
  const [visibleBars, setVisibleBars] = useState(initialData.length);

  // Simulate live tick updates
  useEffect(() => {
    const interval = setInterval(() => {
      setData(prev => {
        const newData = [...prev];
        const last = newData[newData.length - 1];
        const shock = (Math.random() - 0.5) * volatility * 0.4;
        const newPrice = +(last.price + shock).toFixed(3);

        // Recalculate VWAP for the last point
        const newVol = last.volume + Math.round(Math.random() * 200);
        // Just update the last bar's price for the live feel
        const updatedLast = { ...last, price: newPrice };

        // Recalculate deviation
        const dev = updatedLast.price - updatedLast.vwap;
        const bw = updatedLast.upperBand - updatedLast.lowerBand;
        const stdDev = bw / 4;
        updatedLast.deviation = stdDev > 0 ? +((dev) / stdDev).toFixed(2) : 0;

        newData[newData.length - 1] = updatedLast;
        return newData;
      });
    }, 1500);
    return () => clearInterval(interval);
  }, [volatility]);

  const lastBar = data[data.length - 1];
  const devColor = lastBar.deviation > 1 ? 'text-green-600' : lastBar.deviation < -1 ? 'text-red-600' : 'text-slate-700';

  return (
    <Card
      title={title}
      badge="VWAP + 2σ Bollinger"
      footer={
        <div className="flex items-center justify-center divide-x divide-slate-200 -mx-3.5 -mb-3.5 bg-slate-50 border-t border-slate-100">
          <Metric label="VWAP" value={lastBar.vwap.toFixed(2)} unit="$/bbl" />
          <Metric label="Band Width" value={lastBar.bandWidth.toFixed(2)} unit="$/bbl" />
          <Metric label="Price-VWAP" value={`${lastBar.deviation > 0 ? '+' : ''}${lastBar.deviation}σ`} unit="" color={devColor} />
        </div>
      }
    >
      <div className="h-[280px]" style={{ minHeight: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={`bbGrad-${seed}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={accentColor} stopOpacity={0.06} />
                <stop offset="50%" stopColor={accentColor} stopOpacity={0.02} />
                <stop offset="100%" stopColor={accentColor} stopOpacity={0.06} />
              </linearGradient>
            </defs>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="time" tick={AXIS_STYLE} interval={59} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(1)}`} domain={['auto', 'auto']} width={52} />
            <Tooltip content={<VWAPTooltip />} />

            {/* Bollinger Band fill between upper and lower */}
            <Area dataKey="upperBand" stroke="none" fill={`url(#bbGrad-${seed})`} fillOpacity={1} dot={false} activeDot={false} name="__upper" legendType="none" />
            <Area dataKey="lowerBand" stroke="none" fill="#FFFFFF" fillOpacity={1} dot={false} activeDot={false} name="__lower" legendType="none" />

            {/* Bollinger Band lines */}
            <Line dataKey="upperBand" name="Upper BB (+2σ)" stroke={accentColor} strokeWidth={1} strokeDasharray="4 3" dot={false} activeDot={false} />
            <Line dataKey="lowerBand" name="Lower BB (−2σ)" stroke={accentColor} strokeWidth={1} strokeDasharray="4 3" dot={false} activeDot={false} />

            {/* VWAP line */}
            <Line dataKey="vwap" name="VWAP" stroke="#868E96" strokeWidth={1.5} dot={false} activeDot={false} />

            {/* Price line */}
            <Line dataKey="price" name="Price" stroke={accentColor === '#0D47A1' ? '#0D47A1' : '#343A40'} strokeWidth={1.8} dot={false} activeDot={{ r: 3, strokeWidth: 0 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ── Main Export ──────────────────────────────────────────────── */
const IntradayVWAP = memo(function IntradayVWAP() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
      <VWAPChart
        title="WTI M1 — Intraday VWAP"
        basePrice={72.45}
        volatility={0.08}
        seed={42}
        accentColor="#0D47A1"
      />
      <VWAPChart
        title="Brent M1 — Intraday VWAP"
        basePrice={76.30}
        volatility={0.07}
        seed={137}
        accentColor="#343A40"
      />
    </div>
  );
});

export default IntradayVWAP;
