// ══════════════════════════════════════════════════════════════════
//  MOCK DATA — Swap these for real REST / WebSocket endpoints
// ══════════════════════════════════════════════════════════════════

/* ── Global Header Tickers ───────────────────────────────────── */
export const INITIAL_TICKERS = [
  { id: 'wti',    label: 'WTI M1',     price: 72.45, change: +0.83, pct: '+1.16%' },
  { id: 'brent',  label: 'Brent M1',   price: 76.30, change: +0.65, pct: '+0.86%' },
  { id: 'rbob',   label: 'RBOB',       price: 2.342, change: -0.018, pct: '-0.76%' },
  { id: 'ho',     label: 'Heat Oil',   price: 2.485, change: +0.012, pct: '+0.48%' },
  { id: 'gasoil', label: 'ICE Gasoil', price: 684.50, change: +3.25, pct: '+0.48%' },
  { id: 'natgas', label: 'Nat Gas',    price: 2.78,  change: -0.06, pct: '-2.11%' },
  { id: 'dxy',    label: 'DXY',        price: 104.21, change: -0.32, pct: '-0.31%' },
  { id: 'bwsprd', label: 'B-W Sprd',   price: 3.85,  change: +0.18, pct: '+4.91%' },
  { id: 'rigs',   label: 'Rig Count',  price: 584,   change: -3, pct: '-0.51%' },
];

/* ── Tab 1: Forward Curve ────────────────────────────────────── */
export const FWD_CURVE_MONTHS = Array.from({ length: 35 }, (_, i) => `M${i + 1}`);

function generateCurvedData(basePrice, numMonths) {
  return Array.from({ length: numMonths }, (_, i) => {
    const decay = 0.15 * (1 - Math.exp(-i / 12));
    const avgDecay = 0.10 * (1 - Math.exp(-i / 12));
    const current = +(basePrice * (1 - decay)).toFixed(2);
    const avg5yr = +(basePrice * 0.94 * (1 - avgDecay)).toFixed(2);
    return { month: `M${i + 1}`, current, avg5yr };
  });
}

export const FWD_CURVE_DATA = generateCurvedData(72.45, 35);
export const BRENT_FWD_CURVE_DATA = generateCurvedData(76.30, 35);

/* ── Tab 1: Near-Term Spreads ────────────────────────────────── */
function generateDays(n) {
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() - (n - 1) + i);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
}

const SPREAD_DAYS_60 = generateDays(60);
const M1M2 = [0.35,0.38,0.32,0.40,0.42,0.37,0.30,0.28,0.33,0.36,0.41,0.45,0.48,0.44,0.39,0.35,0.31,0.29,0.34,0.38,0.42,0.46,0.50,0.47,0.43,0.38,0.34,0.30,0.35,0.39,0.43,0.47,0.51,0.48,0.44,0.40,0.36,0.33,0.37,0.41,0.45,0.49,0.52,0.48,0.44,0.40,0.37,0.34,0.38,0.42,0.46,0.50,0.53,0.49,0.45,0.41,0.38,0.35,0.39,0.43];
const M1M3 = [0.65,0.70,0.62,0.74,0.78,0.68,0.58,0.54,0.62,0.68,0.76,0.82,0.88,0.82,0.74,0.66,0.60,0.56,0.64,0.72,0.80,0.86,0.92,0.86,0.78,0.70,0.64,0.58,0.66,0.74,0.82,0.88,0.94,0.88,0.80,0.74,0.68,0.62,0.70,0.78,0.86,0.92,0.96,0.90,0.82,0.76,0.70,0.64,0.72,0.80,0.88,0.94,0.98,0.92,0.84,0.78,0.72,0.66,0.74,0.82];
const BRENT_M1M2_NEAR = [0.55,0.58,0.52,0.60,0.63,0.57,0.50,0.48,0.53,0.56,0.62,0.66,0.70,0.65,0.60,0.55,0.51,0.49,0.54,0.58,0.63,0.67,0.72,0.68,0.64,0.59,0.54,0.50,0.55,0.60,0.64,0.68,0.73,0.69,0.65,0.61,0.57,0.53,0.58,0.62,0.66,0.71,0.74,0.70,0.66,0.62,0.58,0.55,0.59,0.63,0.68,0.72,0.75,0.71,0.67,0.63,0.59,0.56,0.60,0.65];
const BRENT_M1M3_NEAR = [0.90,0.96,0.86,1.02,1.08,0.94,0.82,0.78,0.88,0.94,1.04,1.12,1.20,1.12,1.02,0.92,0.84,0.78,0.88,0.98,1.08,1.18,1.26,1.18,1.06,0.96,0.88,0.80,0.90,1.00,1.10,1.20,1.28,1.20,1.10,1.02,0.94,0.86,0.96,1.06,1.16,1.24,1.30,1.22,1.12,1.04,0.96,0.88,0.98,1.08,1.18,1.26,1.32,1.24,1.14,1.06,0.98,0.90,1.00,1.10];

