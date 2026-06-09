import React, { memo, useState } from 'react';
import {
  ComposedChart, Line, Area, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import Card from './Card';
import { useLiveChartData } from '../hooks/useLiveData';
import {
  WTI_CAL_SPREADS, BRENT_CAL_SPREADS,
  WTI_FLY_TERM, BRENT_FLY_TERM,
  WTI_FLY_HISTORY, WTI_FLY_KEYS, WTI_FLY_LABELS,
  BRENT_FLY_HISTORY, BRENT_FLY_KEYS, BRENT_FLY_LABELS_ARR,
} from '../data/mockData';

const AXIS_STYLE = { fontSize: 9, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.05)' };
const SPREAD_COLORS = ['#0D47A1', '#1976D2', '#42A5F5', '#90CAF9', '#BBDEFB'];
const FLY_COLORS = ['#0D47A1', '#1565C0', '#1E88E5', '#42A5F5', '#90CAF9'];
const BRENT_SPREAD_COLORS = ['#4A148C', '#6A1B9A', '#8E24AA', '#AB47BC', '#CE93D8'];
const BRENT_FLY_COLORS = ['#4A148C', '#6A1B9A', '#8E24AA', '#AB47BC', '#CE93D8'];

/* ── Tooltip ─────────────────────────────────────────────────── */
const SpreadTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-[10px] px-3 py-2 rounded-lg shadow-xl min-w-[140px]">
      <div className="font-semibold text-slate-300 mb-1 pb-1 border-b border-slate-700">{label}</div>
      {payload.filter(p => !p.name.startsWith('_')).map((p, i) => (
        <div key={i} className="flex justify-between gap-3">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
            <span className="text-slate-400">{p.name}</span>
          </span>
          <span className="font-semibold tabular-nums">
            {typeof p.value === 'number' ? `$${p.value.toFixed(3)}` : p.value}
          </span>
        </div>
      ))}
    </div>
  );
};

