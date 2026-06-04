import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Live ticker simulation hook.
 * Returns [tickers, flashMap] where flashMap tracks which ticker just changed direction.
 */
export function useLiveTickers(initialTickers, intervalMs = 2000) {
  const [tickers, setTickers] = useState(initialTickers);
  const [flashMap, setFlashMap] = useState({});

  useEffect(() => {
    const id = setInterval(() => {
      setTickers(prev => {
        const newFlash = {};
        const updated = prev.map(t => {
          const fluctuation = (Math.random() - 0.48) * t.price * 0.001;
          const newPrice = +(t.price + fluctuation).toFixed(
            t.price > 100 ? 2 : t.price > 10 ? 2 : 3
          );
          const newChange = +(t.change + fluctuation).toFixed(
            t.price > 100 ? 2 : t.price > 10 ? 2 : 3
          );
          const pctVal = ((newChange / (newPrice - newChange)) * 100);
          const dir = fluctuation >= 0 ? 'up' : 'down';
          newFlash[t.id] = dir;
          return {
            ...t,
            price: newPrice,
            change: newChange,
            pct: `${pctVal >= 0 ? '+' : ''}${pctVal.toFixed(2)}%`,
          };
        });
        // Update flash map on next microtask so the render catches it
        setTimeout(() => setFlashMap(newFlash), 0);
        setTimeout(() => setFlashMap({}), 600);
        return updated;
      });
    }, intervalMs);

    return () => clearInterval(id);
  }, [intervalMs]);

  return [tickers, flashMap];
}

/**
 * Live chart data simulation — appends a new point with realistic micro-fluctuation.
 * Only updates the last value in the array to simulate streaming.
 */
export function useLiveChartData(initialData, key, intervalMs = 3000, volatility = 0.0005) {
  const [data, setData] = useState(initialData);
  const dataRef = useRef(initialData);

  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  useEffect(() => {
    const id = setInterval(() => {
      setData(prev => {
        const updated = [...prev];
        const last = { ...updated[updated.length - 1] };
        if (typeof last[key] === 'number') {
          const fluctuation = (Math.random() - 0.48) * last[key] * volatility;
          last[key] = +(last[key] + fluctuation).toFixed(2);
        }
        updated[updated.length - 1] = last;
        return updated;
      });
    }, intervalMs);

    return () => clearInterval(id);
  }, [key, intervalMs, volatility]);

  return data;
}

/**
 * Live multi-key chart data simulation for charts with multiple series.
 */
export function useLiveMultiChartData(initialData, keys, intervalMs = 3000, volatility = 0.0005) {
  const [data, setData] = useState(initialData);

  useEffect(() => {
    const id = setInterval(() => {
      setData(prev => {
        const updated = [...prev];
        const last = { ...updated[updated.length - 1] };
        keys.forEach(k => {
          if (typeof last[k] === 'number') {
            const fluct = (Math.random() - 0.48) * Math.abs(last[k]) * volatility;
            last[k] = +(last[k] + fluct).toFixed(2);
          }
        });
        updated[updated.length - 1] = last;
        return updated;
      });
    }, intervalMs);

    return () => clearInterval(id);
  }, [keys.join(','), intervalMs, volatility]);

  return data;
}

/**
 * Live sentiment score simulation.
 */
export function useLiveSentiment(initialScore, intervalMs = 4000) {
  const [score, setScore] = useState(initialScore);
  const [flash, setFlash] = useState(null);

  useEffect(() => {
    const id = setInterval(() => {
      setScore(prev => {
        const delta = (Math.random() - 0.48) * 3;
        const next = Math.max(-100, Math.min(100, Math.round(prev + delta)));
        setFlash(delta >= 0 ? 'up' : 'down');
        setTimeout(() => setFlash(null), 500);
        return next;
      });
    }, intervalMs);

    return () => clearInterval(id);
  }, [intervalMs]);

  return [score, flash];
}
