"""
Shipping & Tanker Analytics Engine.
Algorithms for floating storage detection, chokepoint transit monitoring,
and China import flow analysis — powered by live TankerMap data.
"""

import math
from datetime import datetime, timezone
from typing import Optional


# ──────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────

# Geofence bounding boxes for key chokepoints [min_lat, max_lat, min_lon, max_lon]
CHOKEPOINTS = {
    "strait_of_hormuz": {
        "bbox": [26.0, 26.8, 56.0, 56.8],
        "label": "Strait of Hormuz",
        "daily_flow_mbpd": 21.0,  # ~21 mbpd historical avg
        "description": "World's most important oil chokepoint. ~21% of global petroleum.",
    },
    "strait_of_malacca": {
        "bbox": [2.0, 4.0, 100.5, 102.5],
        "label": "Strait of Malacca",
        "daily_flow_mbpd": 16.0,
        "description": "Key route for Middle East → East Asia oil flows.",
    },
    "suez_canal": {
        "bbox": [29.5, 31.5, 32.0, 33.0],
        "label": "Suez Canal",
        "daily_flow_mbpd": 5.5,
        "description": "Critical Mediterranean–Red Sea transit.",
    },
    "bab_el_mandeb": {
        "bbox": [12.0, 14.0, 42.5, 44.5],
        "label": "Bab el-Mandeb",
        "daily_flow_mbpd": 6.2,
        "description": "Gateway between Red Sea and Gulf of Aden.",
    },
    "turkish_straits": {
        "bbox": [40.5, 41.5, 27.5, 29.5],
        "label": "Turkish Straits (Bosphorus)",
        "daily_flow_mbpd": 2.4,
        "description": "Bosphorus/Dardanelles — Black Sea oil exports.",
    },
    "panama_canal": {
        "bbox": [8.5, 9.5, -80.0, -79.0],
        "label": "Panama Canal",
        "daily_flow_mbpd": 0.9,
        "description": "Pacific-Atlantic transit route.",
    },
    "cape_of_good_hope": {
        "bbox": [-36.0, -33.0, 17.0, 21.0],
        "label": "Cape of Good Hope",
        "daily_flow_mbpd": 6.0,
        "description": "Alternative to Suez for VLCC traffic.",
    },
}

# China port names for destination matching
CHINA_PORTS = [
    "CHINA", "QINGDAO", "DALIAN", "NINGBO", "ZHOUSHAN", "SHANGHAI",
    "TIANJIN", "RIZHAO", "DONGJIAKOU", "HUANGDAO", "GUANGZHOU",
    "SHENZHEN", "ZHANJIANG", "MAOMING", "QUANZHOU", "XIAMEN",
    "HUIZHOU", "YANGPU", "DAXIE", "JINZHOU", "LANSHAN", "BAYUQUAN",
    "YINGKOU", "TAIZHOU", "WENZHOU", "FUZHOU", "PUTIAN", "QUZHOU",
    "ZHUHAI", "DONGGUAN", "HAIKOU", "NANJING", "NANTONG", "CHANGSHU",
    "LONGKOU", "WEIFANG", "YANTAI", "WEIHAI", "LIANYUNGANG",
    "CN ", "CHINA ",
]

INDIA_PORTS = [
    "INDIA", "SIKKA", "JAMNAGAR", "VADINAR", "MUNDRA", "MUMBAI",
    "MANGALORE", "KOCHI", "CHENNAI", "VISAKHAPATNAM", "PARADIP",
    "HALDIA", "HAZIRA", "DAHEJ", "KANDLA", "PIPAVAV",
]

# Tanker class thresholds (DWT)
TANKER_CLASSES = {
    "VLCC": (200000, float("inf")),
    "Suezmax": (120000, 200000),
    "Aframax": (80000, 120000),
    "Panamax": (60000, 80000),
    "MR": (40000, 60000),
    "Handysize": (0, 40000),
}

# Conversion factors
DWT_TO_BBL_CRUDE = 7.33       # 1 metric ton crude ≈ 7.33 barrels
LOAD_FACTOR = 0.85             # typical cargo/DWT ratio
BBL_PER_DWT = DWT_TO_BBL_CRUDE * LOAD_FACTOR  # ~6.23 bbl per DWT


