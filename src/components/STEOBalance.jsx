import React, { memo } from 'react';
import {
  ComposedChart, Line, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import Card from './Card';
import { STEO_DATA } from '../data/mockData';

const AXIS_STYLE = { fontSize: 10, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.04)' };

const STEOTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div className="bg-slate-900 text-white text-[11px] px-2.5 py-1.5 rounded-md shadow-lg min-w-[170px]">
      <div className="font-semibold text-slate-300 mb-1 border-b border-slate-700 pb-1">{label} 2026</div>
      {payload.map((p, i) => (
        <div key={i} className="flex justify-between gap-3">
          <span className="text-slate-400">{p.name}</span>
          <span className="font-semibold tabular-nums" style={{ color: p.color }}>
            {typeof p.value === 'number' ? p.value.toFixed(1) : p.value} mb/d
          </span>
        </div>
      ))}
    </div>
  );
};

const STEOBalance = memo(function STEOBalance() {
  return (
    <Card title="Global Oil Balance — EIA STEO" badge="2026 Forecast (mb/d)">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        {/* Supply vs Demand */}
        <div>
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px] mb-2">Supply vs Demand</div>
          <div className="h-[240px]" style={{ minHeight: 240 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={STEO_DATA}>
                <CartesianGrid {...GRID_STYLE} />
                <XAxis dataKey="month" tick={AXIS_STYLE} />
                <YAxis tick={AXIS_STYLE} domain={[99.5, 105]} tickFormatter={v => `${v}`} />
                <Tooltip content={<STEOTooltip />} />
                <Legend iconType="plainline" iconSize={14} wrapperStyle={{ fontSize: 10 }} />
                <Line dataKey="supply" name="World Supply" stroke="#0D47A1" strokeWidth={2} dot={{ r: 2, fill: '#0D47A1' }} />
                <Line dataKey="demand" name="World Demand" stroke="#E53935" strokeWidth={2} dot={{ r: 2, fill: '#E53935' }} />
                <ReferenceLine y={102} stroke="#ADB5BD" strokeDasharray="4 3" strokeOpacity={0.4} />
                <Bar dataKey="balance" name="Implied Balance" fill="#4CAF50" fillOpacity={0.5} radius={[2, 2, 0, 0]} barSize={16} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
        {/* OPEC vs Non-OPEC breakdown */}
        <div>
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px] mb-2">Supply Breakdown</div>
          <div className="h-[240px]" style={{ minHeight: 240 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={STEO_DATA}>
                <CartesianGrid {...GRID_STYLE} />
                <XAxis dataKey="month" tick={AXIS_STYLE} />
                <YAxis tick={AXIS_STYLE} domain={[0, 'auto']} tickFormatter={v => `${v}`} />
                <Tooltip content={<STEOTooltip />} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 10 }} />
                <Bar dataKey="opec" name="OPEC" stackId="supply" fill="#0D47A1" fillOpacity={0.7} barSize={20} radius={[0, 0, 0, 0]} />
                <Bar dataKey="nonOpec" name="Non-OPEC" stackId="supply" fill="#64B5F6" fillOpacity={0.6} barSize={20} radius={[2, 2, 0, 0]} />
                <Line dataKey="demand" name="Demand" stroke="#E53935" strokeWidth={2} strokeDasharray="6 3" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </Card>
  );
});

export default STEOBalance;
