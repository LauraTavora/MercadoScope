from __future__ import annotations

from statistics import mean, median, pstdev


def analyze_products(products: list[dict]) -> dict:
    valid = [p for p in products if isinstance(p.get("price"), (int, float)) and p["price"] >= 0]
    if not valid:
        return {
            "count": 0,
            "mean": 0,
            "median": 0,
            "min": 0,
            "max": 0,
            "stddev": 0,
            "best_value": None,
            "top_rated": None,
        }

    prices = [float(p["price"]) for p in valid]
    rated = [p for p in valid if isinstance(p.get("rating"), (int, float))]

    # Heurística simples e explicável para portfólio: avaliação alta e preço abaixo da média.
    average_price = mean(prices)
    value_candidates = [
        p for p in rated if p["rating"] >= 4.0 and float(p["price"]) <= average_price
    ]
    best_value = max(
        value_candidates,
        key=lambda p: (float(p["rating"]) / max(float(p["price"]), 1)) * 1000,
        default=min(valid, key=lambda p: float(p["price"])),
    )
    top_rated = max(
        rated,
        key=lambda p: (float(p["rating"]), int(p.get("review_count") or 0)),
        default=None,
    )

    return {
        "count": len(valid),
        "mean": round(average_price, 2),
        "median": round(median(prices), 2),
        "min": round(min(prices), 2),
        "max": round(max(prices), 2),
        "stddev": round(pstdev(prices), 2) if len(prices) > 1 else 0,
        "best_value": best_value,
        "top_rated": top_rated,
    }
