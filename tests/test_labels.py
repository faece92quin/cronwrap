"""
Tests for cronwrap.labels
"""

import pytest

from cronwrap.labels import (
    format_labels,
    labels_match,
    merge_labels,
    parse_label,
    parse_labels,
)


# ---------------------------------------------------------------------------
# parse_label
# ---------------------------------------------------------------------------

def test_parse_label_basic():
    assert parse_label("env=production") == ("env", "production")


def test_parse_label_key_lowercased():
    assert parse_label("Team=backend") == ("team", "backend")


def test_parse_label_value_with_equals():
    # Only the first '=' is the separator
    assert parse_label("expr=a=b") == ("expr", "a=b")


def test_parse_label_missing_equals_raises():
    with pytest.raises(ValueError, match="key=value"):
        parse_label("noequals")


def test_parse_label_empty_key_raises():
    with pytest.raises(ValueError, match="must not be empty"):
        parse_label("=value")


# ---------------------------------------------------------------------------
# parse_labels
# ---------------------------------------------------------------------------

def test_parse_labels_empty_list():
    assert parse_labels([]) == {}


def test_parse_labels_multiple():
    result = parse_labels(["env=prod", "team=ops"])
    assert result == {"env": "prod", "team": "ops"}


def test_parse_labels_last_value_wins():
    result = parse_labels(["env=staging", "env=prod"])
    assert result == {"env": "prod"}


# ---------------------------------------------------------------------------
# format_labels
# ---------------------------------------------------------------------------

def test_format_labels_sorted():
    assert format_labels({"z": "last", "a": "first"}) == ["a=first", "z=last"]


def test_format_labels_empty():
    assert format_labels({}) == []


# ---------------------------------------------------------------------------
# labels_match
# ---------------------------------------------------------------------------

def test_labels_match_all_present():
    assert labels_match({"env": "prod", "team": "ops"}, {"env": "prod"}) is True


def test_labels_match_wrong_value():
    assert labels_match({"env": "prod"}, {"env": "staging"}) is False


def test_labels_match_missing_key():
    assert labels_match({"team": "ops"}, {"env": "prod"}) is False


def test_labels_match_empty_required():
    assert labels_match({"env": "prod"}, {}) is True


# ---------------------------------------------------------------------------
# merge_labels
# ---------------------------------------------------------------------------

def test_merge_labels_later_wins():
    result = merge_labels({"env": "staging"}, {"env": "prod", "team": "ops"})
    assert result == {"env": "prod", "team": "ops"}


def test_merge_labels_none_sources_ignored():
    result = merge_labels(None, {"env": "prod"}, None)
    assert result == {"env": "prod"}


def test_merge_labels_all_none():
    assert merge_labels(None, None) == {}
