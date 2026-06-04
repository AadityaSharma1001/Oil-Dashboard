import React, { memo } from 'react';
import {
  LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import Card from './Card';
import { useLiveMultiChartData, useLiveChartData } from '../hooks/useLiveData';
import {
  FLAT_PRICE_DATA, BW_SPREAD_DATA, BW_HIST_MEAN, TERM_SPREAD_DATA,
} from '../data/mockData';

const AXIS_STYLE = { fontSize: 10, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.04)' };

const CustomTooltip = ({ active, payload, label, prefix = '$' }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-[11px] px-2.5 py-1.5 rounded-md shadow-lg">
      <div className="font-semibold text-slate-300 mb-0.5">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-400">{p.name}:</span>
          <span className="font-semibold tabular-nums">{prefix}{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

/* ── Flat Price Trend ────────────────────────────────────────── */
const FlatPriceTrend = memo(() => {
  const data = useLiveMultiChartData(FLAT_PRICE_DATA, ['wti', 'brent'], 3000, 0.0003);
  return (
    <Card title="Flat Price Trend" badge="30-Day WTI vs Brent">
      <div className="h-[260px]" style={{ minHeight: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="day" tick={AXIS_STYLE} interval={5} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v}`} domain={['auto', 'auto']} />
            <Tooltip content={<CustomTooltip />} />
            <Legend iconType="plainline" iconSize={14} wrapperStyle={{ fontSize: 11 }} />
            <Line name="WTI" dataKey="wti" stroke="#0D47A1" strokeWidth={2} dot={false} />
            <Line name="Brent" dataKey="brent" stroke="#343A40" strokeWidth={2} strokeDasharray="6 3" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ── Brent-WTI Spread ────────────────────────────────────────── */
const BrentWTISpread = memo(() => {
  const data = useLiveChartData(BW_SPREAD_DATA, 'spread', 3000, 0.002);
  return (
    <Card title="Brent-WTI Spread" badge="vs Historical Mean">
      <div className="h-[260px]" style={{ minHeight: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="bwGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0D47A1" stopOpacity={0.12} />
                <stop offset="100%" stopColor="#0D47A1" stopOpacity={0.01} />
              </linearGradient>
            </defs>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="day" tick={AXIS_STYLE} interval={5} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(2)}`} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={BW_HIST_MEAN} stroke="#ADB5BD" strokeDasharray="6 3" strokeWidth={1.5} label={{ value: 'Hist Mean', position: 'insideTopLeft', fill: '#868E96', fontSize: 10 }} />
            <Area dataKey="spread" name="Spread" stroke="#0D47A1" fill="url(#bwGrad)" strokeWidth={1.5} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ── Term Spreads ────────────────────────────────────────────── */
const TermSpreads = memo(() => {
  const data = useLiveMultiChartData(TERM_SPREAD_DATA, ['brentM1M2', 'wtiM1M12'], 3000, 0.003);
  return (
    <Card title="Term Spreads" badge="Brent M1-M2 vs WTI M1-M12">
      <div className="h-[260px]" style={{ minHeight: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="day" tick={AXIS_STYLE} interval={5} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(2)}`} />
            <Tooltip content={<CustomTooltip />} />
            <Legend iconType="plainline" iconSize={14} wrapperStyle={{ fontSize: 11 }} />
            <Line name="Brent M1-M2" dataKey="brentM1M2" stroke="#0D47A1" strokeWidth={1.5} dot={false} />
            <Line name="WTI M1-M12" dataKey="wtiM1M12" stroke="#E53935" strokeWidth={1.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ═══════════════════════ Main Layout ═════════════════════════ */
const PriceSpreads = memo(function PriceSpreads() {
  return (
    <div className="space-y-3.5 animate-fadeIn">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <FlatPriceTrend />
        <BrentWTISpread />
      </div>
      <div className="grid grid-cols-1 gap-3.5">
        <TermSpreads />
      </div>
    </div>
  );
});

export default PriceSpreads;
