import React, { memo, useState, useMemo } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, ReferenceArea,
} from 'recharts';
import Card from './Card';
import { useLiveChartData, useLiveMultiChartData } from '../hooks/useLiveData';
import {
  FWD_CURVE_DATA, BRENT_FWD_CURVE_DATA,
  M1M12_DATA, M1M12_THRESHOLD,
  COV_LABELS, COV_VALUES, COV_HIGHLIGHT,
  HEATMAP_M1M12_LABELS, HEATMAP_M1M12_VALUES, BRENT_HEATMAP_M1M12_VALUES,
  PCA_DATA, BRENT_PCA_DATA, ARB_DATA, ARB_MEAN, ARB_STD,
  DIFF_DATA, CRACK_DATA,
  CUSHING_UTIL, CUSHING_DATA, FLOATING_DATA, MACRO_TABLE,
  FUNDAMENTALS_CARDS,
} from '../data/mockData';
import DollarCorrelation from './DollarCorrelation';

/* ── Shared chart config ─────────────────────────────────────── */
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

/* ── Gradient definitions reusable component ─────────────────── */
const ChartGradient = ({ id, color }) => (
  <defs>
    <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor={color} stopOpacity={0.15} />
      <stop offset="100%" stopColor={color} stopOpacity={0.01} />
    </linearGradient>
  </defs>
);

/* ═══════════════════════ Section Components ═══════════════════ */

