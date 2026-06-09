import React, { memo, useMemo } from 'react';
import {
  AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import Card from './Card';
import { useApiData } from '../hooks/useApiData';
import { fetchBDTI } from '../api';
import { BDTI_DATA } from '../data/mockData';

const AXIS_STYLE = { fontSize: 10, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.04)' };

const BDTITooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-[11px] px-2.5 py-1.5 rounded-md shadow-lg">
      <div className="font-semibold text-slate-300 mb-0.5">{label}</div>
      <div className="font-semibold tabular-nums">{payload[0]?.value?.toFixed(0)}</div>
    </div>
  );
};

const BDTIFreight = memo(function BDTIFreight() {
  const { data: apiData, source } = useApiData(fetchBDTI, { fallback: null, refreshInterval: 300000 });

  const chartData = useMemo(() => {
    if (apiData?.data && Array.isArray(apiData.data) && apiData.data.length > 0) {
      return apiData.data;
    }
    return BDTI_DATA;
  }, [apiData]);

  const current = apiData?.current || chartData[chartData.length - 1]?.value || 0;
  const change30d = apiData?.change_30d ?? (chartData[chartData.length - 1]?.value - chartData[0]?.value) ?? 0;
  const changePct = apiData?.change_30d_pct ?? ((change30d / (chartData[0]?.value || 1)) * 100);
  const isUp = change30d >= 0;

  return (
    <Card
      title="BDTI Freight Index"
      badge={`${isUp ? '+' : ''}${changePct.toFixed(1)}% 30d`}
      badgeVariant={isUp ? 'green' : 'red'}
      source={source}
    >
      <div className="mb-2 text-center">
        <span className="text-xl font-bold text-slate-800 tabular-nums">{current.toFixed(0)}</span>
        <span className={`text-xs font-semibold ml-2 ${isUp ? 'text-emerald-600' : 'text-red-600'}`}>
          {isUp ? '▲' : '▼'} {Math.abs(change30d).toFixed(0)}
        </span>
      </div>
      <div className="h-[220px]" style={{ minHeight: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="bdtiGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0D47A1" stopOpacity={0.12} />
                <stop offset="100%" stopColor="#0D47A1" stopOpacity={0.01} />
              </linearGradient>
            </defs>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="day" tick={AXIS_STYLE} interval={5} />
            <YAxis tick={AXIS_STYLE} domain={['auto', 'auto']} />
            <Tooltip content={<BDTITooltip />} />
            <Area dataKey="value" name="BDTI" stroke="#0D47A1" fill="url(#bdtiGrad)" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

export default BDTIFreight;
