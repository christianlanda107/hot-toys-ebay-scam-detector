"""
score_listings.py - score every listing in the dataset and compare the
scores with the manual review.

What it does:
  1. Loads data/listings.csv and data/official_prices.csv
  2. Prepares each listing (total cost, account age, official price, ...)
  3. Scores each listing twice: automatic rules only, then all rules
  4. Compares the scores with the manual verdicts
  5. Prints a report and saves everything to the results/ folder

Run it from anywhere:
    python score_listings.py
"""

from datetime import date
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")                     # save charts as image files, no window
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from rules import (RULES, OBSERVED_FLAGS, HIGH_RISK_THRESHOLD,
                   score_listing, risk_level, months_since)

# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------
PROJECT = Path(__file__).resolve().parent
DATA = PROJECT / "data"
RESULTS = PROJECT / "results"
CHARTS = RESULTS / "charts"

COLLECTION_DATE = date(2026, 10, 10)            # when the listings were recorded
REVIEWER_HIGH_RISK = {"Suspicious", "Likely scam"}
FIGURES = ["Doctor Doom", "Iron Man Mark 85 BD", "Anakin Artisan", "Black Suit Spider-Man"]

# Chart colors (light background). Checked for colorblind safety.
SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE = "#2a78d6", "#eb6834"
RISK_COLORS = {"Low": "#86b6ef", "Medium": "#3987e5", "High": "#104281"}  # one hue, light to dark


# ------------------------------------------------------------------
# 1. Load the data
# ------------------------------------------------------------------
def load_data():
    listings = pd.read_csv(DATA / "listings.csv")
    prices = pd.read_csv(DATA / "official_prices.csv")
    return listings, prices


# ------------------------------------------------------------------
# 2. Prepare each listing for the rules
# ------------------------------------------------------------------
def yes(value):
    """Turn 'yes'/'no' from the CSV into True/False."""
    return str(value).strip().lower() == "yes"


def official_price_lookup(prices):
    """Return a function that finds the official retail price for a listing."""
    by_version = dict(zip(prices["version"], prices["official_price_usd"]))
    highest_by_figure = prices.groupby("figure")["official_price_usd"].max().to_dict()

    def lookup(figure, version):
        if version in by_version:
            return by_version[version]        # can be blank: no official US price
        # Version unclear: use the figure's highest official price, so the
        # price red flags are less likely to fire by mistake.
        return highest_by_figure.get(figure)

    return lookup


def prepare(listings, prices):
    lookup = official_price_lookup(prices)
    df = listings.copy()
    df["total_cost"] = df["price_usd"] + df["shipping_usd"]
    df["shipping"] = df["shipping_usd"]
    df["reference_price"] = [lookup(f, v) for f, v in zip(df["figure"], df["version"])]
    df["account_age_months"] = [months_since(j, COLLECTION_DATE) for j in df["seller_joined"]]
    df["ships_from_us"] = df["ships_from"] == "USA"
    for column in ["figure_released", "labeled_presale", "returns_accepted"] + OBSERVED_FLAGS:
        df[column] = df[column].map(yes)
    df["reviewer_high_risk"] = df["verdict"].isin(REVIEWER_HIGH_RISK)
    return df


# ------------------------------------------------------------------
# 3. Score every listing
# ------------------------------------------------------------------
def add_scores(df):
    """Score each listing with automatic rules only ('auto') and with all rules ('full')."""
    for mode, include_observed in [("auto", False), ("full", True)]:
        scores, flags = [], []
        for listing in df.to_dict("records"):
            score, fired = score_listing(listing, include_observed)
            scores.append(score)
            flags.append(", ".join(f"{rule} (+{points})" for rule, points in fired))
        df[f"score_{mode}"] = scores
        df[f"flags_{mode}"] = flags
        df[f"flagged_{mode}"] = df[f"score_{mode}"] >= HIGH_RISK_THRESHOLD
    df["risk_level"] = df["score_full"].map(risk_level)
    df["agrees"] = df["flagged_full"] == df["reviewer_high_risk"]
    return df


# ------------------------------------------------------------------
# 4. Compare with the manual review
# ------------------------------------------------------------------
def compare(df, mode):
    flagged = df[f"flagged_{mode}"]
    reviewer = df["reviewer_high_risk"]
    return {
        "agree": int((flagged == reviewer).sum()),
        "total": len(df),
        "caught": int((flagged & reviewer).sum()),          # high risk in both
        "reviewer_high": int(reviewer.sum()),
        "flagged": int(flagged.sum()),
        "missed": df.loc[reviewer & ~flagged, "listing_id"].tolist(),
        "false_alarms": df.loc[flagged & ~reviewer, "listing_id"].tolist(),
    }


def by_figure(df):
    """Share of each figure's listings rated high risk, by the review and by the scorer."""
    return (df.groupby("figure")
              .agg(listings=("listing_id", "count"),
                   reviewer=("reviewer_high_risk", "mean"),
                   scorer=("flagged_full", "mean"))
              .reindex(FIGURES))


