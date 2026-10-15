# Hot Toys eBay Scam Listing Detector

A rule-based risk scorer for eBay listings of high-end collectible figures, built on a hand-collected dataset of 30 Hot Toys listings ($300–$1,000 each).

Hot Toys figures are expensive, limited and heavily counterfeited, which makes them a good small-scale test case for marketplace fraud detection. This project records listings for four figures, reviews each one for scam signals, turns those signals into weighted rules, and measures how well the rules match the manual review.

## Key findings

- **The unreleased figure was by far the riskiest.** 4 of 7 listings (57%) for a figure still on pre-order (Doctor Doom from *Avengers: Doomsday*) were rated suspicious or likely scams, compared with 0–14% for the three figures already on the market.
- **The most common trick was "in stock" claims for a figure that doesn't exist yet.** 5 of the 7 Doom listings claimed the figure was in hand or would arrive within weeks, even though official retailers don't expect it until 2027. Four of those five were rated high risk.
- **Copied listings were the cleanest signal.** Four listings were word-for-word copies posted on two pairs of seller accounts, and all four were rated high risk.
- **Some common worries were weak signals.** "No returns accepted" appeared on 14 listings, but only 2 of them were rated high risk, so it only adds 1 point.
- **The scorer agreed with the manual review on 27 of 30 listings (90%)** and caught 5 of the 6 listings rated high risk.

![High-risk share by figure](results/charts/high_risk_by_figure.png)

## How it works

### 1. Data collection

Listings for four figures were found through normal eBay searches on October 9–10, 2026, and reviewed one at a time:

| Figure | Status | Listings |
|---|---|---|
| Doctor Doom (*Avengers: Doomsday*) | Pre-order only, official release expected 2027 | 7 |
| Iron Man Mark 85, Battle Damaged | Released | 8 |
| Anakin Skywalker Artisan Edition | Released, limited (one listing is a related Japan-exclusive Artisan release) | 8 |
| Spider-Man Black Suit Deluxe (*Spider-Man 3*) | Released | 7 |

For each listing, the price, shipping, seller history, return policy and listing details were recorded, along with official retail prices for comparison. Each listing then got a manual verdict: Probably legit, Medium risk, Suspicious or Likely scam. The full data dictionary is in [`data/README.md`](data/README.md).

### 2. Red-flag rules

Each rule checks for one red flag and adds points to the listing's risk score. **Automatic** rules are calculated from the listing's facts. **Observed** rules record something a person noticed, like two sellers posting the same listing.

| Rule | Points | Type | Red flag |
|---|---|---|---|
| `off_platform_request` | 4 | Observed | Asks buyers to message first or pay outside eBay |
| `counterfeit_prone_history` | 4 | Observed | Seller's past sales are mostly in a knockoff-heavy category |
| `ships_before_release` | 3 | Automatic | Sells an unreleased figure without calling it a pre-order |
| `copied_listing` | 2 | Observed | Same listing text appears on another seller account |
| `condition_conflict` | 2 | Observed | Condition details contradict each other |
| `new_account_high_volume` | 2 | Automatic | Account under a year old with 300+ sales |
| `low_feedback` | 2 | Automatic | Fewer than 50 feedback |
| `new_account` | 1 | Automatic | Account under a year old |
| `no_returns` | 1 | Automatic | No returns accepted |
| `over_twice_official` | 1 | Automatic | Total cost more than double the official price |
| `under_official_overseas` | 1 | Automatic | Below official price and ships from overseas |
| `inflated_shipping` | 1 | Automatic | Shipping of $100 or more |
| `odd_item_specifics` | 1 | Observed | Item specifics unrelated to the product |
| `unrelated_store_categories` | 1 | Observed | Seller's store mixes in unrelated goods |

The points follow a simple scale: **4** is critical (enough to flag a listing on its own), **3** is strong, **2** medium and **1** weak.

### 3. Scoring

A listing's score is the sum of the points for every red flag it has. **4 or more points is high risk**, 2–3 is medium and 0–1 is low. A score of 4 takes either one critical signal or a combination, such as a strong signal plus a weak one, so no single weak signal can flag a listing.

### 4. Evaluation

Each listing is scored twice, once with automatic rules only and once with all rules, and both are compared with the manual verdicts. A listing counts as high risk in the review if its verdict was Suspicious or Likely scam.

## Results

| | Automatic rules only | All rules |
|---|---|---|
| Agreement with the manual review | 27/30 (90%) | 27/30 (90%) |
| High-risk listings caught | 4 of 6 | 5 of 6 |
| Scorer flags that matched the review | 4 of 5 | 5 of 7 |

