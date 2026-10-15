"""Checks that the dataset is clean before anything is scored. Run with:  pytest"""

import score_listings
from rules import OBSERVED_FLAGS

YES_NO_COLUMNS = ["figure_released", "labeled_presale", "returns_accepted"] + OBSERVED_FLAGS
VERDICTS = {"Probably legit", "Probably legit (unconfirmed)", "Medium risk", "Suspicious", "Likely scam"}


def test_listings_file_is_valid():
    listings, prices = score_listings.load_data()
    assert len(listings) == 30
    assert listings["listing_id"].is_unique
    assert listings["seller_id"].is_unique
    for column in YES_NO_COLUMNS:
        assert set(listings[column]) <= {"yes", "no"}, column
    assert set(listings["verdict"]) <= VERDICTS
    assert (listings["price_usd"] > 0).all()
    assert (listings["shipping_usd"] >= 0).all()


def test_every_figure_has_official_prices():
    listings, prices = score_listings.load_data()
    assert set(listings["figure"]) <= set(prices["figure"])


def test_known_versions_are_in_the_price_table():
    listings, prices = score_listings.load_data()
    versions = set(listings["version"]) - {"unclear"}
    assert versions <= set(prices["version"])
