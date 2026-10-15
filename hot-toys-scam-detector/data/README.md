# Data

## `listings.csv`

30 eBay listings for four Hot Toys figures, recorded on **October 9–10, 2026**. Each row is one listing.

Seller usernames and listing links were removed and replaced with IDs (`S01`–`S30`, `L01`–`L30`). The verdicts describe risk signals, not proven fraud, and I didn't want to publicly label real accounts as scammers. The raw spreadsheet with names and links is kept private.

| Column | Meaning |
|---|---|
| `listing_id` | Listing ID, `L01`–`L30` |
| `figure` | Which figure the listing is for |
| `figure_released` | `yes` if the figure had been released when the data was collected, `no` if it was still pre-order only |
| `version` | Official Hot Toys product code. `unclear` when the listing didn't say which version it was |
| `seller_id` | Anonymized seller ID |
| `condition` | Condition the listing was posted under (`New` / `Used`) |
| `price_usd` | Listed price in US dollars (for the one auction, the current bid at the time) |
| `shipping_usd` | Shipping cost to the US |
| `labeled_presale` | `yes` if the listing clearly said it was a pre-order |
| `ships_from` | Country the item ships from |
| `seller_joined` | Month the seller's account was created (`YYYY-MM`) |
| `feedback_count` | Seller's feedback score |
| `positive_feedback_pct` | Seller's positive feedback percentage (blank if they had none) |
| `items_sold` | Total items the seller had sold |
| `returns_accepted` | `yes` / `no` |
| `return_policy` | Return window and who pays return shipping |
| `verdict` | Manual review result: `Probably legit`, `Probably legit (unconfirmed)`, `Medium risk`, `Suspicious` or `Likely scam` |
| `notes` | What stood out in the review |

### Reviewer observations

These columns record things a person noticed that can't be read from a single number. Each is `yes` or `no`.

| Column | Marked `yes` when... |
|---|---|
| `copied_listing` | The same title or listing text appears word-for-word on a different seller account |
| `condition_conflict` | Details about condition contradict each other (for example, "New" in the title on a listing posted as Used, or several "used" units at retail price) |
| `odd_item_specifics` | The item specifics contain values unrelated to the product that are unique to this listing. Junk values that appear identically across many unrelated sellers were treated as eBay catalog autofill and not counted |
| `unrelated_store_categories` | The seller's store includes several categories with no connection to toys, collectibles or pop-culture media (such as pet supplies, cameras, baby goods or business equipment) |
| `counterfeit_prone_history` | The seller's past sales are mostly in a category known for knockoffs (for example, "new sealed" DVD box sets with garbled titles) |
| `off_platform_request` | The listing asks buyers to message first or pay outside eBay. Not observed in this dataset, but kept because it's a classic scam signal |

## `official_prices.csv`

Official retail price for each product code, used to spot listings priced far above or below retail.

| Column | Meaning |
|---|---|
| `version` | Hot Toys product code |
| `figure` | Figure name, matching `listings.csv` |
| `name` | Full product name |
| `official_price_usd` | Official US retail price (blank if there isn't one) |
| `note` | Release status or caveats |
| `source` | Where the price came from |

When a listing's version is `unclear`, the scorer uses the highest official price for that figure, so price-based red flags are less likely to fire by mistake. The MMS728B price is an assumption (same as MMS728) and is marked as such.