export const NEAR_SPREAD_DATA = SPREAD_DAYS_60.map((d, i) => ({
  day: d, m1m2: M1M2[i], m1m3: M1M3[i], brentM1M2: BRENT_M1M2_NEAR[i], brentM1M3: BRENT_M1M3_NEAR[i],
}));

/* ── Tab 1: M1-M12 Spread ───────────────────────────────────── */
const SPREAD_DAYS_30 = generateDays(30);
const M1M12_RAW = [-3.20,-3.35,-3.50,-3.42,-3.60,-3.75,-3.65,-3.80,-3.90,-3.85,-4.00,-4.10,-3.95,-4.15,-4.20,-4.08,-4.25,-4.30,-4.18,-4.35,-4.40,-4.28,-4.42,-4.48,-4.35,-4.50,-4.52,-4.45,-4.55,-4.52];
const BRENT_M1M12_RAW = [-2.80,-2.95,-3.10,-3.00,-3.20,-3.35,-3.22,-3.40,-3.52,-3.45,-3.60,-3.72,-3.55,-3.70,-3.78,-3.65,-3.82,-3.88,-3.75,-3.90,-3.98,-3.85,-4.00,-4.05,-3.92,-4.08,-4.12,-4.02,-4.15,-4.10];
export const M1M12_THRESHOLD = -4.80;
export const M1M12_DATA = SPREAD_DAYS_30.map((d, i) => ({ day: d, wti: M1M12_RAW[i], brent: BRENT_M1M12_RAW[i] }));

/* ── Tab 1: Covariance Matrix ────────────────────────────────── */
export const COV_LABELS = ['WTI', 'Brent', 'RBOB', 'Gasoil', 'DXY'];
export const COV_VALUES = [
  [1.00, 0.92, 0.78, 0.81, -0.45],
  [0.92, 1.00, 0.74, 0.85, -0.42],
  [0.78, 0.74, 1.00, 0.68, -0.33],
  [0.81, 0.85, 0.68, 1.00, -0.38],
  [-0.45, -0.42, -0.33, -0.38, 1.00],
];
export const COV_HIGHLIGHT = [[2, 3], [3, 2]];

/* ── Tab 1: M1-M12 Heatmap ──────────────────────────────────── */
export const HEATMAP_M1M12_LABELS = ['M1-M2','M2-M3','M3-M4','M4-M5','M5-M6','M6-M7','M7-M8','M8-M9','M9-M10','M10-M11','M11-M12'];
export const HEATMAP_M1M12_VALUES = [0.43,0.30,0.25,0.22,0.18,0.15,0.12,0.10,0.08,0.06,0.04];
export const BRENT_HEATMAP_M1M12_VALUES = [0.65,0.48,0.38,0.32,0.26,0.22,0.18,0.14,0.11,0.08,0.05];

/* ── Tab 1: PCA ──────────────────────────────────────────────── */
export const PCA_DATA = [
  { label: 'PC1 — Level', pct: 74, color: '#0D47A1', spark: [60,65,70,68,72,74,73,75,74,72,74,76,74,73,74] },
  { label: 'PC2 — Slope', pct: 19, color: '#1976D2', spark: [15,17,19,20,18,16,17,19,21,20,18,19,20,19,19] },
  { label: 'PC3 — Curvature', pct: 7, color: '#64B5F6', spark: [5,6,7,8,7,6,7,8,7,6,7,8,7,7,7] },
];
export const BRENT_PCA_DATA = [
  { label: 'PC1 — Level', pct: 71, color: '#343A40', spark: [58,62,67,65,69,71,70,72,71,69,71,73,71,70,71] },
  { label: 'PC2 — Slope', pct: 21, color: '#6C757D', spark: [17,19,21,22,20,18,19,21,23,22,20,21,22,21,21] },
  { label: 'PC3 — Curvature', pct: 8, color: '#ADB5BD', spark: [6,7,8,9,8,7,8,9,8,7,8,9,8,8,8] },
];

