"""
rules.py - the red-flag rules and the scoring logic.

Every rule looks at one listing and answers a yes/no question, like
"Is the seller's account less than a year old?". If the answer is yes,
the rule adds its points to the listing's risk score.

Both score_listings.py (the dataset) and check_listing.py (a single new
listing) import this file, so the rules only live in one place.

A "listing" here is a dictionary with these prepared fields:
    figure_released     True if the figure is out in stores
    labeled_presale     True if the listing says it's a pre-order
    account_age_months  How old the seller's account is
    items_sold          Seller's total items sold
    feedback_count      Seller's feedback score
    returns_accepted    True if returns are accepted
    total_cost          Price + shipping
    shipping            Shipping cost alone
    reference_price     Official retail price (None if unknown)
    ships_from_us       True if the item ships from the United States
  plus the reviewer observations (True/False):
    off_platform_request, counterfeit_prone_history, copied_listing,
    condition_conflict, odd_item_specifics, unrelated_store_categories
"""

import math
from datetime import date

# A score at or above this number counts as HIGH risk.
HIGH_RISK_THRESHOLD = 4
# A score at or above this number (but below high) counts as MEDIUM risk.
MEDIUM_RISK_THRESHOLD = 2

# Reviewer observations: things a person notices that aren't a single number.
OBSERVED_FLAGS = [
    "off_platform_request",
    "counterfeit_prone_history",
    "copied_listing",
    "condition_conflict",
    "odd_item_specifics",
    "unrelated_store_categories",
]


# ------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------
def is_missing(value):
    """True if a value is empty (None or NaN, which is how pandas stores blanks)."""
    return value is None or (isinstance(value, float) and math.isnan(value))


def months_since(joined, as_of):
    """
    How many months between a 'YYYY-MM' join date and another date.
    Example: months_since("2025-12", date(2026, 10, 10)) -> about 10.3
    """
    year, month = (int(part) for part in str(joined).split("-"))
    joined_date = date(year, month, 1)
    return (as_of - joined_date).days / 30.44   # average days per month


# ------------------------------------------------------------------
# The rules. Each function returns True if the red flag is present.
# ------------------------------------------------------------------

# --- Automatic rules: computed from the listing's facts ---

def ships_before_release(listing):
    """Sells a figure that isn't out yet, without calling it a pre-order."""
    return (not listing["figure_released"]) and (not listing["labeled_presale"])


def new_account(listing):
    """Seller's account is less than 12 months old."""
    return listing["account_age_months"] < 12


def new_account_high_volume(listing):
    """New account that has already sold 300+ items (possibly bought or recycled)."""
    return new_account(listing) and listing["items_sold"] >= 300


def low_feedback(listing):
    """Seller has fewer than 50 feedback."""
    return listing["feedback_count"] < 50


def no_returns(listing):
    """Seller doesn't accept returns."""
    return not listing["returns_accepted"]


def over_twice_official(listing):
    """Total cost is more than double the official retail price."""
    ref = listing["reference_price"]
    return not is_missing(ref) and listing["total_cost"] > 2 * ref


def under_official_overseas(listing):
    """Cheaper than official retail AND ships from overseas (a common bootleg pattern)."""
    ref = listing["reference_price"]
    return (not is_missing(ref)
            and listing["total_cost"] < ref
            and not listing["ships_from_us"])


def inflated_shipping(listing):
    """Shipping of $100 or more, which makes the price look lower than it really is."""
    return listing["shipping"] >= 100


# --- Reviewer observations: recorded by a person looking at the listing ---

def off_platform_request(listing):
    """Asks buyers to message first or pay outside eBay."""
    return listing["off_platform_request"]


def counterfeit_prone_history(listing):
    """Seller's past sales are mostly in a knockoff-heavy category."""
    return listing["counterfeit_prone_history"]


def copied_listing(listing):
    """Same listing text appears word-for-word on another seller account."""
    return listing["copied_listing"]


def condition_conflict(listing):
    """Condition details contradict each other (e.g. 'New' title on a Used listing)."""
    return listing["condition_conflict"]


def odd_item_specifics(listing):
    """Item specifics contain values unrelated to the product."""
    return listing["odd_item_specifics"]


def unrelated_store_categories(listing):
    """Seller's store mixes in unrelated goods (pet supplies, cameras, etc.)."""
    return listing["unrelated_store_categories"]


# ------------------------------------------------------------------
# The rule list: points for each rule.
#   4 = critical (enough to make a listing high risk on its own)
#   3 = strong   2 = medium   1 = weak
# "observed" rules need a person's judgment; "automatic" rules don't.
# ------------------------------------------------------------------
RULES = [
    # id                          points  type         function
    ("off_platform_request",       4, "observed",  off_platform_request),
    ("counterfeit_prone_history",  4, "observed",  counterfeit_prone_history),
    ("ships_before_release",       3, "automatic", ships_before_release),
    ("copied_listing",             2, "observed",  copied_listing),
    ("condition_conflict",         2, "observed",  condition_conflict),
    ("new_account_high_volume",    2, "automatic", new_account_high_volume),
    ("low_feedback",               2, "automatic", low_feedback),
    ("new_account",                1, "automatic", new_account),
    ("no_returns",                 1, "automatic", no_returns),
    ("over_twice_official",        1, "automatic", over_twice_official),
    ("under_official_overseas",    1, "automatic", under_official_overseas),
    ("inflated_shipping",          1, "automatic", inflated_shipping),
    ("odd_item_specifics",         1, "observed",  odd_item_specifics),
    ("unrelated_store_categories", 1, "observed",  unrelated_store_categories),
]


def describe(rule_id):
    """Plain-English description of a rule (the first line of its docstring)."""
    for rid, _points, _kind, func in RULES:
        if rid == rule_id:
            return func.__doc__.strip()
    raise KeyError(rule_id)


# ------------------------------------------------------------------
# Scoring
# ------------------------------------------------------------------
def score_listing(listing, include_observed=True):
    """
    Run every rule on one listing.

    Returns (score, fired) where fired is a list of (rule_id, points)
    for each red flag that was found. Set include_observed=False to use
    only the automatic rules.
    """
    score = 0
    fired = []
    for rule_id, points, kind, check in RULES:
        if kind == "observed" and not include_observed:
            continue
        if check(listing):
            score += points
            fired.append((rule_id, points))
    return score, fired


def risk_level(score):
    """Turn a score into Low / Medium / High."""
    if score >= HIGH_RISK_THRESHOLD:
        return "High"
    if score >= MEDIUM_RISK_THRESHOLD:
        return "Medium"
    return "Low"
