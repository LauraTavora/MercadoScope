from app.services.scraper import _parse_number, _parse_price


def test_parse_price_brazilian():
    assert _parse_price("R$ 1.299,90") == 1299.90


def test_parse_number_mil():
    assert _parse_number("2,5 mil vendidos") == 2500


def test_parse_number_plain():
    assert _parse_number("342 vendidos") == 342