def rule_stats(df):
    """How many listings each rule fired on, and how many of those the review rated high risk."""
    records = df.to_dict("records")
    rows = []
    for rule_id, points, kind, check in RULES:
        hits = [r for r in records if check(r)]
        rows.append({"rule": rule_id, "points": points, "type": kind,
                     "fired_on": len(hits),
                     "reviewer_high_risk": sum(r["reviewer_high_risk"] for r in hits)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------
# 5a. Charts
# ------------------------------------------------------------------
def style_axes(fig, ax):
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(1)
    ax.tick_params(colors=INK_2, labelsize=9, length=0)
    ax.xaxis.label.set_color(INK_2)
    ax.grid(axis="x", color=GRID, linewidth=1)
    ax.set_axisbelow(True)


def chart_by_figure(table, path):
    fig, ax = plt.subplots(figsize=(8, 4.4), dpi=150)
    style_axes(fig, ax)
    labels = [f"{f}\n(pre-order)" if f == "Doctor Doom" else f for f in table.index]
    positions = range(len(labels))
    bar = 0.32
    gap = 0.03
    reviewer = table["reviewer"] * 100
    scorer = table["scorer"] * 100
    ax.barh([p - bar / 2 - gap for p in positions], reviewer, height=bar, color=BLUE, label="Manual review")
    ax.barh([p + bar / 2 + gap for p in positions], scorer, height=bar, color=ORANGE, label="Scorer")
    for p, r, s in zip(positions, reviewer, scorer):
        ax.text(r + 1.5, p - bar / 2 - gap, percent(r / 100), va="center", fontsize=9, color=INK_2)
        ax.text(s + 1.5, p + bar / 2 + gap, percent(s / 100), va="center", fontsize=9, color=INK_2)
    ax.set_yticks(list(positions))
    ax.set_yticklabels(labels, color=INK, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(PercentFormatter())
    ax.set_xlabel("Listings rated high risk")
    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK_2)
    fig.suptitle("The unreleased figure had by far the most high-risk listings",
                 x=0.02, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.text(0.02, 0.895, "Share of each figure's listings rated high risk, by manual review and by the scorer",
             fontsize=9, color=INK_2)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def chart_scores(df, path):
    data = df.sort_values(["score_full", "listing_id"], ascending=[True, False])
    review_level = data["verdict"].map(
        lambda v: "High" if v in REVIEWER_HIGH_RISK else ("Medium" if v == "Medium risk" else "Low"))

    fig, ax = plt.subplots(figsize=(8, 9.5), dpi=150)
    style_axes(fig, ax)
    positions = range(len(data))
    ax.barh(positions, data["score_full"], height=0.6, color=[RISK_COLORS[r] for r in review_level])
    for p, score in zip(positions, data["score_full"]):
        ax.text(score + 0.15, p, str(score), va="center", fontsize=8, color=INK_2)
    ax.set_yticks(list(positions))
    ax.set_yticklabels([f"{i}  {f}" for i, f in zip(data["listing_id"], data["figure"])],
                       fontsize=8, color=INK)
    ax.set_ylim(-0.7, len(data) + 0.5)
    ax.set_xlim(0, data["score_full"].max() + 1.5)
    ax.set_xlabel("Risk score (points)")

    # The high-risk threshold
    ax.axvline(HIGH_RISK_THRESHOLD, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(HIGH_RISK_THRESHOLD + 0.1, len(data) + 0.05, f"High-risk threshold ({HIGH_RISK_THRESHOLD} points)",
            fontsize=8, color=INK_2, va="center")

    handles = [plt.Rectangle((0, 0), 1, 1, color=RISK_COLORS[level]) for level in ["High", "Medium", "Low"]]
    ax.legend(handles, ["High (suspicious / likely scam)", "Medium", "Low (probably legit)"],
              title="Manual review rating", title_fontsize=9, loc="lower right",
              frameon=False, fontsize=8, labelcolor=INK_2)
    fig.suptitle("Risk score for each listing", x=0.02, y=0.988, ha="left",
                 fontsize=12, fontweight="bold", color=INK)
    fig.text(0.02, 0.948, "Bars that reach the dashed line are flagged by the scorer; color shows the manual rating",
             fontsize=9, color=INK_2)
    fig.tight_layout(rect=(0, 0, 1, 0.945))
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


# ------------------------------------------------------------------
# 5b. Text report and saved files
# ------------------------------------------------------------------
def percent(fraction):
    """0.125 -> '13%' (rounds halves up, unlike Python's default rounding)."""
    return f"{int(fraction * 100 + 0.5)}%"


def pct(part, whole):
    return percent(part / whole) if whole else "n/a"


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def comparison_rows(auto, full):
    return [
        ["Agreement with the manual review",
         f"{auto['agree']}/{auto['total']} ({pct(auto['agree'], auto['total'])})",
         f"{full['agree']}/{full['total']} ({pct(full['agree'], full['total'])})"],
        ["High-risk listings caught",
         f"{auto['caught']} of {auto['reviewer_high']}", f"{full['caught']} of {full['reviewer_high']}"],
        ["Scorer flags that matched the review",
         f"{auto['caught']} of {auto['flagged']}", f"{full['caught']} of {full['flagged']}"],
        ["Missed (review: high, scorer: not)",
         ", ".join(auto["missed"]) or "none", ", ".join(full["missed"]) or "none"],
        ["False alarms (scorer: high, review: not)",
         ", ".join(auto["false_alarms"]) or "none", ", ".join(full["false_alarms"]) or "none"],
    ]


def print_report(df, auto, full, figures):
    print("=" * 66)
    print(f"HOT TOYS SCAM LISTING SCORER  -  {len(df)} listings, "
          f"high risk = {HIGH_RISK_THRESHOLD}+ points")
    print("=" * 66)
    print(f"{'':40}{'Automatic':>12}{'All rules':>14}")
    for label, a, f in comparison_rows(auto, full):
        print(f"{label:40}{a:>12}{f:>14}")
    print()
    print(f"{'High-risk share by figure':40}{'Review':>12}{'Scorer':>14}")
    for figure, row in figures.iterrows():
        print(f"  {figure:38}{percent(row['reviewer']):>12}{percent(row['scorer']):>14}")
    print()


def write_summary(df, auto, full, figures, rules_table, path):
    comparison = md_table(["", "Automatic rules only", "All rules"], comparison_rows(auto, full))

    figure_rows = [[figure, int(row["listings"]), percent(row["reviewer"]), percent(row["scorer"])]
                   for figure, row in figures.iterrows()]
    figure_table = md_table(["Figure", "Listings", "Manual review", "Scorer"], figure_rows)

    rule_rows = rules_table[["rule", "points", "type", "fired_on", "reviewer_high_risk"]].values.tolist()
    rule_table = md_table(["Rule", "Points", "Type", "Listings it fired on",
                           "...of which the review rated high risk"], rule_rows)

    listing_rows = [
        [r["listing_id"], r["figure"], r["score_auto"], r["score_full"], r["risk_level"],
         r["verdict"], "yes" if r["agrees"] else "**no**", r["flags_full"] or "-"]
        for r in df.sort_values(["score_full", "listing_id"], ascending=[False, True]).to_dict("records")
    ]
    listing_table = md_table(["ID", "Figure", "Score (automatic)", "Score (all rules)", "Risk level",
                              "Manual verdict", "Agrees?", "Red flags (all rules)"], listing_rows)

    text = "\n".join([
        "# Results",
        "",
        "_Generated by `score_listings.py`. Re-run the script instead of editing this file._",
        "",
        f"{len(df)} listings were scored. A score of **{HIGH_RISK_THRESHOLD} or more** counts as high risk. "
        "In the manual review, high risk means a verdict of Suspicious or Likely scam.",
        "",
        "## Scorer vs. manual review",
        "",
        comparison,
        "",
        "## High-risk share by figure",
        "",
        figure_table,
        "",
        "![High-risk share by figure](charts/high_risk_by_figure.png)",
        "",
        "## How often each rule fired",
        "",
        rule_table,
        "",
        "## Every listing",
        "",
        listing_table,
        "",
        "![Risk score for each listing](charts/risk_scores.png)",
        "",
    ])
    path.write_text(text, encoding="utf-8")


def save_scored_csv(df, path):
    columns = ["listing_id", "figure", "version", "seller_id", "total_cost", "reference_price",
               "score_auto", "score_full", "risk_level", "flagged_full", "verdict",
               "reviewer_high_risk", "agrees", "flags_full"]
    out = df[columns].rename(columns={"flagged_full": "scorer_high_risk", "flags_full": "red_flags"})
    out.to_csv(path, index=False)


# ------------------------------------------------------------------
# Run everything
# ------------------------------------------------------------------
def main():
    CHARTS.mkdir(parents=True, exist_ok=True)
    listings, prices = load_data()
    df = add_scores(prepare(listings, prices))

    auto = compare(df, "auto")
    full = compare(df, "full")
    figures = by_figure(df)
    rules_table = rule_stats(df)

    print_report(df, auto, full, figures)
    save_scored_csv(df, RESULTS / "scored_listings.csv")
    write_summary(df, auto, full, figures, rules_table, RESULTS / "summary.md")
    chart_by_figure(figures, CHARTS / "high_risk_by_figure.png")
    chart_scores(df, CHARTS / "risk_scores.png")
    print("Saved: results/scored_listings.csv, results/summary.md, results/charts/")


if __name__ == "__main__":
    main()