/* ── Tab 1: WTI-Brent Arb ───────────────────────────────────── */
const ARB_RAW = [-3.10,-3.25,-3.40,-3.15,-3.50,-3.60,-3.30,-3.45,-3.55,-3.70,-3.35,-3.50,-3.65,-3.80,-3.45,-3.60,-3.75,-3.90,-3.55,-3.70,-3.85,-3.95,-3.60,-3.75,-3.90,-4.00,-3.70,-3.85,-3.92,-3.85];
export const ARB_MEAN = -3.20;
export const ARB_STD = 0.81;
export const ARB_DATA = SPREAD_DAYS_30.map((d, i) => ({
  day: d, spread: ARB_RAW[i], upper: ARB_MEAN + ARB_STD, lower: ARB_MEAN - ARB_STD, mean: ARB_MEAN,
}));

/* ── Tab 1: Differentials ────────────────────────────────────── */
export const DIFF_DATA = [
  { grade: 'Midland WTI', value: +1.25 },
  { grade: 'WCS', value: -13.50 },
  { grade: 'Urals', value: -8.20 },
  { grade: 'EFP', value: -3.85 },
];

/* ── Tab 1: Crack Spreads (6 types) ──────────────────────────── */
export const CRACK_DATA = [
  { name: '3:2:1 USGC', current: 28.5, avg5yr: 24.0 },
  { name: '5:3:2 NWE', current: 22.3, avg5yr: 19.5 },
  { name: '3:2:1 Singapore', current: 18.7, avg5yr: 16.2 },
  { name: '2:1:1 Chicago', current: 24.1, avg5yr: 21.0 },
  { name: 'Gasoil NWE', current: 19.8, avg5yr: 17.3 },
  { name: 'Jet USGC', current: 31.2, avg5yr: 26.5 },
];

/* ── Tab 1: Marine Fuel ──────────────────────────────────────── */
const MARINE_RAW = [105,110,108,115,112,118,120,122,125,128,130,127,125,128,132,135,130,128,132,136,138,135,132,136,140,142,138,136,140,143];
export const MARINE_THRESHOLD = 130;
export const MARINE_DATA = SPREAD_DAYS_30.map((d, i) => ({ day: d, value: MARINE_RAW[i], threshold: MARINE_THRESHOLD }));

/* ── Tab 1: Cushing ──────────────────────────────────────────── */
export const CUSHING_UTIL = 53;
export const CUSHING_DATA = [
  { week: 'W-8', stock: 38.2, avg5yr: 42.5 }, { week: 'W-7', stock: 37.5, avg5yr: 41.8 },
  { week: 'W-6', stock: 36.8, avg5yr: 41.2 }, { week: 'W-5', stock: 37.1, avg5yr: 40.6 },
  { week: 'W-4', stock: 36.5, avg5yr: 40.1 }, { week: 'W-3', stock: 35.8, avg5yr: 39.5 },
  { week: 'W-2', stock: 35.2, avg5yr: 39.0 }, { week: 'W-1', stock: 34.6, avg5yr: 38.4 },
];

/* ── Tab 1: Floating Storage ─────────────────────────────────── */
const FLOAT_DAYS = generateDays(20);
const FLOAT_C = [82,84,86,83,80,78,76,74,72,70,68,66,65,64,63,62,61,60,59,58];
export const FLOATING_DATA = FLOAT_DAYS.map((d, i) => ({
  day: d, central: FLOAT_C[i], upper: FLOAT_C[i] + 8, lower: FLOAT_C[i] - 6,
}));

/* ── Tab 2: Seasonality ──────────────────────────────────────── */
const WEEKS = Array.from({ length: 52 }, (_, i) => `W${i + 1}`);
const S_CUR = [68.2,69.1,70.5,71.2,70.8,71.5,72.3,73.0,72.5,71.8,72.4,73.1,73.8,74.2,73.6,72.9,73.5,74.1,74.8,75.2,74.5,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null];
const S_5Y = [66.0,66.5,67.2,67.8,68.3,68.9,69.4,69.8,70.1,70.4,70.6,70.8,71.0,71.2,71.3,71.4,71.5,71.5,71.5,71.4,71.3,71.1,70.9,70.7,70.5,70.3,70.1,69.9,69.7,69.5,69.4,69.3,69.2,69.2,69.3,69.4,69.6,69.8,70.1,70.4,70.7,71.0,71.3,71.6,71.8,72.0,72.1,72.2,72.2,72.1,72.0,71.8];
const S_10Y = [64.5,65.0,65.6,66.1,66.6,67.1,67.5,67.9,68.2,68.5,68.7,68.9,69.1,69.2,69.3,69.4,69.4,69.4,69.3,69.2,69.1,68.9,68.7,68.5,68.3,68.1,67.9,67.7,67.5,67.4,67.3,67.2,67.2,67.3,67.4,67.5,67.7,67.9,68.2,68.5,68.8,69.1,69.4,69.6,69.8,70.0,70.1,70.2,70.2,70.1,70.0,69.8];

