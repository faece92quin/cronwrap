"""Tests for cronwrap.tags."""
import pytest
from cronwrap.tags import (
    normalize_tag,
    normalize_tags,
    tags_match,
    tags_match_any,
    format_tags,
    parse_tags_arg,
)


def test_normalize_tag_strips_and_lowercases():
    assert normalize_tag("  Prod  ") == "prod"


def test_normalize_tags_deduplicates_and_sorts():
    result = normalize_tags(["beta", "Alpha", "alpha", " Beta "])
    assert result == ["alpha", "beta"]


def test_normalize_tags_ignores_blank():
    assert normalize_tags(["", "  ", "ok"]) == ["ok"]


def test_tags_match_all_required_present():
    assert tags_match(["prod", "nightly"], ["prod"]) is True


def test_tags_match_missing_required():
    assert tags_match(["prod"], ["prod", "nightly"]) is False


def test_tags_match_empty_required_always_true():
    assert tags_match([], []) is True
    assert tags_match(["prod"], []) is True


def test_tags_match_any_one_present():
    assert tags_match_any(["prod", "staging"], ["staging", "dev"]) is True


def test_tags_match_any_none_present():
    assert tags_match_any(["prod"], ["dev", "staging"]) is False


def test_tags_match_any_empty_candidates():
    assert tags_match_any(["prod"], []) is True


def test_format_tags_non_empty():
    assert format_tags(["alpha", "beta"]) == "alpha, beta"


def test_format_tags_empty():
    assert format_tags([]) == "(none)"


def test_parse_tags_arg_comma_separated():
    result = parse_tags_arg("Prod,Nightly, Beta")
    assert result == ["beta", "nightly", "prod"]


def test_parse_tags_arg_single():
    assert parse_tags_arg("prod") == ["prod"]
