/**
 * Central API client for the Oil Trading Dashboard.
 * All backend calls go through this module.
 * 
 * The backend returns APIResponse { data, provenance } where
 * provenance = { status, source, fetched_at, cache_age_seconds, message }
 */

const BASE_URL = 'http://localhost:8000/api/v1';

/** In-flight request deduplication map */
const _inflight = new Map();

/**
 * Generic fetch wrapper that extracts data from the APIResponse envelope.
 * - 15s timeout via AbortController
 * - Retries once on network errors (ERR_CONNECTION_RESET, etc.)
 * - Deduplicates identical in-flight requests
 * Returns { data, provenance } on success, or { data: null, provenance: null, error } on failure.
 */
async function apiFetch(endpoint) {
  // Deduplicate: if we already have an in-flight request for this endpoint, return its promise
  if (_inflight.has(endpoint)) {
    return _inflight.get(endpoint);
  }

  const promise = _apiFetchWithRetry(endpoint);
  _inflight.set(endpoint, promise);

  try {
    return await promise;
  } finally {
    _inflight.delete(endpoint);
  }
}

async function _apiFetchWithRetry(endpoint, retries = 1) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);

      const resp = await fetch(`${BASE_URL}${endpoint}`, { signal: controller.signal });
      clearTimeout(timeout);

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json = await resp.json();
      return {
        data: json.data,
        provenance: json.provenance || null,
        error: null,
      };
    } catch (err) {
      // On last attempt, return error gracefully
      if (attempt >= retries) {
        return {
          data: null,
          provenance: null,
          error: err.name === 'AbortError' ? 'Request timeout' : (err.message || 'Network error'),
        };
      }
      // Wait briefly before retry
      await new Promise(r => setTimeout(r, 500 + Math.random() * 500));
    }
  }
}

// ═══════════════════════════════════════════════════════════════
// Ticker Prices (yfinance + TwelveData DXY)
// ═══════════════════════════════════════════════════════════════

export async function fetchTickers() {
  return apiFetch('/tickers');
}

// ═══════════════════════════════════════════════════════════════
// Forward Curves
// ═══════════════════════════════════════════════════════════════

export async function fetchForwardCurves(commodity = 'wti') {
  return apiFetch(`/forward-curves/${commodity}`);
}

// ═══════════════════════════════════════════════════════════════
// Intraday VWAP
// ═══════════════════════════════════════════════════════════════

export async function fetchIntraday(commodity = 'wti') {
  return apiFetch(`/intraday/${commodity}`);
}

// ═══════════════════════════════════════════════════════════════
// Spreads
// ═══════════════════════════════════════════════════════════════

export async function fetchCalendarSpreads(commodity = 'wti', tenor = 'M1-M2') {
  return apiFetch(`/spreads/calendar/${commodity}?tenor=${tenor}`);
}

export async function fetchFlySpreads(commodity = 'wti') {
  return apiFetch(`/spreads/fly/${commodity}`);
}

export async function fetchPriceSpreads() {
  return apiFetch('/spreads/price-spreads');
}

// ═══════════════════════════════════════════════════════════════
// 5-Year Range
// ═══════════════════════════════════════════════════════════════

export async function fetchFiveYearRange(commodity = 'wti') {
  return apiFetch(`/five-year-range/${commodity}`);
}

// ═══════════════════════════════════════════════════════════════
// Core Desk Analytics
// ═══════════════════════════════════════════════════════════════

export async function fetchCovariance() {
  return apiFetch('/core-desk/covariance');
}

export async function fetchM1M12Heatmap() {
  return apiFetch('/core-desk/heatmap');
}

export async function fetchPCA(commodity = 'wti') {
  return apiFetch(`/core-desk/pca/${commodity}`);
}

export async function fetchDollarCorrelation() {
  return apiFetch('/core-desk/dollar-correlation');
}

export async function fetchWtiBrentArb() {
  return apiFetch('/core-desk/arb/wti-brent');
}

export async function fetchDifferentials() {
  return apiFetch('/core-desk/differentials');
}

export async function fetchCrackSpreads() {
  return apiFetch('/crack-spreads');
}

// ═══════════════════════════════════════════════════════════════
// Fundamentals
// ═══════════════════════════════════════════════════════════════

export async function fetchFundamentalsCards() {
  return apiFetch('/fundamentals/cards');
}

export async function fetchCushing() {
  return apiFetch('/fundamentals/cushing');
}

export async function fetchFloatingStorage() {
  return apiFetch('/fundamentals/floating-storage');
}

export async function fetchSpareCapacity() {
  return apiFetch('/fundamentals/spare-capacity');
}

// ═══════════════════════════════════════════════════════════════
// Positioning & Flows
// ═══════════════════════════════════════════════════════════════

export async function fetchCOT(weeks = 12) {
  return apiFetch(`/cot/positioning?weeks=${weeks}`);
}

export async function fetchBDTI() {
  return apiFetch('/freight/bdti');
}

// ═══════════════════════════════════════════════════════════════
// STEO Balance
// ═══════════════════════════════════════════════════════════════

export async function fetchSTEO() {
  return apiFetch('/steo/balance');
}

// ═══════════════════════════════════════════════════════════════
// Macro & Seasonality
// ═══════════════════════════════════════════════════════════════

export async function fetchSeasonality(commodity = 'wti') {
  return apiFetch(`/macro/seasonality/${commodity}`);
}

export async function fetchHeatmap(commodity = 'wti') {
  return apiFetch(`/macro/heatmap/${commodity}`);
}

export async function fetchWeeklyMetrics() {
  return apiFetch('/macro/weekly-metrics');
}

// ═══════════════════════════════════════════════════════════════
// Sentiment & News
// ═══════════════════════════════════════════════════════════════

export async function fetchSentiment() {
  return apiFetch('/sentiment/aggregate');
}

export async function fetchNews(limit = 20) {
  return apiFetch(`/sentiment/latest?limit=${limit}`);
}

export async function fetchTradeSignals() {
  return apiFetch('/signals/trade');
}

// ═══════════════════════════════════════════════════════════════
// Health
// ═══════════════════════════════════════════════════════════════

export async function fetchHealth() {
  return apiFetch('/health');
}
