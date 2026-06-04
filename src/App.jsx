import React from 'react';
import GlobalHeader from './components/GlobalHeader';
import TradingViewCharts from './components/TradingViewCharts';
import IntradayVWAP from './components/IntradayVWAP';
import SpreadAndFly from './components/SpreadAndFly';
import FiveYearRange from './components/FiveYearRange';
import CoreTradingDesk from './components/CoreTradingDesk';
import COTPositioning from './components/COTPositioning';
import BDTIFreight from './components/BDTIFreight';
import STEOBalance from './components/STEOBalance';
import MacroSentiments from './components/MacroSentiments';

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
        {/* Live TradingView Charts */}
        <SectionDivider label="Live Markets" />
        <TradingViewCharts />

        {/* Intraday VWAP + Bollinger Bands */}
        <SectionDivider label="Intraday VWAP & Bollinger Bands" />
        <IntradayVWAP />

        {/* Brent-WTI Spread & Butterfly */}
        <SectionDivider label="Spread & Fly" />
        <SpreadAndFly />

        {/* 5-Year Same-Week Range */}
        <SectionDivider label="5-Year Same-Week Range" />
        <FiveYearRange />

        {/* Core Trading Desk */}
        <SectionDivider label="Core Trading Desk" />
        <CoreTradingDesk />

        {/* Positioning & Flows */}
        <SectionDivider label="Positioning & Flows" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
          <COTPositioning />
          <BDTIFreight />
        </div>

        {/* Global Oil Balance */}
        <SectionDivider label="Global Oil Balance — EIA STEO" />
        <STEOBalance />

        {/* Macro Sentiments & Seasonality */}
        <SectionDivider label="Macro Sentiments & Seasonality" />
        <MacroSentiments />
      </main>

      {/* Footer */}
      <footer className="text-center py-4 px-5 text-[11px] text-slate-400 border-t border-slate-200 bg-white">
        Quant Oil Desk · Data as of {new Date().toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })} · All values simulated
      </footer>
    </div>
  );
}