def classify_tanker(dwt: int) -> str:
    """Classify tanker by DWT."""
    for cls, (lo, hi) in TANKER_CLASSES.items():
        if lo <= dwt < hi:
            return cls
    return "Unknown"


def is_oil_tanker(vessel: dict) -> bool:
    """Check if vessel is an oil tanker (crude or products)."""
    vtype = (vessel.get("vessel_type") or "").lower()
    return "oil" in vtype or "crude" in vtype


def is_lng_tanker(vessel: dict) -> bool:
    """Check if vessel is an LNG tanker."""
    vtype = (vessel.get("vessel_type") or "").lower()
    return "lng" in vtype


def estimate_cargo_bbl(vessel: dict) -> float:
    """Estimate cargo in barrels from DWT and draught."""
    dwt = vessel.get("deadweight") or 0
    draught = vessel.get("draught_meters") or 0
    if dwt == 0 or draught == 0:
        return 0

    # Use draught ratio as load proxy
    # Typical max draught for VLCC ~22m, Suezmax ~17m, Aframax ~14m
    if dwt >= 200000:
        max_draught = 22.0
    elif dwt >= 120000:
        max_draught = 17.0
    elif dwt >= 80000:
        max_draught = 14.5
    else:
        max_draught = 12.0

    load_pct = min(draught / max_draught, 1.0)
    if load_pct < 0.5:
        # Likely in ballast
        return 0
    return dwt * load_pct * DWT_TO_BBL_CRUDE


def vessel_in_bbox(vessel: dict, bbox: list) -> bool:
    """Check if vessel is within a bounding box [min_lat, max_lat, min_lon, max_lon]."""
    lat = vessel.get("latitude") or 0
    lon = vessel.get("longitude") or 0
    return bbox[0] <= lat <= bbox[1] and bbox[2] <= lon <= bbox[3]


# ──────────────────────────────────────────────────────────
# Floating Storage Detection
# ──────────────────────────────────────────────────────────

