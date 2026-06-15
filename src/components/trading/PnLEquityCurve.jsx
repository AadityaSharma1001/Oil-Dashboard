import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const PnLEquityCurve = ({ data = [], currentUnrealized = 0 }) => {
  const chartData = useMemo(() => {
    // We want to map the equity curve. If it's empty, just show a flat line at 0.
    if (!data || data.length === 0) {
      return [{ time: 'Start', equity: 0 }];
    }
    
    // Convert trade ledger timestamp to a more readable format and aggregate
    let currentEquity = 0;
    const formattedData = data.map((trade, idx) => {
      currentEquity += trade.pnl; // assuming ledger stores individual PnL
      const date = new Date(trade.timestamp);
      const timeStr = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
      return {
        time: timeStr,
        equity: currentEquity,
        unrealized: currentEquity + currentUnrealized
      };
    });
    
    return formattedData;
  }, [data, currentUnrealized]);

  const latestEquity = chartData[chartData.length - 1]?.equity || 0;
  const isPositive = latestEquity >= 0;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis 
          dataKey="time" 
          stroke="#64748b" 
          fontSize={12} 
          tickLine={false} 
          axisLine={false}
          minTickGap={20}
        />
        <YAxis 
          stroke="#64748b" 
          fontSize={12} 
          tickLine={false} 
          axisLine={false}
          tickFormatter={(value) => `$${value.toLocaleString()}`}
        />
        <Tooltip 
          contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          itemStyle={{ color: '#0f172a', fontWeight: 'bold' }}
          formatter={(value) => [`$${value.toFixed(2)}`, 'Equity']}
        />
        <ReferenceLine y={0} stroke="#cbd5e1" strokeDasharray="3 3" />
        <Line 
          type="monotone" 
          dataKey="equity" 
          stroke={isPositive ? '#10b981' : '#ef4444'} 
          strokeWidth={3}
          dot={false}
          activeDot={{ r: 6, fill: isPositive ? '#10b981' : '#ef4444', stroke: '#ffffff', strokeWidth: 2 }}
        />
        {/* Optional: Show unrealized path */}
        <Line 
          type="stepAfter" 
          dataKey="unrealized" 
          stroke="#3b82f6" 
          strokeWidth={2}
          strokeDasharray="4 4"
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default PnLEquityCurve;
