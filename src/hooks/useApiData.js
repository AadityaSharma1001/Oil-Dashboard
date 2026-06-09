import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Generic hook to fetch data from the backend API with:
 * - Auto-refresh on interval
 * - Graceful fallback to provided mock data
 * - Loading / error / provenance state
 *
 * @param {Function} fetchFn - Async function from api.js (e.g., fetchTickers)
 * @param {Object} options
 * @param {any} options.fallback - Mock data to use when API fails
 * @param {number} options.refreshInterval - Auto-refresh interval in ms (0 = no refresh)
 * @param {any[]} options.deps - Dependency array for re-fetching
 * @returns {{ data, loading, error, provenance, source }}
 */
export function useApiData(fetchFn, { fallback = null, refreshInterval = 0, deps = [] } = {}) {
  const [data, setData] = useState(fallback);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [provenance, setProvenance] = useState(null);
  const mountedRef = useRef(true);

  const doFetch = useCallback(async () => {
    try {
      const result = await fetchFn();
      if (!mountedRef.current) return;

      if (result.error || result.data === null || result.data === undefined) {
        // API failed — keep existing data or use fallback
        setError(result.error || 'No data');
        if (data === null || data === fallback) {
          setData(fallback);
        }
        setProvenance(result.provenance || { status: 'mock', source: 'fallback' });
      } else {
        setData(result.data);
        setError(null);
        setProvenance(result.provenance);
      }
    } catch (err) {
      if (!mountedRef.current) return;
      setError(err.message);
      if (data === null) setData(fallback);
      setProvenance({ status: 'mock', source: 'fallback' });
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchFn, ...deps]);

  useEffect(() => {
    mountedRef.current = true;

    // Stagger initial fetch to prevent thundering herd on page load
    const staggerDelay = Math.random() * 2000;
    const initialTimeout = setTimeout(() => {
      if (mountedRef.current) doFetch();
    }, staggerDelay);

    let intervalId;
    if (refreshInterval > 0) {
      // Start the interval after the staggered initial fetch
      intervalId = setInterval(doFetch, refreshInterval);
    }

    return () => {
      mountedRef.current = false;
      clearTimeout(initialTimeout);
      if (intervalId) clearInterval(intervalId);
    };
  }, [doFetch, refreshInterval]);

  // Derive source status: 'live', 'mock', 'stale', 'degraded'
  const source = provenance?.status || (error ? 'mock' : 'live');

  return { data, loading, error, provenance, source };
}


/**
 * Specialized hook for the ticker strip in GlobalHeader.
 * Fetches tickers from the API every `intervalMs`, and manages flash map
 * for direction indicators (up/down color flashes).
 *
 * @param {Array} initialTickers - Fallback mock tickers
 * @param {number} intervalMs - Refresh interval in ms
 * @returns {[Array, Object, string]} [tickers, flashMap, source]
 */
export function useApiTickers(initialTickers, intervalMs = 5000) {
  const [tickers, setTickers] = useState(initialTickers);
  const [flashMap, setFlashMap] = useState({});
  const [source, setSource] = useState('loading');
  const prevPricesRef = useRef({});

  useEffect(() => {
    let mounted = true;

    // Build initial price map
    const priceMap = {};
    initialTickers.forEach(t => { priceMap[t.id] = t.price; });
    prevPricesRef.current = priceMap;

    const fetchAndUpdate = async () => {
      try {
        // Dynamic import to avoid circular deps
        const { fetchTickers } = await import('../api');
        const result = await fetchTickers();

        if (!mounted) return;

        if (result.data && Array.isArray(result.data) && result.data.length > 0) {
          const newFlash = {};
          const newPrices = {};

          result.data.forEach(t => {
            const prev = prevPricesRef.current[t.id];
            if (prev !== undefined && prev !== t.price) {
              newFlash[t.id] = t.price > prev ? 'up' : 'down';
            }
            newPrices[t.id] = t.price;
          });

          prevPricesRef.current = newPrices;
          setTickers(result.data);
          setFlashMap(newFlash);
          setSource(result.provenance?.status || 'live');

          // Clear flash after animation
          setTimeout(() => {
            if (mounted) setFlashMap({});
          }, 600);
        } else {
          // API returned empty — keep current data, mark as mock
          setSource('mock');
        }
      } catch {
        if (mounted) setSource('mock');
      }
    };

    // Initial fetch
    fetchAndUpdate();

    // Periodic refresh
    const id = setInterval(fetchAndUpdate, intervalMs);

    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [intervalMs]); // eslint-disable-line react-hooks/exhaustive-deps

  return [tickers, flashMap, source];
}