export const SEASONALITY_DATA = WEEKS.map((w, i) => ({
  week: w, current: S_CUR[i], avg5yr: S_5Y[i], avg10yr: S_10Y[i],
}));

/* ── Tab 2: Seasonal Heatmap ─────────────────────────────────── */
export const HEATMAP_MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
export const HEATMAP_YEARS = [2022, 2023, 2024, 2025, 2026];
export const HEATMAP_RETURNS = [
  [+5.2,-2.1,+8.4,+3.1,-1.5,+6.3,-3.7,+2.8,-0.9,+4.2,-2.3,+1.5],
  [-1.8,+3.4,-0.6,+5.7,+2.1,-4.2,+1.3,-2.5,+6.8,-1.1,+3.6,-0.4],
  [+4.1,-3.2,+2.7,-1.4,+7.3,+0.8,-5.1,+3.9,-2.6,+1.7,-0.3,+4.5],
  [-2.5,+6.1,-1.8,+3.3,-0.7,+4.9,+2.2,-3.4,+1.6,+5.4,-2.8,+0.9],
  [+3.8,+1.2,+4.6,+2.4,+1.8,null,null,null,null,null,null,null],
];

export const SEASONAL_METRICS = {
  currentWeek: 21,
  currentPerf: '+3.2%',
  historicalMedian: '+1.8%',
  deviation: '+1.4%',
  banner: 'bullish',
  bannerText: 'Current price is trading 2.1σ above the 10-year seasonal median for Week 21. Historically, this premium reverts within 3-4 weeks in 68% of cases.',
};

/* ── Tab 2: Sentiment ────────────────────────────────────────── */
export const INITIAL_SENTIMENT_SCORE = 32;
const SENT_RAW = [18,22,15,20,28,25,30,35,28,32,38,42,35,30,28,32,36,40,34,30,28,32,35,32];
export const SENTIMENT_TREND_DATA = SENT_RAW.map((v, i) => ({ hour: `${23 - i}h`, value: v })).reverse();

/* ── Tab 2: News ─────────────────────────────────────────────── */
export const NEWS_ITEMS = [
  { id: 1, time: '2m', headline: 'OPEC+ considers extending 2.2mb/d voluntary cuts through Q3 2026', category: 'OPEC', impact: '+22', type: 'bullish' },
  { id: 2, time: '14m', headline: 'US crude inventories fall by 6.1mb — largest draw in 8 weeks', category: 'Demand', impact: '+15', type: 'bullish' },
  { id: 3, time: '28m', headline: 'Red Sea shipping disruptions widen Brent-Dubai EFS to 14-month high', category: 'Geopolitical', impact: '+18', type: 'bullish' },
  { id: 4, time: '45m', headline: 'China May refinery throughput drops 3.2% YoY on weak demand signals', category: 'Demand', impact: '-40', type: 'bearish' },
  { id: 5, time: '1h', headline: 'Fed officials signal potential rate hold — DXY softens to 104.2', category: 'Macro', impact: '+12', type: 'bullish' },
  { id: 6, time: '2h', headline: 'US SPR refill pace slows as Congress debates budget allocation', category: 'Macro', impact: '-8', type: 'bearish' },
  { id: 7, time: '3h', headline: 'Kazakhstan overproduction continues to breach OPEC+ quota by 80kb/d', category: 'OPEC', impact: '-25', type: 'bearish' },
  { id: 8, time: '4h', headline: 'European refinery margins recover on gasoline restocking demand', category: 'Demand', impact: '+10', type: 'bullish' },
  { id: 9, time: '5h', headline: 'Iran nuclear talks resume in Vienna — market eyes potential supply deal', category: 'Geopolitical', impact: '-30', type: 'bearish' },
  { id: 10, time: '6h', headline: 'India crude imports surge 8% MoM as Jamnagar ramps throughput', category: 'Demand', impact: '+14', type: 'bullish' },
];

