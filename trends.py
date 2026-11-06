"""Pull Google Trends data for many keywords and countries, without pytrends 429s.

Usage:
    export APIFY_TOKEN=...            # free account: https://console.apify.com/sign-up
    python trends.py "air fryer" "standing desk" matcha --geo US GB --timeframe "today 12-m"

Writes two CSV files:
    trends_summary.csv  one row per keyword x country: trend (rising/falling/flat), percentOfPeak, peakDate, ...
    trends_series.csv   the full interest-over-time series in long format (keyword, geo, date, value)

The scraping runs on Apify (https://apify.com/najiva/google-trends-reliable). It handles
proxies, cookies and 429 retries. Pricing: $1.50 per 1,000 results + $0.01 per run;
failed and no-data keywords are not charged.
"""
import argparse
import csv
import os
import sys

from apify_client import ApifyClient

ACTOR = "najiva/google-trends-reliable"
SUMMARY_FIELDS = ["keyword", "geo", "timeframe", "trend", "trendChangePercent", "percentOfPeak",
                  "peakDate", "latestValue", "topRisingQueries", "otherRisingQueries"]


def fetch(keywords, geos, timeframe, token):
    client = ApifyClient(token)
    run = client.actor(ACTOR).call(run_input={"keywords": keywords, "geos": geos, "timeframe": timeframe})
    if run is None or run.get("status") != "SUCCEEDED":
        sys.exit(f"Run did not succeed: {run and run.get('status')}")
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("keywords", nargs="+", help="search terms, each fetched separately")
    p.add_argument("--geo", nargs="*", default=[], help="country codes such as US GB DE (default: worldwide)")
    p.add_argument("--timeframe", default="today 12-m", help='e.g. "now 7-d", "today 3-m", "today 5-y"')
    p.add_argument("--out", default="trends", help="prefix for the output CSV files")
    a = p.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("Set APIFY_TOKEN first (Apify Console -> Settings -> API & Integrations).")

    rows = fetch(a.keywords, a.geo, a.timeframe, token)

    with open(f"{a.out}_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "topRisingQueries": "; ".join(r.get("topRisingQueries") or []),
                        "otherRisingQueries": "; ".join(r.get("otherRisingQueries") or [])})

    with open(f"{a.out}_series.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["keyword", "geo", "date", "value", "isPartial"])
        for r in rows:
            for pt in r.get("interestOverTime") or []:
                w.writerow([r["keyword"], r.get("geo", ""), pt["date"], pt["value"], pt.get("isPartial", False)])

    for r in rows:
        print(f'{r["keyword"]:<25} {r.get("geo") or "world":<6} {str(r.get("trend")):<8} '
              f'{r.get("percentOfPeak")}% of peak (peak {r.get("peakDate")})')
    print(f"\nSaved {a.out}_summary.csv and {a.out}_series.csv")


if __name__ == "__main__":
    main()
