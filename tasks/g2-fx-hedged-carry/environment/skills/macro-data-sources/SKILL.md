---
name: macro-data-sources
description: "Endpoints, schemas, and known gotchas for fetching daily fixed-income, FX, and macro projection data from four primary public authorities — U.S. Department of the Treasury (par yield curve rates), Ministry of Finance Japan (JGB constant-maturity yields), FRED (St. Louis Fed economic time series), and the IMF DataMapper API (WEO projections). Use when a task requires assembling cross-country sovereign yield, FX spot, or WEO macro projection data from these primary sources."
---

# Macro Data Sources

Practical, verified-as-of-2026-04 access patterns for the four authorities that publish freely-redistributable daily fixed-income, FX, and macro projection data covering the US and Japan. Endpoints, headers, schemas, and the gotchas each one bites first-time users with.

## 1. U.S. Department of the Treasury — Daily Treasury Par Yield Curve Rates

The canonical US Treasury constant-maturity yield series. 14 tenors: 1 Mo, 1.5 Month, 2 Mo, 3 Mo, 4 Mo, 6 Mo, 1 Yr, 2 Yr, 3 Yr, 5 Yr, 7 Yr, 10 Yr, 20 Yr, 30 Yr. Yields are par yields, in percent.

**CSV download (whole year):**
```
https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/<YEAR>/all?type=daily_treasury_yield_curve&field_tdr_date_value=<YEAR>&_format=csv
```

**Schema** — header is `Date,"1 Mo","1.5 Month","2 Mo","3 Mo","4 Mo","6 Mo","1 Yr","2 Yr","3 Yr","5 Yr","7 Yr","10 Yr","20 Yr","30 Yr"`. Date format `MM/DD/YYYY`. **Rows are returned most-recent-first** — sort ascending before any time-series operation.

**Gotchas:**
- Column `1.5 Month` is non-standard among curve sources — most yield-curve libraries don't expect it. Either drop it or carry it through explicitly.
- Cell values are strings; some are blank (e.g., `30 Yr` in periods when Treasury suspended the issue). Coerce with care.

## 2. Ministry of Finance Japan — JGB Constant-Maturity Reference Yields

The MOF JGB "jgbcme" (JGB constant maturity series) is the standard reference for Japanese government bond yields. 15 tenors: 1Y through 10Y in 1Y steps, then 15Y, 20Y, 25Y, 30Y, 40Y. Yields are semiannual compound rates, in percent.

**CSV downloads** — must send a browser-style User-Agent or the server returns a Japanese-language HTML splash page:

```bash
curl -A "Mozilla/5.0" \
  "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv"
```

Two endpoints:
- `…/jgbcme.csv` — current month only.
- `…/historical/jgbcme_all.csv` — entire history from 1974, refreshed daily.

**Schema** — title row, then header `Date,1Y,2Y,3Y,4Y,5Y,6Y,7Y,8Y,9Y,10Y,15Y,20Y,25Y,30Y,40Y`. Date format `YYYY/M/D` (no zero-pad). Rows ascending by date. Missing observations encoded as `-`, not blank.

**Gotchas:**
- Without the `Mozilla/5.0` UA you get an HTML page back, not the CSV. The mistake is silent — `head` shows `<!DOCTYPE html>` but file extensions stay `.csv`.
- Japan New Year holiday (Jan 1–3) means JP markets are closed when US markets reopen on Jan 2. Cross-country lookups by US date will miss those JP days — handle with `IFERROR(INDEX(...MATCH(...,0)), "")` rather than imputing zero.
- Long-end tenors (15Y, 20Y, 25Y, 30Y, 40Y) carry `-` in early decades when those issues didn't exist.

## 3. FRED — St. Louis Fed Economic Research Database

FRED hosts curated daily macro/financial time series. Highly relevant series for cross-country sovereign desks:

| Series ID | Description |
|---|---|
| `DEXJPUS` | Japanese yen / U.S. dollar spot, daily, JPY per USD |
| `DEXUSEU` | U.S. dollar / euro spot, daily, USD per EUR |
| `DGS1`, `DGS2`, `DGS5`, `DGS10`, `DGS30` | US Treasury constant-maturity yields (single-tenor; for the whole curve use Treasury's CSV — series 1) |
| `DFF` | Federal funds effective rate (daily, %) |
| `IRLTLT01JPM156N` | Japan 10-Year long-term government bond yield (monthly, derived from MOF) |

**CSV download:**
```
https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>&cosd=YYYY-MM-DD&coed=YYYY-MM-DD
```
No auth required, returns `observation_date,<SERIES_ID>` columns. ISO date format, ascending.

**Gotchas:**
- Missing observations are encoded as `.` (single dot), not blank or NA. Filter explicitly.
- Daily series stop on the most-recent business day; weekend / holiday rows are simply absent (not zero).

## 4. IMF DataMapper API — WEO and SDG indicators

IMF's DataMapper exposes the WEO database (and several others) as a JSON REST API.

**Endpoint:** `https://www.imf.org/external/datamapper/api/v1/<INDICATOR_CODE>` — returns `{values: {<CODE>: {<ISO3>: {<YEAR>: <value>}}}, periods: ...}`.

**Filtering by country in the URL is silently ignored** — append `/USA/JPN` and you'll still get every country in the response. Filter client-side.

**WEO indicator codes you'll actually want:**

| Code | Indicator |
|---|---|
| `NGDP_RPCH` | Real GDP growth (% YoY) |
| `NGDPD` | GDP, current prices (USD bn) |
| `PCPIPCH` | Inflation, average consumer prices (% YoY) |
| `PCPIE_PCH` | Inflation, end-of-period (% YoY) |
| `LUR` | Unemployment rate (%) |
| `GGXWDG_NGDP` | General government gross debt (% GDP) |
| `BCA_NGDPD` | Current account balance (% GDP) |
| `NGDPDPC` | GDP per capita (USD) |

**Country codes** are ISO-3 (`USA`, `JPN`, `DEU`, `GBR`, `CHN`, …), not the IMF's internal short names.

**Gotchas:**
- Each call returns the full universe (~190 countries × ~50 years). Pull what you need into a dict before doing anything else.
- The API exposes the latest WEO vintage. Tasks anchored to a specific vintage (e.g., "April 2026 WEO") cannot be served from this endpoint reliably; for vintage-specific data use the official Excel database download instead.
- Forecast horizon: WEO publishes 5-year-out projections. Year ranges past that horizon return `null`.
- Indicator labels on the UI ("Real GDP growth") differ from the codes (`NGDP_RPCH`); always cite by code in code paths.

## Cross-source workflow recipes

### Aligning a US date series with a JP series

JP holidays cause date misses. The pattern that always works:

```
=IFERROR(INDEX(JP_Yields!<col>$4:<col>$1000,
              MATCH($A<row>,JP_Yields!A$4:A$1000,0)),"")
```

Returning `""` (empty string) instead of `NA()` lets `AVERAGE` and `STDEV` skip those rows naturally. Add an outer `IF(OR(...="",.."",...))` on any downstream cell that does arithmetic, otherwise `""` gets coerced to 0.

### Quarter-start anchor for FX

When computing a Q1 carry-trade PnL, the Q1 "start" spot is the **previous business day's close** (e.g., 2025-12-31 for a Q1 2026 trade), not 2026-01-02. Always pull the trailing-business-day fix as the strike anchor.

### CIP forward sanity check

`F = S · (1 + r_base / 100) / (1 + r_quote / 100)` for tenor 1Y, where `S` and `F` are quoted in `quote/base`. For USD/JPY (JPY per USD), base = USD, quote = JPY: `F_JPYperUSD = S_JPYperUSD · (1 + r_USD/100) / (1 + r_JPY/100)`. Higher US rates → forward higher than spot → JPY at a forward premium against USD (textbook).