/* ── Tab 2: Keywords ─────────────────────────────────────────── */
export const KEYWORD_DATA = [
  { keyword: 'Cushing Draw', mentions: 142, sentiment: 72, color: '#4CAF50' },
  { keyword: 'Quota Compliance', mentions: 128, sentiment: -35, color: '#E53935' },
  { keyword: 'Refinery Outage', mentions: 96, sentiment: -48, color: '#E53935' },
  { keyword: 'SPR Release', mentions: 84, sentiment: -22, color: '#FFB300' },
  { keyword: 'Red Sea Disruption', mentions: 78, sentiment: 55, color: '#4CAF50' },
  { keyword: 'OPEC+ Cuts', mentions: 71, sentiment: 62, color: '#4CAF50' },
  { keyword: 'China Demand', mentions: 65, sentiment: -18, color: '#FFB300' },
  { keyword: 'Rate Decision', mentions: 52, sentiment: 15, color: '#2196F3' },
  { keyword: 'Backwardation', mentions: 48, sentiment: 45, color: '#4CAF50' },
  { keyword: 'Contango Risk', mentions: 35, sentiment: -55, color: '#E53935' },
];

/* ── Tab 3: Flat Price (30-day) ───────────────────────────────── */
const DAYS_30 = generateDays(30);
const WTI_30 = [70.12,70.45,71.10,70.85,71.35,71.80,71.20,71.65,72.10,71.75,72.30,72.85,72.40,72.15,72.60,73.05,72.50,72.80,73.20,72.90,73.35,73.80,73.25,72.95,73.40,73.85,73.30,72.75,72.95,72.45];
const BRENT_30 = [73.90,74.25,74.80,74.55,75.10,75.60,74.95,75.40,75.90,75.50,76.10,76.65,76.20,75.90,76.35,76.80,76.25,76.55,77.00,76.70,77.15,77.60,77.05,76.75,77.20,77.65,77.10,76.55,76.75,76.30];

export const FLAT_PRICE_DATA = DAYS_30.map((d, i) => ({
  day: d, wti: WTI_30[i], brent: BRENT_30[i],
}));

/* ── Tab 3: Brent-WTI Spread ─────────────────────────────────── */
export const BW_HIST_MEAN = 3.75;
export const BW_SPREAD_DATA = DAYS_30.map((d, i) => ({
  day: d, spread: +(BRENT_30[i] - WTI_30[i]).toFixed(2), mean: BW_HIST_MEAN,
}));

/* ── Tab 3: Term Spreads ─────────────────────────────────────── */
const BRENT_M1M2_RAW = [0.55,0.58,0.62,0.56,0.60,0.64,0.59,0.63,0.67,0.61,0.65,0.69,0.63,0.60,0.64,0.68,0.62,0.66,0.70,0.64,0.68,0.72,0.66,0.63,0.67,0.71,0.65,0.62,0.66,0.70];
const WTI_M1M12_RAW = [-3.20,-3.35,-3.55,-3.30,-3.60,-3.75,-3.45,-3.65,-3.80,-3.50,-3.70,-3.90,-3.60,-3.75,-3.85,-4.00,-3.70,-3.85,-4.05,-3.80,-3.95,-4.10,-3.85,-4.00,-4.15,-4.30,-4.00,-4.20,-4.35,-4.52];

export const TERM_SPREAD_DATA = DAYS_30.map((d, i) => ({
  day: d, brentM1M2: BRENT_M1M2_RAW[i], wtiM1M12: WTI_M1M12_RAW[i],
}));

/* ── Macro Table ─────────────────────────────────────────────── */
export const MACRO_TABLE = [
  { indicator: 'US Mfg PMI', latest: '51.3', prior: '50.8' },
  { indicator: 'China Mfg PMI', latest: '49.5', prior: '49.1' },
  { indicator: 'EUR CPI (YoY)', latest: '2.4%', prior: '2.6%' },
  { indicator: 'DXY Index', latest: '104.2', prior: '103.8' },
];

/* ══════════════════════════════════════════════════════════════
   NEW PANELS (B–I)
   ══════════════════════════════════════════════════════════════ */

/* ── Panel B: WTI-Dollar Correlation ─────────────────────────── */
const CORR_DAYS = generateDays(60);
const CORR_RAW = [-0.32,-0.35,-0.38,-0.42,-0.40,-0.44,-0.48,-0.45,-0.50,-0.52,-0.48,-0.55,-0.58,-0.54,-0.50,-0.46,-0.42,-0.38,-0.35,-0.32,-0.30,-0.28,-0.32,-0.36,-0.40,-0.44,-0.48,-0.52,-0.56,-0.60,-0.58,-0.55,-0.52,-0.48,-0.45,-0.42,-0.38,-0.35,-0.32,-0.30,-0.34,-0.38,-0.42,-0.46,-0.50,-0.54,-0.52,-0.48,-0.44,-0.40,-0.36,-0.32,-0.28,-0.30,-0.34,-0.38,-0.42,-0.45,-0.48,-0.45];
export const DOLLAR_CORR_DATA = CORR_DAYS.map((d, i) => ({ day: d, correlation: CORR_RAW[i] }));