def detect_floating_storage(vessels: list[dict], min_draught: float = 11.0) -> dict:
    """
    Identify floating storage vessels.

    Criteria:
    1. Oil tanker (crude or products)
    2. Speed < 0.5 knots (stationary)
    3. Nav status is 'At anchor' or 'Moored'
    4. Draught > min_draught (loaded — not in ballast)
    5. Not at a known discharge/load port (heuristic: stationary > threshold)

    Returns detailed floating storage analysis.
    """
    oil_tankers = [v for v in vessels if is_oil_tanker(v)]
    candidates = []

    for v in oil_tankers:
        speed = v.get("speed_knots") or 0
        nav = (v.get("nav_status") or "").lower()
        draught = v.get("draught_meters") or 0
        dwt = v.get("deadweight") or 0

        # Core criteria
        is_stationary = speed < 0.5
        is_anchored = "anchor" in nav or "moored" in nav
        is_loaded = draught > min_draught

        if is_stationary and is_anchored and is_loaded:
            est_bbl = estimate_cargo_bbl(v)
            candidates.append({
                "vessel_id": v.get("vessel_id"),
                "name": v.get("name", ""),
                "imo": v.get("imo"),
                "flag": v.get("flag", ""),
                "vessel_type": v.get("vessel_type", ""),
                "tanker_class": classify_tanker(dwt),
                "deadweight": dwt,
                "draught_meters": draught,
                "latitude": v.get("latitude"),
                "longitude": v.get("longitude"),
                "destination": v.get("destination", ""),
                "sanctions_status": v.get("sanctions_status"),
                "estimated_cargo_bbl": round(est_bbl),
                "nav_status": v.get("nav_status"),
                "observed_at": v.get("observed_at"),
            })

    # Sort by estimated cargo
    candidates.sort(key=lambda x: x["estimated_cargo_bbl"], reverse=True)

    total_bbl = sum(c["estimated_cargo_bbl"] for c in candidates)
    total_dwt = sum(c["deadweight"] for c in candidates)

    # By class breakdown
    by_class = {}
    for cls in TANKER_CLASSES:
        cls_vessels = [c for c in candidates if c["tanker_class"] == cls]
        by_class[cls] = {
            "count": len(cls_vessels),
            "total_bbl": sum(c["estimated_cargo_bbl"] for c in cls_vessels),
            "total_dwt": sum(c["deadweight"] for c in cls_vessels),
        }

    # By region (cluster by location)
    regions = _cluster_by_region(candidates)

    return {
        "total_vessels": len(candidates),
        "total_estimated_bbl": round(total_bbl),
        "total_estimated_mb": round(total_bbl / 1_000_000, 2),
        "total_dwt": total_dwt,
        "by_class": by_class,
        "by_region": regions,
        "sanctioned_count": sum(1 for c in candidates if c.get("sanctions_status")),
        "vessels": candidates[:50],  # Top 50 by cargo
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _cluster_by_region(vessels: list[dict]) -> dict:
    """Cluster floating storage vessels by region."""
    regions = {
        "Middle East Gulf": {"bbox": [23, 32, 47, 60], "vessels": [], "bbl": 0},
        "Southeast Asia": {"bbox": [-5, 10, 95, 120], "vessels": [], "bbl": 0},
        "West Africa": {"bbox": [-5, 10, -20, 15], "vessels": [], "bbl": 0},
        "North Sea / Baltic": {"bbox": [50, 65, -5, 30], "vessels": [], "bbl": 0},
        "Mediterranean": {"bbox": [30, 46, -6, 40], "vessels": [], "bbl": 0},
        "US Gulf Coast": {"bbox": [25, 32, -98, -80], "vessels": [], "bbl": 0},
        "US West Coast": {"bbox": [30, 50, -125, -115], "vessels": [], "bbl": 0},
        "East Asia": {"bbox": [20, 45, 115, 145], "vessels": [], "bbl": 0},
        "Other": {"bbox": None, "vessels": [], "bbl": 0},
    }

    for v in vessels:
        placed = False
        for rname, rinfo in regions.items():
            if rinfo["bbox"] and vessel_in_bbox(v, rinfo["bbox"]):
                rinfo["vessels"].append(v["name"])
                rinfo["bbl"] += v["estimated_cargo_bbl"]
                placed = True
                break
        if not placed:
            regions["Other"]["vessels"].append(v["name"])
            regions["Other"]["bbl"] += v["estimated_cargo_bbl"]

    return {
        rname: {
            "count": len(rinfo["vessels"]),
            "estimated_bbl": round(rinfo["bbl"]),
            "estimated_mb": round(rinfo["bbl"] / 1_000_000, 2),
        }
        for rname, rinfo in regions.items()
        if rinfo["vessels"]
    }


# ──────────────────────────────────────────────────────────
# Chokepoint Transit Monitoring
# ──────────────────────────────────────────────────────────

def analyze_chokepoint_traffic(vessels: list[dict]) -> dict:
    """
    Analyze vessel traffic at all key chokepoints.
    Returns count, volume, directionality for each chokepoint.
    """
    results = {}

    for cp_key, cp_info in CHOKEPOINTS.items():
        bbox = cp_info["bbox"]
        in_zone = [v for v in vessels if vessel_in_bbox(v, bbox)]
        oil_in_zone = [v for v in in_zone if is_oil_tanker(v)]
        lng_in_zone = [v for v in in_zone if is_lng_tanker(v)]

        # Moving vessels (actually transiting vs waiting)
        oil_transiting = [v for v in oil_in_zone if (v.get("speed_knots") or 0) > 3]
        oil_waiting = [v for v in oil_in_zone if (v.get("speed_knots") or 0) <= 3]
        lng_transiting = [v for v in lng_in_zone if (v.get("speed_knots") or 0) > 3]

        # Volume estimate
        transit_bbl = sum(estimate_cargo_bbl(v) for v in oil_transiting)
        waiting_bbl = sum(estimate_cargo_bbl(v) for v in oil_waiting)

        # DWT totals
        transit_dwt = sum(v.get("deadweight", 0) for v in oil_transiting)
        waiting_dwt = sum(v.get("deadweight", 0) for v in oil_waiting)

        # By class
        transit_classes = {}
        for v in oil_transiting:
            cls = classify_tanker(v.get("deadweight", 0))
            transit_classes[cls] = transit_classes.get(cls, 0) + 1

        # Sanctioned vessels in zone
        sanctioned_in_zone = [v for v in in_zone if v.get("sanctions_status")]

        results[cp_key] = {
            "label": cp_info["label"],
            "description": cp_info["description"],
            "historical_flow_mbpd": cp_info["daily_flow_mbpd"],
            "total_vessels": len(in_zone),
            "oil_tankers": len(oil_in_zone),
            "lng_tankers": len(lng_in_zone),
            "oil_transiting": len(oil_transiting),
            "oil_waiting": len(oil_waiting),
            "lng_transiting": len(lng_transiting),
            "transit_dwt": transit_dwt,
            "transit_estimated_bbl": round(transit_bbl),
            "waiting_dwt": waiting_dwt,
            "waiting_estimated_bbl": round(waiting_bbl),
            "transit_by_class": transit_classes,
            "sanctioned_in_zone": len(sanctioned_in_zone),
            "vessels": [
                {
                    "name": v.get("name"),
                    "imo": v.get("imo"),
                    "flag": v.get("flag"),
                    "tanker_class": classify_tanker(v.get("deadweight", 0)),
                    "dwt": v.get("deadweight"),
                    "speed_knots": v.get("speed_knots"),
                    "draught_meters": v.get("draught_meters"),
                    "destination": v.get("destination"),
                    "cargo_bbl": round(estimate_cargo_bbl(v)),
                    "sanctions_status": v.get("sanctions_status"),
                }
                for v in oil_in_zone[:30]
            ],
        }

    return results


# ──────────────────────────────────────────────────────────
# China Import Flow Analysis
# ──────────────────────────────────────────────────────────

def analyze_china_imports(vessels: list[dict]) -> dict:
    """
    Estimate China crude oil import flows from live vessel data.
    Identifies all tankers heading to Chinese ports.
    """
    oil_tankers = [v for v in vessels if is_oil_tanker(v)]

    china_bound = []
    for v in oil_tankers:
        dest = (v.get("destination") or "").upper().strip()
        if not dest:
            continue
        if any(p in dest for p in CHINA_PORTS):
            est_bbl = estimate_cargo_bbl(v)
            speed = v.get("speed_knots") or 0
            china_bound.append({
                "name": v.get("name"),
                "imo": v.get("imo"),
                "flag": v.get("flag"),
                "vessel_type": v.get("vessel_type"),
                "tanker_class": classify_tanker(v.get("deadweight", 0)),
                "deadweight": v.get("deadweight", 0),
                "draught_meters": v.get("draught_meters"),
                "speed_knots": speed,
                "latitude": v.get("latitude"),
                "longitude": v.get("longitude"),
                "destination": v.get("destination", ""),
                "estimated_cargo_bbl": round(est_bbl),
                "status": "transiting" if speed > 3 else "waiting" if speed > 0.5 else "stationary",
                "sanctions_status": v.get("sanctions_status"),
                "observed_at": v.get("observed_at"),
            })

    china_bound.sort(key=lambda x: x["estimated_cargo_bbl"], reverse=True)

    total_bbl = sum(c["estimated_cargo_bbl"] for c in china_bound)
    total_dwt = sum(c["deadweight"] for c in china_bound)

    # By port breakdown
    by_port = {}
    for v in china_bound:
        port = v["destination"].strip()
        if port not in by_port:
            by_port[port] = {"count": 0, "total_bbl": 0, "total_dwt": 0}
        by_port[port]["count"] += 1
        by_port[port]["total_bbl"] += v["estimated_cargo_bbl"]
        by_port[port]["total_dwt"] += v["deadweight"]

    # By tanker class
    by_class = {}
    for cls in TANKER_CLASSES:
        cls_v = [c for c in china_bound if c["tanker_class"] == cls]
        if cls_v:
            by_class[cls] = {
                "count": len(cls_v),
                "total_bbl": sum(c["estimated_cargo_bbl"] for c in cls_v),
                "total_dwt": sum(c["deadweight"] for c in cls_v),
            }

    # By origin estimate (based on current position)
    origins = _estimate_origin_regions(china_bound)

    # Transiting vs stationary
    transiting = [v for v in china_bound if v["status"] == "transiting"]
    stationary = [v for v in china_bound if v["status"] == "stationary"]

    # Sanctioned vessels
    sanctioned = [v for v in china_bound if v.get("sanctions_status")]

    return {
        "total_vessels": len(china_bound),
        "total_estimated_bbl": round(total_bbl),
        "total_estimated_mb": round(total_bbl / 1_000_000, 2),
        "total_dwt": total_dwt,
        "transiting_count": len(transiting),
        "stationary_count": len(stationary),
        "sanctioned_count": len(sanctioned),
        "by_port": dict(sorted(by_port.items(), key=lambda x: x[1]["count"], reverse=True)),
        "by_class": by_class,
        "by_origin_region": origins,
        "vessels": china_bound[:50],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _estimate_origin_regions(vessels: list[dict]) -> dict:
    """Estimate origin regions based on current vessel position."""
    region_boxes = {
        "Middle East": [10, 35, 40, 65],
        "West Africa": [-5, 15, -20, 15],
        "Southeast Asia": [-10, 10, 95, 125],
        "Russia/FSU": [40, 75, 25, 180],
        "Americas": [-40, 60, -130, -30],
        "Mediterranean": [30, 46, -6, 40],
        "Indian Subcontinent": [5, 25, 65, 95],
    }

    origins = {}
    for v in vessels:
        placed = False
        for rname, bbox in region_boxes.items():
            if vessel_in_bbox(v, bbox):
                if rname not in origins:
                    origins[rname] = {"count": 0, "bbl": 0}
                origins[rname]["count"] += 1
                origins[rname]["bbl"] += v["estimated_cargo_bbl"]
                placed = True
                break
        if not placed:
            if "Other/En Route" not in origins:
                origins["Other/En Route"] = {"count": 0, "bbl": 0}
            origins["Other/En Route"]["count"] += 1
            origins["Other/En Route"]["bbl"] += v["estimated_cargo_bbl"]

    return origins


# ──────────────────────────────────────────────────────────
# India Import Flow Analysis
# ──────────────────────────────────────────────────────────

def analyze_india_imports(vessels: list[dict]) -> dict:
    """Estimate India crude oil import flows."""
    oil_tankers = [v for v in vessels if is_oil_tanker(v)]
    india_bound = []
    for v in oil_tankers:
        dest = (v.get("destination") or "").upper().strip()
        if not dest:
            continue
        if any(p in dest for p in INDIA_PORTS):
            est_bbl = estimate_cargo_bbl(v)
            india_bound.append({
                "name": v.get("name"),
                "destination": v.get("destination"),
                "deadweight": v.get("deadweight", 0),
                "estimated_cargo_bbl": round(est_bbl),
                "tanker_class": classify_tanker(v.get("deadweight", 0)),
                "flag": v.get("flag"),
                "sanctions_status": v.get("sanctions_status"),
            })

    total_bbl = sum(c["estimated_cargo_bbl"] for c in india_bound)
    return {
        "total_vessels": len(india_bound),
        "total_estimated_bbl": round(total_bbl),
        "total_estimated_mb": round(total_bbl / 1_000_000, 2),
        "vessels": india_bound[:30],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ──────────────────────────────────────────────────────────
# Fleet Summary
# ──────────────────────────────────────────────────────────

def compute_fleet_summary(vessels: list[dict]) -> dict:
    """Compute a global fleet summary from live vessel data."""
    oil_tankers = [v for v in vessels if is_oil_tanker(v)]
    lng_tankers = [v for v in vessels if is_lng_tanker(v)]

    # Speed distribution
    speeds = [(v.get("speed_knots") or 0) for v in oil_tankers]
    stationary = sum(1 for s in speeds if s < 0.5)
    slow = sum(1 for s in speeds if 0.5 <= s < 3)
    moving = sum(1 for s in speeds if s >= 3)

    # Class distribution
    class_dist = {}
    for cls in TANKER_CLASSES:
        cls_v = [v for v in oil_tankers if classify_tanker(v.get("deadweight", 0)) == cls]
        class_dist[cls] = len(cls_v)

    # Flag distribution (top 10)
    from collections import Counter
    flags = Counter(v.get("flag", "Unknown") for v in vessels).most_common(10)

    # Sanctions
    sanctioned = [v for v in vessels if v.get("sanctions_status")]

    return {
        "total_vessels": len(vessels),
        "oil_tankers": len(oil_tankers),
        "lng_tankers": len(lng_tankers),
        "speed_distribution": {
            "stationary": stationary,
            "slow": slow,
            "moving": moving,
        },
        "class_distribution": class_dist,
        "top_flags": [{"flag": f, "count": c} for f, c in flags],
        "sanctioned_total": len(sanctioned),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
