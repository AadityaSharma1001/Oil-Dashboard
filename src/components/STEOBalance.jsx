import React, { memo, useMemo } from 'react';
import {
  ComposedChart, Bar, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import Card from './Card';
import { useApiData } from '../hooks/useApiData';
import { fetchSTEO } from '../api';
import { STEO_DATA } from '../data/mockData';

const AXIS_STYLE = { fontSize: 10, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.04)' };

const STEOTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-[11px] px-2.5 py-1.5 rounded-md shadow-lg min-w-[160px]">
      <div className="font-semibold text-slate-300 mb-1 border-b border-slate-700 pb-1">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex justify-between gap-3">
          <span className="text-slate-400">{p.name}</span>
          <span className="font-semibold tabular-nums" style={{ color: p.color }}>
            {p.value?.toFixed(1)} mb/d
          </span>
        </div>
      ))}
    </div>
  );
};

const STEOBalance = memo(function STEOBalance() {
  const { data: apiData, source } = useApiData(fetchSTEO, { fallback: null, refreshInterval: 300000 });

  const chartData = useMemo(() => {
    if (apiData?.data && Array.isArray(apiData.data) && apiData.data.length > 0) {
      return apiData.data;
    }
    return STEO_DATA;
  }, [apiData]);

  return (
    <Card title="EIA STEO — Global Oil Balance" badge="Supply / Demand · mb/d" source={source}>
      <div className="h-[300px]" style={{ minHeight: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <defs>
              <linearGradient id="balGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4CAF50" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#E53935" stopOpacity={0.15} />
              </linearGradient>
            </defs>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="month" tick={AXIS_STYLE} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `${v}`} />
            <Tooltip content={<STEOTooltip />} />
            <Legend iconType="plainline" iconSize={14} wrapperStyle={{ fontSize: 10 }} />
            <ReferenceLine y={0} stroke="#868E96" strokeDasharray="4 3" />
            <Bar dataKey="balance" name="Balance" fill="url(#balGrad)" radius={[3, 3, 0, 0]} barSize={20}>
              {chartData.map((entry, idx) => (
                <React.Fragment key={idx} />
              ))}
            </Bar>
            <Line dataKey="supply" name="Supply" stroke="#0D47A1" strokeWidth={2} dot={{ r: 2, fill: '#0D47A1' }} />
            <Line dataKey="demand" name="Demand" stroke="#E53935" strokeWidth={2} dot={{ r: 2, fill: '#E53935' }} />
            <Line dataKey="opec" name="OPEC" stroke="#FFB300" strokeWidth={1.5} strokeDasharray="6 3" dot={false} />
            <Line dataKey="nonOpec" name="Non-OPEC" stroke="#00BCD4" strokeWidth={1.5} strokeDasharray="6 3" dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

export default STEOBalance;