/* ── Panel C: BDTI Freight Index ──────────────────────────────── */
const BDTI_RAW = [1245,1260,1275,1290,1310,1325,1340,1355,1370,1350,1335,1320,1305,1290,1275,1260,1280,1300,1320,1340,1360,1380,1370,1355,1340,1360,1385,1400,1415,1408];
export const BDTI_DATA = SPREAD_DAYS_30.map((d, i) => ({ day: d, value: BDTI_RAW[i] }));

/* ── Panel E: Expanded Fundamentals ──────────────────────────── */
export const FUNDAMENTALS_CARDS = [
  { id: 'us_stocks',   label: 'US Crude Stocks',    value: '457.2',  unit: 'mb',    change: -6.1, avg5yr: '472.0', direction: 'down' },
  { id: 'cushing',     label: 'Cushing Inventory',   value: '34.6',   unit: 'mb',    change: -0.6, avg5yr: '38.4',  direction: 'down' },
  { id: 'production',  label: 'US Production',       value: '13.4',   unit: 'mb/d',  change: +0.1, avg5yr: '12.2',  direction: 'up' },
  { id: 'ref_util',    label: 'Refinery Utilization', value: '93.2',   unit: '%',     change: +0.8, avg5yr: '91.5',  direction: 'up' },
  { id: 'opec_prod',   label: 'OPEC Production',     value: '27.1',   unit: 'mb/d',  change: -0.3, avg5yr: '28.5',  direction: 'down' },
  { id: 'rig_count',   label: 'US Oil Rig Count',    value: '584',    unit: 'rigs',  change: -3,   avg5yr: '620',   direction: 'down' },
  { id: 'spr',         label: 'SPR Level',           value: '372.4',  unit: 'mb',    change: +0.8, avg5yr: '580.0', direction: 'up' },
  { id: 'imports',     label: 'US Net Imports',      value: '2.1',    unit: 'mb/d',  change: -0.2, avg5yr: '3.4',   direction: 'down' },
];

/* ── Panel F: CFTC COT Positioning ───────────────────────────── */
const COT_WEEKS = Array.from({ length: 12 }, (_, i) => `W-${12 - i}`);
const MM_NET = [185,192,178,165,172,180,195,210,225,218,230,242]; // managed money net long (k contracts)
const PROD_NET = [-220,-215,-210,-205,-218,-225,-240,-255,-268,-260,-275,-285]; // producer net short
const SWAP_NET = [-45,-48,-42,-38,-40,-44,-50,-55,-60,-58,-62,-65]; // swap dealer
export const COT_DATA = COT_WEEKS.map((w, i) => ({
  week: w, managedMoney: MM_NET[i], producer: PROD_NET[i], swapDealer: SWAP_NET[i],
  netSpec: MM_NET[i] + SWAP_NET[i],
}));

/* ── Panel G: STEO Global Oil Balance ────────────────────────── */
const STEO_MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const STEO_SUPPLY = [101.2,101.5,101.8,102.0,102.3,102.5,102.8,103.0,103.2,103.5,103.7,104.0];
const STEO_DEMAND = [100.8,101.0,101.5,102.2,102.8,103.2,103.5,103.8,103.5,103.0,102.5,102.0];
const STEO_OPEC = [27.1,27.0,27.2,27.3,27.4,27.5,27.6,27.7,27.8,27.9,28.0,28.1];
const STEO_NON_OPEC = [74.1,74.5,74.6,74.7,74.9,75.0,75.2,75.3,75.4,75.6,75.7,75.9];
export const STEO_DATA = STEO_MONTHS.map((m, i) => ({
  month: m,
  supply: STEO_SUPPLY[i], demand: STEO_DEMAND[i],
  balance: +(STEO_SUPPLY[i] - STEO_DEMAND[i]).toFixed(1),
  opec: STEO_OPEC[i], nonOpec: STEO_NON_OPEC[i],
}));

