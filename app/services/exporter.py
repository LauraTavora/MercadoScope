from __future__ import annotations

from pathlib import Path

import pandas as pd


CSV_COLUMNS = [
    "position",
    "title",
    "price",
    "currency",
    "rating",
    "review_count",
    "sold_quantity",
    "product_url",
    "image_url",
]


def export_csv(products: list[dict], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(products)
    for column in CSV_COLUMNS:
        if column not in frame.columns:
            frame[column] = None
    frame[CSV_COLUMNS].to_csv(destination, index=False, encoding="utf-8-sig")
    return destination