const ForwardCurve = memo(() => {
  const data = useLiveChartData(FWD_CURVE_DATA, 'current', 3000, 0.0003);
  return (
    <Card title="WTI Forward Curve" badge="M1–M36 vs 5-Yr Avg">
      <div className="h-[220px]" style={{ minHeight: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <ChartGradient id="fwdGrad" color="#0D47A1" />
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="month" tick={AXIS_STYLE} interval={5} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v}`} domain={['auto', 'auto']} />
            <Tooltip content={<CustomTooltip />} />
            <Legend iconType="plainline" iconSize={14} wrapperStyle={{ fontSize: 11 }} />
            <Area name="Current" dataKey="current" stroke="#0D47A1" fill="url(#fwdGrad)" strokeWidth={2} dot={false} />
            <Line name="5-Yr Avg" dataKey="avg5yr" stroke="#ADB5BD" strokeWidth={1.5} strokeDasharray="6 3" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

const BrentForwardCurve = memo(() => {
  const data = useLiveChartData(BRENT_FWD_CURVE_DATA, 'current', 3000, 0.0003);
  return (
    <Card title="Brent Forward Curve" badge="M1–M36 vs 5-Yr Avg">
      <div className="h-[220px]" style={{ minHeight: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <ChartGradient id="brentFwdGrad" color="#343A40" />
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="month" tick={AXIS_STYLE} interval={5} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v}`} domain={['auto', 'auto']} />
            <Tooltip content={<CustomTooltip />} />
            <Legend iconType="plainline" iconSize={14} wrapperStyle={{ fontSize: 11 }} />
            <Area name="Current" dataKey="current" stroke="#343A40" fill="url(#brentFwdGrad)" strokeWidth={2} dot={false} />
            <Line name="5-Yr Avg" dataKey="avg5yr" stroke="#ADB5BD" strokeWidth={1.5} strokeDasharray="6 3" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

const NearSpreads = memo(() => {
  const data = useLiveMultiChartData(NEAR_SPREAD_DATA, ['m1m2', 'm1m3', 'brentM1M2', 'brentM1M3'], 3000, 0.003);
  return (
    <Card title="Near-Term Spreads" badge="WTI & Brent M1-M2 / M1-M3">
      <div className="h-[220px]" style={{ minHeight: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="day" tick={AXIS_STYLE} interval={9} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(2)}`} />
            <Tooltip content={<CustomTooltip />} />
            <Legend iconType="plainline" iconSize={14} wrapperStyle={{ fontSize: 10 }} />
            <Line name="WTI M1-M2" dataKey="m1m2" stroke="#0D47A1" strokeWidth={1.5} dot={false} />
            <Line name="WTI M1-M3" dataKey="m1m3" stroke="#90CAF9" strokeWidth={1.5} dot={false} />
            <Line name="Brent M1-M2" dataKey="brentM1M2" stroke="#343A40" strokeWidth={1.5} strokeDasharray="6 3" dot={false} />
            <Line name="Brent M1-M3" dataKey="brentM1M3" stroke="#ADB5BD" strokeWidth={1.5} strokeDasharray="6 3" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

const M1M12Spread = memo(() => {
  const data = useLiveMultiChartData(M1M12_DATA, ['wti', 'brent'], 3000, 0.002);
  return (
    <Card
      title="M1-M12 Spread"
      badge="WTI & Brent"
      badgeVariant="amber"
      footer={
        <div className="flex items-center gap-2 bg-amber-50 -mx-3.5 -mb-3.5 px-3.5 py-2.5 text-amber-700 text-[11px] font-medium">
          <span className="text-sm">⚠</span>
          <span>WTI spread approaching full carry threshold at –$4.80. Current: –$4.52</span>
        </div>
      }
    >
      <div className="h-[220px]" style={{ minHeight: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="day" tick={AXIS_STYLE} interval={5} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(2)}`} />
            <Tooltip content={<CustomTooltip />} />
            <Legend iconType="plainline" iconSize={14} wrapperStyle={{ fontSize: 11 }} />
            <ReferenceLine y={M1M12_THRESHOLD} stroke="#FFB300" strokeDasharray="6 3" strokeWidth={1.5} label={{ value: 'Full Carry', position: 'insideTopLeft', fill: '#E65100', fontSize: 10, fontWeight: 600 }} />
            <Line name="WTI M1-M12" dataKey="wti" stroke="#0D47A1" strokeWidth={1.5} dot={false} />
            <Line name="Brent M1-M12" dataKey="brent" stroke="#343A40" strokeWidth={1.5} strokeDasharray="6 3" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ── Covariance Matrix ───────────────────────────────────────── */
const CovMatrix = memo(() => {
  const [hoverCell, setHoverCell] = useState(null);

  return (
    <Card title="EWMA Covariance Matrix" badge="λ = 0.94 · 5-Leg">
      <div className="grid gap-0.5" style={{ gridTemplateColumns: `56px repeat(5, 1fr)` }}>
        <div />
        {COV_LABELS.map(l => (
          <div key={l} className={`flex items-center justify-center h-9 text-[10px] font-semibold uppercase tracking-[0.3px] transition-colors ${hoverCell?.c === COV_LABELS.indexOf(l) ? 'text-blue-900' : 'text-slate-500'}`}>{l}</div>
        ))}
        {COV_VALUES.map((row, r) => (
          <React.Fragment key={r}>
            <div className={`flex items-center justify-center h-9 text-[10px] font-semibold uppercase tracking-[0.3px] transition-colors ${hoverCell?.r === r ? 'text-blue-900' : 'text-slate-500'}`}>{COV_LABELS[r]}</div>
            {row.map((val, c) => {
              const isDiag = r === c;
              const isHL = COV_HIGHLIGHT.some(([hr, hc]) => hr === r && hc === c);
              const isHovered = hoverCell?.r === r && hoverCell?.c === c;
              const isRowCol = hoverCell && (hoverCell.r === r || hoverCell.c === c);
              return (
                <div
                  key={c}
                  onMouseEnter={() => setHoverCell({ r, c })}
                  onMouseLeave={() => setHoverCell(null)}
                  className={`flex items-center justify-center h-9 rounded text-[10.5px] font-medium tabular-nums cursor-default transition-all duration-150
                    ${isDiag ? 'bg-purple-50 text-purple-600 font-semibold' : ''}
                    ${isHL ? 'bg-red-50 text-red-700 font-bold border border-red-200' : ''}
                    ${!isDiag && !isHL ? 'bg-slate-50 text-slate-600' : ''}
                    ${isHovered ? 'scale-110 shadow-md z-10 ring-2 ring-blue-300' : ''}
                    ${isRowCol && !isHovered ? 'bg-blue-50/50' : ''}
                  `}
                >
                  {val.toFixed(2)}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </Card>
  );
});

/* ── M1-M12 Heatmap (WTI + Brent) ────────────────────────────── */
const M1M12Heatmap = memo(() => {
  const wtiMax = Math.max(...HEATMAP_M1M12_VALUES);
  const brentMax = Math.max(...BRENT_HEATMAP_M1M12_VALUES);
  return (
    <Card title="M1-M12 Heatmap" badge="WTI & Brent">
      <div className="flex flex-col gap-3">
        {/* WTI Row */}
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ background: 'rgba(0,150,136,0.35)' }} />
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px]">WTI</span>
          </div>
          <div className="flex gap-1">
            {HEATMAP_M1M12_VALUES.map((v, i) => (
              <div
                key={i}
                className="flex-1 h-8 rounded flex items-center justify-center text-[9.5px] font-medium hover:scale-110 transition-transform cursor-default"
                style={{ background: `rgba(0,150,136,${0.08 + (v / wtiMax) * 0.35})`, color: '#00695C' }}
                title={`${HEATMAP_M1M12_LABELS[i]}: $${v.toFixed(2)}`}
              >
                ${v.toFixed(2)}
              </div>
            ))}
          </div>
        </div>
        {/* Brent Row */}
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ background: 'rgba(13,71,161,0.35)' }} />
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px]">Brent</span>
          </div>
          <div className="flex gap-1">
            {BRENT_HEATMAP_M1M12_VALUES.map((v, i) => (
              <div
                key={i}
                className="flex-1 h-8 rounded flex items-center justify-center text-[9.5px] font-medium hover:scale-110 transition-transform cursor-default"
                style={{ background: `rgba(13,71,161,${0.06 + (v / brentMax) * 0.28})`, color: '#0D47A1' }}
                title={`${HEATMAP_M1M12_LABELS[i]}: $${v.toFixed(2)}`}
              >
                ${v.toFixed(2)}
              </div>
            ))}
          </div>
        </div>
        {/* Labels */}
        <div className="flex gap-1">
          {HEATMAP_M1M12_LABELS.map(l => (
            <div key={l} className="flex-1 text-center text-[8px] text-slate-400">{l}</div>
          ))}
        </div>
      </div>
    </Card>
  );
});

/* ── PCA Decomposition (WTI + Brent) ─────────────────────────── */
const PCADecomposition = memo(() => (
  <Card title="PCA Decomposition" badge="WTI & Brent — 3 Components">
    <div className="grid grid-cols-2 gap-5">
      {/* WTI Column */}
      <div>
        <div className="flex items-center gap-1.5 mb-3">
          <span className="w-2.5 h-2.5 rounded-sm bg-blue-900" />
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px]">WTI</span>
        </div>
        <div className="flex flex-col gap-3.5">
          {PCA_DATA.map((pc, idx) => (
            <div key={idx}>
              <div className="flex justify-between items-baseline mb-1">
                <span className="text-[11px] font-semibold text-slate-600">{pc.label}</span>
                <span className="text-xs font-bold text-blue-900 tabular-nums">{pc.pct}%</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-1.5">
                <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pc.pct}%`, background: pc.color }} />
              </div>
              <div className="h-8" style={{ minHeight: 32 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={pc.spark.map((v, i) => ({ i, v }))}>
                    <defs>
                      <linearGradient id={`pcaG${idx}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={pc.color} stopOpacity={0.15} />
                        <stop offset="100%" stopColor={pc.color} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area dataKey="v" stroke={pc.color} fill={`url(#pcaG${idx})`} strokeWidth={1.5} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          ))}
        </div>
      </div>
      {/* Brent Column */}
      <div>
        <div className="flex items-center gap-1.5 mb-3">
          <span className="w-2.5 h-2.5 rounded-sm bg-slate-700" />
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px]">Brent</span>
        </div>
        <div className="flex flex-col gap-3.5">
          {BRENT_PCA_DATA.map((pc, idx) => (
            <div key={idx}>
              <div className="flex justify-between items-baseline mb-1">
                <span className="text-[11px] font-semibold text-slate-600">{pc.label}</span>
                <span className="text-xs font-bold text-slate-800 tabular-nums">{pc.pct}%</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-1.5">
                <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pc.pct}%`, background: pc.color }} />
              </div>
              <div className="h-8" style={{ minHeight: 32 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={pc.spark.map((v, i) => ({ i, v }))}>
                    <defs>
                      <linearGradient id={`bPcaG${idx}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={pc.color} stopOpacity={0.15} />
                        <stop offset="100%" stopColor={pc.color} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area dataKey="v" stroke={pc.color} fill={`url(#bPcaG${idx})`} strokeWidth={1.5} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </Card>
));

/* ── WTI-Brent Arb ───────────────────────────────────────────── */
const ArbChart = memo(() => {
  const data = useLiveChartData(ARB_DATA, 'spread', 3000, 0.002);
  return (
    <Card
      title="WTI-Brent Arb"
      badge="±1σ Z-Score Bands"
      footer={
        <table className="w-full text-[11.5px]">
          <thead><tr className="text-left text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px]"><th className="py-1 px-2">Metric</th><th className="py-1 px-2">Value</th><th className="py-1 px-2">Z</th></tr></thead>
          <tbody className="tabular-nums">
            <tr className="border-t border-slate-100"><td className="py-1 px-2">Current Spread</td><td className="py-1 px-2">–$3.85</td><td className="py-1 px-2 text-red-700 font-medium">–0.8σ</td></tr>
            <tr className="border-t border-slate-100"><td className="py-1 px-2">30d Mean</td><td className="py-1 px-2">–$3.20</td><td className="py-1 px-2 text-slate-400">—</td></tr>
            <tr className="border-t border-slate-100"><td className="py-1 px-2">30d Std</td><td className="py-1 px-2">$0.81</td><td className="py-1 px-2 text-slate-400">—</td></tr>
          </tbody>
        </table>
      }
    >
      <div className="h-[220px]">
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="day" tick={AXIS_STYLE} interval={5} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(2)}`} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={ARB_MEAN} stroke="#ADB5BD" strokeDasharray="3 3" />
            <ReferenceLine y={ARB_MEAN + ARB_STD} stroke="#DEE2E6" strokeDasharray="4 3" />
            <ReferenceLine y={ARB_MEAN - ARB_STD} stroke="#DEE2E6" strokeDasharray="4 3" />
            <Line name="Spread" dataKey="spread" stroke="#0D47A1" strokeWidth={1.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ── Differentials ───────────────────────────────────────────── */
const Differentials = memo(() => (
  <Card title="Physical Grade Differentials" badge="$/bbl vs WTI">
    <div className="h-[220px]">
      <ResponsiveContainer>
        <BarChart data={DIFF_DATA} layout="vertical">
          <CartesianGrid {...GRID_STYLE} />
          <XAxis type="number" tick={AXIS_STYLE} tickFormatter={v => `${v >= 0 ? '+' : ''}$${v}`} />
          <YAxis type="category" dataKey="grade" tick={{ fontSize: 10.5, fill: '#495057' }} width={80} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" radius={[0, 3, 3, 0]}>
            {DIFF_DATA.map((d, i) => (
              <React.Fragment key={i}>
              </React.Fragment>
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  </Card>
));

/* ── Crack Spreads (redesigned) ───────────────────────────────── */
const CrackTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  const diff = d.current - d.avg5yr;
  const pct = ((diff / d.avg5yr) * 100).toFixed(1);
  return (
    <div className="bg-slate-900 text-white text-[11px] px-3 py-2 rounded-lg shadow-xl min-w-[180px]">
      <div className="font-semibold text-slate-200 mb-1.5 pb-1 border-b border-slate-700">{label}</div>
      <div className="space-y-0.5">
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">Current</span>
          <span className="font-bold tabular-nums">${d.current.toFixed(1)}/bbl</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">5yr Avg</span>
          <span className="font-semibold tabular-nums text-slate-300">${d.avg5yr.toFixed(1)}/bbl</span>
        </div>
        <div className={`flex justify-between gap-4 border-t border-slate-700 pt-1 mt-1 ${diff >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          <span>Deviation</span>
          <span className="font-bold tabular-nums">{diff >= 0 ? '+' : ''}{diff.toFixed(1)} ({pct}%)</span>
        </div>
      </div>
    </div>
  );
};

const CrackSpreads = memo(() => {
  // Enrich data with deviation
  const enriched = CRACK_DATA.map(d => ({
    ...d,
    deviation: +(d.current - d.avg5yr).toFixed(1),
  }));

  return (
    <Card title="Major Crack Spreads" badge="Current vs 5-Yr Avg · $/bbl">
      <div className="h-[300px]" style={{ minHeight: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={enriched} layout="vertical" margin={{ top: 5, right: 60, left: 5, bottom: 5 }}>
            <CartesianGrid {...GRID_STYLE} horizontal={false} />
            <XAxis type="number" tick={AXIS_STYLE} tickFormatter={v => `$${v}`} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#495057', fontWeight: 500 }} width={110} />
            <Tooltip content={<CrackTooltip />} cursor={{ fill: 'rgba(0,0,0,0.02)' }} />
            <Legend iconType="square" iconSize={10} wrapperStyle={{ fontSize: 10, paddingTop: 8 }} />
            <Bar name="Current" dataKey="current" fill="#0D47A1" fillOpacity={0.75} radius={[0, 4, 4, 0]} barSize={14}
              label={({ x, y, width, height, value, index }) => {
                const d = enriched[index];
                const diff = d.deviation;
                const isUp = diff >= 0;
                return (
                  <text x={x + width + 5} y={y + height / 2 + 4} fontSize={10} fontWeight={600} fill={isUp ? '#16a34a' : '#dc2626'}>
                    {isUp ? '+' : ''}{diff.toFixed(1)}
                  </text>
                );
              }}
            />
            <Bar name="5-Yr Avg" dataKey="avg5yr" fill="#ADB5BD" fillOpacity={0.45} radius={[0, 4, 4, 0]} barSize={14} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ── Cushing Storage ─────────────────────────────────────────── */
const CushingStorage = memo(() => (
  <Card title="Cushing Storage" badge="53% Utilization">
    <div className="mb-3">
      <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px] mb-1">Capacity Utilization</div>
      <div className="h-5 bg-slate-100 rounded overflow-hidden">
        <div className="h-full rounded bg-gradient-to-r from-blue-500 to-blue-700 flex items-center justify-center transition-all duration-700" style={{ width: `${CUSHING_UTIL}%` }}>
          <span className="text-[10px] font-bold text-white">{CUSHING_UTIL}%</span>
        </div>
      </div>
    </div>
    <div className="h-[140px]" style={{ minHeight: 140 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={CUSHING_DATA}>
          <ChartGradient id="cushGrad" color="#0D47A1" />
          <CartesianGrid {...GRID_STYLE} />
          <XAxis dataKey="week" tick={AXIS_STYLE} />
          <YAxis tick={AXIS_STYLE} tickFormatter={v => `${v}mb`} />
          <Tooltip content={<CustomTooltip prefix="" />} />
          <Legend iconType="plainline" iconSize={14} wrapperStyle={{ fontSize: 10 }} />
          <Area dataKey="stock" name="Current" stroke="#0D47A1" fill="url(#cushGrad)" strokeWidth={1.5} dot={false} />
          <Line dataKey="avg5yr" name="5-Yr Avg" stroke="#ADB5BD" strokeWidth={1.5} strokeDasharray="6 3" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  </Card>
));

/* ── Floating Storage ────────────────────────────────────────── */
const FloatingStorage = memo(() => (
  <Card title="Global Floating Storage" badge="With Confidence Bands">
    <div className="h-[220px]">
      <ResponsiveContainer>
        <AreaChart data={FLOATING_DATA}>
          <defs>
            <linearGradient id="floatBand" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0D47A1" stopOpacity={0.06} />
              <stop offset="100%" stopColor="#0D47A1" stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid {...GRID_STYLE} />
          <XAxis dataKey="day" tick={AXIS_STYLE} interval={3} />
          <YAxis tick={AXIS_STYLE} tickFormatter={v => `${v}mb`} />
          <Tooltip content={<CustomTooltip prefix="" />} />
          <Area dataKey="upper" name="Upper" stroke="#CED4DA" strokeDasharray="4 3" strokeWidth={1} fill="url(#floatBand)" />
          <Area dataKey="lower" name="Lower" stroke="#CED4DA" strokeDasharray="4 3" strokeWidth={1} fill="white" />
          <Line dataKey="central" name="Central" stroke="#0D47A1" strokeWidth={1.5} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  </Card>
));

/* ── Spare Capacity & Macro ──────────────────────────────────── */
const SpareCapacity = memo(() => (
  <Card title="Spare Capacity & Macro" badge="Key Indicators">
    <div className="grid grid-cols-3 gap-2 mb-3">
      {[
        { label: 'OPEC Spare', value: '3.2', unit: 'mb/d', color: '' },
        { label: 'Non-OPEC Growth', value: '+1.8', unit: 'mb/d', color: 'text-emerald-700' },
        { label: 'Demand Growth', value: '+1.1', unit: 'mb/d', color: '' },
      ].map(m => (
        <div key={m.label} className="bg-slate-50 border border-slate-200 rounded p-2.5 text-center">
          <div className="text-[9.5px] font-semibold text-slate-500 uppercase tracking-[0.5px] mb-1">{m.label}</div>
          <div className={`text-base font-bold ${m.color || 'text-slate-800'} tabular-nums`}>{m.value} <small className="text-[10px] font-medium text-slate-400">{m.unit}</small></div>
        </div>
      ))}
    </div>
    <table className="w-full text-[11.5px]">
      <thead><tr className="text-left text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px]"><th className="py-1.5 px-2 border-b border-slate-200">Macro Indicator</th><th className="py-1.5 px-2 border-b border-slate-200">Latest</th><th className="py-1.5 px-2 border-b border-slate-200">Prior</th></tr></thead>
      <tbody className="tabular-nums">
        {MACRO_TABLE.map(row => (
          <tr key={row.indicator} className="border-b border-slate-100 last:border-0">
            <td className="py-1 px-2">{row.indicator}</td>
            <td className="py-1 px-2">{row.latest}</td>
            <td className="py-1 px-2 text-slate-400">{row.prior}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </Card>
));


/* ═══════════════════════ Main Tab Export ══════════════════════ */
const SectionTitle = ({ children }) => (
  <h2 className="text-[11px] font-semibold uppercase tracking-[1.2px] text-slate-400 mb-2.5 pl-0.5">{children}</h2>
);

const CoreTradingDesk = memo(function CoreTradingDesk() {
  return (
    <div className="space-y-5 animate-fadeIn">
      {/* Flat Price & Term Structure */}
      <section>
        <SectionTitle>Flat Price & Term Structure</SectionTitle>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5 mb-3.5">
          <ForwardCurve />
          <BrentForwardCurve />
        </div>
        <div className="grid grid-cols-1 gap-3.5">
          <M1M12Spread />
        </div>
      </section>

      {/* Stat-Arb Engine */}
      <section>
        <SectionTitle>Statistical Arbitrage Engine</SectionTitle>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5 mb-3.5">
          <CovMatrix />
          <M1M12Heatmap />
          <PCADecomposition />
        </div>
        <div className="grid grid-cols-1 gap-3.5">
          <DollarCorrelation />
        </div>
      </section>

      {/* Global Arb & Differentials */}
      <section>
        <SectionTitle>Global Arbitrage & Differentials</SectionTitle>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
          <ArbChart />
          <Differentials />
        </div>
      </section>

      {/* Crack Spreads */}
      <section>
        <SectionTitle>Crack Spreads</SectionTitle>
        <div className="grid grid-cols-1 gap-3.5">
          <CrackSpreads />
        </div>
      </section>

      {/* Fundamentals */}
      <section>
        <SectionTitle>Fundamentals Panel</SectionTitle>
        {/* EIA Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5 mb-3.5">
          {FUNDAMENTALS_CARDS.map(f => (
            <div key={f.id} className="bg-white border border-slate-200 rounded-lg p-2.5 text-center hover:shadow-md transition-shadow">
              <div className="text-[8.5px] font-semibold text-slate-400 uppercase tracking-[0.4px] mb-1 leading-tight">{f.label}</div>
              <div className="text-sm font-bold text-slate-800 tabular-nums">{f.value}<span className="text-[9px] font-medium text-slate-400 ml-0.5">{f.unit}</span></div>
              <div className={`text-[10px] font-semibold tabular-nums mt-0.5 ${f.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {f.change >= 0 ? '▲' : '▼'} {Math.abs(f.change).toFixed(1)}
              </div>
              <div className="text-[8px] text-slate-400 mt-0.5">5yr: {f.avg5yr}</div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5">
          <CushingStorage />
          <FloatingStorage />
          <SpareCapacity />
        </div>
      </section>
    </div>
  );
});

export default CoreTradingDesk;
