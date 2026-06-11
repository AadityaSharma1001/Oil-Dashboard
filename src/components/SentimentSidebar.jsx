import React, { memo, useCallback, useMemo } from 'react';
import Card from './Card';
import { useApiData } from '../hooks/useApiData';
import { fetchSentiment, fetchNews, fetchFundamentalsCards } from '../api';
import { FUNDAMENTALS_CARDS, NEWS_ITEMS } from '../data/mockData';

/* ── Sentiment Gauge ─────────────────────────────────────────── */
const SentimentGauge = memo(() => {
  const fetchFn = useCallback(() => fetchSentiment(), []);
  const { data: apiData, source } = useApiData(fetchFn, { refreshInterval: 60000 });
  
  const compound = apiData?.overall_compound || 0;
  const score = Math.round(compound * 100);
  const pct = ((score + 100) / 200) * 100;
  
  const label = apiData?.overall_bias ? 
    apiData.overall_bias.charAt(0).toUpperCase() + apiData.overall_bias.slice(1) 
    : (score > 50 ? 'Bullish' : score > 15 ? 'Slightly Bullish' : score > -15 ? 'Neutral' : score > -50 ? 'Slightly Bearish' : 'Bearish');
    
  const scoreColor = score >= 0 ? 'text-emerald-700' : 'text-red-700';

  return (
    <Card title="Aggregate Sentiment" badge="Live" badgeVariant="blue" source={source}>
      <div>
        <div className="relative h-6 rounded-md overflow-hidden" style={{ background: 'linear-gradient(to right, rgba(229,57,53,0.12), #F8F9FA 40%, #F8F9FA 60%, rgba(76,175,80,0.12))' }}>
          <div className="absolute top-[-1px] w-[3px] h-[28px] bg-slate-900 rounded transition-all duration-600" style={{ left: `calc(${pct}% - 1.5px)` }} />
        </div>
        <div className="flex justify-between text-[9px] text-slate-400 font-medium mt-0.5">
          <span>Bearish</span><span>Neutral</span><span>Bullish</span>
        </div>
        <div className="text-center mt-1">
          <div className={`text-xl font-bold tabular-nums transition-colors duration-500 ${scoreColor}`}>
            {score > 0 ? '+' : ''}{score}
          </div>
          <div className="text-[10px] text-slate-500 font-medium">{label}</div>
        </div>
      </div>
    </Card>
  );
});

/* ── Fundamentals Signals ────────────────────────────────────── */
const SIGNAL_CONFIG = {
  us_stocks:  { bearishWhen: 'up',   label: 'US Crude Stocks',    desc: 'vs 5yr avg' },
  cushing:    { bearishWhen: 'up',   label: 'Cushing',            desc: 'vs 5yr avg' },
  production: { bearishWhen: 'up',   label: 'US Production',      desc: 'weekly change' },
  ref_util:   { bearishWhen: 'down', label: 'Refinery Util.',     desc: 'weekly change' },
  opec_prod:  { bearishWhen: 'up',   label: 'OPEC Production',    desc: 'vs quota' },
  rig_count:  { bearishWhen: 'up',   label: 'Rig Count',          desc: 'weekly change' },
  spr:        { bearishWhen: 'down', label: 'SPR Level',          desc: 'releases' },
  imports:    { bearishWhen: 'up',   label: 'Net Imports',        desc: 'weekly change' },
};