Adding the observed rules caught one more high-risk listing (L27, a seller whose history was mostly knockoff-looking DVD box sets) but added one more false alarm. Overall agreement stayed the same.

With all rules, the scorer disagreed with the manual review on three listings:

- **L13 (missed, score 3):** a used figure listed without saying so in the title, with three "used" units at about retail price. It fell one point short of the threshold.
- **L21 (flagged, score 4) and L29 (flagged, score 6):** both were rated medium risk in the review, so the scorer was stricter than the reviewer on two borderline listings.

![Risk score for each listing](results/charts/risk_scores.png)

The full per-listing breakdown, including every red flag that fired, is in [`results/summary.md`](results/summary.md) and [`results/scored_listings.csv`](results/scored_listings.csv).

## What changed along the way

Some early assumptions didn't hold up once they were checked:

- **Dropped a rule about feedback replies under a different name.** Several sellers replied to feedback under a different username than their store name. That looked like a sign of renamed or linked accounts, but eBay stores routinely show a store name that differs from the account's user ID, so it wasn't a reliable signal.
- **Dropped a "seller is new to this category" rule.** It couldn't be defined consistently. For example, is a seller of Star Wars lightsaber parts new to Star Wars figures?
- **Filtered out eBay's autofill junk.** Some unrelated sellers had identical nonsense item specifics (like "Vehicle Type: Ship" on an action figure). Since those come from eBay's own product catalog, only odd values unique to one listing count as a red flag.
- **Double-checked product codes.** One Doom product code (MMS902) first looked fake, but turned out to be a separate limited-edition Doom figure.

## Limitations

- **Small sample.** 30 listings, 4 figures, one weekend. The percentages describe this dataset, not eBay as a whole.
- **Optimistic accuracy.** The rules and threshold were designed while looking at these same listings, so the 90% agreement is likely higher than it would be on new listings.
- **Verdicts are judgments, not confirmed fraud.** Nothing was purchased, so no listing is proven to be a scam. The verdicts describe how many warning signs each listing showed.
- **Observed rules depend on the reviewer.** Another person might mark some observations differently.
- **Some prices are estimates.** The Spider-Man Special Edition (MMS728B) price is assumed to match the regular Deluxe. Four listings didn't say which version they were, so the scorer used the highest official price for that figure.
- **A snapshot in time.** Listings, prices and seller stats change. One "in stock" Doom listing (L07) came from a long-established Hong Kong seller that may really have had early stock.

## Ethics and privacy

- No scraper and no eBay API were used. Listings were found through normal searches and reviewed individually.
- Nothing was bought or bid on, and no sellers were contacted.
- Seller usernames and listing links were removed and replaced with IDs (`S01`–`S30`, `L01`–`L30`), so the project doesn't publicly accuse real accounts. The raw research notes are kept private.

## Run it yourself

Requires Python 3.9 or newer.

```bash
pip install -r requirements.txt

python score_listings.py          # score the dataset and regenerate results/
python check_listing.py --demo    # check a made-up example listing
python check_listing.py           # check a real listing by answering questions
pytest                            # run the tests
```

`check_listing.py` asks about the listing, the seller and anything suspicious you noticed, then prints a risk score, the red flags it found and what to do next:

```
Risk score: 11    Risk level: High
Red flags found:
  +3  Sells a figure that isn't out yet, without calling it a pre-order.
  +2  Same listing text appears word-for-word on another seller account.
  +2  Seller has fewer than 50 feedback.
  ...
```

## Project structure

```
hot-toys-scam-detector/
├── data/
│   ├── listings.csv            30 anonymized listings + manual verdicts
│   ├── official_prices.csv     official retail prices and sources
│   └── README.md               data dictionary
├── results/                    generated by score_listings.py
│   ├── scored_listings.csv
│   ├── summary.md
│   └── charts/
├── tests/
│   ├── test_rules.py           checks each rule and the scoring
│   └── test_dataset.py         checks the data files are clean
├── rules.py                    the red-flag rules and scoring logic
├── score_listings.py           scores the dataset and compares with the review
├── check_listing.py            checks a single new listing
├── requirements.txt
└── LICENSE
```

## Next steps

- **Test on fresh listings** collected later to get an honest accuracy number.
- **Re-check flagged listings after a few weeks.** If eBay removed them, that's a rough way to confirm the verdicts.
- **Collect more data,** both more listings per figure and other heavily counterfeited collectibles like sneakers and trading cards.
- **Learn the weights from data** instead of setting them by hand, once there are enough examples.
- **Turn the checker into a simple web page** so other collectors can use it.

## Built with

Python, pandas, matplotlib and pytest.

---

**Christian Landa** · Cybersecurity student, Illinois State University · [LinkedIn](https://www.linkedin.com/in/christian-landa-619100431)
