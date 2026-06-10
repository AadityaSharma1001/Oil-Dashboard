import React, { memo, useState, useMemo, useCallback } from 'react';
import {
  LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import Card from './Card';
import { useLiveChartData, useLiveSentiment } from '../hooks/useLiveData';
import { useApiData } from '../hooks/useApiData';
import { fetchSeasonality, fetchHeatmap, fetchWeeklyMetrics, fetchSentiment, fetchNews } from '../api';
import {
  SEASONALITY_DATA, HEATMAP_MONTHS, HEATMAP_YEARS, HEATMAP_RETURNS,
  SEASONAL_METRICS, INITIAL_SENTIMENT_SCORE, SENTIMENT_TREND_DATA,
  NEWS_ITEMS, KEYWORD_DATA,
} from '../data/mockData';

const AXIS_STYLE = { fontSize: 10, fill: '#868E96' };
const GRID_STYLE = { stroke: 'rgba(0,0,0,0.04)' };

const CustomTooltip = ({ active, payload, label, prefix = '$' }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-[11px] px-2.5 py-1.5 rounded-md shadow-lg">
      <div className="font-semibold text-slate-300 mb-0.5">{label}</div>
      {payload.filter(p => p.value != null).map((p, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-400">{p.name}:</span>
          <span className="font-semibold tabular-nums">{prefix}{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

/* ═══════════════════════ Seasonality Chart Removed ═══════════════════ */

/* ═══════════════════════ Seasonal Heatmap ════════════════════ */
const SeasonalHeatmap = memo(({ commodity, setCommodity }) => {
  const [hoverCell, setHoverCell] = useState(null);
  
  const fetchMap = useCallback(() => fetchHeatmap(commodity), [commodity]);
  const { data: apiData, source } = useApiData(fetchMap, { refreshInterval: 600000 });
  
  const heatmapYears = apiData?.years || HEATMAP_YEARS;
  const heatmapReturns = apiData?.returns || HEATMAP_RETURNS;

  const allVals = useMemo(() => heatmapReturns.flat().filter(v => v !== null), [heatmapReturns]);
  const min = Math.min(...allVals, -10);
  const max = Math.max(...allVals, 10);

  const heatColor = (val) => {
    if (val === null) return { bg: '#F8F9FA', text: '#ADB5BD' };
    const t = (val - min) / (max - min);
    if (t < 0.45) {
      const intensity = 1 - t / 0.45;
      return { bg: `rgba(229,57,53,${0.06 + intensity * 0.14})`, text: intensity > 0.5 ? '#C62828' : '#495057' };
    } else if (t > 0.55) {
      const intensity = (t - 0.55) / 0.45;
      return { bg: `rgba(76,175,80,${0.06 + intensity * 0.14})`, text: intensity > 0.5 ? '#2E7D32' : '#495057' };
    }
    return { bg: '#F8F9FA', text: '#495057' };
  };

  return (
    <Card 
      title={
        <div className="flex items-center gap-3">
          <span>Monthly % Returns</span>
          <div className="flex bg-slate-100 rounded p-0.5">
            <button
              onClick={() => setCommodity('wti')}
              className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded transition-colors ${commodity === 'wti' ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'}`}
            >
              WTI
            </button>
            <button
              onClick={() => setCommodity('brent')}
              className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded transition-colors ${commodity === 'brent' ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'}`}
            >
              Brent
            </button>
          </div>
        </div>
      }
      badge="Last 5 Years" 
      source={source}
    >
      <div className="overflow-x-auto">
        <table className="w-full border-separate" style={{ borderSpacing: '3px' }}>
          <thead>
            <tr>
              <th className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.3px] p-1" />
              {HEATMAP_MONTHS.map((m, ci) => (
                <th key={m} className={`text-[10px] font-semibold uppercase tracking-[0.3px] p-1 text-center transition-colors ${hoverCell?.c === ci ? 'text-blue-900' : 'text-slate-500'}`}>{m}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {heatmapYears.map((yr, ri) => (
              <tr key={yr}>
                <td className={`text-[11px] font-semibold text-right pr-2.5 transition-colors ${hoverCell?.r === ri ? 'text-blue-900' : 'text-slate-500'}`}>{yr}</td>
                {heatmapReturns[ri].map((val, ci) => {
                  const c = heatColor(val);
                  const isHovered = hoverCell?.r === ri && hoverCell?.c === ci;
                  const isRowCol = hoverCell && (hoverCell.r === ri || hoverCell.c === ci);
                  return (
                    <td
                      key={ci}
                      onMouseEnter={() => setHoverCell({ r: ri, c: ci })}
                      onMouseLeave={() => setHoverCell(null)}
                      className={`text-center py-2 px-1 text-[11px] font-semibold rounded tabular-nums cursor-default transition-all duration-150
                        ${isHovered ? 'scale-110 shadow-md ring-2 ring-blue-300 z-10 relative' : ''}
                        ${isRowCol && !isHovered ? 'brightness-95' : ''}
                      `}
                      style={{ background: c.bg, color: c.text }}
                    >
                      {val !== null ? `${val >= 0 ? '+' : ''}${val.toFixed(1)}%` : '—'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
});

/* ── Seasonal Metrics Sidebar ────────────────────────────────── */
const SeasonalMetricsSidebar = memo(({ commodity }) => {
  const fetchMet = useCallback(() => fetchWeeklyMetrics(commodity), [commodity]);
  const { data: apiData } = useApiData(fetchMet, { refreshInterval: 600000 });
  const d = apiData || SEASONAL_METRICS;
  
  return (
    <Card title="Weekly Metrics">
      <div className="flex flex-col gap-3">
        <div className="bg-slate-50 border border-slate-200 rounded p-3">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px] mb-1">Current Week</div>
          <div className="text-xl font-bold text-slate-800">Week {d.currentWeek}</div>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded p-3">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px] mb-1">Week Performance</div>
          <div className="text-xl font-bold text-emerald-700">{d.currentPerf}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">vs Historical Median: {d.historicalMedian}</div>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded p-3">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-[0.5px] mb-1">Deviation from Median</div>
          <div className="text-xl font-bold text-emerald-700">{d.deviation}</div>
        </div>
        <div className={`p-3 rounded text-[11.5px] font-medium leading-relaxed border ${
          d.banner === 'bullish'
            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
            : 'bg-red-50 text-red-800 border-red-200'
        }`}>
          <strong>⚑ Seasonal Alert:</strong> {d.bannerText}
        </div>
      </div>
    </Card>
  );
});

/* ═══════════════════════ Sentiment Gauge ═════════════════════ */
const SentimentPanel = memo(() => {
  const [score, flash] = useLiveSentiment(INITIAL_SENTIMENT_SCORE, 4000);
  const pct = ((score + 100) / 200) * 100;
  const label = score > 50 ? 'Bullish' : score > 15 ? 'Slightly Bullish' : score > -15 ? 'Neutral' : score > -50 ? 'Slightly Bearish' : 'Bearish';
  const scoreColor = score >= 0 ? 'text-emerald-700' : 'text-red-700';

  return (
    <Card title="Aggregate Sentiment" badge="Slightly Bullish" badgeVariant="blue">
      <div className="mb-4">
        <div className="relative h-7 rounded-md overflow-hidden" style={{ background: 'linear-gradient(to right, rgba(229,57,53,0.1), #F8F9FA 40%, #F8F9FA 60%, rgba(76,175,80,0.1))' }}>
          <div className="absolute top-[-2px] w-[3px] h-[30px] bg-slate-900 rounded transition-all duration-600" style={{ left: `calc(${pct}% - 1.5px)` }} />
        </div>
        <div className="flex justify-between text-[10px] text-slate-500 font-medium mt-1">
          <span>-100 Bearish</span><span>Neutral</span><span>+100 Bullish</span>
        </div>
        <div className="text-center mt-2">
          <div className={`text-2xl font-bold tabular-nums transition-colors duration-500 ${
            flash === 'up' ? 'text-emerald-500' : flash === 'down' ? 'text-red-500' : scoreColor
          }`}>
            {score >= 0 ? '+' : ''}{score}
          </div>
          <div className="text-[11px] text-slate-500 font-medium">{label}</div>
        </div>
      </div>
      <div className="h-[140px]" style={{ minHeight: 140 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={SENTIMENT_TREND_DATA}>
            <defs>
              <linearGradient id="sentGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4CAF50" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#4CAF50" stopOpacity={0.01} />
              </linearGradient>
            </defs>
            <XAxis dataKey="hour" tick={AXIS_STYLE} interval={5} />
            <YAxis hide domain={[-10, 60]} />
            <Tooltip content={<CustomTooltip prefix="" />} />
            <Area dataKey="value" name="Sentiment" stroke="#4CAF50" fill="url(#sentGrad)" strokeWidth={1.5} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
});

/* ═══════════════════════ News Stream ═════════════════════════ */
const CATEGORY_CLASSES = {
  OPEC: 'bg-blue-50 text-blue-900',
  Geopolitical: 'bg-amber-50 text-amber-700',
  Demand: 'bg-teal-50 text-teal-700',
  Macro: 'bg-purple-50 text-purple-700',
};

const NewsStream = memo(() => (
  <Card title="News Stream" badge="Simulated Headlines">
    <div className="flex flex-col gap-0.5 max-h-[360px] overflow-y-auto scrollbar-hide">
      {NEWS_ITEMS.map(n => (
        <div key={n.id} className="flex items-start gap-2.5 px-2 py-2.5 rounded hover:bg-slate-50 hover:translate-x-1 hover:shadow transition-all duration-200 cursor-default group">
          <span className="text-[10px] text-slate-400 font-medium w-9 shrink-0 pt-0.5 tabular-nums">{n.time}</span>
          <div className="flex-1">
            <div className="text-[12px] font-medium text-slate-700 leading-snug mb-1 group-hover:text-slate-900 transition-colors">{n.headline}</div>
            <div className="flex items-center gap-2">
              <span className={`text-[9.5px] font-semibold uppercase tracking-[0.5px] px-1.5 py-px rounded ${CATEGORY_CLASSES[n.category] || ''}`}>{n.category}</span>
              <span className={`text-[10.5px] font-semibold tabular-nums ${n.type === 'bullish' ? 'text-emerald-700' : 'text-red-700'}`}>
                {n.impact} {n.type === 'bullish' ? 'Bullish' : 'Bearish'}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  </Card>
));

/* ═══════════════════════ Keyword Tracker ═════════════════════ */
const KeywordTracker = memo(() => {
  const maxMentions = Math.max(...KEYWORD_DATA.map(k => k.mentions));
  return (
    <Card title="Trending Keywords" badge="Sorted by Mention Volume">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5">
        {KEYWORD_DATA.map((k, i) => (
          <div key={k.keyword} className="flex items-center gap-2.5 px-2.5 py-2 rounded hover:bg-slate-50 transition-colors">
            <span className="text-[10px] font-bold text-slate-300 w-4 text-center tabular-nums">{i + 1}</span>
            <span className="text-[12px] font-semibold text-slate-700 min-w-[120px] shrink-0">{k.keyword}</span>
            <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700" style={{ width: `${(k.mentions / maxMentions) * 100}%`, background: k.color }} />
            </div>
            <span className="text-[10px] font-medium text-slate-400 w-7 text-right tabular-nums">{k.mentions}</span>
          </div>
        ))}
      </div>
    </Card>
  );
});


/* ═══════════════════════ Main Tab Export ══════════════════════ */
const SectionTitle = ({ children }) => (
  <h2 className="text-[11px] font-semibold uppercase tracking-[1.2px] text-slate-400 mb-2.5 pl-0.5">{children}</h2>
);

const MacroSentiments = memo(function MacroSentiments() {
  const [commodity, setCommodity] = useState('wti');

  return (
    <div className="space-y-5 animate-fadeIn">
      <section>
        <SectionTitle>Seasonal Heatmap & Metrics</SectionTitle>
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-3.5">
          <SeasonalHeatmap commodity={commodity} setCommodity={setCommodity} />
          <SeasonalMetricsSidebar commodity={commodity} />
        </div>
      </section>

      <section>
        <SectionTitle>Sentiment Analysis & News Stream</SectionTitle>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
          <SentimentPanel />
          <NewsStream />
        </div>
      </section>

      <section>
        <SectionTitle>Entity Weight Tracker</SectionTitle>
        <KeywordTracker />
      </section>
    </div>
  );
});

export default MacroSentiments;
