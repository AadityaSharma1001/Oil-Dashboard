import React, { memo, useCallback } from 'react';
import Card from './Card';
import { useApiData } from '../hooks/useApiData';
import { fetchHurricanes } from '../api';

const StormTracker = memo(() => {
  const fetchFn = useCallback(() => fetchHurricanes(), []);
  const { data: apiData, source, loading } = useApiData(fetchFn, { refreshInterval: 60000 });

  if (loading && !apiData) {
    return <div className="h-48 flex items-center justify-center text-slate-400">Loading Storm Data...</div>;
  }

  const season = apiData?.season || {};
  const storms = apiData?.active_storms || [];
  const infra = apiData?.infrastructure || {};
  const gulfPlatforms = apiData?.gulf_platforms || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
      {/* Active Storms Tracking (7 columns) */}
      <div className="lg:col-span-7 flex flex-col gap-3.5">
        <Card title="Active Storm Tracking" badge="Live NHC Feed" source={source} badgeVariant="blue">
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between px-1">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                {season.year} Season: <span className="text-slate-800">{season.named_storms} Named Storms</span>
              </div>
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Active Now: <span className="text-emerald-600">{season.active_now}</span>
              </div>
            </div>

            {storms.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 bg-slate-50 rounded border border-slate-100">
                <div className="text-3xl mb-2">☀️</div>
                <div className="text-sm font-semibold text-slate-600">No Active Storms</div>
                <div className="text-[11px] text-slate-400">All basins are currently quiet.</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {storms.map(storm => (
                  <div key={storm.id} className={`p-3 rounded border relative overflow-hidden ${storm.in_gulf ? 'bg-red-50 border-red-200' : 'bg-white border-slate-200'}`}>
                    {storm.in_gulf && <div className="absolute top-0 right-0 w-10 h-10 overflow-hidden"><div className="bg-red-500 text-white text-[9px] font-bold py-0.5 px-3 transform rotate-45 translate-x-3 translate-y-1">GULF</div></div>}
                    
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`w-2.5 h-2.5 rounded-full ${storm.wind > 64 ? 'bg-purple-500' : storm.wind > 34 ? 'bg-amber-500' : 'bg-blue-400'} animate-pulse`} />
                      <div className="font-bold text-slate-800">{storm.name}</div>
                      <div className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded font-mono">{storm.id}</div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[11px]">
                      <div>
                        <div className="text-slate-400 font-medium">Status</div>
                        <div className={`font-semibold ${storm.wind > 64 ? 'text-purple-700' : 'text-amber-700'}`}>{storm.status}</div>
                      </div>
                      <div>
                        <div className="text-slate-400 font-medium">Movement</div>
                        <div className="font-semibold text-slate-700">{storm.movement}</div>
                      </div>
                      <div>
                        <div className="text-slate-400 font-medium">Pressure</div>
                        <div className="font-semibold text-slate-700">{storm.pressure} mb</div>
                      </div>
                      <div>
                        <div className="text-slate-400 font-medium">Location</div>
                        <div className="font-semibold text-slate-700">{storm.location.lat}°, {storm.location.lon}°</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Infrastructure Impact (5 columns) */}
      <div className="lg:col-span-5 flex flex-col gap-3.5">
        <Card title="Gulf Infrastructure Impact" badge="Simulated Model">
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className={`p-3 rounded border ${infra.platforms_shut_in > 0 ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'}`}>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Platforms Shut</div>
              <div className="flex items-baseline gap-1">
                <span className={`text-2xl font-bold ${infra.platforms_shut_in > 0 ? 'text-amber-600' : 'text-slate-700'}`}>
                  {infra.platforms_shut_in}
                </span>
                <span className="text-xs text-slate-400">/ {infra.platforms_total}</span>
              </div>
            </div>
            
            <div className={`p-3 rounded border ${infra.production_offline > 0 ? 'bg-red-50 border-red-200' : 'bg-slate-50 border-slate-200'}`}>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Prod Offline (mbpd)</div>
              <div className="flex items-baseline gap-1">
                <span className={`text-2xl font-bold ${infra.production_offline > 0 ? 'text-red-600' : 'text-slate-700'}`}>
                  {infra.production_offline}
                </span>
                <span className="text-xs text-slate-400">/ {infra.production_total}</span>
              </div>
            </div>

            <div className={`p-3 rounded border ${infra.ports_closed?.length > 0 ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'}`}>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Ports Closed</div>
              <div className="flex items-baseline gap-1">
                <span className={`text-2xl font-bold ${infra.ports_closed?.length > 0 ? 'text-amber-600' : 'text-slate-700'}`}>
                  {infra.ports_closed?.length || 0}
                </span>
                <span className="text-xs text-slate-400">/ {infra.ports_closed?.length + infra.ports_open}</span>
              </div>
            </div>

            <div className={`p-3 rounded border ${infra.ref_capacity_at_risk > 0 ? 'bg-red-50 border-red-200' : 'bg-slate-50 border-slate-200'}`}>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Refining at Risk</div>
              <div className="flex items-baseline gap-1">
                <span className={`text-2xl font-bold ${infra.ref_capacity_at_risk > 0 ? 'text-red-600' : 'text-slate-700'}`}>
                  {infra.ref_capacity_at_risk}
                </span>
                <span className="text-xs text-slate-400">mbpd</span>
              </div>
            </div>
          </div>

          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 px-1">Key Deepwater Platforms</div>
          <div className="space-y-1">
            {gulfPlatforms.map(p => (
              <div key={p.name} className="flex justify-between items-center p-2 bg-slate-50 rounded text-[11px]">
                <div className="font-semibold text-slate-700">{p.name}</div>
                <div className="flex items-center gap-3">
                  <span className="text-slate-400 font-mono">{p.capacity} mbpd</span>
                  <span className={`px-2 py-0.5 rounded uppercase font-bold tracking-wider text-[9px] ${
                    p.status === 'evacuated' ? 'bg-red-100 text-red-700' :
                    p.status === 'reduced' ? 'bg-amber-100 text-amber-700' :
                    'bg-emerald-100 text-emerald-700'
                  }`}>
                    {p.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
});

export default StormTracker;
