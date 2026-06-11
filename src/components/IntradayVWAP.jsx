import React, { memo, useCallback, useMemo } from 'react';
import {
  ComposedChart, Line, Area, ReferenceLine,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import Card from './Card';
import { useApiData } from '../hooks/useApiData';
import { fetchIntraday } from '../api';

const AXIS_STYLE = { fontSize: 9, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.04)' };

/* ── Custom Tooltip ──────────────────────────────────────────── */
const VWAPTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div className="bg-slate-900 text-white text-[10px] px-2.5 py-2 rounded-md shadow-lg min-w-[140px]">
      <div className="font-semibold text-slate-300 mb-1 border-b border-slate-700 pb-1">{d.time}</div>
        <div className="flex justify-between gap-3"><span className="text-slate-400">Price</span><span className="font-semibold tabular-nums">${d.price?.toFixed(2)}</span></div>
        <div className="flex justify-between gap-3"><span className="text-slate-400">Z-Score</span><span className={`font-semibold tabular-nums ${d.z_score > 0 ? 'text-green-400' : d.z_score < 0 ? 'text-red-400' : 'text-slate-400'}`}>{d.z_score > 0 ? '+' : ''}{d.z_score?.toFixed(2)}σ</span></div>
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
const VWAPChart = memo(({ title, fetchFn, accentColor, gradId }) => {
  const { data: apiResponse, source } = useApiData(fetchFn, { fallback: null, refreshInterval: 60000 });

  const chartData = useMemo(() => {
    if (apiResponse?.data && Array.isArray(apiResponse.data)) {
      return apiResponse.data;
    }
    return [];
  }, [apiResponse]);

  const lastBar = chartData.length > 0 ? chartData[chartData.length - 1] : { vwap: 0, band_width: 0, deviation: 0 };
  const devColor = lastBar.deviation > 1 ? 'text-green-600' : lastBar.deviation < -1 ? 'text-red-600' : 'text-slate-700';

  return (
    <Card
      title={title}
      badge="Intraday Z-Score"
      source={source}
      footer={
        <div className="flex items-center justify-center divide-x divide-slate-200 -mx-3.5 -mb-3.5 bg-slate-50 border-t border-slate-100">
          <Metric label="Current Price" value={lastBar.price?.toFixed(2)} unit="$/bbl" />
          <Metric label="Current Z-Score" value={`${lastBar.z_score > 0 ? '+' : ''}${lastBar.z_score?.toFixed(2)}σ`} unit="" color={lastBar.z_score > 0 ? 'text-green-500' : 'text-red-500'} />
        </div>
      }
    >
      <div className="h-[280px]" style={{ minHeight: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={accentColor} stopOpacity={0.06} />
                <stop offset="50%" stopColor={accentColor} stopOpacity={0.02} />
                <stop offset="100%" stopColor={accentColor} stopOpacity={0.06} />
              </linearGradient>
            </defs>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="time" tick={AXIS_STYLE} minTickGap={30} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `${v > 0 ? '+' : ''}${v}σ`} domain={[-3.5, 3.5]} width={52} />
            <Tooltip content={<VWAPTooltip />} />

            {/* Z-Score Reference Lines */}
            <ReferenceLine y={2} stroke="#ef4444" strokeDasharray="3 3" opacity={0.5} />
            <ReferenceLine y={-2} stroke="#10b981" strokeDasharray="3 3" opacity={0.5} />
            <ReferenceLine y={0} stroke="#94a3b8" opacity={0.5} />

            {/* Z-Score line */}
            <Line dataKey="z_score" name="Z-Score" stroke={accentColor} strokeWidth={2} dot={false} activeDot={{ r: 4, fill: accentColor, stroke: "#fff", strokeWidth: 2 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ── Main Export ──────────────────────────────────────────────── */
const IntradayVWAP = memo(function IntradayVWAP() {
  const fetchWti = useCallback(() => fetchIntraday('wti'), []);
  const fetchBrent = useCallback(() => fetchIntraday('brent'), []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
      <VWAPChart
        title="WTI M1 — Intraday VWAP"
        fetchFn={fetchWti}
        accentColor="#0D47A1"
        gradId="wti-bb-grad"
      />
      <VWAPChart
        title="Brent M1 — Intraday VWAP"
        fetchFn={fetchBrent}
        accentColor="#343A40"
        gradId="brent-bb-grad"
      />
    </div>
  );
});

export default IntradayVWAP;
