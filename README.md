# Sentiment Pipeline Test

## Background

The objective of this module is to identify and evaluate suitable data sources for ingesting user feedback at scale.

Two candidate sources were selected for in-depth testing based on an initial multi-criteria scoring assessment:

- **Google Play Store** — app reviews across multiple categories
- **Amazon** — product reviews with rich commercial context

---

## Google Play Store Test

**Tool:** `google-play-scraper` (open-source Python library)

**Apps tested:**

| App | Industry |
|-----|----------|
| Uber | Ride-hailing |
| DoorDash | Food delivery |
| Spotify | Music streaming |
| Duolingo | Education |
| TikTok | Social media |

**Key findings:**
- 1,000 reviews successfully fetched per app with no rate-limiting or blocking observed
- Core fields (reviewId, userName, content, score, timestamp) are 100% complete across all apps
- `appVersion` completeness ranges from 67% (TikTok) to 92% (Duolingo)
- TikTok shows 84% developer reply rate; most other apps show 0%
- No authentication or API key required


---

## Amazon Test

**Tool:** Python `requests` + `BeautifulSoup`

**Product tested:** Apple AirPods 4 (ASIN: B0DGHMNQ5Z)

**Three approaches tested:**

**Approach 1 — Basic static request (`amazon_static.py`)**
- Status code: 200 (page reachable)
- Reviews found: 0
- Bot detection triggered: True
- Amazon returned a valid-looking page but without review content, while flagging the request as automated

**Approach 2 — Improved browser-mimicking headers (`amazon_improvedheader.py`)**
- Status code: 200
- Reviews found: 0
- Bot detection triggered: False
- Headers successfully bypassed bot detection, but reviews still not present in static HTML — confirmed to be dynamically rendered via JavaScript

**Approach 3 — Internal API endpoint (`amazon_internalapi.py`)**
- Successfully identified an internal Amazon review API via browser DevTools
- API returns structured JSON with full review fields (id, title, rating, text, date, contributor)
- However, the endpoint requires session-bound parameters (`stamp`, `x-amz-acp-params`) that are dynamically generated per browser session and expire immediately
- Attempting to replay the request returned HTTP 400
- Recurring automated collection via this method is not feasible

**Overall conclusion:**
Amazon live review data is not practically accessible for automated ingestion due to JavaScript dynamic rendering, session-bound API parameters, and explicit Terms of Service restrictions prohibiting scraping and ML use of collected content.


---

## Findings Summary

| Dimension | Google Play Store | Amazon |
|-----------|-------------------|--------|
| Accessibility | High — no auth required | Low — JS rendering + session-bound API |
| Volume | 1,000+ per request, no cap | Not accessible via automated methods |
| Data Structure | Consistent JSON, 100% core fields | Cannot be verified via live collection |
| Recurring Collection | Stable, no blocking observed | Not feasible without ToS violation |
| Commercial Value | Strong — tied to real app usage | Very high in theory, inaccessible in practice |

---

## Recommendation

**Google Play Store** is recommended as the primary data source for this pipeline.