const FundamentalsSignals = memo(() => {
  const { data: apiData } = useApiData(fetchFundamentalsCards, { fallback: null, refreshInterval: 60000 });
  const cards = apiData?.cards || FUNDAMENTALS_CARDS;
  
  const signals = useMemo(() => {
    return cards.map(card => {
      const config = SIGNAL_CONFIG[card.id] || { bearishWhen: 'up', label: card.label, desc: '' };
      const change = card.change || 0;
      
      // Determine signal direction based on the indicator
      let signal;
      if (config.bearishWhen === 'up') {
        signal = change > 0 ? 'bearish' : change < 0 ? 'bullish' : 'neutral';
      } else {
        signal = change < 0 ? 'bearish' : change > 0 ? 'bullish' : 'neutral';
      }
      
      return {
        id: card.id,
        label: config.label,
        value: card.value,
        unit: card.unit,
        change: change,
        signal,
        desc: config.desc,
      };
    });
  }, [cards]);

  const bullCount = signals.filter(s => s.signal === 'bullish').length;
  const bearCount = signals.filter(s => s.signal === 'bearish').length;

  return (
    <Card 
      title="Fundamentals Bias" 
      badge={
        <span className={`font-bold ${bullCount > bearCount ? 'text-emerald-600' : bearCount > bullCount ? 'text-red-600' : 'text-slate-500'}`}>
          {bullCount > bearCount ? '▲ Net Bullish' : bearCount > bullCount ? '▼ Net Bearish' : '— Neutral'}
        </span>
      }
    >
      <div className="flex items-center justify-between mb-2.5 px-1">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-[10px] font-semibold text-emerald-700">{bullCount} Bullish</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-red-500" />
          <span className="text-[10px] font-semibold text-red-700">{bearCount} Bearish</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-slate-400" />
          <span className="text-[10px] font-semibold text-slate-500">{signals.length - bullCount - bearCount} Neutral</span>
        </div>
      </div>
      <div className="flex flex-col gap-0.5">
        {signals.map(s => (
          <div key={s.id} className={`flex items-center gap-2 px-2 py-1.5 rounded text-[11px] transition-colors ${
            s.signal === 'bullish' ? 'bg-emerald-50/60' : s.signal === 'bearish' ? 'bg-red-50/60' : 'bg-slate-50'
          }`}>
            <span className={`text-xs font-bold w-4 text-center ${
              s.signal === 'bullish' ? 'text-emerald-600' : s.signal === 'bearish' ? 'text-red-600' : 'text-slate-400'
            }`}>
              {s.signal === 'bullish' ? '▲' : s.signal === 'bearish' ? '▼' : '—'}
            </span>
            <span className="flex-1 font-medium text-slate-700 truncate">{s.label}</span>
            <span className="tabular-nums font-semibold text-slate-600">{s.value}<span className="text-[9px] text-slate-400 ml-0.5">{s.unit}</span></span>
            <span className={`tabular-nums text-[10px] font-bold min-w-[36px] text-right ${
              s.change > 0 ? 'text-emerald-600' : s.change < 0 ? 'text-red-600' : 'text-slate-400'
            }`}>
              {s.change > 0 ? '+' : ''}{typeof s.change === 'number' ? s.change.toFixed(1) : s.change}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
});

/* ── News Stream ─────────────────────────────────────────────── */
const CATEGORY_CLASSES = {
  OPEC: 'bg-blue-50 text-blue-900',
  Geopolitical: 'bg-amber-50 text-amber-700',
  Demand: 'bg-teal-50 text-teal-700',
  Macro: 'bg-purple-50 text-purple-700',
};

const CompactNewsStream = memo(() => {
  const fetchFn = useCallback(() => fetchNews(15), []);
  const { data: apiData, source } = useApiData(fetchFn, { refreshInterval: 60000 });
  const articles = apiData?.articles || NEWS_ITEMS;

  return (
    <Card title="News Stream" badge="Live feed" source={source}>
      <div className="flex flex-col gap-0 max-h-[520px] overflow-y-auto scrollbar-hide">
        {articles.map((n, i) => {
          const type = n.label === 'positive' || (n.type && n.type === 'bullish') ? 'bullish' : n.label === 'negative' || (n.type && n.type === 'bearish') ? 'bearish' : 'neutral';
          const impact = n.impact_score || n.impact || '+0';
          
          return (
            <div key={n.id || i} className="flex items-start gap-2 px-1.5 py-2 border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
              <div className="text-[9px] text-slate-400 font-medium w-8 shrink-0 pt-0.5 tabular-nums">
                {n.published_at ? new Date(n.published_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : n.time}
              </div>
              <div className="flex-1 min-w-0">
                <a href={n.url} target="_blank" rel="noreferrer" className="block text-[11px] font-medium text-slate-700 leading-snug mb-0.5 hover:text-blue-700 transition-colors line-clamp-2">
                  {n.headline}
                </a>
                <div className="flex items-center gap-1.5">
                  <span className={`text-[8px] font-semibold uppercase tracking-[0.5px] px-1 py-px rounded ${CATEGORY_CLASSES[n.category] || 'bg-slate-100 text-slate-600'}`}>
                    {n.category || 'General'}
                  </span>
                  {type !== 'neutral' && (
                    <span className={`text-[9px] font-semibold tabular-nums ${type === 'bullish' ? 'text-emerald-700' : 'text-red-700'}`}>
                      {type === 'bullish' ? '▲' : '▼'} {type === 'bullish' ? 'Bullish' : 'Bearish'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
});

/* ── Sidebar Export ───────────────────────────────────────────── */
const SentimentSidebar = memo(function SentimentSidebar() {
  return (
    <div className="flex flex-col gap-3.5 sticky top-4">
      <SentimentGauge />
      <FundamentalsSignals />
      <CompactNewsStream />
    </div>
  );
});

export default SentimentSidebar;
