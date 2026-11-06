# Google Trends API for Python (a pytrends alternative)

[pytrends](https://github.com/GeneralMills/pytrends) is archived, and many people now get
`TooManyRequestsError: The request failed: Google returned a response with code 429` on their first few requests.
Google's official Trends API is a limited alpha you have to apply for.

This repo is a small Python script that gets Google Trends data for **many keywords × many countries** and
saves it as CSV:

- interest over time (full series)
- interest by region
- top and rising related queries
- a one-line summary per keyword: `trend` (rising / falling / flat), `percentOfPeak`, `peakDate`

```text
$ python trends.py "air fryer" matcha --geo US
matcha                    US     falling  56% of peak (peak 2026-06-21)
air fryer                 US     flat     55% of peak (peak 2026-04-12)

Saved trends_summary.csv and trends_series.csv
```

**Disclosure:** the scraping runs on my
[Google Trends Scraper on Apify](https://apify.com/najiva/google-trends-reliable), which handles proxies,
cookies and 429 retries. I built it and earn money when it's used. It costs **$1.50 per 1,000 results**
(one result = one keyword in one country, all data types included) plus $0.01 per run. Failed queries and
keywords with no data are not charged. Apify's free plan includes monthly credit, enough to try it.

## Quick start

```bash
git clone https://github.com/Najiva/google-trends-api-python.git
cd google-trends-api-python
pip install -r requirements.txt
export APIFY_TOKEN=...   # Apify Console -> Settings -> API & Integrations
python trends.py "air fryer" "standing desk" matcha --geo US GB DE --timeframe "today 5-y"
```

Options:

| Flag | Meaning | Default |
|---|---|---|
| `keywords` | one or more search terms; each is fetched separately with its own 0–100 scale | required |
| `--geo` | country or region codes, e.g. `US GB DE US-CA` | worldwide |
| `--timeframe` | `now 1-H`, `now 7-d`, `today 1-m`, `today 3-m`, `today 12-m`, `today 5-y`, `all`, or `YYYY-MM-DD YYYY-MM-DD` | `today 12-m` |
| `--out` | prefix for the CSV files | `trends` |

Output:

- `trends_summary.csv`: one row per keyword × country with `trend`, `trendChangePercent`, `percentOfPeak`, `peakDate`, `latestValue`, `topRisingQueries` and `otherRisingQueries`
- `trends_series.csv`: the interest-over-time series in long format (`keyword, geo, date, value, isPartial`), ready for pandas or a spreadsheet

`trend` compares the average of the last 12 complete points with the 12 before them (±10% counts as flat).

## Use it from your own code

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("najiva/google-trends-reliable").call(run_input={
    "keywords": ["air fryer", "standing desk", "matcha"],
    "geos": ["US", "GB"],
    "timeframe": "today 12-m",
})
for row in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(row["keyword"], row["geo"], row["trend"], row["percentOfPeak"])
```

Every row also has `interestOverTime`, `interestByRegion` and `relatedQueries`. You can call the same Actor from
JavaScript, plain HTTP, Make, Zapier or n8n. See the [Actor page](https://apify.com/najiva/google-trends-reliable).

## If you'd rather do it yourself for free

For a few keywords a day you don't need any of this:

- Put up to 5 keywords in each pytrends `build_payload` call and wait 60 s or more between calls.
- Try [trendspyg](https://pypi.org/project/trendspyg/), an open-source client that is still being updated (I haven't tested it).
- The 429s behave like a per-IP limit. For bulk work you need rotating IPs, and each new IP needs a fresh
  `NID` cookie from `https://trends.google.com/trends/explore` before the API calls work.

## Notes

- Google Trends values are relative (0–100) per query, not search volumes.
- Google's "rising" related queries currently include a lot of unrelated junk (for "air fryer" in the US: "laptop stand", "hotel booking", "solar panels"; the Google Trends website shows the same). `topRisingQueries` keeps only queries that mention your keyword; the rest are in `otherRisingQueries`.

## License

MIT