/* ── Calendar Spread Chart (single spread with mean + range) ── */
const CalSpreadChart = memo(({ title, spreadsMap, accentColors }) => {
  const keys = Object.keys(spreadsMap);
  const [activeSpread, setActiveSpread] = useState(keys[0]);
  const rawData = spreadsMap[activeSpread];
  const data = useLiveChartData(rawData, 'value', 3000, 0.004);

  const last = data[data.length - 1];
  const deviation = last ? ((last.value - last.mean) / (last.hi - last.lo) * 100).toFixed(0) : '0';

  return (
    <Card
      title={title}
      badge={
        <div className="flex items-center gap-0.5 flex-wrap">
          {keys.map((k, i) => (
            <button
              key={k}
              onClick={() => setActiveSpread(k)}
              className={`px-1.5 py-0.5 text-[8px] font-bold uppercase rounded transition-all ${
                activeSpread === k
                  ? 'text-white shadow-sm'
                  : 'bg-slate-100 text-slate-400 hover:bg-slate-200'
              }`}
              style={activeSpread === k ? { background: accentColors[i] } : {}}
            >
              {k}
            </button>
          ))}
        </div>
      }
    >
      <div className="h-[250px]" style={{ minHeight: 250 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={`calGrad-${title}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={accentColors[keys.indexOf(activeSpread)]} stopOpacity={0.12} />
                <stop offset="100%" stopColor={accentColors[keys.indexOf(activeSpread)]} stopOpacity={0.01} />
              </linearGradient>
            </defs>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="day" tick={AXIS_STYLE} interval={5} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(2)}`} domain={['auto', 'auto']} width={48} />
            <Tooltip content={<SpreadTooltip />} />

            {/* Historical range band */}
            <Line dataKey="hi" name="_hi" stroke="#E57373" strokeWidth={0.8} strokeDasharray="3 4" strokeOpacity={0.5} dot={false} activeDot={false} legendType="none" />
            <Line dataKey="lo" name="_lo" stroke="#64B5F6" strokeWidth={0.8} strokeDasharray="3 4" strokeOpacity={0.5} dot={false} activeDot={false} legendType="none" />

            {/* Mean line */}
            <Line dataKey="mean" name="Mean" stroke="#ADB5BD" strokeWidth={1.5} dot={false} activeDot={false} />

            {/* Spread value */}
            <Area
              dataKey="value"
              name={activeSpread}
              stroke={accentColors[keys.indexOf(activeSpread)]}
              fill={`url(#calGrad-${title})`}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 3, strokeWidth: 0 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      {/* Metrics strip */}
      <div className="flex items-center justify-between mt-2 px-1 text-[9px] text-slate-500">
        <div className="flex items-center gap-3">
          <span>Spread: <span className="font-bold text-slate-700 tabular-nums">${last?.value?.toFixed(3)}</span></span>
          <span>Mean: <span className="font-bold text-slate-700 tabular-nums">${last?.mean?.toFixed(3)}</span></span>
        </div>
        <div className="flex items-center gap-3">
          <span>Range: <span className="font-semibold tabular-nums text-red-400">${last?.hi?.toFixed(3)}</span> / <span className="font-semibold tabular-nums text-blue-400">${last?.lo?.toFixed(3)}</span></span>
          <span className={`font-bold tabular-nums ${Math.abs(+deviation) > 50 ? 'text-amber-600' : 'text-slate-500'}`}>
            {+deviation > 0 ? '+' : ''}{deviation}% from mean
          </span>
        </div>
      </div>
    </Card>
  );
});

/* ── Combined Fly Card (Term Structure + History in tabs) ────── */
const FlyCard = memo(({ title, flyTerm, flyHistory, flyKeys, flyLabels, barColor, lineColors }) => {
  const [view, setView] = useState('term');

  return (
    <Card
      title={title}
      badge={
        <div className="flex items-center gap-0.5">
          {[['term', 'Term Structure'], ['history', '30d History']].map(([k, label]) => (
            <button
              key={k}
              onClick={() => setView(k)}
              className={`px-2 py-0.5 text-[8px] font-bold uppercase rounded transition-all ${
                view === k
                  ? 'bg-slate-800 text-white'
                  : 'bg-slate-100 text-slate-400 hover:bg-slate-200'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      }
    >
      <div className="h-[260px]" style={{ minHeight: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          {view === 'term' ? (
            <ComposedChart data={flyTerm} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="label" tick={{ fontSize: 8, fill: '#868E96' }} interval={0} angle={-25} textAnchor="end" height={45} />
              <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(2)}`} domain={['auto', 'auto']} width={45} />
              <Tooltip content={<SpreadTooltip />} />
              <ReferenceLine y={0} stroke="#ADB5BD" strokeDasharray="4 3" strokeOpacity={0.5} />
              <Line dataKey="hi" name="5yr High" stroke="#E57373" strokeWidth={1} strokeDasharray="3 3" dot={{ r: 2, fill: '#E57373' }} />
              <Line dataKey="lo" name="5yr Low" stroke="#64B5F6" strokeWidth={1} strokeDasharray="3 3" dot={{ r: 2, fill: '#64B5F6' }} />
              <Line dataKey="mean" name="Mean" stroke="#ADB5BD" strokeWidth={1.5} dot={{ r: 2.5, fill: '#ADB5BD' }} />
              <Bar dataKey="value" name="Current" fill={barColor} fillOpacity={0.7} radius={[3, 3, 0, 0]} barSize={18} />
            </ComposedChart>
          ) : (
            <ComposedChart data={flyHistory} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="day" tick={AXIS_STYLE} interval={5} />
              <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(2)}`} domain={['auto', 'auto']} width={45} />
              <Tooltip content={<SpreadTooltip />} />
              <Legend iconType="plainline" iconSize={10} wrapperStyle={{ fontSize: 9 }} />
              <ReferenceLine y={0} stroke="#ADB5BD" strokeDasharray="4 3" strokeOpacity={0.4} />
              {flyKeys.map((k, i) => (
                <Line
                  key={k}
                  dataKey={k}
                  name={flyLabels[i]}
                  stroke={lineColors[i]}
                  strokeWidth={i === 0 ? 2 : 1.5}
                  strokeDasharray={i > 0 ? `${4 + i} ${2 + i}` : undefined}
                  dot={false}
                  activeDot={{ r: 3, strokeWidth: 0, fill: lineColors[i] }}
                />
              ))}
            </ComposedChart>
          )}
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ═══════════════════════ Main Layout ═════════════════════════ */
const SpreadAndFly = memo(function SpreadAndFly() {
  return (
    <div className="space-y-3.5 animate-fadeIn">
      {/* Row 1: Individual Calendar Spreads */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <CalSpreadChart
          title="WTI Calendar Spreads"
          spreadsMap={WTI_CAL_SPREADS}
          accentColors={SPREAD_COLORS}
        />
        <CalSpreadChart
          title="Brent Calendar Spreads"
          spreadsMap={BRENT_CAL_SPREADS}
          accentColors={BRENT_SPREAD_COLORS}
        />
      </div>

      {/* Row 2: Fly (Term Structure + History merged) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <FlyCard
          title="WTI Butterfly Spread"
          flyTerm={WTI_FLY_TERM}
          flyHistory={WTI_FLY_HISTORY}
          flyKeys={WTI_FLY_KEYS}
          flyLabels={WTI_FLY_LABELS}
          barColor="#0D47A1"
          lineColors={FLY_COLORS}
        />
        <FlyCard
          title="Brent Butterfly Spread"
          flyTerm={BRENT_FLY_TERM}
          flyHistory={BRENT_FLY_HISTORY}
          flyKeys={BRENT_FLY_KEYS}
          flyLabels={BRENT_FLY_LABELS_ARR}
          barColor="#6A1B9A"
          lineColors={BRENT_FLY_COLORS}
        />
      </div>
    </div>
  );
});

export default SpreadAndFly;