/* ── Panel H: Trade Signals ──────────────────────────────────── */
export const TRADE_SIGNALS = [
  { id: 1, name: 'WTI M1-M12 Calendar Spread', direction: 'BUY', confidence: 82, rationale: 'Backwardation exceeding 2σ from 120d mean — reversion expected within 10 sessions.' },
  { id: 2, name: 'Brent-WTI Arb', direction: 'SELL', confidence: 71, rationale: 'Spread compressed below −1σ Bollinger; Atlantic arb economics favor widening.' },
  { id: 3, name: '3:2:1 USGC Crack', direction: 'BUY', confidence: 88, rationale: 'Crack above 5yr avg with driving season pull; RBOB stocks 8% below seasonal norm.' },
  { id: 4, name: 'WTI vs DXY Mean Reversion', direction: 'BUY', confidence: 65, rationale: 'Negative correlation strengthening; DXY rollover signal from EUR/USD breakout.' },
  { id: 5, name: 'Cushing Storage Play', direction: 'SELL', confidence: 74, rationale: 'Cushing draws decelerating; pipeline flows normalizing post-maintenance.' },
  { id: 6, name: 'OPEC+ Compliance Fade', direction: 'HOLD', confidence: 52, rationale: 'Kazakhstan overproduction offsets Saudi cuts — net neutral until July meeting.' },
  { id: 7, name: 'Gasoil NWE Crack', direction: 'BUY', confidence: 78, rationale: 'European refinery turnarounds tightening distillate supply; ARA stocks at 3yr low.' },
];

/* ── Panel I: 5-Year Same-Week Range (52-week series) ──────── */
function gen5YrRange(base, amplitude, currentWeek) {
  return Array.from({ length: 52 }, (_, i) => {
    const w = i + 1;
    const seasonal = Math.sin((w / 52) * Math.PI * 2) * amplitude;
    const median = base + seasonal;
    const high = median + 8 + Math.sin(w * 0.3) * 4;
    const low = median - 10 + Math.cos(w * 0.4) * 3;
    const current = w <= currentWeek ? median + (Math.sin(w * 0.7) * 3) - 1.5 : null;
    return { week: `W${w}`, high5yr: +high.toFixed(2), low5yr: +low.toFixed(2), median5yr: +median.toFixed(2), current };
  });
}
export const WTI_5YR_RANGE = gen5YrRange(72, 5, 21);
export const BRENT_5YR_RANGE = gen5YrRange(78, 4.5, 21);

/* ── Individual Calendar Spreads (30-day history) ────────────── */
const SP_DAYS = generateDays(30);

function genSpread(base, amplitude, mean, seed) {
  let r = seed;
  const rand = () => { r = (r * 16807) % 2147483647; return (r / 2147483647 - 0.5) * 2; };
  return SP_DAYS.map((d, i) => {
    const val = +(base + Math.sin(i * 0.4 + seed) * amplitude + rand() * amplitude * 0.3).toFixed(3);
    const hi = +(mean + amplitude * 2.2).toFixed(3);
    const lo = +(mean - amplitude * 1.8).toFixed(3);
    return { day: d, value: val, mean, hi, lo };
  });
}

// WTI Calendar Spreads
export const WTI_CAL_SPREADS = {
  'M1-M2': genSpread(0.85, 0.20, 0.80, 42),
  'M2-M3': genSpread(0.62, 0.15, 0.58, 73),
  'M3-M4': genSpread(0.45, 0.12, 0.42, 101),
  'M4-M5': genSpread(0.32, 0.10, 0.30, 137),
  'M5-M6': genSpread(0.22, 0.08, 0.20, 163),
};

// Brent Calendar Spreads
export const BRENT_CAL_SPREADS = {
  'M1-M2': genSpread(0.72, 0.18, 0.68, 51),
  'M2-M3': genSpread(0.55, 0.14, 0.52, 82),
  'M3-M4': genSpread(0.40, 0.11, 0.38, 113),
  'M4-M5': genSpread(0.28, 0.09, 0.26, 144),
  'M5-M6': genSpread(0.18, 0.07, 0.16, 175),
};

