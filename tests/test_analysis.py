from app.services.analysis import analyze_products


def test_analysis_metrics():
    result = analyze_products(
        [
            {"title": "A", "price": 100.0, "rating": 4.5, "review_count": 20},
            {"title": "B", "price": 200.0, "rating": 4.9, "review_count": 100},
            {"title": "C", "price": 300.0, "rating": None, "review_count": None},
        ]
    )
    assert result["count"] == 3
    assert result["mean"] == 200.0
    assert result["median"] == 200.0
    assert result["min"] == 100.0
    assert result["max"] == 300.0
    assert result["top_rated"]["title"] == "B"


def test_analysis_empty():
    assert analyze_products([])["count"] == 0
