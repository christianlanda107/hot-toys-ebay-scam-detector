"""
check_listing.py - check one eBay listing for scam red flags.

Answer a few questions about the listing and the seller, and the script
scores it with the same rules used on the dataset (see rules.py).

Run:
    python check_listing.py           asks you the questions
    python check_listing.py --demo    runs on a made-up example listing
"""

import argparse
from datetime import date

from rules import score_listing, risk_level, months_since, describe

ADVICE = {
    "High": ("HIGH RISK: several warning signs together. The safest move is to skip it. "
             "If you still want it, pay only through eBay so the Money Back Guarantee covers you, "
             "and never pay or message outside eBay."),
    "Medium": ("MEDIUM RISK: some warning signs. Look closer before buying: read the seller's "
               "recent feedback, check their other listings, compare the photos with official "
               "product images and read the return policy."),
    "Low": ("LOW RISK: no major warning signs. Still pay only through eBay and check that "
            "the photos match the official product."),
}


# ------------------------------------------------------------------
# Asking questions (each helper keeps asking until the answer is valid)
# ------------------------------------------------------------------
def ask_yes_no(question):
    while True:
        answer = input(f"{question} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please type y or n.")


def ask_number(question, allow_blank=False):
    while True:
        answer = input(f"{question}: ").strip().replace("$", "").replace(",", "")
        if allow_blank and answer == "":
            return None
        try:
            return float(answer)
        except ValueError:
            print("  Please type a number" + (", or press Enter to skip." if allow_blank else "."))


def ask_month(question):
    while True:
        answer = input(f"{question} (YYYY-MM, for example 2023-04): ").strip()
        try:
            if months_since(answer, date.today()) >= 0:
                return answer
        except ValueError:
            pass
        print("  Please use the format YYYY-MM, with a date that isn't in the future.")


# ------------------------------------------------------------------
# Building a listing the rules can read
# ------------------------------------------------------------------
def build_listing(figure_released, labeled_presale, official_price, price, shipping,
                  ships_from_us, returns_accepted, seller_joined, feedback_count,
                  items_sold, observations, as_of=None):
    listing = {
        "figure_released": figure_released,
        "labeled_presale": labeled_presale,
        "reference_price": official_price,
        "total_cost": price + shipping,
        "shipping": shipping,
        "ships_from_us": ships_from_us,
        "returns_accepted": returns_accepted,
        "account_age_months": months_since(seller_joined, as_of or date.today()),
        "feedback_count": feedback_count,
        "items_sold": items_sold,
    }
    listing.update(observations)
    return listing


def listing_from_questions():
    print("Answer a few questions about the listing. Press Ctrl+C to quit.\n")

    print("-- The figure --")
    released = ask_yes_no("Is the figure already released (in stores now)?")
    presale = False if released else ask_yes_no("Does the listing clearly say it's a pre-order?")
    official = ask_number("Official retail price in $ (press Enter if you don't know)", allow_blank=True)

    print("\n-- The listing --")
    price = ask_number("Listing price in $")
    shipping = ask_number("Shipping cost in $")
    ships_from_us = ask_yes_no("Does it ship from the United States?")
    returns = ask_yes_no("Does the seller accept returns?")

    print("\n-- The seller --")
    joined = ask_month("When did the seller join eBay?")
    feedback = ask_number("Seller's feedback score (the number next to their name)")
    sold = ask_number("Seller's total items sold")

    print("\n-- Things you noticed --")
    observations = {
        "off_platform_request": ask_yes_no("Does it ask you to message first or pay outside eBay?"),
        "counterfeit_prone_history": ask_yes_no(
            "Are the seller's past sales mostly knockoff-prone goods (like cheap 'sealed' DVD box sets)?"),
        "copied_listing": ask_yes_no("Have you seen this exact listing text from a different seller?"),
        "condition_conflict": ask_yes_no(
            "Do the condition details contradict each other (like a 'New' title on a Used listing)?"),
        "odd_item_specifics": ask_yes_no("Do the item specifics list things that make no sense for this product?"),
        "unrelated_store_categories": ask_yes_no(
            "Does the seller's store mix in unrelated goods (pet supplies, cameras, etc.)?"),
    }
    return build_listing(released, presale, official, price, shipping, ships_from_us,
                         returns, joined, feedback, sold, observations)


def demo_listing():
    """A made-up listing showing several red flags at once (not a real seller)."""
    print("Demo: an unreleased $305 figure listed as 'in stock' for $649 + $59 shipping\n"
          "from overseas, by a 4-month-old account with 18 feedback and no returns.\n")
    observations = {
        "off_platform_request": False, "counterfeit_prone_history": False,
        "copied_listing": True, "condition_conflict": False,
        "odd_item_specifics": False, "unrelated_store_categories": True,
    }
    # as_of is fixed so the demo gives the same result whenever you run it
    return build_listing(False, False, 304.99, 649.00, 59.00, False, False,
                         "2026-06", 18, 60, observations, as_of=date(2026, 10, 10))


# ------------------------------------------------------------------
# The result
# ------------------------------------------------------------------
def print_result(listing):
    score, fired = score_listing(listing)
    level = risk_level(score)
    print("\n" + "=" * 60)
    print(f"Risk score: {score}    Risk level: {level}")
    print("=" * 60)
    if fired:
        print("Red flags found:")
        for rule_id, points in fired:
            print(f"  +{points}  {describe(rule_id)}")
    else:
        print("No red flags found.")
    print("\n" + ADVICE[level])


def main():
    parser = argparse.ArgumentParser(description="Check one eBay listing for scam red flags.")
    parser.add_argument("--demo", action="store_true", help="run on a made-up example listing")
    args = parser.parse_args()
    try:
        listing = demo_listing() if args.demo else listing_from_questions()
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")
        return
    print_result(listing)


if __name__ == "__main__":
    main()
