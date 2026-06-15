import React from 'react';
import GlobalHeader from './components/GlobalHeader';
import IntradayVWAP from './components/IntradayVWAP';
import SpreadAndFly from './components/SpreadAndFly';
import FiveYearRange from './components/FiveYearRange';
import CoreTradingDesk from './components/CoreTradingDesk';
import COTPositioning from './components/COTPositioning';
import STEOBalance from './components/STEOBalance';
import MacroSentiments from './components/MacroSentiments';
import StormTracker from './components/StormTracker';
import SentimentSidebar from './components/SentimentSidebar';
import TradingDashboard from './components/trading/TradingDashboard';

const SectionDivider = ({ label }) => (
  <div className="flex items-center gap-4 pt-6 pb-2">
    <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
    <span className="text-[11px] font-bold uppercase tracking-[2px] text-slate-400 shrink-0">{label}</span>
    <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
  </div>
);

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      <GlobalHeader />

      <main className="max-w-[1600px] mx-auto px-5 py-4 pb-10 space-y-2">
        {/* Quantitative Trading Engine */}
        <div className="mb-8">
          <TradingDashboard />
        </div>

        {/* ─── Top Section: Charts (left) + Sentiment Sidebar (right) ─── */}
        <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-4">
          {/* Left: Intraday Charts, Spread & Fly, 5-Year Range */}
          <div className="space-y-2">
            <SectionDivider label="Intraday VWAP & Z-Score" />
            <IntradayVWAP />

            <SectionDivider label="Spread & Fly" />
            <SpreadAndFly />

            <SectionDivider label="5-Year Same-Week Range" />
            <FiveYearRange />
          </div>

          {/* Right: Sentiment Sidebar */}
          <div className="pt-8">
            <div className="flex items-center gap-4 pb-2 mb-2">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
              <span className="text-[11px] font-bold uppercase tracking-[2px] text-slate-400 shrink-0">Sentiment & Signals</span>
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
            </div>
            <SentimentSidebar />
          </div>
        </div>

        {/* Core Trading Desk */}
        <SectionDivider label="Core Trading Desk" />
        <CoreTradingDesk />

        {/* Positioning & Flows */}
        <SectionDivider label="Positioning & Flows" />
        <div className="grid grid-cols-1 gap-3.5">
          <COTPositioning />
        </div>

        {/* Global Oil Balance */}
        <SectionDivider label="Global Oil Balance — EIA STEO" />
        <STEOBalance />

        {/* Macro Sentiments & Seasonality */}
        <SectionDivider label="Macro Sentiments & Seasonality" />
        <MacroSentiments />

        {/* Storm Tracker & Impact */}
        <SectionDivider label="Live Storm Tracker & Gulf Impacts" />
        <StormTracker />
      </main>

      {/* Footer */}
      <footer className="text-center py-4 px-5 text-[11px] text-slate-400 border-t border-slate-200 bg-white">
        Quant Oil Desk · Data as of {new Date().toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })} · All values simulated
      </footer>
    </div>
  );
}
