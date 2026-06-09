import React, { useEffect, useRef, memo } from 'react';

const TradingViewWidget = memo(function TradingViewWidget({ symbol, title }) {
  const containerRef = useRef(null);
  const isMountedRef = useRef(false);

  useEffect(() => {
    if (!containerRef.current || isMountedRef.current) return;
    isMountedRef.current = true;

    containerRef.current.innerHTML = '';

    const widgetDiv = document.createElement('div');
    widgetDiv.className = 'tradingview-widget-container__widget';
    widgetDiv.style.height = '100%';
    widgetDiv.style.width = '100%';
    containerRef.current.appendChild(widgetDiv);

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.type = 'text/javascript';
    script.async = true;
    script.textContent = JSON.stringify({
      autosize: true,
      symbol: symbol,
      interval: '60',
      timezone: 'Etc/UTC',
      theme: 'light',
      style: '1',
      locale: 'en',
      backgroundColor: 'rgba(255, 255, 255, 1)',
      gridColor: 'rgba(233, 236, 239, 0.5)',
      hide_top_toolbar: false,
      hide_legend: false,
      allow_symbol_change: false,
      save_image: false,
      calendar: false,
      support_host: 'https://www.tradingview.com',
    });
    containerRef.current.appendChild(script);
  }, [symbol]);

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
      <div className="px-3.5 py-2.5 border-b border-slate-100">
        <h3 className="text-[12.5px] font-semibold text-slate-700">{title}</h3>
      </div>
      <div
        className="tradingview-widget-container"
        ref={containerRef}
        style={{ height: 850, width: '100%' }}
      />
    </div>
  );
});

const TradingViewCharts = memo(function TradingViewCharts() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
      <TradingViewWidget symbol="TVC:USOIL" title="WTI Crude Oil — Live" />
      <TradingViewWidget symbol="TVC:UKOIL" title="Brent Crude Oil — Live" />
    </div>
  );
});

export default TradingViewCharts;
