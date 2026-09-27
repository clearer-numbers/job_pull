#!/usr/bin/env python3
"""
Pulls new Platsbanken job ads from the JobTech JobSearch API (free, keyless)
for a fixed set of search terms, dedupes against ads already seen, and
writes any new ones to jobs/ads_<date>.json.

State (last run time + seen ad ids) is kept in state.json so re-runs never
re-report the same ad twice, even if the lookback window overlaps.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API_BASE = "https://jobsearch.api.jobtechdev.se/search"

# Search terms to cover the requested titles (Swedish + English variants
# where they differ meaningfully).
SEARCH_TERMS = [
    "Data Analyst",
    "Business Intelligence",
    "BI Analyst",
    "Tableau",
    "Power BI",
]

LOOKBACK_DAYS_DEFAULT = 3   # used only if there's no prior state.json
RESULTS_PER_QUERY = 100     # generous; well under the API's page cap

STATE_PATH = "state.json"
JOBS_DIR = "jobs"


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_run_utc": None, "seen_ad_ids": []}


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def fetch(query, published_after):
    params = {
        "q": query,
        "limit": RESULTS_PER_QUERY,
        "sort": "pubdate-desc",
        "published-after": published_after,
    }
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_ad(hit):
    employer = (hit.get("employer") or {}).get("name")
    workplace = (hit.get("workplace_address") or {}).get("municipality")
    description = (hit.get("description") or {}).get("text", "")
    return {
        "id": hit.get("id"),
        "headline": hit.get("headline"),
        "employer": employer,
        "municipality": workplace,
        "publication_date": hit.get("publication_date"),
        "application_deadline": hit.get("application_deadline"),
        "webpage_url": hit.get("webpage_url"),
        "description_text": description,
    }


def main():
    state = load_state()

    if state.get("last_run_utc"):
        published_after = state["last_run_utc"]
    else:
        published_after = (
            datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS_DEFAULT)
        ).strftime("%Y-%m-%dT%H:%M:%S")

    seen_ids = set(state.get("seen_ad_ids", []))
    new_ads = {}
    errors = []

    for term in SEARCH_TERMS:
        try:
            data = fetch(term, published_after)
        except Exception as exc:
            errors.append(f"{term}: {exc}")
            continue
        for hit in data.get("hits", []):
            ad = extract_ad(hit)
            if ad["id"] and ad["id"] not in seen_ids:
                new_ads[ad["id"]] = ad

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ads_list = sorted(
        new_ads.values(), key=lambda a: a["publication_date"] or "", reverse=True
    )

    os.makedirs(JOBS_DIR, exist_ok=True)
    out_path = os.path.join(JOBS_DIR, f"ads_{now_utc[:10]}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_utc": now_utc,
                "published_after_used": published_after,
                "search_terms": SEARCH_TERMS,
                "new_ad_count": len(ads_list),
                "ads": ads_list,
                "errors": errors,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    # Update state regardless of whether anything new was found, so the
    # next run's window starts from here.
    seen_ids.update(new_ads.keys())
    state["last_run_utc"] = now_utc
    state["seen_ad_ids"] = sorted(seen_ids)
    save_state(state)

    print(f"Wrote {len(ads_list)} new ad(s) to {out_path}")
    if errors:
        print("Errors during fetch:", errors, file=sys.stderr)


if __name__ == "__main__":
    main()
