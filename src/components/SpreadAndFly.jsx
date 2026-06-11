import React, { memo, useState, useCallback, useMemo } from 'react';
import {
  ComposedChart, Line, Area, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import Card from './Card';
import { useApiData } from '../hooks/useApiData';
import { fetchCalendarSpreads, fetchFlySpreads } from '../api';

const AXIS_STYLE = { fontSize: 9, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.05)' };
const SPREAD_COLORS = ['#08306b', '#08519c', '#2171b5', '#4292c6', '#6baed6', '#9ecae1', '#c6dbef', '#deebf7', '#f7fbff', '#d1e5f0', '#92c5de'];
const FLY_COLORS = ['#08306b', '#08519c', '#2171b5', '#4292c6', '#6baed6', '#9ecae1', '#c6dbef', '#deebf7', '#f7fbff', '#d1e5f0', '#92c5de'];
const BRENT_SPREAD_COLORS = ['#4a148c', '#6a1b9a', '#7b1fa2', '#8e24aa', '#9c27b0', '#ab47bc', '#ba68c8', '#ce93d8', '#e1bee7', '#f3e5f5', '#d1c4e9'];
const BRENT_FLY_COLORS = ['#4a148c', '#6a1b9a', '#7b1fa2', '#8e24aa', '#9c27b0', '#ab47bc', '#ba68c8', '#ce93d8', '#e1bee7', '#f3e5f5', '#d1c4e9'];

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

/* ── Combined Card (Term Structure + History in tabs) ────── */
const TermHistoryCard = memo(({ title, termData, historyData, keys, barColor, lineColors, source }) => {
  const [view, setView] = useState('term');

  if (!termData || !termData.length) return <Card title={title} source={source}>Loading...</Card>;

  return (
    <Card
      title={title}
      source={source}
      badge={
        <div className="flex items-center gap-0.5">
          {[['term', 'Term Structure'], ['history', '20d History']].map(([k, label]) => (
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
            <ComposedChart data={termData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="label" tick={{ fontSize: 8, fill: '#868E96' }} interval={0} angle={-25} textAnchor="end" height={45} />
              <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(2)}`} domain={['auto', 'auto']} width={45} />
              <Tooltip content={<SpreadTooltip />} />
              <ReferenceLine y={0} stroke="#ADB5BD" strokeDasharray="4 3" strokeOpacity={0.5} />
              <Line dataKey="hi" name="High" stroke="#E57373" strokeWidth={1} strokeDasharray="3 3" dot={{ r: 2, fill: '#E57373' }} />
              <Line dataKey="lo" name="Low" stroke="#64B5F6" strokeWidth={1} strokeDasharray="3 3" dot={{ r: 2, fill: '#64B5F6' }} />
              <Line dataKey="mean" name="Mean" stroke="#ADB5BD" strokeWidth={1.5} dot={{ r: 2.5, fill: '#ADB5BD' }} />
              <Bar dataKey="value" name="Current" fill={barColor} fillOpacity={0.7} radius={[3, 3, 0, 0]} barSize={18} />
            </ComposedChart>
          ) : (
            <ComposedChart data={historyData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="day" tick={AXIS_STYLE} interval={5} />
              <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v.toFixed(2)}`} domain={['auto', 'auto']} width={45} />
              <Tooltip content={<SpreadTooltip />} />
              <Legend iconType="plainline" iconSize={10} wrapperStyle={{ fontSize: 9 }} />
              <ReferenceLine y={0} stroke="#ADB5BD" strokeDasharray="4 3" strokeOpacity={0.4} />
              {keys.map((k, i) => (
                <Line
                  key={k}
                  dataKey={k}
                  name={k}
                  stroke={lineColors[i % lineColors.length]}
                  strokeWidth={i === 0 ? 2 : 1.5}
                  strokeDasharray={i > 0 ? `${4 + i} ${2 + i}` : undefined}
                  dot={false}
                  activeDot={{ r: 3, strokeWidth: 0, fill: lineColors[i % lineColors.length] }}
                />
              ))}
            </ComposedChart>
          )}
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ── Live Wrappers ───────────────────────────────────────────── */

const LiveCalSpreads = memo(({ commodity, title, barColor, lineColors }) => {
  const fetchFn = useCallback(() => fetchCalendarSpreads(commodity, 'ALL'), [commodity]);
  const { data, source } = useApiData(fetchFn, { fallback: null, refreshInterval: 60000 });
  const spreadsMap = data?.data || {};

  const termStructure = useMemo(() => {
    const keys = Object.keys(spreadsMap);
    if (!keys.length) return [];
    return keys.map(k => {
      const history = spreadsMap[k];
      const last = history.length > 0 ? history[history.length - 1] : {};
      return {
        label: k,
        value: last?.value,
        mean: last?.mean,
        hi: last?.hi,
        lo: last?.lo,
        history: history.map(h => ({ day: h.day, value: h.value }))
      };
    });
  }, [spreadsMap]);

  const historyData = useMemo(() => {
    if (!termStructure.length) return [];
    const dates = termStructure[0]?.history?.map(h => h.day) || [];
    return dates.map((d, i) => {
      const row = { day: d };
      termStructure.forEach(ts => {
         row[ts.label] = ts.history?.[i]?.value;
      });
      return row;
    });
  }, [termStructure]);

  const keys = termStructure.map(t => t.label);

  return (
    <TermHistoryCard
      title={title}
      termData={termStructure}
      historyData={historyData}
      keys={keys}
      barColor={barColor}
      lineColors={lineColors}
      source={source}
    />
  );
});

const LiveFlySpreads = memo(({ commodity, title, barColor, lineColors }) => {
  const fetchFn = useCallback(() => fetchFlySpreads(commodity), [commodity]);
  const { data, source } = useApiData(fetchFn, { fallback: null, refreshInterval: 60000 });
  const termStructure = data?.term_structure || [];

  const historyData = useMemo(() => {
    if (!termStructure.length) return [];
    const dates = termStructure[0]?.history?.map(h => h.day) || [];
    return dates.map((d, i) => {
      const row = { day: d };
      termStructure.forEach(ts => {
         row[ts.label] = ts.history?.[i]?.value;
      });
      return row;
    });
  }, [termStructure]);

  const keys = termStructure.map(t => t.label);

  return (
    <TermHistoryCard
      title={title}
      termData={termStructure}
      historyData={historyData}
      keys={keys}
      barColor={barColor}
      lineColors={lineColors}
      source={source}
    />
  );
});


/* ═══════════════════════ Main Layout ═════════════════════════ */
const SpreadAndFly = memo(function SpreadAndFly() {
  return (
    <div className="space-y-3.5 animate-fadeIn">
      {/* Row 1: Calendar Spreads */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <LiveCalSpreads
          commodity="wti"
          title="WTI Calendar Spreads"
          barColor="#0D47A1"
          lineColors={SPREAD_COLORS}
        />
        <LiveCalSpreads
          commodity="brent"
          title="Brent Calendar Spreads"
          barColor="#6A1B9A"
          lineColors={BRENT_SPREAD_COLORS}
        />
      </div>

      {/* Row 2: Fly (Term Structure + History merged) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <LiveFlySpreads
          commodity="wti"
          title="WTI Butterfly Spread"
          barColor="#0D47A1"
          lineColors={FLY_COLORS}
        />
        <LiveFlySpreads
          commodity="brent"
          title="Brent Butterfly Spread"
          barColor="#6A1B9A"
          lineColors={BRENT_FLY_COLORS}
        />
      </div>
    </div>
  );
});

export default SpreadAndFly;
