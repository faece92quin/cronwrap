"""Tests for cronwrap.schedule."""

import pytest
from cronwrap.schedule import parse_cron, validate_cron, CronExpression


def test_parse_every_minute():
    expr = parse_cron("* * * * *")
    assert isinstance(expr, CronExpression)
    assert expr.minute == "*"
    assert expr.describe() == "every minute"


def test_parse_specific_fields():
    expr = parse_cron("30 6 * * 1")
    assert expr.minute == "30"
    assert expr.hour == "6"
    assert expr.day_of_week == "1"


def test_describe_partial():
    expr = parse_cron("0 12 * * *")
    desc = expr.describe()
    assert "minute=0" in desc
    assert "hour=12" in desc


def test_parse_step_syntax():
    expr = parse_cron("*/15 * * * *")
    assert expr.minute == "*/15"


def test_parse_range_syntax():
    expr = parse_cron("0 9-17 * * 1-5")
    assert expr.hour == "9-17"
    assert expr.day_of_week == "1-5"


def test_parse_wrong_field_count():
    with pytest.raises(ValueError, match="5 cron fields"):
        parse_cron("* * * *")


def test_parse_invalid_field():
    with pytest.raises(ValueError, match="minute"):
        parse_cron("abc * * * *")


def test_validate_cron_valid():
    assert validate_cron("0 0 1 1 *") is None


def test_validate_cron_invalid():
    msg = validate_cron("60 * * * *")
    assert msg is not None
    assert "minute" in msg


def test_raw_preserved():
    raw = "5 4 * * 0"
    expr = parse_cron(raw)
    assert expr.raw == raw
