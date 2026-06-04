import React, { memo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import Card from './Card';
import { useLiveChartData } from '../hooks/useLiveData';
import { BDTI_DATA } from '../data/mockData';

const AXIS_STYLE = { fontSize: 10, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.04)' };

const BDTITooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-[11px] px-2.5 py-1.5 rounded-md shadow-lg">
      <div className="font-semibold text-slate-300 mb-0.5">{label}</div>
      <div className="flex items-center gap-1.5">
        <span className="text-slate-400">BDTI:</span>
        <span className="font-semibold tabular-nums">{payload[0].value}</span>
        <span className="text-slate-500">pts</span>
      </div>
    </div>
  );
};

const BDTIFreight = memo(function BDTIFreight() {
  const data = useLiveChartData(BDTI_DATA, 'value', 5000, 0.002);
  const last = data[data.length - 1]?.value ?? 0;
  const first = data[0]?.value ?? last;
  const change30d = last - first;
  const pct = ((change30d / first) * 100).toFixed(1);

  return (
    <Card
      title="BDTI Freight Index"
      badge={
        <span className="flex items-center gap-1.5">
          <span className="px-1.5 py-0.5 bg-amber-100 text-amber-700 text-[9px] font-bold rounded tracking-wide">SIM</span>
          <span className="tabular-nums">{last.toFixed(0)} pts</span>
        </span>
      }
    >
      <div className="h-[220px]" style={{ minHeight: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="bdtiGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#795548" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#795548" stopOpacity={0.01} />
              </linearGradient>
            </defs>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="day" tick={AXIS_STYLE} interval={5} />
            <YAxis tick={AXIS_STYLE} domain={['auto', 'auto']} />
            <Tooltip content={<BDTITooltip />} />
            <Area dataKey="value" name="BDTI" stroke="#795548" fill="url(#bdtiGrad)" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center justify-between mt-2 px-1 text-[10px]">
        <span className="text-slate-400">30d change:</span>
        <span className={`font-semibold tabular-nums ${change30d >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {change30d >= 0 ? '+' : ''}{change30d.toFixed(0)} pts ({change30d >= 0 ? '+' : ''}{pct}%)
        </span>
      </div>
    </Card>
  );
});

export default BDTIFreight;
