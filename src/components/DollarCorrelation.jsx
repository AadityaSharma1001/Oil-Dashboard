import React, { memo, useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import Card from './Card';
import { useLiveChartData } from '../hooks/useLiveData';
import { useApiData } from '../hooks/useApiData';
import { fetchDollarCorrelation } from '../api';
import { DOLLAR_CORR_DATA } from '../data/mockData';

const AXIS_STYLE = { fontSize: 10, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.04)' };

const CorrTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const v = payload[0].value;
  const strength = Math.abs(v) > 0.5 ? 'Strong' : Math.abs(v) > 0.3 ? 'Moderate' : 'Weak';
  return (
    <div className="bg-slate-900 text-white text-[11px] px-2.5 py-1.5 rounded-md shadow-lg">
      <div className="font-semibold text-slate-300 mb-0.5">{label}</div>
      <div className="flex items-center gap-1.5">
        <span className="text-slate-400">Pearson ρ:</span>
        <span className={`font-semibold tabular-nums ${v < -0.3 ? 'text-red-400' : v > 0.3 ? 'text-green-400' : 'text-slate-300'}`}>{v.toFixed(3)}</span>
      </div>
      <div className="text-[10px] text-slate-500 mt-0.5">{strength} {v < 0 ? 'negative' : 'positive'} correlation</div>
    </div>
  );
};

const DollarCorrelation = memo(function DollarCorrelation() {
  const { data: apiData, source } = useApiData(fetchDollarCorrelation, { fallback: null, refreshInterval: 300000 });
  const corrData = useMemo(() => {
    if (apiData?.data && Array.isArray(apiData.data) && apiData.data.length > 0) return apiData.data;
    return DOLLAR_CORR_DATA;
  }, [apiData]);
  const data = corrData;
  const last = data[data.length - 1]?.correlation ?? 0;

  return (
    <Card
      title="WTI · Dollar Correlation"
      badge={`ρ = ${last.toFixed(3)}`}
      badgeVariant={last < -0.4 ? 'red' : 'default'}
      source={source}
    >
      <div className="h-[220px]" style={{ minHeight: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="corrGradPos" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4CAF50" stopOpacity={0.12} />
                <stop offset="100%" stopColor="#4CAF50" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="corrGradNeg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#E53935" stopOpacity={0} />
                <stop offset="100%" stopColor="#E53935" stopOpacity={0.12} />
              </linearGradient>
            </defs>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="day" tick={AXIS_STYLE} interval={9} />
            <YAxis tick={AXIS_STYLE} domain={[-1, 1]} ticks={[-1, -0.5, 0, 0.5, 1]} />
            <Tooltip content={<CorrTooltip />} />
            <ReferenceLine y={0} stroke="#868E96" strokeDasharray="4 3" />
            <ReferenceLine y={-0.5} stroke="#E53935" strokeDasharray="3 5" strokeOpacity={0.3} />
            <ReferenceLine y={0.5} stroke="#4CAF50" strokeDasharray="3 5" strokeOpacity={0.3} />
            <Area dataKey="correlation" name="Correlation" stroke="#E53935" fill="url(#corrGradNeg)" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center justify-center gap-4 mt-2 text-[10px] text-slate-400">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400" /> Strong negative ({"<"} −0.5)</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-300" /> Weak (±0.3)</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-400" /> Strong positive ({">"} +0.5)</span>
      </div>
    </Card>
  );
});

export default DollarCorrelation;
