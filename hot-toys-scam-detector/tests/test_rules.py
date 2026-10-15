"""Tests for the red-flag rules. Run with:  pytest"""

from datetime import date

import rules
from rules import score_listing, risk_level, months_since, HIGH_RISK_THRESHOLD


def make_listing(**changes):
    """A clean, low-risk listing. Pass keyword arguments to change any field."""
    listing = {
        "figure_released": True,
        "labeled_presale": False,
        "account_age_months": 60,
        "items_sold": 1000,
        "feedback_count": 500,
        "returns_accepted": True,
        "total_cost": 450.0,
        "shipping": 20.0,
        "reference_price": 400.0,
        "ships_from_us": True,
        "off_platform_request": False,
        "counterfeit_prone_history": False,
        "copied_listing": False,
        "condition_conflict": False,
        "odd_item_specifics": False,
        "unrelated_store_categories": False,
    }
    listing.update(changes)
    return listing


def flags(listing, include_observed=True):
    """Just the ids of the rules that fired."""
    return [rule_id for rule_id, _points in score_listing(listing, include_observed)[1]]


def test_clean_listing_has_no_red_flags():
    score, fired = score_listing(make_listing())
    assert score == 0
    assert fired == []
    assert risk_level(score) == "Low"


def test_unreleased_figure_sold_as_in_stock_is_flagged():
    listing = make_listing(figure_released=False, labeled_presale=False)
    assert flags(listing) == ["ships_before_release"]
    assert score_listing(listing)[0] == 3


def test_labeled_preorder_is_not_flagged():
    assert flags(make_listing(figure_released=False, labeled_presale=True)) == []


def test_new_account_with_many_sales_gets_both_account_rules():
    fired = flags(make_listing(account_age_months=6, items_sold=500))
    assert "new_account" in fired
    assert "new_account_high_volume" in fired


def test_new_account_with_few_sales_only_gets_new_account():
    assert flags(make_listing(account_age_months=6, items_sold=20)) == ["new_account"]


def test_price_rules_are_skipped_when_official_price_is_unknown():
    fired = flags(make_listing(reference_price=float("nan"), total_cost=5000.0, ships_from_us=False))
    assert "over_twice_official" not in fired
    assert "under_official_overseas" not in fired


def test_cheap_listing_is_only_flagged_when_it_ships_from_overseas():
    assert "under_official_overseas" in flags(make_listing(total_cost=300.0, ships_from_us=False))
    assert "under_official_overseas" not in flags(make_listing(total_cost=300.0, ships_from_us=True))


def test_inflated_shipping():
    assert flags(make_listing(shipping=119.99)) == ["inflated_shipping"]
    assert flags(make_listing(shipping=59.99)) == []


def test_observed_flags_are_ignored_in_automatic_mode():
    listing = make_listing(copied_listing=True, counterfeit_prone_history=True)
    assert score_listing(listing, include_observed=False)[0] == 0
    assert score_listing(listing)[0] == 6


def test_a_critical_flag_alone_makes_a_listing_high_risk():
    score, _ = score_listing(make_listing(off_platform_request=True))
    assert score >= HIGH_RISK_THRESHOLD
    assert risk_level(score) == "High"


def test_risk_level_boundaries():
    assert [risk_level(s) for s in range(6)] == ["Low", "Low", "Medium", "Medium", "High", "High"]


def test_months_since():
    assert round(months_since("2025-10", date(2026, 10, 1))) == 12
    assert months_since("2026-10", date(2026, 10, 10)) < 1


def test_every_rule_is_described_and_weighted():
    for rule_id, points, kind, check in rules.RULES:
        assert check.__doc__, f"{rule_id} needs a description"
        assert points in (1, 2, 3, 4)
        assert kind in ("automatic", "observed")
