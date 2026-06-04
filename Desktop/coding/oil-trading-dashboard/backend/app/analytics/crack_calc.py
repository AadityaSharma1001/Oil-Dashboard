"""Crack spread formulas — 3:2:1, 5:3:2, 2:1:1 and variants."""


def crack_3_2_1(crude: float, gasoline: float, heating_oil: float) -> float:
    """3:2:1 crack spread (USGC standard)."""
    return (2 * gasoline * 42 + heating_oil * 42 - 3 * crude) / 3


def crack_5_3_2(crude: float, gasoline: float, heating_oil: float) -> float:
    """5:3:2 NWE crack spread."""
    return (3 * gasoline * 42 + 2 * heating_oil * 42 - 5 * crude) / 5


def crack_2_1_1(crude: float, gasoline: float, heating_oil: float) -> float:
    """2:1:1 crack spread."""
    return (gasoline * 42 + heating_oil * 42 - 2 * crude) / 2


def jet_crack(crude: float, jet_fuel: float) -> float:
    """Jet fuel crack spread."""
    return jet_fuel * 42 - crude


def singapore_crack(dubai: float, gasoil: float) -> float:
    """Singapore gasoil crack."""
    return gasoil - dubai


def gasoline_blending(rbob: float, ethanol: float) -> float:
    """Gasoline blending margin."""
    return rbob * 42 - ethanol


def compute_all_cracks(prices: dict) -> list[dict]:
    """
    Compute all crack spreads given current prices.
    
    prices: {
        "wti": float, "brent": float, "rbob": float,
        "ho": float, "gasoil": float, "dubai": float
    }
    """
    wti = prices.get("wti", 72.0)
    brent = prices.get("brent", 76.0)
    rbob = prices.get("rbob", 2.34)
    ho = prices.get("ho", 2.48)
    gasoil = prices.get("gasoil", 684.0)

    return [
        {
            "name": "3:2:1 USGC",
            "current": round(crack_3_2_1(wti, rbob, ho), 2),
            "avg5yr": 28.50,
            "deviation": 0, "deviation_pct": 0,
        },
        {
            "name": "5:3:2 NWE",
            "current": round(crack_5_3_2(brent, rbob, ho), 2),
            "avg5yr": 18.20,
            "deviation": 0, "deviation_pct": 0,
        },
        {
            "name": "2:1:1 USGC",
            "current": round(crack_2_1_1(wti, rbob, ho), 2),
            "avg5yr": 24.80,
            "deviation": 0, "deviation_pct": 0,
        },
        {
            "name": "WTI Gasoline",
            "current": round(rbob * 42 - wti, 2),
            "avg5yr": 22.40,
            "deviation": 0, "deviation_pct": 0,
        },
        {
            "name": "WTI Heating Oil",
            "current": round(ho * 42 - wti, 2),
            "avg5yr": 30.10,
            "deviation": 0, "deviation_pct": 0,
        },
        {
            "name": "Brent Gasoil",
            "current": round(gasoil / 7.45 - brent, 2),  # mt to bbl conversion
            "avg5yr": 15.60,
            "deviation": 0, "deviation_pct": 0,
        },
    ]
