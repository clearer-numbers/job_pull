# job_pull

A two-stage pipeline for Samuel's Platsbanken job search.

## Stage 1 — fetch (GitHub Actions, every 3 days)

`fetch_jobs.py` queries Arbetsförmedlingen's free, keyless JobTech
JobSearch API for a fixed set of search terms (Data Analyst, Business
Intelligence, BI Analyst, Tableau, Power BI), keeps only ads whose
**headline** actually contains one of those terms (free-text search alone
pulled in a lot of unrelated ads that just mentioned the terms in passing),
and writes new ones to `jobs/ads_<date>.json`. `state.json` tracks what's
already been seen so nothing repeats. Runs via
`.github/workflows/schedule.yml` (cron `0 6 */3 * *`, i.e. every 3rd day at
06:00 UTC), or manually from the Actions tab.

## Stage 2 — score, tailor, alert (Claude scheduled task, every 3 days)

A separate Claude scheduled task reads each new `jobs/ads_<date>.json` not
yet in `review_state.json`, and for every ad:

- Reads the ad's full text and `cv/master_cv.md` (a plain-text copy of
  Samuel's CV, kept here so the task always has it regardless of whether
  his computer is linked at run time).
- Writes a plain-language verdict — **Apply**, **Maybe**, or **Skip** — with
  reasoning, not a numeric/ATS-style score (there's no real ATS to
  calibrate against, so a percentage would be false precision).
- **Apply:** tailors a `.docx` CV immediately and sends it to Samuel.
- **Maybe:** added to `queue.json` under `pending`, for Samuel to review;
  once he decides, the task (in that conversation, or a later one) tailors
  it and moves the entry to `decided`.
- **Skip:** just noted in the summary, no CV made.

Samuel is alerted (push + email) with a summary each cycle.

## Files

- `fetch_jobs.py` — stage 1 fetch script.
- `.github/workflows/schedule.yml` — stage 1 schedule.
- `cv/master_cv.md` — plain-text copy of the CV, source of truth for tailoring.
- `queue.json` — pending/decided "Maybe" ads awaiting Samuel's review.
- `review_state.json` — tracks which `jobs/ads_*.json` files stage 2 has processed.
- `state.json` — stage 1's dedup state (last run time + seen ad ids).
- `jobs/ads_<date>.json` — raw output of each stage 1 run.
