import React, { memo, useState, useMemo, useCallback } from 'react';
import {
  ComposedChart, Area, Line,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import Card from './Card';
import { useApiData } from '../hooks/useApiData';
import { fetchFiveYearRange } from '../api';
import { WTI_5YR_RANGE, BRENT_5YR_RANGE } from '../data/mockData';

const AXIS_STYLE = { fontSize: 9, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.05)' };

const RangeTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div className="bg-slate-900 text-white text-[10px] px-3 py-2 rounded-lg shadow-xl min-w-[150px]">
      <div className="font-semibold text-slate-300 mb-1.5 pb-1 border-b border-slate-700">{d.week}</div>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">5yr High</span>
          <span className="font-semibold tabular-nums text-red-300">${d.high5yr}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">5yr Median</span>
          <span className="font-semibold tabular-nums text-slate-300">${d.median5yr}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">5yr Low</span>
          <span className="font-semibold tabular-nums text-blue-300">${d.low5yr}</span>
        </div>
        {d.current != null && (
          <div className="flex justify-between gap-4 border-t border-slate-700 pt-1 mt-1">
            <span className="text-emerald-300 font-semibold">Current</span>
            <span className="font-bold tabular-nums text-emerald-300">${d.current}</span>
          </div>
        )}
      </div>
    </div>
  );
};

const Metric = ({ label, value, unit, color }) => (
  <div className="flex flex-col items-center px-4 py-1.5">
    <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-[0.5px]">{label}</span>
    <span className={`text-sm font-bold tabular-nums ${color || 'text-slate-800'}`}>
      {value}<span className="text-[10px] font-medium text-slate-400 ml-0.5">{unit}</span>
    </span>
  </div>
);

const RangeChart = memo(({ title, data, accentColor, gradId, source }) => {
  const currentWeekData = data.filter(d => d.current != null);
  const lastCurrent = currentWeekData[currentWeekData.length - 1];
  const currentPrice = lastCurrent?.current ?? 0;
  const median = lastCurrent?.median5yr ?? 0;
  const high = lastCurrent?.high5yr ?? 0;
  const low = lastCurrent?.low5yr ?? 0;
  const range = high - low;
  const percentile = range > 0 ? Math.round(((currentPrice - low) / range) * 100) : 0;
  const vsMedian = (currentPrice - median).toFixed(2);

  return (
    <Card
      title={title}
      badge="52-Week Seasonal"
      source={source}
      footer={
        <div className="flex items-center justify-center divide-x divide-slate-200 -mx-3.5 -mb-2.5 bg-slate-50">
          <Metric label="Current" value={`$${currentPrice.toFixed(2)}`} unit="" />
          <Metric label="5yr Median" value={`$${median.toFixed(2)}`} unit="" />
          <Metric label="vs Median" value={`${+vsMedian >= 0 ? '+' : ''}${vsMedian}`} unit="$/bbl" color={+vsMedian >= 0 ? 'text-emerald-600' : 'text-red-600'} />
          <Metric label="Percentile" value={`P${percentile}`} unit="" color={percentile >= 50 ? 'text-emerald-600' : 'text-amber-600'} />
        </div>
      }
    >
      <div className="h-[280px]" style={{ minHeight: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={accentColor} stopOpacity={0.12} />
                <stop offset="100%" stopColor={accentColor} stopOpacity={0.01} />
              </linearGradient>
            </defs>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="week" tick={AXIS_STYLE} interval={7} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `$${v}`} domain={['auto', 'auto']} width={48} />
            <Tooltip content={<RangeTooltip />} />

            {/* 5yr high/low as dashed lines */}
            <Line dataKey="high5yr" name="5yr High" stroke="#f87171" strokeWidth={1} strokeDasharray="4 3" strokeOpacity={0.5} dot={false} activeDot={false} />
            <Line dataKey="low5yr" name="5yr Low" stroke="#60a5fa" strokeWidth={1} strokeDasharray="4 3" strokeOpacity={0.5} dot={false} activeDot={false} />

            {/* Median */}
            <Line dataKey="median5yr" name="5yr Median" stroke="#ADB5BD" strokeWidth={1.5} dot={false} activeDot={false} />

            {/* Current year price with area fill */}
            <Area dataKey="current" name="2026 Current" stroke={accentColor} fill={`url(#${gradId})`} strokeWidth={2} dot={false} activeDot={{ r: 3, strokeWidth: 0 }} connectNulls={false} />

            <ReferenceLine x="W21" stroke={accentColor} strokeDasharray="4 4" strokeOpacity={0.3} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

const FiveYearRange = memo(function FiveYearRange() {
  const fetchWti = useCallback(() => fetchFiveYearRange('wti'), []);
  const fetchBrent = useCallback(() => fetchFiveYearRange('brent'), []);
  const { data: wtiApi, source: wtiSource } = useApiData(fetchWti, { fallback: null, refreshInterval: 300000 });
  const { data: brentApi, source: brentSource } = useApiData(fetchBrent, { fallback: null, refreshInterval: 300000 });

  const wtiData = useMemo(() => {
    if (wtiApi?.data && Array.isArray(wtiApi.data) && wtiApi.data.length > 0) {
      return wtiApi.data.map(d => ({
        week: d.day || d.week,
        high5yr: d.high5yr,
        low5yr: d.low5yr,
        median5yr: d.mean5yr ?? d.median5yr,
        current: d.close ?? d.current ?? d.open,
      }));
    }
    return WTI_5YR_RANGE;
  }, [wtiApi]);

  const brentData = useMemo(() => {
    if (brentApi?.data && Array.isArray(brentApi.data) && brentApi.data.length > 0) {
      return brentApi.data.map(d => ({
        week: d.day || d.week,
        high5yr: d.high5yr,
        low5yr: d.low5yr,
        median5yr: d.mean5yr ?? d.median5yr,
        current: d.close ?? d.current ?? d.open,
      }));
    }
    return BRENT_5YR_RANGE;
  }, [brentApi]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
      <RangeChart title="WTI — 5yr Same-Week Range" data={wtiData} accentColor="#0D47A1" gradId="wtiRng" source={wtiSource} />
      <RangeChart title="Brent — 5yr Same-Week Range" data={brentData} accentColor="#7B1FA2" gradId="brtRng" source={brentSource} />
    </div>
  );
});

export default FiveYearRange;