/* ── Fly Term Structure (current snapshot) ───────────────────── */
// Fly = Front - 2*Middle + Back  for each 3-month window
export const WTI_FLY_TERM = [
  { label: 'M1-2M2+M3', value: 0.22, mean: 0.15, hi: 0.35, lo: -0.05 },
  { label: 'M2-2M3+M4', value: 0.18, mean: 0.12, hi: 0.28, lo: -0.04 },
  { label: 'M3-2M4+M5', value: 0.14, mean: 0.10, hi: 0.22, lo: -0.03 },
  { label: 'M4-2M5+M6', value: 0.10, mean: 0.08, hi: 0.18, lo: -0.02 },
  { label: 'M5-2M6+M7', value: 0.07, mean: 0.06, hi: 0.14, lo: -0.02 },
  { label: 'M6-2M7+M8', value: 0.05, mean: 0.04, hi: 0.11, lo: -0.01 },
  { label: 'M7-2M8+M9', value: 0.03, mean: 0.03, hi: 0.09, lo: -0.01 },
  { label: 'M8-2M9+M10', value: 0.02, mean: 0.02, hi: 0.07, lo: -0.01 },
  { label: 'M9-2M10+M11', value: 0.01, mean: 0.02, hi: 0.06, lo: -0.01 },
  { label: 'M10-2M11+M12', value: 0.01, mean: 0.01, hi: 0.05, lo: -0.01 },
];

export const BRENT_FLY_TERM = [
  { label: 'M1-2M2+M3', value: 0.18, mean: 0.12, hi: 0.30, lo: -0.06 },
  { label: 'M2-2M3+M4', value: 0.15, mean: 0.10, hi: 0.24, lo: -0.04 },
  { label: 'M3-2M4+M5', value: 0.12, mean: 0.08, hi: 0.20, lo: -0.03 },
  { label: 'M4-2M5+M6', value: 0.08, mean: 0.06, hi: 0.16, lo: -0.02 },
  { label: 'M5-2M6+M7', value: 0.06, mean: 0.05, hi: 0.12, lo: -0.02 },
  { label: 'M6-2M7+M8', value: 0.04, mean: 0.04, hi: 0.10, lo: -0.01 },
  { label: 'M7-2M8+M9', value: 0.03, mean: 0.03, hi: 0.08, lo: -0.01 },
  { label: 'M8-2M9+M10', value: 0.02, mean: 0.02, hi: 0.06, lo: -0.01 },
  { label: 'M9-2M10+M11', value: 0.01, mean: 0.01, hi: 0.05, lo: -0.01 },
  { label: 'M10-2M11+M12', value: 0.01, mean: 0.01, hi: 0.04, lo: -0.01 },
];

/* ── Fly Time Series (30-day history for each leg) ───────────── */
function genFlyHistory(base, amp, seed) {
  let r = seed;
  const rand = () => { r = (r * 16807) % 2147483647; return (r / 2147483647 - 0.5) * 2; };
  return SP_DAYS.map((d, i) => +(base + Math.sin(i * 0.5 + seed * 0.1) * amp + rand() * amp * 0.25).toFixed(3));
}

const WTI_FLY_KEYS = ['F1','F2','F3','F4','F5'];
const WTI_FLY_LABELS = ['M1-2M2+M3','M2-2M3+M4','M3-2M4+M5','M4-2M5+M6','M5-2M6+M7'];
const WTI_FLY_HIST_RAW = [
  genFlyHistory(0.22, 0.08, 42),
  genFlyHistory(0.18, 0.06, 73),
  genFlyHistory(0.14, 0.05, 101),
  genFlyHistory(0.10, 0.04, 137),
  genFlyHistory(0.07, 0.03, 163),
];
export const WTI_FLY_HISTORY = SP_DAYS.map((d, i) => {
  const row = { day: d };
  WTI_FLY_KEYS.forEach((k, j) => { row[k] = WTI_FLY_HIST_RAW[j][i]; });
  return row;
});
export { WTI_FLY_KEYS, WTI_FLY_LABELS };

const BRENT_FLY_KEYS = ['BF1','BF2','BF3','BF4','BF5'];
const BRENT_FLY_LABELS_ARR = ['M1-2M2+M3','M2-2M3+M4','M3-2M4+M5','M4-2M5+M6','M5-2M6+M7'];
const BRENT_FLY_HIST_RAW = [
  genFlyHistory(0.18, 0.07, 51),
  genFlyHistory(0.15, 0.05, 82),
  genFlyHistory(0.12, 0.04, 113),
  genFlyHistory(0.08, 0.03, 144),
  genFlyHistory(0.06, 0.025, 175),
];
export const BRENT_FLY_HISTORY = SP_DAYS.map((d, i) => {
  const row = { day: d };
  BRENT_FLY_KEYS.forEach((k, j) => { row[k] = BRENT_FLY_HIST_RAW[j][i]; });
  return row;
});
export { BRENT_FLY_KEYS, BRENT_FLY_LABELS_ARR };
