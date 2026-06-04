"""
Comprehensive API endpoint test — hits every route and reports results.
Run: python test_endpoints.py
"""

import urllib.request
import json
import time
import sys

BASE = "http://localhost:8000"

ENDPOINTS = [
    # Root
    ("GET", "/", "Root"),
    ("GET", "/docs", "Swagger Docs"),
    ("GET", "/api/v1/health", "Health"),
    ("GET", "/api/v1/readiness", "Readiness"),

    # Tickers
    ("GET", "/api/v1/tickers", "Tickers"),

    # Forward Curves
    ("GET", "/api/v1/forward-curves/wti", "Forward Curve WTI"),
    ("GET", "/api/v1/forward-curves/brent", "Forward Curve Brent"),

    # Intraday
    ("GET", "/api/v1/intraday/wti", "Intraday WTI"),
    ("GET", "/api/v1/intraday/brent", "Intraday Brent"),

    # Spreads
    ("GET", "/api/v1/spreads/calendar/wti", "Calendar Spread WTI"),
    ("GET", "/api/v1/spreads/fly/wti", "Fly Spread WTI"),
    ("GET", "/api/v1/spreads/m1-m12/wti", "M1-M12 Spread WTI"),

    # 5-Year Range
    ("GET", "/api/v1/five-year-range/wti", "5yr Range WTI"),
    ("GET", "/api/v1/five-year-range/brent", "5yr Range Brent"),

    # Core Desk
    ("GET", "/api/v1/core-desk/covariance", "Covariance Matrix"),
    ("GET", "/api/v1/core-desk/pca/wti", "PCA WTI"),
    ("GET", "/api/v1/core-desk/dollar-correlation", "Dollar Correlation"),
    ("GET", "/api/v1/core-desk/arb/wti-brent", "WTI-Brent Arb"),
    ("GET", "/api/v1/core-desk/differentials", "Differentials"),

    # Crack Spreads
    ("GET", "/api/v1/crack-spreads", "Crack Spreads"),

    # Fundamentals
    ("GET", "/api/v1/fundamentals/cards", "Fundamental Cards"),
    ("GET", "/api/v1/fundamentals/cushing", "Cushing Inventory"),
    ("GET", "/api/v1/fundamentals/floating-storage", "Floating Storage"),
    ("GET", "/api/v1/fundamentals/spare-capacity", "Spare Capacity"),

    # Signals
    ("GET", "/api/v1/signals/engine", "Signal Engine"),
    ("GET", "/api/v1/signals/trade", "Trade Signals"),
    ("GET", "/api/v1/signals/audit", "Signal Audit"),
    ("GET", "/api/v1/signals/news", "Signal News"),

    # Sentiment
    ("GET", "/api/v1/sentiment/latest", "Sentiment Latest"),
    ("GET", "/api/v1/sentiment/aggregate", "Sentiment Aggregate"),

    # COT
    ("GET", "/api/v1/cot/positioning", "COT Positioning"),

    # Freight
    ("GET", "/api/v1/freight/bdti", "BDTI Index"),

    # Shipping
    ("GET", "/api/v1/shipping/chokepoints", "Chokepoints"),
    ("GET", "/api/v1/shipping/floating-storage", "Shipping Float Storage"),
    ("GET", "/api/v1/shipping/vlcc-rates", "VLCC Rates"),
    ("GET", "/api/v1/shipping/fleet-utilization", "Fleet Utilization"),

    # STEO
    ("GET", "/api/v1/steo/balance", "STEO Balance"),

    # Hurricanes
    ("GET", "/api/v1/hurricanes/active", "Active Hurricanes"),
    ("GET", "/api/v1/hurricanes/season-summary", "Season Summary"),

    # Macro & Seasonality
    ("GET", "/api/v1/macro/seasonality/wti", "Seasonality WTI"),
    ("GET", "/api/v1/macro/heatmap/wti", "Heatmap WTI"),
    ("GET", "/api/v1/macro/weekly-metrics", "Weekly Metrics"),
]


def test_endpoint(method, path, name):
    url = f"{BASE}{path}"
    start = time.time()
    try:
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed = round((time.time() - start) * 1000)
            status = resp.status
            body = resp.read().decode()
            data = json.loads(body) if body else {}

            # Check for provenance
            has_provenance = "provenance" in data
            prov_status = data.get("provenance", {}).get("status", "n/a")
            has_data = "data" in data

            return {
                "name": name,
                "status": status,
                "time_ms": elapsed,
                "has_provenance": has_provenance,
                "prov_status": prov_status,
                "has_data": has_data,
                "result": "PASS",
            }
    except urllib.error.HTTPError as e:
        elapsed = round((time.time() - start) * 1000)
        return {
            "name": name,
            "status": e.code,
            "time_ms": elapsed,
            "has_provenance": False,
            "prov_status": "n/a",
            "has_data": False,
            "result": "FAIL",
            "error": str(e),
        }
    except Exception as e:
        elapsed = round((time.time() - start) * 1000)
        return {
            "name": name,
            "status": 0,
            "time_ms": elapsed,
            "has_provenance": False,
            "prov_status": "n/a",
            "has_data": False,
            "result": "ERROR",
            "error": str(e),
        }


if __name__ == "__main__":
    print("=" * 90)
    print(f"{'ENDPOINT TEST SUITE':^90}")
    print(f"{'Testing ' + str(len(ENDPOINTS)) + ' endpoints':^90}")
    print("=" * 90)
    print(f"{'#':>3} | {'Name':<28} | {'Status':>6} | {'Time':>7} | {'Provenance':>10} | {'Data':>4} | {'Result':>6}")
    print("-" * 90)

    results = []
    for i, (method, path, name) in enumerate(ENDPOINTS, 1):
        result = test_endpoint(method, path, name)
        results.append(result)
        prov = result['prov_status'] if result['has_provenance'] else 'none'
        data_flag = 'Y' if result['has_data'] else 'N'
        icon = "PASS" if result['result'] == 'PASS' else "FAIL"
        print(f"{i:>3} | {name:<28} | {result['status']:>6} | {result['time_ms']:>5}ms | {prov:>10} | {data_flag:>4} | {icon:>6}")

    print("=" * 90)
    passed = sum(1 for r in results if r['result'] == 'PASS')
    failed = sum(1 for r in results if r['result'] != 'PASS')
    avg_ms = sum(r['time_ms'] for r in results) / len(results) if results else 0
    print(f"TOTAL: {passed} PASS / {failed} FAIL / {len(results)} TOTAL | Avg: {avg_ms:.0f}ms")

    if failed:
        print("\nFAILED ENDPOINTS:")
        for r in results:
            if r['result'] != 'PASS':
                print(f"  - {r['name']}: {r.get('error', 'unknown')}")

    print("=" * 90)
    sys.exit(0 if failed == 0 else 1)
