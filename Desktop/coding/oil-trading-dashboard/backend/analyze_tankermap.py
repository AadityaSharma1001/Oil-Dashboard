"""
TankerMap API Data Analyzer — explore the live vessel feed.
Run: python analyze_tankermap.py
"""

import urllib.request
import json
import sys
from collections import Counter, defaultdict


def fetch_vessels():
    """Fetch all live vessels from TankerMap."""
    url = "https://tankermap.com/api/vessels/live?fields=map"
    req = urllib.request.Request(url, headers={"User-Agent": "OilDesk/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def analyze(vessels):
    print(f"\n{'='*80}")
    print(f"{'TANKERMAP LIVE DATA ANALYSIS':^80}")
    print(f"{'='*80}")
    print(f"\nTotal vessels: {len(vessels)}")

    # ── Data fields ──
    if vessels:
        print(f"\nFields per vessel: {list(vessels[0].keys())}")

    # ── Vessel types ──
    types = Counter(v.get("vessel_type", "Unknown") for v in vessels)
    print(f"\n--- Vessel Types ---")
    for t, c in types.most_common():
        print(f"  {t:<30} {c:>5}")

    # ── Nav statuses ──
    statuses = Counter(v.get("nav_status") or "Unknown" for v in vessels)
    print(f"\n--- Navigation Status ---")
    for s, c in statuses.most_common():
        print(f"  {str(s):<30} {c:>5}")

    # ── Flags ──
    flags = Counter(v.get("flag", "Unknown") for v in vessels)
    print(f"\n--- Top 15 Flags ---")
    for f, c in flags.most_common(15):
        print(f"  {f:<30} {c:>5}")

    # ── Speed distribution ──
    speeds = [v.get("speed_knots", 0) or 0 for v in vessels]
    stationary = sum(1 for s in speeds if s < 0.5)
    slow = sum(1 for s in speeds if 0.5 <= s < 3)
    moving = sum(1 for s in speeds if s >= 3)
    print(f"\n--- Speed Distribution ---")
    print(f"  Stationary (<0.5 kn):  {stationary:>5} ({stationary/len(vessels)*100:.1f}%)")
    print(f"  Slow (0.5-3 kn):       {slow:>5} ({slow/len(vessels)*100:.1f}%)")
    print(f"  Moving (>3 kn):        {moving:>5} ({moving/len(vessels)*100:.1f}%)")

    # ── DWT distribution ──
    vlcc = [v for v in vessels if (v.get("deadweight") or 0) >= 200000]
    suezmax = [v for v in vessels if 120000 <= (v.get("deadweight") or 0) < 200000]
    aframax = [v for v in vessels if 80000 <= (v.get("deadweight") or 0) < 120000]
    panamax = [v for v in vessels if 60000 <= (v.get("deadweight") or 0) < 80000]
    smaller = [v for v in vessels if (v.get("deadweight") or 0) < 60000]
    print(f"\n--- Tanker Classes (by DWT) ---")
    print(f"  VLCC (200k+):          {len(vlcc):>5}")
    print(f"  Suezmax (120-200k):    {len(suezmax):>5}")
    print(f"  Aframax (80-120k):     {len(aframax):>5}")
    print(f"  Panamax (60-80k):      {len(panamax):>5}")
    print(f"  Smaller (<60k):        {len(smaller):>5}")

    # ── Sanctions ──
    sanctioned = [v for v in vessels if v.get("sanctions_status")]
    print(f"\n--- Sanctions ---")
    print(f"  Sanctioned vessels:    {len(sanctioned):>5}")
    for v in sanctioned[:5]:
        print(f"    {v['name']:<25} {v.get('flag',''):<15} DWT={v.get('deadweight',0)}")

    # ── Draught analysis (loaded vs ballast) ──
    oil_tankers = [v for v in vessels if "Oil" in (v.get("vessel_type") or "") or "Crude" in (v.get("vessel_type") or "")]
    loaded = [v for v in oil_tankers if (v.get("draught_meters") or 0) > 12]
    ballast = [v for v in oil_tankers if 0 < (v.get("draught_meters") or 0) <= 8]
    mid = [v for v in oil_tankers if 8 < (v.get("draught_meters") or 0) <= 12]
    print(f"\n--- Load Status (Oil Tankers, by draught) ---")
    print(f"  Oil tankers total:     {len(oil_tankers):>5}")
    print(f"  Loaded (>12m):         {len(loaded):>5}")
    print(f"  Partially (8-12m):     {len(mid):>5}")
    print(f"  Ballast (<=8m):        {len(ballast):>5}")

    # ── Floating storage candidates ──
    # Criteria: stationary (<0.5kn), at anchor, loaded (draught>12m), oil tanker
    fs_candidates = [
        v for v in oil_tankers
        if (v.get("speed_knots") or 0) < 0.5
        and v.get("nav_status") in ("At anchor", "Moored")
        and (v.get("draught_meters") or 0) > 12
    ]
    total_fs_dwt = sum(v.get("deadweight", 0) for v in fs_candidates)
    print(f"\n--- Floating Storage Candidates ---")
    print(f"  Criteria: stationary + at anchor/moored + loaded (draught>12m)")
    print(f"  Candidates:            {len(fs_candidates):>5}")
    print(f"  Total DWT capacity:    {total_fs_dwt:>12,} tonnes")
    print(f"  Est. barrels stored:   ~{int(total_fs_dwt * 0.85 / 0.136):>10,} bbl")  # rough crude estimate
    for v in fs_candidates[:10]:
        print(f"    {v['name']:<25} DWT={v.get('deadweight',0):>7,}  draught={v.get('draught_meters',0):.1f}m  dest={v.get('destination','')}")

    # ── Strait of Hormuz vessels ──
    # Hormuz: lat 25.5-27.5, lon 55.5-57.5
    hormuz = [v for v in vessels if 25.0 <= (v.get("latitude") or 0) <= 27.5 and 55.5 <= (v.get("longitude") or 0) <= 57.5]
    hormuz_moving = [v for v in hormuz if (v.get("speed_knots") or 0) > 3]
    hormuz_dwt = sum(v.get("deadweight", 0) for v in hormuz_moving)
    print(f"\n--- Strait of Hormuz (25-27.5°N, 55.5-57.5°E) ---")
    print(f"  Vessels in zone:       {len(hormuz):>5}")
    print(f"  Actively transiting:   {len(hormuz_moving):>5}")
    print(f"  Transit DWT:           {hormuz_dwt:>12,}")

    # ── Strait of Malacca vessels ──
    # Malacca: lat 1-6, lon 99-104
    malacca = [v for v in vessels if 1.0 <= (v.get("latitude") or 0) <= 6.0 and 99.0 <= (v.get("longitude") or 0) <= 104.5]
    malacca_moving = [v for v in malacca if (v.get("speed_knots") or 0) > 3]
    malacca_dwt = sum(v.get("deadweight", 0) for v in malacca_moving)
    print(f"\n--- Strait of Malacca (1-6°N, 99-104.5°E) ---")
    print(f"  Vessels in zone:       {len(malacca):>5}")
    print(f"  Actively transiting:   {len(malacca_moving):>5}")
    print(f"  Transit DWT:           {malacca_dwt:>12,}")

    # ── China-bound vessels (crude + products) ──
    china_ports = ["CHINA", "QINGDAO", "DALIAN", "NINGBO", "ZHOUSHAN", "SHANGHAI", "TIANJIN",
                   "RIZHAO", "DONGJIAKOU", "HUANGDAO", "GUANGZHOU", "SHENZHEN", "ZHANJIANG",
                   "MAOMING", "QUANZHOU", "XIAMEN", "HUIZHOU", "YANGPU", "DAXIE"]
    china_bound = [v for v in oil_tankers if any(p in (v.get("destination") or "").upper() for p in china_ports)]
    china_dwt = sum(v.get("deadweight", 0) for v in china_bound)
    print(f"\n--- China-Bound Oil Tankers ---")
    print(f"  Vessels heading to CN: {len(china_bound):>5}")
    print(f"  Total DWT:             {china_dwt:>12,}")
    print(f"  Est. volume (bbl):     ~{int(china_dwt * 0.85 / 0.136):>10,}")
    for v in china_bound[:10]:
        spd = v.get("speed_knots", 0) or 0
        print(f"    {v['name']:<25} DWT={v.get('deadweight',0):>7,}  {spd:.1f}kn  dest={v.get('destination','')}")

    # ── Destinations ──
    dests = Counter(v.get("destination", "").upper().strip() for v in vessels if v.get("destination"))
    print(f"\n--- Top 20 Destinations ---")
    for d, c in dests.most_common(20):
        print(f"  {d:<30} {c:>5}")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    print("Fetching live vessel data from TankerMap...")
    vessels = fetch_vessels()
    analyze(vessels)
