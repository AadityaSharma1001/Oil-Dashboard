import React, { memo, useMemo } from 'react';
import {
  ComposedChart, Bar, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import Card from './Card';
import { useApiData } from '../hooks/useApiData';
import { fetchCOT } from '../api';
import { COT_DATA } from '../data/mockData';

const AXIS_STYLE = { fontSize: 10, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.04)' };

const COTTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-[11px] px-2.5 py-1.5 rounded-md shadow-lg min-w-[160px]">
      <div className="font-semibold text-slate-300 mb-1 border-b border-slate-700 pb-1">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex justify-between gap-3">
          <span className="text-slate-400">{p.name}</span>
          <span className="font-semibold tabular-nums" style={{ color: p.color }}>
            {p.value > 0 ? '+' : ''}{p.value}k
          </span>
        </div>
      ))}
    </div>
  );
};

const COTPositioning = memo(function COTPositioning() {
  const { data: apiData, source } = useApiData(fetchCOT, { fallback: null, refreshInterval: 300000 });

  const chartData = useMemo(() => {
    if (apiData?.data && Array.isArray(apiData.data) && apiData.data.length > 0) {
      return apiData.data.map(row => ({
        week: row.week,
        managedMoney: row.managed_money ?? row.managedMoney ?? 0,
        producer: row.producer ?? 0,
        swapDealer: row.swap_dealer ?? row.swapDealer ?? 0,
        netSpec: row.net_spec ?? row.netSpec ?? 0,
      }));
    }
    return COT_DATA;
  }, [apiData]);

  const last = chartData[chartData.length - 1];
  return (
    <Card
      title="CFTC COT Positioning"
      badge={`Net Spec: ${last.netSpec > 0 ? '+' : ''}${last.netSpec}k`}
      badgeVariant={last.netSpec > 0 ? 'green' : 'red'}
      source={source}
    >
      <div className="h-[280px]" style={{ minHeight: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="week" tick={AXIS_STYLE} />
            <YAxis tick={AXIS_STYLE} tickFormatter={v => `${v}k`} />
            <Tooltip content={<COTTooltip />} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: 10 }} />
            <ReferenceLine y={0} stroke="#868E96" strokeDasharray="4 3" />
            <Bar dataKey="managedMoney" name="Managed Money" fill="#0D47A1" fillOpacity={0.7} radius={[2, 2, 0, 0]} barSize={14} />
            <Bar dataKey="producer" name="Producer/Merchant" fill="#E53935" fillOpacity={0.7} radius={[2, 2, 0, 0]} barSize={14} />
            <Bar dataKey="swapDealer" name="Swap Dealer" fill="#FFB300" fillOpacity={0.6} radius={[2, 2, 0, 0]} barSize={14} />
            <Line dataKey="netSpec" name="Net Speculative" stroke="#00BCD4" strokeWidth={2} dot={{ r: 2.5, fill: '#00BCD4' }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

export default COTPositioning;
