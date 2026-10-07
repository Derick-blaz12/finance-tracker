import pytest

from money import format_naira, parse_naira


@pytest.mark.parametrize("text, expected", [
    ("5000", 500000),
    ("5000.50", 500050),
    ("5000.5", 500050),
    ("0.01", 1),
    ("0.1", 10),
    ("5,000.50", 500050),
    ("₦200", 20000),
    ("  100  ", 10000),
])
def test_parse_valid(text, expected):
    assert parse_naira(text) == expected


@pytest.mark.parametrize("text", [
    "", "abc", "1.234", "-5", "NaN", "Infinity", "1e3", "5.", ".5", "1.2.3",
])
def test_parse_invalid_raises(text):
    with pytest.raises(ValueError):
        parse_naira(text)


@pytest.mark.parametrize("kobo, expected", [
    (500050, "₦5,000.50"),
    (0, "₦0.00"),
    (5, "₦0.05"),
    (20000000, "₦200,000.00"),
    (123456789, "₦1,234,567.89"),
    (-1000000, "-₦10,000.00"),
])
def test_format(kobo, expected):
    assert format_naira(kobo) == expected


def test_the_float_problem_is_gone():
    # With floats, 0.1 + 0.2 == 0.3 is False. With kobo it is exact.
    assert parse_naira("0.1") + parse_naira("0.2") == parse_naira("0.3")